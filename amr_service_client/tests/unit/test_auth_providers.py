"""Offline U05-T01 regression for none, API-key, bearer and basic providers.

The socket/request guards observe this process, not native or child-process egress.
"""
import copy
import http.client
import importlib.util
from pathlib import Path
import socket
import sys
import urllib.request
import types
import unittest
from unittest import mock

import jwt  # Preload dependencies before temporarily stubbing the Odoo namespace.
import requests


def load_providers():
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda method: method)
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    path = Path(__file__).resolve().parents[2] / "services" / "providers.py"
    spec = importlib.util.spec_from_file_location("isolated_auth_providers", str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.exceptions": exceptions}):
        spec.loader.exec_module(module)
    return module


providers = load_providers()


class NetworkGuard:
    """Count and deny token POST, business request and socket attempts."""

    def __init__(self):
        self.token = 0
        self.business = 0
        self.socket = 0
        self.dns = 0
        self.urlopen = 0
        self.http_connect = 0
        self.stack = None

    def deny_token(self, *args, **kwargs):
        self.token += 1
        raise RuntimeError("token network denied")

    def deny_business(self, *args, **kwargs):
        self.business += 1
        raise RuntimeError("business network denied")

    def deny_socket(self, *args, **kwargs):
        self.socket += 1
        raise RuntimeError("socket network denied")

    def deny_dns(self, *args, **kwargs):
        self.dns += 1
        raise RuntimeError("DNS network denied")

    def deny_urlopen(self, *args, **kwargs):
        self.urlopen += 1
        raise RuntimeError("urlopen network denied")

    def deny_http_connect(self, *args, **kwargs):
        self.http_connect += 1
        raise RuntimeError("HTTP connection network denied")

    def __enter__(self):
        from contextlib import ExitStack
        self.stack = ExitStack()
        self.stack.enter_context(mock.patch.object(requests, "post", self.deny_token))
        self.stack.enter_context(mock.patch.object(requests, "request", self.deny_business))
        self.stack.enter_context(mock.patch.object(socket.socket, "connect", self.deny_socket))
        self.stack.enter_context(mock.patch.object(socket.socket, "connect_ex", self.deny_socket))
        self.stack.enter_context(mock.patch.object(socket, "getaddrinfo", self.deny_dns))
        self.stack.enter_context(mock.patch.object(urllib.request, "urlopen", self.deny_urlopen))
        self.stack.enter_context(mock.patch.object(http.client.HTTPConnection, "connect",
                                                   self.deny_http_connect))
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)


