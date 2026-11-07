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
    user = SimpleNamespace(has_group=lambda group: False)


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
        helper.validate.assert_not_called()

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
        helper.validate.assert_not_called()

    def test_introspection_authenticates_client_and_returns_only_allowed_claims(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        client = mock.Mock()
        client.allow_introspection = True
        client.client_id = "client"
        client.check_credentials.return_value = True
        client_model = mock.Mock()
        client_model.sudo.return_value.search.return_value = client
        helper = mock.Mock()
        helper.get_basic_auth.return_value = ("client", "secret")
        helper.validate.return_value = {
            "sub": "subject", "iss": "https://issuer.invalid", "aud": "api",
            "exp": 10, "iat": 1, "scope": "read", "jti": "id",
            "token_type": "Bearer", "uid": 42, "login": "private",
        }
        module.request.env = {"oidc.client": client_model, "amr.oidc.helper": helper}
        module.request.httprequest = SimpleNamespace(
            method="POST", args={}, is_secure=True,
            form={"token": "[REDACTED]"},
            headers={"Authorization": "Basic Y2xpZW50OnNlY3JldA=="},
        )
        response = controller.api_oidc_introspect()
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data)
        self.assertEqual(payload, {
            "active": True, "sub": "subject",
            "iss": "https://issuer.invalid", "aud": "api", "exp": 10,
            "iat": 1, "scope": "read", "jti": "id", "token_type": "Bearer",
        })
        client.check_credentials.assert_called_once_with("secret")

    def test_introspection_accepts_form_token_dispatched_as_route_kwarg(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        client = mock.Mock(allow_introspection=True, client_id="introspector")
        client.check_credentials.return_value = True
        client_model = mock.Mock()
        client_model.sudo.return_value.search.return_value = client
        helper = mock.Mock()
        helper.get_basic_auth.return_value = ("introspector", "secret")
        helper.validate.return_value = {"client_id": "token-owner", "sub": "subject"}
        module.request.env = {"oidc.client": client_model, "amr.oidc.helper": helper}
        module.request.httprequest = SimpleNamespace(
            method="POST", args={}, is_secure=True,
            form={"token": "opaque"}, headers={"Authorization": "Basic x"},
        )

        response = controller.api_oidc_introspect(token="opaque")

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data)
        self.assertEqual(payload.get("client_id"), "token-owner")
        helper.validate.assert_called_once_with("opaque", audience="introspector")

    def test_userinfo_rejects_json_body_token_even_with_bearer_header(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load_controller()
        controller = module.ControllerOIDC()
        helper = mock.Mock()
        helper.validate.return_value = {"sub": "subject"}
        module.request.env = {"amr.oidc.helper": helper}
        module.request.httprequest = SimpleNamespace(
            method="POST", args={}, form={}, is_secure=True,
            headers={"Authorization": "Bearer valid"},
            get_data=lambda **kwargs: b'{"token":"body-token"}',
        )

        response = controller.api_oidc_profile()

        self.assertEqual(response.status_code, 400)
        helper.validate.assert_not_called()

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
        helper.validate.assert_not_called()

    # def test_client_token_validation_uses_explicit_client_audience(self):
    #     import importlib.util
    #     support_path = ADDON_ROOT / "tests" / "support.py"
    #     spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
    #     support = importlib.util.module_from_spec(spec)
    #     spec.loader.exec_module(support)
    #     module = support.load("models/oidc_client.py")
    #     client = module.OidcClient()
    #     helper = mock.Mock()
    #     client.env = {"amr.oidc.helper": helper}
    #     client.name = "client-name"
    #     client.client_id = "client-context"
    #
    #     client.validate_token("opaque")
    #
    #     helper.decode.assert_called_once_with("opaque")

    def test_secret_signature_mode_rejects_asymmetric_algorithm(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        fake_crypto = __import__('types').ModuleType('cryptography')
        fake_hazmat = __import__('types').ModuleType('cryptography.hazmat')
        fake_primitives = __import__('types').ModuleType('cryptography.hazmat.primitives')
        fake_asymmetric = __import__('types').ModuleType('cryptography.hazmat.primitives.asymmetric')
        fake_asymmetric.ec = mock.Mock()
        fake_asymmetric.rsa = mock.Mock()
        with mock.patch.dict('sys.modules', {
                'cryptography': fake_crypto,
                'cryptography.hazmat': fake_hazmat,
                'cryptography.hazmat.primitives': fake_primitives,
                'cryptography.hazmat.primitives.asymmetric': fake_asymmetric}):
            module = support.load("models/token_helper.py")
        helper = module.TokenHelper()
        config = mock.Mock()
        config.sudo.return_value.get_param.side_effect = lambda key, default=None: {
            "amr_token.signature_type": "secret",
            "amr_token.secret_algorithm": "RS256",
        }.get(key, default)
        helper.env = {"ir.config_parameter": config}
        helper.get_expires_in = lambda: 60
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_audience = lambda: "database-id"

        with self.assertRaisesRegex(ValueError, "signature type"):
            helper._generate_token({}, expires_in=60)

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
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        helper.get_expires_in = lambda: 60
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_audience = lambda: "database-audience"
        module.jwt.encode = lambda payload, secret, algorithm: ("opaque", payload)

        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_token({}, expires_in=60, audience="")
        _, default_payload = helper._generate_token({}, expires_in=60)
        self.assertEqual(default_payload["aud"], "database-audience")
        _, client_payload = helper._generate_token({}, expires_in=60, audience="client-audience")
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
        _, payload = helper._generate_token({}, expires_in=60, audience=audience)
        self.assertEqual(payload["aud"], audience)

    def test_user_token_generation_does_not_require_resource_user_types(self):
        helper = self._audience_alias_helper()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")

        _, payload, _ = helper._generate_user_token(
            user, audience="client-audience", expires_in=60
        )

        self.assertEqual(payload["uid"], 7)
        self.assertEqual(payload["aud"], "client-audience")
        self.assertNotIn("type", payload)

    def test_generate_user_token_alias_preserves_explicit_empty_audience(self):
        self._assert_empty_user_audience_rejected()

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
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        helper.get_expires_in = lambda: 60
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_audience = lambda: "database-audience"
        helper.env = SimpleNamespace(uid=7, user=SimpleNamespace(has_group=lambda group: False),
                                     cr=SimpleNamespace(dbname="unit-db"))
        return helper

    def _assert_empty_user_audience_rejected(self):
        helper = self._audience_alias_helper()
        user = SimpleNamespace(id=7, login="user", email="u@example.invalid")
        with self.assertRaisesRegex(ValueError, "audience"):
            helper._generate_user_token(user, audience="")

    def _assert_empty_encode_audience_rejected(self):
        helper = self._audience_alias_helper()
        with self.assertRaisesRegex(ValueError, "audience"):
            helper.encode(aud="")

    def test_public_provider_helpers_reject_unconfigured_algorithms(self):
        import importlib.util
        import types
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_helpers", str(support_path))
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
        helper.get_signature_type = lambda: "secret"
        helper.get_signature_algorithm = lambda: "HS256"
        helper._get_secret = lambda: "synthetic-secret"
        helper.get_issuer = lambda: "https://issuer.invalid"
        helper.get_audience = lambda: "database-audience"
        key = mock.Mock(active=True)
        class KeySet(list):
            active = True
            def generate_token(self, payload):
                return "opaque"
            def validate_token(self, *args, **kwargs):
                return {}
        key_model = mock.Mock()
        key_model.sudo.return_value.search.return_value = KeySet([key])
        helper.env = {"amr.public.key": key_model}

        for call in (
                lambda: helper._generate_token_secret({}, "HS512"),
                lambda: helper._generate_token_asymmetric({}, "RS256"),
                lambda: helper.validate_secret("opaque", "HS512"),
                lambda: helper.validate_asymmetric("opaque", "kid", "RS256")):
            with self.subTest(call=call):
                with self.assertRaisesRegex(ValueError, "provider configuration|signature type"):
                    call()

    def test_res_users_omitted_audience_passes_none_to_database_default(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        helper = self._audience_alias_helper()
        captured = {}
        helper._generate_token_secret = lambda payload, algorithm: (
            captured.update(payload) or "synthetic-token", payload)
        model.id, model.login, model.email = 7, "user", "u@example.invalid"
        model.ensure_one = lambda: None
        model.env = UnitEnv({"amr.oidc.helper": helper})

        result = model.get_access_token()

        self.assertEqual(result, "synthetic-token")
        self.assertEqual(captured["aud"], "database-audience")

    def test_res_users_explicit_empty_url_audience_fails(self):
        import importlib.util
        support_path = ADDON_ROOT / "tests" / "support.py"
        spec = importlib.util.spec_from_file_location("oidc_test_support_users_empty", str(support_path))
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        model = support.load("models/res_users.py").ResUsers()
        helper = self._audience_alias_helper()
        model.id, model.login, model.email = 7, "user", "u@example.invalid"
        model.ensure_one = lambda: None
        model.env = UnitEnv({"amr.oidc.helper": helper})

        with self.assertRaisesRegex(ValueError, "audience"):
            model.add_url_access_token("https://app.example.invalid", audience="")
        with self.assertRaisesRegex(ValueError, "audience"):
            model.get_auto_login_url("https://app.example.invalid", audience="")

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

                with self.assertRaises(Exception):
                    helper._generate_token({}, expires_in=60)
