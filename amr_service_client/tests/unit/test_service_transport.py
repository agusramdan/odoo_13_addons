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
        self.provider = types.SimpleNamespace(authenticate=mock.Mock(side_effect=lambda context, audience: context))
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
            'params': None, 'timeout': 17, 'json': {'x': 1}})
        self.provider.authenticate.assert_called_with(result, audience='default-audience')
        result = self.client.prepare_request_context(path='read', method='GET', payload={'ignored': True})
        self.assertEqual(result['method'], 'GET')
        self.assertNotIn('json', result)
        self.assertEqual(result['url'], 'https://example.invalid/read')

    def assert_call_contract(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        spy = mock.Mock(return_value=response)
        with mock.patch.object(requests, 'request', spy):
            actual = self.client.call(method='PATCH', path='items', params={'page': 2},
                payload={'amount': Decimal('3.5')}, headers={'X-Test': 'yes'}, audience='ignored-by-call')
        self.assertIs(actual, response)
        spy.assert_called_once_with(url='https://example.invalid/items', method='PATCH',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Test': 'yes'},
            params={'page': 2}, timeout=17, json={'amount': 3.5})
        response.raise_for_status.assert_called_once_with()
        # Existing call() does not forward its audience argument: characterization, not policy.
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'default-audience')
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

    def test_call_ignores_per_call_active_log_and_audience_but_uses_method(self):
        response = types.SimpleNamespace(raise_for_status=mock.Mock())
        spy = mock.Mock(return_value=response)
        with mock.patch.object(requests, 'request', spy):
            self.client.call(method='PATCH', path='child/', payload={'x': 1},
                             active_log=True, audience='synthetic-audience')
        self.assertEqual(spy.call_count, 1)
        self.assertEqual(spy.call_args[1]['method'], 'PATCH')
        self.assertNotIn('audience', spy.call_args[1])
        self.assertNotIn('active_log', spy.call_args[1])
        self.assertEqual(self.provider.authenticate.call_args[1]['audience'], 'default-audience')

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
