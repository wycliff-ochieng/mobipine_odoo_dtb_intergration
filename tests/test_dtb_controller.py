from odoo.tests.common import TransactionCase
from odoo import fields


class TestDtbReferenceValidation(TransactionCase):

    def _create_invoice(self, ref, partner, product, price):
        income = self.env['account.account'].create({
            'name': 'Test Income',
            'code': '400001',
            'account_type': 'income',
        })
        receivable = self.env['account.account'].create({
            'name': 'Test Receivable',
            'code': '100001',
            'account_type': 'asset_receivable',
        })
        partner.property_account_receivable_id = receivable
        sale_journal = self.env['account.journal'].create({
            'name': 'Test Sale Journal',
            'type': 'sale',
            'code': 'TSJ',
            'company_id': self.env.ref('base.main_company').id,
        })
        product.property_account_income_id = income
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'payment_reference': ref,
            'journal_id': sale_journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1,
                'price_unit': price,
            })],
        })
        invoice.action_post()
        return invoice

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.partner = self.env['res.partner'].create({
            'name': 'Test Patient',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Service',
            'sale_ok': True,
            'lst_price': 1000.0,
        })
        self.invoice = self._create_invoice('INV/2026/001', self.partner, self.product, 1500.0)

    def test_validate_reference_matches_invoice(self):
        result = self.env['dtb.moja.validation']._validate_reference(
            '100004', 'INV/2026/001', 1500.0
        )
        self.assertEqual(result['till_number'], '100004')
        self.assertEqual(result['reference_id'], 'INV/2026/001')
        self.assertEqual(result['value_1'], 'Test Patient')
        self.assertEqual(result['value_2'], self.invoice.name)
        self.assertEqual(float(result['value_3']), 1500.0)

    def test_validate_reference_not_found(self):
        result = self.env['dtb.moja.validation']._validate_reference(
            '100004', 'NONEXISTENT', 100.0
        )
        self.assertIsNone(result)

    def test_validate_reference_amount_mismatch(self):
        result = self.env['dtb.moja.validation']._validate_reference(
            '100004', 'INV/2026/001', 500.0
        )
        self.assertIsNone(result)


class TestDtbCallbackProcessing(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.partner = self.env['res.partner'].create({
            'name': 'Callback Patient',
        })
        self.product = self.env['product.product'].create({
            'name': 'Consultation',
            'sale_ok': True,
            'lst_price': 2000.0,
        })

    def _search_payment_tx(self, xref):
        return self.env['payment.transaction'].search([
            ('dtb_xref', '=', xref),
        ], limit=1)

    def test_callback_creates_transaction_log(self):
        payload = {
            'xref': 'EXT-72D0D443-0A56-4197-A215-CB294F21A818',
            'cbs_reference': '110CDPO172380008',
            'amount': '1500',
            'customer_name': 'John Doe',
            'customer_mobile': '254700000000',
            'narration': 'INV/2026/001',
        }
        result = self.env['dtb.moja.validation']._process_callback_payload(payload)
        tx = self._search_payment_tx('EXT-72D0D443-0A56-4197-A215-CB294F21A818')
        self.assertTrue(tx)
        self.assertEqual(tx.amount, 1500.0)
        self.assertEqual(result['ack_code'], '00')

    def test_callback_idempotency(self):
        payload = {
            'xref': 'EXT-DEDUP-CALLBACK-001',
            'cbs_reference': 'CBS001',
            'amount': '500',
            'narration': 'TEST-001',
        }
        first = self.env['dtb.moja.validation']._process_callback_payload(payload)
        second = self.env['dtb.moja.validation']._process_callback_payload(payload)
        txs = self.env['payment.transaction'].search([
            ('dtb_xref', '=', 'EXT-DEDUP-CALLBACK-001'),
        ])
        self.assertEqual(len(txs), 1)

    def test_callback_matches_invoice_and_reconciles(self):
        income = self.env['account.account'].create({
            'name': 'Test Income',
            'code': '400002',
            'account_type': 'income',
        })
        receivable = self.env['account.account'].create({
            'name': 'Test Receivable',
            'code': '100002',
            'account_type': 'asset_receivable',
        })
        transfer = self.env['account.account'].create({
            'name': 'Transfer',
            'code': '100099',
            'account_type': 'asset_current',
        })
        self.company.transfer_account_id = transfer
        self.partner.property_account_receivable_id = receivable
        self.product.property_account_income_id = income
        sale_journal = self.env['account.journal'].create({
            'name': 'Test Sale Journal',
            'type': 'sale',
            'code': 'TSJ2',
            'company_id': self.company.id,
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'payment_reference': 'INV/2026/002',
            'journal_id': sale_journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 2000.0,
            })],
        })
        invoice.action_post()
        journal = self.env['account.journal'].create({
            'name': 'DTB Bank',
            'type': 'bank',
            'code': 'DTBBNK',
        })
        self.env['dtb.moja.till'].create({
            'name': 'Callback Till',
            'company_id': self.company.id,
            'till_number': '700007',
            'user_id': 'API_SYBN',
            'password': 'testpass',
            'journal_id': journal.id,
        })

        payload = {
            'xref': 'EXT-MATCH-INVOICE-001',
            'cbs_reference': 'CBS002',
            'amount': '2000',
            'account_number': '700007',
            'customer_name': 'Callback Patient',
            'customer_mobile': '254700000000',
            'narration': 'INV/2026/002',
        }
        result = self.env['dtb.moja.validation']._process_callback_payload(payload)

        tx = self._search_payment_tx('EXT-MATCH-INVOICE-001')
        self.assertEqual(tx.state, 'done')
        self.assertEqual(result['ack_code'], '00')
        self.assertEqual(result['ack_description'], 'SUCCESS')

    def test_callback_unmatched_reference_goes_to_mismatch(self):
        payload = {
            'xref': 'EXT-UNMATCHED-001',
            'cbs_reference': 'CBS003',
            'amount': '3000',
            'customer_name': 'Unknown',
            'narration': 'NO-INVOICE-REF',
        }
        result = self.env['dtb.moja.validation']._process_callback_payload(payload)

        tx = self._search_payment_tx('EXT-UNMATCHED-001')
        self.assertEqual(tx.state, 'done')
        self.assertEqual(result['ack_code'], '00')
        self.assertEqual(result['ack_description'], 'UNMATCHED_REFERENCE')
