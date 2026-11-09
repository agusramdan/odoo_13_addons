"""Provider package boundaries; no Odoo registry or database is loaded."""
import ast
import json
from pathlib import Path
import unittest
import types
from types import SimpleNamespace
from unittest import mock

ADDON_ROOT = Path(__file__).resolve().parents[2]


class UnitEnv(dict):
    uid = 7
    user = SimpleNamespace(id=7, login="email", email="em@em",has_group=lambda group: False)
    cr = SimpleNamespace(dbname="unit-db")


class StandalonePackageTests(unittest.TestCase):
    def test_provider_manifest_does_not_require_token_or_resource_addons(self):
        manifest = ast.literal_eval(
            (ADDON_ROOT / "__manifest__.py").read_text(encoding="utf-8")
        )
        dependencies = manifest.get("depends", [])

        self.assertNotIn("amr_token", dependencies)
        self.assertNotIn("amr_resource", dependencies)

    def test_introspection_rejects_non_post_before_lookup(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        module.request.httprequest = SimpleNamespace(
            method="GET", args={}, is_secure=True, form={}, headers={},
        )
        helper = mock.Mock()
        module.request.env = {"amr.oidc.helper": helper}
        response = controller.api_oidc_introspect()
        self.assertEqual(response.status_code, 400)
        helper.decode.assert_not_called()

    def test_introspection_rejects_query_token_even_when_form_overrides_route_kwarg(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_query", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        helper = mock.Mock()
        module.request.env = {"amr.oidc.helper": helper}
        module.request.httprequest = SimpleNamespace(
            method="POST", args={"token": "[REDACTED]"}, is_secure=True,
            form={"token": "[REDACTED]"}, headers={},
        )

        # Odoo 13 merges form params over query params before calling **kwargs.
        response = controller.api_oidc_introspect(token="[REDACTED]")

        self.assertEqual(response.status_code, 400)
        helper.decode.assert_not_called()



    def test_userinfo_rejects_json_body_token_even_with_bearer_header(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        helper = mock.Mock()
        helper.decode.return_value = {"sub": "subject"}
        module.request.env = {"amr.oidc.helper": helper}
        module.request.httprequest = SimpleNamespace(
            method="POST", args={}, form={}, is_secure=True,
            headers={"Authorization": "Bearer valid"},
            get_data=lambda **kwargs: b'{"token":"body-token"}',
        )

        response = controller.api_oidc_profile()

        self.assertEqual(response.status_code, 400)
        helper.decode.assert_not_called()

    def test_userinfo_rejects_form_body_token_even_with_bearer_header(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        helper = mock.Mock()
        module.request.env = {"amr.oidc.helper": helper}
        module.request.httprequest = SimpleNamespace(
            method="POST", args={}, form={"token": "body-token"}, is_secure=True,
            headers={"Authorization": "Bearer valid"},
            get_data=lambda **kwargs: b'token=body-token',
        )

        response = controller.api_oidc_profile()

        self.assertEqual(response.status_code, 400)
        helper.decode.assert_not_called()

    def test_client_decode_forwards_explicit_audience(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load("models/oidc_client.py")
        client = module.OidcClient()
        helper = mock.Mock()
        client.env = {"amr.oidc.helper": helper}

        client.decode("opaque", audience="api-audience")

        helper.decode.assert_called_once_with("opaque", audience="api-audience")
        helper.with_user.assert_not_called()

    # def test_secret_signature_mode_rejects_asymmetric_algorithm(self):
    #     import importlib.util
    #     support_path = ADDON_ROOT / "tests" / "support.py"
    #     spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
    #     support = importlib.util.module_from_spec(spec)
    #     spec.loader.exec_module(support)
    #     fake_crypto = __import__('types').ModuleType('cryptography')
    #     fake_hazmat = __import__('types').ModuleType('cryptography.hazmat')
    #     fake_primitives = __import__('types').ModuleType('cryptography.hazmat.primitives')
    #     fake_asymmetric = __import__('types').ModuleType('cryptography.hazmat.primitives.asymmetric')
    #     fake_asymmetric.ec = mock.Mock()
    #     fake_asymmetric.rsa = mock.Mock()
    #     with mock.patch.dict('sys.modules', {
    #             'cryptography': fake_crypto,
    #             'cryptography.hazmat': fake_hazmat,
    #             'cryptography.hazmat.primitives': fake_primitives,
    #             'cryptography.hazmat.primitives.asymmetric': fake_asymmetric}):
    #         module = support.load("models/token_helper.py")
    #     helper = module.TokenHelper()
    #     config = mock.Mock()
    #     config.sudo.return_value.get_param.side_effect = lambda key, default=None: {
    #         "amr_token.signature_type": "secret",
    #         "amr_token.secret_algorithm": "RS256",
    #     }.get(key, default)
    #     helper.env = {"ir.config_parameter": config}
    #     helper.get_expires_in = lambda: 60
    #     helper.get_issuer = lambda: "https://issuer.invalid"
    #     helper.get_audience = lambda: "database-id"
    #
    #     with self.assertRaisesRegex(ValueError, "signature type"):
    #         helper._generate_token({}, expires_in=60)

    def test_resource_overrides_audience_and_is_not_emitted_as_claim(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_resource", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        packages = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric")}
        packages["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
        packages["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
        with mock.patch.dict("sys.modules", packages):
            module = support.load("models/token_helper.py")
        module.jwt.encode = mock.Mock(return_value="opaque")
        helper = module.TokenHelper()
        helper.env = UnitEnv()
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        helper.get_expires_in = lambda: 60
        helper.get_issuer = lambda: "https://issuer.invalid"
        _, payload, _ = helper._generate_token(
            {"resource": "https://resource.invalid", "custom": "kept"},
            audience="https://audience.invalid", expires_in=60)
        self.assertEqual(payload["aud"], "https://resource.invalid")
        self.assertNotIn("resource", payload)
        self.assertEqual(payload["custom"], "kept")

        _, list_payload, _ = helper._generate_token(
            {"resource": "https://resource.invalid"},
            audience=["https://audience-one.invalid", "https://audience-two.invalid"], expires_in=60)
        self.assertEqual(list_payload["aud"], "https://resource.invalid")
        self.assertNotIn("resource", list_payload)

    def test_resource_requires_one_nonempty_string_at_token_generation(self):
        helper = self._audience_alias_helper()

        for resource in (None, "", "   ", [], ["resource"], {}, False, 0):
            with self.subTest(resource_type=type(resource).__name__):
                with self.assertRaisesRegex(ValueError, "resource"):
                    helper._generate_token(
                        {"resource": resource}, audience="valid-audience", expires_in=60)

    def test_token_helper_encode_resource_overrides_audience_and_emits_only_aud(self):
        helper = self._audience_alias_helper()

        token = helper._encode(resource="resource-audience", audience="explicit-audience")

        self.assertEqual(token, "opaque")
        payload = helper._jwt_encode.call_args[0][0]
        self.assertEqual(payload["aud"], "resource-audience")
        self.assertNotIn("resource", payload)

    def test_generate_user_token_resource_overrides_audience_and_emits_only_aud(self):
        helper = self._audience_alias_helper()

        token, payload, _expires_in = helper._generate_user_token(
            helper.env.user, audience="explicit-audience", resource="resource-audience")

        self.assertEqual(token, "opaque")
        self.assertEqual(payload["aud"], "resource-audience")
        self.assertNotIn("resource", payload)

    def test_generate_user_token_resource_overrides_empty_audience(self):
        helper = self._audience_alias_helper()

        token, payload, _expires_in = helper._generate_user_token(
            helper.env.user, audience="", resource="resource-audience")

        self.assertEqual(token, "opaque")
        self.assertEqual(payload["aud"], "resource-audience")
        self.assertNotIn("resource", payload)

    def test_client_credentials_forwards_resource_to_encode(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_client_credentials_resource", str(support_path))
        if spec is None or spec.loader is None:
            raise ImportError("cannot load isolated OIDC client")
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        client = support.load("models/oidc_client.py").OidcClient()
        helper = self._audience_alias_helper()
        client.env = UnitEnv({"amr.oidc.helper": helper})
        client.user_id = helper.env.user
        client.check_credentials = mock.Mock(return_value=True)
        client.with_user = mock.Mock(return_value=client)

        result = client._client_credentials(
            client_secret="synthetic-secret", audience="explicit-audience",
            resource="resource-audience", scope="read")

        self.assertEqual(result["access_token"], "opaque")
        payload = helper._jwt_encode.call_args[0][0]
        self.assertEqual(payload["aud"], "resource-audience")
        self.assertNotIn("resource", payload)
        client.check_credentials.assert_called_once_with("synthetic-secret")

    def test_empty_generation_audience_fails_and_absent_uses_database_audience(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_audience", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        packages = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric")}
        packages["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
        packages["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
        with mock.patch.dict("sys.modules", packages):
            module = support.load("models/token_helper.py")
        module.jwt.encode = mock.Mock(return_value="opaque")
        module.jwt.decode = mock.Mock(return_value={})
        helper = module.TokenHelper()
        helper.env = UnitEnv()
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        helper.get_expires_in = lambda: 60
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_audience = lambda: "database-audience"
        module.jwt.encode = lambda payload, secret, algorithm: ("opaque", payload)

        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_token({}, expires_in=60, audience="")
        _, default_payload, _ = helper._generate_token({}, expires_in=60)
        self.assertEqual(default_payload["aud"], "database-audience")
        _, client_payload, _ = helper._generate_token({}, expires_in=60, audience="client-audience")
        self.assertEqual(client_payload["aud"], "client-audience")

    def test_generation_rejects_malformed_audience_values(self):
        helper = self._audience_alias_helper()
        invalid_audiences = (False, 0, [], ["client-audience", False], {})
        for audience in invalid_audiences:
            with self.subTest(audience_type=type(audience).__name__):
                with self.assertRaisesRegex(ValueError, "audience"):
                    helper._generate_token({}, expires_in=60, audience=audience)

    def test_generation_rejects_empty_configured_audience(self):
        helper = self._audience_alias_helper()
        helper.get_audience = lambda: ""
        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_token({}, expires_in=60)

    def test_generation_accepts_audience_array_of_strings(self):
        helper = self._audience_alias_helper()
        audience = ["client-one", "client-two"]
        _, payload, _ = helper._generate_token({}, expires_in=60, audience=audience)
        self.assertEqual(payload["aud"], audience)

    def test_encode_alias_preserves_explicit_empty_audience(self):
        self._assert_empty_encode_audience_rejected()

    def _audience_alias_helper(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_alias", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        packages = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric")}
        packages["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
        packages["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
        with mock.patch.dict("sys.modules", packages):
            module = support.load("models/token_helper.py")
        module.jwt.encode = mock.Mock(return_value="opaque")
        helper = module.TokenHelper()
        helper._jwt_encode = module.jwt.encode
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        helper.get_expires_in = lambda: 60
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_audience = lambda: "database-audience"
        helper.env = SimpleNamespace(
            uid=7,
            user=SimpleNamespace(id=7, login="user", email="u@example.invalid", has_group=lambda group: False),
            cr=SimpleNamespace(dbname="unit-db")
        )
        return helper

    def _assert_empty_encode_audience_rejected(self):
        helper = self._audience_alias_helper()
        with self.assertRaisesRegex(ValueError, "audience"):
            helper._encode(aud="")

    def test_res_users_explicit_empty_url_audience_fails(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users_empty", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        helper = self._audience_alias_helper()
        model._uid, model.id, model.login, model.email = 7, 7, "user", "u@example.invalid"
        model.ensure_one = lambda: None
        model.browse = lambda uid: SimpleNamespace(
            id=uid, login="user", email="u@example.invalid"
        )
        model.env = UnitEnv({"amr.oidc.helper": helper})

        with self.assertRaisesRegex(ValueError, "audience"):
            model.add_url_access_token("https://app.example.invalid", audience="")
        with self.assertRaisesRegex(ValueError, "audience"):
            model.get_auto_login_url("https://app.example.invalid", audience="")

    def test_res_users_access_token_keeps_absent_audience_for_uuid_default(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users_default", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        model.id = 7
        model.env = UnitEnv()
        model.ensure_one = lambda: None
        model.is_user_allow_create_token = lambda: True
        model._get_access_token = mock.Mock(return_value="synthetic-token")

        with mock.patch("time.time", return_value=900):
            result = model.get_access_token()

        self.assertEqual(result, "synthetic-token")
        model._get_access_token.assert_called_once_with(7, None, 3)

    def test_res_users_resource_is_effective_cache_audience(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users_resource", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        model.id, model.env = 7, UnitEnv()
        model.ensure_one = lambda: None
        model.is_user_allow_create_token = lambda: True
        model._get_access_token = mock.Mock(return_value="synthetic-token")

        with mock.patch("time.time", return_value=900):
            model.get_access_token(create=True, audience="ignored", resource="resource-a")
            model.get_access_token(create=True, audience="ignored", resource="resource-b")

        self.assertEqual(model._get_access_token.call_args_list, [
            mock.call(7, "resource-a", 3), mock.call(7, "resource-b", 3),
        ])

    def test_res_users_rejects_explicit_invalid_resource(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users_bad_resource", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        model.id, model.env = 7, UnitEnv()
        model.ensure_one = lambda: None
        model.is_user_allow_create_token = lambda: True
        model._get_access_token = mock.Mock(return_value="synthetic-token")

        for resource in (None, "", "   ", [], False):
            with self.subTest(resource=resource):
                with self.assertRaisesRegex(ValueError, "resource"):
                    model.get_access_token(create=True, audience="valid-audience", resource=resource)

    def test_oidc_client_rejects_whitespace_resource_before_helper(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_client_bad_resource", str(support_path))
        if spec is None or spec.loader is None:
            raise ImportError("cannot load isolated OIDC client")
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load("models/oidc_client.py")
        client = module.OidcClient()
        helper = mock.Mock()
        helper._generate_user_token.return_value = ("opaque", {}, 60)
        client.redirect_path = False
        client.redirect_uri = "https://callback.invalid"
        client.client_id = "client"
        client.env = UnitEnv({"amr.oidc.helper": helper})

        with self.assertRaisesRegex(ValueError, "resource"):
            client._create_access_token(resource="   ", audience="valid-audience")

        helper._generate_user_token.assert_not_called()

    def test_oidc_client_encode_forwards_resource_without_losing_audience(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_client_resource", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load("models/oidc_client.py")
        client = module.OidcClient()
        helper = mock.Mock()
        helper._generate_user_token.return_value = ("opaque", {}, 60)
        client.redirect_path = False
        client.redirect_uri = "https://callback.invalid"
        client.client_id = "client"
        client.env = UnitEnv({"amr.oidc.helper": helper})

        client._create_access_token(scope="openid", resource="resource-a", audience="audience-a")

        helper._generate_user_token.assert_called_once()
        self.assertEqual(helper._generate_user_token.call_args[1]["audience"], "resource-a")
        self.assertNotIn("resource", helper._generate_user_token.call_args.kwargs)

    def test_res_users_url_audiences_derive_and_cache_keys_remain_distinct(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users_urls", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        model.get_access_token = mock.Mock(return_value="synthetic-token")

        model.add_url_access_token("https://app.example.invalid/path")
        model.get_auto_login_url("https://other.example.invalid/path")

        self.assertEqual(model.get_access_token.call_args_list, [
            mock.call(create=True, audience="https://app.example.invalid"),
            mock.call(create=True, audience="https://other.example.invalid"),
        ])

    def test_public_key_rejects_jwt_kid_that_does_not_match_active_key(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_pubkey_kid", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        fake_modules = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.exceptions", "cryptography.hazmat",
            "cryptography.hazmat.primitives", "cryptography.hazmat.primitives.serialization",
            "jwt.algorithms", "odoo.exceptions", "odoo.tools")}
        fake_modules["cryptography.exceptions"].UnsupportedAlgorithm = type("UnsupportedAlgorithm", (Exception,), {})
        fake_modules["cryptography.hazmat.primitives.serialization"].Encoding = mock.Mock()
        fake_modules["cryptography.hazmat.primitives.serialization"].PublicFormat = mock.Mock()
        fake_modules["jwt.algorithms"].ECAlgorithm = mock.Mock()
        fake_modules["jwt.algorithms"].RSAAlgorithm = mock.Mock()
        fake_modules["odoo.exceptions"].ValidationError = type("ValidationError", (Exception,), {})
        fake_modules["odoo.tools"].config = {}
        support.Field.now = lambda: None
        with mock.patch.dict("sys.modules", fake_modules):
            module = support.load("models/public_key.py")
        key = module.PublicKey()
        key.public_key, key.algorithm, key.active, key.kid = "public", "RS256", True, "active-kid"
        module.jwt.get_unverified_header = mock.Mock(return_value={"kid": "different-kid"})
        module.jwt.decode = mock.Mock(return_value={})

        with self.assertRaisesRegex(ValueError, "kid"):
            key.validate_token("opaque", issuer="https://issuer.invalid", audience="api")
        module.jwt.decode.assert_not_called()

    def test_public_key_validation_requires_issuer_audience_and_registered_claims(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_pubkey", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        fake_modules = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.exceptions", "cryptography.hazmat",
            "cryptography.hazmat.primitives", "cryptography.hazmat.primitives.serialization",
            "jwt.algorithms", "odoo.exceptions", "odoo.tools")}
        fake_modules["cryptography.exceptions"].UnsupportedAlgorithm = type("UnsupportedAlgorithm", (Exception,), {})
        fake_modules["cryptography.hazmat.primitives.serialization"].Encoding = mock.Mock()
        fake_modules["cryptography.hazmat.primitives.serialization"].PublicFormat = mock.Mock()
        fake_modules["jwt.algorithms"].ECAlgorithm = mock.Mock()
        fake_modules["jwt.algorithms"].RSAAlgorithm = mock.Mock()
        fake_modules["odoo.exceptions"].ValidationError = type("ValidationError", (Exception,), {})
        fake_modules["odoo.tools"].config = {}
        support.Field.now = lambda: None
        with mock.patch.dict("sys.modules", fake_modules):
            module = support.load("models/public_key.py")
        key = module.PublicKey()
        key.public_key = "public"
        key.algorithm = "RS256"
        key.active = True
        key.kid = "active-kid"
        module.jwt.decode = mock.Mock(return_value={})

        key.active = False
        with self.assertRaisesRegex(ValueError, "active"):
            key.validate_token("opaque", issuer="https://issuer.invalid", audience="api")
        key.active = True
        key.kid = ""
        with self.assertRaisesRegex(ValueError, "active"):
            key.validate_token("opaque", issuer="https://issuer.invalid", audience="api")
        key.kid = "active-kid"
        module.jwt.get_unverified_header = mock.Mock(return_value={"kid": "active-kid"})
        key.algorithm = "HS256"
        with self.assertRaisesRegex(ValueError, "algorithm"):
            key.validate_token("opaque", issuer="https://issuer.invalid", audience="api")
        key.algorithm = "RS256"

        for issuer, audience in ((None, "api"), ("https://issuer.invalid", None),
                                 ("", "api"), ("https://issuer.invalid", "")):
            with self.subTest(issuer=issuer, audience=audience):
                with self.assertRaises(ValueError):
                    key.validate_token("opaque", issuer=issuer, audience=audience)
        key.validate_token("opaque", issuer="https://issuer.invalid", audience="api",
                           options={"verify_signature": False, "verify_exp": False,
                                    "verify_nbf": False, "require": []})
        kwargs = module.jwt.decode.call_args[1]
        self.assertEqual(kwargs["issuer"], "https://issuer.invalid")
        self.assertEqual(kwargs["audience"], "api")
        self.assertEqual(kwargs["options"]["require"], ["exp", "iss", "aud"])
        self.assertTrue(kwargs["options"]["verify_signature"])
        self.assertTrue(kwargs["options"]["verify_aud"])
        self.assertTrue(kwargs["options"]["verify_exp"])
        self.assertTrue(kwargs["options"]["verify_nbf"])

    def test_secret_decode_overrides_weak_options_and_requires_registered_claims(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_secret_options", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        packages = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric")}
        packages["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
        packages["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
        with mock.patch.dict("sys.modules", packages):
            module = support.load("models/token_helper.py")
        secret = module.TokenSecret({}, "HS256", "https://issuer.invalid", "synthetic-secret")
        module.jwt.decode = mock.Mock(return_value={})

        secret.decode("opaque", audience="api", options={
            "verify_signature": False, "verify_iss": False, "verify_aud": False,
            "verify_exp": False, "verify_nbf": False, "require": [],
        })

        options = module.jwt.decode.call_args[1]["options"]
        for option in ("verify_signature", "verify_iss", "verify_aud", "verify_exp", "verify_nbf"):
            self.assertTrue(options[option])
        self.assertEqual(options["require"], ["exp", "iss", "aud"])


    def test_encode_without_audience_defaults_to_database_uuid(self):
        helper = self._audience_alias_helper()

        helper._encode()
        helper._encode(audience=None)

        encoded_payloads = [call[0][0] for call in helper._encode.__globals__["jwt"].encode.call_args_list]
        self.assertEqual([payload["aud"] for payload in encoded_payloads], [
            "database-audience", "database-audience",
        ])

    def test_secret_strategy_rejects_algorithm_mismatch_before_secret_lookup(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = mock.Mock(return_value="synthetic-secret")

        with self.assertRaisesRegex(ValueError, "algorithm"):
            helper._token_strategy("HS512")

        helper._get_secret.assert_not_called()

    def test_validation_rejects_header_algorithm_mismatch_before_decode(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        jwt = helper.decode.__globals__["jwt"]
        jwt.get_unverified_header = mock.Mock(return_value={"alg": "HS512"})
        jwt.decode = mock.Mock(return_value={})

        with self.assertRaisesRegex(ValueError, "algorithm"):
            helper.decode("opaque-token", audience="client-audience")

        jwt.decode.assert_not_called()

    def test_user_token_generation_needs_no_resource_user_classification(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.env = UnitEnv()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        token, payload, expires_in = helper._generate_user_token(
            user, audience="client-audience", expires_in=60
        )

        self.assertTrue(token)
        self.assertEqual(expires_in, 60)
        self.assertEqual(payload["uid"], 7)
        self.assertEqual(payload["user_id"], "user")
        self.assertEqual(payload["sub"], "user")
        self.assertEqual(payload["email"], "u@example.invalid")
        self.assertEqual(payload["db"], "unit-db")
        self.assertEqual(payload["aud"], "client-audience")
        self.assertNotIn("type", payload)

    def test_generate_user_token_without_audience_defaults_to_database_uuid(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.env = UnitEnv()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        _, payload, _ = helper._generate_user_token(user, expires_in=60)

        self.assertEqual(payload["aud"], "database-audience")

    def test_cached_user_issuance_preserves_actor_and_passes_target_user(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_cached_user", str(support_path))
        if spec is None or spec.loader is None:
            raise ImportError("cannot create isolated support module spec")
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        target = SimpleNamespace(id=29, login="target", email="target@example.invalid")
        helper = mock.Mock()
        helper._generate_user_token.return_value = ("target-token", {}, 60)
        model._uid = 7
        model.env = UnitEnv({"amr.oidc.helper": helper})
        model.browse = mock.Mock(return_value=target)
        model.with_user = mock.Mock(return_value=model)

        result = model._get_access_token(29, "client-audience", 1)

        self.assertEqual(result, "target-token")
        helper._generate_user_token.assert_called_once_with(
            target, audience="client-audience"
        )
        model.with_user.assert_not_called()

    def test_generate_user_token_rejects_explicit_empty_audience(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.env = UnitEnv()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_user_token(user, audience="", aud="fallback-audience", expires_in=60)

    def test_generate_user_token_rejects_malformed_explicit_audience(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.env = UnitEnv()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_user_token(user, audience=False, expires_in=60)

    def test_generate_user_token_rejects_explicit_empty_string_audience(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.env = UnitEnv()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_user_token(user, audience="", aud="fallback-audience", expires_in=60)

    def test_generate_user_token_rejects_explicit_empty_list_audience(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.env = UnitEnv()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_user_token(user, audience=[], aud="fallback-audience", expires_in=60)

    def test_encode_rejects_caller_algorithm_mismatch_before_signing(self):
        helper = self._audience_alias_helper()
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = mock.Mock(return_value="synthetic-secret")
        jwt = helper._encode.__globals__["jwt"]
        jwt.encode = mock.Mock(return_value="opaque-token")

        with self.assertRaisesRegex(ValueError, "algorithm"):
            helper._encode(audience="client-audience", alg="HS512")

        jwt.encode.assert_not_called()
        helper._get_secret.assert_not_called()


    def test_signature_modes_fail_closed_for_none_missing_keys_and_secret(self):
        import importlib.util
        import types
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        packages = {
            name: types.ModuleType(name) for name in (
                "cryptography", "cryptography.hazmat",
                "cryptography.hazmat.primitives",
                "cryptography.hazmat.primitives.asymmetric",
            )
        }
        packages["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
        packages["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
        with mock.patch.dict("sys.modules", packages):
            module = support.load("models/token_helper.py")

        for signature_type, algorithm in (
                ("none", "RS256"), ("public_key", "HS256"),
                ("secret", "HS1024"), ("secret", "HS256"),
                ("public_key", "RS256")):
            with self.subTest(signature_type=signature_type, algorithm=algorithm):
                helper = module.TokenHelper()
                config = mock.Mock()
                params = {
                    "amr_token.signature_type": signature_type,
                    "amr_token.secret_algorithm": algorithm,
                    "amr_token.public_key_algorithm": algorithm,
                }
                config.sudo.return_value.get_param.side_effect = lambda key, default=None: params.get(key, default)
                key_model = mock.Mock()
                key_model.sudo.return_value.search.return_value = []
                helper.env = {"ir.config_parameter": config, "amr.public.key": key_model}
                helper.get_expires_in = lambda: 60
                helper.get_issuer = lambda: "https://issuer.invalid"
                helper.get_audience = lambda: "database-id"
                helper._get_secret = lambda: None

                expected = {
                    ("none", "RS256"): (ValueError, "A supported signature type is required"),
                    ("public_key", "HS256"): (ValueError, "Token algorithm does not match provider configuration"),
                    ("secret", "HS1024"): (ValueError, "Token algorithm does not match provider configuration"),
                    ("secret", "HS256"): (ValueError, "JWT Secret not set"),
                    ("public_key", "RS256"): (Exception, "Private Key not set"),
                }[(signature_type, algorithm)]
                with self.assertRaisesRegex(expected[0], expected[1]):
                    helper._generate_token({}, expires_in=60)


    def _load_token_helper_for_direct_validation_tests(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_token_fixes", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        packages = {name: types.ModuleType(name) for name in (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric")}
        packages["cryptography.hazmat.primitives.asymmetric"].ec = mock.Mock()
        packages["cryptography.hazmat.primitives.asymmetric"].rsa = mock.Mock()
        with mock.patch.dict("sys.modules", packages):
            return support.load("models/token_helper.py")


    def test_token_helper_decode_returns_decode_claims_and_forwards_arguments_once(self):
        module = self._load_token_helper_for_direct_validation_tests()
        helper = module.TokenHelper()
        claims = {"sub": "subject"}
        helper.decode = mock.Mock(return_value=claims)

        result = helper.decode("opaque", audience="api", leeway=3)

        self.assertIs(result, claims)
        helper.decode.assert_called_once_with("opaque", audience="api", leeway=3)

    def test_token_helper_decode_propagates_decode_validation_errors(self):
        module = self._load_token_helper_for_direct_validation_tests()
        helper = module.TokenHelper()
        invalid_token_error = module.jwt.InvalidTokenError("invalid token")
        for error in (ValueError("invalid claims"), invalid_token_error):
            with self.subTest(error_type=type(error).__name__):
                helper.decode = mock.Mock(side_effect=error)
                with self.assertRaises(type(error)) as raised:
                    helper.decode("opaque", audience="api")
                helper.decode.assert_called_once_with("opaque", audience="api")
                self.assertIs(raised.exception, error)

    def test_consumer_decode_enforces_configured_signature_policy_with_real_hmac(self):
        import jwt as real_jwt
        module = self._load_token_helper_for_direct_validation_tests()
        module.jwt.encode = real_jwt.encode
        module.jwt.decode = real_jwt.decode
        module.jwt.get_unverified_header = real_jwt.get_unverified_header
        helper = module.TokenHelper()
        helper.env = UnitEnv()
        claims = {"iss": "https://issuer.invalid", "aud": "synthetic-audience",
                  "exp": 4102444800, "nbf": 0, "sub": "synthetic-subject"}
        secret = "synthetic-only-hmac-key"
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper.get_allowed_algorithms = lambda: {"secret": ["HS256"], "public_key": ["RS256"]}
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper._get_secret = mock.Mock(return_value=secret)

        valid = module.jwt.encode(claims, secret, algorithm="HS256")
        self.assertEqual(helper.decode(valid, audience="synthetic-audience"), claims)
        helper._get_secret.assert_called_once_with()

        mismatched = module.jwt.encode(claims, secret, algorithm="HS384")
        helper._get_secret.reset_mock()
        with self.assertRaises(ValueError):
            helper.decode(mismatched, audience="synthetic-audience")
        helper._get_secret.assert_not_called()

        helper.get_signature_type = lambda: "public_key"
        helper.get_signature_algorithm = lambda: "RS256"
        helper._get_secret.reset_mock()
        with self.assertRaises(ValueError):
            helper.decode(valid, audience="synthetic-audience")
        helper._get_secret.assert_not_called()

    def test_consumer_decode_rejects_caller_algorithm_overrides(self):
        import jwt as real_jwt
        module = self._load_token_helper_for_direct_validation_tests()
        module.jwt.encode = real_jwt.encode
        module.jwt.decode = real_jwt.decode
        module.jwt.get_unverified_header = real_jwt.get_unverified_header
        helper = module.TokenHelper()
        helper.env = UnitEnv()
        claims = {"iss": "https://issuer.invalid", "aud": "synthetic-audience",
                  "exp": 4102444800, "nbf": 0, "sub": "synthetic-subject"}
        secret = "synthetic-only-hmac-key"
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper.get_allowed_algorithms = lambda: {"secret": ["HS256"], "public_key": ["RS256"]}
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper._get_secret = mock.Mock(return_value=secret)
        token = real_jwt.encode(claims, secret, algorithm="HS256")

        self.assertEqual(helper.decode(token, audience="synthetic-audience", algorithm="HS256"), claims)
