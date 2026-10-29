# -*- coding: utf-8 -*-
import base64
import json
from urllib.parse import quote_plus, urlencode

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("-at_install", "post_install")
class TestTokenClientAuthHttp(HttpCase):
    def _client(self, client_id, secret, method=None, active=True, confidential=True):
        values = {"client_id": client_id, "active": active, "is_confidential": confidential}
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

    def _assert_error(self, response, error, status=400, basic=False):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.json().get("error"), error)
        self.assertEqual(response.headers.get("WWW-Authenticate"), "Basic" if basic else None)
        for field in ("access_token", "refresh_token", "id_token"):
            self.assertNotIn(field, response.json())

    def test_missing_credentials_return_400_without_basic_challenge(self):
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"})
        self._assert_error(response, "invalid_client")

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

    def test_client_secret_post_is_an_available_opt_in_authentication_method(self):
        selection = dict(self.env["oidc.client"]._fields["authentication_method"].selection)
        self.assertIn("client_secret_post", selection)
        self.assertEqual(self.env["oidc.client"].default_get(["authentication_method"])
                         ["authentication_method"], "client_secret")

    def test_legacy_client_secret_rejects_body_credentials(self):
        client = self._client("legacy-post", "legacy-secret")
        response = self._post_credentials(client, "legacy-secret")
        self._assert_error(response, "invalid_client")

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
        self._assert_error(post_response, "invalid_client")

    def test_mixed_duplicate_and_query_credentials_are_invalid_request(self):
        client = self._client("ambiguous-client", "ambiguous-secret")
        encoded = base64.b64encode((client.client_id + ":ambiguous-secret").encode()).decode()
        mixed = self.url_open("/oidc/token", data={"client_id": client.client_id, "client_secret": "ambiguous-secret", "grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        conflicting = self.url_open("/oidc/token", data={"client_id": "different-client", "client_secret": "different-secret", "grant_type": "client_credentials"}, headers={"Authorization": "Basic " + encoded})
        duplicate = self.url_open("/oidc/token", data="client_id=ambiguous-client&client_id=ambiguous-client&client_secret=ambiguous-secret&grant_type=client_credentials", headers={"Content-Type": "application/x-www-form-urlencoded"})
        query = self.url_open("/oidc/token?client_id=ambiguous-client&client_secret=", data={"grant_type": "client_credentials"})
        for response in (mixed, conflicting, duplicate, query):
            self._assert_error(response, "invalid_request")
            self.assertNotIn("ambiguous-secret", response.content.decode())

    def test_partial_post_credentials_are_invalid_client(self):
        client = self._client("partial-post", "partial-secret", "client_secret_post")
        for credentials in ({"client_id": client.client_id},
                            {"client_secret": "partial-secret"},
                            {"client_id": client.client_id, "client_secret": ""}):
            with self.subTest(fields=sorted(credentials)):
                response = self.url_open("/oidc/token", data=dict(
                    credentials, grant_type="client_credentials"))
                self._assert_error(response, "invalid_client")

    def test_rejects_valid_body_credentials_for_legacy_and_explicit_basic(self):
        clients = (
            self._client("legacy-body", "legacy-body-secret"),
            self._client("explicit-body", "explicit-body-secret", "client_secret_basic"),
        )
        for client, secret in zip(clients, ("legacy-body-secret", "explicit-body-secret")):
            response = self._post_credentials(client, secret)
            self._assert_error(response, "invalid_client")

    def _basic_request(self, client_id, secret):
        pair = quote_plus(client_id, safe="") + ":" + quote_plus(secret, safe="")
        encoded = base64.b64encode(pair.encode("ascii")).decode("ascii")
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
        self._assert_error(response, "invalid_request")

    def test_explicit_post_authenticates_and_all_grants_stay_fail_closed(self):
        client = self._client("selected-post", "selected-secret", "client_secret_post")
        basic = self._client("selected-basic", "selected-secret", "client_secret_basic")
        grants = (None, "client_credentials", "password", "refresh_token",
                  "authorization_code", "urn:ietf:params:oauth:grant-type:jwt-bearer",
                  "challenge_approval", "digital_signature", "untrusted-grant-canary")
        descriptions = set()
        pair = quote_plus(basic.client_id) + ":selected-secret"
        header = "Basic " + base64.b64encode(pair.encode("ascii")).decode("ascii")
        for method in ("basic", "post"):
            for grant in grants:
                with self.subTest(method=method, grant=grant):
                    data = {} if grant is None else {"grant_type": grant}
                    headers = {"Content-Type": "application/x-www-form-urlencoded"}
                    if method == "basic":
                        headers["Authorization"] = header
                    else:
                        data.update(client_id=client.client_id, client_secret="selected-secret")
                    # A truthy body keeps HttpCase.url_open on POST for missing grant.
                    response = self.url_open("/oidc/token", data=urlencode(data) or "ignored=1",
                                             headers=headers)
                    self._assert_error(response, "unsupported_grant_type")
                    description = response.json().get("error_description")
                    self.assertNotIn("untrusted-grant-canary", description or "")
                    descriptions.add(description)
        self.assertEqual(len(descriptions), 1)

    def test_failed_post_and_public_clients_do_not_fall_back(self):
        post = self._client("failed-post", "correct-secret", "client_secret_post")
        inactive = self._client("inactive-post", "correct-secret", "client_secret_post", active=False)
        public = self._client("public-post", "correct-secret", "client_secret_post", confidential=False)
        for client, secret in ((post, "wrong-secret"), (inactive, "correct-secret"),
                               (public, "correct-secret")):
            with self.subTest(client=client.client_id):
                self._assert_error(self._post_credentials(client, secret), "invalid_client")
        for method in ("client_secret", "client_secret_basic"):
            client = self._client("public-" + method, "correct-secret", method, confidential=False)
            self._assert_error(self._basic_request(client.client_id, "correct-secret"),
                               "invalid_client", 401, basic=True)
        self._assert_error(self._basic_request(post.client_id, "correct-secret"),
                           "invalid_client", 401, basic=True)
        self._assert_error(self.url_open("/oidc/token", data={
            "client_id": "unknown-post", "client_secret": "synthetic-secret",
            "grant_type": "client_credentials"}), "invalid_client")
        empty = self._client("empty-post-verifier", "synthetic-secret", "client_secret_post")
        empty.sudo().write({"client_secret_hash": False})
        self._assert_error(self._post_credentials(empty, "synthetic-secret"), "invalid_client")

    def test_non_basic_and_malformed_basic_have_distinct_errors(self):
        for header in ("Bearer synthetic-token", "Digest synthetic-token"):
            response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"},
                                     headers={"Authorization": header})
            self._assert_error(response, "invalid_request")
        for header in ("Basic", "Basic !!!", "Basic " + base64.b64encode(b"no-colon").decode()):
            response = self.url_open("/oidc/token", data={"grant_type": "client_credentials"},
                                     headers={"Authorization": header})
            self._assert_error(response, "invalid_client", 401, basic=True)

    def test_duplicate_consumed_parameters_and_malformed_forms(self):
        client = self._client("form-post", "form-secret", "client_secret_post")
        pairs = [("client_id", client.client_id), ("client_secret", "form-secret"),
                 ("grant_type", "client_credentials")]
        for name in ("client_id", "client_secret", "grant_type"):
            for value in (dict(pairs)[name], ""):
                response = self.url_open("/oidc/token", data=urlencode(pairs + [(name, value)]),
                                         headers={"Content-Type": "application/x-www-form-urlencoded"})
                self._assert_error(response, "invalid_request")
        for body in ("client_id=%ZZ", "client_id=%FF", "client_id=one&bare", "client_id=%"):
            response = self.url_open("/oidc/token", data=body,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
            self._assert_error(response, "invalid_request")
        for name in ("client_id", "client_secret"):
            response = self.url_open("/oidc/token?" + name + "=", data={"grant_type": "client_credentials"})
            self._assert_error(response, "invalid_request")

    def test_unsupported_media_are_not_credential_channels(self):
        for media, body in (("application/json", '{"client_id":"synthetic"}'),
                            ("multipart/form-data; boundary=synthetic", "--synthetic--\r\n"),
                            ("text/plain", "client_id=synthetic")):
            with self.subTest(media=media):
                response = self.url_open("/oidc/token", data=body, headers={"Content-Type": media})
                self._assert_error(response, "invalid_request")

    def test_post_form_encoding_and_ignored_parameters(self):
        client = self._client("form:plus+ spaceé", "secret:plus+ spaceé", "client_secret_post")
        response = self.url_open("/oidc/token", data={
            "client_id": client.client_id, "client_secret": "secret:plus+ spaceé",
            "grant_type": "client_credentials", "unrecognized": "ignored"})
        self._assert_error(response, "unsupported_grant_type")
        self._client("ignored-basic", "synthetic-secret")
        encoded = base64.b64encode(b"ignored-basic:synthetic-secret").decode("ascii")
        response = self.url_open("/oidc/token", data={"grant_type": "client_credentials", "unrecognized": "ignored"},
                                 headers={"Authorization": "Basic " + encoded})
        self._assert_error(response, "unsupported_grant_type")

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
