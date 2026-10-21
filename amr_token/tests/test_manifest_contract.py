"""P-02 manifest contract derived from addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db."""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "amr_token" / "__manifest__.py"


class TestManifestContract(unittest.TestCase):
    def test_port_preserves_source_manifest_contract(self):
        self.assertTrue(MANIFEST.is_file(), "candidate addon manifest is missing")
        tree = ast.parse(MANIFEST.read_text(encoding="utf-8"), filename=str(MANIFEST))
        values = [node.value for node in tree.body if isinstance(node, ast.Expr)]
        self.assertTrue(values, "manifest must be a literal dictionary")
        manifest = ast.literal_eval(values[0])

        self.assertEqual(manifest["name"], "Token Provider")
        self.assertEqual(manifest["version"], "13.0.0.0.8")
        self.assertEqual(manifest["depends"], ["base", "base_setup", "web", "amr_resource"])
        self.assertEqual(manifest["external_dependencies"], {"python": ["pyjwt"]})
        self.assertEqual(
            manifest["data"],
            [
                "security/ir.model.access.csv",
                "views/public_key_views.xml",
                "views/menuitem.xml",
                "views/res_config_settings_views.xml",
            ],
        )
        self.assertNotIn("views/token_views.xml", manifest["data"])

    def test_manifest_registers_safe_demo_and_all_data_paths_exist(self):
        manifest = ast.literal_eval(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("demo"), ["demo/public_key_demo.xml"])
        for relative in manifest["data"] + manifest["demo"]:
            with self.subTest(path=relative):
                self.assertTrue((MANIFEST.parent / relative).is_file())
        self.assertNotIn("demo/public_key_demo.xml", manifest["data"])
        self.assertTrue((ROOT / "amr_resource" / "__manifest__.py").is_file())


if __name__ == "__main__":
    unittest.main()
