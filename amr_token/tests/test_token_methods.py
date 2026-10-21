"""P-05 token signing/validation source behavior; RSA keys are ephemeral only."""
import unittest
from types import SimpleNamespace
from unittest import mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if __package__:
    from .support import load_public_key_model
else:
    from support import load_public_key_model


class TestTokenMethods(unittest.TestCase):
    def setUp(self):
        self.module = load_public_key_model()
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_pem = private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
        self.public_pem = private.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        self.payload = {
            "sub": "synthetic-user",
            "iss": "https://issuer.example.invalid",
            "aud": "synthetic-client",
        }
        self.record = SimpleNamespace(
            algorithm="RS256",
            private_key=self.private_pem,
            public_key=self.public_pem,
            kid="synthetic-kid",
            source="database",
        )

    def _require(self, method):
        self.assertTrue(callable(getattr(self.module.PublicKey, method, None)), f"candidate {method} method is missing")

    def test_generate_token_signs_and_sets_kid_header(self):
        self._require("generate_token")

        token = self.module.PublicKey.generate_token(self.record, self.payload)

        self.assertEqual(jwt.get_unverified_header(token)["kid"], "synthetic-kid")
        claims = jwt.decode(token, self.public_pem, algorithms=["RS256"], audience="synthetic-client", issuer=self.payload["iss"])
        self.assertEqual(claims["sub"], "synthetic-user")

    def test_default_validation_does_not_require_audience(self):
        self._require("validate_token")
        token = jwt.encode(self.payload, self.private_pem, algorithm="RS256")

        claims = self.module.PublicKey.validate_token(self.record, token)

        self.assertEqual(claims["aud"], "synthetic-client")

    def test_validation_checks_requested_issuer(self):
        self._require("validate_token")
        token = jwt.encode(self.payload, self.private_pem, algorithm="RS256")

        with self.assertLogs(self.module._logger, level="WARNING") as captured:
            with self.assertRaises(jwt.InvalidIssuerError):
                self.module.PublicKey.validate_token(self.record, token, issuer="https://wrong.example.invalid")

        self.assertIn("Invalid issuer", captured.output[0])

    def test_signing_uses_database_field_not_private_key_source_helper(self):
        self._require("generate_token")
        record = SimpleNamespace(
            algorithm="RS256",
            private_key=None,
            kid="synthetic-kid",
            get_private_key=mock.Mock(return_value=self.private_pem),
        )
        with mock.patch.object(self.module.jwt, "encode", return_value="synthetic-token") as encode:
            result = self.module.PublicKey.generate_token(record, self.payload)

        self.assertEqual(result, "synthetic-token")
        encode.assert_called_once_with(self.payload, None, algorithm="RS256", headers={"kid": "synthetic-kid"})
        record.get_private_key.assert_not_called()


if __name__ == "__main__":
    unittest.main()
