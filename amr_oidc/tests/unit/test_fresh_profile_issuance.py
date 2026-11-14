"""Fresh-profile client issuance boundary tests; Odoo ORM is intentionally mocked."""
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest import mock

import jwt
from werkzeug.datastructures import Headers, MultiDict
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ADDON = Path(__file__).resolve().parents[2]


def load_support():
    spec = importlib.util.spec_from_file_location("fresh_issuance_support", ADDON / "tests" / "support.py")
    if spec is None or spec.loader is None:
        raise ImportError("test support is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_helper(support):
    crypto = {name: ModuleType(name) for name in (
        "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
        "cryptography.hazmat.primitives.asymmetric")}
    crypto["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
    crypto["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
    with mock.patch.dict(sys.modules, crypto):
        return support.load("models/token_helper.py")


class SettingsEnv(dict):
    user: object


class FreshProfileControllerTests(unittest.TestCase):
    def setUp(self):
        self.support = load_support()
        self.module = self.support.load_controller()
        self.controller = self.module.ControllerOIDC()
        self.helper = mock.Mock()
        self.helper._fresh_profile_is_enabled.return_value = True
        self.module.request.env = {"amr.oidc.helper": self.helper}
        self.module.request.httprequest = SimpleNamespace(
            headers=Headers([("Authorization", "Basic bWFjaGluZS1hOnN5bnRoZXRpYy1zZWNyZXQ=")]),
            form=MultiDict([("grant_type", "client_credentials"), ("scope", "")]),
            args=MultiDict(), method="POST", is_secure=True,
        )

    def test_route_authenticates_basic_and_issues_only_supported_fresh_grant(self):
        self.helper._issue_fresh_client_token.return_value = {
            "access_token": "opaque", "token_type": "Bearer", "expires_in": 900,
        }
        response = self.controller.api_oidc_token()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(response.headers.get("Pragma"), "no-cache")
        self.assertEqual(self.support.json.loads(response.data), {
            "access_token": "opaque", "token_type": "Bearer", "expires_in": 900,
        })
        self.helper._issue_fresh_client_token.assert_called_once_with(
            "machine-a", "synthetic-secret", "")

    def test_repeated_fresh_grant_type_is_rejected_before_issuing(self):
        self.module.request.httprequest.form.add("grant_type", "client_credentials")

        response = self.controller.api_oidc_token()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.support.json.loads(response.data), {"error": "invalid_request"})
        self.helper._issue_fresh_client_token.assert_not_called()

    def test_repeated_scope_is_rejected_before_issuing(self):
        self.module.request.httprequest.form.add("scope", "other")

        response = self.controller.api_oidc_token()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.support.json.loads(response.data), {"error": "invalid_request"})
        self.helper._issue_fresh_client_token.assert_not_called()

    def test_repeated_authorization_headers_are_rejected_at_werkzeug_boundary(self):
        headers = self.module.request.httprequest.headers
        headers.add("Authorization", "Basic bWFjaGluZS1hOnN5bnRoZXRpYy1zZWNyZXQ=")

        response = self.controller.api_oidc_token()

        self.assertEqual(headers.getlist("Authorization"), [
            "Basic bWFjaGluZS1hOnN5bnRoZXRpYy1zZWNyZXQ=",
            "Basic bWFjaGluZS1hOnN5bnRoZXRpYy1zZWNyZXQ=",
        ])
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.support.json.loads(response.data), {"error": "invalid_client"})
        self.helper._issue_fresh_client_token.assert_not_called()

    def test_disabled_profile_keeps_legacy_lookup_for_repeated_grant_type(self):
        self.helper._fresh_profile_is_enabled.return_value = False
        self.helper.sudo.return_value.oidc_token.return_value = {
            "status": 400, "error": "unsupported_grant_type",
        }
        self.module.request.httprequest.form.add("grant_type", "authorization_code")

        response = self.controller.api_oidc_token()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.support.json.loads(response.data), {
            "error": "unsupported_grant_type",
        })
        self.helper._issue_fresh_client_token.assert_not_called()
        self.helper.sudo.return_value.oidc_token.assert_called_once_with()

    def test_basic_credentials_form_decode_reserved_characters_before_issuing(self):
        from urllib.parse import quote_plus

        client_id = "machine:id + space"
        client_secret = "secret: /+ value"
        credentials = "{}:{}".format(
            quote_plus(client_id, safe=""), quote_plus(client_secret, safe=""))
        self.module.request.httprequest.headers["Authorization"] = "Basic {}".format(
            __import__("base64").b64encode(credentials.encode("ascii")).decode("ascii"))
        self.helper._issue_fresh_client_token.return_value = {"access_token": "opaque"}

        response = self.controller.api_oidc_token()

        self.assertEqual(response.status_code, 200)
        self.helper._issue_fresh_client_token.assert_called_once_with(
            client_id, client_secret, "")

    def test_malformed_percent_encoding_is_rejected_with_basic_challenge_before_issuing(self):
        import base64
        credentials = base64.b64encode(b"machine%GG:secret").decode("ascii")
        self.module.request.httprequest.headers["Authorization"] = "Basic {}".format(credentials)

        response = self.controller.api_oidc_token()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.support.json.loads(response.data), {"error": "invalid_client"})
        self.assertEqual(response.headers.get("WWW-Authenticate"), 'Basic realm="token"')
        self.assertNotIn("machine", response.headers.get("WWW-Authenticate", ""))
        self.helper._issue_fresh_client_token.assert_not_called()

    def test_authentication_failure_has_basic_challenge_without_secret_details(self):
        self.helper._issue_fresh_client_token.side_effect = ValueError("secret detail")

        response = self.controller.api_oidc_token()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("WWW-Authenticate"), 'Basic realm="token"')
        body = response.data.decode("utf-8")
        self.assertNotIn("synthetic-secret", body)
        self.assertNotIn("secret detail", body)

    def test_disabled_fresh_profile_preserves_unsupported_grant_contract(self):
        self.helper._fresh_profile_is_enabled.return_value = False
        self.helper.sudo.return_value.oidc_token.return_value = {
            "status": 400, "error": "unsupported_grant_type",
        }
        response = self.controller.api_oidc_token()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(response.headers.get("Pragma"), "no-cache")
        self.assertEqual(self.support.json.loads(response.data), {
            "error": "unsupported_grant_type",
        })
        self.helper._issue_fresh_client_token.assert_not_called()
        self.helper.sudo.return_value.oidc_token.assert_called_once_with()

    def test_legacy_token_error_shape_is_preserved_with_no_store_headers(self):
        helper = self.module.request.env["amr.oidc.helper"]
        helper.sudo.return_value.oidc_token.side_effect = ValueError("synthetic")
        self.module.request.httprequest.form["grant_type"] = "authorization_code"

        response = self.controller.api_oidc_token(grant_type="authorization_code")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(response.headers.get("Pragma"), "no-cache")
        self.assertEqual(self.support.json.loads(response.data), {
            "success": False, "error": "invalid_request", "error_description": "synthetic",
        })

    def test_route_rejects_caller_client_id_and_bad_auth_before_issuing(self):
        self.module.request.httprequest.form["client_id"] = "victim"
        response = self.controller.api_oidc_token()
        self.assertEqual(response.status_code, 400)
        self.helper._issue_fresh_client_token.assert_not_called()

        self.module.request.httprequest.form.pop("client_id")
        self.module.request.httprequest.is_secure = False
        response = self.controller.api_oidc_token()
        self.assertEqual(response.status_code, 400)
        self.helper._issue_fresh_client_token.assert_not_called()

        self.module.request.httprequest.is_secure = True
        self.module.request.httprequest.headers["Authorization"] = "Basic invalid"
        response = self.controller.api_oidc_token()
        self.assertEqual(response.status_code, 401)
        self.helper._issue_fresh_client_token.assert_not_called()


