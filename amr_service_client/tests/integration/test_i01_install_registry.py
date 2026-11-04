from odoo.tests.common import TransactionCase


class TestI01InstallRegistry(TransactionCase):
    def test_module_and_registry(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'amr_service_client'),
        ])
        self.assertEqual(len(module), 1, 'Expected one addon module record')
        # During post-install testing Odoo can still be finalizing the module.
        self.assertIn(module.state, ('installed', 'to install', 'to upgrade'))

        expected_fields = {
            'service.endpoint': ('name', 'code', 'base_url', 'credential_id'),
            'service.credential': ('name', 'source', 'credential_json'),
            'service.client': ('name', 'endpoint_id', 'credential_id', 'payload_ids'),
            'service.client.payload': ('key', 'value', 'service_client_id'),
            'service.client.log': ('state', 'endpoint_id', 'client_id', 'response'),
            'ir.actions.server': ('service_client_id',),
            'service.credential.wizard': ('credential_type', 'generated_file'),
            'service.endpoint.test.wizard': ('endpoint_id', 'response_status'),
        }
        for model_name, field_names in expected_fields.items():
            self.assertIn(model_name, self.env.registry, model_name)
            model = self.env[model_name]
            for field_name in field_names:
                self.assertIn(field_name, model._fields, '%s.%s' % (model_name, field_name))
