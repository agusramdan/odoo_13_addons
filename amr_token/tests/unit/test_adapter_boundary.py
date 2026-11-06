"""Compatibility adapter has no provider routes, settings, or user extension."""
import ast
from pathlib import Path
import unittest

ADDON = Path(__file__).resolve().parents[2]


class AdapterBoundaryTests(unittest.TestCase):
    def test_manifest_depends_only_on_oidc_provider(self):
        manifest = ast.literal_eval((ADDON / "__manifest__.py").read_text())
        self.assertEqual(manifest["depends"], ["amr_oidc"])
        self.assertEqual(manifest["data"], [])
        self.assertNotIn("external_dependencies", manifest)

    def test_legacy_package_has_no_routes_settings_or_user_extension(self):
        self.assertFalse((ADDON / "controllers" / "main.py").exists())
        self.assertFalse((ADDON / "models" / "res_users.py").exists())
        self.assertFalse((ADDON / "models" / "res_config_settings.py").exists())
        models = (ADDON / "models" / "helper.py").read_text()
        self.assertIn("_inherit = 'amr.oidc.helper'", models)
        self.assertIn("_name = 'amr.token.helper'", models)
        self.assertEqual(models.count("_inherit = 'amr.oidc.helper'"), 1)
        self.assertNotIn("@api.model", models)


if __name__ == "__main__":
    unittest.main()
