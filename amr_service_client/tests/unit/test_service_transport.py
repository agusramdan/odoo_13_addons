"""Offline U03 client context/transport characterization; not ORM or security proof."""
import contextlib
import importlib.util
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import socket
import sys
import types
import unittest
from uuid import UUID
from unittest import mock

import requests


def load_client():
    addon = Path(__file__).resolve().parents[2]
    fields = types.ModuleType('odoo.fields')
    for name in ('Boolean', 'Char', 'Many2one', 'One2many', 'Text', 'Selection'):
        setattr(fields, name, lambda *args, **kwargs: None)
    fields.Date = fields.Datetime = types.SimpleNamespace(to_string=lambda value: value.isoformat(sep=' ') if isinstance(value, datetime) else value.isoformat())
    odoo = types.ModuleType('odoo')
    setattr(odoo, '_', lambda value: value)
    odoo.fields = fields
    odoo.models = types.SimpleNamespace(Model=type('Model', (), {}))
    setattr(odoo, 'api', types.SimpleNamespace(model=lambda fn: fn,
                                               returns=lambda *a, **kw: lambda fn: fn,
                                               constrains=lambda *a: lambda fn: fn))
    tools = types.ModuleType('odoo.tools')
    tools.config = {}
    odoo.tools = tools
    safe = types.ModuleType('odoo.tools.safe_eval')
    safe.safe_eval = safe.test_python_expr = lambda *a, **kw: None
    exceptions = types.ModuleType('odoo.exceptions')
    exceptions.UserError = type('UserError', (Exception,), {})
    exceptions.ValidationError = type('ValidationError', (Exception,), {})
    reporting = types.ModuleType('u03_transport.services.sentry_reporting')
    reporting.report_outcome = reporting.report_sentry = lambda *a, **kw: None
    modules = {'odoo': odoo, 'odoo.fields': fields, 'odoo.tools': tools,
               'odoo.tools.safe_eval': safe, 'odoo.exceptions': exceptions,
               'u03_transport.services.sentry_reporting': reporting}
    for name, path in (('u03_transport', addon), ('u03_transport.models', addon / 'models'),
                       ('u03_transport.services', addon / 'services')):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        modules[name] = package
    spec = importlib.util.spec_from_file_location('u03_transport.models.service_client', str(addon / 'models' / 'service_client.py'))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


production = load_client()


class Endpoint:
    credential_id = None
    active_log = False
    audience = 'default-audience'
    timeout = 17

    def __init__(self):
        self.paths = []

    def get_url(self, path):
        self.paths.append(path)
        return 'https://example.invalid/' + (path or 'default')

    def request_headers_default(self, headers):
        result = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        result.update(headers or {})
        return result


