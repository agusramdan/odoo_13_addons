"""Offline source contracts for optional provider/resource glue."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
PROVIDER = ROOT / "amr_oidc"
GLUE = ROOT / "amr_oidc_resource"
MOVED = {
    "is_user_allow_create_token",
    "get_access_token",
    "create_access_token",
    "add_url_access_token",
    "get_auto_login_url",
}


class ResourceGlueContract(unittest.TestCase):
    def test_registered_glue_test_patches_provider_addon_module_path(self):
        registration = (GLUE / "tests/integration/__init__.py").read_text()
        self.assertIn("test_user_token_glue", registration)
        provider_models = (PROVIDER / "models/__init__.py").read_text()
        self.assertIn("from . import token_helper", provider_models)
        source = (GLUE / "tests/integration/test_user_token_glue.py").read_text()
        self.assertIn(
            'mock.patch("odoo.addons.amr_oidc.models.token_helper.time.time",',
            source,
        )
        self.assertNotIn('mock.patch("amr_oidc.models.token_helper.time.time",', source)

    def test_glue_issuance_is_not_cached_across_signing_configuration_changes(self):
        tree = ast.parse((GLUE / "models/res_users.py").read_text())
        method = next(node for node in ast.walk(tree)
                      if isinstance(node, ast.FunctionDef)
                      and node.name == "_get_access_token")
        self.assertFalse(any(isinstance(node, ast.Call)
                             and isinstance(node.func, ast.Name)
                             and node.func.id == "ormcache"
                             for node in method.decorator_list))

    def test_missing_secret_fixture_clears_secret_before_negative_assertion(self):
        source = (PROVIDER / "tests/integration/test_provider_selected_uat.py").read_text()
        test = source.split("class TestProviderSelectedUAT01", 1)[1].split("class TestProviderSelectedUAT08", 1)[0]
        self.assertLess(test.index('params.set_param("amr_token.secret", "")'),
                        test.index('with self.assertRaisesRegex(ValueError, "JWT Secret not set")'))

    def test_provider_only_audience_helpers_remain_registered_without_glue(self):
        tests_init = (PROVIDER / "tests/__init__.py").read_text()
        integration_init = (PROVIDER / "tests/integration/__init__.py").read_text()
        self.assertNotIn("from .integration import test_access_token_audience_presence", tests_init)
        self.assertIn("test_access_token_audience_presence", integration_init)
        provider_test = PROVIDER / "tests/integration/test_access_token_audience_presence.py"
        self.assertTrue(provider_test.is_file())
        source = provider_test.read_text()
        self.assertIn("test_client_create_access_token_accepts_aud_only_alias", source)
        self.assertIn("test_client_encode_omitted_audience_defaults_and_none_is_rejected", source)
        self.assertNotIn("add_url_access_token", source)
        glue_source = (ROOT / "amr_oidc_resource/tests/integration/test_access_token_audience_presence.py").read_text()
        for test_name in (
                "test_client_create_access_token_accepts_aud_only_alias",
                "test_client_create_access_token_omitted_audience_uses_database_uuid",
                "test_client_credentials_omitted_audience_defaults_and_none_is_rejected",
                "test_client_encode_omitted_audience_defaults_and_none_is_rejected",
                "test_helper_resource_overrides_conflicting_audience_shapes",
                "test_helper_invalid_resource_values_rejected_before_signing"):
            self.assertNotIn(test_name, glue_source)

    def test_glue_reads_current_signing_key_and_ttl_for_each_issuance(self):
        import importlib.util
        support_path = PROVIDER / "tests/support.py"
        spec = importlib.util.spec_from_file_location("resource_glue_cache_support", support_path)
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        module = support.load("models/res_users.py", addon=GLUE)
        model = module.ResUsers()
        model.id = 11
        class Env(dict):
            pass
        class Params:
            value = "60"
            secret = ""
            def sudo(self):
                return self
            def get_param(self, key):
                return self.value
        params = Params()
        model.env = Env({"ir.config_parameter": params,
                         "amr.oidc.helper": SimpleNamespace(_validate_audience=lambda audience: audience)})
        model.env.uid = 11
        model.env.user = SimpleNamespace(has_group=lambda group: False)
        model.ensure_one = lambda: None
        model.is_user_allow_create_token = lambda: True
        model.env["amr.oidc.helper"] = SimpleNamespace(
            _validate_audience=lambda audience: audience)
        params.secret = "synthetic-signing-key-a"
        helper = model.env["amr.oidc.helper"]
        def generate(user, audience=None, expires_in=None):
            if not params.secret:
                raise ValueError("JWT Secret not set")
            lifetime = expires_in or params.value
            return "%s:%s" % (params.secret, lifetime), {}, lifetime
        helper._generate_user_token = mock.Mock(side_effect=generate)
        model.browse = mock.Mock(return_value=SimpleNamespace(id=11))
        self.assertEqual(module.ResUsers.get_access_token(model, audience="client-audience"),
                         "synthetic-signing-key-a:60")
        params.secret = "synthetic-signing-key-b"
        params.value = "120"
        self.assertEqual(module.ResUsers.get_access_token(model, audience="client-audience"),
                         "synthetic-signing-key-b:120")
        params.secret = ""
        with self.assertRaisesRegex(ValueError, "JWT Secret not set"):
            module.ResUsers.get_access_token(model, audience="client-audience")
        self.assertEqual(helper._generate_user_token.call_count, 3)
        user = SimpleNamespace(id=11)
        helper._generate_user_token.assert_called_with(
            user, audience="client-audience")

    def test_glue_actor_denial_precedes_ttl_read_and_cache(self):
        import importlib.util
        support_path = PROVIDER / "tests/support.py"
        spec = importlib.util.spec_from_file_location("resource_glue_actor_support", support_path)
        support = importlib.util.module_from_spec(spec)
        self.assertIsNotNone(spec.loader)
        spec.loader.exec_module(support)
        module = support.load("models/res_users.py", addon=GLUE)
        model = module.ResUsers()
        model.id = 22
        class Env(dict):
            pass
        params = mock.Mock()
        model.env = Env({"ir.config_parameter": params})
        model.env.uid = 11
        model.env.user = SimpleNamespace(has_group=lambda group: False)
        model.ensure_one = lambda: None
        model._get_access_token = mock.Mock()
        with self.assertRaises(module.AccessError):
            module.ResUsers.get_access_token(model, audience="client-audience")
        params.sudo.assert_not_called()
        model._get_access_token.assert_not_called()

    def test_provider_methods_are_owned_by_optional_glue(self):
        glue_manifest = ast.literal_eval((GLUE / "__manifest__.py").read_text())
        self.assertEqual(glue_manifest["depends"], ["amr_oidc", "amr_resource"])
        self.assertFalse(glue_manifest.get("auto_install", False))

        provider_tree = ast.parse((PROVIDER / "models/res_users.py").read_text())
        provider_class = next(node for node in provider_tree.body
                              if isinstance(node, ast.ClassDef))
        provider_methods = {node.name for node in provider_class.body
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(MOVED.isdisjoint(provider_methods))
        self.assertNotIn("get_mobile_access_token", provider_methods)
        self.assertIn("get_user_by_username", provider_methods)

        glue_tree = ast.parse((GLUE / "models/res_users.py").read_text())
        glue_class = next(node for node in glue_tree.body if isinstance(node, ast.ClassDef))
        glue_methods = {node.name for node in glue_class.body
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(MOVED <= glue_methods)
        self.assertIn("_get_access_token", glue_methods)

        resource_tree = ast.parse((ROOT / "amr_resource/models/res_users.py").read_text())
        resource_class = next(node for node in resource_tree.body
                              if isinstance(node, ast.ClassDef) and node.name == "ResUsers")
        resource_methods = {node.name for node in resource_class.body
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertTrue(MOVED <= resource_methods)

    def test_url_helpers_reject_bearer_creation(self):
        import importlib.util
        from unittest import mock

        support_path = PROVIDER / "tests/support.py"
        spec = importlib.util.spec_from_file_location("resource_glue_contract_support", support_path)
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        glue_module = support.load("models/res_users.py", addon=GLUE)
        model = glue_module.ResUsers()
        model.get_access_token = mock.Mock(side_effect=AssertionError("URL issuance attempted"))
        urls = (
            "https://app.example.invalid/path?keep=1",
            "https://app.example.invalid/path#fragment",
        )
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaisesRegex(glue_module.UserError, "URL access tokens are disabled"):
                    model.add_url_access_token(url)
                with self.assertRaisesRegex(glue_module.UserError, "URL access tokens are disabled"):
                    model.add_url_access_token(url, url_type="auto_login")
                with self.assertRaisesRegex(glue_module.UserError, "URL access tokens are disabled"):
                    model.get_auto_login_url(url)
        model.get_access_token.assert_not_called()

    def test_resource_routes_use_resource_owned_url_passthrough(self):
        resource = ROOT / "amr_resource"
        model_tree = ast.parse((resource / "models/res_users.py").read_text())
        resource_class = next(node for node in model_tree.body
                              if isinstance(node, ast.ClassDef) and node.name == "ResUsers")
        self.assertIn("_resource_access_url", {
            node.name for node in resource_class.body if isinstance(node, ast.FunctionDef)
        })
        controller = (resource / "controllers/main.py").read_text()
        self.assertNotIn("request.env.user.add_url_access_token", controller)
        self.assertIn("request.env.user._resource_access_url", controller)

    def test_provider_login_template_uses_provider_owned_visibility_hook(self):
        provider_tree = ast.parse((PROVIDER / "models/res_users.py").read_text())
        provider_class = next(node for node in provider_tree.body
                              if isinstance(node, ast.ClassDef))
        self.assertIn("_oidc_can_show_continue", {
            node.name for node in provider_class.body if isinstance(node, ast.FunctionDef)
        })
        template = (PROVIDER / "views/login_template.xml").read_text()
        self.assertIn("request.env.user._oidc_can_show_continue()", template)
        self.assertNotIn("request.env.user.is_user_allow_create_token()", template)


if __name__ == "__main__":
    unittest.main()
