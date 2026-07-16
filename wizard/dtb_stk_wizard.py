from odoo import models, fields, api
from odoo.exceptions import UserError
from ..models.dtb_logger import DTBLogger

log = DTBLogger('WIZARD')


class DtbStkPaymentWizard(models.TransientModel):
    _name = 'dtb.stk.payment.wizard'
    _description = 'STK Push Payment Wizard'

    invoice_id = fields.Many2one('account.move', required=True)
    amount = fields.Monetary(
        currency_field='currency_id',
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
    )
    phone_number = fields.Char(
        required=True,
        string='Phone Number',
        help='Customer phone number in 254 format (e.g. 254790999957)',
    )
    till_id = fields.Many2one(
        'dtb.moja.till',
        string='DTB Till',
        domain=[('is_active', '=', True)],
        help='Select the DTB Till to process this payment through.',
    )
    settlement_mode = fields.Selection([
        ('till_moja', 'Till Moja'),
        ('core_banking', 'Core Banking'),
    ], string='Settlement Mode', default='till_moja',
        help='Till Moja: funds settle to the till balance.\n'
             'Core Banking: funds settle directly to the bank account.')
    account_source = fields.Char(
        string='Account Source',
        default='CORE BANKING',
        help='Source system for the bank account (e.g. CORE BANKING).',
    )
    account_id = fields.Char(
        string='Bank Account Number',
        help='Bank account number where funds will be settled.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'invoice_id' in res and res['invoice_id']:
            invoice = self.env['account.move'].browse(res['invoice_id'])
            if 'amount' in fields_list:
                res['amount'] = invoice.amount_residual or invoice.amount_total
        return res

    @api.onchange('till_id')
    def _onchange_till_id(self):
        if self.till_id:
            self.settlement_mode = self.till_id.settlement_mode
            self.account_source = self.till_id.account_source or 'CORE BANKING'
            self.account_id = self.till_id.account_id or ''

    @api.onchange('settlement_mode')
    def _onchange_settlement_mode(self):
        if self.settlement_mode == 'till_moja':
            self.account_source = False
            self.account_id = False

    def action_send_stk_push(self):
        self.ensure_one()
        log.info('action_send_stk_push | ENTER',
                 invoice=self.invoice_id.id, amount=self.amount,
                 phone=self.phone_number, till=self.till_id.id,
                 settlement=self.settlement_mode,
                 account=self.account_id if self.settlement_mode == 'core_banking' else None)

        invoice = self.invoice_id
        if invoice.payment_state in ('paid', 'in_payment'):
            log.warn('action_send_stk_push | ALREADY_PAID',
                     invoice=invoice.id, state=invoice.payment_state)
            raise UserError('Invoice is already paid or in payment.')

        if self.settlement_mode == 'core_banking' and not self.account_id:
            log.warn('action_send_stk_push | MISSING_ACCOUNT_ID')
            raise UserError(
                'Bank Account Number is required for Core Banking settlement. '
                'Enter the account number or select a till with Core Banking configured.'
            )

        till = self.till_id
        if not till:
            domain = [('is_active', '=', True), ('stk_push_url', '!=', False)]
            if self.settlement_mode == 'core_banking':
                domain += [('account_id', '!=', False)]
            till = self.env['dtb.moja.till'].sudo().search(domain, limit=1)
        if not till:
            log.warn('action_send_stk_push | NO_TILL',
                     reason='no active till with STK Push configured')
            raise UserError(
                'No active till with STK Push configured. '
                'Set up a DTB Till with STK Push URL first.'
            )
        log.info('action_send_stk_push | TILL_FOUND',
                 id=till.id, name=till.name, till=till.till_number,
                 url=till.stk_push_url, settlement=self.settlement_mode)

        narration = invoice.payment_reference or invoice.name
        log.info('action_send_stk_push | NARRATION', narration=narration)

        self.env['dtb.moja.validation'].sudo()._stk_push_request(
            till.id,
            amount=self.amount,
            phone_number=self.phone_number,
            narration=narration,
            partner_name=invoice.partner_id.display_name,
            partner_id=invoice.partner_id.id,
            settlement_mode=self.settlement_mode,
        )

        log.ok('action_send_stk_push | SUCCESS', closing='wizard')
        return {'type': 'ir.actions.act_window_close'}
