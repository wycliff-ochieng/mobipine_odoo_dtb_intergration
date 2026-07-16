from odoo.tests.common import TransactionCase


class TestDtbTransactionLog(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.till = self.env['dtb.moja.till'].create({
            'name': 'Test Till',
            'company_id': self.company.id,
            'till_number': '100004',
            'user_id': 'API_M247',
            'password': 'qOw1EaF23xvf=',
            'journal_id': self.env['account.journal'].create({
                'name': 'Test Journal',
                'type': 'bank',
                'code': 'TEST',
            }).id,
        })

    def test_transaction_creation_from_callback_payload(self):
        tx = self.env['dtb.moja.transaction'].create({
            'xref': 'EXT-72D0D443-0A56-4197-A215-CB294F21A818',
            'cbs_reference': '110CDPO172380008',
            'amount': 1500.0,
            'customer_name': 'John Doe',
            'customer_mobile': '254700000000',
            'narration': 'INV/2026/001',
            'till_id': self.till.id,
        })
        self.assertTrue(tx)
        self.assertEqual(tx.xref, 'EXT-72D0D443-0A56-4197-A215-CB294F21A818')
        self.assertEqual(tx.amount, 1500.0)
        self.assertEqual(tx.state, 'draft')

    def test_transaction_default_state_is_draft(self):
        tx = self.env['dtb.moja.transaction'].create({
            'xref': 'EXT-UNIQUE-TEST-XREF-001',
            'amount': 500.0,
        })
        self.assertEqual(tx.state, 'draft')

    def test_transaction_unique_xref(self):
        self.env['dtb.moja.transaction'].create({
            'xref': 'EXT-DEDUP-TEST-001',
            'amount': 100.0,
        })
        with self.assertRaises(Exception):
            self.env['dtb.moja.transaction'].create({
                'xref': 'EXT-DEDUP-TEST-001',
                'amount': 200.0,
            })