class FreshProfileModelBoundaryTests(unittest.TestCase):
    def test_subject_model_rejects_direct_rpc_create_write_unlink_and_forged_context(self):
        support = load_support()
        module = support.load("models/oidc_issuer_principal_subject.py")
        model = module.OidcIssuerPrincipalSubject()
        model.env = SimpleNamespace(context={})
        with self.assertRaises(support.AccessError):
            model.create({})
        with self.assertRaises(support.AccessError):
            model.write({"namespace": "https://issuer.invalid"})
        with self.assertRaises(support.AccessError):
            model.unlink()

        model.env.context = {"_oidc_subject_capability": "trusted"}
        with self.assertRaises(support.AccessError):
            model.create({})

    def test_settings_direct_rpc_requires_system_group_for_profile_and_ttl(self):
        support = load_support()
        module = support.load("models/res_config_settings.py")
        settings = type(
            "IterableSettings", (module.ResConfigSettings,),
            {"__iter__": lambda self: iter((self,))},
        )()
        params = SimpleNamespace(sudo=lambda: params,
                                 get_param=lambda key: "https://issuer.invalid")
        env = SettingsEnv({"ir.config_parameter": params})
        env.user = SimpleNamespace(has_group=lambda group: False)
        settings.env = env
        settings.amr_token_fresh_profile_issuer = "https://issuer.invalid"
        settings.amr_token_expires_in = 900
        with self.assertRaises(support.AccessError):
            settings.set_values()

    def test_settings_only_binds_on_first_explicit_activation_and_never_rebinds(self):
        support = load_support()
        module = support.load("models/res_config_settings.py")
        settings_class = type(
            "IterableSettings", (module.ResConfigSettings,),
            {"__iter__": lambda self: iter((self,))},
        )
        for configured_issuer in (None, "https://issuer.invalid"):
            with self.subTest(configured_issuer=configured_issuer):
                helper = SimpleNamespace(
                    get_issuer=lambda: "https://issuer.invalid",
                    _bind_fresh_profile_instance=mock.Mock(),
                    _require_fresh_profile_instance=mock.Mock(),
                )
                params = SimpleNamespace(
                    sudo=lambda: params,
                    get_param=lambda key: configured_issuer,
                )
                env = SettingsEnv({"ir.config_parameter": params, "amr.oidc.helper": helper})
                env.user = SimpleNamespace(has_group=lambda group: group == "base.group_system")
                settings = settings_class()
                settings.env = env
                settings.amr_token_fresh_profile_issuer = "https://issuer.invalid"
                settings.amr_token_expires_in = 900

                self.assertTrue(settings.set_values())
                if configured_issuer:
                    helper._require_fresh_profile_instance.assert_called_once_with()
                    helper._bind_fresh_profile_instance.assert_not_called()
                else:
                    helper._bind_fresh_profile_instance.assert_called_once_with()
                    helper._require_fresh_profile_instance.assert_not_called()

    def test_settings_reject_noncanonical_and_out_of_range_fresh_ttl_before_persistence(self):
        support = load_support()
        module = support.load("models/res_config_settings.py")
        settings = module.ResConfigSettings()
        params = SimpleNamespace(sudo=lambda: params,
                                 get_param=lambda key: "https://issuer.invalid")
        env = SettingsEnv({"ir.config_parameter": params})
        env.user = SimpleNamespace(has_group=lambda group: group == "base.group_system")
        settings.env = env
        for ttl in ("060", "+60", "59", "86401", True, 60.0):
            with self.subTest(ttl=ttl):
                with self.assertRaises(module.UserError):
                    settings.create([{"amr_token_expires_in": ttl}])

    def test_subject_schema_keeps_archived_uniqueness_and_no_external_acl(self):
        source = (ADDON / "models" / "oidc_issuer_principal_subject.py").read_text()
        acl = (ADDON / "security" / "ir.model.access.csv").read_text()
        self.assertIn("unique(namespace, user_id)", source)
        self.assertIn("unique(namespace, subject)", source)
        self.assertIn("ondelete='restrict'", source)
        self.assertIn("secrets.token_bytes(32).hex()", source)
        self.assertIn("access_oidc_issuer_principal_subject_deny", acl)
        self.assertIn("model_oidc_issuer_principal_subject,base.group_user,0,0,0,0", acl)


