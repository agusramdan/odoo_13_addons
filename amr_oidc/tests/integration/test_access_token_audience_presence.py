"""Registered regression for omitted versus explicitly-null token audience."""
import time
from urllib.parse import parse_qs, urlparse

from odoo.tests.common import TransactionCase


class TestAccessTokenAudiencePresence(TransactionCase):
    def test_client_create_access_token_accepts_aud_only_alias(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://oidc-regression.invalid")
        client = self.env["oidc.client"].create({
            "client_id": "aud-only-alias-regression-client",
            "web_base_url": "https://oidc-regression.invalid",
        })

        token, _redirect_uri, _expires_in = client._create_access_token(
            aud="alias-audience"
        )
        payload = self.env["amr.oidc.helper"].decode(
            token, audience="alias-audience"
        )
        self.assertEqual(payload["aud"], "alias-audience")
        self.assertNotIn("resource", payload)

    def test_client_create_access_token_omitted_audience_uses_database_uuid(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://oidc-regression.invalid")
        client = self.env["oidc.client"].create({
            "client_id": "audience-omission-client",
            "web_base_url": "https://oidc-regression.invalid",
        })

        try:
            token, _redirect_uri, _expires_in = client._create_access_token()
        except ValueError as error:
            self.fail(
                "_create_access_token() with audience omitted should use the "
                "database UUID default; it raised ValueError: %s" % error
            )

        expected_audience = params.get_param("database.uuid")
        self.assertTrue(expected_audience)
        payload = self.env["amr.oidc.helper"].decode(token, audience=expected_audience)
        self.assertEqual(payload["aud"], expected_audience)
        self.assertNotIn("resource", payload)

    def test_client_create_access_token_explicit_none_does_not_use_aud_alias(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://oidc-regression.invalid")
        client = self.env["oidc.client"].create({
            "client_id": "audience-none-alias-client",
            "web_base_url": "https://oidc-regression.invalid",
        })

        with self.assertRaisesRegex(ValueError, "audience"):
            client._create_access_token(
                audience=None, aud="fallback-audience"
            )

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

    def test_client_credentials_omitted_audience_defaults_and_none_is_rejected(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://oidc-regression.invalid")
        client = self.env["oidc.client"].create({
            "client_id": "client-credentials-audience-presence",
            "web_base_url": "https://oidc-regression.invalid",
        })
        secret = "synthetic-client-secret-for-audience-presence"
        verifier = self.env["res.users"]._crypt_context().hash(secret)
        client.sudo().write({"client_secret_hash": verifier})

        result = client._client_credentials(client_secret=secret)
        token = result["access_token"]
        expected_audience = params.get_param("database.uuid")
        self.assertTrue(expected_audience)
        payload = self.env["amr.oidc.helper"].decode(
            token, audience=expected_audience
        )
        self.assertEqual(payload["aud"], expected_audience)

        with self.assertRaisesRegex(ValueError, "audience"):
            client._client_credentials(client_secret=secret, audience=None)

    def test_client_encode_omitted_audience_defaults_and_none_is_rejected(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://oidc-regression.invalid")
        client = self.env["oidc.client"].create({
            "client_id": "client-encode-audience-presence",
            "web_base_url": "https://oidc-regression.invalid",
        })

        token, _, _ = client._encode()
        expected_audience = params.get_param("database.uuid")
        self.assertTrue(expected_audience)
        payload = self.env["amr.oidc.helper"].decode(
            token, audience=expected_audience
        )
        self.assertEqual(payload["aud"], expected_audience)

        with self.assertRaisesRegex(ValueError, "audience"):
            client._encode(audience=None)

    def _configure_url_wrapper_signing(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://configured-origin.invalid")

    def _decode_wrapper_token(self, token, audience):
        payload = self.env["amr.oidc.helper"].decode(token, audience=audience)
        self.assertEqual(payload["aud"], audience)
        self.assertNotIn("resource", payload)
        return payload

    def test_add_url_access_token_omitted_audience_uses_url_origin(self):
        self._configure_url_wrapper_signing()
        url = "https://wrapper-origin.invalid/path"
        result = self.env.user.add_url_access_token(url=url)
        token = parse_qs(urlparse(result).query)["access_token"][0]
        self._decode_wrapper_token(token, "https://wrapper-origin.invalid")

    def test_add_url_access_token_explicit_none_rejects_audience(self):
        self._configure_url_wrapper_signing()
        with self.assertRaisesRegex(ValueError, "audience"):
            self.env.user.add_url_access_token(
                url="https://wrapper-origin.invalid/path", audience=None
            )

    def test_get_auto_login_url_omitted_audience_uses_configured_origin(self):
        self._configure_url_wrapper_signing()
        result = self.env.user.get_auto_login_url(url=None)
        token = parse_qs(urlparse(result).query)["token_access"][0]
        self._decode_wrapper_token(token, "https://configured-origin.invalid")

    def test_get_auto_login_url_explicit_none_rejects_audience(self):
        self._configure_url_wrapper_signing()
        with self.assertRaisesRegex(ValueError, "audience"):
            self.env.user.get_auto_login_url(
                url="https://wrapper-origin.invalid/path", audience=None
            )

    def test_add_url_access_token_auto_login_preserves_explicit_audience(self):
        self._configure_url_wrapper_signing()
        result = self.env.user.add_url_access_token(
            url="https://wrapper-origin.invalid/path",
            url_type="auto_login",
            audience="explicit-aud",
        )
        token = parse_qs(urlparse(result).query)["token_access"][0]
        payload = self.env["amr.oidc.helper"].decode(token, audience="explicit-aud")
        self.assertEqual(payload["aud"], "explicit-aud")
        self.assertNotIn("resource", payload)

    def test_add_url_access_token_auto_login_forwards_explicit_none(self):
        self._configure_url_wrapper_signing()
        with self.assertRaisesRegex(ValueError, "audience"):
            self.env.user.add_url_access_token(
                url="https://wrapper-origin.invalid/path",
                url_type="auto_login",
                audience=None,
            )
