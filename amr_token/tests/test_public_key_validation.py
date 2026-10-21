"""P-03 PEM validation/loading tests with ephemeral public keys only."""
import unittest
from types import SimpleNamespace

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if __package__:
    from .support import ADDON, load_public_key_model
else:
    from support import ADDON, load_public_key_model


def _public_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


class TestPublicKeyValidation(unittest.TestCase):
    def test_valid_public_pem_passes_model_constraint(self):
        self.assertTrue((ADDON / "models" / "public_key.py").is_file(), "candidate public-key model is missing")
        module = load_public_key_model()
        record = SimpleNamespace(public_key=_public_pem())
        self.assertTrue(callable(getattr(module.PublicKey, "_check_public_key", None)), "candidate PEM constraint is missing")

        module.PublicKey._check_public_key([record])

    def test_invalid_public_pem_raises_validation_error(self):
        module = load_public_key_model()
        record = SimpleNamespace(public_key="not a PEM public key")
        self.assertTrue(callable(getattr(module.PublicKey, "_check_public_key", None)), "candidate PEM constraint is missing")

        with self.assertRaises(module.ValidationError):
            module.PublicKey._check_public_key([record])

    def test_pem_loader_returns_a_cryptography_public_key(self):
        module = load_public_key_model()
        record = SimpleNamespace(public_key=_public_pem())
        self.assertTrue(callable(getattr(module.PublicKey, "load_pem_public_key", None)), "candidate PEM loader is missing")

        loaded = module.PublicKey.load_pem_public_key(record)

        self.assertIsInstance(loaded, rsa.RSAPublicKey)


if __name__ == "__main__":
    unittest.main()
