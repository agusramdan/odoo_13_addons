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

    def test_d1_ambiguous_positional_arguments_fail_before_provider_or_transport(self):
        for invoke in (
            lambda: self.client.call('POST', 'orders', {}, {'x': 1}, {'X-Test': 'v'}),
            lambda: self.client.call('POST', 'orders', {}, {'x': 1}, {'X-Test': 'v'}, False),
            lambda: self.client.prepare_request_context('orders', 'POST', {}, {'x': 1}, {'X-Test': 'v'}),
        ):
            with self.subTest(invoke=invoke):
                before = self.provider.authenticate.call_count
                with mock.patch.object(requests, 'request') as transport:
                    with self.assertRaises(TypeError):
                        invoke()
                    transport.assert_not_called()
                self.assertEqual(self.provider.authenticate.call_count, before)
        with mock.patch.object(requests, 'request', return_value=None):
            result = self.client.call(method='POST', path='orders', payload={'x': 1},
                                      headers={'X-Test': 'v'}, raise_exception=False)
        self.assertIsNone(result)
        self.provider.authenticate.assert_called_once()

    def test_d2_endpoint_normalizer_receives_original_falsy_headers(self):
        normalize = mock.Mock(return_value={})
        self.endpoint.request_headers_default = normalize
        for supplied in (None, False, {}):
            with self.subTest(supplied=supplied):
                result = self.client.prepare_request_context(headers=supplied)
                self.assertNotIn('headers', result)
        self.assertEqual([call[0][0] for call in normalize.call_args_list], [None, False, {}])

    def test_d3_empty_effective_method_fails_before_provider(self):
        self.client.method = None
        before = self.provider.authenticate.call_count
        with self.assertRaisesRegex(ValueError, 'method'):
            self.client.prepare_request_context()
        self.assertEqual(self.provider.authenticate.call_count, before)

    def test_d4_reports_effective_provider_method_and_falls_back_before_context(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        self.client.provider.authenticate.side_effect = lambda context, audience=None: dict(context, method='PUT')
        with mock.patch.object(requests, 'request', return_value=response):
            self.client.call(method='POST')
        self.client._report_sentry.assert_called_once_with(response=response, method='PUT')

        self.client._report_sentry.reset_mock()
        response.raise_for_status.side_effect = RuntimeError('transport response failed')
        with mock.patch.object(requests, 'request', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'transport response failed'):
                self.client.call(method='POST')
        self.client._report_sentry.assert_called_once()
        self.assertEqual(self.client._report_sentry.call_args[1]['method'], 'PUT')

        self.client._report_sentry.reset_mock()
        self.client.provider.authenticate.side_effect = RuntimeError('prepare failed')
        with self.assertRaisesRegex(RuntimeError, 'prepare failed'):
            self.client.call(method='POST')
        self.client._report_sentry.assert_called_once()
        self.assertEqual(self.client._report_sentry.call_args[1]['method'], 'POST')

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

    def test_amendment_a01_a02_endpoint_url_override_and_fallback(self):
        self.endpoint.get_url = mock.Mock(return_value='https://example.invalid/fallback')
        result = self.client.prepare_request_context(
            url='https://override.invalid/exact', path='per-call')
        self.assertEqual(result['url'], 'https://override.invalid/exact')
        self.endpoint.get_url.assert_not_called()

        self.endpoint.get_url.reset_mock()
        result = self.client.prepare_request_context(url='', path='per-call')
        self.assertEqual(result['url'], 'https://example.invalid/fallback')
        self.endpoint.get_url.assert_called_once_with('per-call')

        self.endpoint.get_url.reset_mock()
        self.client.prepare_request_context(url=None, path='')
        self.endpoint.get_url.assert_called_once_with('stored')

        self.client.path = None
        self.endpoint.get_url = mock.Mock(return_value=None)
        result = self.client.prepare_request_context(url=None, path=None)
        self.assertNotIn('url', result)
        self.endpoint.get_url.assert_called_once_with(None)

    def test_amendment_a01_a03_without_endpoint_uses_only_truthy_url(self):
        self.client.endpoint = None
        result = self.client.prepare_request_context(
            url='https://override.invalid/exact', path='per-call')
        self.assertEqual(result['url'], 'https://override.invalid/exact')
        result = self.client.prepare_request_context(url=None, path='per-call')
        self.assertNotIn('url', result)
        result = self.client.prepare_request_context(url='', path='stored')
        self.assertNotIn('url', result)

    def test_amendment_a05_endpoint_header_defaults_and_empty_result(self):
        from test_endpoint_request import Endpoint as MixinEndpoint

        endpoint = MixinEndpoint(content_type='text/plain')
        endpoint.audience = 'default-audience'
        client = production.ServiceClient(self.client.env, endpoint, None, path='stored', method='PUT')
        for supplied in (None, {}):
            with self.subTest(supplied=supplied):
                result = client.prepare_request_context(headers=supplied)
                self.assertEqual(result['headers'], {
                    'Content-Type': 'text/plain', 'Accept': 'application/json'})
                self.provider.authenticate.assert_called_with(result, audience='default-audience')

        custom = {'Content-Type': 'application/json', 'X-Test': 'synthetic'}
        result = client.prepare_request_context(headers=custom)
        self.assertEqual(result['headers'], {
            'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Test': 'synthetic'})
        self.provider.authenticate.assert_called_with(result, audience='default-audience')

        normalize = mock.Mock(return_value={})
        self.endpoint.request_headers_default = normalize
        for supplied in (None, {'X-Test': 'synthetic'}):
            with self.subTest(empty_result_for=supplied):
                result = self.client.prepare_request_context(headers=supplied)
                self.assertNotIn('headers', result)
        self.assertEqual(normalize.call_args_list, [mock.call(None), mock.call({'X-Test': 'synthetic'})])

    def test_amendment_a05_without_endpoint_omits_only_falsy_headers(self):
        self.client.endpoint = None
        headers = {'X-Test': 'synthetic'}
        result = self.client.prepare_request_context(headers=headers)
        self.assertIs(result['headers'], headers)
        for supplied in (None, {}):
            with self.subTest(supplied=supplied):
                self.assertNotIn('headers', self.client.prepare_request_context(headers=supplied))

    def test_amendment_a06_characterizes_strict_provider_key_compatibility(self):
        self.client.endpoint = None
        for field, arguments in (('url', {'url': None}), ('headers', {'headers': None})):
            def require_key(context, audience=None, key=field):
                context[key]
                return context
            self.client.provider.authenticate = require_key
            with self.subTest(field=field):
                with self.assertRaises(KeyError):
                    self.client.prepare_request_context(**arguments)

    def test_amendment_a13_strict_headers_provider_key_error_with_valid_url(self):
        self.client.endpoint = None

        def require_headers(context, audience=None):
            context['headers']
            return context

        self.client.provider.authenticate = require_headers
        with self.assertRaises(KeyError) as raised:
            self.client.prepare_request_context(url='https://example.invalid/valid', headers=None)
        self.assertEqual(raised.exception.args, ('headers',))

    def test_amendment_a14_strict_url_provider_key_error(self):
        self.client.endpoint = None

        def require_url(context, audience=None):
            context['url']
            return context

        self.client.provider.authenticate = require_url
        with self.assertRaises(KeyError) as raised:
            self.client.prepare_request_context(url=None, method='GET')
        self.assertEqual(raised.exception.args, ('url',))

    def test_amendment_a07_provider_may_change_context_after_seam(self):
        self.client.endpoint = None
        observed_at_provider = []
        def authenticate(context, audience=None):
            observed_at_provider.append(dict(context))
            context['headers'] = {'Authorization': 'synthetic'}
            return context
        self.client.provider.authenticate = authenticate

        result = self.client.prepare_request_context(url='https://example.invalid', headers=None)

        self.assertNotIn('headers', observed_at_provider[0])
        self.assertEqual(result['headers'], {'Authorization': 'synthetic'})

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

    def test_call_forwards_audience_and_rejects_unknown_active_log_option(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        spy = mock.Mock(return_value=response)
        with mock.patch.object(requests, 'request', spy):
            self.client.call(method='PATCH', path='child/', payload={'x': 1},
                             audience='synthetic-audience')
        spy.assert_called_once()
        self.assertEqual(spy.call_args[1]['method'], 'PATCH')
        self.assertNotIn('audience', spy.call_args[1])
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'synthetic-audience')

        spy.reset_mock()
        before = self.provider.authenticate.call_count
        with self.assertRaises(TypeError):
            self.client.call(method='PATCH', active_log=True, raise_exception=False)
        spy.assert_not_called()
        self.assertEqual(self.provider.authenticate.call_count, before)

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

                error = requests.exceptions.Timeout('synthetic transport failure')
                with mock.patch.object(requests, 'request', side_effect=error):
                    with mock.patch.object(production._logger, 'exception'):
                        client.prepare_payload().dispatch_send()
                logged_credential = env['service.client.log']._create_error.call_args[1]['credential_id']
                self.assertIs(logged_credential, resolved)

    def test_prepared_sender_keeps_resolved_none_after_endpoint_credential_changes(self):
        original_credential = types.SimpleNamespace(id=13)
        self.endpoint.credential_id = None
        self.endpoint.active_log = True
        self.client.loader.get_credential.return_value = None
        self.client = production.ServiceClient(self.client.env, self.endpoint, None,
                                               path='stored', method='PUT')
        self.client._report_sentry = mock.Mock()
        self.assertIsNone(self.client.credential)
        self.endpoint.credential_id = original_credential

        log_writer = self.client.env['service.client.log'] = types.SimpleNamespace(
            _create_log=mock.Mock(), _create_error=mock.Mock())
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic response')
        with mock.patch.object(requests, 'request', return_value=response):
            sender = self.client.prepare_payload()
            self.assertIsNone(sender.credential_id)
            sender.dispatch_send()

        self.assertIsNone(self.client.env['service.auth.factory'].create_service_auth.call_args[0][0])
        self.client.provider.authenticate.assert_called_once()
        log_writer._create_log.assert_called_once()
        self.assertIsNone(log_writer._create_log.call_args[1]['credential_id'])

        error = requests.exceptions.Timeout('synthetic transport failure')
        with mock.patch.object(requests, 'request', side_effect=error):
            with mock.patch.object(production._logger, 'exception'):
                self.client.prepare_payload().dispatch_send()
        log_writer._create_error.assert_called_once()
        self.assertIs(log_writer._create_error.call_args[0][0], error)
        self.assertIsNone(log_writer._create_error.call_args[1]['credential_id'])

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


class FactoryWhitelistRegression(unittest.TestCase):
    def setUp(self):
        TransportRegression.setUp(self)
        self.addCleanup(TransportRegression.tearDown, self)

    def test_direct_call_and_preparation_reject_unknown_before_provider_even_when_suppressed(self):
        for invoke in (
            lambda: self.client.call(method="POST", unexpected_opt=1),
            lambda: self.client.call(method="POST", unexpected_opt=1, raise_exception=False),
            lambda: self.client.prepare_request_context(method="POST", unexpected_opt=1),
            lambda: self.client.get(unexpected_opt=1),
            lambda: self.client.post(unexpected_opt=1),
            lambda: self.client.put(unexpected_opt=1),
            lambda: self.client.delete(unexpected_opt=1),
        ):
            with self.subTest(invoke=invoke):
                before = self.provider.authenticate.call_count
                with self.assertRaises(TypeError):
                    invoke()
                self.assertEqual(self.provider.authenticate.call_count, before)

    def test_direct_wrappers_preserve_all_accepted_request_options(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        with mock.patch.object(requests, 'request', return_value=response) as transport:
            self.client.post('/p', payload={'v': 1}, params={'q': 'x'},
                             headers={'X-Test': 'h'}, url='https://override.invalid/x',
                             audience='aud', raise_exception=False)
        transport.assert_called_once()
        self.assertEqual(transport.call_args[1]['method'], 'POST')
        self.assertEqual(transport.call_args[1]['url'], 'https://override.invalid/x')
        self.assertEqual(transport.call_args[1]['params'], {'q': 'x'})
        self.assertEqual(transport.call_args[1]['json'], {'v': 1})
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'aud')

    def test_each_direct_wrapper_keeps_its_method_payload_and_common_options(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        cases = (
            ('GET', lambda **options: self.client.get('/p', **options), False),
            ('POST', lambda **options: self.client.post('/p', **options), True),
            ('PUT', lambda **options: self.client.put('/p', **options), True),
            ('DELETE', lambda **options: self.client.delete('/p', **options), False),
        )
        for method, invoke, sends_json in cases:
            with self.subTest(method=method):
                with mock.patch.object(requests, 'request', return_value=response) as transport:
                    invoke(params={'q': 'x'}, payload={'v': 1}, headers={'X-Test': 'h'},
                           url='https://override.invalid/x', audience='aud',
                           raise_exception=False)
                actual = transport.call_args[1]
                self.assertEqual(actual['method'], method)
                self.assertEqual(actual['url'], 'https://override.invalid/x')
                self.assertEqual(actual['params'], {'q': 'x'})
                if sends_json:
                    self.assertEqual(actual['json'], {'v': 1})
                else:
                    self.assertNotIn('json', actual)
                self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'aud')

    def test_direct_method_keyword_conflict_is_rejected(self):
        for invoke in (lambda: self.client.get(method='GET'),
                       lambda: self.client.post(method='POST'),
                       lambda: self.client.put(method='PUT'),
                       lambda: self.client.delete(method='DELETE')):
            with self.subTest(invoke=invoke):
                before = self.provider.authenticate.call_count
                with self.assertRaises(TypeError):
                    invoke()
                self.assertEqual(self.provider.authenticate.call_count, before)

    def test_remote_proxy_rejects_unknown_config_but_remote_data_remains_arbitrary(self):
        with self.assertRaises(TypeError):
            production.RemoteObjectProxy(self.client, 'res.partner', unexpected_opt=1)
        proxy = production.RemoteObjectProxy(self.client, 'res.partner',
            context={'lang': 'id'}, domain=[], fields=['name'], offset=0, limit=10, order='name')
        response = types.SimpleNamespace(raise_for_status=mock.Mock(),
                                         json=lambda: {'result': []})
        with mock.patch.object(self.client, 'post', return_value=response) as post:
            proxy.call('remote_method', [], {'custom_remote_kw': 1, 'nested': {'unknown': 2}})
        posted = post.call_args[1]
        self.assertEqual(posted['path'], '/api/dataset/call_kw')
        self.assertEqual(posted['payload']['params']['kwargs']['custom_remote_kw'], 1)
        self.assertEqual(posted['payload']['params']['kwargs']['nested'], {'unknown': 2})

    def test_sender_payload_keys_are_domain_data_not_request_options(self):
        sender = self.client.prepare_payload(active_log='data', unexpected_opt={'nested': 1})
        self.assertEqual(sender.payload,
                         {'active_log': 'data', 'unexpected_opt': {'nested': 1}})

    def test_model_call_factory_validates_before_client_creation_and_keeps_allowed_keys(self):
        model = production.ServiceClientModel()
        model.env = self.client.env
        model.get_service_client = mock.Mock(return_value=self.client)
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        with mock.patch.object(requests, 'request', return_value=response) as transport:
            model.call('svc', 'POST', '/p', {'q': 'x'}, {'v': 1}, {'X-Test': 'h'},
                       credential='cred', audience='aud', url='https://override.invalid/x',
                       raise_exception=False)
        model.get_service_client.assert_called_once_with('svc', credential='cred')
        transport.assert_called_once()
        self.assertEqual(transport.call_args[1]['method'], 'POST')
        self.assertEqual(transport.call_args[1]['url'], 'https://override.invalid/x')
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'aud')

        for extra in ({'unexpected_opt': 1},
                      {'unexpected_opt': 1, 'raise_exception': False}):
            model.get_service_client.reset_mock()
            with self.assertRaises(TypeError):
                model.call('svc', 'POST', **extra)
            model.get_service_client.assert_not_called()

    def test_model_call_eighth_positional_audience_is_rejected_with_migration_hint_doc(self):
        model = production.ServiceClientModel()
        model.get_service_client = mock.Mock(return_value=self.client)
        with self.assertRaises(TypeError):
            model.call('svc', 'POST', '/p', None, {'v': 1}, None, None, 'aud')
        model.get_service_client.assert_not_called()

    def test_model_wrappers_keep_their_declared_keyword_surfaces(self):
        model = production.ServiceClientModel()
        model.call = mock.Mock(return_value='response')
        self.assertEqual(model.get('svc', params={'q': 'x'}, headers=None,
                                  credential='cred', audience='aud'), 'response')
        model.call.assert_called_once_with(service='svc', method='GET', path=None,
            params={'q': 'x'}, headers=None, credential='cred', audience='aud')
        model.call.reset_mock()
        self.assertEqual(model.post('svc', payload={'v': 1}, audience='aud'), 'response')
        model.call.assert_called_once_with(service='svc', method='POST', path=None,
            payload={'v': 1}, headers=None, credential=None, audience='aud')
        model.call.reset_mock()
        self.assertEqual(model.put('svc', payload={'v': 1}), 'response')
        model.call.assert_called_once_with(service='svc', method='PUT', path=None,
            payload={'v': 1}, headers=None, credential=None, audience=None)
        model.call.reset_mock()
        self.assertEqual(model.delete('svc', None), 'response')
        model.call.assert_called_once_with(service='svc', method='DELETE', path=None,
            headers=None, credential=None, audience=None)
        for invoke in (lambda: model.get('svc', url='https://override.invalid'),
                       lambda: model.post('svc', params={}),
                       lambda: model.put('svc', raise_exception=False),
                       lambda: model.delete('svc', None, payload={})):
            with self.subTest(invoke=invoke):
                model.call.reset_mock()
                with self.assertRaises(TypeError):
                    invoke()
                model.call.assert_not_called()

    def test_model_factory_signature_rejects_unknown_before_constructor(self):
        model = production.ServiceClientModel()
        model.env = self.client.env
        model._get_endpoint = mock.Mock(return_value=self.endpoint)
        with mock.patch.object(production, 'ServiceClient') as constructor:
            client = model.get_service_client('svc', credential='cred', path='/stored', method='POST')
            self.assertIs(client, constructor.return_value)
            constructor.assert_called_once_with(model.env, self.endpoint, 'cred',
                service_client=model, path='/stored', method='POST')
            constructor.reset_mock()
            with self.assertRaises(TypeError):
                model.get_service_client('svc', unexpected_opt=1)
            constructor.assert_not_called()

    def test_remote_factory_accepts_exact_proxy_configuration(self):
        model = production.ServiceClientModel()
        model.env = self.client.env
        model._get_endpoint = mock.Mock(return_value=self.endpoint)
        with mock.patch.object(production, 'ServiceClient', return_value=self.client) as constructor:
            proxy = model.get_remote_object('svc', 'res.partner', context={'lang': 'id'},
                domain=[], fields=['name'], offset=0, limit=10, order='name')
        constructor.assert_called_once_with(model.env, self.endpoint, None, service_client=model)
        self.assertEqual((proxy.context, proxy.domain, proxy.fields, proxy.offset,
                          proxy.limit, proxy.order),
                         ({'lang': 'id'}, [], ['name'], 0, 10, 'name'))

    def test_remote_factory_rejects_unknown_config_before_client_creation(self):
        model = production.ServiceClientModel()
        model._get_endpoint = mock.Mock(return_value=self.endpoint)
        model.env = self.client.env
        with mock.patch.object(production, 'ServiceClient') as constructor:
            with self.assertRaises(TypeError):
                model.get_remote_object('svc', 'res.partner', unexpected_opt=1)
            constructor.assert_not_called()



    def test_direct_call_first_four_positionals_keep_their_binding(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        cases = (
            (('GET',), {'method': 'GET', 'url': 'https://example.invalid/stored'}),
            (('POST', 'items'), {'method': 'POST', 'url': 'https://example.invalid/items'}),
            (('POST', 'items', {'q': 'x'}),
             {'method': 'POST', 'url': 'https://example.invalid/items', 'params': {'q': 'x'}}),
            (('POST', 'items', {'q': 'x'}, {'v': 1}),
             {'method': 'POST', 'url': 'https://example.invalid/items',
              'params': {'q': 'x'}, 'json': {'v': 1}}),
        )
        for positional, expected in cases:
            with self.subTest(positional=positional):
                with mock.patch.object(requests, 'request', return_value=response) as transport:
                    self.client.call(*positional)
                if expected['method'] in ('POST', 'PUT', 'PATCH'):
                    expected.setdefault('json', None)
                expected.update(headers={
                    'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=17)
                transport.assert_called_once_with(**expected)

    def test_direct_duplicate_bindings_fail_before_provider_and_transport(self):
        invokes = (
            lambda: self.client.call('POST', method='POST'),
            lambda: self.client.call('POST', 'one', path='two'),
            lambda: self.client.call('POST', 'one', {'q': 1}, params={'q': 2}),
            lambda: self.client.call('POST', 'one', None, {'v': 1}, payload={'v': 2}),
            lambda: self.client.get('/p', path='/q'),
            lambda: self.client.get('/p', {'q': 1}, params={'q': 2}),
            lambda: self.client.post('/p', {'v': 1}, payload={'v': 2}),
            lambda: self.client.put('/p', {'v': 1}, payload={'v': 2}),
            lambda: self.client.delete('/p', path='/q'),
            lambda: self.client.prepare_request_context('one', path='two'),
            lambda: self.client.prepare_request_context('one', 'POST', method='GET'),
            lambda: self.client.prepare_request_context(
                'one', 'POST', {'q': 1}, params={'q': 2}),
            lambda: self.client.prepare_request_context(
                'one', 'POST', None, {'v': 1}, payload={'v': 2}),
        )
        for invoke in invokes:
            with self.subTest(invoke=invoke):
                before = self.provider.authenticate.call_count
                with mock.patch.object(requests, 'request') as transport:
                    with self.assertRaises(TypeError):
                        invoke()
                    transport.assert_not_called()
                self.assertEqual(self.provider.authenticate.call_count, before)

    def test_empty_method_reports_input_and_sender_writer_without_dispatch(self):
        self.client.method = None
        log_writer = types.SimpleNamespace(_create_log=mock.Mock(), _create_error=mock.Mock())
        self.client.env['service.client.log'] = log_writer
        for raise_exception in (True, False):
            with self.subTest(raise_exception=raise_exception):
                before = self.provider.authenticate.call_count
                with mock.patch.object(requests, 'request') as transport:
                    if raise_exception:
                        with self.assertRaisesRegex(ValueError, 'method'):
                            self.client.call(raise_exception=True)
                    else:
                        self.assertIsNone(self.client.call(raise_exception=False))
                    transport.assert_not_called()
                self.assertEqual(self.provider.authenticate.call_count, before)
                self.client._report_sentry.assert_called_with(exception=mock.ANY, method=None)
                for active_log in (True, False):
                    with self.subTest(active_log=active_log):
                        sender = production.ServiceClientSend(
                            self.client, {'item': 1}, active_log=active_log, endpoint_id=self.endpoint)
                        with mock.patch.object(requests, 'request') as transport:
                            with mock.patch.object(production._logger, 'exception'):
                                sender.dispatch_send()
                            transport.assert_not_called()
                        log_writer._create_error.assert_called_once()
                        self.assertIsInstance(log_writer._create_error.call_args[0][0], ValueError)
                        self.assertEqual(log_writer._create_log.call_count, 0)
                        log_writer._create_error.reset_mock()

    def test_model_wrapper_invalid_keys_never_construct_a_client(self):
        model = production.ServiceClientModel()
        model.env = self.client.env
        model.get_service_client = mock.Mock(return_value=self.client)
        cases = (
            ('get', ('svc',), ('payload', 'method', 'url', 'raise_exception', 'unexpected_opt')),
            ('post', ('svc',), ('params', 'method', 'url', 'raise_exception', 'unexpected_opt')),
            ('put', ('svc',), ('params', 'method', 'url', 'raise_exception', 'unexpected_opt')),
            ('delete', ('svc', '/p'),
             ('params', 'payload', 'method', 'url', 'raise_exception', 'unexpected_opt')),
        )
        for name, args, keys in cases:
            for key in keys:
                with self.subTest(wrapper=name, key=key):
                    model.get_service_client.reset_mock()
                    factory = self.client.env['service.auth.factory'].create_service_auth
                    before = factory.call_count
                    with mock.patch.object(requests, 'request') as transport:
                        with self.assertRaises(TypeError):
                            getattr(model, name)(*args, **{key: 1})
                        transport.assert_not_called()
                    model.get_service_client.assert_not_called()
                    self.assertEqual(factory.call_count, before)

    def test_action_eval_context_is_not_request_options_and_keeps_post_default(self):
        model = production.ServiceClientModel()
        model.ensure_one = mock.Mock()
        model.active = True
        model.each_record = False
        model.endpoint_id = self.endpoint
        model.credential_id = None
        records = object()
        action_context = {'records': records, 'opaque_eval_value': {'arbitrary': 7},
                          'audience': 'documented-but-not-forwarded'}
        model._get_eval_context = mock.Mock(return_value={'ctx': {}})
        model._run_action_iteration = mock.Mock(return_value={
            'ctx': {}, 'response': [{}]})
        model.prepare_request = mock.Mock(return_value={
            'url': None, 'path': None, 'method': None, 'params': None,
            'headers': None, 'payload': None, 'raise_exception': True,
            'audience': action_context['audience'],
        })
        client = types.SimpleNamespace(call=mock.Mock(return_value='response'),
                                       _report_sentry=mock.Mock())
        model.get_service_client = mock.Mock(return_value=client)
        model._run_action_handle = mock.Mock(return_value={})
        model.action_next_id = types.SimpleNamespace(
            with_context=lambda context: types.SimpleNamespace(run=mock.Mock(return_value=None)))

        model.run_action_service_client(eval_context=action_context)

        model.prepare_request.assert_called_once_with(records, {}, action_context)
        model.get_service_client.assert_called_once_with(self.endpoint, credential=None)
        client.call.assert_called_once_with(method='POST', path=None, params={}, payload={},
                                           headers={}, raise_exception=True, url=None)
        self.assertNotIn('audience', client.call.call_args[1])

    def test_sender_preserves_arbitrary_nested_domain_data_on_wire_without_changing_log_flag(self):
        payload = {'active_log': 'domain value', 'unexpected_opt': {'nested': [1, {'x': 2}]}}
        sender = self.client.prepare_payload(**payload)
        self.assertFalse(sender.active_log)
        response = types.SimpleNamespace(raise_for_status=mock.Mock(), text='synthetic')
        with mock.patch.object(requests, 'request', return_value=response) as transport:
            sender.dispatch_send()
        self.assertEqual(transport.call_args[1]['json'], payload)
        self.assertFalse(sender.active_log)

    def test_direct_wrappers_accept_omitted_none_and_explicit_paths(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        wrappers = (
            ('GET', self.client.get, {'params': {'q': 1}, 'payload': {'v': 1}}),
            ('POST', self.client.post, {'payload': {'v': 1}}),
            ('PUT', self.client.put, {'payload': {'v': 1}}),
            ('DELETE', self.client.delete, {'params': {'q': 1}, 'payload': {'v': 1}}),
        )
        for method, invoke, options in wrappers:
            for supplied, expected_url in ((Ellipsis, 'https://example.invalid/stored'),
                                           (None, 'https://example.invalid/stored'),
                                           ('/p', 'https://example.invalid//p')):
                with self.subTest(method=method, path=supplied):
                    self.endpoint.paths[:] = []
                    call_options = dict(options)
                    if supplied is not Ellipsis:
                        call_options['path'] = supplied
                    with mock.patch.object(requests, 'request', return_value=response) as transport:
                        invoke(**call_options)
                    self.assertEqual(transport.call_args[1]['method'], method)
                    self.assertEqual(transport.call_args[1]['url'], expected_url)
                    self.assertEqual('json' in transport.call_args[1], method in ('POST', 'PUT'))

    def test_each_direct_wrapper_unknown_and_method_conflict_stop_before_dispatch(self):
        invokes = (
            lambda: self.client.get(unexpected_opt=1),
            lambda: self.client.post(unexpected_opt=1),
            lambda: self.client.put(unexpected_opt=1),
            lambda: self.client.delete(unexpected_opt=1),
            lambda: self.client.get(method='GET'),
            lambda: self.client.post(method='POST'),
            lambda: self.client.put(method='PUT'),
            lambda: self.client.delete(method='DELETE'),
        )
        for invoke in invokes:
            with self.subTest(invoke=invoke):
                before = self.provider.authenticate.call_count
                with mock.patch.object(requests, 'request') as transport:
                    with self.assertRaises(TypeError):
                        invoke()
                    transport.assert_not_called()
                self.assertEqual(self.provider.authenticate.call_count, before)

    def test_model_call_duplicate_bindings_fail_before_factory(self):
        model = production.ServiceClientModel()
        model.get_service_client = mock.Mock(return_value=self.client)
        invokes = (
            lambda: model.call('svc', 'POST', method='POST'),
            lambda: model.call('svc', 'POST', '/p', path='/q'),
            lambda: model.call('svc', 'POST', '/p', {'q': 1}, params={'q': 2}),
            lambda: model.call('svc', 'POST', '/p', None, {'v': 1}, payload={'v': 2}),
        )
        for invoke in invokes:
            with self.subTest(invoke=invoke):
                with mock.patch.object(requests, 'request') as transport:
                    with self.assertRaises(TypeError):
                        invoke()
                    transport.assert_not_called()
                model.get_service_client.assert_not_called()

    def test_model_wrappers_preserve_omitted_none_and_explicit_paths(self):
        model = production.ServiceClientModel()
        model.call = mock.Mock(return_value='ok')
        cases = (
            (lambda: model.get('svc'), 'GET'),
            (lambda: model.get('svc', None), 'GET'),
            (lambda: model.get('svc', '/p'), 'GET'),
            (lambda: model.post('svc'), 'POST'),
            (lambda: model.post('svc', None), 'POST'),
            (lambda: model.post('svc', '/p'), 'POST'),
            (lambda: model.put('svc'), 'PUT'),
            (lambda: model.put('svc', None), 'PUT'),
            (lambda: model.put('svc', '/p'), 'PUT'),
            (lambda: model.delete('svc', None), 'DELETE'),
            (lambda: model.delete('svc', '/p'), 'DELETE'),
        )
        for invoke, expected_method in cases:
            with self.subTest(method=expected_method, invoke=invoke):
                model.call.reset_mock()
                self.assertEqual(invoke(), 'ok')
                self.assertEqual(model.call.call_args[1]['method'], expected_method)
                self.assertIn('path', model.call.call_args[1])
        model.call.reset_mock()
        with self.assertRaises(TypeError):
            model.delete('svc')
        model.call.assert_not_called()

    def test_preparation_and_call_reject_reserved_keys_before_provider_or_transport(self):
        invokes = (
            lambda: self.client.prepare_request_context(method='POST', credential='secret'),
            lambda: self.client.prepare_request_context(method='POST', raise_exception=False),
            lambda: self.client.prepare_request_context(method='POST', unexpected_opt=1),
            lambda: self.client.call(method='POST', credential='secret'),
            lambda: self.client.call(method='POST', unexpected_opt=1),
            lambda: self.client.call(method='POST', unexpected_opt=1, raise_exception=False),
        )
        for invoke in invokes:
            with self.subTest(invoke=invoke):
                before = self.provider.authenticate.call_count
                with mock.patch.object(requests, 'request') as transport:
                    with self.assertRaises(TypeError):
                        invoke()
                    transport.assert_not_called()
                self.assertEqual(self.provider.authenticate.call_count, before)

if __name__ == '__main__':
    unittest.main()
