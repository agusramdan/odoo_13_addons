import contextlib
import sys
import types
from unittest import mock

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import OfflineCase, load


class SentryBehaviorTests(OfflineCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sentry = load('services/sentry.py')
        cls.model = load('models/service_client.py')
        cls.log_model = load('models/service_client_log.py')

    def env(self, mode):
        params = types.SimpleNamespace(get_param=lambda key, default=None: mode)
        return {'ir.config_parameter': types.SimpleNamespace(sudo=lambda: params)}

    def sdk_mock(self):
        captured = []
        class Scope:
            def __init__(self): self.tags = {}
            def set_tag(self, key, value): self.tags[key] = value
        @contextlib.contextmanager
        def scope():
            current = Scope()
            yield current
            captured.append(current.tags)
        sdk = types.SimpleNamespace(push_scope=scope, capture_message=mock.Mock())
        return sdk, captured

    def test_modes_filtering_and_metadata_privacy(self):
        sdk, scopes = self.sdk_mock()
        client = types.SimpleNamespace(id=17, sentry_enabled=True)
        with mock.patch.dict(sys.modules, {'sentry_sdk': sdk}):
            self.sentry.capture_service_event(self.env('none'), 'service.client', None, 'error')
            self.sentry.capture_service_event(self.env('error'), 'service.client', None, 'done')
            self.sentry.capture_service_event(self.env('error'), 'service.client', None, 'error', error_type='Timeout')
            self.sentry.capture_service_event(self.env('selected'), 'service.client', None, 'error')
            self.sentry.capture_service_event(self.env('selected'), 'service.client', None, 'error', client_id=types.SimpleNamespace(id=18, sentry_enabled=False))
            self.sentry.capture_service_event(self.env('selected'), 'service.client', None, 'error', client_id=client, endpoint_id=9)
            self.sentry.capture_service_event(self.env('all'), 'service.client', 4, 'done')
        self.assertEqual(len(scopes), 3)
        self.assertEqual(sdk.capture_message.call_count, 3)
        self.assertNotIn('service_client.payload', str(scopes))
        self.assertEqual(scopes[0]['service_client.error_type'], 'Timeout')
        self.assertEqual(scopes[1]['service_client.client_id'], 17)
        self.assertEqual(scopes[2]['service_client.record_id'], 4)

    def test_reporting_failure_does_not_change_request_return_or_exception(self):
        client = object.__new__(self.model.ServiceClient)
        client.env, client.endpoint, client.client_id = self.env('error'), types.SimpleNamespace(id=3), None
        client.prepare_request_context = mock.Mock(return_value={'url': 'https://stub.invalid'})
        response = types.SimpleNamespace(status_code=200)
        sdk = types.SimpleNamespace(push_scope=mock.Mock(side_effect=RuntimeError('sentry down')))
        with mock.patch.dict(sys.modules, {'sentry_sdk': sdk}), mock.patch.object(self.model.requests, 'request', return_value=response):
            self.assertIs(client.call(), response)
        err = self.model.requests.ConnectionError('offline')
        with mock.patch.dict(sys.modules, {'sentry_sdk': sdk}):
            client.prepare_request_context.side_effect = err
            with self.assertRaises(self.model.requests.ConnectionError) as raised:
                client.call()
        self.assertIs(raised.exception, err)

    def test_http_non_2xx_is_returned_and_reported_as_error_without_raise(self):
        client = object.__new__(self.model.ServiceClient)
        client.env, client.endpoint, client.client_id = self.env('error'), types.SimpleNamespace(id=3), None
        client.prepare_request_context = mock.Mock(return_value={})
        response = types.SimpleNamespace(status_code=503)
        with mock.patch.object(self.model.requests, 'request', return_value=response), mock.patch.object(self.model, 'capture_service_event') as capture:
            self.assertIs(client.call(active_log=True), response)
        self.assertEqual(capture.call_args.args[3], 'error')

    def test_dispatch_send_logs_and_preserves_baseline_exception_handling(self):
        send = object.__new__(self.model.ServiceClientSend)
        send.active_log = False
        send.payload = {'safe': True}
        send.env = {'service.client.log': types.SimpleNamespace(
            sudo=lambda: types.SimpleNamespace(create_log=lambda state, **values: types.SimpleNamespace(
                id=51, values={'state': state, 'response': values['response_text'], **values})))}
        send.client_id = send.endpoint_id = send.credential_id = None
        send.service_client = types.SimpleNamespace(
            env=send.env, client_id=None, endpoint_id=None,
            prepare_request_context=mock.Mock(side_effect=ValueError('bad request setup')))
        with mock.patch.object(self.model, 'capture_service_event') as capture:
            record = send.dispatch_send()
        self.assertEqual(record.id, 51)
        self.assertEqual(record.values['state'], 'error')
        self.assertIn('ValueError', record.values['response'])
        capture.assert_called_once()
        self.assertEqual(capture.call_args.args[3], 'error')

    def test_dispatch_sentry_failure_does_not_change_original_result_or_exception_policy(self):
        send = object.__new__(self.model.ServiceClientSend)
        send.active_log = False
        send.payload = {}
        send.client_id = send.endpoint_id = send.credential_id = None
        send.env = {'service.client.log': types.SimpleNamespace(
            sudo=lambda: types.SimpleNamespace(create_log=lambda state, **values: types.SimpleNamespace(id=52)))}
        send.service_client = types.SimpleNamespace(env=send.env, client_id=None, endpoint_id=None,
            prepare_request_context=mock.Mock(side_effect=ValueError('caught as baseline')))
        sdk = types.SimpleNamespace(push_scope=mock.Mock(side_effect=RuntimeError('Sentry down')))
        send.env['ir.config_parameter'] = types.SimpleNamespace(
            sudo=lambda: types.SimpleNamespace(get_param=lambda *args: 'error'))
        with mock.patch.dict(sys.modules, {'sentry_sdk': sdk}):
            # The real reporting helper swallows SDK failures; dispatch_send retains
            # its baseline generic-exception handling and returns the created log.
            record = send.dispatch_send()
        self.assertEqual(record.id, 52)

    def test_service_client_log_send_updates_state_and_sentry_is_best_effort(self):
        log = object.__new__(self.log_model.ServiceClientLog)
        params = types.SimpleNamespace(get_param=lambda *args: 'error')
        log.env = {'ir.config_parameter': types.SimpleNamespace(sudo=lambda: params)}
        log.id = 81
        log.request_context = '{}'
        log.endpoint_id = types.SimpleNamespace(request_headers_default=lambda headers: headers, audience=None, id=2)
        log.credential_id = None
        log.client_id = types.SimpleNamespace(get_service_client=mock.Mock(side_effect=ValueError('bad replay')))
        log.write = mock.Mock()
        sdk = types.SimpleNamespace(push_scope=mock.Mock(side_effect=RuntimeError('Sentry down')))
        with mock.patch.dict(sys.modules, {'sentry_sdk': sdk}):
            result = log.send()
        self.assertIs(result, log)
        self.assertEqual(log.write.call_args.args[0]['state'], 'error')
