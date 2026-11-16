import uuid
from unittest.mock import Mock, patch

from odoo.addons.amr_service_client.models import service_client as core_service_client
from odoo.addons.amr_sentry.models import service_client as sentry_hook
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestServiceClientHook(TransactionCase):

    def setUp(self):
        super(TestServiceClientHook, self).setUp()
        model = self.env['ir.model']._get('res.partner')
        self.credential = self.env['service.credential'].create({
            'name': 'Sentry dispatch test', 'source': 'database',
            'credential_json': '{"type":"api_key","header":"X-Test","value":"synthetic"}',
        })
        self.endpoint = self.env['service.endpoint'].create({
            'name': 'Sentry dispatch test', 'code': 'sentry_dispatch_test',
            'source': 'value', 'base_url_value': 'https://example.invalid/send',
            'credential_id': self.credential.id,
        })
        self.client = self.env['service.client'].create({
            'name': 'Sentry hook test', 'model_id': model.id,
            'endpoint_id': self.endpoint.id, 'credential_id': self.credential.id,
        })

    def _service_client(self, credential=None):
        return self.client.get_service_client(
            self.endpoint, credential=credential or self.credential, method='POST')

    def test_uncommitted_fixture_is_invisible_to_fresh_cursor_and_rolls_back(self):
        key = 'addons13_72.rollback.%s' % uuid.uuid4().hex

        def fresh_count():
            with self.env.registry.cursor() as cr:
                cr.execute(
                    'SELECT COUNT(*) FROM ir_config_parameter WHERE key = %s', (key,))
                return cr.fetchone()[0]

        baseline = fresh_count()
        self.assertEqual(baseline, 0)

        class RollbackFixture(Exception):
            pass

        with self.assertRaises(RollbackFixture):
            with self.env.cr.savepoint():
                self.env['ir.config_parameter'].create({'key': key, 'value': 'synthetic'})
                self.assertEqual(self.env['ir.config_parameter'].search_count([('key', '=', key)]), 1)
                self.assertEqual(fresh_count(), baseline)
                raise RollbackFixture()

        self.assertEqual(self.env['ir.config_parameter'].search_count([('key', '=', key)]), 0)
        self.assertEqual(fresh_count(), baseline)

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

    def test_dispatch_success_reports_through_orm_hook_and_creates_safe_log(self):
        response = Mock(text='synthetic response')
        reporter = Mock()
        payload = {'token': 'synthetic-token'}
        before_ids = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids
        sender = core_service_client.ServiceClientSend(
            self._service_client(), payload, active_log=True)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response) as request:
            result = sender.dispatch_send()

        self.assertIsNone(result)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args[1]['url'], 'https://example.invalid/send')
        self.assertEqual(request.call_args[1]['method'], 'POST')
        self.assertEqual(request.call_args[1]['json'], payload)
        reporter.report.assert_called_once_with(
            success=True, service_client=self.client, exception=None)
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', before_ids),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'done')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)

    def test_dispatch_success_without_active_log_reports_once_and_creates_no_log(self):
        response = Mock(text='synthetic response')
        reporter = Mock()
        dispatch_client = self._service_client()
        sender = core_service_client.ServiceClientSend(
            dispatch_client, {'value': 'synthetic'}, active_log=False)
        before_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response) as request:
            result = sender.dispatch_send()

        self.assertIsNone(result)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args[1]['url'], 'https://example.invalid/send')
        self.assertEqual(request.call_args[1]['method'], 'POST')
        self.assertEqual(request.call_args[1]['json'], {'value': 'synthetic'})
        reporter.report.assert_called_once_with(
            success=True, service_client=self.client, exception=None)
        after_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)
        self.assertEqual(after_ids, before_ids)

    def test_dispatch_preparation_error_logs_with_active_log_on_and_off(self):
        reporter = Mock()
        bad_credential = self.env['service.credential'].create({
            'name': 'Sentry dispatch invalid credential', 'source': 'database',
            'credential_json': '{"type":"api_key"}',
        })
        for active_log in (False, True):
            sender = core_service_client.ServiceClientSend(
                self._service_client(bad_credential),
                {'value': 'synthetic'}, active_log=active_log)
            log_model = self.env['service.client.log']
            before_ids = set(log_model.search([
                ('client_id', '=', self.client.id),
            ]).ids)

            with patch.object(sentry_hook, 'REPORTER', reporter), \
                    patch.object(core_service_client.requests, 'request') as request, \
                    mute_logger(core_service_client._logger.name):
                result = sender.dispatch_send()

            self.assertIsNone(result)
            request.assert_not_called()
            reporter.report.assert_called_once_with(
                success=False, service_client=self.client,
                exception=reporter.report.call_args[1]['exception'])
            self.assertIsInstance(reporter.report.call_args[1]['exception'], KeyError)
            rows = log_model.search([
                ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
            ])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows.state, 'error')
            self.assertFalse(rows.request_context)
            self.assertFalse(rows.response)
            reporter.reset_mock()

    def test_dispatch_transport_error_logs_with_active_log(self):
        error = RuntimeError('synthetic transport failure')
        reporter = Mock()
        dispatch_client = self._service_client()
        sender = core_service_client.ServiceClientSend(
            dispatch_client, {'value': 'synthetic'}, active_log=True)
        before_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             side_effect=error) as request, \
                mute_logger(core_service_client._logger.name):
            result = sender.dispatch_send()

        self.assertIsNone(result)
        request.assert_called_once()
        reporter.report.assert_called_once_with(
            success=False, service_client=self.client, exception=error)
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'error')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)

    def test_dispatch_http_error_logs_without_active_log(self):
        error = ValueError('synthetic HTTP failure')
        response = Mock(text='private synthetic response')
        response.raise_for_status.side_effect = error
        reporter = Mock()
        dispatch_client = self._service_client()
        sender = core_service_client.ServiceClientSend(
            dispatch_client, {'value': 'synthetic'}, active_log=False)
        before_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response) as request, \
                mute_logger(core_service_client._logger.name):
            result = sender.dispatch_send()

        self.assertIsNone(result)
        request.assert_called_once()
        reporter.report.assert_called_once_with(
            success=False, service_client=self.client, exception=error)
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'error')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)

    def test_dispatch_transport_error_logs_even_without_active_log(self):
        error = RuntimeError('synthetic transport failure')
        reporter = Mock()
        dispatch_client = self._service_client()
        sender = core_service_client.ServiceClientSend(
            dispatch_client, {'value': 'synthetic'}, active_log=False)
        before_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             side_effect=error) as request, \
                mute_logger(core_service_client._logger.name):
            result = sender.dispatch_send()

        self.assertIsNone(result)
        request.assert_called_once()
        reporter.report.assert_called_once_with(
            success=False, service_client=self.client, exception=error)
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'error')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)

    def test_dispatch_reporter_failure_does_not_change_log_outcome(self):
        response = Mock(text='synthetic response')
        reporter = Mock()
        reporter.report.side_effect = RuntimeError('synthetic reporter failure')
        sender = core_service_client.ServiceClientSend(
            self._service_client(), {'value': 'synthetic'}, active_log=True)
        before_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response), \
                self.assertLogs(sentry_hook.__name__, level='WARNING') as logs:
            result = sender.dispatch_send()

        self.assertIsNone(result)
        reporter.report.assert_called_once_with(
            success=True, service_client=self.client, exception=None)
        self.assertNotIn('synthetic reporter failure', '\n'.join(logs.output))
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'done')

    def test_dispatch_error_reporter_failure_keeps_error_log_and_safe_warning(self):
        error = RuntimeError('synthetic transport failure')
        reporter = Mock()
        reporter.report.side_effect = RuntimeError('synthetic reporter secret')
        dispatch_client = self._service_client()
        sender = core_service_client.ServiceClientSend(
            dispatch_client, {'value': 'synthetic'}, active_log=True)
        before_ids = set(self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             side_effect=error) as request, \
                self.assertLogs(sentry_hook.__name__, level='WARNING') as logs, \
                mute_logger(core_service_client._logger.name):
            result = sender.dispatch_send()

        self.assertIsNone(result)
        request.assert_called_once()
        reporter.report.assert_called_once_with(
            success=False, service_client=self.client, exception=error)
        self.assertNotIn('synthetic reporter secret', '\n'.join(logs.output))
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'error')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)

    def test_dispatch_success_writer_failure_uses_error_writer_once(self):
        writer_error = RuntimeError('synthetic done writer failure')
        response = Mock(text='synthetic response')
        reporter = Mock()
        log_model = self.env['service.client.log']
        original_create_log = type(log_model)._create_log
        done_writer_calls = []

        def fail_done_writer(records, state, *args, **kwargs):
            done_writer_calls.append(state)
            if state == 'done':
                raise writer_error
            return original_create_log(records, state, *args, **kwargs)

        error_writer = Mock(wraps=log_model._create_error)

        sender = core_service_client.ServiceClientSend(
            self._service_client(), {'value': 'synthetic'}, active_log=True)
        before_ids = set(log_model.search([
            ('client_id', '=', self.client.id),
        ]).ids)
        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response), \
                patch.object(type(log_model), '_create_log', new=fail_done_writer), \
                patch.object(type(log_model), '_create_error', new=error_writer), \
                mute_logger(core_service_client._logger.name):
            result = sender.dispatch_send()

        self.assertIsNone(result)
        self.assertEqual(done_writer_calls, ['done'])
        error_writer.assert_called_once()
        reporter.report.assert_called_once_with(
            success=True, service_client=self.client, exception=None)
        rows = log_model.search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'error')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)

    def test_dispatch_error_writer_failure_propagates_after_one_failure_report(self):
        error = RuntimeError('synthetic HTTP failure')
        writer_error = RuntimeError('synthetic error writer failure')
        response = Mock(text='synthetic response')
        response.raise_for_status.side_effect = error
        reporter = Mock()
        dispatch_client = self._service_client()
        sender = core_service_client.ServiceClientSend(
            dispatch_client, {'value': 'synthetic'}, active_log=False)
        log_model = self.env['service.client.log']
        before_ids = set(log_model.search([
            ('client_id', '=', self.client.id),
        ]).ids)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response), \
                patch.object(type(log_model), '_create_error', side_effect=writer_error) as error_writer, \
                mute_logger(core_service_client._logger.name):
            with self.assertRaises(RuntimeError) as caught:
                sender.dispatch_send()

        self.assertIs(caught.exception, writer_error)
        error_writer.assert_called_once()
        reporter.report.assert_called_once_with(
            success=False, service_client=self.client, exception=error)
        self.assertEqual(log_model.search([
            ('client_id', '=', self.client.id), ('id', 'not in', list(before_ids)),
        ]), log_model.browse())

    def test_dispatch_http_error_reports_same_exception_and_creates_error_log(self):
        response = Mock(text='private synthetic response')
        error = ValueError('synthetic HTTP failure')
        response.raise_for_status.side_effect = error
        reporter = Mock()
        payload = {'token': 'synthetic-token'}
        before_ids = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id),
        ]).ids
        sender = core_service_client.ServiceClientSend(
            self._service_client(), payload, active_log=True)

        with patch.object(sentry_hook, 'REPORTER', reporter), \
                patch.object(core_service_client.requests, 'request',
                             return_value=response) as request, \
                mute_logger(core_service_client._logger.name):
            result = sender.dispatch_send()

        self.assertIsNone(result)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args[1]['url'], 'https://example.invalid/send')
        self.assertEqual(request.call_args[1]['method'], 'POST')
        self.assertEqual(request.call_args[1]['json'], payload)
        reporter.report.assert_called_once_with(
            success=False, service_client=self.client, exception=error)
        rows = self.env['service.client.log'].search([
            ('client_id', '=', self.client.id), ('id', 'not in', before_ids),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.state, 'error')
        self.assertFalse(rows.request_context)
        self.assertFalse(rows.response)
