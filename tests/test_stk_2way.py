from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from unittest.mock import patch, MagicMock


class TestSettlementModeTill(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': '2Way Journal',
            'type': 'bank',
            'code': '2WAY',
        })

    def test_till_defaults_to_till_moja(self):
        till = self.env['dtb.moja.till'].create({
            'name': 'Default Till',
            'company_id': self.company.id,
            'till_number': '400001',
            'user_id': 'API_2WAY',
            'password': 'pass',
            'journal_id': self.journal.id,
        })
        self.assertEqual(till.settlement_mode, 'till_moja')

    def test_till_core_banking_with_account(self):
        till = self.env['dtb.moja.till'].create({
            'name': 'Bank Till',
            'company_id': self.company.id,
            'till_number': '400002',
            'user_id': 'API_2WAY',
            'password': 'pass',
            'journal_id': self.journal.id,
            'settlement_mode': 'core_banking',
            'account_source': 'CORE BANKING',
            'account_id': '0012870005',
        })
        self.assertEqual(till.settlement_mode, 'core_banking')
        self.assertEqual(till.account_source, 'CORE BANKING')
        self.assertEqual(till.account_id, '0012870005')

    def test_transaction_stores_settlement_mode(self):
        tx = self.env['dtb.moja.transaction'].create({
            'xref': 'EXT-SETTLE-TEST-001',
            'amount': 100.0,
            'payment_method': 'stk_push',
            'settlement_mode': 'core_banking',
        })
        self.assertEqual(tx.settlement_mode, 'core_banking')

    def test_payment_transaction_stores_dtb_settlement_mode(self):
        provider = self.env['payment.provider'].sudo().create({
            'name': 'Test DTB',
            'code': 'dtb',
            'state': 'test',
            'is_published': True,
        })
        partner = self.env['res.partner'].sudo().create({
            'name': 'Test',
            'company_id': self.company.id,
        })
        method = self.env['payment.method'].sudo().search([], limit=1)
        tx = self.env['payment.transaction'].sudo().create({
            'provider_id': provider.id,
            'payment_method_id': method.id,
            'amount': 100.0,
            'currency_id': self.company.currency_id.id,
            'partner_id': partner.id,
            'reference': 'EXT-PAY-TX-SETTLE',
            'dtb_settlement_mode': 'core_banking',
        })
        self.assertEqual(tx.dtb_settlement_mode, 'core_banking')


class TestC2BCallbackCoreBanking(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.partner = self.env['res.partner'].create({
            'name': 'CBS Patient',
            'company_id': self.company.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'CBS Service',
            'sale_ok': True,
            'lst_price': 2500.0,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'CBS Journal',
            'type': 'bank',
            'code': 'CBS',
        })
        self.till = self.env['dtb.moja.till'].create({
            'name': 'CBS Till',
            'company_id': self.company.id,
            'till_number': '500001',
            'user_id': 'API_CBS',
            'password': 'cbpass',
            'journal_id': self.journal.id,
            'settlement_mode': 'core_banking',
            'account_id': '0012870005',
        })

    def test_callback_lookup_till_by_account_id(self):
        payload = {
            'xref': 'EXT-CBS-ACC-LOOKUP',
            'cbs_reference': 'CBS_REF_001',
            'amount': '1000',
            'account_number': '0012870005',
            'customer_name': 'Test',
            'customer_mobile': '254700000000',
            'narration': 'TEST-CBS',
        }
        result = self.env['dtb.moja.validation']._process_callback_payload(payload)
        self.assertEqual(result['ack_code'], '00')
        tx = self.env['payment.transaction'].sudo().search([
            ('dtb_xref', '=', 'EXT-CBS-ACC-LOOKUP'),
        ], limit=1)
        self.assertTrue(tx)
        self.assertEqual(tx.dtb_settlement_mode, 'core_banking')
        self.assertEqual(tx.dtb_till_id, self.till)

    def test_callback_matches_invoice_by_cbs_reference(self):
        income = self.env['account.account'].create({
            'name': 'CBS Income',
            'code': '400004',
            'account_type': 'income',
        })
        receivable = self.env['account.account'].create({
            'name': 'CBS Receivable',
            'code': '100004',
            'account_type': 'asset_receivable',
        })
        transfer = self.env['account.account'].create({
            'name': 'Transfer',
            'code': '100097',
            'account_type': 'asset_current',
        })
        self.company.transfer_account_id = transfer
        self.partner.property_account_receivable_id = receivable
        self.product.property_account_income_id = income
        sale_journal = self.env['account.journal'].create({
            'name': 'CBS Sale Journal',
            'type': 'sale',
            'code': 'CBSSALE',
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'payment_reference': 'CBS_REF_002',
            'journal_id': sale_journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 2500.0,
            })],
        })
        invoice.action_post()
        payload = {
            'xref': 'EXT-CBS-INV-MATCH',
            'cbs_reference': 'CBS_REF_002',
            'amount': '2500',
            'account_number': '0012870005',
            'customer_name': 'CBS Patient',
            'customer_mobile': '254700000000',
            'narration': 'some random note',
        }
        result = self.env['dtb.moja.validation']._process_callback_payload(payload)
        self.assertEqual(result['ack_code'], '00')
        self.assertEqual(result['ack_description'], 'SUCCESS')

    def test_callback_unmatched_cbs_goes_to_mismatch(self):
        payload = {
            'xref': 'EXT-CBS-MISMATCH',
            'cbs_reference': 'CBS_NONEXISTENT',
            'amount': '3000',
            'account_number': '0012870005',
            'customer_name': 'Unknown',
            'customer_mobile': '254700000000',
            'narration': 'NO-INVOICE-FOR-THIS',
        }
        result = self.env['dtb.moja.validation']._process_callback_payload(payload)
        self.assertEqual(result['ack_code'], '00')
        self.assertEqual(result['ack_description'], 'UNMATCHED_REFERENCE')


