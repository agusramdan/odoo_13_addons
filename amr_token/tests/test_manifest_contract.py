"""P-02 manifest contract derived from addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "amr_token" / "__manifest__.py"
OIDC_MANIFEST = ROOT / "amr_oidc" / "__manifest__.py"


class TestManifestContract(unittest.TestCase):
    def test_token_manifest_preserves_provider_metadata_and_dependency_contract(self):
        manifest = ast.literal_eval(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "Token Provider")
        self.assertEqual(manifest["version"], "13.0.0.0.8")
        self.assertEqual(manifest["depends"], ["base", "base_setup", "web", "amr_resource"])
        self.assertEqual(manifest["external_dependencies"], {"python": ["pyjwt"]})
        self.assertEqual(manifest["data"], [
            "security/ir.model.access.csv",
            "views/res_config_settings_views.xml",
        ])
        self.assertNotIn("views/token_views.xml", manifest["data"])

    def test_token_manifest_does_not_register_moved_key_resources(self):
        manifest = ast.literal_eval(MANIFEST.read_text(encoding="utf-8"))
        self.assertNotIn("public_key", str(manifest["data"]))
        self.assertNotIn("views/menuitem.xml", manifest["data"])
        self.assertNotIn("demo/public_key_demo.xml", manifest.get("demo", []))
        oidc = ast.literal_eval(OIDC_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue((ROOT / "amr_resource" / "__manifest__.py").is_file())
        self.assertIn("views/public_key_views.xml", oidc["data"])
        self.assertIn("views/menuitem.xml", oidc["data"])

    def test_manifest_registers_safe_demo_and_all_data_paths_exist(self):
        manifest = ast.literal_eval(OIDC_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("demo"), ["demo/public_key_demo.xml"])
        for relative in manifest["data"] + manifest["demo"]:
            with self.subTest(path=relative):
                self.assertTrue((OIDC_MANIFEST.parent / relative).is_file())
        self.assertNotIn("demo/public_key_demo.xml", manifest["data"])


if __name__ == "__main__":
    unittest.main()
