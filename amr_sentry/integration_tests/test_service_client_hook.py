from odoo.tests.common import TransactionCase


class TestServiceClientHook(TransactionCase):

    def test_sentry_hook_is_registered_on_service_client(self):
        self.assertIn('service.client', self.env.registry.models)
        service_client = self.env['service.client']
        self.assertTrue(callable(getattr(type(service_client), '_report_sentry', None)))
