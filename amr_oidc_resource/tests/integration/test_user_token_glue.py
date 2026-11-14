# -*- coding: utf-8 -*-
"""Runtime actor/audience regressions for the optional user glue."""
import jwt
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase
from unittest import mock


class TestUserTokenGlueActorAndIssuer(TransactionCase):
    def _configure_secret(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-actor-target-secret-012345")
        params.set_param("amr_token.expires_in", "900")
        params.set_param("web.base.url", "https://actor-target.invalid")
        return params

    def test_malformed_ttl_configuration_keeps_helper_error_before_signing(self):
        params = self._configure_secret()
        params.set_param("amr_token.expires_in", "")
        with mock.patch("jwt.encode") as signer:
            with self.assertRaises(ValueError):
                self.env.user.get_access_token(audience="ttl-config-audience")
        signer.assert_not_called()

    def _new_target(self, login):
        return self.env["res.users"].create({
            "name": "Synthetic target " + login,
            "login": login,
            "email": login + "@example.invalid",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })

    def test_self_issuance_and_system_cross_user_signed_target_claims(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
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
        self._configure_secret()
        helper = self.env["amr.oidc.helper"]
        audience = ["actor-list-audience", "actor-list-secondary"]
        other_audience = ["actor-list-other"]
        with mock.patch("jwt.encode", wraps=jwt.encode) as signer:
            token = self.env.user.get_access_token(audience=audience)
            self.env.user.get_access_token(audience=audience)
            other_token = self.env.user.get_access_token(audience=other_audience)
            self.assertEqual(signer.call_count, 3)
            with self.assertRaisesRegex(ValueError, "A valid audience is required"):
                self.env.user.get_access_token(audience=[])
            self.assertEqual(signer.call_count, 3)

        claims = helper.decode(token, audience=audience)
        self.assertEqual(claims["aud"], audience)
        other_claims = helper.decode(other_token, audience=other_audience)
        self.assertEqual(other_claims["aud"], other_audience)

    def test_non_system_cross_user_denial_precedes_signing(self):
        self._configure_secret()
        actor = self._new_target("synthetic-nonsystem-actor")
        target = self._new_target("synthetic-nonsystem-target")
        with mock.patch("jwt.encode", wraps=jwt.encode) as signer:
            with self.assertRaises(AccessError):
                target.with_user(actor).get_access_token(
                    audience="actor-target-aud")
        signer.assert_not_called()

    def test_signing_key_removal_after_warm_issuance_rejects(self):
        params = self._configure_secret()
        self.env.user.get_access_token(audience="key-rotation-audience")
        params.set_param("amr_token.secret", "")
        with self.assertRaisesRegex(ValueError, "JWT Secret not set"):
            self.env.user.get_access_token(audience="key-rotation-audience")

    def test_signing_configuration_change_uses_new_key_and_ttl(self):
        params = self._configure_secret()
        old_token = self.env.user.get_access_token(audience="key-rotation-audience")
        new_secret = "synthetic-rotated-signing-secret-012345"
        params.set_param("amr_token.secret", new_secret)
        params.set_param("amr_token.expires_in", "120")
        fixed_time = 1800000000
        with mock.patch("odoo.addons.amr_oidc.models.token_helper.time.time", return_value=fixed_time):
            new_token = self.env.user.get_access_token(audience="key-rotation-audience")
        claims = jwt.decode(new_token, new_secret, algorithms=["HS256"],
                            options={"verify_exp": False, "verify_aud": False})
        self.assertEqual(claims["exp"], fixed_time + 120)
        self.assertEqual(claims["aud"], "key-rotation-audience")
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(old_token, new_secret, algorithms=["HS256"],
                       options={"verify_exp": False, "verify_aud": False})

    def test_persistent_access_token_storage_remains_unsupported(self):
        self.assertIn("amr.oidc.helper", self.env.registry.models)
        with self.assertRaises(UserError) as raised:
            self.env.user.create_access_token(audience="synthetic-audience")
        self.assertEqual(raised.exception.args[0],
                         "Persistent access-token storage is not available")
        self.assertEqual(raised.exception.args[1:], ("",))
        self.assertNotIn("synthetic-audience", str(raised.exception))
        self.assertNotIn("amr.token", self.env.registry.models)
