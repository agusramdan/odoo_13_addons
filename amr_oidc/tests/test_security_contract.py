"""Focused offline policy contracts; these do not exercise Odoo ORM/HTTP."""
import ast
import csv
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import unittest
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET
from unittest.mock import patch

try:
    from .support import load, load_controller
except ImportError:
    from support import load, load_controller

ADDON = Path(__file__).resolve().parents[1]


class RedirectPolicyTest(unittest.TestCase):
    def test_external_redirect_requires_exact_query_and_fragment(self):
        client_class = load("models/oidc_client.py").OidcClient
        client = SimpleNamespace(
            redirect_path=False,
            redirect_uri="https://client.example.invalid/callback?tenant=blue#done",
        )

        accepted = client_class._validate_redirect_uri(
            client, "https://client.example.invalid/callback?tenant=red#done"
        )

        self.assertFalse(accepted)

    def test_external_redirect_fails_closed_when_allowlist_or_target_is_empty(self):
        client_class = load("models/oidc_client.py").OidcClient
        cases = (
            (SimpleNamespace(redirect_path=False, redirect_uri=""),
             "https://client.example.invalid/callback"),
            (SimpleNamespace(redirect_path=False,
                             redirect_uri="https://client.example.invalid/callback"),
             None),
        )
        for client, target in cases:
            with self.subTest(redirect_uri=target):
                self.assertFalse(client_class._validate_redirect_uri(client, target))

    def test_fixed_callback_accepts_only_absent_or_exact_request_target(self):
        client_class = load("models/oidc_client.py").OidcClient
        client = client_class()
        client.redirect_path = "auth_oauth_oidc"
        client.web_base_url = "https://issuer.example.invalid/"
        expected = "https://issuer.example.invalid/auth_oauth/oidc"

        self.assertTrue(client_class._validate_redirect_uri(client, None))
        self.assertTrue(client_class._validate_redirect_uri(client, expected))
        self.assertFalse(client_class._validate_redirect_uri(
            client, "https://attacker.example.invalid/callback"
        ))


class RedirectControllerPolicyTest(unittest.TestCase):
    def test_missing_external_redirect_is_rejected_before_code_creation(self):
        module = load_controller()

        class ClientStub:
            def __init__(self):
                self.redirect_uri = "https://client.example.invalid/callback"
                self.validated_targets = []
                self.created_codes = 0

            def _validate_redirect_uri(self, target):
                self.validated_targets.append(target)
                return target == self.redirect_uri

            def _create_authorization_code(self, redirect_uri=None, scope=""):
                self.created_codes += 1
                return SimpleNamespace(code="synthetic-code",
                                       redirect_uri=redirect_uri)

        client = ClientStub()

        class ClientModel:
            def sudo(self):
                return self

            def search(self, domain, limit=1):
                return client

        class Environment:
            def __getitem__(self, model_name):
                if model_name != "oidc.client":
                    raise AssertionError("Unexpected model: " + model_name)
                return ClientModel()

        module.request.env = Environment()
        result = module.ControllerOIDC().oidc_authorize(
            client_id="synthetic-client", response_type="code"
        )

        self.assertEqual(result, {"status": 400, "error": "invalid_redirect_uri"})
        self.assertEqual(client.validated_targets, [None])
        self.assertEqual(client.created_codes, 0)

    def test_invalid_external_redirect_is_rejected_before_login_redirect(self):
        module = load_controller()

        class ClientStub:
            name = "Synthetic Client"
            redirect_uri = "https://client.example.invalid/callback"

            def _validate_redirect_uri(self, target):
                return target == self.redirect_uri

        client = ClientStub()

        class ClientModel:
            def sudo(self):
                return self

            def search(self, domain, limit=1):
                return client

        class Environment:
            user = SimpleNamespace(_is_public=lambda: True)

            def __getitem__(self, model_name):
                if model_name != "oidc.client":
                    raise AssertionError("Unexpected model: " + model_name)
                return ClientModel()

        module.request.env = Environment()
        result = module.ControllerOIDC().authorize(
            client_id="synthetic-client",
            redirect_uri="https://attacker.example.invalid/callback",
            response_type="code",
        )

        self.assertEqual(result, {"status": 400, "error": "invalid_redirect_uri"})

    def test_exact_external_redirect_preserves_query_and_fragment(self):
        module = load_controller()
        registered = "https://client.example.invalid/callback?tenant=blue#done"

        class ClientStub:
            def _validate_redirect_uri(self, target):
                return target == registered

            def _create_authorization_code(self, redirect_uri=None, scope=""):
                return SimpleNamespace(code="synthetic-code", redirect_uri=redirect_uri)

        client = ClientStub()

        class ClientModel:
            def sudo(self):
                return self

            def search(self, domain, limit=1):
                return client

        class Environment:
            def __getitem__(self, model_name):
                if model_name != "oidc.client":
                    raise AssertionError("Unexpected model: " + model_name)
                return ClientModel()

        module.request.env = Environment()
        result = module.ControllerOIDC().oidc_authorize(
            client_id="synthetic-client",
            response_type="code",
            redirect_uri=registered,
            state="synthetic-state",
        )
        parsed = urlsplit(result["redirect"])
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "client.example.invalid")
        self.assertEqual(parsed.path, "/callback")
        self.assertEqual(parsed.fragment, "done")
        self.assertEqual(query["tenant"], ["blue"])
        self.assertEqual(query["code"], ["synthetic-code"])
        self.assertEqual(query["state"], ["synthetic-state"])

    def test_implicit_token_response_stays_in_fragment(self):
        module = load_controller()
        registered = "https://client.example.invalid/callback?tenant=blue#existing"

        class ClientStub:
            def _validate_redirect_uri(self, target):
                return target == registered

            def _create_access_token(self, redirect_uri=None, scope="", **kwargs):
                return SimpleNamespace(token="synthetic-access-token",
                                       redirect_uri=redirect_uri,
                                       get_expires_in=lambda: 3600)

        client = ClientStub()

        class ClientModel:
            def sudo(self):
                return self

            def search(self, domain, limit=1):
                return client

        class Environment:
            def __getitem__(self, model_name):
                if model_name != "oidc.client":
                    raise AssertionError("Unexpected model: " + model_name)
                return ClientModel()

        module.request.env = Environment()
        result = module.ControllerOIDC().oidc_authorize(
            client_id="synthetic-client",
            response_type="token",
            redirect_uri=registered,
        )
        parsed = urlsplit(result["redirect"])
        fragment_params = parse_qs(parsed.fragment)

        self.assertEqual(parsed.query, "tenant=blue")
        self.assertTrue(parsed.fragment.startswith("existing&"))
        self.assertEqual(fragment_params["access_token"],
                         ["synthetic-access-token"])


