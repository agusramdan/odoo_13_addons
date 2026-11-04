"""Offline U03 slice: existing endpoint URL and header behavior only.

Odoo is doubled; the process-local network guard is not a native/child monitor.
"""
import importlib.util
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest import mock

import requests


def load_endpoint():
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(depends=lambda *args: lambda method: method)
    odoo.fields = types.SimpleNamespace(**{
        name: (lambda *args, **kwargs: None)
        for name in ("Char", "Selection", "Many2one", "Integer", "Boolean")
    })
    odoo.models = types.SimpleNamespace(AbstractModel=type("AbstractModel", (), {}),
                                        Model=type("Model", (), {}))
    tools = types.ModuleType("odoo.tools")
    tools.config = {}
    odoo.tools = tools
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    path = Path(__file__).resolve().parents[2] / "models" / "service_endpoint.py"
    spec = importlib.util.spec_from_file_location("isolated_service_endpoint", str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.tools": tools,
                                      "odoo.exceptions": exceptions}):
        spec.loader.exec_module(module)
    return module


endpoint_module = load_endpoint()


class Endpoint(endpoint_module.ServiceEndpointMixin):
    def __init__(self, base_url="https://example.invalid/", base_path="/api/v1/",
                 url="https://example.invalid/api/v1", content_type="application/json",
                 present=True):
        self.base_url = base_url
        self.base_path = base_path
        self.url = url
        self.content_type_default = content_type
        self.present = present

    def __bool__(self):
        return self.present


