"""Documentation contract checks for the optional AMR Sentry addon."""
import pathlib
import re

import yaml

from support import OfflineCase, ROOT


class SentryDocs(OfflineCase):
    def _guides_exist(self):
        exists = all((ROOT / relpath).is_file() for relpath in (
            'amr_sentry/README.md', 'amr_sentry/docs/operator.md'))
        self.assertTrue(exists, 'missing operator documentation: amr_sentry/README.md or amr_sentry/docs/operator.md')
        return exists

    def test_operator_guides_and_entry_point_links_exist(self):
        if not self._guides_exist():
            return
        required = ('amr_sentry/README.md', 'amr_sentry/docs/operator.md')
        for relpath in required:
            self.assertTrue((ROOT / relpath).is_file(), f'missing operator documentation: {relpath}')
        for relpath, target in (
                ('README.md', 'amr_sentry/README.md'),
                ('amr_service_client/README.md', '../amr_sentry/README.md')):
            text = (ROOT / relpath).read_text()
            links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', text)
            self.assertIn(target, links, f'{relpath} must link to {target}')

    def test_root_addon_index_lists_optional_addon(self):
        text = (ROOT / 'README.md').read_text()
        rows = [line for line in text.splitlines() if line.startswith('| [amr_sentry]')]
        self.assertEqual(len(rows), 1, 'root addon index must list amr_sentry exactly once')
        for required in ('13.0.1.0.0', 'amr_service_client', 'sentry_sdk', 'yaml', 'Development/demo-only'):
            self.assertIn(required, rows[0])

    def test_configuration_mechanism_and_policy_are_documented(self):
        if not self._guides_exist():
            return
        docs = '\n'.join((ROOT / relpath).read_text() for relpath in (
            'amr_sentry/README.md', 'amr_sentry/docs/operator.md'))
        for required in (
                'AMR_SENTRY_CONFIG', '/etc/odoo/amr_sentry.yaml', '.yaml', '.yml', '.json',
                'sentry', 'service_client', 'enabled: false', 'mode: none',
                'all', 'error', 'selected', 'none', 'sentry_opt_in', 'restart',
                'sentry-sdk==2.73.0', 'PyYAML==6.0.1', 'amr_service_client'):
            with self.subTest(required=required):
                self.assertIn(required, docs)

    def test_yaml_example_is_valid_and_safe_by_default(self):
        if not self._guides_exist():
            return
        docs = '\n'.join((ROOT / relpath).read_text() for relpath in (
            'amr_sentry/README.md', 'amr_sentry/docs/operator.md'))
        match = re.search(r'```ya?ml\s*\n(.*?)\n```', docs, re.DOTALL | re.IGNORECASE)
        self.assertIsNotNone(match, 'operator documentation must include a fenced YAML example')
        config = yaml.safe_load(match.group(1))
        self.assertIsInstance(config, dict)
        self.assertIsInstance(config.get('sentry'), dict)
        self.assertIsInstance(config.get('service_client'), dict)
        self.assertIs(config['service_client'].get('enabled'), False)
        self.assertEqual(config['service_client'].get('mode'), 'none')
        dsn = config['sentry'].get('dsn', '')
        self.assertIn('example.invalid', dsn)
        self.assertNotIn('sentry.io', dsn)
