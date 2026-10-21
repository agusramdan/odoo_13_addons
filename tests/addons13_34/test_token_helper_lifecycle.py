"""P-05 signing/validation routing, expiry, and key-selection contract."""
import unittest
from types import SimpleNamespace
from unittest import mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from support import load_helper_module


class TestTokenHelperLifecycle(unittest.TestCase):
    def setUp(self):
        self.module = load_helper_module()
        self.helper = object.__new__(self.module.TokenHelper)
        self.keys = mock.Mock()
        self.keys.sudo.return_value = self.keys
        self.helper.env = {"amr.public.key": self.keys}

    def _require(self, method):
        self.assertTrue(callable(self.module.TokenHelper.__dict__.get(method)), f"candidate {method} method is missing")

    def test_generate_token_routes_hmac_and_adds_claims(self):
        self._require("generate_token")
        self.helper.get_signature_algorithm = mock.Mock(return_value="HS256")
        self.helper.get_expires_in = mock.Mock(return_value=30)
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")
        self.helper.get_audience = mock.Mock(return_value="default-audience")
        self.helper.generate_token_secret = mock.Mock(side_effect=lambda payload, _algorithm: ("synthetic-jwt", payload))
        payload = {"sub": "synthetic-user"}
        with mock.patch.object(self.module.time, "time", return_value=1000):
            with self.assertLogs(self.module._logger, level="WARNING"):
                result = self.module.TokenHelper.generate_token(
                    self.helper, payload, audience="requested-audience", expires_in=60, scope="profile",
                )

        self.assertEqual(result, ("synthetic-jwt", payload))
        self.assertEqual(payload, {
            "sub": "synthetic-user", "iss": "https://issuer.example.invalid",
            "aud": "requested-audience", "exp": 1060, "scope": "profile",
        })
        self.helper.generate_token_secret.assert_called_once_with(payload, "HS256")

    def test_generate_token_routes_asymmetric_algorithms(self):
        self._require("generate_token")
        self.helper.get_signature_algorithm = mock.Mock(return_value="RS256")
        self.helper.get_expires_in = mock.Mock(return_value=10)
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")
        self.helper.get_audience = mock.Mock(return_value="default-audience")
        self.helper.generate_token_asymmetric = mock.Mock(return_value=("synthetic-jwt", {"sub": "u"}))
        payload = {"sub": "synthetic-user"}
        with mock.patch.object(self.module.time, "time", return_value=100):
            result = self.module.TokenHelper.generate_token(self.helper, payload)

        self.assertEqual(result[0], "synthetic-jwt")
        self.helper.generate_token_asymmetric.assert_called_once_with(payload, "RS256")

    def test_asymmetric_generation_selects_by_algorithm_only(self):
        self._require("generate_token_asymmetric")
        key = SimpleNamespace(
            active=False,
            is_signing=False,
            expires_at="2000-01-01 00:00:00",
            generate_token=mock.Mock(return_value="synthetic-signed-token"),
        )
        self.keys.search.return_value = key
        payload = {"sub": "synthetic-user"}

        result = self.module.TokenHelper.generate_token_asymmetric(self.helper, payload, "RS256")

        self.assertEqual(result, ("synthetic-signed-token", payload))
        self.keys.search.assert_called_once_with([("algorithm", "=", "RS256")])
        key.generate_token.assert_called_once_with(payload)

    def test_asymmetric_generation_propagates_multi_match_boundary_without_selection(self):
        # ORM ambiguity is synthetic here; native singleton behavior needs authorized UAT.
        records = mock.MagicMock()
        records.__len__.return_value = 2
        records.generate_token.side_effect = ValueError("synthetic multi-match boundary")
        self.keys.search.return_value = records
        with self.assertRaisesRegex(ValueError, "synthetic multi-match boundary"):
            self.module.TokenHelper.generate_token_asymmetric(self.helper, {}, "RS256")
        self.keys.search.assert_called_once_with([("algorithm", "=", "RS256")])
        records.generate_token.assert_called_once_with({})
        records.__getitem__.assert_not_called()
        records.__iter__.assert_not_called()

    def test_asymmetric_generation_rejects_missing_key(self):
        self._require("generate_token_asymmetric")
        self.keys.search.return_value = False
        with self.assertRaisesRegex(Exception, "Private Key not set"):
            self.module.TokenHelper.generate_token_asymmetric(self.helper, {}, "RS256")

    def test_hmac_generation_and_validation_with_synthetic_secret(self):
        self._require("generate_token_secret")
        self._require("validate_secret")
        secret = "SYNTHETIC-NOT-A-REAL-SECRET-FOR-TEST-ONLY-32"
        self.helper.get_secret = mock.Mock(return_value=secret)
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")
        payload = {"sub": "synthetic-user", "iss": "https://issuer.example.invalid", "aud": "synthetic-client"}
        token, same_payload = self.module.TokenHelper.generate_token_secret(self.helper, payload, "HS256")
        self.assertIs(same_payload, payload)
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")
        decoded = self.module.TokenHelper.validate_secret(self.helper, token, "HS256")
        self.assertEqual(decoded["sub"], "synthetic-user")
        self.assertEqual(decoded["aud"], "synthetic-client")

        with self.assertRaises(jwt.InvalidAudienceError):
            self.module.TokenHelper.validate_secret(self.helper, token, "HS256", audience="wrong-client")

    def test_validate_dispatches_using_token_header_and_kid(self):
        self._require("validate")
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")
        hmac_token = jwt.encode({"sub": "synthetic-user"}, "SYNTHETIC-HMAC-SECRET-FOR-TEST-ONLY-32", algorithm="HS256")
        rsa_token = jwt.encode({"sub": "synthetic-user"}, pem, algorithm="RS256", headers={"kid": "synthetic-kid"})
        self.helper.validate_secret = mock.Mock(return_value={"path": "secret"})
        self.helper.validate_asymmetric = mock.Mock(return_value={"path": "public"})

        with self.assertLogs(self.module._logger, level="WARNING"):
            self.assertEqual(self.module.TokenHelper.validate(self.helper, hmac_token, audience="client-a"), {"path": "secret"})
        self.helper.validate_secret.assert_called_once_with(hmac_token, algorithm="HS256", audience="client-a")
        self.assertEqual(self.module.TokenHelper.validate(self.helper, rsa_token, audience="client-b"), {"path": "public"})
        self.helper.validate_asymmetric.assert_called_once_with(rsa_token, "synthetic-kid", algorithm="RS256", audience="client-b")

    def test_asymmetric_validation_selects_algorithm_and_kid_only(self):
        self._require("validate_asymmetric")
        key = SimpleNamespace(validate_token=mock.Mock(return_value={"sub": "synthetic-user"}))
        self.keys.search.return_value = key
        self.helper.get_issuer = mock.Mock(return_value="https://issuer.example.invalid")

        result = self.module.TokenHelper.validate_asymmetric(
            self.helper, "synthetic-token", "synthetic-kid", "RS256", "synthetic-client",
        )

        self.assertEqual(result, {"sub": "synthetic-user"})
        self.keys.search.assert_called_once_with([
            ("algorithm", "=", "RS256"), ("kid", "=", "synthetic-kid"),
        ])
        key.validate_token.assert_called_once_with(
            "synthetic-token", issuer="https://issuer.example.invalid",
            audience="synthetic-client", options={"verify_aud": True},
        )

    def test_decode_delegates_to_validate(self):
        self._require("decode")
        self.helper.validate = mock.Mock(return_value={"sub": "synthetic-user"})
        self.assertEqual(self.module.TokenHelper.decode(self.helper, "synthetic-token", audience="client"), {"sub": "synthetic-user"})
        self.helper.validate.assert_called_once_with("synthetic-token", audience="client")

    def test_encode_normalizes_aliases_and_removes_issuer_claim_inputs(self):
        self._require("encode")
        self.helper.generate_token = mock.Mock(return_value=("synthetic-token", {}))
        result = self.module.TokenHelper.encode(
            self.helper, alg="RS256", aud="service-a", iss="forged-issuer", issuer="also-forged",
            scope="profile", sub="synthetic-user",
        )

        self.assertEqual(result, ("synthetic-token", {}))
        self.helper.generate_token.assert_called_once_with(
            {"sub": "synthetic-user"}, algorithm="RS256", audience="service-a", scope="profile",
        )


if __name__ == "__main__":
    unittest.main()
