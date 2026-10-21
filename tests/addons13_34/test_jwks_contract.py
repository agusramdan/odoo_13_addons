"""P-04 JWKS and R-JWKS-FILTERS characterization using ephemeral keys only."""
import datetime
import unittest
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric import ec, rsa

from support import ADDON, load_public_key_model


PRIVATE_JWK_PARAMETERS = {"d", "p", "q", "dp", "dq", "qi", "oth"}


def _record(kid, algorithm, public_key, *, active, is_signing, expires_at=None):
    return SimpleNamespace(
        kid=kid,
        algorithm=algorithm,
        active=active,
        is_signing=is_signing,
        expires_at=expires_at,
        load_pem_public_key=lambda: public_key,
    )


class _ModelRecords:
    def __init__(self, records):
        self.records = records
        self.domains = []

    def search(self, domain):
        self.domains.append(domain)
        return [record for record in self.records if record.active]


class TestJwksContract(unittest.TestCase):
    def test_algorithm_key_mismatch_is_not_rejected_until_jwks_serialization(self):
        from cryptography.hazmat.primitives import serialization

        model = load_public_key_model().PublicKey
        public = ec.generate_private_key(ec.SECP256R1()).public_key()
        pem = public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")
        model._check_public_key([SimpleNamespace(public_key=pem, algorithm="RS256")])
        records = _ModelRecords([_record("synthetic-mismatch", "RS256", public, active=True, is_signing=False)])
        # Characterize missing RSA numbers without relying on version-specific type names.
        with self.assertRaisesRegex(AttributeError, "has no attribute 'n'"):
            model.get_jwks(records)
        self.assertEqual(records.domains, [[("active", "=", True)]])

    def test_active_rsa_and_ec_keys_are_serialized_publicly(self):
        model_path = ADDON / "models" / "public_key.py"
        self.assertTrue(model_path.is_file(), "candidate public-key model is missing")
        model = load_public_key_model().PublicKey

        rsa_public = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
        ec_public = ec.generate_private_key(ec.SECP256R1()).public_key()
        records = _ModelRecords(
            [
                _record("rsa-active", "RS256", rsa_public, active=True, is_signing=True),
                _record("ec-active", "ES256", ec_public, active=True, is_signing=False),
                _record(
                    "rsa-expired-active", "RS256", rsa_public, active=True,
                    is_signing=False, expires_at=datetime.datetime(2000, 1, 1),
                ),
                _record("rsa-inactive", "RS256", rsa_public, active=False, is_signing=True),
            ]
        )

        self.assertTrue(callable(getattr(model, "get_jwks", None)), "candidate get_jwks method is missing")
        jwks = model.get_jwks(records)

        self.assertEqual(records.domains, [[("active", "=", True)]])
        self.assertEqual({key["kid"] for key in jwks}, {"rsa-active", "ec-active", "rsa-expired-active"})
        by_kid = {key["kid"]: key for key in jwks}
        self.assertEqual((by_kid["rsa-active"]["kty"], by_kid["rsa-active"]["alg"]), ("RSA", "RS256"))
        self.assertEqual(by_kid["rsa-active"]["use"], "sig")
        self.assertEqual((by_kid["ec-active"]["kty"], by_kid["ec-active"]["alg"]), ("EC", "ES256"))
        self.assertNotIn("use", by_kid["ec-active"])
        self.assertIn("rsa-expired-active", by_kid)
        for jwk in jwks:
            self.assertTrue(PRIVATE_JWK_PARAMETERS.isdisjoint(jwk))
        self.assertNotIn("rsa-inactive", by_kid)


if __name__ == "__main__":
    unittest.main()
