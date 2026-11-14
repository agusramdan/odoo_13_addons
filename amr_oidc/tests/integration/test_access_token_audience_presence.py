"""Provider-owned client/helper audience regressions; no glue dependency."""
from odoo.tests.common import TransactionCase

class TestProviderAudienceHelpers(TransactionCase):
    def _configure_signing(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("amr_token.signature_type", "secret")
        params.set_param("amr_token.secret_algorithm", "HS256")
        params.set_param("amr_token.secret", "synthetic-test-signing-secret")
        params.set_param("web.base.url", "https://configured-origin.invalid")

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

    def test_helper_resource_overrides_conflicting_audience_shapes(self):
        self._configure_signing()
        helper = self.env["amr.oidc.helper"]
        resource = "https://resource.invalid/api"
        for case_id, conflict in (("string", "wrong-audience"),
                                  ("list", ["wrong-audience", "other"])):
            with self.subTest(case_id=case_id):
                token, _, _ = helper._generate_token(
                    {"resource": resource}, audience=conflict
                )
                payload = helper.decode(token, audience=resource)
                self.assertEqual(payload["aud"], resource)
                self.assertNotIn("resource", payload)

    def test_helper_invalid_resource_values_rejected_before_signing(self):
        helper = self.env["amr.oidc.helper"]
        invalid_resources = [[], (), {}, object(), 17, True, None, "", " \t "]
        for index, resource in enumerate(invalid_resources):
            with self.subTest(case_id="invalid_resource_%s" % index):
                with self.assertRaisesRegex(ValueError, "resource"):
                    helper._generate_token(
                        {"resource": resource}, audience="valid-fallback"
                    )
