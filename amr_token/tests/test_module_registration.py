"""P-01 Odoo addon registration-chain contract."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
ADDON = ROOT / "amr_token"


def _relative_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.level == 1
        for alias in node.names
    }


class TestModuleRegistration(unittest.TestCase):
    def test_addon_root_loads_models_and_controllers(self):
        path = ADDON / "__init__.py"
        self.assertTrue(path.is_file(), "candidate addon root initializer is missing")
        self.assertEqual(_relative_imports(path), {"models", "controllers"})

    def test_models_initializer_imports_all_source_models(self):
        path = ADDON / "models" / "__init__.py"
        self.assertTrue(path.is_file(), "candidate models initializer is missing")
        self.assertEqual(_relative_imports(path), {"helper", "res_users", "res_config_settings"})
        oidc_models = ROOT / "amr_oidc" / "models" / "__init__.py"
        self.assertIn("public_key", _relative_imports(oidc_models))
        self.assertFalse((ADDON / "models" / "public_key.py").exists())

    def test_controllers_initializer_loads_main(self):
        path = ADDON / "controllers" / "__init__.py"
        self.assertTrue(path.is_file(), "candidate controllers initializer is missing")
        self.assertEqual(_relative_imports(path), {"main"})


if __name__ == "__main__":
    unittest.main()