class CsrfPolicyTest(unittest.TestCase):
    def test_state_changing_routes_are_post_only_and_csrf_enabled(self):
        tree = ast.parse((ADDON / "controllers/main.py").read_text(encoding="utf-8"))
        expected_paths = {"/oidc/authorize_continue", "/oidc/login/submit"}
        route_options = {}
        for class_node in tree.body:
            if not isinstance(class_node, ast.ClassDef):
                continue
            for method in class_node.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                for decorator in method.decorator_list:
                    if not (isinstance(decorator, ast.Call)
                            and isinstance(decorator.func, ast.Name)
                            and decorator.func.id == "route"):
                        continue
                    paths = ast.literal_eval(decorator.args[0])
                    if isinstance(paths, str):
                        paths = [paths]
                    options = {item.arg: ast.literal_eval(item.value)
                               for item in decorator.keywords}
                    for path in paths:
                        if path in expected_paths:
                            route_options[path] = options

        self.assertEqual(set(route_options), expected_paths)
        for path in expected_paths:
            with self.subTest(path=path):
                self.assertEqual(route_options[path].get("methods"), ["POST"])
                self.assertIsNot(route_options[path].get("csrf", True), False)

    def test_login_and_continue_forms_include_csrf_tokens(self):
        root = ET.parse(ADDON / "views/login_template.xml").getroot()
        templates = {node.get("id"): node for node in root.iter("template")}
        cases = (
            ("custom_login_template", "/oidc/login/submit"),
            ("custom_oidc_continue_template", "/oidc/authorize_continue"),
        )
        for template_id, action in cases:
            with self.subTest(template=template_id):
                forms = [node for node in templates[template_id].iter("form")
                         if node.get("action") == action]
                self.assertEqual(len(forms), 1)
                self.assertEqual(forms[0].get("method"), "post")
                tokens = [node for node in forms[0].iter("input")
                          if node.get("name") == "csrf_token"]
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0].get("type"), "hidden")
                self.assertEqual(tokens[0].get("t-att-value"),
                                 "request.csrf_token()")


class RpcBoundaryPolicyTest(unittest.TestCase):
    def test_sensitive_refresh_and_client_operations_are_not_public_rpc_methods(self):
        client = load("models/oidc_client.py").OidcClient
        refresh = load("models/oidc_refresh_token.py").OidcRefreshToken
        client_private = (
            "_check_credentials", "_validate_redirect_uri", "_client_auth",
            "_create_authorization_code", "_create_access_token", "_validate_token",
            "_validate_refresh_token",
        )
        client_public = (
            "check_credentials", "validate_redirect_uri", "client_auth",
            "create_authorization_code", "create_access_token", "validate_token",
            "validate_refresh_token",
        )

        for name in client_public:
            with self.subTest(model="oidc.client", method=name):
                self.assertFalse(hasattr(client, name))
        for name in client_private:
            with self.subTest(model="oidc.client", method=name):
                self.assertTrue(hasattr(client, name))
        self.assertFalse(hasattr(refresh, "validate_token"))
        self.assertTrue(hasattr(refresh, "_validate_token"))


