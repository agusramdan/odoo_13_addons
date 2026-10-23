"""Offline checks of candidate migration planning and protected key resolution."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from test_registry_unit import load_registry, IssuerProbe, ValidationError, AccessError

ROOT = Path(__file__).resolve().parents[1]


class MigrationUnitTests(unittest.TestCase):
    def setUp(self):
        self.module = load_registry()
        self.params = {
            'amr_resource.issuer': 'legacy.issuer',
            'amr_resource.audience': 'legacy.audience',
            'legacy.issuer': 'https://issuer.invalid',
            'legacy.audience': 'resource-a',
        }
        self.values = dict(issuer='https://issuer.invalid', client_id='client-a',
                           token_profile='jwt', jwks_uri='https://keys.invalid/jwks',
                           allow_missing_azp=True, resolver_mode='get_user_match')
        self.bindings = [dict(sub='subject-a', user_id=42)]

    def plan(self, **kw):
        return self.module._legacy_plan(
            self.params.get, kw.get('values', self.values),
            kw.get('audiences', ['resource-a']), kw.get('bindings', self.bindings), 7)

    def test_explicit_versioned_plan_is_deterministic_and_preserves_inputs(self):
        original = dict(self.params)
        first = self.plan()
        self.assertEqual(first, self.plan())
        self.assertEqual(first['version'], 1)
        self.assertEqual(first['values']['company_id'], 7)
        self.assertEqual(first['audiences'], ['resource-a'])
        self.assertEqual(len(first['digest']), 64)
        self.assertEqual(self.params, original)
        self.assertNotIn('company_id', self.values)
        self.assertNotIn('password', str(first))

    def test_key_indirection_is_never_treated_as_url_or_default(self):
        for selector in (None, '', 'https://issuer.invalid', 'missing.key', 'legacy.issuer '):
            with self.subTest(selector_type=type(selector).__name__):
                self.params['amr_resource.issuer'] = selector
                with self.assertRaises(ValidationError):
                    self.plan()

    def test_conflicting_issuer_audience_and_ambiguous_binding_rejected(self):
        for kw in (
            dict(values=dict(self.values, issuer='https://other.invalid')),
            dict(audiences=['other']), dict(audiences=['resource-a', 'resource-a']),
            dict(audiences=['resource-a', '']), dict(bindings=self.bindings * 2),
            dict(bindings=[dict(sub='subject-a', user_id=True)]),
            dict(bindings=[dict(sub='subject-a', user_id=0)]),
            dict(bindings=[dict(email='user@example.invalid', user_id=42)]),
            dict(values=dict(self.values, python_code='disabled')),
            dict(values=dict(self.values, company_id=8)),
            dict(values=dict(self.values, resolver_mode='')),
        ):
            with self.subTest(fields=sorted(kw)):
                with self.assertRaises(ValidationError):
                    self.plan(**kw)

    def test_plan_fingerprint_detects_reference_and_binding_revision(self):
        old = self.plan()['digest']
        self.assertNotEqual(old, self.plan(bindings=[dict(sub='subject-b', user_id=42)])['digest'])
        self.params['amr_resource.issuer'] = 'new.reference'
        self.params['new.reference'] = 'https://issuer.invalid'
        self.assertNotEqual(old, self.plan()['digest'])

    def test_local_key_compute_reads_only_explicit_protected_reference(self):
        compute = self.module.AmrResourceIssuer._compute_local_public_key
        params = SimpleNamespace(sudo=Mock(), get_param=Mock(return_value='synthetic-public-pem'))
        params.sudo.return_value = params
        row = SimpleNamespace(local_key_ref='amr_resource.keys.synthetic', local_public_key=False)
        probe = SimpleNamespace(env={'ir.config_parameter': params})
        # The method iterates records; use a minimal ORM boundary, not a replacement compute.
        class Records(list):
            env = probe.env
        compute(Records([row]))
        self.assertEqual(row.local_public_key, 'synthetic-public-pem')
        params.get_param.assert_called_once_with('amr_resource.keys.synthetic')
        params.get_param.reset_mock()
        row.local_key_ref = False
        compute(Records([row]))
        self.assertFalse(row.local_public_key)
        params.get_param.assert_not_called()

    def test_inline_local_key_input_rejected_before_orm(self):
        probe = SimpleNamespace()
        with self.assertRaises(AccessError):
            self.module.AmrResourceIssuer._guard_issuer_values(probe, {'local_public_key': 'inline'})

    def test_pinned_dependency_and_python_runtime(self):
        import sys
        import jwt
        import cryptography
        self.assertEqual(sys.version_info[:3], (3, 7, 9))
        self.assertEqual(jwt.__version__, '2.8.0')
        self.assertEqual(cryptography.__version__, '39.0.2')
        import cffi
        import pycparser
        self.assertEqual(cffi.__version__, '1.15.1')
        self.assertEqual(pycparser.__version__, '2.21')

    def test_native_loader_and_dependency_declarations(self):
        import ast
        manifest = ast.literal_eval((ROOT / '__manifest__.py').read_text())
        self.assertEqual(manifest['external_dependencies']['python'], ['jwt', 'cryptography'])
        pins = (ROOT / 'requirements.txt').read_text()
        self.assertIn('PyJWT==2.8.0', pins)
        self.assertIn('cryptography==39.0.2', pins)
        source = (ROOT / 'tests/__init__.py').read_text()
        self.assertIn('test_registry', source)
        self.assertNotIn('test_security_unit', source)
        settings = ast.parse((ROOT / 'models/res_config_settings.py').read_text())
        self.assertNotIn('amr_select_issuer', [n.targets[0].id for n in ast.walk(settings)
                         if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)])


    def test_actual_migration_dry_run_apply_repeat_and_conflicts(self):
        from contextlib import contextmanager
        from unittest.mock import Mock
        module = self.module
        storage = dict(self.params)
        params = SimpleNamespace(get_param=lambda key: storage.get(key),
                                 set_param=Mock(side_effect=lambda key, value: storage.update({key: value})))
        params.sudo = lambda: params
        company = SimpleNamespace(id=7)
        rows = []
        @contextmanager
        def savepoint():
            yield
        helper = SimpleNamespace(_eligible_user=Mock())
        users = SimpleNamespace(browse=lambda uid: SimpleNamespace(exists=lambda: SimpleNamespace(id=uid)))
        class Environment(dict):
            user = SimpleNamespace(share=False, has_group=lambda group: True)
            uid = 9
            cr = SimpleNamespace(savepoint=savepoint)
        env = Environment({'ir.config_parameter': params, 'amr.resource.helper': helper,
                           'res.users': users})
        env.company = company
        class Row(SimpleNamespace):
            def __getitem__(self, key):
                return getattr(self, key)
        class Children(list):
            def mapped(self, name):
                return [getattr(child, name) for child in self]
        class Rows(list):
            def __getattr__(self, name):
                return getattr(self[0], name)
            def __getitem__(self, key):
                return getattr(list.__getitem__(self, 0), key) if isinstance(key, str) else list.__getitem__(self, key)
        class Registry(module.AmrResourceIssuer):
            _registry_role = module.RegistryAccess._registry_role
            def check_access_rights(self, operation):
                return True
            def with_context(self, **kw):
                return self
            def sudo(self):
                return self
            def search(self, domain):
                return Rows(rows)
            def new(self, data):
                return SimpleNamespace(_check_profile=Mock())
            def create(self, data):
                self.created += 1
                fields = dict(data)
                fields['fixed_user_id'] = SimpleNamespace(id=fields['fixed_user_id'])
                fields['company_id'] = company
                fields['active'] = True
                fields['audience_ids'] = Children([SimpleNamespace(**c[2]) for c in data['audience_ids']])
                fields['binding_ids'] = Children([SimpleNamespace(sub=c[2]['sub'],
                    user_id=SimpleNamespace(id=c[2]['user_id'])) for c in data['binding_ids']])
                rows.append(Row(**fields))
                return Rows(rows)
        registry = Registry()
        registry.env, registry.created = env, 0
        args = (self.values, ['resource-a'], self.bindings)
        result = registry._migrate_legacy_v1(*args)
        self.assertTrue(result['dry_run'])
        self.assertEqual(registry.created, 0)
        params.set_param.assert_not_called()
        result = registry._migrate_legacy_v1(*args, dry_run=False)
        self.assertFalse(result['already_applied'])
        self.assertEqual(registry.created, 1)
        self.assertEqual(registry._migrate_legacy_v1(*args, dry_run=False)['already_applied'], True)
        self.assertEqual(registry.created, 1)
        self.assertEqual(params.set_param.call_count, 1)
        self.assertEqual(storage['legacy.issuer'], self.params['legacy.issuer'])
        rows[0].client_id = 'conflicting-client'
        with self.assertRaises(ValidationError):
            registry._migrate_legacy_v1(*args, dry_run=False)
        rows[0].client_id = self.values['client_id']
        rows[0].binding_ids[0].sub = 'conflicting-subject'
        with self.assertRaises(ValidationError):
            registry._migrate_legacy_v1(*args, dry_run=False)
        rows[:] = []
        with self.assertRaises(ValidationError):
            registry._migrate_legacy_v1(*args, dry_run=False)
        with self.assertRaises(ValidationError):
            registry._migrate_legacy_v1(self.values, ['resource-a'], [], dry_run=False)
        env.user = SimpleNamespace(share=False, has_group=lambda group: False)
        with self.assertRaises(AccessError):
            registry._migrate_legacy_v1(*args)
        self.assertEqual(registry.created, 1)

if __name__ == '__main__':
    unittest.main()