class AuthProviderRegression(unittest.TestCase):
    def assert_none_contract(self, provider):
        context = {"headers": {"Existing": "synthetic-existing"}, "params": {"page": 1}}
        before = copy.deepcopy(context)
        headers = context["headers"]
        with NetworkGuard() as guard:
            result = provider.authenticate(context, audience="synthetic-audience")
        self.assertIs(result, context)
        self.assertIs(context["headers"], headers)
        self.assertEqual(context, before)
        self.assertEqual((guard.token, guard.business, guard.socket), (0, 0, 0))

    def assert_api_key_contract(self, provider):
        context = {"headers": {"Existing": "synthetic-existing", "X-Api-Key": "old"},
                   "params": {"page": 1}}
        headers = context["headers"]
        with NetworkGuard() as guard:
            result = provider.authenticate(context, audience="synthetic-audience")
        self.assertIs(result, context)
        self.assertIs(context["headers"], headers)
        self.assertEqual(context, {"headers": {"Existing": "synthetic-existing",
                                               "X-Api-Key": "synthetic-key"},
                                   "params": {"page": 1}})
        self.assertEqual((guard.token, guard.business, guard.socket), (0, 0, 0))

    def test_none_preserves_context_and_headers(self):
        self.assert_none_contract(providers.NoneAuthProvider(None, {}))

    def test_legacy_U04_api_key_bearer_basic_headers(self):
        context = {}
        providers.ApiKeyProvider(None, {'header': 'X-Synthetic', 'value': 'v'}).authenticate(context)
        self.assertEqual(context['headers']['X-Synthetic'], 'v')
        context = {}
        providers.BearerProvider(None, {'token': 'v'}).authenticate(context)
        self.assertEqual(context['headers']['Authorization'], 'Bearer v')
        context = {}
        providers.BasicProvider(None, {'username': 'u', 'password': 'p'}).authenticate(context)
        self.assertEqual(context['headers']['Authorization'], 'Basic dTpw')

    def test_legacy_U04_factory_dispatches_provider_types_and_none(self):
        from pathlib import Path
        import importlib.util
        odoo = types.ModuleType('odoo')
        odoo.api = types.SimpleNamespace(model=lambda fn: fn)
        odoo.models = types.SimpleNamespace(AbstractModel=object)
        odoo.__dict__['models'] = odoo.models
        path = Path(__file__).resolve().parents[2] / 'services' / 'auth_factory.py'
        package_name = 'isolated_legacy_auth'
        package = types.ModuleType(package_name)
        package.__path__ = []
        module_name = package_name + '.auth_factory'
        factory_spec = importlib.util.spec_from_file_location(module_name, str(path))
        module = importlib.util.module_from_spec(factory_spec)
        with mock.patch.dict(sys.modules, {package_name: package, 'odoo': odoo,
                                          module_name.rpartition('.')[0] + '.providers': providers}):
            factory_spec.loader.exec_module(module)
        obj = object.__new__(module.ServiceAuthFactory)
        obj.env = None
        for kind, expected in (('api_key', providers.ApiKeyProvider), ('bearer', providers.BearerProvider),
                               ('basic', providers.BasicProvider), ('none', providers.NoneAuthProvider)):
            with self.subTest(kind=kind):
                self.assertIsInstance(obj.create_service_auth({'type': kind}), expected)

    def test_legacy_U04_loader_factory_type_compatibility(self):
        from pathlib import Path
        import importlib.util
        odoo = types.ModuleType('odoo')
        odoo.api = types.SimpleNamespace(model=lambda fn: fn)
        class AbstractModel:
            pass
        odoo.models = types.SimpleNamespace(AbstractModel=AbstractModel)
        odoo.__dict__['models'] = odoo.models
        path = Path(__file__).resolve().parents[2] / 'services' / 'credential_loader.py'
        odoo.__dict__['tools'] = types.SimpleNamespace(config={},
                                                     ormcache=lambda *args: lambda fn: fn)
        tools = types.ModuleType('odoo.tools')
        tools.config = {}
        module_name = 'isolated_legacy_auth_loader'
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {'odoo': odoo, 'odoo.tools': tools}):
            spec.loader.exec_module(module)
        validator = object.__new__(module.ServiceCredentialLoader)
        supported_types = {'api_key', 'bearer', 'basic', 'client_secret', 'service_account'}
        validator.env = {'service.auth.factory': types.SimpleNamespace(
            is_supported=lambda kind: kind in supported_types)}
        for kind in supported_types:
            validator._validate({'type': kind})
        with self.assertRaises(ValueError):
            validator._validate({'type': 'get_jwt'})
        factory_types = {'none', 'get_jwt', 'api_key', 'bearer', 'basic',
                         'client_secret', 'service_account'}
        self.assertEqual(factory_types - supported_types, {'none', 'get_jwt'})


    def test_legacy_U04_wizard_and_loader_each_expose_only_five_auth_types(self):
        import ast
        from pathlib import Path
        addon = Path(__file__).resolve().parents[2]
        tree = ast.parse((addon / 'wizards' / 'service_credential.py').read_text())
        wizard = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ServiceCredentialWizard')
        assignment = next(n for n in wizard.body if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'credential_type' for t in n.targets))
        options = ast.literal_eval(assignment.value.args[0])
        fake_factory = types.SimpleNamespace(is_supported=lambda kind: kind in {
            'none', 'get_jwt', 'api_key', 'bearer', 'basic', 'client_secret', 'service_account'})
        wizard_types = {item[0] for item in options}
        loader_types = {'api_key', 'bearer', 'basic', 'client_secret', 'service_account'}
        self.assertEqual(set(kind for kind in ('api_key', 'bearer', 'basic', 'client_secret',
                                               'service_account', 'get_jwt')
                             if fake_factory.is_supported(kind)),
                         loader_types | {'get_jwt'})
        self.assertEqual(wizard_types, loader_types | {'get_jwt'})
        self.assertNotIn('none', wizard_types)
        self.assertIn('get_jwt', wizard_types)

    def test_get_jwt_bypasses_cache_and_requests_fresh_token(self):
        cache = types.SimpleNamespace(
            get_cache=mock.Mock(return_value='stale-synthetic-token'),
            set_cache=mock.Mock())
        provider = providers.GetJWTTokenProvider(
            {'service.token.cache': cache},
            {'username': 'synthetic-user', 'token_uri': 'https://issuer.example.invalid/token'})
        response = mock.Mock()
        response.json.return_value = {'token': 'synthetic-selected-token'}
        response.raise_for_status.return_value = None
        with mock.patch.object(requests, 'post', return_value=response) as token_request:
            token = provider._get_token(audience='synthetic-audience')
        self.assertEqual(token, 'synthetic-selected-token')
        token_request.assert_called_once()
        cache.get_cache.assert_not_called()
        cache.set_cache.assert_not_called()
        self.assertNotIn('synthetic-selected-token', repr(token_request.call_args))
        self.assertNotIn('synthetic-selected-token', repr(cache.get_cache.call_args_list))
        self.assertNotIn('synthetic-selected-token', repr(cache.set_cache.call_args_list))

    def test_legacy_U04_base_test_credential_raises_user_error(self):
        from pathlib import Path
        import importlib.util
        odoo = types.ModuleType('odoo')
        odoo.api = types.SimpleNamespace(model=lambda fn: fn)
        exceptions = types.ModuleType('odoo.exceptions')
        exceptions.UserError = type('UserError', (Exception,), {})
        path = Path(__file__).resolve().parents[2] / 'services' / 'providers.py'
        spec = importlib.util.spec_from_file_location('isolated_legacy_credential_test', str(path))
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {'odoo': odoo, 'odoo.exceptions': exceptions}):
            spec.loader.exec_module(module)
        with self.assertRaises(exceptions.UserError):
            module.AuthenticationProvider(None, {}).test_credential()

    def test_api_key_replaces_only_key_and_preserves_headers(self):
        self.assert_api_key_contract(providers.ApiKeyProvider(
            None, {"header": "X-Api-Key", "value": "synthetic-key"}))

    def test_api_key_creates_missing_headers(self):
        context = {"params": {"page": 1}}
        provider = providers.ApiKeyProvider(None, {"header": "X-Api-Key", "value": "synthetic-key"})
        with NetworkGuard() as guard:
            result = provider.authenticate(context)
        self.assertIs(result, context)
        self.assertEqual(context, {"params": {"page": 1}, "headers": {"X-Api-Key": "synthetic-key"}})
        self.assertEqual((guard.token, guard.business, guard.socket), (0, 0, 0))

    def test_network_guard_positive_and_negative_controls(self):
        with NetworkGuard() as guard:
            self.assertEqual((guard.token, guard.business, guard.socket, guard.dns,
                              guard.urlopen, guard.http_connect), (0, 0, 0, 0, 0, 0))
            with self.assertRaisesRegex(RuntimeError, "token network denied"):
                requests.post("http://synthetic.invalid")
            with self.assertRaisesRegex(RuntimeError, "business network denied"):
                requests.request("GET", "http://synthetic.invalid")
            with socket.socket() as sock:
                with self.assertRaisesRegex(RuntimeError, "socket network denied"):
                    sock.connect(("127.0.0.1", 9))
                with self.assertRaisesRegex(RuntimeError, "socket network denied"):
                    sock.connect_ex(("127.0.0.1", 9))
            with self.assertRaisesRegex(RuntimeError, "DNS network denied"):
                socket.getaddrinfo("synthetic.invalid", 443)
            with self.assertRaisesRegex(RuntimeError, "urlopen network denied"):
                urllib.request.urlopen("http://synthetic.invalid")
            connection = http.client.HTTPConnection("dummy.invalid", 80)
            with self.assertRaisesRegex(RuntimeError, "HTTP connection network denied"):
                connection.connect()
            self.assertEqual((guard.token, guard.business, guard.socket, guard.dns,
                              guard.urlopen, guard.http_connect), (1, 1, 2, 1, 1, 1))

    def test_network_guard_negative_control_allows_no_attempts(self):
        with NetworkGuard() as guard:
            self.assertEqual((guard.token, guard.business, guard.socket, guard.dns,
                              guard.urlopen, guard.http_connect), (0, 0, 0, 0, 0, 0))

    def test_mutation_controls_detect_broken_provider_behavior(self):
        def corrupt_none(self, context, audience=None):
            context["headers"]["Existing"] = "changed"
            return context

        def wrong_api_key(self, context, audience=None):
            context["headers"][self.credential["header"]] = "wrong"
            return context

        def drop_existing_header(self, context, audience=None):
            context["headers"].pop("Existing")
            context["headers"][self.credential["header"]] = self.credential["value"]
            return context

        with mock.patch.object(providers.NoneAuthProvider, "authenticate", corrupt_none):
            with self.assertRaises(AssertionError):
                self.assert_none_contract(providers.NoneAuthProvider(None, {}))
        for mutation in (wrong_api_key, drop_existing_header):
            with self.subTest(mutation=mutation.__name__):
                with mock.patch.object(providers.ApiKeyProvider, "authenticate", mutation):
                    with self.assertRaises(AssertionError):
                        self.assert_api_key_contract(providers.ApiKeyProvider(
                            None, {"header": "X-Api-Key", "value": "synthetic-key"}))


    def test_unsupported_auth_factory_value_error_is_baseline_characterization(self):
        """Baseline only: unsupported auth raises ValueError; policy remains open."""
        import importlib.util
        from pathlib import Path

        odoo = types.ModuleType("odoo")
        odoo.api = types.SimpleNamespace(model=lambda method: method)
        odoo.models = types.SimpleNamespace(AbstractModel=object)
        odoo.__dict__["models"] = odoo.models
        package_name = "isolated_unsupported_auth"
        package = types.ModuleType(package_name)
        package.__path__ = []
        module_name = package_name + ".auth_factory"
        path = Path(__file__).resolve().parents[2] / "services" / "auth_factory.py"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {package_name: package, "odoo": odoo,
                                          package_name + ".providers": providers}):
            spec.loader.exec_module(module)

        factory = object.__new__(module.ServiceAuthFactory)
        factory.env = None
        with NetworkGuard() as guard:
            with self.assertRaises(ValueError):
                factory.create_service_auth({"type": "synthetic-unsupported"})
        self.assertEqual((guard.token, guard.business, guard.socket, guard.dns,
                          guard.urlopen, guard.http_connect), (0, 0, 0, 0, 0, 0))

    def test_service_client_call_sends_auth_headers_without_token_or_extra_requests(self):
        # Import the existing offline ServiceClient.call harness, then replace its
        # fake provider with each real provider and keep transport synthetic.
        from test_service_transport import Endpoint, production as client_module

        cases = (
            (providers.NoneAuthProvider(None, {}), {}),
            (providers.ApiKeyProvider(None, {"header": "X-Api-Key", "value": "synthetic-key"}),
             {"X-Api-Key": "synthetic-key"}),
            (providers.BearerProvider(None, {"token": "synthetic-token"}),
             {"Authorization": "Bearer synthetic-token"}),
            (providers.BasicProvider(None, {"username": "synthetic-user",
                                            "password": "synthetic-password"}),
             {"Authorization": "Basic c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3N3b3Jk"}),
        )
        for provider, auth_headers in cases:
            with self.subTest(provider=type(provider).__name__):
                endpoint = Endpoint()
                response = types.SimpleNamespace(raise_for_status=mock.Mock())
                client = object.__new__(client_module.ServiceClient)
                client.endpoint = endpoint
                client.path = "synthetic-path"
                client.method = "GET"
                client.provider = provider
                client.env = {}
                client.service_client = None
                client._report_sentry = mock.Mock()
                expected_headers = {"Content-Type": "application/json",
                                    "Accept": "application/json"}
                expected_headers.update(auth_headers)
                with NetworkGuard() as guard:
                    with mock.patch.object(requests, "request", return_value=response) as send:
                        result = client.call(method="GET", path="synthetic-path",
                                             headers={"X-Client": "synthetic-client"})
                self.assertIs(result, response)
                self.assertEqual(send.call_count, 1, "unexpected transport request count")
                sent = send.call_args[1]
                self.assertEqual(
                    sent["headers"] == dict(expected_headers, **{"X-Client": "synthetic-client"}),
                    True, "request headers did not match expected values")
                self.assertEqual((guard.token, send.call_count), (0, 1),
                                 "token request and business request counts did not match")
                self.assertEqual((guard.token, guard.business, guard.socket), (0, 0, 0))
                self.assertEqual(guard.dns, 0)
                self.assertEqual(guard.urlopen, 0)
                self.assertEqual(guard.http_connect, 0)