class EndpointRegression(unittest.TestCase):
    def setUp(self):
        self.attempts = []
        def deny(*args, **kwargs):
            self.attempts.append("network")
            raise RuntimeError("network denied")
        self.stack = __import__("contextlib").ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch.object(requests, "post", deny))
        self.stack.enter_context(mock.patch.object(requests, "request", deny))
        self.stack.enter_context(mock.patch.object(requests.sessions.Session, "request", deny))
        self.stack.enter_context(mock.patch.object(socket.socket, "connect", deny))
        self.stack.enter_context(mock.patch.object(socket.socket, "connect_ex", deny))

    def tearDown(self):
        self.assertEqual(self.attempts, [], "unexpected network attempt")

    def assert_url_contract(self):
        endpoint = Endpoint()
        cases = ((None, "https://example.invalid/api/v1"),
                 (False, "https://example.invalid/api/v1"),
                 ("", "https://example.invalid"),
                 ("/", "https://example.invalid"),
                 ("items/", "https://example.invalid/api/v1/items"),
                 ("/items/", "https://example.invalid/items"))
        for path, expected in cases:
            self.assertEqual(endpoint.get_url(path), expected, "path={!r}".format(path))
        self.assertEqual(Endpoint(base_path=False).get_url("items/"),
                         "https://example.invalid/items")
        self.assertIs(Endpoint(url=False).get_url(None), False)

    def assert_headers_contract(self):
        endpoint = Endpoint()
        self.assertEqual(endpoint.request_headers_default(),
                         {"Content-Type": "application/json", "Accept": "application/json"})
        supplied = {"Content-Type": "text/custom", "Accept": "application/custom", "X-Test": "synthetic"}
        before = supplied.copy()
        result = endpoint.request_headers_default(supplied)
        self.assertEqual(result, before)
        self.assertEqual(supplied, before)
        self.assertIsNot(result, supplied)
        self.assertEqual(Endpoint(content_type=False).request_headers_default(),
                         {"Content-Type": "text/plain", "Accept": "application/json"})
        self.assertEqual(Endpoint(present=False).request_headers_default(),
                         {"Content-Type": "text/plain", "Accept": "application/json"})

    def test_get_url_existing_path_semantics(self):
        self.assert_url_contract()

    def test_default_and_override_headers(self):
        self.assert_headers_contract()

    def test_url_mutations_are_detected(self):
        original = endpoint_module.ServiceEndpointMixin.get_url
        def ignore_base_path(self, path=None):
            if path == "items/":
                return "https://example.invalid/items"
            return original(self, path)
        def retain_base_path_for_absolute(self, path=None):
            if path == "/items/":
                return "https://example.invalid/api/v1/items"
            return original(self, path)
        for mutation in (ignore_base_path, retain_base_path_for_absolute):
            with self.subTest(mutation=mutation.__name__):
                with mock.patch.object(endpoint_module.ServiceEndpointMixin, "get_url", mutation):
                    with self.assertRaises(AssertionError):
                        self.assert_url_contract()

    def test_header_mutations_are_detected(self):
        original = endpoint_module.ServiceEndpointMixin.request_headers_default
        def overwrite_override(self, headers=None):
            result = original(self, headers)
            result["Content-Type"] = self.content_type_default or "text/plain"
            return result
        def drop_accept(self, headers=None):
            result = original(self, headers)
            result.pop("Accept", None)
            return result
        for mutation in (overwrite_override, drop_accept):
            with self.subTest(mutation=mutation.__name__):
                with mock.patch.object(endpoint_module.ServiceEndpointMixin, "request_headers_default", mutation):
                    with self.assertRaises(AssertionError):
                        self.assert_headers_contract()

    def test_guard_positive_controls(self):
        with self.assertRaisesRegex(RuntimeError, "network denied"):
            requests.post("https://example.invalid")
        with self.assertRaisesRegex(RuntimeError, "network denied"):
            requests.request("GET", "https://example.invalid")
        with self.assertRaisesRegex(RuntimeError, "network denied"):
            requests.Session().request("GET", "https://example.invalid")
        with socket.socket() as sock:
            with self.assertRaisesRegex(RuntimeError, "network denied"):
                sock.connect(("127.0.0.1", 9))
            with self.assertRaisesRegex(RuntimeError, "network denied"):
                sock.connect_ex(("127.0.0.1", 9))
        self.assertEqual(len(self.attempts), 5)
        self.attempts.clear()  # The deliberate, denied controls are not product attempts.

    def test_client_path_fallback_and_child_composition(self):
        from test_service_transport import production
        endpoint = Endpoint()
        loader = types.SimpleNamespace(get_credential=mock.Mock(return_value=None))
        provider = types.SimpleNamespace(authenticate=lambda context, audience: context)
        env = {'service.credential.loader': loader,
               'service.auth.factory': types.SimpleNamespace(create_service_auth=mock.Mock(return_value=provider))}
        client = production.ServiceClient(env, endpoint, None, path='root/', method='GET')
        for child in (None, False, ''):
            self.assertEqual(client.prepare_request_context(path=child)['url'], 'https://example.invalid/api/v1/root')
        self.assertEqual(client.prepare_request_context(path='/child/')['url'], 'https://example.invalid/child')
        self.assertEqual(client.prepare_request_context(path='child/')['url'], 'https://example.invalid/api/v1/child')

    def test_get_endpoint_lookup_contract(self):
        from test_service_transport import production
        class Record:
            def __init__(self, code, active=True, record_id=None): self.code, self.active, self.id = code, active, record_id
            def __bool__(self): return self.active
        class Model:
            def __init__(self, records): self.records, self.search_calls, self.browse_calls = records, [], []
            def search(self, domain, limit=None):
                self.search_calls.append((domain, limit))
                return next((r for r in self.records if r.code == domain[0][2] and r.active), None)
            def browse(self, record_id):
                self.browse_calls.append(record_id)
                return next((r for r in self.records if r.id == record_id), None)
        first, duplicate = Record('svc', record_id=11), Record('svc', record_id=12)
        model = Model([first, duplicate])
        factory = production.ServiceClientFactory.__new__(production.ServiceClientFactory)
        factory.env = {'service.endpoint': model}
        self.assertIs(factory._get_endpoint('svc'), first)
        self.assertEqual(model.search_calls, [([('code', '=', 'svc'), ('active', '=', True)], 1)])
        self.assertIs(factory._get_endpoint(12), duplicate)
        self.assertEqual(model.browse_calls, [12])
        for records in ([], [Record('svc', active=False)]):
            factory.env = {'service.endpoint': Model(records)}
            with self.assertRaisesRegex(ValueError, r"^Service 'svc' not found$"):
                factory._get_endpoint('svc')


if __name__ == "__main__":
    unittest.main()
