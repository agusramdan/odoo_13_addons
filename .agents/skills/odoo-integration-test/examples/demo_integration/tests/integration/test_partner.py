from odoo.tests.common import TransactionCase

class TestPartnerIntegration(TransactionCase):
    def test_create_and_update_partner(self):
        partner = self.env['res.partner'].create({'name': 'Integration test partner'})
        partner.write({'name': 'Updated partner'})
        self.assertEqual(self.env['res.partner'].browse(partner.id).name, 'Updated partner')

    def test_wizard_like_transient_interaction(self):
        # Base transient configuration model exercises real registry and ORM.
        wizard = self.env['res.config.settings'].create({})
        self.assertTrue(wizard.id)
