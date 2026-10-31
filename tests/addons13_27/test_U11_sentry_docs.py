"""Documentation contract checks for the optional AMR Sentry addon."""
import importlib.util
import json
import os
import pathlib
import re
import tempfile
import unittest
from unittest.mock import patch

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

    def test_guides_document_target_and_test_only_dependency_boundary(self):
        for relpath in ('amr_sentry/README.md', 'amr_sentry/docs/operator.md'):
            text = (ROOT / relpath).read_text().lower()
            for phrase in ('odoo 13', 'cpython 3.7.3', 'test-only',
                           'requests', 'production compatibility', 'security clearance'):
                with self.subTest(guide=relpath, phrase=phrase):
                    self.assertIn(phrase, text)
            with self.subTest(guide=relpath, boundary='no approval'):
                self.assertRegex(text, r'not (?:a |an )?production compatibility or security clearance')

    def test_operator_discloses_original_exception_residual_risk(self):
        text = (ROOT / 'amr_sentry/docs/operator.md').read_text().lower()
        self.assertRegex(text, r'original exception[^\n]*sentry')
        for detail in ('message', 'chained cause', 'path/url', 'sensitive data'):
            with self.subTest(detail=detail):
                self.assertIn(detail, text)
        self.assertIn('residual', text)
        self.assertIn('not a guarantee', text)
        self.assertIn('owner accepted the bounded d-ex residual', text)
        self.assertIn('ecaba4b8-afcb-47b4-924b-94d97e4a1b9b', text)
        self.assertIn('exception-text uat remains unverified', text)
        self.assertIn('not privacy, runtime, or security pass', text)
        self.assertNotIn('until that decision', text)

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


class ActivatedOperatorExamples(unittest.TestCase):
    def test_yaml_and_json_examples_load_when_activated(self):
        text = (ROOT / 'amr_sentry/docs/operator.md').read_text()
        yaml_match = re.search(r'```yaml\s*\n(.*?)\n```', text, re.DOTALL)
        json_match = re.search(r'The equivalent JSON shape is `([^`]+)`', text)
        self.assertIsNotNone(yaml_match)
        self.assertIsNotNone(json_match)
        examples = ((".yaml", yaml.safe_load(yaml_match.group(1))),
                    (".json", json.loads(json_match.group(1))))
        self.assertEqual(examples[0][1], examples[1][1])
        spec = importlib.util.spec_from_file_location(
            'operator_config_test', ROOT / 'amr_sentry/services/config.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for suffix, example in examples:
            with self.subTest(format=suffix):
                self.assertIs(example['service_client']['enabled'], False)
                self.assertEqual(example['service_client']['mode'], 'none')
                example['service_client'].update(enabled=True, mode='error')
                example['sentry']['dsn'] = 'https://public@example.invalid/1'
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, encoding='utf-8') as stream:
                    if suffix == '.json':
                        json.dump(example, stream)
                    else:
                        yaml.safe_dump(example, stream)
                    stream.flush()
                    with patch.dict(os.environ, {'AMR_SENTRY_CONFIG': stream.name}):
                        try:
                            sentry, policy = module.load_config()
                        except module.SentryConfigError as error:
                            self.fail('Activated {} operator example rejected: {}'.format(suffix, error))
                self.assertEqual(sentry, example['sentry'])
                self.assertEqual(policy, {'enabled': True, 'mode': 'error'})
