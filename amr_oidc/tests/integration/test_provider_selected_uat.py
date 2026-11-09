# -*- coding: utf-8 -*-
"""Provider-only runtime assertions for selected ADDONS13-82 UAT gaps."""
import base64
import time

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from unittest import mock


class TestProviderSelectedUAT01(TransactionCase):
    def _configure_secret(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-provider-only-secret-0123456789")
        params.set_param("web.base.url", "https://provider-uat.invalid")
        params.set_param("database.uuid", "synthetic-provider-audience")
        return params

    def test_valid_provider_token_operation_and_missing_configuration_rejects(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        params = self._configure_secret()
        helper = self.env["amr.oidc.helper"]
        token, claims, _expires = helper._generate_user_token(
            self.env.user, audience="synthetic-provider-audience")
        decoded = helper.decode(token, audience="synthetic-provider-audience")
        self.assertEqual(decoded["sub"], self.env.user.login)
        self.assertEqual(decoded["uid"], self.env.user.id)
        self.assertEqual(claims["uid"], self.env.user.id)

        params.set_param("amr_token.secret", "")
        with self.assertRaisesRegex(ValueError, "JWT Secret not set"):
            self.env.user.get_access_token(audience="synthetic-provider-audience")

    def test_create_access_token_fails_when_legacy_persistent_storage_is_absent(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        with self.assertRaises(UserError) as raised:
            self.env.user.create_access_token(audience="synthetic-provider-audience")
        self.assertEqual(raised.exception.args[0],
                         "Persistent access-token storage is not available")
        self.assertEqual(raised.exception.args[1:], ("",))
        self.assertNotIn("synthetic-provider-audience", str(raised.exception))
        self.assertNotIn("amr.token", self.env.registry.models)


class TestProviderSelectedUAT07(TransactionCase):
    def _configure_secret(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-actor-target-secret-012345")
        params.set_param("web.base.url", "https://actor-target.invalid")

    def _new_target(self, login):
        return self.env["res.users"].create({
            "name": "Synthetic target " + login,
            "login": login,
            "email": login + "@example.invalid",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })

    def test_self_issuance_and_system_cross_user_signed_target_claims(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("res.users", self.env.registry.models)
        self._configure_secret()
        helper = self.env["amr.oidc.helper"]
        own_token = self.env.user.get_access_token(audience="actor-target-aud")
        own_claims = helper.decode(own_token, audience="actor-target-aud")
        self.assertEqual(own_claims["uid"], self.env.user.id)
        self.assertEqual(own_claims["sub"], self.env.user.login)

        target = self._new_target("synthetic-cross-user-target")
        system_actor = self.env.ref("base.user_admin")
        token = target.with_user(system_actor).get_access_token(
            audience="actor-target-aud")
        claims = helper.decode(token, audience="actor-target-aud")
        self.assertEqual(claims["uid"], target.id)
        self.assertEqual(claims["sub"], target.login)
        self.assertNotEqual(claims["uid"], system_actor.id)

    def test_audience_list_is_supported_and_invalid_list_does_not_default(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("res.users", self.env.registry.models)
        self._configure_secret()
        helper = self.env["amr.oidc.helper"]
        audience = ["actor-list-audience", "actor-list-secondary"]
        other_audience = ["actor-list-other"]
        with mock.patch("jwt.encode", wraps=jwt.encode) as signer:
            token = self.env.user.get_access_token(audience=audience)
            repeated_token = self.env.user.get_access_token(audience=audience)
            other_token = self.env.user.get_access_token(audience=other_audience)
            self.assertEqual(signer.call_count, 2)
            with self.assertRaisesRegex(ValueError, "A valid audience is required"):
                self.env.user.get_access_token(audience=[])
            self.assertEqual(signer.call_count, 2)

        self.assertEqual(repeated_token, token)
        claims = helper.decode(token, audience=audience)
        self.assertEqual(claims["aud"], audience)
        other_claims = helper.decode(other_token, audience=other_audience)
        self.assertEqual(other_claims["aud"], other_audience)

    def test_non_system_cross_user_denial_precedes_cache_and_signing(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("res.users", self.env.registry.models)
        self._configure_secret()
        actor = self._new_target("synthetic-nonsystem-actor")
        target = self._new_target("synthetic-nonsystem-target")
        users_model = self.env["res.users"]
        with mock.patch.object(
                type(users_model), "_get_access_token") as cache:
            with mock.patch("jwt.encode", wraps=jwt.encode) as signer:
                with self.assertRaises(AccessError):
                    target.with_user(actor).get_access_token(
                        audience="actor-target-aud")
        cache.assert_not_called()
        signer.assert_not_called()


class TestProviderSelectedUAT08(TransactionCase):
    issuer = "https://provider-verifier.invalid"
    audience = "synthetic-verifier-audience"

    def _configure_secret(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-uat08-secret-0123456789")
        params.set_param("web.base.url", self.issuer)
        return params

    def _configure_public_key(self, signing_algorithm="RS256"):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "public_key")
        params.set_param("amr_token.public_key_algorithm", signing_algorithm)
        params.set_param("web.base.url", self.issuer)

    def _key_record(self, private_key, algorithm, kid, active=True):
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")
        return self.env["amr.public.key"].create({
            "kid": kid, "public_key": public_pem, "algorithm": algorithm,
            "active": active, "is_signing": False,
        })

    def _token(self, private_key, algorithm="RS256", kid="synthetic-uat08-kid",
               claims=None):
        now = int(time.time())
        payload = {"iss": self.issuer, "aud": self.audience,
                   "iat": now, "nbf": now - 1, "exp": now + 300,
                   "sub": "synthetic-verifier-subject"}
        if claims:
            payload.update(claims)
        token = jwt.encode(payload, private_key, algorithm=algorithm,
                           headers={"kid": kid})
        return token if isinstance(token, str) else token.decode("ascii")

    def _decode(self, token, **kwargs):
        return self.env["amr.oidc.helper"].decode(
            token, audience=self.audience, **kwargs)

    def _assert_public_key_unavailable(self, token):
        with self.assertRaises(Exception) as raised:
            self._decode(token)
        self.assertIs(type(raised.exception), Exception)
        self.assertEqual(raised.exception.args, ("Public Key not set",))

    def test_secret_signed_token_and_signature_override_reject(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self._configure_secret()
        secret = "synthetic-uat08-secret-0123456789"
        now = int(time.time())
        payload = {"iss": self.issuer, "aud": self.audience, "exp": now + 300,
                   "nbf": now - 1, "sub": "synthetic-secret-subject"}
        token = jwt.encode(payload, secret, algorithm="HS256")
        claims = self._decode(token if isinstance(token, str) else token.decode("ascii"))
        self.assertEqual(claims["sub"], "synthetic-secret-subject")

        header, body, signature = (token if isinstance(token, str)
                                   else token.decode("ascii")).split(".")
        changed = ("A" if signature[0] != "A" else "B") + signature[1:]
        tampered = ".".join((header, body, changed))
        with self.assertRaises(jwt.InvalidSignatureError):
            self._decode(tampered, options={"verify_signature": False})

    def test_secret_claim_policy_fails_closed_under_option_overrides(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self._configure_secret()
        secret = "synthetic-uat08-secret-0123456789"
        now = int(time.time())
        disabled_options = {
            "verify_signature": False, "verify_iss": False, "verify_aud": False,
            "verify_exp": False, "verify_nbf": False, "require": [],
        }
        invalid_cases = (
            ({"iss": "https://wrong-issuer.invalid"}, jwt.InvalidIssuerError),
            ({"aud": "wrong-audience"}, jwt.InvalidAudienceError),
            ({"exp": now - 30}, jwt.ExpiredSignatureError),
            ({"nbf": now + 300}, jwt.ImmatureSignatureError),
            ({"exp": None}, jwt.MissingRequiredClaimError),
        )
        for changes, error_type in invalid_cases:
            with self.subTest(claims=tuple(changes)):
                payload = {"iss": self.issuer, "aud": self.audience,
                           "exp": now + 300, "nbf": now - 1}
                payload.update(changes)
                token = jwt.encode(payload, secret, algorithm="HS256")
                token = token if isinstance(token, str) else token.decode("ascii")
                with self.assertRaises(error_type):
                    self._decode(token, options=disabled_options)

        for payload in (
                {"aud": self.audience, "exp": now + 300},
                {"iss": self.issuer, "exp": now + 300},
                {"iss": self.issuer, "aud": self.audience}):
            with self.subTest(missing=tuple(sorted(set(("iss", "aud", "exp")) - set(payload)))):
                token = jwt.encode(payload, secret, algorithm="HS256")
                token = token if isinstance(token, str) else token.decode("ascii")
                with self.assertRaises(jwt.MissingRequiredClaimError):
                    self._decode(token, options=disabled_options)

    def test_real_asymmetric_signature_header_algorithm_and_trusted_kid(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("amr.public.key", self.env.registry.models)
        self._configure_public_key("RS256")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._key_record(key, "RS256", "synthetic-uat08-kid")
        token = self._token(key)
        claims = self._decode(token)
        self.assertEqual(claims["sub"], "synthetic-verifier-subject")
        self.assertEqual(claims["aud"], self.audience)

        # Header alg, not configured signing alg, selects asymmetric verifier.
        ec_key = ec.generate_private_key(ec.SECP256R1())
        self._key_record(ec_key, "ES256", "synthetic-uat08-ec-kid")
        ec_token = self._token(ec_key, algorithm="ES256",
                               kid="synthetic-uat08-ec-kid")
        self.assertEqual(self._decode(ec_token)["sub"], "synthetic-verifier-subject")

    def test_signature_kid_and_algorithm_fail_closed_even_if_caller_disables_verify(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("amr.public.key", self.env.registry.models)
        self._configure_public_key("RS256")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._key_record(key, "RS256", "synthetic-uat08-kid")
        token = self._token(key)
        header, payload, signature = token.split(".")
        changed = ("A" if signature[0] != "A" else "B") + signature[1:]
        tampered = ".".join((header, payload, changed))
        with self.assertRaises(jwt.InvalidSignatureError):
            self._decode(tampered, options={"verify_signature": False})

        unknown = self._token(key, kid="synthetic-unknown-kid")
        self._assert_public_key_unavailable(unknown)
        no_kid = jwt.encode({"iss": self.issuer, "aud": self.audience,
                             "exp": int(time.time()) + 300}, key,
                            algorithm="RS256", headers={"kid": ""})
        with self.assertRaisesRegex(ValueError, "kid are required"):
            self._decode(no_kid if isinstance(no_kid, str) else no_kid.decode("ascii"))
        absent_kid_header = base64.urlsafe_b64encode(
            b'{"alg":"RS256","typ":"JWT"}').rstrip(b"=").decode("ascii")
        absent_kid = ".".join((absent_kid_header, payload, signature))
        with self.assertRaisesRegex(ValueError, "kid are required"):
            self._decode(absent_kid)

        # Absent and non-asymmetric algorithms cannot widen the verification path.
        absent_alg_header = base64.urlsafe_b64encode(
            b'{"kid":"synthetic-uat08-kid","typ":"JWT"}').rstrip(b"=").decode("ascii")
        absent_alg = ".".join((absent_alg_header, payload, signature))
        with self.assertRaises(ValueError):
            self._decode(absent_alg)

        # A valid signature with an untrusted HMAC header must not take secret path.
        hmac_token = jwt.encode({"iss": self.issuer, "aud": self.audience,
                                 "exp": int(time.time()) + 300},
                                "synthetic-not-a-provider-secret", algorithm="HS256")
        with self.assertRaisesRegex(ValueError, "Token algorithm does not match provider configuration"):
            self._decode(hmac_token if isinstance(hmac_token, str) else hmac_token.decode("ascii"))

    def test_required_issuer_audience_and_time_claims_reject_invalid_tokens(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("amr.public.key", self.env.registry.models)
        self._configure_public_key("RS256")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._key_record(key, "RS256", "synthetic-uat08-kid")
        disabled_options = {
            "verify_signature": False, "verify_iss": False, "verify_aud": False,
            "verify_exp": False, "verify_nbf": False, "require": [],
        }
        invalid_claim_cases = (
            ({"iss": "https://wrong-issuer.invalid"}, jwt.InvalidIssuerError),
            ({"aud": "wrong-audience"}, jwt.InvalidAudienceError),
            ({"exp": int(time.time()) - 30}, jwt.ExpiredSignatureError),
            ({"nbf": int(time.time()) + 300}, jwt.ImmatureSignatureError),
            ({"exp": None}, jwt.MissingRequiredClaimError),
        )
        for changes, error_type in invalid_claim_cases:
            with self.subTest(claims=tuple(changes)):
                token = self._token(key, claims=changes)
                with self.assertRaises(error_type):
                    self._decode(token, options=disabled_options)

        # Omission is distinct from malformed values; all required claims fail closed.
        now = int(time.time())
        missing_claim_payloads = (
            {"aud": self.audience, "exp": now + 300},
            {"iss": self.issuer, "exp": now + 300},
            {"iss": self.issuer, "aud": self.audience},
        )
        for payload in missing_claim_payloads:
            with self.subTest(missing=tuple(set(("iss", "aud", "exp")) - set(payload))):
                token = jwt.encode(payload, key, algorithm="RS256",
                                   headers={"kid": "synthetic-uat08-kid"})
                token = token if isinstance(token, str) else token.decode("ascii")
                with self.assertRaises(jwt.MissingRequiredClaimError):
                    self._decode(token, options=disabled_options)

    def test_malformed_serialized_token_rejected(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("amr.public.key", self.env.registry.models)
        self._configure_public_key("RS256")
        with self.assertRaises(jwt.DecodeError):
            self._decode("not-a-jwt")

    def test_missing_audience_and_invalid_issuer_configuration_rejected(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("amr.public.key", self.env.registry.models)
        self._configure_public_key("RS256")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._key_record(key, "RS256", "synthetic-uat08-config-kid")
        token = self._token(key, kid="synthetic-uat08-config-kid")
        helper = self.env["amr.oidc.helper"]
        with self.assertRaisesRegex(ValueError,
                                    "A key identifier and non-empty audience are required"):
            helper.decode(token)

        params = self.env["ir.config_parameter"].sudo()
        for issuer in ("", "http://provider-verifier.invalid"):
            with self.subTest(issuer_scheme=issuer.split(":", 1)[0]):
                params.set_param("web.base.url", issuer)
                with self.assertRaisesRegex(ValueError, "A valid HTTPS issuer is required"):
                    self._decode(token)

    def test_inactive_key_and_algorithm_key_mismatch_reject(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        self.assertIn("amr.public.key", self.env.registry.models)
        self._configure_public_key("RS256")
        rs_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._key_record(rs_key, "RS256", "synthetic-uat08-inactive", active=False)
        inactive = self._token(rs_key, kid="synthetic-uat08-inactive")
        self._assert_public_key_unavailable(inactive)

        mismatched_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._key_record(mismatched_key, "ES256", "synthetic-uat08-mismatch")
        mismatch = self._token(mismatched_key, algorithm="RS256",
                               kid="synthetic-uat08-mismatch")
        self._assert_public_key_unavailable(mismatch)