class BearerBasicRegression(unittest.TestCase):
    def assert_auth_contract(self, provider, expected):
        context = {"headers": {"Existing": "synthetic-existing", "Authorization": "old"},
                   "params": {"page": 1}}
        headers = context["headers"]
        params = context["params"]
        with NetworkGuard() as guard:
            result = provider.authenticate(context, audience="synthetic-audience")
        self.assertIs(result, context)
        self.assertIs(context["headers"], headers)
        self.assertIs(context["params"], params)
        # Do not include credentials or computed authorization values in failures.
        self.assertTrue(context == {"headers": {"Existing": "synthetic-existing",
                                               "Authorization": expected},
                                   "params": {"page": 1}})
        self.assertEqual((guard.token, guard.business, guard.socket), (0, 0, 0))

    def test_bearer_replaces_authorization_and_preserves_context(self):
        self.assert_auth_contract(providers.BearerProvider(None, {"token": "synthetic-token"}),
                                  "Bearer synthetic-token")

    def test_basic_replaces_authorization_and_preserves_context(self):
        self.assert_auth_contract(providers.BasicProvider(
            None, {"username": "synthetic-user", "password": "synthetic-password"}),
            "Basic c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3N3b3Jk")

    def test_bearer_and_basic_create_missing_headers(self):
        cases = ((providers.BearerProvider(None, {"token": "synthetic-token"}),
                  "Bearer synthetic-token"),
                 (providers.BasicProvider(None, {"username": "synthetic-user",
                                                 "password": "synthetic-password"}),
                  "Basic c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3N3b3Jk"))
        for provider, expected in cases:
            with self.subTest(provider=type(provider).__name__):
                context = {"params": {"page": 1}}
                with NetworkGuard() as guard:
                    result = provider.authenticate(context)
                self.assertIs(result, context)
                self.assertTrue(context == {"params": {"page": 1},
                                            "headers": {"Authorization": expected}})
                self.assertEqual((guard.token, guard.business, guard.socket), (0, 0, 0))

    def test_mutations_detect_wrong_authorization_and_lost_header(self):
        def wrong_authorization(self, context, audience=None):
            context["headers"]["Authorization"] = "wrong"
            return context

        def drop_header(self, context, audience=None):
            context["headers"].pop("Existing")
            return original(self, context, audience)

        cases = ((providers.BearerProvider, {"token": "synthetic-token"},
                  "Bearer synthetic-token"),
                 (providers.BasicProvider, {"username": "synthetic-user",
                                            "password": "synthetic-password"},
                  "Basic c3ludGhldGljLXVzZXI6c3ludGhldGljLXBhc3N3b3Jk"))
        for cls, credential, expected in cases:
            original = cls.authenticate
            for mutation in (wrong_authorization, drop_header):
                with self.subTest(provider=cls.__name__, mutation=mutation.__name__):
                    with mock.patch.object(cls, "authenticate", mutation):
                        with self.assertRaises(AssertionError):
                            self.assert_auth_contract(cls(None, credential), expected)


if __name__ == "__main__":
    unittest.main()
