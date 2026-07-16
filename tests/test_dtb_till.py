from odoo.tests.common import TransactionCase


class TestDtbTillConfig(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.journal = self.env['account.journal'].create({
            'name': 'DTB Test Journal',
            'type': 'bank',
            'code': 'DTBTST',
            'company_id': self.company.id,
        })

    def test_till_creation_creates_record(self):
        till = self.env['dtb.moja.till'].create({
            'name': 'Parklands Branch Till',
            'company_id': self.company.id,
            'till_number': '100004',
            'user_id': 'API_M247',
            'password': 'qOw1EaF23xvf=',
            'channel': 'MBS',
            'journal_id': self.journal.id,
        })
        self.assertTrue(till)
        self.assertEqual(till.name, 'Parklands Branch Till')
        self.assertEqual(till.till_number, '100004')
        self.assertEqual(till.channel, 'MBS')
        self.assertTrue(till.is_active)

    def test_till_defaults_to_active(self):
        till = self.env['dtb.moja.till'].create({
            'name': 'Test Till',
            'company_id': self.company.id,
            'till_number': '100005',
            'user_id': 'API_TEST',
            'password': 'test123',
            'journal_id': self.journal.id,
        })
        self.assertTrue(till.is_active)
        self.assertEqual(till.channel, 'MBS')
