"""Offline U06 cache-primitive characterization, not an isolation verdict.

The provider constructs the cache key; this component alone cannot prove DB,
credential, issuer, scope or rotation isolation. Exact TTL/boundary policy and
security targets remain open; this records only current behavior away from the
expiry boundary. No Odoo registry, database or real transport is exercised.
"""
import datetime
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

import requests


def load_cache():
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda method: method)
    odoo.models = types.SimpleNamespace(AbstractModel=object)
    odoo.tools = types.SimpleNamespace(timedelta=datetime.timedelta)
    exceptions = types.ModuleType("odoo.exceptions")
    exceptions.UserError = type("UserError", (Exception,), {})
    path = Path(__file__).resolve().parents[2] / "services" / "token_cache.py"
    spec = importlib.util.spec_from_file_location("isolated_u06_token_cache", str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.exceptions": exceptions}):
        spec.loader.exec_module(module)
    return module


cache_module = load_cache()


class FrozenClock:
    current = datetime.datetime(2020, 1, 1, 12, 0, 0)

    @classmethod
    def now(cls):
        return cls.current


class TokenCachePrimitive(unittest.TestCase):
    def setUp(self):
        cache_module.TOKEN_CACHE.clear()
        self.addCleanup(cache_module.TOKEN_CACHE.clear)
        FrozenClock.current = datetime.datetime(2020, 1, 1, 12, 0, 0)
        self.clock = mock.patch.object(cache_module, "datetime", FrozenClock)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.token_post = mock.patch.object(requests, "post", side_effect=RuntimeError("token POST denied"))
        self.business_request = mock.patch.object(requests, "request", side_effect=RuntimeError("business request denied"))
        self.t = self.token_post.start()
        self.b = self.business_request.start()
        self.addCleanup(self.token_post.stop)
        self.addCleanup(self.business_request.stop)
        self.cache = cache_module.ServiceTokenCache()

    def assert_no_transport(self):
        self.assertEqual((self.t.call_count, self.b.call_count), (0, 0))

    def assert_missing_contract(self):
        self.assertIsNone(self.cache.get_cache("synthetic-missing"))
        self.assertNotIn("synthetic-missing", cache_module.TOKEN_CACHE)
        self.assert_no_transport()

    def assert_fresh_contract(self):
        self.cache.set_cache("synthetic-key", "synthetic-token-a", 120)
        self.assertEqual(cache_module.TOKEN_CACHE["synthetic-key"]["expires_at"],
                         datetime.datetime(2020, 1, 1, 12, 2, 0))
        FrozenClock.current += datetime.timedelta(seconds=30)
        self.assertTrue(self.cache.get_cache("synthetic-key") == "synthetic-token-a")
        self.assertIn("synthetic-key", cache_module.TOKEN_CACHE)
        self.assert_no_transport()

    def assert_expired_contract(self):
        self.cache.set_cache("synthetic-key", "synthetic-token-a", 120)
        self.cache.set_cache("other-key", "synthetic-token-b", 300)
        FrozenClock.current += datetime.timedelta(seconds=121)
        self.assertIsNone(self.cache.get_cache("synthetic-key"))
        self.assertNotIn("synthetic-key", cache_module.TOKEN_CACHE)
        self.assertTrue(self.cache.get_cache("other-key") == "synthetic-token-b")
        self.assert_no_transport()

    def test_missing_key_returns_none(self):
        self.assert_missing_contract()

    def test_set_and_fresh_get_with_fixed_clock(self):
        self.assert_fresh_contract()

    def test_expired_get_removes_only_expired_entry(self):
        self.assert_expired_contract()

    def test_set_same_key_replaces_value_and_expiry(self):
        self.cache.set_cache("synthetic-key", "synthetic-token-a", 120)
        FrozenClock.current += datetime.timedelta(seconds=30)
        self.cache.set_cache("synthetic-key", "synthetic-token-b", 300)
        FrozenClock.current += datetime.timedelta(seconds=100)
        self.assertTrue(self.cache.get_cache("synthetic-key") == "synthetic-token-b")
        self.assert_no_transport()

    def test_transport_spies_positive_control(self):
        self.assert_no_transport()
        with self.assertRaisesRegex(RuntimeError, "token POST denied"):
            requests.post("https://synthetic.invalid")
        with self.assertRaisesRegex(RuntimeError, "business request denied"):
            requests.request("GET", "https://synthetic.invalid")
        self.assertEqual((self.t.call_count, self.b.call_count), (1, 1))

    def test_mutation_controls_catch_bad_cache_behavior(self):
        cls = cache_module.ServiceTokenCache
        original_get = cls.get_cache
        original_set = cls.set_cache

        def false_miss(self, key):
            return None

        def stale_hit(self, key):
            data = cache_module.TOKEN_CACHE.get(key)
            return data.get("token") if data else None

        def no_eviction(self, key):
            data = cache_module.TOKEN_CACHE.get(key)
            if data and data["expires_at"] > FrozenClock.now():
                return data["token"]
            return None

        def wrong_expiry(self, key, token, expires_in):
            return original_set(self, key, token, expires_in + 1)

        for name, method, mutation, oracle in (
                ("false miss", "get_cache", false_miss, self.assert_fresh_contract),
                ("stale hit", "get_cache", stale_hit, self.assert_expired_contract),
                ("no eviction", "get_cache", no_eviction, self.assert_expired_contract),
                ("wrong expiry", "set_cache", wrong_expiry, self.assert_fresh_contract)):
            with self.subTest(mutation=name):
                cache_module.TOKEN_CACHE.clear()
                FrozenClock.current = datetime.datetime(2020, 1, 1, 12, 0, 0)
                with mock.patch.object(cls, method, mutation):
                    with self.assertRaises(AssertionError):
                        oracle()
        self.assertIs(cls.get_cache, original_get)
        self.assertIs(cls.set_cache, original_set)


if __name__ == "__main__":
    unittest.main()
