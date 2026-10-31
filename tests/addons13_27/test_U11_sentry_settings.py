# -*- coding: utf-8 -*-
"""Contracts for removing global Sentry settings while retaining client opt-in."""
import ast
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ADDON_ROOT = Path(__file__).resolve().parents[2] / 'amr_service_client'


class TestSentrySettingsRemoval(unittest.TestCase):
    def test_legacy_global_sentry_settings_are_removed_from_core(self):
        model_path = ADDON_ROOT / 'models' / 'res_config_settings.py'
        view_path = ADDON_ROOT / 'views' / 'res_config_settings_views.xml'
        models_init = (ADDON_ROOT / 'models' / '__init__.py').read_text()
        manifest = ast.literal_eval((ADDON_ROOT / '__manifest__.py').read_text())

        self.assertFalse(model_path.exists(), 'legacy global Sentry settings model file must be absent')
        self.assertFalse(view_path.exists(), 'legacy global Sentry settings view file must be absent')
        self.assertNotRegex(models_init, r'(?m)^\s*from\s+\.\s+import\s+res_config_settings\s*$')
        self.assertNotIn('views/res_config_settings_views.xml', manifest.get('data', []))

    def test_per_client_sentry_opt_in_remains_declared_and_visible(self):
        model_source = (ADDON_ROOT / 'models' / 'service_client.py').read_text()
        self.assertRegex(model_source, r'(?m)^\s*sentry_opt_in\s*=\s*fields\.Boolean\b')

        view_root = ET.parse(ADDON_ROOT / 'views' / 'service_client_views.xml').getroot()
        client_form = view_root.find(".//record[@id='service_client_form']")
        if client_form is None:
            self.fail('service client form view must be present')
        fields = client_form.findall(".//field[@name='sentry_opt_in']")
        self.assertTrue(fields, 'sentry_opt_in must remain visible in the service client form')


if __name__ == '__main__':
    unittest.main()
