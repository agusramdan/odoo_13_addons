"""U08: offline characterization of the existing proxy, not a new contract.

Odoo and HTTP are doubles; this does not establish ORM, RPC or UAT behavior.
"""
import contextlib
import importlib.util
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest import mock

import requests


def load_proxy():
    addon = Path(__file__).resolve().parents[2]
    field = lambda *args, **kwargs: None
    fields = types.ModuleType('odoo.fields')
    for name in ('Boolean', 'Char', 'Many2one', 'One2many', 'Text', 'Selection'):
        setattr(fields, name, field)
    fields.Date = fields.Datetime = types.SimpleNamespace(to_string=str)
    odoo = types.ModuleType('odoo')
    odoo.fields = fields
    odoo.models = types.SimpleNamespace(Model=type('Model', (), {}))
    odoo.api = types.SimpleNamespace(model=lambda fn: fn,
                                     constrains=lambda *args: lambda fn: fn)
    tools = types.ModuleType('odoo.tools')
    tools.config = {}
    odoo.tools = tools
    safe = types.ModuleType('odoo.tools.safe_eval')
    safe.safe_eval = safe.test_python_expr = lambda *args, **kwargs: None
    exceptions = types.ModuleType('odoo.exceptions')
    exceptions.UserError = type('UserError', (Exception,), {})
    exceptions.ValidationError = type('ValidationError', (Exception,), {})
    reporting = types.ModuleType('u08_isolated.services.sentry_reporting')
    reporting.report_outcome = reporting.report_sentry = lambda *args, **kwargs: None
    packages = {}
    for name, path in (('u08_isolated', addon), ('u08_isolated.models', addon / 'models'),
                       ('u08_isolated.services', addon / 'services')):
        packages[name] = types.ModuleType(name)
        packages[name].__path__ = [str(path)]
    modules = dict(packages, **{'odoo': odoo, 'odoo.fields': fields,
        'odoo.tools': tools, 'odoo.tools.safe_eval': safe, 'odoo.exceptions': exceptions,
        'u08_isolated.services.sentry_reporting': reporting})
    spec = importlib.util.spec_from_file_location('u08_isolated.models.service_client',
                                                   str(addon / 'models' / 'service_client.py'))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module.RemoteObjectProxy


Proxy = load_proxy()


class Response:
    def __init__(self, body=None, status_error=None, json_error=None):
        self.body = body
        self.status_error = status_error
        self.json_error = json_error
        self.calls = []

    def raise_for_status(self):
        self.calls.append('status')
        if self.status_error:
            raise self.status_error

    def json(self):
        self.calls.append('json')
        if self.json_error:
            raise self.json_error
        return self.body


