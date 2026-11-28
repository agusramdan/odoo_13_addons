import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).parents[3] / '.agents' / 'skills' / 'odoo-unit-test' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from mock_odoo import odoo_modules


def load_registry():
    path = Path(__file__).parents[2] / 'models' / 'trust_registry.py'
    helper = types.ModuleType('amr_resource.models.helper')
    helper._PROVENANCE = object()
    helper._string = helper._manual_key_source = helper._require_policy_revision = lambda *a: None
    helper.fetch_json = lambda *a, **kw: None
    spec = importlib.util.spec_from_file_location('amr_resource.models.trust_registry', path)
    module = importlib.util.module_from_spec(spec)
    packages = {'amr_resource': types.ModuleType('amr_resource'),
                'amr_resource.models': types.ModuleType('amr_resource.models')}
    packages['amr_resource'].__path__ = [str(Path(__file__).parents[2])]
    packages['amr_resource.models'].__path__ = [str(path.parent)]
    with odoo_modules():
        import odoo
        odoo.SUPERUSER_ID = 1
        with patch.dict(sys.modules, dict(packages, **{
                'amr_resource.models.helper': helper,
                'amr_resource.models.trust_registry': module})):
            spec.loader.exec_module(module)
            algorithm_path = path.with_name('oidc_alogritma.py')
            algorithm_spec = importlib.util.spec_from_file_location('amr_resource.models.oidc_alogritma', algorithm_path)
            algorithm_module = importlib.util.module_from_spec(algorithm_spec)
            algorithm_spec.loader.exec_module(algorithm_module)
            module.OidcAlgorithm = algorithm_module.OidcAlgorithm
    return module


class TestChildGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_registry()

    def test_child_write_and_unlink_check_real_parent_guard(self):
        m = self.m
        class Parents(m.OidcResourceIssuer):
            def __init__(self, states):
                self.records = [types.SimpleNamespace(state=state, audience_ids=[1])
                                for state in states]
            def filtered(self, predicate):
                return [record for record in self.records if predicate(record)]
            def exists(self):
                return self

        base = m.OidcResourceIssuer.__mro__[1]
        for child_cls in (m.AmrResourceAudience, m.AmrResourceBinding,
                          m.AmrResourceUserMapping, m.OidcIssuerAlgorithmPolicy):
            for states in (('draft',), ('production',), ('disable',), ('draft', 'production')):
                for operation in ('write', 'unlink'):
                    with self.subTest(model=child_cls.__name__, states=states, operation=operation):
                        parents = Parents(states)
                        child = child_cls.__new__(child_cls)
                        child.mapped = lambda name: parents
                        child.env = {'oidc.issuer.register': parents}
                        calls = []
                        def orm(*args):
                            calls.append(args)
                            return True
                        with patch.object(base, operation, orm, create=True):
                            invoke = lambda: getattr(child, operation)(*([{'value': 'x'}] if operation == 'write' else []))
                            if states == ('draft',):
                                self.assertTrue(invoke())
                                self.assertEqual(len(calls), 1)
                            else:
                                with self.assertRaises(m.ValidationError):
                                    invoke()
                                self.assertEqual(calls, [])

    def test_immutable_snapshot_and_algorithm_catalog_guards(self):
        for method, args in ((self.m.OidcPolicySnapshot.write, ({},)),
                             (self.m.OidcPolicySnapshot.unlink, ()),
                             (self.m.OidcAlgorithm.write, ({},)),
                             (self.m.OidcAlgorithm.unlink, ())):
            with self.subTest(method=method.__name__), self.assertRaises(self.m.AccessError):
                method(object(), *args)
        create = self.m.OidcAlgorithm.create
        with self.assertRaises(self.m.AccessError):
            create(object(), [{'name': 'HS256'}])


if __name__ == '__main__':
    unittest.main()
