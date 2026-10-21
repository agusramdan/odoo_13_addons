"""P-01/P-07 pinned-source UI/ACL parity, not effective Odoo access evidence."""
import ast
import csv
import hashlib
import unittest
import xml.etree.ElementTree as ET

from support import ADDON


class TestDataContract(unittest.TestCase):
    def _source_file(self, relative, digest):
        path = ADDON / relative
        self.assertTrue(path.is_file(), f"missing pinned source data: {relative}")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        return path

    def test_public_key_views_preserves_source_contract(self):
        path = self._source_file('views/public_key_views.xml', 'c9321e59ee285e8d40032dd7761d8f98a36184d9345b9d49ef308a2d9d6ef8e0')
        root = ET.parse(path).getroot()
        self.assertEqual(root.tag, "odoo")
        self.assertEqual(root.findtext("./record[@id='action_amr_public_key']/field[@name='res_model']"), "amr.public.key")
        self.assertIsNotNone(root.find(".//field[@name='private_key']"))

    def test_settings_view_preserves_source_contract(self):
        path = self._source_file('views/res_config_settings_views.xml', 'd2eae955753b1e4dcfafbb572e80bcd48092a8c82c4a2b8f740df3637907f61e')
        root = ET.parse(path).getroot()
        self.assertEqual(root.findall(".//field[@name='inherit_id']")[0].get("ref"), "amr_resource.res_config_settings_view_form")
        self.assertEqual(root.findall(".//button")[0].get("name"), "action_create_public_key")

    def test_menu_preserves_source_contract(self):
        path = self._source_file('views/menuitem.xml', '408296ea453cdfdea07d39c4bb40fb91c08f8d635601d98292d6aed836db7180')
        root = ET.parse(path).getroot()
        self.assertEqual({item.get("groups") for item in root.findall("menuitem")}, {"base.group_no_one"})
        self.assertEqual(root.findall("./menuitem[@id='menu_public_key']")[0].get("action"), "action_amr_public_key")

    def test_unregistered_token_view_preserves_source_contract(self):
        path = self._source_file('views/token_views.xml', 'ec5b025ec11a2abc1e6e4269b5ed7ec1b47fc0a8adedabee963a8cdd4d7b565c')
        root = ET.parse(path).getroot()
        self.assertEqual(root.findtext("./record[@id='action_amr_token']/field[@name='res_model']"), "amr.token")
        manifest = ast.literal_eval((ADDON / "__manifest__.py").read_text())
        self.assertNotIn("views/token_views.xml", manifest["data"])

    def test_manager_acl_preserves_source_contract(self):
        path = self._source_file('security/ir.model.access.csv', '56866ffa58d67ef48044f524dece3ae59bb42c5dc13f0b670bd24625f415841f')
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows, [{
            "id": "access_amr_public_key_admin", "name": "access.amr.public.key admin",
            "model_id:id": "model_amr_public_key", "group_id:id": "base.group_erp_manager",
            "perm_read": "1", "perm_write": "1", "perm_create": "1", "perm_unlink": "1",
        }])
