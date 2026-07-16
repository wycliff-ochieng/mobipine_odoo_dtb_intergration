from odoo import models, fields, api
from .dtb_logger import DTBLogger

log = DTBLogger('TILL')


class DtbMojaTill(models.Model):
    _name = 'dtb.moja.till'
    _description = 'DTB Till Moja Configuration'
    _rec_name = 'name'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    till_number = fields.Char(required=True)
    user_id = fields.Char(string='API User ID', required=True)
    password = fields.Char(string='API Password', required=True)
    api_key = fields.Char(string='API Key')
    channel = fields.Char(default='MBS')
    journal_id = fields.Many2one('account.journal', string='Payment Journal')
    is_active = fields.Boolean(default=True)

    settlement_mode = fields.Selection([
        ('till_moja', 'Till Moja'),
        ('core_banking', 'Core Banking'),
    ], string='Settlement Mode', default='till_moja', required=True,
        help='Till Moja: funds settle to the till balance.\n'
             'Core Banking: funds settle directly to the bank account.')

    account_source = fields.Char(
        string='Account Source',
        default='CORE BANKING',
        help='Source system for the bank account (e.g. CORE BANKING). '
             'Used when settlement_mode is Core Banking.',
    )
    account_id = fields.Char(
        string='Bank Account Number',
        help='Bank account number for settlement. '
             'Used when settlement_mode is Core Banking.',
    )

    stk_push_url = fields.Char(
        string='STK Push URL',
        help='DTB API endpoint for initiating M-Pesa STK Push requests. '
             'Leave empty to use the default till-moja/stk-push endpoint.',
    )
    stk_push_callback_url = fields.Char(
        string='STK Callback URL',
        help='Public URL where DTB should send STK push results. '
             'Typically https://your-odoo.com/api/dtb/stk-callback',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec, vals in zip(records, vals_list):
            log.info('CREATE', id=rec.id, name=rec.name, till=rec.till_number,
                     active=rec.is_active, stk_url=rec.stk_push_url)
        return records

    def write(self, vals):
        for rec in self:
            changed = {k: vals[k] for k in vals if k in ('name', 'till_number', 'is_active',
                                                          'stk_push_url', 'journal_id') and vals[k] != rec[k]}
            if changed:
                log.info('WRITE', id=rec.id, name=rec.name, changes=changed)
        return super().write(vals)

    def name_get(self):
        result = super().name_get()
        log.info('name_get', count=len(result))
        return result

    @api.model
    def search(self, domain, **kwargs):
        result = super().search(domain, **kwargs)
        log.info('SEARCH', domain=domain, count=len(result))
        return result
