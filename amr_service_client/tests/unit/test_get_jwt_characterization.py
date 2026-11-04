"""U05 get_jwt offline wire and approved safe-failure contract, not ORM/UAT.

Guards observe only this Python process, not native or child-process activity.
"""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import traceback
import types
import unittest
from contextlib import ExitStack
from unittest import mock

import jwt  # Load dependencies before temporarily stubbing the Odoo namespace.
import requests


def load_provider_module():
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda method: method)
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    path = Path(__file__).resolve().parents[2] / "services" / "providers.py"
    spec = importlib.util.spec_from_file_location("get_jwt_characterization_provider", str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.exceptions": exceptions}):
        spec.loader.exec_module(module)
    return module


providers = load_provider_module()


class Cache:
    def __init__(self):
        self.lookups = []
        self.writes = []
        self.entries = {}

    def get_cache(self, key):
        self.lookups.append(key)
        return self.entries.get(key)

    def set_cache(self, *args):
        self.writes.append(args)


class SanitizedLogger:
    """Keep only redacted rendered messages; never retain original log arguments."""

    def __init__(self, secrets):
        self.secrets = secrets
        self.messages = []

    def _capture(self, message, *args, **kwargs):
        rendered = message % args if args else str(message)
        for secret in self.secrets:
            rendered = rendered.replace(secret, "[REDACTED]")
        self.messages.append(rendered)

    info = debug = warning = error = exception = critical = _capture


def marker_in_exception(error, marker):
    return marker in str(error)


class GetJWTCharacterization(unittest.TestCase):
    def setUp(self):
        self.credential = {"token_uri": "https://synthetic.invalid/token",
                           "username": "synthetic-user", "password": "synthetic-password",
                           "connect_timeout": 4, "read_timeout": 9}
        self.cache = Cache()
        self.warm_token = jwt.encode({"sub": "synthetic-stale"}, "synthetic-key", algorithm="HS256")
        if isinstance(self.warm_token, bytes):
            self.warm_token = self.warm_token.decode("ascii")
        self.provider = providers.GetJWTTokenProvider({"service.token.cache": self.cache}, self.credential)
        self.token_calls = []
        self.business_calls = 0
        self.socket_calls = 0
        self.response = mock.Mock()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.secrets = [self.credential["username"], self.credential["password"],
                        "synthetic-token", "synthetic-audience"]
        self.logger = SanitizedLogger(self.secrets)
        self.stack.enter_context(mock.patch.object(providers, "_logger", self.logger))
        self.stack.enter_context(mock.patch.object(requests, "post", self.token_post))
        self.stack.enter_context(mock.patch.object(requests, "request", self.deny_business))
        self.stack.enter_context(mock.patch.object(requests.sessions.Session, "request", self.deny_business))
        self.stack.enter_context(mock.patch.object(socket.socket, "connect", self.deny_socket))
        self.stack.enter_context(mock.patch.object(socket.socket, "connect_ex", self.deny_socket))

    def token_post(self, *args, **kwargs):
        self.token_calls.append((args, kwargs))
        return self.response

    def deny_business(self, *args, **kwargs):
        self.business_calls += 1
        raise RuntimeError("business request denied")

    def deny_socket(self, *args, **kwargs):
        self.socket_calls += 1
        raise RuntimeError("socket connection denied")

    def invoke_safely(self, operation, expected=None, marker=None):
        # Catch only at the production-call boundary; do not retain exceptions or
        # chain their tracebacks into unittest diagnostics.
        outcome = "returned"
        result = None
        exposed = False
        try:
            result = operation()
        except Exception as error:
            if expected is ValueError and type(error) is ValueError:
                outcome = "expected"
                try:
                    exposed = marker_in_exception(error, marker)
                except Exception:
                    outcome = "unexpected-exception"
            elif expected is KeyError and type(error) is KeyError:
                outcome = "expected" if error.args == ("cache_ttl",) else "wrong-key"
            else:
                outcome = "unexpected-exception"
        if outcome not in ("returned", "expected"):
            self.fail("provider boundary: unexpected exception category")
        if expected is not None and outcome != "expected":
            self.fail("provider boundary: expected exception was not raised")
        if expected is None and outcome != "returned":
            self.fail("provider boundary: unexpected exception category")
        return exposed if expected is ValueError else result

    def assert_wire(self):
        self.assertEqual(len(self.token_calls), 1)
        args, kwargs = self.token_calls[0]
        self.assertTrue(args == (self.credential["token_uri"],))
        self.assertTrue(set(kwargs) == {"headers", "data", "timeout"})
        self.assertTrue(kwargs["headers"] == {"Content-Type": "application/json", "Accept": "application/json"})
        self.assertTrue(json.loads(kwargs["data"]) == {"username": self.credential["username"],
                                                       "password": self.credential["password"]})
        self.assertEqual(kwargs["timeout"], (4, 9))
        self.assertEqual((self.business_calls, self.socket_calls), (0, 0))
        self.assertTrue(self.logger.messages)
        self.assertFalse(any(secret in message for secret in self.secrets
                             for message in self.logger.messages), "captured log not sanitized")

    def test_wire_json_and_success_response(self):
        self.response.json.return_value = {"token": "synthetic-token", "token_type": "JWT"}
        result = self.invoke_safely(lambda: self.provider._request_token(audience="synthetic-audience"))
        self.assertTrue(result == {"access_token": "synthetic-token", "token_type": "JWT",
                                  "raw_response": {"token": "synthetic-token", "token_type": "JWT"}})
        self.response.raise_for_status.assert_called_once_with()
        self.assert_wire()

    def test_cold_cache_valid_response_authenticates(self):
        # Historical U05 characterization: a cold response raised KeyError('cache_ttl').
        # The Owner approved successful authentication without local reuse instead.
        self.response.json.return_value = {"access_token": "synthetic-token"}
        with mock.patch.object(self.provider, "_request_token", wraps=self.provider._request_token) as request:
            result = self.invoke_safely(lambda: self.provider.authenticate(
                {"headers": {}}, audience="synthetic-audience"))
        self.assertTrue(result["headers"]["Authorization"] == "JWT synthetic-token")
        self.assertEqual(request.call_count, 1)
        self.assertEqual((len(self.cache.lookups), len(self.cache.writes)), (0, 0))
        self.assert_wire()

    def test_warm_cache_two_requests_use_two_fresh_tokens(self):
        self.cache.entries[self.provider._get_cache_key("synthetic-audience")] = self.warm_token
        self.response.json.side_effect = [{"token": "fresh-one"}, {"token": "fresh-two"}]
        with mock.patch.object(self.provider, "_request_token", wraps=self.provider._request_token) as request:
            first = self.invoke_safely(lambda: self.provider.authenticate({}, audience="synthetic-audience"))
            second = self.invoke_safely(lambda: self.provider.authenticate({}, audience="synthetic-audience"))
        self.assertTrue(first["headers"]["Authorization"] == "JWT fresh-one")
        self.assertTrue(second["headers"]["Authorization"] == "JWT fresh-two")
        self.assertEqual((request.call_count, len(self.token_calls), self.business_calls), (2, 2, 0))
        self.assertEqual((len(self.cache.lookups), len(self.cache.writes)), (0, 0))

    def test_warm_cache_identical_issuer_tokens_still_request_twice(self):
        self.cache.entries[self.provider._get_cache_key("synthetic-audience")] = self.warm_token
        self.response.json.return_value = {"token": "same"}
        with mock.patch.object(self.provider, "_request_token", wraps=self.provider._request_token) as request:
            first = self.invoke_safely(lambda: self.provider.authenticate({}, audience="synthetic-audience"))
            second = self.invoke_safely(lambda: self.provider.authenticate({}, audience="synthetic-audience"))
        self.assertTrue(first["headers"]["Authorization"] == second["headers"]["Authorization"] == "JWT same")
        self.assertEqual((request.call_count, len(self.token_calls), self.business_calls), (2, 2, 0))
        self.assertEqual((len(self.cache.lookups), len(self.cache.writes)), (0, 0))

    def test_token_failure_never_falls_back_or_calls_business(self):
        from test_service_transport import production, Endpoint
        for failure in ("timeout", "missing_token"):
            with self.subTest(failure=failure):
                self.cache.entries[self.provider._get_cache_key("default-audience")] = self.warm_token
                self.cache.lookups[:] = []
                self.cache.writes[:] = []
                self.response.json.return_value = {}
                loader = types.SimpleNamespace(get_credential=mock.Mock(return_value=None))
                factory = types.SimpleNamespace(create_service_auth=mock.Mock(return_value=self.provider))
                client = production.ServiceClient({"service.credential.loader": loader,
                                                   "service.auth.factory": factory}, Endpoint(), None, method="GET")
                client._report_sentry = mock.Mock()
                with mock.patch.object(self.provider, "_request_token", wraps=self.provider._request_token) as request, \
                        mock.patch.object(requests, "post", side_effect=requests.Timeout if failure == "timeout" else None,
                                          return_value=self.response) as post:
                    self.invoke_safely(lambda: client.call(method="GET"), expected=ValueError, marker="unused-marker")
                self.assertEqual((request.call_count, post.call_count, self.business_calls), (1, 1, 0))
                self.assertEqual((len(self.cache.lookups), len(self.cache.writes)), (0, 0))

    def test_non_json_response_does_not_expose_marker(self):
        # Compare in memory only. Never include marker, response, or exception in diagnostics.
        marker = "synthetic-sensitive-response-marker"
        self.response.text = marker
        self.response.json.side_effect = ValueError("not JSON")
        self.secrets.append(marker)
        marker_exposed = self.invoke_safely(self.provider._request_token, expected=ValueError, marker=marker)
        self.assertFalse(marker_exposed, "response body exposed")
        self.assert_wire()

    def test_http_error_non_json_does_not_expose_marker(self):
        marker = "synthetic-sensitive-http-error-marker"
        self.response.text = marker
        self.response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        self.response.json.side_effect = ValueError("not JSON")
        self.secrets.append(marker)
        marker_exposed = self.invoke_safely(self.provider._request_token, expected=ValueError, marker=marker)
        self.assertFalse(marker_exposed, "response body exposed")
        self.assert_wire()

    def test_http_error_json_does_not_expose_marker(self):
        marker = "synthetic-sensitive-json-error-marker"
        self.secrets.append(marker)
        self.response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        self.response.json.return_value = {"error": marker}
        marker_exposed = self.invoke_safely(self.provider._request_token, expected=ValueError, marker=marker)
        self.assertFalse(marker_exposed, "response body exposed")
        self.assert_wire()

    def test_sanitizer_and_marker_detection_positive_controls(self):
        marker = "synthetic-positive-control-marker"
        self.secrets.append(marker)
        self.logger.info("value=%s", marker)
        self.assertTrue(self.logger.messages[-1] == "value=[REDACTED]")
        self.assertTrue(marker_in_exception(ValueError(marker), marker))
        self.assertFalse(marker_in_exception(ValueError("unrelated"), marker))
        def unexpected():
            raise RuntimeError(marker)
        try:
            self.invoke_safely(unexpected, expected=ValueError, marker=marker)
        except AssertionError as error:
            formatted = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            safe = marker not in formatted and error.__context__ is None
        else:
            safe = False
        self.assertTrue(safe, "unexpected exception boundary leaked or failed to reject")

    def test_process_guard_positive_controls(self):
        with self.assertRaises(RuntimeError):
            requests.request("GET", "https://synthetic.invalid")
        with self.assertRaises(RuntimeError):
            requests.Session().request("GET", "https://synthetic.invalid")
        with socket.socket() as sock:
            with self.assertRaises(RuntimeError):
                sock.connect(("127.0.0.1", 9))
            with self.assertRaises(RuntimeError):
                sock.connect_ex(("127.0.0.1", 9))
        self.assertEqual((len(self.token_calls), self.business_calls, self.socket_calls), (0, 2, 2))


class ClientSecretLegacySchemaCharacterization(unittest.TestCase):
    """Client-secret wire/schema compatibility; not a cache-bypass policy test."""

    def setUp(self):
        self.credential = {"client_id": "synthetic-client", "client_secret": "synthetic-secret",
                           "token_uri": "https://synthetic.invalid/token"}
        self.calls = []
        self.response = mock.Mock()
        self.response.raise_for_status.return_value = None
        self.response.json.return_value = {"access_token": "synthetic-token"}
        self.post_patch = mock.patch.object(requests, "post", side_effect=self.post)
        self.post_patch.start()
        self.addCleanup(self.post_patch.stop)
        self.provider = providers.ClientSecretProvider({}, self.credential)

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response

    def assert_single_post(self, uri, payload, timeout):
        self.assertEqual(len(self.calls), 1)
        args, kwargs = self.calls[0]
        self.assertEqual(args, (uri,))
        self.assertEqual(set(kwargs), {"headers", "data", "timeout"})
        self.assertEqual(kwargs["headers"], {"Accept": "application/json"})
        self.assertEqual(kwargs["data"], payload)
        self.assertEqual(kwargs["timeout"], timeout)
        self.response.raise_for_status.assert_called_once_with()

    def test_client_secret_schema_defaults_and_short_ttl(self):
        marker = "synthetic-response-marker"
        raw = {"access_token": "synthetic-token", "expires_in": 10, "marker": marker}
        self.response.json.return_value = raw
        result = self.provider._request_token()
        self.assertEqual(result, {"access_token": "synthetic-token", "token_type": "Bearer",
                                  "expires_in": 10, "cache_ttl": 60, "raw_response": raw})
        self.assertIs(result["raw_response"], raw)
        self.assert_single_post(self.credential["token_uri"],
                                {"grant_type": "client_credentials", "client_id": "synthetic-client",
                                 "client_secret": "synthetic-secret"}, (10, 30))

    def test_client_secret_default_ttl_bearer_and_scope_string(self):
        self.credential["scope"] = "read:synthetic"
        self.response.json.return_value = {"access_token": "synthetic-token"}
        result = self.provider._request_token(audience="synthetic-audience")
        self.assertEqual(result, {"access_token": "synthetic-token", "token_type": "Bearer",
                                  "expires_in": 3600, "cache_ttl": 3540,
                                  "raw_response": {"access_token": "synthetic-token"}})
        self.assert_single_post(self.credential["token_uri"],
                                {"grant_type": "client_credentials", "client_id": "synthetic-client",
                                 "client_secret": "synthetic-secret", "audience": "synthetic-audience",
                                 "scope": "read:synthetic"}, (10, 30))

    def test_client_secret_custom_timeouts_and_token_uri_in_key(self):
        first_uri = self.credential["token_uri"]
        second_uri = "https://synthetic-other.invalid/token"
        self.credential.update(token_uri=first_uri, connect_timeout=2, read_timeout=7)
        first_key = self.provider._get_cache_key("synthetic-audience")
        self.credential["token_uri"] = second_uri
        second_key = self.provider._get_cache_key("synthetic-audience")
        self.assertEqual(first_key, "ClientSecret|synthetic-client|synthetic-audience|" + first_uri)
        self.assertEqual(second_key, "ClientSecret|synthetic-client|synthetic-audience|" + second_uri)
        self.assertNotEqual(first_key, second_key)
        self.credential["token_uri"] = first_uri
        self.response.json.return_value = {"access_token": "synthetic-token", "token_type": "Custom"}
        result = self.provider._request_token()
        self.assertEqual(result, {"access_token": "synthetic-token", "token_type": "Custom",
                                  "expires_in": 3600, "cache_ttl": 3540,
                                  "raw_response": {"access_token": "synthetic-token", "token_type": "Custom"}})
        self.assert_single_post(first_uri,
                                {"grant_type": "client_credentials", "client_id": "synthetic-client",
                                 "client_secret": "synthetic-secret"}, (2, 7))


if __name__ == "__main__":
    unittest.main()
