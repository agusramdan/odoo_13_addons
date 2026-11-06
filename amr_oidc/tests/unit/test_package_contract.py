"""Offline package contracts only; no registry, ORM, HTTP or security verdict.

Run from repository root with the pinned Python 3.8.20 test image:
python -B -m unittest discover -s amr_oidc/tests/unit -p 'test_*.py' -v
The addon root is deliberately never imported.
"""
import ast
from pathlib import Path
import unittest
from unittest import mock

try:
    from .support import load
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from support import load


ADDON = Path(__file__).resolve().parents[2]


class PackageContract(unittest.TestCase):
    def source(self, relative):
        path = ADDON / relative
        self.assertTrue(path.is_file(), "Missing candidate file: " + relative)
        return path.read_text(encoding="utf-8")

    def tree(self, relative):
        return ast.parse(self.source(relative))

    def model(self, relative, name):
        self.source(relative)
        return getattr(load(relative), name)

    def test_candidate_manifest_identity_and_dependencies(self):
        manifest = ast.literal_eval(self.source("__manifest__.py"))
        self.assertEqual(manifest["version"], "13.0.1.0.0")
        self.assertEqual(manifest["license"], "LGPL-3")
        self.assertEqual(manifest["depends"], ["base", "base_setup", "web"])
        # Distribution/import-name loader compatibility is not verified here.
        self.assertEqual(manifest["external_dependencies"]["python"],
                         ["pyjwt", "cryptography"])
        self.assertTrue(manifest["data"])
        self.assertFalse(manifest.get("auto_install", False))


    def test_client_nonsecret_declarations(self):
        client = self.model("models/oidc_client.py", "OidcClient")
        self.assertEqual(client._name, "oidc.client")
        self.assertTrue(client._description)
        self.assertEqual(client.user_id.args, ("res.users",))
        self.assertEqual(client.key_ids.args, ("oidc.client.key", "client_id"))
        self.assertEqual(client.authorization_ids.args,
                         ("oidc.authorization.code", "client_id"))

    def test_code_model_relationship_declarations_only(self):
        code = self.model("models/oidc_authorization_code.py", "OidcAuthorizationCode")
        self.assertEqual(code._name, "oidc.authorization.code")
        self.assertTrue(code._description)
        self.assertEqual(code.client_id.args, ("oidc.client",))
        self.assertEqual(code.user_id.args, ("res.users",))
        self.assertTrue(code.client_id.kwargs["required"])
        self.assertTrue(code.user_id.kwargs["required"])

    def test_key_model_identity_only_not_lifecycle(self):
        key = self.model("models/oidc_client_key.py", "OidcClientKey")
        self.assertEqual(key._name, "oidc.client.key")
        self.assertTrue(key._description)
        self.assertEqual(key.client_id.args, ("oidc.client",))

    def test_replay_model_identity_only_not_replay_policy(self):
        replay = self.model("models/oidc_jwt_replay.py", "OidcJwtReplay")
        self.assertEqual(replay._name, "oidc.jwt.replay")
        self.assertTrue(replay._description)

    def test_refresh_model_identity_only_not_refresh_behavior(self):
        refresh = self.model("models/oidc_refresh_token.py", "OidcRefreshToken")
        self.assertEqual(refresh._name, "oidc.refresh.token")
        self.assertTrue(refresh._description)
        self.assertEqual(refresh.user_id.args, ("res.users",))

    def load_token_helper(self):
        import types
        package_names = (
            "cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
            "cryptography.hazmat.primitives.asymmetric",
        )
        packages = {name: types.ModuleType(name) for name in package_names}
        for name in package_names[:-1]:
            packages[name].__path__ = []
        setattr(packages["cryptography.hazmat.primitives.asymmetric"], "ec", mock.Mock())
        setattr(packages["cryptography.hazmat.primitives.asymmetric"], "rsa", mock.Mock())
        with mock.patch.dict("sys.modules", packages):
            return self.model("models/token_helper.py", "TokenHelper")

    def test_helper_parent_dispatch_rejects_unhandled_grants(self):
        helper_class = self.load_token_helper()
        helper = helper_class()
        client = mock.Mock()
        client.client_credentials.return_value = {"access_token": "synthetic-token"}
        helper.env = {"oidc.client": client}

        grant_types = (
            None, "client_credentials", "authorization_code", "refresh_token",
            "password", "urn:ietf:params:oauth:grant-type:jwt-bearer", "unit_sentinel",
        )
        for grant_type in grant_types:
            with self.subTest(grant_type=grant_type):
                kwargs = {} if grant_type is None else {"grant_type": grant_type}
                result = helper.oidc_token(**kwargs)
                self.assertEqual(result.get("status"), 400)
                self.assertEqual(result.get("error"), "unsupported_grant_type")
                self.assertNotIn("access_token", result)
        client.client_credentials.assert_not_called()

    def test_unsupported_grant_handlers_are_not_registered(self):
        helper_class = self.load_token_helper()
        for method_name in (
                "_do_password_grant", "_do_challenge_grant", "_do_digital_signature_grant"):
            with self.subTest(method=method_name):
                self.assertFalse(callable(getattr(helper_class, method_name, None)))

    def test_oidc_helper_is_standalone_token_engine_base_and_adapter_alias(self):
        helper_class = self.load_token_helper()
        self.assertEqual(helper_class._name, "amr.oidc.helper")
        self.assertNotIn("amr.token.helper", self.source("models/token_helper.py"))

        adapter_path = ADDON.parent / "amr_token" / "models" / "helper.py"
        adapter_tree = ast.parse(adapter_path.read_text(encoding="utf-8"))
        adapter_class = next(
            node for node in adapter_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TokenHelper"
        )
        assignments = {
            target.id: ast.literal_eval(statement.value)
            for statement in adapter_class.body
            if isinstance(statement, ast.Assign)
            for target in statement.targets
            if isinstance(target, ast.Name)
        }
        self.assertEqual(assignments.get("_name"), "amr.token.helper")
        self.assertEqual(assignments.get("_inherit"), "amr.oidc.helper")
        self.assertFalse(any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for node in adapter_class.body
        ))

    def test_wizard_identity_only_not_export_or_generation(self):
        wizard = self.model("wizard/service_account.py", "OidcServiceAccountWizard")
        self.assertEqual(wizard._name, "oidc.service.account.wizard")
        self.assertTrue(wizard._description)
        self.assertEqual(wizard.client_id.args, ("oidc.client",))

    def test_controller_extends_target_controller_without_loading_http(self):
        tree = self.tree("controllers/main.py")
        controller = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        self.assertEqual(controller.name, "ControllerOIDC")
        self.assertEqual([node.id for node in controller.bases], ["Controller"])
        imports = [node.module for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertIn("odoo.http", imports)
        self.assertFalse(any(module and module.startswith("odoo.addons.amr_token")
                             for module in imports))

    def test_replay_acl_is_one_minimal_system_create_only_rule(self):
        import csv
        from io import StringIO
        rows = list(csv.DictReader(StringIO(self.source("security/ir.model.access.csv"))))
        replay_rows = [row for row in rows if row["model_id:id"] == "model_oidc_jwt_replay"]
        self.assertEqual(replay_rows, [{
            "id": "access_oidc_jwt_replay_provider_admin",
            "name": "access.oidc.jwt.replay.provider.admin",
            "model_id:id": "model_oidc_jwt_replay",
            "group_id:id": "base.group_system",
            "perm_read": "0",
            "perm_write": "0",
            "perm_create": "1",
            "perm_unlink": "0",
        }])

    def test_manifest_resources_and_local_template_assets_exist(self):
        import xml.etree.ElementTree as ET
        manifest = ast.literal_eval(self.source("__manifest__.py"))
        ids = set()
        for relative in manifest["data"]:
            with self.subTest(resource=relative):
                content = self.source(relative)
                if not relative.endswith(".xml"):
                    continue
                root = ET.fromstring(content)
                self.assertTrue(root.tag == "odoo")
                self.assertTrue([node.tag for node in root] == ["data"] or
                                all(node.tag == "record" for node in root))
                for node in root.iter():
                    if "id" in node.attrib:
                        self.assertFalse(node.attrib["id"] in ids)
                        ids.add(node.attrib["id"])
                    src = node.attrib.get("src", "")
                    if src.startswith("/amr_oidc/static/"):
                        self.assertTrue((ADDON / src[len("/amr_oidc/"):]).is_file())
        self.assertTrue("custom_login_template" in ids)
        self.assertTrue("custom_oidc_continue_template" in ids)

    def test_loaded_graph_is_connected_without_booting_addon_root(self):
        expected = {
            "__init__.py": {"controllers", "models", "wizard"},
            "models/__init__.py": {"token_helper", "public_key", "oidc_authorization_code", "oidc_client",
                                   "oidc_client_key", "oidc_client_grant", "oidc_jwt_replay",
                                   "oidc_refresh_token", "res_config_settings", "res_users"},
            "controllers/__init__.py": {"main"},
            "wizard/__init__.py": {"service_account"},
        }
        for relative, names in expected.items():
            with self.subTest(module=relative):
                tree = self.tree(relative)
                imports = {alias.name for node in tree.body
                           if isinstance(node, ast.ImportFrom) and node.level == 1
                           for alias in node.names}
                self.assertEqual(imports, names)
                for name in names:
                    folder = (ADDON / relative).parent
                    self.assertTrue((folder / (name + ".py")).is_file() or
                                    (folder / name / "__init__.py").is_file())

    def test_redirect_selection_is_a_materialized_odoo_selection(self):
        client = self.model("models/oidc_client.py", "OidcClient")
        selection = client.redirect_path.kwargs["selection"]
        self.assertTrue(isinstance(selection, list))
        self.assertEqual(selection, list(load("models/oidc_client.py").REDIRECT_MODE.items()))


    def test_existing_sudo_calls_have_local_provenance_comments(self):
        # Comments describe existing elevation; they do not endorse or add it.
        import tokenize
        from io import StringIO
        for relative in ("controllers/main.py",
                         "models/oidc_client.py", "models/oidc_refresh_token.py",
                         "wizard/service_account.py"):
            content = self.source(relative)
            comments = {token.start[0]: token.string for token in
                        tokenize.generate_tokens(StringIO(content).readline)
                        if token.type == tokenize.COMMENT}
            for node in ast.walk(ast.parse(content)):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "sudo":
                        with self.subTest(module=relative, line=node.lineno):
                            self.assertTrue("sudo:" in comments.get(node.lineno - 1, ""))


if __name__ == "__main__":
    unittest.main()
