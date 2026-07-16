from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch, MagicMock


class TestDtbStkConfig(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': 'STK Test Journal',
            'type': 'bank',
            'code': 'STKTST',
            'company_id': self.company.id,
        })

    def test_till_has_stk_fields(self):
        till = self.env['dtb.moja.till'].create({
            'name': 'STK Till',
            'company_id': self.company.id,
            'till_number': '200001',
            'user_id': 'API_STK',
            'password': 'stkpass',
            'journal_id': self.journal.id,
            'stk_push_url': 'https://api.dtbafrica.com/till-moja/stk-push',
            'stk_push_callback_url': 'https://odoo.example.com/api/dtb/stk-callback',
        })
        self.assertEqual(till.stk_push_url, 'https://api.dtbafrica.com/till-moja/stk-push')
        self.assertTrue('stk-push' in till.stk_push_url)

    def test_transaction_has_stk_fields(self):
        tx = self.env['dtb.moja.transaction'].create({
            'xref': 'EXT-STK-FIELDS-TEST',
            'amount': 100.0,
            'payment_method': 'stk_push',
            'checkout_request_id': 'ws_CO_DMZ_12345',
            'phone_number': '254790999957',
            'state': 'pending_stk',
        })
        self.assertEqual(tx.payment_method, 'stk_push')
        self.assertEqual(tx.checkout_request_id, 'ws_CO_DMZ_12345')
        self.assertEqual(tx.state, 'pending_stk')
        self.assertEqual(tx.phone_number, '254790999957')


class TestDtbStkPush(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': 'STK Push Journal',
            'type': 'bank',
            'code': 'STKPUSH',
        })
        self.till = self.env['dtb.moja.till'].create({
            'name': 'STK Push Till',
            'company_id': self.company.id,
            'till_number': '200002',
            'user_id': 'API_STK_PUSH',
            'password': 'stkpush123',
            'api_key': 'test_stk_api_key',
            'journal_id': self.journal.id,
        })

    def test_stk_push_request_fails_with_missing_till(self):
        with self.assertRaises(UserError):
            self.env['dtb.moja.validation']._stk_push_request(
                99999, 1500.0, '254790999957', 'INV/STK/001',
            )

    def test_stk_push_request_creates_pending_transaction(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response_data': {
                'response_code': '000',
                'checkout_request_id': 'ws_CO_DMZ_67890',
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_response):
            result = self.env['dtb.moja.validation']._stk_push_request(
                self.till.id, 2000.0, '254790999957', 'INV/STK/002',
                partner_name='STK Patient',
            )

        self.assertEqual(result['checkout_request_id'], 'ws_CO_DMZ_67890')

        tx = self.env['payment.transaction'].search([
            ('dtb_checkout_request_id', '=', 'ws_CO_DMZ_67890'),
        ])
        self.assertTrue(tx)
        self.assertEqual(tx.dtb_payment_method, 'stk_push')
        self.assertEqual(tx.amount, 2000.0)

    def test_stk_push_rejected_by_dtb(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response_data': {
                'response_code': '100',
                'response_description': 'INVALID AMOUNT',
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_response):
            with self.assertRaises(UserError):
                self.env['dtb.moja.validation']._stk_push_request(
                    self.till.id, -1, '254790999957', 'INV/BAD',
                )