class ProxyRegression(unittest.TestCase):
    def setUp(self):
        self.attempts = []
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        def deny(*args, **kwargs):
            self.attempts.append('network')
            raise RuntimeError('network denied')
        for obj, name in ((requests, 'request'), (requests, 'post'),
                          (requests.sessions.Session, 'request'),
                          (socket.socket, 'connect'), (socket.socket, 'connect_ex')):
            self.stack.enter_context(mock.patch.object(obj, name, deny))

    def tearDown(self):
        self.assertEqual(self.attempts, [])

    def test_explicit_call_preserves_legacy_argument_shapes(self):
        response = Response({'result': ['legacy-result']})
        client = types.SimpleNamespace(post=mock.Mock(return_value=response))
        proxy = Proxy(client, 'synthetic.model', context={'lang': 'en'})

        self.assertEqual(proxy.call('read', [4], {'limit': 3, 'context': {'tz': 'UTC'}}),
                         ['legacy-result'])

        client.post.assert_called_once_with(path='/api/dataset/call_kw',
            headers={'Content-Type': 'application/json'}, payload={
                'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                'params': {'model': 'synthetic.model', 'method': 'read',
                           'args': [4], 'kwargs': {
                               'limit': 3, 'context': {'lang': 'en', 'tz': 'UTC'}}}})
        self.assertEqual(response.calls, ['status', 'json'])

    def test_envelope_context_and_dynamic_method(self):
        response = Response({'result': [3]})
        client = types.SimpleNamespace(post=mock.Mock(return_value=response))
        proxy = Proxy(client, 'synthetic.model', context={'lang': 'en'})
        self.assertEqual(proxy.custom_method(4, flag=True, context={'tz': 'UTC'}), [3])
        client.post.assert_called_once_with(path='/api/dataset/call_kw',
            headers={'Content-Type': 'application/json'}, payload={
                'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                'params': {'model': 'synthetic.model', 'method': 'custom_method',
                           'args': (4,), 'kwargs': {'flag': True,
                           'context': {'lang': 'en', 'tz': 'UTC'}}}})
        self.assertEqual(response.calls, ['status', 'json'])
        self.assertEqual(proxy.context, {'lang': 'en', 'tz': 'UTC'})

    def assert_results(self):
        for result, expected in (([3], [3]), (0, []), (False, []), (None, [])):
            with contextlib.nullcontext():
                response = Response({'result': result})
                proxy = Proxy(types.SimpleNamespace(post=lambda **kw: response), 'm')
                self.assertEqual(proxy.call('x', [], {}), expected)

    def test_existing_result_characterization(self):
        self.assert_results()
        proxy = Proxy(types.SimpleNamespace(post=lambda **kw: Response({})), 'm')
        self.assertEqual(proxy.call('x', None), [])

    def test_http_json_and_envelope_errors_propagate(self):
        for kind in ('status', 'json', 'envelope'):
            with self.subTest(kind=kind):
                error = ValueError('synthetic')
                response = Response({'error': {'message': 'synthetic'}} if kind == 'envelope' else {},
                                    status_error=error if kind == 'status' else None,
                                    json_error=error if kind == 'json' else None)
                proxy = Proxy(types.SimpleNamespace(post=lambda **kw: response), 'm')
                if kind == 'envelope':
                    with self.assertRaisesRegex(RuntimeError, 'Odoo login error'):
                        proxy.call('x', [])
                else:
                    with self.assertRaises(ValueError) as caught:
                        proxy.call('x', [])
                    self.assertIs(caught.exception, error)
                self.assertEqual(response.calls, ['status'] if kind == 'status' else ['status', 'json'])

    def assert_fallbacks(self):
        defaults = {'domain': [('active', '=', True)], 'fields': ['name'],
                    'order': 'name', 'limit': 9, 'offset': 7}
        cases = {'domain': ([], [('id', '=', 4)]), 'fields': ([], ['id']),
                 'order': ('', 'id desc'), 'limit': (0, 3), 'offset': (0, 2)}
        for key, (empty, override) in cases.items():
            for label, supplied, constructor, expected in (
                    ('omitted', {}, defaults[key], defaults[key]),
                    ('none', {key: None}, defaults[key], defaults[key]),
                    ('falsey', {key: empty}, defaults[key], defaults[key]),
                    ('override', {key: override}, defaults[key], override),
                    ('empty-default', {key: empty}, empty, [] if key == 'domain' else empty)):
                with contextlib.nullcontext():
                    params = defaults.copy()
                    params[key] = constructor
                    proxy = Proxy(None, 'm', **params)
                    proxy.call = mock.Mock(return_value=['sentinel'])
                    self.assertEqual(proxy.search_read(**supplied), ['sentinel'])
                    expected_kw = defaults.copy()
                    expected_kw[key] = expected
                    proxy.call.assert_called_once_with('search_read', [], kwargs=expected_kw)

    def test_search_read_each_fallback_and_override(self):
        self.assert_fallbacks()

    def test_read_and_count_delegate(self):
        proxy = Proxy(None, 'm', fields=['name'], domain=[('active', '=', True)])
        proxy.call = mock.Mock(return_value=[3])
        self.assertEqual(proxy.read([1, 2], fields=[]), [3])
        proxy.call.assert_called_with('read', ([1, 2],), kwargs={'fields': ['name']})
        proxy.call.reset_mock()
        self.assertEqual(proxy.search_count(), [3])
        proxy.call.assert_called_once_with('search_count', args=[[('active', '=', True)]])

    def assert_pagination(self):
        proxy = Proxy(None, 'm', limit=2)
        proxy.search_count = mock.Mock(return_value=5)
        proxy.search_read = mock.Mock(side_effect=[[{'id': 1}, {'id': 2}],
                                                   [{'id': 3}, {'id': 4}], []])
        received = []
        self.assertIsNone(proxy.external_data_callback(lambda item, **kw: received.append((item, kw))))
        self.assertEqual(proxy.search_read.call_args_list, [mock.call(offset=0, limit=2),
                         mock.call(offset=2, limit=2), mock.call(offset=4, limit=2)])
        self.assertEqual(received, [({'id': n}, {'offset': n, 'total': 5}) for n in range(1, 5)])
        proxy.search_count.assert_called_once_with()

    def test_pagination_two_full_pages_then_empty(self):
        self.assert_pagination()

    def test_pagination_short_page_and_zero_count(self):
        proxy = Proxy(None, 'm', limit=2)
        proxy.search_count = mock.Mock(return_value=4)
        proxy.search_read = mock.Mock(return_value=[{'id': 1}])
        callback = mock.Mock()
        proxy.external_data_callback(callback)
        proxy.search_read.assert_called_once_with(offset=0, limit=2)
        callback.assert_called_once_with({'id': 1}, offset=1, total=4)
        proxy.search_count.return_value = []
        proxy.search_read.reset_mock()
        callback.reset_mock()
        proxy.external_data_callback(callback)
        proxy.search_read.assert_not_called()
        callback.assert_not_called()

    def test_callback_exception_propagates(self):
        proxy = Proxy(None, 'm', limit=2)
        proxy.search_count = mock.Mock(return_value=2)
        proxy.search_read = mock.Mock(return_value=[{'id': 1}, {'id': 2}])
        error = RuntimeError('synthetic callback')
        callback = mock.Mock(side_effect=error)
        with self.assertRaises(RuntimeError) as caught:
            proxy.external_data_callback(callback)
        self.assertIs(caught.exception, error)
        callback.assert_called_once_with({'id': 1}, offset=1, total=2)
        proxy.search_read.assert_called_once()

    def test_mutation_controls(self):
        original_call = Proxy.call
        def preserve_zero(self, method, args, kwargs=None):
            value = original_call(self, method, args, kwargs)
            return 0 if value == [] else value
        with mock.patch.object(Proxy, 'call', preserve_zero):
            with self.assertRaises(AssertionError):
                self.assert_results()
        original_search = Proxy.search_read
        def ignore_override(self, domain=None, fields=None, offset=0, limit=None, order=None):
            return original_search(self, domain=domain, fields=fields, offset=offset,
                                   limit=None, order=order)
        with mock.patch.object(Proxy, 'search_read', ignore_override):
            with self.assertRaises(AssertionError):
                self.assert_fallbacks()
        original_callback = Proxy.external_data_callback
        def wrong_total(self, callback):
            return original_callback(self, lambda item, **kw: callback(item, offset=kw['offset'], total=99))
        with mock.patch.object(Proxy, 'external_data_callback', wrong_total):
            with self.assertRaises(AssertionError):
                self.assert_pagination()

    def test_network_guard_positive_control(self):
        with self.assertRaisesRegex(RuntimeError, 'network denied'):
            requests.post('https://example.invalid')
        with socket.socket() as sock:
            with self.assertRaisesRegex(RuntimeError, 'network denied'):
                sock.connect(('127.0.0.1', 9))
        self.assertEqual(self.attempts, ['network', 'network'])
        self.attempts.clear()


if __name__ == '__main__':
    unittest.main()
