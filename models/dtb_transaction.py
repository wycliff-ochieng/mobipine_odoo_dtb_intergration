from odoo import models, fields, api
from .dtb_logger import DTBLogger
from odoo.exceptions import ValidationError

log = DTBLogger('DTB_TX')


class DtbMojaTransaction(models.Model):
    _name = 'dtb.moja.transaction'
    _description = 'DTB Till Moja Transaction Log'
    _rec_name = 'xref'
    _sql_constraints = [
        ('xref_unique', 'UNIQUE(xref)',
         'Transaction reference (xref) must be unique per DTB transaction.'),
    ]

    @api.constrains('xref')
    def _check_xref_unique(self):
        for record in self:
            if self.search([('xref', '=', record.xref), ('id', '!=', record.id)]):
                raise ValidationError(
                    'Transaction reference (xref) must be unique per DTB transaction.'
                )

    xref = fields.Char(string='Trace Reference', required=True, index=True)
    cbs_reference = fields.Char(string='Core Banking Reference')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    customer_name = fields.Char()
    customer_mobile = fields.Char()
    narration = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_stk', 'STK Pending'),
        ('processed', 'Processed'),
        ('mismatch', 'Mismatch'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    ], default='draft', required=True)
    till_id = fields.Many2one('dtb.moja.till', string='Till')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    error_reason = fields.Text()

    checkout_request_id = fields.Char(
        string='Checkout Request ID',
        help='Safaricom/Daraja checkout request ID returned by the STK Push.',
    )
    phone_number = fields.Char(
        string='Phone Number',
        help='Customer M-Pesa phone number (format: 2547XXXXXXXX).',
    )
    payment_method = fields.Selection([
        ('till_moja', 'Till Moja (C2B)'),
        ('stk_push', 'STK Push (B2C)'),
    ], default='till_moja', required=True)
    settlement_mode = fields.Selection([
        ('till_moja', 'Till Moja'),
        ('core_banking', 'Core Banking'),
    ], string='Settlement Mode', default='till_moja',
        help='How this transaction was settled on DTB side.')
    stk_response_code = fields.Char(string='STK Response Code')
    stk_result_code = fields.Char(string='STK Result Code')
    stk_result_desc = fields.Char(string='STK Result Description')
    mpesa_receipt = fields.Char(string='M-Pesa Receipt Number')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list):
            log.info('CREATE', id=rec.id, xref=rec.xref, state=rec.state,
                     method=rec.payment_method, amount=rec.amount,
                     invoice=rec.invoice_id.id, checkout=rec.checkout_request_id)
        return records

    def write(self, vals):
        for rec in self:
            changed = {k: vals[k] for k in vals if vals[k] != rec[k]}
            if changed:
                log.info('WRITE', id=rec.id, xref=rec.xref, changes=changed)
        return super().write(vals)