class TestStkPushSettlementMode(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': 'STK 2Way Journal',
            'type': 'bank',
            'code': 'STK2W',
        })
        self.till = self.env['dtb.moja.till'].create({
            'name': 'STK 2Way Till',
            'company_id': self.company.id,
            'till_number': '600001',
            'user_id': 'API_STK2W',
            'password': 'stk2wpass',
            'api_key': 'stk2w_key',
            'journal_id': self.journal.id,
            'settlement_mode': 'core_banking',
            'account_id': '0012870006',
        })

    def test_stk_push_stores_settlement_mode_from_param(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response_data': {
                'response_code': '000',
                'checkout_request_id': 'ws_CO_2WAY_001',
            }
        }
        mock_response.raise_for_status = MagicMock()
        with patch('requests.post', return_value=mock_response):
            result = self.env['dtb.moja.validation']._stk_push_request(
                self.till.id, 2000.0, '254790999957', 'INV/2WAY/001',
                partner_name='2Way Patient',
                settlement_mode='till_moja',
            )
        tx = self.env['payment.transaction'].sudo().search([
            ('dtb_checkout_request_id', '=', 'ws_CO_2WAY_001'),
        ], limit=1)
        self.assertTrue(tx)
        self.assertEqual(tx.dtb_settlement_mode, 'till_moja')

    def test_stk_push_defaults_settlement_from_till(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response_data': {
                'response_code': '000',
                'checkout_request_id': 'ws_CO_2WAY_002',
            }
        }
        mock_response.raise_for_status = MagicMock()
        with patch('requests.post', return_value=mock_response):
            result = self.env['dtb.moja.validation']._stk_push_request(
                self.till.id, 1500.0, '254790999957', 'INV/2WAY/002',
                partner_name='2Way Patient',
            )
        tx = self.env['payment.transaction'].sudo().search([
            ('dtb_checkout_request_id', '=', 'ws_CO_2WAY_002'),
        ], limit=1)
        self.assertTrue(tx)
        self.assertEqual(tx.dtb_settlement_mode, 'core_banking')


