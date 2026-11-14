"""Registered regression for omitted versus explicitly-null token audience."""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

class TestAccessTokenAudiencePresence(TransactionCase):

    def setUp(self):
        super(TestAccessTokenAudiencePresence, self).setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            "amr_token.expires_in", "900")

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

        # Explicit None must not be reinterpreted as an omitted audience.
        with self.assertRaisesRegex(ValueError, "audience"):
            user.get_access_token(audience=None)

        with self.assertRaisesRegex(ValueError, "audience"):
            self.env["res.users"]._get_access_token(
                user.id, None, 60
            )

    def _configure_url_wrapper_signing(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://configured-origin.invalid")

    def test_user_resource_overrides_conflicting_audience_shapes(self):
        self._configure_url_wrapper_signing()
        user = self.env.user
        for case_id, conflict in (("string", "wrong-audience"),
                                  ("list", ["wrong-audience", "other"])):
            with self.subTest(case_id=case_id):
                resource = "https://resource.invalid/%s" % case_id
                token = user.get_access_token(resource=resource, audience=conflict)
                payload = self.env["amr.oidc.helper"].decode(token, audience=resource)
                self.assertEqual(payload["aud"], resource)
                self.assertNotIn("resource", payload)

    def test_user_invalid_resource_types_rejected_without_audience_fallback(self):
        invalid_resources = [[], (), {}, object(), 17, True, None]
        for index, resource in enumerate(invalid_resources):
            with self.subTest(case_id="invalid_resource_type_%s" % index):
                with self.assertRaisesRegex(ValueError, "resource"):
                    self.env.user.get_access_token(
                        resource=resource, audience="valid-fallback"
                    )

    def test_user_empty_resource_rejected_without_audience_fallback(self):
        for case_id, resource in (("empty", ""), ("whitespace", " \t ")):
            with self.subTest(case_id=case_id):
                with self.assertRaisesRegex(ValueError, "resource"):
                    self.env.user.get_access_token(
                        resource=resource, audience="valid-fallback"
                    )

    def test_add_url_access_token_rejects_url_bearer_by_default(self):
        self._configure_url_wrapper_signing()
        with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):
            self.env.user.add_url_access_token(url="https://wrapper-origin.invalid/path")

    def test_add_url_access_token_rejects_explicit_none_without_signing(self):
        with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):
            self.env.user.add_url_access_token(
                url="https://wrapper-origin.invalid/path", audience=None
            )

    def test_get_auto_login_url_rejects_url_bearer_by_default(self):
        self._configure_url_wrapper_signing()
        with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):
            self.env.user.get_auto_login_url(url=None)

    def test_get_auto_login_url_rejects_explicit_none_without_signing(self):
        with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):
            self.env.user.get_auto_login_url(
                url="https://wrapper-origin.invalid/path", audience=None
            )

    def test_add_url_auto_login_rejects_explicit_audience_without_signing(self):
        with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):
            self.env.user.add_url_access_token(
                url="https://wrapper-origin.invalid/path",
                url_type="auto_login",
                audience="explicit-aud",
            )

    def test_add_url_auto_login_rejects_explicit_none_without_signing(self):
        with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):
            self.env.user.add_url_access_token(
                url="https://wrapper-origin.invalid/path",
                url_type="auto_login",
                audience=None,
            )
