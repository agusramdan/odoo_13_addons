"""Registered regression for omitted versus explicitly-null token audience."""
import time

from odoo.tests.common import TransactionCase


class TestAccessTokenAudiencePresence(TransactionCase):
    def test_access_token_omission_defaults_but_explicit_none_is_rejected(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://oidc-regression.invalid")

        user = self.env.user
        token = user.get_access_token()
        expected_audience = params.get_param("database.uuid")
        self.assertTrue(expected_audience)
        payload = self.env["amr.oidc.helper"].decode(
            token, audience=expected_audience
        )
        self.assertEqual(payload["aud"], expected_audience)

        # The public method rejects explicit None; the cache boundary must not
        # reinterpret it as an omitted audience either.
        with self.assertRaisesRegex(ValueError, "audience"):
            user.get_access_token(audience=None)

        # Use a fresh bucket so this private-boundary assertion cannot pass or
        # fail based on the default-audience token cached above.
        fresh_bucket = int(time.time() / 300) + 1
        with self.assertRaisesRegex(ValueError, "audience"):
            self.env["res.users"]._get_access_token(
                user.id, None, fresh_bucket
            )
