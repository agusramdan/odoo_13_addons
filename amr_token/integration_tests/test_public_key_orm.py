"""P-03/P-04 ORM contract; requires an authorized disposable Odoo 13 DB."""
import json
import unittest
import uuid

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native ORM tests NOT RUN")

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jwt.algorithms import ECAlgorithm


class TestPublicKeyORM(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPublicKeyORM, cls).setUpClass()
        # Isolate global JWKS search; SavepointCase rolls these changes back.
        cls.env["amr.public.key"].search([]).write({"active": False})
        cls.public_pems = {}
        for algorithm, public in (
            ("RS256", rsa.generate_private_key(
                public_exponent=65537, key_size=2048).public_key()),
            ("ES256", ec.generate_private_key(ec.SECP256R1()).public_key()),
        ):
            cls.public_pems[algorithm] = public.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("ascii")

    def test_valid_public_pem_and_defaults(self):
        key = self.env["amr.public.key"].create({
            "kid": "synthetic-orm-defaults",
            "public_key": self.public_pems["RS256"],
        })
        self.assertEqual(key.public_key, self.public_pems["RS256"])
        self.assertEqual(key.source, "database")
        self.assertEqual(key.algorithm, "RS256")
        self.assertTrue(key.active)
        self.assertFalse(key.is_signing)
        self.assertTrue(key.created_at)
        self.assertFalse(key.name)
        self.assertFalse(key.private_key)
        self.assertFalse(key.expires_at)

    def test_action_generate_key_stores_coherent_pair_and_public_only_jwks(self):
        key = self.env["amr.public.key"].create({
            "kid": "synthetic-orm-generation",
            "public_key": self.public_pems["ES256"],
            "algorithm": "ES256",
            # A non-default source detects accidental replacement by the helper.
            "source": "env_pem",
        })

        key.action_generate_key()

        self.assertTrue(key.kid != "synthetic-orm-generation")
        self.assertTrue(str(uuid.UUID(key.kid)) == key.kid)
        self.assertEqual(key.algorithm, "ES256")
        self.assertEqual(key.source, "env_pem")
        self.assertTrue(key.public_key != self.public_pems["ES256"])
        public = serialization.load_pem_public_key(key.public_key.encode("ascii"))
        private = serialization.load_pem_private_key(
            key.private_key.encode("ascii"), password=None)
        if not isinstance(public, ec.EllipticCurvePublicKey) or not isinstance(
                private, ec.EllipticCurvePrivateKey):
            self.fail("Expected an ES256 private/public key pair")
        self.assertEqual(public.curve.name, "secp256r1")
        # Boolean comparisons keep key material out of assertion failure output.
        self.assertTrue(private.public_key().public_numbers() == public.public_numbers())

        jwks = self.env["amr.public.key"].get_jwks()
        self.assertEqual(len(jwks), 1)
        jwk = jwks[0]
        self.assertEqual(set(jwk), {"kty", "crv", "x", "y", "kid", "alg"})
        self.assertTrue(jwk["kid"] == key.kid)
        self.assertEqual(jwk["alg"], "ES256")
        self.assertEqual(jwk["kty"], "EC")
        self.assertEqual(jwk["crv"], "P-256")
        published = ECAlgorithm.from_jwk(json.dumps(jwk))
        if not isinstance(published, ec.EllipticCurvePublicKey):
            self.fail("Expected a public EC JWK")
        self.assertTrue(published.public_numbers() == public.public_numbers())

    def test_required_field_metadata(self):
        fields = self.env["amr.public.key"].fields_get()
        for name in ("kid", "source", "public_key"):
            self.assertTrue(fields[name]["required"], name)
        for name in ("name", "algorithm", "private_key", "expires_at"):
            self.assertFalse(fields[name]["required"], name)

    def test_invalid_public_pem_rejected_on_create_and_write(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["amr.public.key"].create({
                "kid": "synthetic-orm-invalid",
                "public_key": "not a PEM public key",
            })
        key = self.env["amr.public.key"].create({
            "kid": "synthetic-orm-write",
            "public_key": self.public_pems["RS256"],
        })
        with self.assertRaises(ValidationError), self.cr.savepoint():
            key.write({"public_key": "not a PEM public key"})
        self.assertEqual(key.public_key, self.public_pems["RS256"])

    def test_rsa_ec_jwks_active_signing_and_public_only(self):
        expected = {}
        for algorithm, key_type in (("RS256", "RSA"), ("ES256", "EC")):
            for active in (True, False):
                for signing in (True, False):
                    kid = "synthetic-orm-{}-{}-{}".format(
                        algorithm, active, signing)
                    self.env["amr.public.key"].create({
                        "kid": kid,
                        "public_key": self.public_pems[algorithm],
                        "algorithm": algorithm,
                        "active": active,
                        "is_signing": signing,
                    })
                    if active:
                        expected[kid] = (algorithm, key_type, signing)
        jwks = self.env["amr.public.key"].get_jwks()
        self.assertEqual(len(jwks), len(expected))
        self.assertEqual({jwk["kid"] for jwk in jwks}, set(expected))
        for jwk in jwks:
            algorithm, key_type, signing = expected[jwk["kid"]]
            self.assertEqual(jwk["alg"], algorithm)
            self.assertEqual(jwk["kty"], key_type)
            if signing:
                self.assertEqual(jwk["use"], "sig")
            else:
                self.assertNotIn("use", jwk)
            self.assertTrue({"d", "p", "q", "dp", "dq", "qi", "oth", "k"}.isdisjoint(jwk))
            for name in (("n", "e") if key_type == "RSA" else ("crv", "x", "y")):
                self.assertTrue(jwk[name])