class TestStkCallbackCoreBanking(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.partner = self.env['res.partner'].create({
            'name': 'STK CB Patient',
            'company_id': self.company.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'STK CB Service',
            'sale_ok': True,
            'lst_price': 4000.0,
        })
        income = self.env['account.account'].create({
            'name': 'STK CB Income',
            'code': '400005',
            'account_type': 'income',
        })
        receivable = self.env['account.account'].create({
            'name': 'STK CB Receivable',
            'code': '100005',
            'account_type': 'asset_receivable',
        })
        transfer = self.env['account.account'].create({
            'name': 'Transfer',
            'code': '100096',
            'account_type': 'asset_current',
        })
        self.company.transfer_account_id = transfer
        self.partner.property_account_receivable_id = receivable
        self.product.property_account_income_id = income
        sale_journal = self.env['account.journal'].create({
            'name': 'STK CB Sale Journal',
            'type': 'sale',
            'code': 'STKCL',
        })
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'payment_reference': 'INV/STK/CB/001',
            'journal_id': sale_journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 4000.0,
            })],
        })
        self.invoice.action_post()
        self.journal = self.env['account.journal'].sudo().create({
            'name': 'STK CB Journal',
            'type': 'bank',
            'code': 'STKCS',
            'default_account_id': transfer.id,
        })
        self.till = self.env['dtb.moja.till'].create({
            'name': 'STK CB Till',
            'company_id': self.company.id,
            'till_number': '700001',
            'user_id': 'API_STKCB',
            'password': 'stkcbpass',
            'journal_id': self.journal.id,
        })
        self.tx = self.env['dtb.moja.transaction'].create({
            'xref': 'EXT-STK-CB-CALLBACK',
            'amount': 4000.0,
            'customer_name': 'STK CB Patient',
            'customer_mobile': '254790999957',
            'narration': 'INV/STK/CB/001',
            'till_id': self.till.id,
            'payment_method': 'stk_push',
            'state': 'pending_stk',
            'checkout_request_id': 'ws_CO_CB_CALLBACK_001',
        })

    def test_stk_callback_core_banking_matches_by_provider_reference(self):
        provider = self.env['payment.provider'].sudo().create({
            'name': 'DTB',
            'code': 'dtb',
            'state': 'test',
            'is_published': True,
        })
        method = self.env['payment.method'].sudo().search([], limit=1)
        ptx = self.env['payment.transaction'].sudo().create({
            'provider_id': provider.id,
            'payment_method_id': method.id,
            'amount': 4000.0,
            'currency_id': self.company.currency_id.id,
            'partner_id': self.partner.id,
            'reference': 'EXT-REF-CB-001',
            'dtb_xref': 'EXT-STK-CB-CALLBACK',
            'dtb_checkout_request_id': 'ws_CO_CB_CALLBACK_001',
            'dtb_payment_method': 'stk_push',
            'dtb_settlement_mode': 'core_banking',
            'provider_reference': 'INV/STK/CB/001',
        })
        payload = {
            'Body': {
                'stkCallback': {
                    'MerchantRequestID': '29115-34620561-1',
                    'CheckoutRequestID': 'ws_CO_CB_CALLBACK_001',
                    'ResultCode': 0,
                    'ResultDesc': 'SUCCESS',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 4000.0},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'RGH_CB_001'},
                            {'Name': 'PhoneNumber', 'Value': 254790999957},
                        ]
                    }
                }
            }
        }
        result = self.env['dtb.moja.validation']._process_stk_callback(payload)
        self.assertEqual(result['ack_code'], '00')


class TestAutoCreateProvider(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')

    def test_dtb_create_transaction_uses_existing_provider(self):
        partner = self.env['res.partner'].sudo().create({
            'name': 'Auto Tx',
            'company_id': self.company.id,
        })
        tx = self.env['payment.transaction'].sudo()._dtb_create_transaction({
            'amount': 500.0,
            'partner_id': partner.id,
            'reference': 'EXT-AUTO-PROV',
            'dtb_xref': 'EXT-AUTO-PROV',
        })
        self.assertTrue(tx)
        self.assertTrue(tx.provider_id)
        self.assertEqual(tx.provider_id.code, 'dtb')

    def test_dtb_create_transaction_fallback_partner(self):
        tx = self.env['payment.transaction'].sudo()._dtb_create_transaction({
            'amount': 300.0,
            'reference': 'EXT-NO-PARTNER',
            'dtb_xref': 'EXT-NO-PARTNER',
        })
        self.assertTrue(tx)
        self.assertTrue(tx.partner_id)
        self.assertEqual(tx.partner_id.name, 'Unreconciled DTB Customer')

    def test_dtb_create_transaction_fallback_currency(self):
        partner = self.env['res.partner'].sudo().create({
            'name': 'Curr Tx',
            'company_id': self.company.id,
        })
        tx = self.env['payment.transaction'].sudo()._dtb_create_transaction({
            'amount': 100.0,
            'partner_id': partner.id,
            'reference': 'EXT-CURR-FALLBACK',
            'dtb_xref': 'EXT-CURR-FALLBACK',
        })
        self.assertTrue(tx)
        self.assertTrue(tx.currency_id)

    def test_dtb_create_transaction_auto_creates_provider_when_missing(self):
        partner = self.env['res.partner'].sudo().create({
            'name': 'Auto Create',
            'company_id': self.company.id,
        })
        with patch.object(self.env['payment.provider'].sudo().__class__, 'search') as mock_search:
            mock_search.return_value = self.env['payment.provider'].sudo()
            tx = self.env['payment.transaction'].sudo()._dtb_create_transaction({
                'amount': 200.0,
                'partner_id': partner.id,
                'reference': 'EXT-AUTO-CREATE',
                'dtb_xref': 'EXT-AUTO-CREATE',
            })
        self.assertTrue(tx)
        self.assertTrue(tx.provider_id)
        self.assertEqual(tx.provider_id.code, 'dtb')
