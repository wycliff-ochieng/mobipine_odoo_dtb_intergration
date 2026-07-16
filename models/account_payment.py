from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    dtb_xref = fields.Char(string='DTB Trace Reference', index=True, copy=False)
    dtb_phone_number = fields.Char(string='DTB Phone Number', copy=False)
    dtb_customer_name = fields.Char(string='DTB Customer Name', copy=False)
    dtb_till_id = fields.Many2one('dtb.moja.till', string='DTB Till', copy=False)
