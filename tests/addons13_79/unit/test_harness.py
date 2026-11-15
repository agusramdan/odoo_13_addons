import json
import ast
import hashlib
import importlib.util
from unittest import mock
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'prepare_run.py'


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.core = self.root / 'core'
        self.source.mkdir()
        self.core.mkdir()
        for name, deps in [('amr_resource', ['base', 'web', 'base_setup']),
                           ('amr_oidc', ['base']), ('amr_token', ['amr_oidc']),
                           ('amr_oidc_resource', ['amr_oidc', 'amr_resource'])]:
            self.addon(self.source, name, deps)
        for name in ('base', 'web', 'base_setup'):
            self.addon(self.core, name, [])

    def addon(self, root, name, deps):
        path = root / name
        path.mkdir()
        (path / '__manifest__.py').write_text(repr({'depends': deps}))
        (path / 'payload').write_bytes(b'unchanged')

    def run_adapter(self, selector, extra=None):
        args = [sys.executable, str(RUNNER), '--source', str(self.source),
                '--core', str(self.core), '--output', str(self.root / 'out'),
                '--selector', selector]
        return subprocess.run(args + (extra or []), capture_output=True, text=True)

    def test_resource_isolation_and_readonly_mount(self):
        before = (self.source / 'amr_resource' / 'payload').read_bytes()
        result = self.run_adapter('amr_resource')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(set(p.name for p in (self.root / 'out').iterdir()), {'amr_resource'})
        self.assertTrue(plan['mount'].endswith(',readonly'))
        self.assertTrue(plan['core_mount'].endswith(',readonly'))
        self.assertEqual(plan['addons_path'], ['/mnt/extra-addons', '/odoo-core'])
        self.assertIn('--addons-path=/mnt/extra-addons,/odoo-core', plan['odoo_args'])
        self.assertEqual((self.root / 'out/amr_resource/payload').read_bytes(), before)
        self.assertEqual((self.source / 'amr_resource/payload').read_bytes(), before)

    def test_nonresource_full_copy_fails_closed_without_verified_contract(self):
        for selector in ('amr_oidc', 'amr_oidc_resource'):
            result = self.run_adapter(selector)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('verified snapshot contract', result.stderr)
            self.assertFalse((self.root / 'out').exists())

    def test_core_sibling_injection_rejected(self):
        self.addon(self.core, 'amr_token', [])
        result = self.run_adapter('amr_resource')
        self.assertNotEqual(result.returncode, 0)

    def test_core_transitive_missing_or_forbidden_dependency_is_rejected(self):
        for dependency in ('missing_core_addon', 'amr_oidc'):
            with self.subTest(dependency=dependency):
                (self.core / 'base' / '__manifest__.py').write_text(
                    repr({'depends': [dependency]}))
                result = self.run_adapter('amr_resource')
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse((self.root / 'out').exists())

    def test_forbidden_dependency_is_rejected(self):
        (self.source / 'amr_resource' / '__manifest__.py').write_text(
            repr({'depends': ['base', 'amr_oidc']}))
        self.assertNotEqual(self.run_adapter('amr_resource').returncode, 0)

    def test_preparation_preserves_entire_source_and_current_commit(self):
        repo = RUNNER.parents[2]
        def inventory():
            return {str(p.relative_to(self.source)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.source.rglob('*') if p.is_file()}
        before = inventory()
        def git_head():
            gitdir = repo / '.git'
            if gitdir.is_file():
                gitdir = (repo / gitdir.read_text().strip().split(': ', 1)[1]).resolve()
            head = (gitdir / 'HEAD').read_text().strip()
            if not head.startswith('ref: '):
                return head
            ref = head[5:]
            common = gitdir
            if (gitdir / 'commondir').is_file():
                common = (gitdir / (gitdir / 'commondir').read_text().strip()).resolve()
            loose = common / ref
            if loose.is_file():
                return loose.read_text().strip()
            return next(line.split(' ', 1)[0] for line in (common / 'packed-refs').read_text().splitlines()
                        if not line.startswith(('#', '^')) and line.endswith(' ' + ref))
        head = git_head()
        self.assertEqual(self.run_adapter('amr_resource').returncode, 0)
        self.assertEqual(inventory(), before)
        self.assertEqual(git_head(), head)

    def test_cleartext_http_negative_has_no_forwarded_headers(self):
        repo = RUNNER.parents[2]
        source = (repo / 'amr_oidc/tests/integration/test_introspect_query_rejection.py').read_text()
        tree = ast.parse(source)
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == 'test_cleartext_post_is_rejected_before_client_authentication')
        request = next(n for n in ast.walk(method) if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Attribute) and n.func.attr == 'url_open')
        headers = next(k.value for k in request.keywords if k.arg == 'headers')
        self.assertNotIn('X-Forwarded-Proto', ast.literal_eval(headers))
        self.assertNotIn('X-Forwarded-Host', ast.literal_eval(headers))

    def test_traversal_alias_output_inside_source_or_core_is_rejected(self):
        def inventory(root):
            return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest()
                    if p.is_file() else None) for p in root.rglob('*')}

        (self.root / 'other').mkdir()
        for root in (self.source, self.core):
            with self.subTest(root=root.name):
                before_source, before_core = inventory(self.source), inventory(self.core)
                output = self.root / 'other' / '..' / root.name / 'alias-out'
                result = self.run_adapter('amr_resource', ['--output', str(output)])
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('must be disjoint', result.stderr)
                self.assertFalse((root / 'alias-out').exists())
                self.assertEqual(inventory(self.source), before_source)
                self.assertEqual(inventory(self.core), before_core)

    def test_traversal_cannot_hide_symlink_in_output_parent(self):
        (self.root / 'link').symlink_to(self.core, target_is_directory=True)
        output = self.root / 'link' / '..' / 'out'
        result = self.run_adapter('amr_resource', ['--output', str(output)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('symlink', result.stderr)
        self.assertFalse((self.root / 'out').exists())

    def test_traversal_alias_source_root_overlapping_output_is_rejected(self):
        (self.root / 'other').mkdir()
        source = self.root / 'other' / '..' / 'source'
        output = self.source / 'alias-out'
        result = self.run_adapter('amr_resource', ['--source', str(source), '--output', str(output)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must be disjoint', result.stderr)
        self.assertFalse(output.exists())

    def test_source_symlink_rejected(self):
        (self.source / 'amr_resource' / 'escape').symlink_to(self.core, target_is_directory=True)
        self.assertNotEqual(self.run_adapter('amr_resource').returncode, 0)

    def test_traversal_selector_rejected(self):
        self.assertNotEqual(self.run_adapter('../amr_resource').returncode, 0)

    def test_resource_process_has_no_proxy_mode(self):
        result = self.run_adapter('amr_resource')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('--proxy-mode', json.loads(result.stdout)['odoo_args'])

    def test_core_to_source_transitive_dependency_is_copied(self):
        self.addon(self.source, 'helper', [])
        (self.core / 'base' / '__manifest__.py').write_text(repr({'depends': ['helper']}))
        result = self.run_adapter('amr_resource')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in (self.root / 'out').iterdir()},
                         {'amr_resource', 'helper'})

    def test_core_cycle_is_rejected(self):
        (self.core / 'base' / '__manifest__.py').write_text(repr({'depends': ['web']}))
        (self.core / 'web' / '__manifest__.py').write_text(repr({'depends': ['base']}))
        result = self.run_adapter('amr_resource')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cycle', result.stderr)
        self.assertFalse((self.root / 'out').exists())

    def test_copy_failure_removes_partial_output(self):
        spec = importlib.util.spec_from_file_location('prepare_run', str(RUNNER))
        assert spec is not None and spec.loader is not None
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        with mock.patch.object(adapter.shutil, 'copytree', side_effect=OSError('copy failed')):
            with self.assertRaises(OSError):
                adapter.prepare(self.source, self.core, self.root / 'out', 'amr_resource')
        self.assertFalse((self.root / 'out').exists())

    def test_comma_output_rejected_before_creation(self):
        result = self.run_adapter('amr_resource', ['--output', str(self.root / 'bad,out')])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'bad,out').exists())


if __name__ == '__main__':
    unittest.main()
