"""U06 Owner target: no token cross-use; ordinary failures are not waivers.

Offline provider/cache component evidence only. DB isolation is NOT RUN: no
real Odoo registry or two databases in one process. Exact TTL/boundary policy,
eviction design and integration I05 remain undecided/unverified. The fake
endpoint and signing seam do not establish actual issuer or JWT verification.
"""
import datetime
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

import jwt  # Preload shared dependencies before patching sys.modules.
import requests


def load_source(name, filename):
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda method: method)
    odoo.models = types.SimpleNamespace(AbstractModel=object)
    odoo.tools = types.SimpleNamespace(timedelta=datetime.timedelta)
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    path = Path(__file__).resolve().parents[2] / "services" / filename
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.exceptions": exceptions}):
        spec.loader.exec_module(module)
    return module


providers = load_source("u06_isolation_providers", "providers.py")
cache_module = load_source("u06_isolation_cache", "token_cache.py")


class Clock:
    current = datetime.datetime(2020, 1, 1)

    @classmethod
    def now(cls):
        return cls.current


class Response:
    def __init__(self, token):
        self.token = token

    def raise_for_status(self):
        pass

    def json(self):
        return {"access_token": self.token, "expires_in": 180}


class TokenIsolationTarget(unittest.TestCase):
    def setUp(self):
        cache_module.TOKEN_CACHE.clear()
        self.addCleanup(cache_module.TOKEN_CACHE.clear)
        Clock.current = datetime.datetime(2020, 1, 1)
        p = mock.patch.object(cache_module, "datetime", Clock)
        p.start()
        self.addCleanup(p.stop)
        self.cache = cache_module.ServiceTokenCache()
        self.env = {"service.token.cache": self.cache}
        self.credentials = {"client_id": "principal", "client_secret": "secret-a",
                            "token_uri": "https://issuer-a.invalid/token", "scope": "scope-a",
                            "private_key": "synthetic-private-key"}
        self.counts = {"T": 0, "B": 0}
        self.issued = []
        p = mock.patch.object(requests, "post", side_effect=self.post)
        p.start()
        self.addCleanup(p.stop)
        p = mock.patch.object(requests, "request", side_effect=self.business)
        p.start()
        self.addCleanup(p.stop)
        # Isolate cache behavior; no cryptographic signing is claimed.
        p = mock.patch.object(providers.ServiceAccountProvider, "_create_jwt_assertion",
                              return_value="synthetic-assertion")
        p.start()
        self.addCleanup(p.stop)

    def post(self, *args, **kwargs):
        self.counts["T"] += 1
        token = "synthetic-token-%d" % self.counts["T"]
        self.issued.append(token)
        return Response(token)

    def business(self, *args, **kwargs):
        self.counts["B"] += 1
        raise RuntimeError("business transport denied")

    def token(self, provider):
        result = provider.authenticate({"headers": {}}, audience="resource")
        return result["headers"]["Authorization"]

    def collision(self, cls, field, replacement):
        a = dict(self.credentials)
        b = dict(a, **{field: replacement})
        # Same principal and all other credential fields, only one dimension differs.
        self.assertEqual([k for k in a if a[k] != b[k]], [field])
        for first, second in ((a, b), (b, a)):
            with self.subTest(order="A-B" if first is a else "B-A"):
                cache_module.TOKEN_CACHE.clear()
                self.counts.update(T=0, B=0)
                self.issued[:] = []
                one = cls(self.env, first)
                two = cls(self.env, second)
                first_header = self.token(one)
                second_header = self.token(two)
                # Collect all observations before asserting; never print tokens.
                results = (self.counts["T"] == 2, self.counts["B"] == 0,
                           first_header == "Bearer " + self.issued[0],
                           len(self.issued) == 2 and second_header == "Bearer " + self.issued[1],
                           first_header != second_header)
                self.assertEqual(results, (True, True, True, True, True),
                                 "Owner target: T=2, B=0, own tokens, zero cross-use")

    def test_U06_credential_collision_both_orders_owner_target(self):
        self.collision(providers.ClientSecretProvider, "client_secret", "secret-b")

    def test_U06_scope_collision_both_orders_owner_target(self):
        self.collision(providers.ClientSecretProvider, "scope", "scope-b")

    def test_U06_service_account_token_endpoint_collision_both_orders_owner_target(self):
        # token_uri is the token endpoint and JWT aud, not JWT iss.
        self.collision(providers.ServiceAccountProvider, "token_uri",
                       "https://issuer-b.invalid/token")

    def test_U06_service_account_credential_collision_both_orders_owner_target(self):
        self.collision(providers.ServiceAccountProvider, "private_key", "synthetic-private-key-b")

    def test_U06_credential_rotation_same_principal_owner_target(self):
        credential = dict(self.credentials)
        provider = providers.ClientSecretProvider(self.env, credential)
        old = self.token(provider)
        credential["client_secret"] = "secret-b"
        new = self.token(provider)
        results = (self.counts["T"] == 2, self.counts["B"] == 0,
                   old == "Bearer " + self.issued[0],
                   len(self.issued) == 2 and new == "Bearer " + self.issued[1], old != new)
        self.assertEqual(results, (True, True, True, True, True),
                         "Owner target: rotation obtains and uses only new token")

    def test_fresh_posts_even_when_issuer_returns_same_token(self):
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.counts.update(T=0, B=0)
                cache_module.TOKEN_CACHE.clear()
                provider = cls(self.env, dict(self.credentials))
                with mock.patch.object(requests, "post", return_value=Response("same")) as post:
                    first = self.token(provider)
                    again = self.token(provider)
                    Clock.current += datetime.timedelta(seconds=181)
                    after = self.token(provider)
                self.assertEqual(post.call_count, 3)
                self.assertTrue(first == again == after == "Bearer same")
                self.assertEqual(self.counts["B"], 0)

    def test_prewarmed_cache_neither_read_nor_written(self):
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                provider = cls(self.env, dict(self.credentials))
                self.cache.set_cache(provider._get_cache_key("resource"), "stale", 300)
                with mock.patch.object(self.cache, "get_cache", wraps=self.cache.get_cache) as get, \
                        mock.patch.object(self.cache, "set_cache", wraps=self.cache.set_cache) as set_cache:
                    header = self.token(provider)
                self.assertEqual((get.call_count, set_cache.call_count), (0, 0))
                self.assertTrue(header == "Bearer " + self.issued[-1])
                self.assertEqual(self.counts["B"], 0)

    def test_client_call_stops_before_business_on_auth_failure(self):
        from test_service_transport import production, Endpoint
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            for failure in ("timeout", "missing_token", "success"):
                with self.subTest(provider=cls.__name__, outcome=failure):
                    provider = cls(self.env, dict(self.credentials))
                    self.cache.set_cache(provider._get_cache_key("default-audience"), "stale", 300)
                    loader = types.SimpleNamespace(get_credential=mock.Mock(return_value=None))
                    factory = types.SimpleNamespace(create_service_auth=mock.Mock(return_value=provider))
                    client = production.ServiceClient({"service.credential.loader": loader,
                                                       "service.auth.factory": factory}, Endpoint(), None, method="GET")
                    client._report_sentry = mock.Mock()
                    response = mock.Mock()
                    response.json.return_value = {} if failure == "missing_token" else {"access_token": "fresh"}
                    business = mock.Mock()
                    with mock.patch.object(requests, "post", side_effect=requests.Timeout if failure == "timeout" else None,
                                           return_value=response) as post, \
                            mock.patch.object(requests, "request", business):
                        if failure == "success":
                            client.call(method="GET")
                        else:
                            with self.assertRaises(ValueError):
                                client.call(method="GET")
                    self.assertEqual(post.call_count, 1)
                    self.assertEqual(business.call_count, 1 if failure == "success" else 0)

    def test_failure_never_falls_back_to_prewarmed_token(self):
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            for failure in ("timeout", "missing_token"):
                with self.subTest(provider=cls.__name__, failure=failure):
                    provider = cls(self.env, dict(self.credentials))
                    self.cache.set_cache(provider._get_cache_key("resource"), "stale", 300)
                    response = mock.Mock()
                    response.json.return_value = {}
                    with mock.patch.object(requests, "post", side_effect=requests.Timeout if failure == "timeout" else None,
                                           return_value=response) as post:
                        with self.assertRaises(ValueError):
                            self.token(provider)
                    self.assertEqual(post.call_count, 1)
                    self.assertEqual(self.counts["B"], 0)


if __name__ == "__main__":
    unittest.main()
