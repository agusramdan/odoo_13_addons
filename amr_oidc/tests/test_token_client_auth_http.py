# -*- coding: utf-8 -*-
import base64
import json

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("-at_install", "post_install")
class TestTokenClientAuthHttp(HttpCase):
    def _client(self, client_id, secret, method=None, active=True):
        values = {"client_id": client_id, "active": active}
        if method:
            values["authentication_method"] = method
        client = self.env["oidc.client"].create(values)
        client.sudo().write({"client_secret_hash": self.env["res.users"]._crypt_context().hash(secret)})
        return client

    def _post_credentials(self, client, secret, query=""):
        return self.url_open("/oidc/token" + query, data={
            "client_id": client.client_id, "client_secret": secret,
            "grant_type": "client_credentials",
        })

    def test_missing_credentials_return_basic_challenge(self):
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic")
        self.assertEqual(response.json().get("error"), "invalid_client")

    def test_bad_basic_client_credentials_return_oauth_401_challenge(self):
        secret = "never-echo-this-secret"
        encoded = base64.b64encode(("missing-token-auth-client:" + secret).encode()).decode()
        response = self.url_open(
            "/oidc/token",
            data={"grant_type": "client_credentials"},
            headers={"Authorization": "Basic " + encoded},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic")
        self.assertIn("application/json", response.headers.get("Content-Type", ""))
        self.assertEqual(json.loads(response.content).get("error"), "invalid_client")
        self.assertNotIn(secret, response.content.decode("utf-8"))

    def test_basic_decodes_components_after_splitting_first_colon(self):
        client_id = "encoded:client +space"
        secret = "secret:with+space value"
        client = self.env["oidc.client"].create({"client_id": client_id})
        verifier = self.env["res.users"]._crypt_context().hash(secret)
        client.sudo().write({"client_secret_hash": verifier})
        credentials = "encoded%3Aclient+%2Bspace:secret%3Awith%2Bspace+value"
        encoded = base64.b64encode(credentials.encode()).decode()
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "unsupported_grant_type")

    def test_basic_rejects_malformed_percent_escape(self):
        encoded = base64.b64encode(b"client%ZZ:secret").decode()
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "invalid_client")

    def test_valid_client_auth_preserves_unsupported_grant_response(self):
        client = self.env["oidc.client"].create({"client_id": "token-auth-valid-client"})
        secret = "token-auth-valid-secret"
        verifier = self.env["res.users"]._crypt_context().hash(secret)
        client.sudo().write({"client_secret_hash": verifier})
        encoded = base64.b64encode((client.client_id + ":" + secret).encode()).decode()
        response = self.url_open(
            "/oidc/token", data={"grant_type": "client_credentials"},
            headers={"Authorization": "Basic " + encoded},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "unsupported_grant_type")
        self.assertNotIn("access_token", response.json())

    def test_client_secret_post_is_not_an_available_authentication_method(self):
        selection = dict(self.env["oidc.client"]._fields["authentication_method"].selection)
        self.assertNotIn("client_secret_post", selection)

    def test_legacy_client_secret_rejects_body_credentials(self):
        client = self._client("legacy-post", "legacy-secret")
        response = self._post_credentials(client, "legacy-secret")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "invalid_client")

    def test_legacy_alias_accepts_basic_credentials(self):
        client = self._client("legacy-basic", "legacy-secret")
        encoded = base64.b64encode((client.client_id + ":legacy-secret").encode()).decode()
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "unsupported_grant_type")

    def test_explicit_basic_accepts_basic_credentials(self):
        client = self._client("explicit-basic-valid", "explicit-secret", "client_secret_basic")
        encoded = base64.b64encode((client.client_id + ":explicit-secret").encode()).decode()
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "unsupported_grant_type")

    def test_explicit_basic_rejects_body_credentials(self):
        basic = self._client("explicit-basic", "secret-basic", "client_secret_basic")
        post_response = self._post_credentials(basic, "secret-basic")
        self.assertEqual(post_response.status_code, 401)
        self.assertEqual(post_response.json().get("error"), "invalid_client")
        self.assertIsNone(post_response.headers.get("WWW-Authenticate"))

    def test_rejects_mixed_duplicate_query_and_partial_credentials(self):
        client = self._client("ambiguous-client", "ambiguous-secret")
        encoded = base64.b64encode((client.client_id + ":ambiguous-secret").encode()).decode()
        mixed = self.url_open("/oidc/token", data={"client_id": client.client_id, "client_secret": "ambiguous-secret", "grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        conflicting = self.url_open("/oidc/token", data={"client_id": "different-client", "client_secret": "different-secret", "grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        duplicate = self.url_open("/oidc/token", data="client_id=ambiguous-client&client_id=ambiguous-client&client_secret=ambiguous-secret&grant_type=client_credentials", headers={"Content-Type": "application/x-www-form-urlencoded"})
        query = self.url_open("/oidc/token?client_id=ambiguous-client&client_secret=", data={"grant_type": "client_credentials"})
        partial = self.url_open("/oidc/token", data={"client_id": client.client_id, "grant_type": "client_credentials"})
        for response in (mixed, conflicting, duplicate, query, partial):
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json().get("error"), "invalid_client")
            self.assertNotIn("ambiguous-secret", response.content.decode())

    def test_rejects_valid_body_credentials_for_legacy_and_explicit_basic(self):
        clients = (
            self._client("legacy-body", "legacy-body-secret"),
            self._client("explicit-body", "explicit-body-secret", "client_secret_basic"),
        )
        for client, secret in zip(clients, ("legacy-body-secret", "explicit-body-secret")):
            response = self._post_credentials(client, secret)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json().get("error"), "invalid_client")
            self.assertIsNone(response.headers.get("WWW-Authenticate"))

    def _basic_request(self, client_id, secret):
        encoded = base64.b64encode((client_id + ":" + secret).encode()).decode()
        return self.url_open(
            "/oidc/token", data={"grant_type": "client_credentials"},
            headers={"Authorization": "Basic " + encoded},
        )

    def test_wrong_basic_secret_is_rejected(self):
        client = self._client("wrong-secret-client", "correct-secret")
        response = self._basic_request(client.client_id, "wrong-secret")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "invalid_client")
        self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic")

    def test_missing_verifier_is_rejected(self):
        client = self.env["oidc.client"].create({"client_id": "missing-verifier-client"})
        response = self._basic_request(client.client_id, "any-secret")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "invalid_client")
        self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic")

    def test_inactive_client_and_unsupported_method_are_rejected(self):
        inactive = self._client("inactive-auth", "inactive-secret", active=False)
        unsupported = self._client("unsupported-auth", "unsupported-secret", method="private_key_jwt")
        for client, secret in ((inactive, "inactive-secret"), (unsupported, "unsupported-secret")):
            response = self._basic_request(client.client_id, secret)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json().get("error"), "invalid_client")
            self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic")

    def test_parsed_form_content_type_rejects_mixed_body_credentials(self):
        client = self._client("parsed-content-type", "parsed-secret")
        encoded = base64.b64encode((client.client_id + ":parsed-secret").encode()).decode()
        response = self.url_open(
            "/oidc/token",
            data={"client_id": "parsed-content-type", "client_secret": "parsed-secret", "grant_type": "client_credentials"},
            headers={
                "Authorization": "Basic " + encoded,
                "Content-Type": "Application/X-WWW-Form-Urlencoded; Charset=UTF-8",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("error"), "invalid_client")
        self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic")

    def test_effective_route_registry_has_one_post_token_route(self):
        routes = [rule for rule in self.env["ir.http"].routing_map().iter_rules()
                  if rule.rule == "/oidc/token" and "POST" in rule.methods]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].methods, {"POST"})
        self.assertEqual(routes[0].endpoint.method.__name__, "api_oidc_token")
        from odoo.addons.amr_oidc.controllers.main import ControllerOIDC
        metadata = ControllerOIDC.api_oidc_token.routing
        self.assertEqual(metadata.get("routes"), ["/oidc/token"])
        self.assertEqual(metadata.get("methods"), ["POST"])
        self.assertEqual(metadata.get("type"), "http")
        self.assertEqual(metadata.get("auth"), "none")
        self.assertFalse(metadata.get("csrf"))

    def test_http_token_dispatches_to_oidc_helper(self):
        registry = self.env.registry
        self.assertIn("amr.oidc.helper", registry.models)
        self.assertIn("amr.token.helper", registry.models)
        oidc_model = registry.models["amr.oidc.helper"]
        token_model = registry.models["amr.token.helper"]
        oidc_original = oidc_model.oidc_token
        token_original = token_model.oidc_token
        try:
            oidc_model.oidc_token = lambda record, **kwargs: {"status": 200, "source": "oidc-helper"}
            token_model.oidc_token = lambda record, **kwargs: {"status": 200, "source": "token-helper"}
            response = self.url_open("/oidc/token", data={"grant_type": "probe"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json().get("source"), "oidc-helper")
        finally:
            oidc_model.oidc_token = oidc_original
            token_model.oidc_token = token_original