class TransportRegression(unittest.TestCase):
    def setUp(self):
        self.denied = []
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        def deny(*args, **kwargs):
            self.denied.append('attempt')
            raise RuntimeError('network denied')
        for obj, name in ((requests, 'request'), (requests, 'post'),
                          (requests.sessions.Session, 'request'),
                          (socket.socket, 'connect'), (socket.socket, 'connect_ex')):
            self.stack.enter_context(mock.patch.object(obj, name, deny))
        self.endpoint = Endpoint()
        self.provider = types.SimpleNamespace(authenticate=mock.Mock(side_effect=lambda context, audience=None: context))
        loader = types.SimpleNamespace(get_credential=mock.Mock(return_value=None))
        factory = types.SimpleNamespace(create_service_auth=mock.Mock(return_value=self.provider))
        self.client = production.ServiceClient({'service.credential.loader': loader,
                                               'service.auth.factory': factory},
                                              self.endpoint, None, path='stored', method='PUT')
        self.client._report_sentry = mock.Mock()
        factory.create_service_auth.assert_called_once_with(None)
        loader.get_credential.assert_called_once_with(None)

    def tearDown(self):
        self.assertEqual(self.denied, [])

    def assert_context_contract(self):
        payload = {'bytes': b'ab', 'decimal': Decimal('1.25'),
                   'nested': [date(2024, 2, 3), {'dt': datetime(2024, 2, 3, 4, 5, 6)}]}
        result = self.client.prepare_request_context(path='override', method='POST',
            params={'q': 'value'}, payload=payload, headers={'Accept': 'text/custom', 'X-Test': 'v'}, audience='override-audience')
        expected = {'url': 'https://example.invalid/override', 'method': 'POST',
                    'headers': {'Content-Type': 'application/json', 'Accept': 'text/custom', 'X-Test': 'v'},
                    'params': {'q': 'value'}, 'timeout': 17,
                    'json': {'bytes': 'YWI=', 'decimal': 1.25,
                             'nested': ['2024-02-03', {'dt': '2024-02-03 04:05:06'}]}}
        self.assertEqual(result, expected)
        self.assertEqual(self.endpoint.paths[-1], 'override')
        self.provider.authenticate.assert_called_with(expected, audience='override-audience')

    def test_context_overrides_and_normalization(self):
        self.assert_context_contract()

    def test_context_defaults_and_non_body_method(self):
        result = self.client.prepare_request_context(payload={'x': 1})
        self.assertEqual(result, {'url': 'https://example.invalid/stored', 'method': 'PUT',
            'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
            'timeout': 17, 'json': {'x': 1}})
        self.provider.authenticate.assert_called_with(result, audience='default-audience')
        result = self.client.prepare_request_context(path='read', method='GET', payload={'ignored': True})
        self.assertEqual(result['method'], 'GET')
        self.assertNotIn('json', result)
        self.assertEqual(result['url'], 'https://example.invalid/read')

    def test_context_includes_params_only_when_truthy(self):
        for arguments in ({}, {'params': None}, {'params': False},
                          {'params': {}}, {'params': []}, {'params': ''}, {'params': 0}):
            with self.subTest(arguments=arguments):
                result = self.client.prepare_request_context(method='GET', **arguments)
                self.assertNotIn('params', result)
                self.provider.authenticate.assert_called_with(result, audience='default-audience')
        params = {'page': 2}
        result = self.client.prepare_request_context(method='GET', params=params)
        self.assertEqual(result['params'], params)
        self.provider.authenticate.assert_called_with(result, audience='default-audience')

    def assert_call_contract(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        spy = mock.Mock(return_value=response)
        with mock.patch.object(requests, 'request', spy):
            actual = self.client.call(method='PATCH', path='items', params={'page': 2},
                payload={'amount': Decimal('3.5')}, headers={'X-Test': 'yes'}, audience='call-audience')
        self.assertIs(actual, response)
        spy.assert_called_once_with(url='https://example.invalid/items', method='PATCH',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Test': 'yes'},
            params={'page': 2}, timeout=17, json={'amount': 3.5})
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'call-audience')
        self.client._report_sentry.assert_called_once_with(response=response, method='PATCH')

    def test_call_reaches_transport_with_context(self):
        self.assert_call_contract()

    def test_transport_and_http_exceptions_pass_through(self):
        for kind in ('transport', 'http'):
            with self.subTest(kind=kind):
                error = requests.exceptions.Timeout('synthetic') if kind == 'transport' else requests.exceptions.HTTPError('synthetic')
                response = types.SimpleNamespace(raise_for_status=mock.Mock(side_effect=error if kind == 'http' else None))
                spy = mock.Mock(side_effect=error if kind == 'transport' else None, return_value=response)
                self.client._report_sentry.reset_mock()
                with mock.patch.object(requests, 'request', spy):
                    with self.assertRaises(type(error)) as caught:
                        self.client.call(method='GET', path='items')
                self.assertIs(caught.exception, error)
                self.assertEqual(spy.call_count, 1)
                self.assertEqual(response.raise_for_status.call_count, int(kind == 'http'))
                self.client._report_sentry.assert_called_once_with(exception=error, method='GET')

    def test_context_mutations_are_detected(self):
        original = production.ServiceClient.prepare_request_context
        def mutate(field):
            def altered(client, *args, **kwargs):
                result = original(client, *args, **kwargs)
                if field == 'audience':
                    client.provider.authenticate.reset_mock()
                    client.provider.authenticate(result, audience='wrong')
                elif field == 'json':
                    result['json'] = {}
                else:
                    result[field] = 'wrong'
                return result
            return altered
        for field in ('method', 'url', 'headers', 'params', 'timeout', 'json', 'audience'):
            with self.subTest(field=field):
                self.provider.authenticate.reset_mock()
                with mock.patch.object(production.ServiceClient, 'prepare_request_context', mutate(field)):
                    with self.assertRaises(AssertionError):
                        self.assert_context_contract()

    def test_call_mutation_dropping_payload_is_detected(self):
        original = production.ServiceClient.prepare_request_context
        def drop(client, *args, **kwargs):
            result = original(client, *args, **kwargs)
            result.pop('json', None)
            return result
        with mock.patch.object(production.ServiceClient, 'prepare_request_context', drop):
            with self.assertRaises(AssertionError):
                self.assert_call_contract()

    def test_guard_positive_controls(self):
        for invoke in (lambda: requests.request('GET', 'https://example.invalid'),
                       lambda: requests.post('https://example.invalid'),
                       lambda: requests.Session().request('GET', 'https://example.invalid')):
            with self.assertRaisesRegex(RuntimeError, 'network denied'):
                invoke()
        with socket.socket() as sock:
            for operation in (sock.connect, sock.connect_ex):
                with self.assertRaisesRegex(RuntimeError, 'network denied'):
                    operation(('127.0.0.1', 9))
        self.assertEqual(len(self.denied), 5)
        self.denied.clear()

    def test_call_forwards_audience_and_ignores_per_call_active_log(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        spy = mock.Mock(return_value=response)
        with mock.patch.object(requests, 'request', spy):
            self.client.call(method='PATCH', path='child/', payload={'x': 1},
                             active_log=True, audience='synthetic-audience')
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(spy.call_args[1]['method'], 'PATCH')
        self.assertNotIn('audience', spy.call_args[1])
        self.assertNotIn('active_log', spy.call_args[1])
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'synthetic-audience')

    def test_audience_override_fallback_and_absence(self):
        for supplied, expected in (('call-audience', 'call-audience'),
                                   (None, 'default-audience'),
                                   ('', 'default-audience')):
            with self.subTest(supplied=supplied):
                self.client.prepare_request_context(audience=supplied)
                self.assertEqual(self.provider.authenticate.call_args[1]['audience'], expected)
        setattr(self.endpoint, 'audience', None)
        self.client.prepare_request_context()
        self.assertEqual(self.provider.authenticate.call_args[1], {'audience': None})

    def test_required_audience_provider_receives_exact_fallback_values(self):
        received = []

        def authenticate(context, audience):
            received.append(audience)
            return context

        self.client.provider.authenticate = authenticate
        for endpoint_audience in (None, False, '', 'endpoint-audience'):
            self.endpoint.audience = endpoint_audience
            for supplied, expected in ((None, endpoint_audience),
                                       (False, endpoint_audience),
                                       ('', endpoint_audience),
                                       ('call-audience', 'call-audience')):
                with self.subTest(endpoint_audience=endpoint_audience, supplied=supplied):
                    result = self.client.prepare_request_context(audience=supplied)
                    self.assertIsInstance(result, dict)
                    self.assertEqual(received[-1], expected)

        self.client.endpoint = None
        for supplied, expected in ((None, None), (False, False), ('', ''),
                                   ('call-audience', 'call-audience')):
            with self.subTest(endpoint=None, supplied=supplied):
                self.client.prepare_request_context(audience=supplied)
                self.assertEqual(received[-1], expected)
        self.client.prepare_request_context()
        self.assertIsNone(received[-1])

    def test_prepare_payload_uses_client_logging_snapshot_and_preserves_payload_key(self):
        endpoint = Endpoint()
        endpoint.active_log = True
        client = production.ServiceClient(self.client.env, endpoint, None)
        endpoint.active_log = False

        sender = client.prepare_payload(active_log='payload value', item=3)

        self.assertTrue(sender.active_log)
        self.assertEqual(sender.payload, {'active_log': 'payload value', 'item': 3})
        endpoint.active_log = False
        self.assertTrue(sender.active_log)

        endpoint.active_log = False
        client = production.ServiceClient(self.client.env, endpoint, None)
        endpoint.active_log = True
        sender = client.prepare_payload(active_log='still payload')
        self.assertFalse(sender.active_log)
        self.assertEqual(sender.payload, {'active_log': 'still payload'})

    def test_prepared_sender_dispatch_logs_success_only_when_snapshot_is_on(self):
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(), _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        dispatch = mock.Mock(return_value=response)

        for active_log in (True, False):
            with self.subTest(active_log=active_log):
                self.endpoint.active_log = active_log
                client = production.ServiceClient(self.client.env, self.endpoint, None, path='stored', method='PUT')
                sender = client.prepare_payload(active_log='payload value', item=3)
                with mock.patch.object(requests, 'request', dispatch):
                    sender.dispatch_send()

                dispatch.assert_called_once()
                self.assertEqual(sender.payload, {'active_log': 'payload value', 'item': 3})
                self.assertEqual(log_writer._create_log.call_count, int(active_log))
                if active_log:
                    self.assertEqual(log_writer._create_log.call_args[0], ('done',))
                    self.assertEqual(log_writer._create_log.call_args[1]['response_text'], 'synthetic response')
                log_writer._create_log.reset_mock()
                dispatch.reset_mock()

        for active_log in (True, False):
            with self.subTest(active_log=active_log, outcome='error'):
                self.endpoint.active_log = active_log
                client = production.ServiceClient(self.client.env, self.endpoint, None, path='stored', method='PUT')
                sender = client.prepare_payload(active_log='payload value')
                error = requests.exceptions.Timeout('synthetic')
                transport = mock.Mock(side_effect=error)
                with mock.patch.object(requests, 'request', transport):
                    with mock.patch.object(production._logger, 'exception'):
                        sender.dispatch_send()
                transport.assert_called_once()
                log_writer._create_error.assert_called_once()
                self.assertIs(log_writer._create_error.call_args[0][0], error)
                self.assertEqual(log_writer._create_log.call_count, 0)
                log_writer._create_error.reset_mock()

        dispatch.assert_not_called()
        self.assertEqual(self.denied, [])

    def test_sender_constructor_preserves_direct_active_log_overrides(self):
        endpoint = Endpoint()
        endpoint.active_log = True
        service = types.SimpleNamespace(env={}, client_id='synthetic-client', endpoint_id=endpoint)

        self.assertFalse(production.ServiceClientSend(service, {}, endpoint_id=endpoint).active_log)
        self.assertTrue(production.ServiceClientSend(service, {}, active_log=True, endpoint_id=endpoint).active_log)
        self.assertFalse(production.ServiceClientSend(service, {}, active_log=False, endpoint_id=endpoint).active_log)
        self.assertTrue(production.ServiceClientSend(service, {}, active_log=None, endpoint_id=endpoint).active_log)
        endpoint.active_log = False
        self.assertTrue(production.ServiceClientSend(service, {}, active_log=True, endpoint_id=endpoint).active_log)
        self.assertFalse(production.ServiceClientSend(service, {}, active_log=None, endpoint_id=endpoint).active_log)

    def test_dispatch_uses_active_log_mutated_after_sender_creation(self):
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(), _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        sender = production.ServiceClientSend(self.client, {'item': 1}, active_log=False,
                                              endpoint_id=self.endpoint)
        sender.active_log = True
        with mock.patch.object(requests, 'request', return_value=response):
            sender.dispatch_send()
        log_writer._create_log.assert_called_once()
        self.assertEqual(log_writer._create_log.call_args[0], ('done',))
        self.assertEqual(log_writer._create_error.call_count, 0)
        self.assertFalse(self.endpoint.active_log)

        log_writer._create_log.reset_mock()
        sender = production.ServiceClientSend(self.client, {'item': 1}, active_log=True,
                                              endpoint_id=self.endpoint)
        sender.active_log = False
        with mock.patch.object(requests, 'request', return_value=response):
            sender.dispatch_send()
        self.assertEqual(log_writer._create_log.call_count, 0)
        self.assertEqual(log_writer._create_error.call_count, 0)
        self.assertFalse(self.endpoint.active_log)

    def test_dispatch_preparation_error_always_attempts_error_writer(self):
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(), _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        error = ValueError('synthetic preparation failure')
        self.client.prepare_request_context = mock.Mock(side_effect=error)
        for active_log in (True, False):
            with self.subTest(active_log=active_log):
                self.client._report_sentry.reset_mock()
                sender = production.ServiceClientSend(self.client, {}, active_log=active_log,
                                                      endpoint_id=self.endpoint)
                with mock.patch.object(requests, 'request') as transport:
                    with mock.patch.object(production._logger, 'exception'):
                        sender.dispatch_send()
                transport.assert_not_called()
                log_writer._create_error.assert_called_once()
                self.assertIs(log_writer._create_error.call_args[0][0], error)
                self.client._report_sentry.assert_called_once_with(
                    response=None, exception=error, method=None)
                log_writer._create_error.reset_mock()
        self.assertEqual(log_writer._create_log.call_count, 0)

    def test_dispatch_http_error_with_logging_on_reports_and_writes_error(self):
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(), _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        error = requests.exceptions.HTTPError('synthetic HTTP failure')
        response = types.SimpleNamespace(text='failure response',
            raise_for_status=mock.Mock(side_effect=error))
        with mock.patch.object(requests, 'request', return_value=response):
            with mock.patch.object(production._logger, 'exception'):
                production.ServiceClientSend(self.client, {}, active_log=True,
                    endpoint_id=self.endpoint).dispatch_send()
        self.client._report_sentry.assert_called_once_with(
            response=response, exception=error, method='PUT')
        log_writer._create_error.assert_called_once()
        self.assertIs(log_writer._create_error.call_args[0][0], error)
        self.assertEqual(log_writer._create_log.call_count, 0)

    def test_dispatch_contains_hook_failures_and_keeps_writer_behavior(self):
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(), _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        self.client._report_sentry.side_effect = RuntimeError('hook unavailable')
        with mock.patch.object(requests, 'request', return_value=response):
            production.ServiceClientSend(self.client, {'item': 1}, active_log=True,
                endpoint_id=self.endpoint).dispatch_send()
        log_writer._create_log.assert_called_once()
        self.assertEqual(log_writer._create_error.call_count, 0)

        log_writer._create_log.reset_mock()
        error = requests.exceptions.Timeout('synthetic transport failure')
        self.client._report_sentry.reset_mock(side_effect=True)
        self.client._report_sentry.side_effect = RuntimeError('hook unavailable')
        with mock.patch.object(requests, 'request', side_effect=error):
            with mock.patch.object(production._logger, 'exception'):
                production.ServiceClientSend(self.client, {}, active_log=False,
                    endpoint_id=self.endpoint).dispatch_send()
        self.client._report_sentry.assert_called_once_with(
            response=None, exception=error, method='PUT')
        log_writer._create_error.assert_called_once()
        self.assertEqual(log_writer._create_log.call_count, 0)

    def test_success_writer_failure_attempts_error_writer_without_second_hook(self):
        error = RuntimeError('success writer failed')
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(side_effect=error),
                                           _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        with mock.patch.object(requests, 'request', return_value=response):
            with mock.patch.object(production._logger, 'exception'):
                result = production.ServiceClientSend(self.client, {}, active_log=True,
                    endpoint_id=self.endpoint).dispatch_send()
        self.assertIsNone(result)
        log_writer._create_log.assert_called_once()
        log_writer._create_error.assert_called_once()
        self.assertIs(log_writer._create_error.call_args[0][0], error)
        self.client._report_sentry.assert_called_once_with(
            response=response, exception=None, method='PUT')

    def test_prepared_payload_keeps_active_log_key_through_transport(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        with mock.patch.object(requests, 'request', return_value=response) as transport:
            self.client.prepare_payload(active_log='payload value', item=3).dispatch_send()
        transport.assert_called_once()
        self.assertEqual(transport.call_args[1]['json'],
                         {'active_log': 'payload value', 'item': 3})

    def test_prepared_sender_attributes_resolved_credential(self):
        endpoint_credential = types.SimpleNamespace(id=13)
        override_credential = types.SimpleNamespace(id=14)
        cases = (
            ('credential-name', override_credential, override_credential, True, endpoint_credential),
            (override_credential, override_credential, override_credential, True, endpoint_credential),
            (None, endpoint_credential, endpoint_credential, True, endpoint_credential),
            (None, None, None, False, None),
        )
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        for supplied, resolved, loaded, should_load, endpoint_credential in cases:
            with self.subTest(supplied=supplied, resolved=resolved):
                endpoint = Endpoint()
                endpoint.active_log = True
                endpoint.credential_id = endpoint_credential
                loader = types.SimpleNamespace(
                    get_credential=mock.Mock(return_value=resolved),
                    load_credential=mock.Mock(return_value={'type': 'none'}),
                )
                provider = types.SimpleNamespace(authenticate=lambda context, audience=None: context)
                env = {
                    'service.credential.loader': loader,
                    'service.auth.factory': types.SimpleNamespace(
                        create_service_auth=mock.Mock(return_value=provider)),
                    'service.client.log': types.SimpleNamespace(
                        _create_log=mock.Mock(), _create_error=mock.Mock()),
                }
                client = production.ServiceClient(env, endpoint, supplied, path='stored', method='PUT')
                self.assertIs(client.credential, resolved)
                if should_load:
                    loader.load_credential.assert_called_once_with(loaded)
                else:
                    loader.load_credential.assert_not_called()
                with mock.patch.object(requests, 'request', return_value=response):
                    client.prepare_payload().dispatch_send()
                logged_credential = env['service.client.log']._create_log.call_args[1]['credential_id']
                self.assertIs(logged_credential, resolved)

    def test_direct_sender_credential_override_and_none_fallback_are_unchanged(self):
        endpoint_credential = types.SimpleNamespace(id=13)
        override_credential = types.SimpleNamespace(id=14)
        service = types.SimpleNamespace(env={}, client_id='synthetic-client',
                                        endpoint_id=types.SimpleNamespace(credential_id=endpoint_credential))

        override = production.ServiceClientSend(service, {}, endpoint_id=service.endpoint_id,
                                                credential_id=override_credential)
        fallback = production.ServiceClientSend(service, {}, endpoint_id=service.endpoint_id,
                                               credential_id=None)

        self.assertIs(override.credential_id, override_credential)
        self.assertIs(fallback.credential_id, endpoint_credential)

    def test_normalize_json_bytearray_uuid_and_unknown_fallback(self):
        unknown = types.SimpleNamespace()
        result = production.normalize_json({
            'bytes': bytearray(b'synthetic'),
            'uuid': UUID('12345678-1234-5678-1234-567812345678'),
            'unknown': unknown,
        })
        self.assertEqual(result['bytes'], 'c3ludGhldGlj')
        self.assertEqual(result['uuid'], '12345678-1234-5678-1234-567812345678')
        self.assertEqual(result['unknown'], str(unknown))


if __name__ == '__main__':
    unittest.main()