class FixedRedirectGenerationTest(unittest.TestCase):
    def test_authorization_code_uses_the_exact_fixed_callback(self):
        module = load("models/oidc_client.py")
        client = module.OidcClient()
        client.redirect_path = "auth_oauth_oidc"
        client.web_base_url = "https://issuer.example.invalid/"
        client.client_id = "synthetic-client"
        code_model = SimpleNamespace()
        code_model.sudo = lambda: code_model
        code_model.create = lambda values: values

        class Environment:
            user = SimpleNamespace(id=7)

            def __getitem__(self, model_name):
                if model_name != "oidc.authorization.code":
                    raise AssertionError("Unexpected model: " + model_name)
                return code_model

        client.env = Environment()
        now = datetime(2026, 1, 1, 12, 0, 0)
        with patch.object(module.fields.Datetime, "now", return_value=now, create=True):
            code = client._create_authorization_code()

        self.assertEqual(code["redirect_uri"],
                         "https://issuer.example.invalid/auth_oauth/oidc")


    def test_authorization_code_creation_does_not_add_model_level_sudo(self):
        module = load("models/oidc_client.py")
        client = module.OidcClient()
        client.redirect_path = False
        client.redirect_uri = "https://client.example.invalid/callback"
        client.client_id = "synthetic-client"

        class CodeModel:
            def sudo(self):
                raise AssertionError("code creation must use the validated controller env")

            def create(self, values):
                return values

        class Environment:
            user = SimpleNamespace(id=7)

            def __getitem__(self, model_name):
                if model_name != "oidc.authorization.code":
                    raise AssertionError("Unexpected model: " + model_name)
                return CodeModel()

        client.env = Environment()
        now = datetime(2026, 1, 1, 12, 0, 0)
        with patch.object(module.fields.Datetime, "now", return_value=now, create=True):
            code = client._create_authorization_code(
                redirect_uri="https://client.example.invalid/callback"
            )
        self.assertEqual(code["client_id"], "synthetic-client")


class ClientSecretPolicyTest(unittest.TestCase):
    def test_client_secret_field_is_restricted_to_admin_oidc_group(self):
        client = load("models/oidc_client.py").OidcClient
        self.assertEqual(client.client_secret.kwargs.get("groups"),
                         "base.group_erp_manager")


class RefreshTokenPolicyTest(unittest.TestCase):
    def _validate_with_expiry(self, expires_at):
        module = load("models/oidc_refresh_token.py")
        now = datetime(2026, 1, 1, 12, 0, 0)
        record = {
            "token": "synthetic-refresh-token",
            "revoked": False,
            "expires_at": expires_at,
        }
        payload = {"token": record["token"]}

        class ModelStub:
            def get_secret(self):
                return "synthetic-secret"

            def get_issuer(self):
                return "https://issuer.example.invalid"

            def get_algorithm(self):
                return "HS256"

            def sudo(self):
                return self

            def search(self, domain, limit=1):
                for field, operator, expected in domain:
                    actual = record[field]
                    if operator == "=":
                        if actual != expected:
                            return None
                    elif operator == "<":
                        if not actual < expected:
                            return None
                    elif operator == ">":
                        if not actual > expected:
                            return None
                    elif operator == ">=":
                        if not actual >= expected:
                            return None
                    else:
                        raise AssertionError("Unexpected search operator: " + operator)
                return record

        module.jwt.decode = lambda *args, **kwargs: payload
        with patch.object(module.fields.Datetime, "now", return_value=now, create=True):
            return module.OidcRefreshToken._validate_token(
                ModelStub(), "synthetic-signed-jwt", "client-audience"
            )

    def test_expired_refresh_token_is_rejected(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        self.assertIsNone(self._validate_with_expiry(now - timedelta(seconds=1)))

    def test_refresh_token_expiring_at_now_is_rejected(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        self.assertIsNone(self._validate_with_expiry(now))

    def test_unexpired_refresh_token_is_accepted(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        self.assertEqual(self._validate_with_expiry(now + timedelta(seconds=1)),
                         {"token": "synthetic-refresh-token"})


class AccessControlPolicyTest(unittest.TestCase):
    def test_refresh_token_acl_is_limited_to_system_admin(self):
        with (ADDON / "security/ir.model.access.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        access = [row for row in rows
                  if row["model_id:id"] == "model_oidc_refresh_token"]

        self.assertEqual(len(access), 1)
        self.assertEqual(access[0]["group_id:id"], "base.group_system")

    def test_client_acl_is_limited_to_admin_oidc_group(self):
        with (ADDON / "security/ir.model.access.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        access = [row for row in rows
                  if row["model_id:id"] == "model_oidc_client"]

        self.assertEqual([row["group_id:id"] for row in access],
                         ["base.group_erp_manager"])

    def test_authorization_code_acl_is_limited_to_admin_oidc_group(self):
        with (ADDON / "security/ir.model.access.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        access = [row for row in rows
                  if row["model_id:id"] == "model_oidc_authorization_code"]

        self.assertEqual([row["group_id:id"] for row in access],
                         ["base.group_erp_manager"])


if __name__ == "__main__":
    unittest.main()
