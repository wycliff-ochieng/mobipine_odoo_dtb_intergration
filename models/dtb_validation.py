from odoo import models, api
import math
import uuid
import requests
import traceback
from odoo.exceptions import UserError
from .dtb_logger import DTBLogger

log = DTBLogger('VALIDATION')


class DtbMojaValidation(models.AbstractModel):
    _name = 'dtb.moja.validation'
    _description = 'DTB Till Moja Validation & Payment Logic'

    # ============================================================
    # REFERENCE VALIDATION — handles GET /api/dtb/validate-reference
    # ============================================================

    @api.model
    def _validate_reference(self, till_number, reference_number, transaction_amount):
        log.info('REFERENCE_VALIDATE | ENTER',
                 till=till_number, ref=reference_number, amount=transaction_amount)
        try:
            Invoice = self.env['account.move'].sudo()
            invoice_data = Invoice.search_read(
                domain=[
                    ('payment_reference', '=', reference_number),
                    ('state', '=', 'posted'),
                    ('payment_state', 'not in', ('paid', 'in_payment')),
                ],
                fields=['amount_residual', 'name', 'partner_id'],
                limit=1,
            )
            log.info('REFERENCE_VALIDATE | SEARCH',
                     model='account.move', field='payment_reference',
                     value=reference_number, found=bool(invoice_data))

            if not invoice_data:
                log.warn('REFERENCE_VALIDATE | NOT_FOUND',
                         ref=reference_number, reason='no invoice matched by payment_reference')
                return None

            row = invoice_data[0]
            amt = float(transaction_amount)
            residual = float(row['amount_residual'] or 0)
            match = math.isclose(amt, residual, rel_tol=1e-9)
            partner_name = row['partner_id'][1] if row.get('partner_id') else ''
            invoice_name = row['name'] or ''

            log.info('REFERENCE_VALIDATE | AMOUNT_CHECK',
                     tx_amount=amt, residual=residual,
                     isclose=match, invoice=invoice_name)

            if not match:
                log.warn('REFERENCE_VALIDATE | MISMATCH',
                         ref=reference_number, expected=residual, got=amt)
                return None

            result = {
                'till_number': till_number,
                'reference_id': reference_number,
                'value_1': partner_name,
                'value_2': invoice_name,
                'value_3': str(residual),
                'value_4': '',
                'value_5': '',
            }
            log.ok('REFERENCE_VALIDATE | SUCCESS',
                   partner=partner_name, invoice=invoice_name, residual=str(residual))
            return result

        except Exception:
            log.exc('REFERENCE_VALIDATE | EXCEPTION',
                    traceback=traceback.format_exc())
            raise

    # ============================================================
    # TILL MOJA CALLBACK (C2B) — handles POST /api/dtb/callback/notification
    # ============================================================

    @api.model
    def _process_callback_payload(self, payload):
        xref = payload.get('xref')
        amount = float(payload.get('amount', 0))
        reference = payload.get('narration', '')
        cbs_reference = payload.get('cbs_reference')
        account_number = payload.get('account_number', '')
        log.incoming('C2B_CALLBACK | ENTER',
                     xref=xref, amount=amount, narration=reference,
                     cbs_ref=cbs_reference, account=account_number)

        existing = self.env['payment.transaction'].sudo().search([
            ('dtb_xref', '=', xref),
        ], limit=1)
        if existing:
            log.info('C2B_CALLBACK | IDEMPOTENT',
                     xref=xref, existing_id=existing.id, state=existing.state)
            return {
                'xref': xref,
                'user_reference': existing.reference,
                'ack_code': '00',
                'ack_description': 'SUCCESS',
            }

        till = self.env['dtb.moja.till'].sudo().search([
            ('till_number', '=', account_number),
        ], limit=1)
        if not till:
            till = self.env['dtb.moja.till'].sudo().search([
                ('account_id', '=', account_number),
            ], limit=1)
        settlement_mode = till.settlement_mode if till else 'till_moja'
        log.info('C2B_CALLBACK | TILL_LOOKUP',
                 account=account_number, till_id=till.id if till else None,
                 settlement=settlement_mode)

        invoice = self.env['account.move'].sudo().search([
            ('payment_reference', '=', reference),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment')),
        ], limit=1)
        if not invoice and cbs_reference and settlement_mode == 'core_banking':
            invoice = self.env['account.move'].sudo().search([
                ('payment_reference', '=', cbs_reference),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ('paid', 'in_payment')),
            ], limit=1)
            log.info('C2B_CALLBACK | CBS_INVOICE_SEARCH',
                     cbs_ref=cbs_reference, found=invoice.id if invoice else None)
        log.info('C2B_CALLBACK | INVOICE_SEARCH',
                 narration=reference, found=invoice.id if invoice else None)

        company = self.env.company
        tx_values = {
            'dtb_xref': xref,
            'dtb_payment_method': 'till_moja',
            'dtb_settlement_mode': settlement_mode,
            'dtb_customer_name': payload.get('customer_name'),
            'dtb_phone_number': payload.get('customer_mobile'),
            'provider_reference': cbs_reference or payload.get('cbs_reference'),
            'amount': amount,
            'reference': xref,
        }

        if invoice:
            tx_values['partner_id'] = invoice.partner_id.id
            tx_values['invoice_ids'] = [(6, 0, invoice.ids)]
            tx_values['currency_id'] = invoice.currency_id.id
        else:
            tx_values['currency_id'] = company.currency_id.id

        tx = self.env['payment.transaction'].sudo()._dtb_create_transaction(tx_values)

        if till:
            tx.write({'dtb_till_id': till.id})

        if invoice:
            log.ok('C2B_CALLBACK | INVOICE_FOUND',
                   invoice_id=invoice.id, invoice_name=invoice.name)
            tx._set_done()
            tx._post_process()
            log.ok('C2B_CALLBACK | RECONCILED',
                   xref=xref, tx_id=tx.id, invoice=invoice.name)
            return {
                'xref': xref,
                'user_reference': tx.reference,
                'ack_code': '00',
                'ack_description': 'SUCCESS',
            }

        tx._set_done()
        log.warn('C2B_CALLBACK | MISMATCH',
                 xref=xref, reason='Invoice not found for narration',
                 narration=reference, settlement=settlement_mode)
        return {
            'xref': xref,
            'user_reference': 'MANUAL_RECONCILIATION_REQUIRED',
            'ack_code': '00',
            'ack_description': 'UNMATCHED_REFERENCE',
        }

    # ============================================================
    # STK PUSH — Outgoing request to DTB
    # ============================================================

    @api.model
    def _stk_push_request(self, till_id, amount, phone_number, narration,
                          partner_name=None, partner_id=None, settlement_mode=None):
        log.info('STK_PUSH | ENTER',
                 till_id=till_id, amount=amount, phone=phone_number,
                 narration=narration, partner=partner_name,
                 settlement=settlement_mode)

        till = self.env['dtb.moja.till'].browse(till_id)
        if not till.exists():
            log.err('STK_PUSH | TILL_NOT_FOUND', till_id=till_id)
            raise UserError('Till configuration not found.')

        api_url = till.stk_push_url or self._get_dtb_base_url() + '/till-moja/stk-push'
        callback_url = till.stk_push_callback_url or self._get_odoo_base_url() + '/api/dtb/stk-callback'
        xref = 'EXT-' + uuid.uuid4().hex[:12].upper()

        log.info('STK_PUSH | CONFIG',
                 till=till.till_number, api_url=api_url, callback_url=callback_url, xref=xref)

        payload = {
            'request_identifier': {
                'xref': xref,
                'user_id': till.user_id,
                'password': till.password,
                'channel': till.channel or 'MBS',
            },
            'request_data': {
                'till_number': till.till_number,
                'amount': str(amount),
                'phone_number': phone_number,
                'narration': narration,
                'callback_url': callback_url,
            },
        }

        try:
            headers = {'Content-Type': 'application/json'}
            if till.api_key:
                headers['Authorization'] = 'Bearer ' + till.api_key
            log.outgoing('STK_PUSH | HTTP_REQUEST', url=api_url, xref=xref)
            with log.timed('STK_PUSH | HTTP_POST', url=api_url, xref=xref):
                resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            log.incoming('STK_PUSH | HTTP_RESPONSE',
                         status=resp.status_code, body=str(result)[:500])
        except requests.ConnectionError:
            log.err('STK_PUSH | CONNECTION_ERROR', url=api_url)
            raise UserError('Cannot connect to DTB STK Push endpoint: ' + api_url)
        except requests.Timeout:
            log.err('STK_PUSH | TIMEOUT', url=api_url)
            raise UserError('DTB STK Push request timed out.')
        except requests.HTTPError as e:
            log.err('STK_PUSH | HTTP_ERROR',
                    status=e.response.status_code if e.response else None,
                    body=e.response.text if e.response else str(e))
            raise UserError('DTB STK Push failed: ' + str(e))

        response_data = result.get('response_data', result)
        checkout_id = (
            response_data.get('checkout_request_id')
            or response_data.get('CheckoutRequestID')
            or result.get('checkout_request_id')
            or result.get('CheckoutRequestID')
        )
        response_code = response_data.get('response_code', result.get('response_code', ''))

        log.info('STK_PUSH | PARSE',
                 checkout_id=checkout_id, response_code=response_code)

        if response_code not in ('000', '0', ''):
            desc = response_data.get('response_description', '')
            log.err('STK_PUSH | REJECTED', code=response_code, desc=desc)
            raise UserError('DTB STK Push rejected: code=%s desc=%s' % (response_code, desc))

        tx_values = {
            'dtb_xref': xref,
            'dtb_checkout_request_id': checkout_id or '',
            'dtb_till_id': till.id,
            'dtb_phone_number': phone_number,
            'dtb_payment_method': 'stk_push',
            'dtb_stk_response_code': response_code,
            'dtb_customer_name': partner_name or 'STK Customer',
            'dtb_settlement_mode': settlement_mode or till.settlement_mode,
            'amount': amount,
            'partner_id': partner_id or False,
            'reference': xref,
        }

        tx = self.env['payment.transaction'].sudo()._dtb_create_transaction(tx_values)
        log.ok('STK_PUSH | TX_CREATED',
               tx_id=tx.id, xref=xref, checkout_id=checkout_id, state=tx.state)

        return {
            'checkout_request_id': checkout_id or '',
            'xref': xref,
            'response_code': response_code,
            'transaction_id': tx.id,
        }

    # ============================================================
    # STK CALLBACK — handles POST /api/dtb/stk-callback
    # ============================================================

    @api.model
    def _process_stk_callback(self, payload):
        log.incoming('STK_CALLBACK | ENTER', payload_preview=str(payload)[:300])
        try:
            checkout_id, amount, receipt, phone, result_code, result_desc = self._parse_stk_payload(payload)
            log.info('STK_CALLBACK | PARSED',
                     checkout_id=checkout_id, amount=amount, receipt=receipt,
                     phone=phone, result_code=result_code, result_desc=result_desc)

            if not checkout_id:
                log.err('STK_CALLBACK | MISSING_CHECKOUT_ID',
                        payload=str(payload)[:500])
                return {'ack_code': '99', 'ack_description': 'MISSING_CHECKOUT_ID'}

            tx = self.env['payment.transaction'].sudo().search([
                ('dtb_checkout_request_id', '=', checkout_id),
            ], limit=1)
            log.info('STK_CALLBACK | TX_LOOKUP',
                     checkout_id=checkout_id, found=tx.id if tx else None)

            if not tx:
                log.err('STK_CALLBACK | TX_NOT_FOUND',
                        checkout_id=checkout_id)
                return {'ack_code': '99', 'ack_description': 'TRANSACTION_NOT_FOUND'}

            settlement_mode = tx.dtb_settlement_mode or 'till_moja'
            log.info('STK_CALLBACK | SETTLEMENT',
                     tx_id=tx.id, mode=settlement_mode)

            if tx.state in ('done',):
                log.info('STK_CALLBACK | IDEMPOTENT',
                         tx_id=tx.id, checkout_id=checkout_id, state=tx.state)
                return {'ack_code': '00', 'ack_description': 'SUCCESS'}

            if result_code not in ('0', '000', 0, '00'):
                log.err('STK_CALLBACK | PAYMENT_FAILED',
                        tx_id=tx.id, result_code=result_code, desc=result_desc)
                tx.write({
                    'dtb_stk_result_code': str(result_code),
                    'dtb_stk_result_desc': result_desc or 'Payment failed',
                })
                tx._set_error('DTB STK failed: %s' % result_desc)
                return {'ack_code': '00', 'ack_description': 'FAILED'}

            updates = {
                'dtb_stk_result_code': str(result_code),
                'dtb_stk_result_desc': result_desc or 'SUCCESS',
                'provider_reference': receipt or tx.provider_reference,
            }
            if receipt:
                updates['provider_reference'] = receipt
            if phone:
                updates['dtb_phone_number'] = str(int(phone)) if phone else phone
            tx.write(updates)

            search_refs = [tx.dtb_xref, tx.reference]
            if settlement_mode == 'core_banking' and tx.provider_reference:
                search_refs.insert(0, tx.provider_reference)
            invoice = None
            for ref in search_refs:
                if not ref:
                    continue
                invoice = self.env['account.move'].sudo().search([
                    ('payment_reference', '=', ref),
                    ('state', '=', 'posted'),
                    ('payment_state', 'not in', ('paid', 'in_payment')),
                ], limit=1)
                if invoice:
                    log.info('STK_CALLBACK | INVOICE_MATCHED_BY',
                             ref=ref, invoice_id=invoice.id)
                    break

            if not invoice:
                log.warn('STK_CALLBACK | INVOICE_NOT_FOUND',
                         xref=tx.dtb_xref, ref=tx.reference,
                         settlement=settlement_mode)

            if invoice:
                tx.write({'invoice_ids': [(6, 0, invoice.ids)]})
                log.ok('STK_CALLBACK | INVOICE_MATCHED',
                       invoice_id=invoice.id, invoice_name=invoice.name)

            tx._set_done()
            tx._post_process()
            log.ok('STK_CALLBACK | DONE', tx_id=tx.id, receipt=receipt,
                   settlement=settlement_mode)

            if invoice:
                return {
                    'ack_code': '00',
                    'ack_description': 'SUCCESS',
                    'user_reference': tx.reference,
                }

            return {'ack_code': '00', 'ack_description': 'SUCCESS'}

        except Exception:
            log.exc('STK_CALLBACK | EXCEPTION',
                    traceback=traceback.format_exc())
            return {'ack_code': '99', 'ack_description': 'INTERNAL_ERROR'}

    @api.model
    def _parse_stk_payload(self, payload):
        log.info('STK_PARSE | ENTER', payload_type=type(payload).__name__)
        checkout_id = None
        amount = None
        receipt = None
        phone = None
        result_code = '0'
        result_desc = 'SUCCESS'

        daraja = payload.get('Body', {}).get('stkCallback', {})
        if daraja:
            checkout_id = daraja.get('CheckoutRequestID')
            result_code = daraja.get('ResultCode', '0')
            result_desc = daraja.get('ResultDesc', 'SUCCESS')
            metadata = daraja.get('CallbackMetadata', {}).get('Item', [])
            log.info('STK_PARSE | DARAJA_FORMAT',
                     checkout_id=checkout_id, result_code=result_code,
                     metadata_count=len(metadata))
            for item in metadata:
                name = item.get('Name', '')
                value = item.get('Value', '')
                if name == 'Amount':
                    amount = value
                elif name == 'MpesaReceiptNumber':
                    receipt = value
                elif name == 'PhoneNumber':
                    phone = str(int(value)) if value else None
        else:
            checkout_id = checkout_id or payload.get('checkout_request_id') or payload.get('CheckoutRequestID')
            result_code = result_code or payload.get('result_code') or payload.get('ResultCode', '0')
            receipt = payload.get('mpesa_receipt') or payload.get('MpesaReceiptNumber')
            phone = payload.get('phone_number') or payload.get('PhoneNumber')
            log.info('STK_PARSE | FLAT_FORMAT',
                     checkout_id=checkout_id, result_code=result_code,
                     receipt=receipt, phone=phone)

        return checkout_id, amount, receipt, phone, result_code, result_desc

    @api.model
    def _get_dtb_base_url(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'mobipine_odoo_dtb_intergration.dtb_base_url')
        url = param or 'https://api.dtbafrica.com'
        log.info('CONFIG | DTB_BASE_URL', url=url, from_param=bool(param))
        return url

    @api.model
    def _get_odoo_base_url(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        url = param or 'http://localhost:8069'
        log.info('CONFIG | ODOO_BASE_URL', url=url, from_param=bool(param))
        return url
