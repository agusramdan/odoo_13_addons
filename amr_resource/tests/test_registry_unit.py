"""Standalone registry units: python tests/test_registry_unit.py -v.

Requires cryptography and Werkzeug; only the Odoo boundary is stubbed.
These do NOT verify ORM SQL,
record-rule evaluation, XML installation, RPC dispatch, or rendered views.
"""
import ast
import csv
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from xml.etree import ElementTree
from werkzeug.exceptions import Unauthorized

ROOT = Path(__file__).resolve().parents[1]


class AccessError(Exception):
    pass


class ValidationError(Exception):
    pass


class BoundaryModel:
    """External ORM boundary, not a replacement security implementation."""
    def check_access_rights(self, operation, raise_exception=True):
        return True

    def check_access_rule(self, operation):
        return None

    def create(self, values):
        self.created_values = values
        return self

    def write(self, values):
        self.written_values = values
        for key, value in values.items():
            setattr(self, key, value)
        return True

    def unlink(self):
        self.deleted = True
        return True

    def name_get(self):
        return [(1, 'fixture')]


class FieldFactory:
    def __getattr__(self, name):
        return lambda *args, **kwargs: SimpleNamespace(args=args, **kwargs)


class DateTimeField:
    def __call__(self, *args, **kwargs):
        return SimpleNamespace(args=args, **kwargs)

    @staticmethod
    def now():
        return 'boundary-clock'


