from unittest.mock import Mock, patch

from odoo.addons.amr_sentry.models import service_client as sentry_hook
from odoo.tests.common import TransactionCase


class TestServiceClientHook(TransactionCase):

    def setUp(self):
        super(TestServiceClientHook, self).setUp()
        model = self.env['ir.model']._get('res.partner')
        self.client = self.env['service.client'].create({
            'name': 'Sentry hook test', 'model_id': model.id,
        })

    def test_explicit_client_and_exception_are_forwarded(self):
        error = ValueError('synthetic error')
        other = self.env['service.client'].create({
            'name': 'Explicit Sentry client', 'model_id': self.client.model_id.id,
        })
        reporter = Mock()
        with patch.object(sentry_hook, 'REPORTER', reporter):
            self.client._report_sentry(
                service_client=other, exception=error,
                response='private response', method='private method')
        reporter.report.assert_called_once_with(
            success=False, service_client=other, exception=error)

    def test_singleton_defaults_to_self(self):
        reporter = Mock()
        with patch.object(sentry_hook, 'REPORTER', reporter):
            self.client._report_sentry()
        reporter.report.assert_called_once_with(
            success=True, service_client=self.client, exception=None)

    def test_empty_recordset_defaults_to_none(self):
        reporter = Mock()
        with patch.object(sentry_hook, 'REPORTER', reporter):
            self.env['service.client']._report_sentry()
        reporter.report.assert_called_once_with(
            success=True, service_client=None, exception=None)

    def test_reporter_failure_is_swallowed_and_secret_not_logged(self):
        reporter = Mock()
        reporter.report.side_effect = RuntimeError('synthetic-secret-marker')
        with patch.object(sentry_hook, 'REPORTER', reporter):
            with self.assertLogs(sentry_hook.__name__, level='WARNING') as logs:
                result = self.client._report_sentry()
        self.assertIsNone(result)
        reporter.report.assert_called_once_with(
            success=True, service_client=self.client, exception=None)
        self.assertNotIn('synthetic-secret-marker', '\n'.join(logs.output))

    def test_sentry_hook_is_registered_on_service_client(self):
        self.assertIn('service.client', self.env.registry.models)
        service_client = self.env['service.client']
        self.assertTrue(callable(getattr(type(service_client), '_report_sentry', None)))
