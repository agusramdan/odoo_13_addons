"""Offline package contracts only; no registry, ORM, HTTP or security verdict.

Run from repository root with:
python3 -B -m unittest discover -s amr_oidc/tests -p 'test_*.py' -v
The addon root is deliberately never imported.
"""
import ast
from pathlib import Path
import unittest

try:
    from .support import load
except ImportError:
    from support import load


ADDON = Path(__file__).resolve().parents[1]


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
        self.assertEqual(manifest["depends"], ["base", "web", "amr_token"])
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

    def test_helper_parent_dispatch_rejects_unhandled_grants(self):
        helper = self.model("models/helper.py", "TokenHelper")
        self.assertEqual(helper._inherit, "amr.token.helper")
        # The isolated parent contract is fail-closed; no real token/auth flow runs.
        expected = {"status": 400, "error": "unsupported_grant_type"}
        self.assertEqual(helper().oidc_token(grant_type="unit_sentinel", marker=7), expected)
        self.assertEqual(helper().oidc_token(), expected)
        self.assertNotIn("oidc_token", helper.__dict__)

    def test_wizard_identity_only_not_export_or_generation(self):
        wizard = self.model("wizard/service_account.py", "OidcServiceAccountWizard")
        self.assertEqual(wizard._name, "oidc.service.account.wizard")
        self.assertTrue(wizard._description)
        self.assertEqual(wizard.client_id.args, ("oidc.client",))

    def test_controller_extends_target_controller_without_loading_http(self):
        tree = self.tree("controllers/main.py")
        controller = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        self.assertEqual(controller.name, "ControllerOIDC")
        self.assertEqual([node.id for node in controller.bases], ["ControllerToken"])
        imports = [node.module for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertTrue("odoo.addons.amr_token.controllers.main" in imports)

    def test_acl_source_bytes_preserved_not_an_access_policy_verdict(self):
        import hashlib
        # Owner exception: no replay ACL row; no added/removed privileges.
        # This is a preservation check, not acceptance of effective permissions.
        self.source("security/ir.model.access.csv")
        self.assertEqual(hashlib.sha256(
            (ADDON / "security/ir.model.access.csv").read_bytes()).hexdigest(),
            "6bacca85a84990610ad6db92bdf1a6e0b0c33064bf2199a8cb9f9218bb767476")

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
                self.assertEqual(root.tag, "odoo")
                self.assertEqual([node.tag for node in root], ["data"])
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
            "models/__init__.py": {"helper", "oidc_authorization_code", "oidc_client",
                                   "oidc_client_key", "oidc_jwt_replay", "oidc_refresh_token"},
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
        for relative in ("controllers/main.py", "models/helper.py",
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
