"""P-06 key generation and safe PEM serialization contract."""
import unittest
import uuid
from types import SimpleNamespace
from unittest import mock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from support import ADDON, load_helper_module


class TestHelperKeyGeneration(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ADDON / "models" / "helper.py").is_file(), "candidate token helper is missing")
        self.module = load_helper_module()

    def test_supported_algorithm_map_contains_source_algorithms(self):
        expected = {
            "RS256", "RS384", "RS512", "PS256", "PS384", "PS512",
            "ES256", "ES384", "ES512", "ES256K",
        }
        self.assertEqual(set(self.module.TokenHelper.ALGORITHM_CONFIG), expected)

    def test_generate_key_returns_parseable_rsa_pair_and_uuid_kid(self):
        result = self.module.TokenHelper.generate_key("RS256")

        private = serialization.load_pem_private_key(result["private_key"].encode(), password=None)
        public = serialization.load_pem_public_key(result["public_key"].encode())
        self.assertIsInstance(private, rsa.RSAPrivateKey)
        self.assertEqual(
            private.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo),
            public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo),
        )
        self.assertEqual(result["algorithm"], "RS256")
        self.assertEqual(str(uuid.UUID(result["kid"])), result["kid"])

    def test_generate_key_returns_parseable_ec_pair(self):
        result = self.module.TokenHelper.generate_key("ES256")

        private = serialization.load_pem_private_key(result["private_key"].encode(), password=None)
        public = serialization.load_pem_public_key(result["public_key"].encode())
        self.assertIsInstance(private, ec.EllipticCurvePrivateKey)
        self.assertEqual(
            private.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo),
            public.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo),
        )
        self.assertEqual(result["algorithm"], "ES256")

    def test_unsupported_algorithm_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported algorithm: HS256"):
            self.module.TokenHelper.generate_key("HS256")

    def test_create_public_key_names_record_with_generated_kid(self):
        generated = {"kid": "synthetic-kid", "algorithm": "RS256", "source": "database"}
        key_model = SimpleNamespace(create=mock.Mock())
        helper = SimpleNamespace(
            generate_key=mock.Mock(return_value=dict(generated)),
            env={"amr.public.key": key_model},
        )

        self.module.TokenHelper.create_public_key(helper, "RS256")

        helper.generate_key.assert_called_once_with("RS256")
        key_model.create.assert_called_once_with({
            "kid": "synthetic-kid",
            "algorithm": "RS256",
            "source": "database",
            "name": "synthetic-kid",
        })


if __name__ == "__main__":
    unittest.main()