class TestDtbStkCallback(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.partner = self.env['res.partner'].create({'name': 'STK Patient'})
        income = self.env['account.account'].create({
            'name': 'Test Income',
            'code': '400003',
            'account_type': 'income',
        })
        receivable = self.env['account.account'].create({
            'name': 'Test Receivable',
            'code': '100003',
            'account_type': 'asset_receivable',
        })
        transfer = self.env['account.account'].create({
            'name': 'Transfer',
            'code': '100098',
            'account_type': 'asset_current',
        })
        self.company.transfer_account_id = transfer
        self.partner.property_account_receivable_id = receivable
        stk_product = self.env['product.product'].create({
            'name': 'Consultation',
            'sale_ok': True,
            'lst_price': 3000.0,
        })
        stk_product.property_account_income_id = income
        sale_journal = self.env['account.journal'].create({
            'name': 'STK Sale Journal',
            'type': 'sale',
            'code': 'STKSALE',
            'company_id': self.company.id,
        })
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'payment_reference': 'INV/STK/CALLBACK',
            'journal_id': sale_journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': stk_product.id,
                'quantity': 1,
                'price_unit': 3000.0,
            })],
        })
        self.invoice.action_post()
        self.journal = self.env['account.journal'].create({
            'name': 'STK CB Journal',
            'type': 'bank',
            'code': 'STKCB',
        })
        self.till = self.env['dtb.moja.till'].create({
            'name': 'STK CB Till',
            'company_id': self.company.id,
            'till_number': '300001',
            'user_id': 'API_CB',
            'password': 'cbpass',
            'journal_id': self.journal.id,
        })
        self.provider = self.env['payment.provider'].sudo().create({
            'name': 'DTB Till Moja',
            'code': 'dtb',
            'state': 'test',
            'is_published': True,
        })
        method = self.env['payment.method'].sudo().search([], limit=1)
        self.tx = self.env['payment.transaction'].create({
            'provider_id': self.provider.id,
            'payment_method_id': method.id,
            'amount': 3000.0,
            'currency_id': self.company.currency_id.id,
            'partner_id': self.partner.id,
            'reference': 'TXN-EXT-STK-CALLBACK-TEST',
            'dtb_xref': 'EXT-STK-CALLBACK-TEST',
            'dtb_checkout_request_id': 'ws_CO_DMZ_CALLBACK_001',
            'dtb_till_id': self.till.id,
            'dtb_phone_number': '254790999957',
            'dtb_payment_method': 'stk_push',
            'dtb_customer_name': 'STK Patient',
            'operation': 'online_direct',
        })

    def _search_payment_tx(self, checkout_id):
        return self.env['payment.transaction'].search([
            ('dtb_checkout_request_id', '=', checkout_id),
        ], limit=1)

    def test_stk_callback_success_daraja_format(self):
        payload = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': '29115-34620561-1',
                    'CheckoutRequestID': 'ws_CO_DMZ_CALLBACK_001',
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully.',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 3000.0},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'RGH9876543'},
                            {'Name': 'PhoneNumber', 'Value': 254790999957},
                        ]
                    }
                }
            }
        }
        result = self.env['dtb.moja.validation']._process_stk_callback(payload)

        tx = self._search_payment_tx('ws_CO_DMZ_CALLBACK_001')
        self.assertEqual(tx.state, 'done')
        self.assertEqual(tx.provider_reference, 'RGH9876543')
        self.assertEqual(result['ack_code'], '00')
        self.assertEqual(result['ack_description'], 'SUCCESS')

    def test_stk_callback_idempotency(self):
        payload = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': 'ws_CO_DMZ_CALLBACK_001',
                    'ResultCode': 0,
                    'ResultDesc': 'SUCCESS',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 3000.0},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'RGH1111111'},
                        ]
                    }
                }
            }
        }
        self.env['dtb.moja.validation']._process_stk_callback(payload)
        result2 = self.env['dtb.moja.validation']._process_stk_callback(payload)

        txs = self.env['payment.transaction'].search([
            ('dtb_checkout_request_id', '=', 'ws_CO_DMZ_CALLBACK_001'),
        ])
        self.assertEqual(len(txs), 1)

    def test_stk_callback_failed_payment(self):
        payload = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': 'ws_CO_DMZ_CALLBACK_001',
                    'ResultCode': 1032,
                    'ResultDesc': 'Request cancelled by user',
                    'CallbackMetadata': {'Item': []},
                }
            }
        }
        result = self.env['dtb.moja.validation']._process_stk_callback(payload)

        tx = self._search_payment_tx('ws_CO_DMZ_CALLBACK_001')
        self.assertEqual(tx.state, 'error')
        self.assertEqual(tx.dtb_stk_result_code, '1032')

    def test_stk_callback_unknown_checkout_id(self):
        payload = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': 'ws_CO_UNKNOWN_999',
                    'ResultCode': 0,
                    'ResultDesc': 'SUCCESS',
                    'CallbackMetadata': {'Item': []},
                }
            }
        }
        result = self.env['dtb.moja.validation']._process_stk_callback(payload)
        self.assertEqual(result['ack_code'], '99')
        self.assertEqual(result['ack_description'], 'TRANSACTION_NOT_FOUND')

    def test_stk_callback_flat_format(self):
        payload = {
            'checkout_request_id': 'ws_CO_DMZ_CALLBACK_001',
            'result_code': '0',
            'mpesa_receipt': 'RGH5555555',
            'phone_number': '254790999957',
        }
        result = self.env['dtb.moja.validation']._process_stk_callback(payload)

        tx = self._search_payment_tx('ws_CO_DMZ_CALLBACK_001')
        self.assertEqual(tx.state, 'done')
        self.assertEqual(result['ack_code'], '00')
