"""Component tests for header-selected asymmetric verification.

These fakes verify dispatch and trusted-key lookup only; they do not exercise
real signature cryptography or the Odoo registry.
"""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest import mock


ADDON = Path(__file__).resolve().parents[2]


class _KeyRecord(object):
    def __init__(self, algorithm, kid, active=True):
        self.algorithm = algorithm
        self.kid = kid
        self.active = active
        self.public_key = "synthetic-public-key"

    def __len__(self):
        return 1


class _EmptyRecord(object):
    def __len__(self):
        return 0


class _TrustedKeyModel(object):
    def __init__(self, records):
        self.records = records
        self.domains = []

    def sudo(self):
        return self

    def search(self, domain):
        self.domains.append(domain)
        values = {term[0]: term[2] for term in domain}
        record = self.records.get((values.get("algorithm"), values.get("kid")))
        if record and record.active == values.get("active"):
            return record
        return _EmptyRecord()


def _load_helper():
    support_path = ADDON / "tests" / "support.py"
    spec = importlib.util.spec_from_file_location("asym_header_test_support", str(support_path))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load isolated token helper")
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    fake_modules = {name: ModuleType(name) for name in (
        "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
        "cryptography.hazmat.primitives.asymmetric")}
    setattr(fake_modules["cryptography.hazmat.primitives.asymmetric"], "ec", mock.Mock())
    setattr(fake_modules["cryptography.hazmat.primitives.asymmetric"], "rsa", mock.Mock())
    with mock.patch.dict(sys.modules, fake_modules):
        module = support.load("models/token_helper.py")
    return module


class AsymmetricHeaderVerificationTests(unittest.TestCase):
    def _fixture(self, header, records=None, signing_algorithm="HS256"):
        module = _load_helper()
        keys = _TrustedKeyModel(records or {})
        helper = module.TokenHelper()
        helper.env = {"amr.public.key": keys}
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: signing_algorithm
        module.jwt.get_unverified_header = mock.Mock(return_value=header)
        module.jwt.decode = mock.Mock(return_value={"sub": "synthetic-user", "aud": "api"})
        return module, helper, keys

    def test_allowed_header_alg_and_kid_select_trusted_key_independent_of_signing_alg(self):
        kid = "trusted-es256-key"
        key = _KeyRecord("ES256", kid)
        module, helper, keys = self._fixture(
            {"alg": "ES256", "kid": kid}, {("ES256", kid): key}, signing_algorithm="HS256")

        result = helper.decode("synthetic-token", audience="api")

        self.assertEqual(result["sub"], "synthetic-user")
        self.assertEqual(keys.domains, [[
            ("algorithm", "=", "ES256"), ("kid", "=", kid), ("active", "=", True),
        ]])
        self.assertEqual(module.jwt.decode.call_args[0], ("synthetic-token", "synthetic-public-key"))
        self.assertEqual(module.jwt.decode.call_args[1]["algorithms"], ["ES256"])
        self.assertEqual(module.jwt.decode.call_args[1]["audience"], "api")

    def test_missing_kid_rejects_before_key_lookup_or_decode(self):
        module, helper, keys = self._fixture({"alg": "ES256"})

        with self.assertRaisesRegex(ValueError, "kid"):
            helper.decode("synthetic-token", audience="api")

        self.assertEqual(keys.domains, [])
        module.jwt.decode.assert_not_called()

    def test_unknown_kid_rejects_without_fallback(self):
        module, helper, keys = self._fixture({"alg": "ES256", "kid": "unknown"})

        with self.assertRaisesRegex(Exception, "Public Key not set") as raised:
            helper.decode("synthetic-token", audience="api")

        self.assertIs(type(raised.exception), Exception)
        self.assertEqual(keys.domains[0][1], ("kid", "=", "unknown"))
        module.jwt.decode.assert_not_called()

    def test_disallowed_or_unknown_header_alg_rejects_before_key_lookup(self):
        module, helper, keys = self._fixture({"alg": "RS1024", "kid": "kid"})

        with self.assertRaises(ValueError):
            helper.decode("synthetic-token", audience="api")

        self.assertEqual(keys.domains, [])
        module.jwt.decode.assert_not_called()

    def test_symmetric_alg_is_not_accepted_for_asymmetric_config(self):
        module, helper, keys = self._fixture(
            {"alg": "HS256", "kid": "kid"}, signing_algorithm="RS256")

        with self.assertRaisesRegex(ValueError, "algorithm"):
            helper.decode("synthetic-token", audience="api")

        self.assertEqual(keys.domains, [])
        module.jwt.decode.assert_not_called()

    def test_key_with_different_algorithm_than_header_is_not_selected(self):
        kid = "known-kid"
        incompatible_key = _KeyRecord("RS256", kid)
        module, helper, keys = self._fixture(
            {"alg": "ES256", "kid": kid}, {("RS256", kid): incompatible_key})

        with self.assertRaisesRegex(Exception, "Public Key not set"):
            helper.decode("synthetic-token", audience="api")

        self.assertEqual(keys.domains[0], [
            ("algorithm", "=", "ES256"), ("kid", "=", kid), ("active", "=", True),
        ])
        module.jwt.decode.assert_not_called()


if __name__ == "__main__":
    unittest.main()
