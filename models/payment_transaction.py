from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from .dtb_logger import DTBLogger

log = DTBLogger('PAYMENT_TX')


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    dtb_xref = fields.Char(string='DTB Trace Reference', index=True, copy=False)
    dtb_checkout_request_id = fields.Char(string='DTB Checkout Request ID', index=True, copy=False)
    dtb_till_id = fields.Many2one('dtb.moja.till', string='DTB Till', copy=False)
    dtb_phone_number = fields.Char(string='Customer Phone', copy=False)
    dtb_stk_response_code = fields.Char(string='STK Response Code', copy=False)
    dtb_stk_result_code = fields.Char(string='STK Result Code', copy=False)
    dtb_stk_result_desc = fields.Char(string='STK Result Description', copy=False)
    dtb_payment_method = fields.Selection([
        ('till_moja', 'Till Moja (C2B)'),
        ('stk_push', 'STK Push (B2C)'),
    ], string='DTB Payment Method', copy=False)
    dtb_customer_name = fields.Char(string='DTB Customer Name', copy=False)
    dtb_settlement_mode = fields.Selection([
        ('till_moja', 'Till Moja'),
        ('core_banking', 'Core Banking'),
    ], string='DTB Settlement Mode', copy=False)

    def _post_process(self):
        log.info('_post_process | ENTER', tx_id=self.id, ref=self.reference,
                 has_user=bool(self.env.user))
        if not self.env.user:
            log.info('_post_process | REBIND_SUPERUSER', tx_id=self.id)
            self = self.with_user(SUPERUSER_ID)
        result = super()._post_process()
        log.ok('_post_process | DONE', tx_id=self.id)
        return result

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        if provider_code != 'dtb':
            return super()._get_tx_from_notification_data(provider_code, notification_data)

        checkout_id = (
            notification_data.get('checkout_request_id')
            or notification_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        )
        if checkout_id:
            log.info('_get_tx | LOOKUP_BY_CHECKOUT_ID', checkout_id=checkout_id)
            tx = self.search([
                ('dtb_checkout_request_id', '=', checkout_id),
                ('provider_id.code', '=', 'dtb'),
            ], limit=1)
            if tx:
                log.ok('_get_tx | FOUND_BY_CHECKOUT_ID', tx_id=tx.id, checkout_id=checkout_id)
                return tx
            log.info('_get_tx | NOT_FOUND_BY_CHECKOUT_ID', checkout_id=checkout_id)

        xref = notification_data.get('xref')
        if xref:
            log.info('_get_tx | LOOKUP_BY_XREF', xref=xref)
            tx = self.search([
                ('dtb_xref', '=', xref),
                ('provider_id.code', '=', 'dtb'),
            ], limit=1)
            if tx:
                log.ok('_get_tx | FOUND_BY_XREF', tx_id=tx.id, xref=xref)
                return tx
            log.info('_get_tx | NOT_FOUND_BY_XREF', xref=xref)

        log.err('_get_tx | NOT_FOUND', provider_code=provider_code,
                checkout_id=checkout_id, xref=xref)
        raise ValidationError('DTB: No transaction found matching notification data.')

    def _process_notification_data(self, notification_data):
        if self.provider_id.code != 'dtb':
            return super()._process_notification_data(notification_data)

        log.incoming('_process_notification_data | ENTER',
                     tx_id=self.id, state=self.state)

        stk = notification_data.get('Body', {}).get('stkCallback', {})
        if stk:
            result_code = stk.get('ResultCode')
            receipt = None
            phone = None
            result_desc = stk.get('ResultDesc', 'Payment failed')
            if result_code == 0:
                metadata = stk.get('CallbackMetadata', {}).get('Item', [])
                meta = {item['Name']: item.get('Value') for item in metadata}
                receipt = meta.get('MpesaReceiptNumber')
                phone = meta.get('PhoneNumber')
            log.info('_process_notification_data | DARAJA_FORMAT',
                     result_code=result_code, receipt=receipt)
        else:
            raw_code = notification_data.get('result_code') or notification_data.get('ResultCode')
            result_code = int(raw_code) if raw_code is not None else None
            receipt = notification_data.get('mpesa_receipt') or notification_data.get('MpesaReceiptNumber')
            phone = notification_data.get('phone_number') or notification_data.get('PhoneNumber')
            result_desc = notification_data.get('result_desc') or notification_data.get('ResultDesc', 'Payment failed')
            log.info('_process_notification_data | FLAT_FORMAT',
                     result_code=result_code, receipt=receipt)

        if result_code in (0, '0', '00', '000'):
            log.ok('_process_notification_data | SUCCESS',
                   tx_id=self.id, receipt=receipt)
            updates = {'provider_reference': receipt or self.provider_reference}
            if receipt:
                updates['dtb_stk_result_code'] = '0'
                updates['dtb_stk_result_desc'] = result_desc or 'SUCCESS'
            if phone:
                updates['dtb_phone_number'] = str(int(phone)) if phone else phone
            self.write(updates)
            self._set_done()
        elif result_code == 1032:
            log.warn('_process_notification_data | CANCELLED',
                     tx_id=self.id, result_code=result_code)
            self._set_cancel('Customer cancelled M-Pesa payment')
        else:
            log.err('_process_notification_data | ERROR',
                    tx_id=self.id, result_code=result_code, desc=result_desc)
            self.write({
                'dtb_stk_result_code': str(result_code),
                'dtb_stk_result_desc': result_desc or 'Payment failed',
            })
            self._set_error('DTB error %s: %s' % (result_code, result_desc))

        log.flow('_process_notification_data | STATE', tx_id=self.id, new_state=self.state)

    def _create_payment(self, **extra_create_values):
        if self.provider_id.code != 'dtb':
            return super()._create_payment(**extra_create_values)

        log.info('_create_payment | ENTER', tx_id=self.id, ref=self.reference)

        till = self.dtb_till_id
        if not till:
            log.warn('_create_payment | NO_TILL_ON_TX',
                     tx_id=self.id, reason='searching fallback active till')
            till = self.env['dtb.moja.till'].sudo().search([
                ('journal_id', '!=', False),
                ('is_active', '=', True),
            ], limit=1)
            if till:
                log.info('_create_payment | FALLBACK_TILL_FOUND',
                         till_id=till.id, till_number=till.till_number)
            else:
                log.warn('_create_payment | NO_FALLBACK_TILL')

        journal = till.journal_id if till and till.journal_id else self.env['account.journal'].sudo().search([
            ('type', '=', 'bank'),
        ], limit=1)
        log.info('_create_payment | JOURNAL',
                 journal_id=journal.id if journal else None,
                 journal_name=journal.name if journal else None,
                 source='till' if (till and till.journal_id) else 'fallback_bank')

        if not journal:
            log.err('_create_payment | NO_JOURNAL')
            raise UserError('DTB: No journal found for payment. Configure a journal on the till or create a bank journal.')

        method_line = journal.inbound_payment_method_line_ids and journal.inbound_payment_method_line_ids[0]
        if not method_line:
            log.err('_create_payment | NO_METHOD_LINE', journal=journal.name)
            raise UserError('DTB: Journal "%s" has no inbound payment method line.' % journal.name)

        partner = self.partner_id or self.env['res.partner'].sudo().search([
            ('name', '=', 'Unreconciled DTB Customer'),
        ], limit=1)
        if not partner:
            log.info('_create_payment | CREATE_FALLBACK_PARTNER',
                     name='Unreconciled DTB Customer')
            partner = self.env['res.partner'].sudo().create({
                'name': 'Unreconciled DTB Customer',
                'is_company': False,
            })
        else:
            log.info('_create_payment | PARTNER',
                     partner_id=partner.id, name=partner.name,
                     source='invoice' if self.partner_id else 'fallback_customer')

        cbs_ref = self.provider_reference or ''
        with log.timed('_create_payment | PAYMENT_CREATE', tx_id=self.id, amount=self.amount):
            payment = self.env['account.payment'].sudo().create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner.id,
                'amount': self.amount,
                'currency_id': self.currency_id.id,
                'journal_id': journal.id,
                'payment_method_line_id': method_line.id,
                'payment_reference': 'DTB M-Pesa: %s' % cbs_ref,
            })
            if self.partner_id:
                payment.action_post()
                log.ok('_create_payment | PAYMENT_POSTED', payment_id=payment.id,
                       payment_name=payment.name, journal=journal.name)
            else:
                log.warn('_create_payment | PAYMENT_DRAFT | no customer details',
                         payment_id=payment.id, payment_name=payment.name)

        self.write({'payment_id': payment.id})

        if self.invoice_ids:
            invoice = self.invoice_ids[0]
            with log.timed('_create_payment | RECONCILE', tx_id=self.id, invoice=invoice.id):
                payment_lines = payment.move_id.line_ids.filtered(
                    lambda l: l.account_id == invoice.partner_id.property_account_receivable_id
                )
                invoice_lines = invoice.line_ids.filtered(
                    lambda l: l.account_id == invoice.partner_id.property_account_receivable_id
                )
                (payment_lines + invoice_lines).filtered(lambda l: not l.reconciled).reconcile()
            log.ok('_create_payment | RECONCILED', payment=payment.name, invoice=invoice.name)
        else:
            log.warn('_create_payment | NO_INVOICES_TO_RECONCILE', tx_id=self.id)

        return payment

    def _dtb_create_transaction(self, values):
        provider = self.env['payment.provider'].sudo().search([('code', '=', 'dtb')], limit=1)
        if not provider:
            log.info('_dtb_create_transaction | PROVIDER_NOT_FOUND | auto-creating')
            provider = self.env['payment.provider'].sudo().create({
                'name': 'DTB Till Moja',
                'code': 'dtb',
                'state': 'test',
                'is_published': True,
            })
            log.ok('_dtb_create_transaction | PROVIDER_AUTO_CREATED', provider_id=provider.id)

        payment_method = self.env['payment.method'].sudo().search([('code', '=', 'DTB_ACQ')], limit=1)
        if not payment_method:
            log.info('_dtb_create_transaction | METHOD_DTB_ACQ_NOT_FOUND | falling back')
            payment_method = self.env['payment.method'].sudo().search([], limit=1)
        log.info('_dtb_create_transaction | PROVIDER', provider_id=provider.id,
                 payment_method_id=payment_method.id if payment_method else None)

        company = self.env.company or self.env['res.company'].sudo().search([], limit=1)
        currency_id = values.get('currency_id') or (company.currency_id.id if company else False)
        if not currency_id:
            currency_id = self.env['res.currency'].sudo().search([('name', '=', 'KES')], limit=1).id or \
                          self.env['res.currency'].sudo().search([], limit=1).id
            log.warn('_dtb_create_transaction | CURRENCY_FALLBACK', currency_id=currency_id)

        partner_id = values.get('partner_id')
        if not partner_id:
            partner = self.env['res.partner'].sudo().search([
                ('name', '=', 'Unreconciled DTB Customer'),
            ], limit=1)
            if not partner:
                partner = self.env['res.partner'].sudo().create({
                    'name': 'Unreconciled DTB Customer',
                    'is_company': False,
                })
            partner_id = partner.id
            log.info('_dtb_create_transaction | PARTNER_FALLBACK', partner_id=partner_id)

        tx_values = {
            'provider_id': provider.id,
            'payment_method_id': payment_method.id if payment_method else False,
            'amount': values.get('amount', 0),
            'currency_id': currency_id,
            'partner_id': partner_id,
            'reference': values.get('reference') or values.get('dtb_xref', ''),
            'operation': 'online_direct',
        }
        dtb_fields = ['dtb_xref', 'dtb_checkout_request_id', 'dtb_till_id', 'dtb_phone_number',
                      'dtb_stk_response_code', 'dtb_stk_result_code', 'dtb_stk_result_desc',
                      'dtb_payment_method', 'dtb_customer_name', 'dtb_settlement_mode',
                      'provider_reference', 'invoice_ids']
        for f in dtb_fields:
            if f in values:
                tx_values[f] = values[f]

        log.info('_dtb_create_transaction | CREATE', xref=tx_values.get('dtb_xref'),
                 amount=tx_values['amount'], method=tx_values.get('dtb_payment_method'))
        tx = self.sudo().create(tx_values)
        log.ok('_dtb_create_transaction | CREATED', id=tx.id, ref=tx.reference,
               xref=tx.dtb_xref, state=tx.state)
        return tx