class FreshProfileTokenHelperTests(unittest.TestCase):
    def setUp(self):
        self.support = load_support()
        self.module = load_helper(self.support)
        self.helper = self.module.TokenHelper()

    def test_ttl_defaults_in_memory_and_enforces_canonical_ascii_bounds(self):
        parameter = SimpleNamespace(get_param=lambda key: None)
        self.helper.env = {"ir.config_parameter": SimpleNamespace(sudo=lambda: parameter)}
        self.assertEqual(self.helper._get_fresh_profile_ttl(), 900)
        for value in ("060", "+60", "60.0", " 60", "６０", "59", "86401", "huge"):
            with self.subTest(value=value):
                parameter.get_param = lambda key, value=value: value
                with self.assertRaises(ValueError):
                    self.helper._get_fresh_profile_ttl()
        for value in ("60", "86400"):
            parameter.get_param = lambda key, value=value: value
            self.assertEqual(self.helper._get_fresh_profile_ttl(), int(value))

    def test_fresh_profile_instance_binding_requires_external_marker_and_matches_digest(self):
        params = {}
        parameter = SimpleNamespace(
            get_param=lambda key, default=False: params.get(key, default),
            set_param=lambda key, value: params.__setitem__(key, value),
        )
        self.helper.env = {"ir.config_parameter": SimpleNamespace(sudo=lambda: parameter)}
        with mock.patch.dict("os.environ", {}, clear=False):
            __import__("os").environ.pop("AMR_OIDC_FRESH_PROFILE_INSTANCE_ID", None)
            with self.assertRaises(ValueError):
                self.helper._bind_fresh_profile_instance()
            with self.assertRaises(ValueError):
                self.helper._require_fresh_profile_instance()

        marker = "synthetic-instance-marker-" + "x" * 40
        with mock.patch.dict("os.environ", {"AMR_OIDC_FRESH_PROFILE_INSTANCE_ID": marker}):
            self.helper._bind_fresh_profile_instance()
            digest = params["amr_token.fresh_profile_instance_binding"]
            self.assertNotIn(marker, digest)
            self.helper._require_fresh_profile_instance()
            params["amr_token.fresh_profile_instance_binding"] = ""
            with self.assertRaises(ValueError):
                self.helper._bind_fresh_profile_instance()
            self.assertEqual(params["amr_token.fresh_profile_instance_binding"], "")
            params["amr_token.fresh_profile_instance_binding"] = digest

        with mock.patch.dict("os.environ", {
                "AMR_OIDC_FRESH_PROFILE_INSTANCE_ID": "other-instance-marker-" + "y" * 40}):
            with self.assertRaises(ValueError):
                self.helper._require_fresh_profile_instance()
            with self.assertRaises(ValueError):
                self.helper._bind_fresh_profile_instance()
            self.assertEqual(params["amr_token.fresh_profile_instance_binding"], digest)

    def test_fresh_profile_instance_gate_rejects_unbound_database(self):
        parameter = SimpleNamespace(
            get_param=lambda key, default=False: {
                "amr_token.fresh_profile_issuer": "https://issuer.invalid",
            }.get(key, default),
        )
        self.helper.env = {"ir.config_parameter": SimpleNamespace(sudo=lambda: parameter)}
        self.helper._get_fresh_profile_issuer = mock.Mock(return_value="https://issuer.invalid")
        with mock.patch.dict("os.environ", {}, clear=False):
            __import__("os").environ.pop("AMR_OIDC_FRESH_PROFILE_INSTANCE_ID", None)
            with self.assertRaises(ValueError):
                self.helper._fresh_profile_is_enabled()

    def test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl(self):
        user = SimpleNamespace(id=7, active=True, share=False,
                               has_group=lambda group: False)

        class GrantList(list):
            def filtered(self, predicate):
                return GrantList(item for item in self if predicate(item))

        class ClientSet(list):
            def __getattr__(self, name):
                return getattr(self[0], name)

        client = SimpleNamespace(
            id=3, client_id="machine-a", name="service-a", active=True,
            is_confidential=True, authentication_method="client_secret", user_id=user,
            allowed_grants=GrantList([SimpleNamespace(code="client_credentials")]),
            check_credentials=mock.Mock(return_value=True),
        )
        client_model = SimpleNamespace(sudo=lambda: client_model,
                                       search=lambda domain: ClientSet([client]))
        mapping = SimpleNamespace(_get_or_create_subject=mock.Mock(return_value="a" * 64))
        self.helper.env = {"oidc.client": client_model,
                           "oidc.issuer.principal.subject": mapping}
        self.helper._get_fresh_profile_issuer = mock.Mock(return_value="https://issuer.invalid")
        self.helper._require_fresh_profile_instance = mock.Mock()
        self.helper._get_fresh_profile_ttl = mock.Mock(return_value=900)
        self.helper.get_signature_type = mock.Mock(return_value="public_key")
        self.helper.get_signature_algorithm = mock.Mock(return_value="RS256")
        signed = mock.Mock(return_value="signed-jwt")
        self.helper._sign_fresh_profile_token = signed

        self.helper._require_fresh_profile_instance.side_effect = ValueError(
            "Fresh profile instance is not authorized")
        with self.assertRaises(ValueError):
            self.helper._issue_fresh_client_token("machine-a", "secret", "")
        mapping._get_or_create_subject.assert_not_called()
        signed.assert_not_called()
        self.helper._require_fresh_profile_instance.side_effect = None
        client.check_credentials.reset_mock()

        result = self.helper._issue_fresh_client_token("machine-a", "secret", "")

        self.assertEqual(result, {"access_token": "signed-jwt", "token_type": "Bearer",
                                  "expires_in": 900})
        claims, provenance = signed.call_args.args
        self.assertEqual(claims["iss"], "https://issuer.invalid")
        self.assertEqual(claims["aud"], "service-a")
        self.assertEqual(claims["sub"], "a" * 64)
        self.assertEqual(claims["client_id"], "machine-a")
        self.assertEqual(claims["azp"], "machine-a")
        self.assertEqual(claims["exp"] - claims["iat"], 900)
        self.assertFalse({"uid", "user_id", "login", "db", "email"}.intersection(claims))
        self.assertEqual(provenance.user_id, 7)
        client.check_credentials.assert_called_once_with("secret")
        mapping._get_or_create_subject.assert_called_once_with("https://issuer.invalid", 7)
        second = self.helper._issue_fresh_client_token("machine-a", "secret", "")
        self.assertEqual(second["expires_in"], 900)
        self.assertEqual(signed.call_count, 2)
        self.assertEqual(client.check_credentials.call_count, 2)
        self.assertEqual(self.helper._get_fresh_profile_issuer.call_count, 2)
        self.assertEqual(self.helper._get_fresh_profile_ttl.call_count, 2)

        signed.reset_mock()
        mappings_before_invalid_override = mapping._get_or_create_subject.call_count
        for override in (None, False, True, 0, 59, 901, 86401, 60.0, "60"):
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    self.helper._issue_fresh_client_token(
                        "machine-a", "secret", "", override)
        self.assertEqual(mapping._get_or_create_subject.call_count,
                         mappings_before_invalid_override)
        signed.assert_not_called()
        result = self.helper._issue_fresh_client_token("machine-a", "secret", "", 60)
        self.assertEqual(result["expires_in"], 60)
        claims = signed.call_args.args[0]
        self.assertEqual(claims["exp"] - claims["iat"], 60)

    def test_bad_client_credential_stops_before_mapping_or_signer(self):
        user = SimpleNamespace(id=7, active=True, share=False,
                               has_group=lambda group: False)
        class GrantList(list):
            def filtered(self, predicate):
                return GrantList(item for item in self if predicate(item))
        class ClientSet(list):
            def __getattr__(self, name):
                return getattr(self[0], name)
        client = SimpleNamespace(
            id=3, client_id="machine-a", name="service-a", active=True,
            is_confidential=True, authentication_method="client_secret", user_id=user,
            allowed_grants=GrantList([SimpleNamespace(code="client_credentials")]),
            check_credentials=mock.Mock(side_effect=ValueError("bad")),
        )
        client_model = SimpleNamespace(sudo=lambda: client_model,
                                       search=lambda domain: ClientSet([client]))
        mapping = SimpleNamespace(_get_or_create_subject=mock.Mock())
        self.helper.env = {"oidc.client": client_model,
                           "oidc.issuer.principal.subject": mapping}
        signed = mock.Mock()
        self.helper._sign_fresh_profile_token = signed
        with self.assertRaises(ValueError):
            self.helper._issue_fresh_client_token("machine-a", "wrong", "", None)
        mapping._get_or_create_subject.assert_not_called()
        signed.assert_not_called()

    def test_fresh_path_rejects_inactive_unknown_other_auth_and_unregistered_grant(self):
        user = SimpleNamespace(id=7, active=True, share=False,
                               has_group=lambda group: False)

        class GrantList(list):
            def filtered(self, predicate):
                return GrantList(item for item in self if predicate(item))

        class ClientSet(list):
            def __getattr__(self, name):
                return getattr(self[0], name)

        grant = SimpleNamespace(code="client_credentials")
        client = SimpleNamespace(
            id=3, client_id="machine-a", name="service-a", active=True,
            is_confidential=True, authentication_method="client_secret", user_id=user,
            allowed_grants=GrantList([grant]),
            check_credentials=mock.Mock(return_value=True),
        )
        found = [client]
        client_model = SimpleNamespace(
            sudo=lambda: client_model,
            search=lambda domain: ClientSet([record for record in found if record.active]),
        )
        mapping = SimpleNamespace(_get_or_create_subject=mock.Mock())
        self.helper.env = {"oidc.client": client_model,
                           "oidc.issuer.principal.subject": mapping}
        signer = mock.Mock()
        self.helper._sign_fresh_profile_token = signer

        cases = (([client], "client_secret", True, False),
                 ([client], "private_key_jwt", True, True),
                 ([client], "client_secret", False, True))
        for records, auth_method, registered, active in cases:
            with self.subTest(records=bool(records), auth_method=auth_method,
                              registered=registered, active=active):
                found[:] = records
                client.active = active
                client.authentication_method = auth_method
                client.allowed_grants = GrantList([grant] if registered else [])
                client.check_credentials.reset_mock()
                with self.assertRaises(self.support.AccessError):
                    self.helper._issue_fresh_client_token("machine-a", "secret", "")
                client.check_credentials.assert_not_called()
                mapping._get_or_create_subject.assert_not_called()
                signer.assert_not_called()

    def test_fresh_signer_requires_bound_provenance_single_rs256_key_and_at_jwt(self):
        class KeySet(list):
            def __getattr__(self, name):
                return getattr(self[0], name)

        key = SimpleNamespace(kid="fresh-rs-key", private_key="synthetic-private-key")
        keys = KeySet([key])
        key_model = SimpleNamespace(sudo=lambda: key_model,
                                    search=mock.Mock(return_value=keys))
        self.helper.env = {"amr.public.key": key_model}
        self.helper.get_signature_type = mock.Mock(return_value="public_key")
        self.helper.get_signature_algorithm = mock.Mock(return_value="RS256")
        claims = {"client_id": "client-a", "azp": "client-a", "iss": "https://issuer.invalid",
                  "aud": "service-a", "sub": "a" * 64}
        with mock.patch.object(self.module.jwt, "encode", return_value="signed", create=True) as signer:
            with self.assertRaises(self.support.AccessError):
                self.helper._sign_fresh_profile_token(claims, object())
            provenance = self.module._FreshIssuanceProvenance(
                "client-a", 7, "https://issuer.invalid", "service-a", "a" * 64)
            self.assertEqual(self.helper._sign_fresh_profile_token(claims, provenance), "signed")
            signer.assert_called_once_with(
                claims, "synthetic-private-key", algorithm="RS256",
                headers={"kid": "fresh-rs-key", "typ": "at+jwt"})

            signer.reset_mock()
            self.helper.get_signature_type.return_value = "secret"
            with self.assertRaises(ValueError):
                self.helper._sign_fresh_profile_token(claims, provenance)
            signer.assert_not_called()

            self.helper.get_signature_type.return_value = "public_key"
            keys.extend([key])
            with self.assertRaises(ValueError):
                self.helper._sign_fresh_profile_token(claims, provenance)
            signer.assert_not_called()

    def test_fresh_signing_produces_verifiable_rs256_at_jwt(self):
        class KeySet(list):
            def __getattr__(self, name):
                return getattr(self[0], name)

        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode("ascii")
        key_model = SimpleNamespace(
            sudo=lambda: key_model,
            search=lambda domain: KeySet([SimpleNamespace(kid="synthetic-rs-kid", private_key=pem)]),
        )
        self.helper.env = {"amr.public.key": key_model}
        self.helper.get_signature_type = lambda: "public_key"
        self.helper.get_signature_algorithm = lambda: "RS256"
        self.module.jwt = jwt
        now = int(__import__("time").time())
        claims = {
            "iss": "https://issuer.invalid", "aud": "service-a", "sub": "a" * 64,
            "iat": now, "exp": now + 900, "jti": "synthetic-jti",
            "client_id": "client-a", "azp": "client-a",
        }
        provenance = self.module._FreshIssuanceProvenance(
            "client-a", 7, claims["iss"], claims["aud"], claims["sub"])

        token = self.helper._sign_fresh_profile_token(claims, provenance)
        header = jwt.get_unverified_header(token)
        decoded = jwt.decode(token, private.public_key(), algorithms=["RS256"],
                             issuer=claims["iss"], audience=claims["aud"])

        self.assertEqual(header, {"alg": "RS256", "kid": "synthetic-rs-kid", "typ": "at+jwt"})
        self.assertEqual(decoded, claims)


if __name__ == "__main__":
    unittest.main()