def load_registry():
    odoo = ModuleType('odoo')
    odoo.models = SimpleNamespace(Model=BoundaryModel, AbstractModel=BoundaryModel)
    odoo.fields = FieldFactory()
    odoo.fields.Datetime = DateTimeField()
    odoo.SUPERUSER_ID = 1
    odoo.api = SimpleNamespace(model=lambda method: method, model_create_multi=lambda method: method,
                               depends=lambda *args: lambda method: method, constrains=lambda *names: lambda method: method)
    errors = ModuleType('odoo.exceptions')
    errors.AccessError, errors.ValidationError = AccessError, ValidationError

    spec = importlib.util.spec_from_file_location('registry_unit_candidate', ROOT / 'models/trust_registry.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'odoo': odoo, 'odoo.exceptions': errors}):
        spec.loader.exec_module(module)
    return module


registry = load_registry()


class IssuerProbe(registry.AmrResourceIssuer, registry.RegistryAccess):
    def __init__(self, groups=(), share=False, su=False, **values):
        self.env = SimpleNamespace(user=SimpleNamespace(share=share, has_group=lambda name: name in groups),
                                   su=su, uid=27, company=SimpleNamespace(id=7), context={})
        self.ids = [19]
        self.code_revision = 0
        self.python_code = False
        self.company_id = self.env.company
        for key, value in values.items():
            setattr(self, key, value)

    def __iter__(self):
        return iter([self])


class ChildProbe(registry.RegistryAccess):
    _name = 'oidc.issuer.subject'

    def __init__(self, groups=(), share=False, su=False):
        self.env = IssuerProbe(groups, share, su).env
        self.company_id = self.env.company
        self.ids = [20]

    def __iter__(self):
        return iter([self])


ADMIN = 'base.group_system'
TRUST = registry.TRUST_GROUP
CODE = registry.CODE_GROUP


class RegistryUnitTests(unittest.TestCase):
    def profile(self, **values):
        row = SimpleNamespace(issuer='https://issuer.example', token_profile='jwt',
                              jwks_uri='https://keys.example/jwks', token_endpoint=False,
                              introspection_endpoint=False, client_id='resource-client', azp='resource-client',
                              allow_missing_azp=False, local_public_key=False, local_key_ref=False, credential_ref=False, audience_ids=[object()],
                              resolver_mode=False, fixed_user_id=False, company_id=7)
        row.__dict__.update(values)
        return row

    def check_profile(self, **values):
        registry.AmrResourceIssuer._check_profile([self.profile(**values)])

    def test_profile_valid_jwt_opaque_and_unselected_resolver(self):
        self.check_profile()
        self.check_profile(token_profile='opaque', jwks_uri=False,
                           introspection_endpoint='https://issuer.example/introspect')
        self.check_profile(allow_missing_azp=True, azp=False)

    def test_profile_rejects_bad_required_configuration(self):
        for values in ({'issuer': 'http://issuer.example'}, {'issuer': 'https://user@issuer.example'},
                       {'issuer': 'https://issuer.example/?query=1'}, {'issuer': 'https://issuer.example:bad'},
                       {'client_id': ''}, {'audience_ids': []}, {'azp': False}, {'azp': 'bad azp'},
                       {'jwks_uri': False}, {'token_profile': 'opaque'},
                       {'local_public_key': 'not a key'},
                       {'token_endpoint': 'http://issuer.example/token'}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                self.check_profile(**values)
        for field in ('local_key_ref', 'credential_ref'):
            with self.subTest(reference_field=field):
                with self.assertRaises(ValidationError):
                    self.check_profile(**{field: 'https://not-a-key.invalid'})

    def test_endpoint_syntax_policy_without_dns(self):
        self.assertTrue(registry._https_url('https://issuer.example:443/token'))
        self.assertTrue(registry._https_url('https://8.8.8.8/jwks'))
        for value in ('http://issuer.example', 'https://user:pass@issuer.example',
                      'https://issuer.example:444', 'https://issuer.example/#fragment',
                      'https://localhost/key', 'https://LOCALHOST./key', 'https://a.localhost/key',
                      'https://127.0.0.1/key', 'https://10.1.1.1/key', 'https://169.254.169.254/key',
                      'https://224.0.0.1/key', 'https://[::1]/key', 'https://[ff02::1]/key',
                      'https://issuer.example\\@other.example', 'https://issuer.example:bad',
                      '', None, 3):
            with self.subTest(value=value):
                self.assertFalse(registry._https_url(value))

    def test_local_public_key_must_be_rsa_public_pem(self):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa, ec
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        public = private.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        self.check_profile(jwks_uri=False, local_public_key=public)
        private_pem = private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                            serialization.NoEncryption()).decode('ascii')
        ec_key = ec.generate_private_key(ec.SECP256R1(), default_backend()).public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode('ascii')
        for key in (private_pem, ec_key, 'not PEM'):
            with self.subTest(key_type=key.splitlines()[0]), self.assertRaises(ValidationError):
                self.check_profile(jwks_uri=False, local_public_key=key)

    def lookup(self, records, issuer='https://issuer.example', profile='jwt', error=None):
        elevated = Mock()
        elevated.with_context.return_value = elevated
        elevated.search.side_effect = error
        elevated.search.return_value = records
        model = IssuerProbe()
        model.sudo = Mock(return_value=elevated)
        result = model._lookup(issuer, profile)
        model.sudo.assert_called_once_with()
        elevated.with_context.assert_called_once_with(active_test=False)
        elevated.search.assert_called_once_with([
            ('issuer', '=', issuer), ('active', '=', True)])
        return result

    def test_lookup_exact_global_active_unique_no_limit(self):
        class Result(list):
            token_profile = 'jwt'
        result = Result([object()])
        self.assertIs(self.lookup(result, issuer='https://Issuer.example/'), result)
        self.assertIs(self.lookup(result, profile=None), result)

    def test_lookup_unknown_duplicate_wrong_profile_and_errors_are_generic(self):
        class Result(list):
            token_profile = 'opaque'
        for result in ([], [object(), object()], Result([object()])):
            with self.subTest(count=len(result)), self.assertRaises(Unauthorized) as caught:
                self.lookup(result)
            self.assertEqual(caught.exception.description, Unauthorized.description)
        with self.assertRaises(Unauthorized) as caught:
            self.lookup([], error=RuntimeError('sensitive database detail'))
        self.assertEqual(caught.exception.description, Unauthorized.description)

    def test_lookup_malformed_input_rejected_before_sudo(self):
        model = IssuerProbe()
        model.sudo = Mock()
        for issuer, profile in ((None, None), ('', 'jwt'), ([], 'jwt'),
                                ('https://issuer.example\n', 'jwt'), ('https://issuer.example', 'id_token')):
            with self.subTest(issuer=issuer, profile=profile), self.assertRaises(Unauthorized):
                model._lookup(issuer, profile)
        model.sudo.assert_not_called()

    def test_role_guards_internal_manually_designated_admin_only(self):
        for groups, share in (((), False), ((ADMIN,), False), ((TRUST,), False),
                              ((CODE,), False), ((ADMIN, TRUST), True)):
            model = IssuerProbe(groups, share)
            for operation in ('read', 'write', 'create', 'unlink'):
                with self.subTest(groups=groups, share=share, operation=operation):
                    self.assertFalse(model.check_access_rights(operation, False))
                    with self.assertRaises(AccessError):
                        model.check_access_rights(operation)
            with self.assertRaises(AccessError):
                model.name_get()
        trust = IssuerProbe((ADMIN, TRUST))
        for operation in ('read', 'write', 'create', 'unlink'):
            self.assertTrue(trust.check_access_rights(operation))
        code = IssuerProbe((ADMIN, CODE))
        self.assertTrue(code.check_access_rights('read'))
        self.assertTrue(code.check_access_rights('write'))
        for operation in ('create', 'unlink'):
            with self.assertRaises(AccessError):
                code.check_access_rights(operation)
        child = ChildProbe((ADMIN, CODE))
        with self.assertRaises(AccessError):
            child.check_access_rights('read')

    def test_registry_access_is_not_company_scoped(self):
        model = IssuerProbe((ADMIN, TRUST))
        model.check_access_rule('read')
        model.company_id = SimpleNamespace(id=8)
        model.check_access_rule('read')
        self.assertFalse(hasattr(registry.AmrResourceIssuer, 'company_id'))
        self.assertFalse(hasattr(registry.AmrResourceAudience, 'company_id'))
        self.assertFalse(hasattr(registry.AmrResourceBinding, 'company_id'))
        elevated = IssuerProbe(su=True)
        self.assertTrue(elevated.check_access_rights('read'))
        elevated.company_id = SimpleNamespace(id=8)
        elevated.check_access_rule('read')

    def test_code_admin_only_source_and_audit_cannot_be_forged(self):
        code = IssuerProbe((ADMIN, CODE))
        code._guard_issuer_values({'python_code': 'source'})
        for values in ({'active': True}, {'issuer': 'https://other.example'},
                       {'python_code': 'source', 'client_id': 'changed'},
                       {'resolver_key': 'get_user_match'}, {'resolver_key': 'arbitrary'},
                       {'code_revision': 4}, {'code_actor_id': 1}, {'code_digest': 'forged'},
                       {'code_date': 'forged'}):
            with self.subTest(values=values), self.assertRaises(AccessError):
                code.write(values)
        trust = IssuerProbe((ADMIN, TRUST))
        with self.assertRaises(AccessError):
            trust.write({'python_code': 'source'})
        with self.assertRaises(AccessError):
            trust.create([{'python_code': 'source'}])
        trust._guard_issuer_values({'resolver_key': 'get_user_match'}, creating=True)

    def test_actual_write_generates_digest_actor_time_revision(self):
        model = IssuerProbe((ADMIN, CODE))
        source = "raise RuntimeError('must never execute')"
        self.assertTrue(model.write({'python_code': source}))
        self.assertEqual(model.code_revision, 1)
        self.assertEqual(model.code_digest, hashlib.sha256(source.encode('utf-8')).hexdigest())
        self.assertEqual(model.code_actor_id, 27)
        self.assertEqual(model.code_date, 'boundary-clock')
        self.assertEqual(model.python_code, source)
        model.write({'python_code': source})
        self.assertEqual(model.code_revision, 1)
        model.write({'python_code': False})
        self.assertEqual(model.code_revision, 2)
        self.assertEqual(model.code_digest, hashlib.sha256(b'').hexdigest())

    def test_actual_create_guards_and_audits(self):
        model = IssuerProbe((ADMIN, TRUST, CODE))
        model.create([{'issuer': 'https://issuer.example', 'python_code': 'stored only'}])
        values = model.created_values[0]
        self.assertEqual(values['code_revision'], 1)
        self.assertEqual(values['code_actor_id'], 27)
        self.assertEqual(values['code_digest'], hashlib.sha256(b'stored only').hexdigest())
        self.assertTrue(model.create([{'issuer': 'https://global.example'}]))

    def test_context_defaults_cannot_inject_source_or_audit(self):
        trust = IssuerProbe((ADMIN, TRUST))
        for name, value in (('python_code', 'injected'), ('code_revision', 12),
                            ('code_digest', 'forged'), ('resolver_key', 'arbitrary')):
            trust.env.context = {'default_' + name: value}
            with self.subTest(name=name), self.assertRaises(AccessError):
                trust.create([{'issuer': 'https://issuer.example'}])

    def test_audience_and_binding_validation(self):
        registry.AmrResourceAudience._check_value([SimpleNamespace(value='api://resource')])
        for value in ('', None, 'bad\nvalue'):
            with self.assertRaises(ValidationError):
                registry.AmrResourceAudience._check_value([SimpleNamespace(value=value)])
        class User(SimpleNamespace):
            def __len__(self):
                return 1
        user = User(id=29, active=True, share=False, company_ids=[7], has_group=lambda name: False)
        row = SimpleNamespace(sub='subject-001', user_id=user, company_id=7)
        registry.AmrResourceBinding._check_binding([row])
        self.check_profile(resolver_mode='fixed_user', fixed_user_id=user)
        for change in ({'active': False}, {'share': True}, {'id': 1},
                       {'has_group': lambda name: name == 'base.group_portal'},
                       {'has_group': lambda name: name == 'base.group_public'}):
            invalid = User(**dict(user.__dict__, **change))
            with self.subTest(change=list(change)), self.assertRaises(ValidationError):
                registry.AmrResourceBinding._check_binding([SimpleNamespace(sub='subject', user_id=invalid, company_id=7)])
            with self.assertRaises(ValidationError):
                self.check_profile(resolver_mode='fixed_user', fixed_user_id=invalid)

    def test_last_audience_cannot_be_removed_or_reparented(self):
        class Parents(list):
            def exists(self):
                return self

            def filtered(self, predicate):
                return Parents(row for row in self if predicate(row))

        class AudienceProbe(registry.AmrResourceAudience, registry.RegistryAccess):
            def __init__(self, parents):
                self.parents = parents
                self.env = MagicMock()
                self.env.su = True
                self.env.company = SimpleNamespace(id=7)
                self.ids = [20]
                target = MagicMock()
                target.__len__.return_value = 1
                target.company_id = self.env.company
                self.env.__getitem__.return_value.browse.return_value.exists.return_value = target

            def mapped(self, name):
                return self.parents

        for remaining in ([], [object()]):
            for operation in ('unlink', 'write'):
                model = AudienceProbe(Parents([SimpleNamespace(audience_ids=remaining)]))
                with self.subTest(remaining=bool(remaining), operation=operation):
                    if remaining:
                        result = model.unlink() if operation == 'unlink' else model.write({'issuer_id': 2})
                        self.assertTrue(result)
                    else:
                        with self.assertRaises(ValidationError):
                            model.unlink() if operation == 'unlink' else model.write({'issuer_id': 2})

    def test_declarations_constraints_no_default_mode_no_execution(self):
        self.assertEqual(registry.AmrResourceIssuer._sql_constraints[0][1], 'unique(issuer)')
        self.assertEqual(registry.AmrResourceAudience._sql_constraints[0][1], 'unique(issuer_id, value)')
        self.assertEqual(registry.AmrResourceBinding._sql_constraints[0][1], 'unique(issuer_id, sub)')
        mode = registry.AmrResourceIssuer.resolver_mode
        self.assertIn(('get_user_match', 'Default'), mode.args[0])
        self.assertFalse(hasattr(mode, 'default'))
        self.assertEqual(registry.AmrResourceIssuer.resolver_key.args[0], [('get_user_match', 'Default')])
        self.assertEqual(registry.AmrResourceIssuer.python_code.groups, CODE)
        self.assertEqual(registry.AmrResourceIssuer.local_public_key.groups, TRUST)
        self.assertEqual(registry.AmrResourceIssuer.credential_ref.groups, TRUST)
        tree = ast.parse((ROOT / 'models/trust_registry.py').read_text())
        names = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertFalse(names.intersection({'eval', 'exec', 'safe_eval', 'compile'}))
        sudo_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute) and node.func.attr == 'sudo']
        sudo_methods = sorted(n.name for n in ast.walk(tree)
                              if isinstance(n, ast.FunctionDef) and any(
                                  isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                                  and c.func.attr == 'sudo' for c in ast.walk(n)))
        self.assertEqual(sudo_methods, ['_compute_local_public_key', '_lookup', '_migrate_legacy_v2'])

    def test_security_and_ui_files_are_wired_and_restricted(self):
        manifest = ast.literal_eval((ROOT / '__manifest__.py').read_text())
        for filename in ('security/res_groups.xml', 'security/ir.model.access.csv',
                         'security/registry_rules.xml', 'views/trust_registry_views.xml'):
            self.assertIn(filename, manifest['data'])
        with (ROOT / 'security/ir.model.access.csv').open() as source:
            acls = list(csv.DictReader(source))
        self.assertEqual(len(acls), 4)
        self.assertEqual({row['group_id:id'] for row in acls}, {TRUST, CODE})
        code_acl = next(row for row in acls if row['group_id:id'] == CODE)
        self.assertEqual((code_acl['perm_create'], code_acl['perm_unlink']), ('0', '0'))
        groups = ElementTree.parse(str(ROOT / 'security/res_groups.xml'))
        for identifier in ('group_oidc_trust_admin', 'group_oidc_code_admin'):
            record = groups.find(".//record[@id='%s']" % identifier)
            self.assertIsNotNone(record)
            self.assertIsNone(record.find("field[@name='users']"))
            self.assertIsNone(record.find("field[@name='implied_ids']"))
        rules = ElementTree.parse(str(ROOT / 'security/registry_rules.xml'))
        self.assertEqual(rules.findall('.//record'), [])
        views = ElementTree.parse(str(ROOT / 'views/trust_registry_views.xml'))
        self.assertIsNone(views.find(".//field[@name='company_id']"))
        self.assertIsNotNone(views.find(".//field[@name='python_code']"))
        self.assertIsNotNone(views.find(".//field[@name='audience_ids']"))
        self.assertIsNotNone(views.find(".//field[@name='binding_ids']"))
        self.assertEqual(views.find(".//form[@string='Stored Source — Execution Disabled']").get('create'), 'false')


if __name__ == '__main__':
    unittest.main()
