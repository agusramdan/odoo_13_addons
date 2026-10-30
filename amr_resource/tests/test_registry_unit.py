"""Standalone registry units: python tests/test_registry_unit.py -v.

Requires cryptography and Werkzeug; only the Odoo boundary is stubbed.
These do NOT verify ORM SQL,
record-rule evaluation, XML installation, RPC dispatch, or rendered views.
"""
import ast
import csv
import hashlib
import importlib.util
import inspect
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


class FakeIssuerRecordset(list):
    def exists(self):
        return self

    def check_access_rights(self, operation, raise_exception=True):
        return True

    def check_access_rule(self, operation):
        return None

    def _lock_policy_state(self):
        for issuer in self:
            issuer._lock_policy_state()


class FakeIssuerModel:
    def __init__(self, issuers):
        self.issuers = {issuer.id: issuer for issuer in issuers}

    def browse(self, ids):
        if not isinstance(ids, (list, tuple, set)):
            ids = [ids] if ids else []
        return FakeIssuerRecordset(self.issuers[identifier]
                                   for identifier in ids if identifier in self.issuers)


class FakeChildEnvironment:
    def __init__(self, issuers, context=None):
        self.uid = 27
        self.su = True
        self.company = SimpleNamespace(id=7)
        self.user = SimpleNamespace(share=False, has_group=lambda group: True)
        self.context = context if context is not None else {}
        self._issuer_model = FakeIssuerModel(issuers)
        self.cr = SimpleNamespace(execute=lambda *args: None)

    def __getitem__(self, model):
        if model != 'oidc.issuer.register':
            raise KeyError(model)
        return self._issuer_model


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


class RevisionCursor:
    """Database-boundary stub: SQL increment changes the simulated row value."""
    def __init__(self, record):
        self.record = record
        self.sql = None
        self.params = None

    def execute(self, sql, params):
        self.sql, self.params = sql, params
        if 'policy_revision = policy_revision + 1' in sql:
            self.record.policy_revision += 1

    def fetchone(self):
        return (self.record.policy_revision,)


class IssuerProbe(registry.AmrResourceIssuer, registry.RegistryAccess):
    _table = 'oidc_issuer_register'

    def __init__(self, groups=(), share=False, su=False, **values):
        self.env = SimpleNamespace(user=SimpleNamespace(share=share, has_group=lambda name: name in groups),
                                   su=su, uid=27, company=SimpleNamespace(id=7), context={})
        self.ids = [19]
        self.id = 19
        self.code_revision = 0
        self.policy_revision = 1
        self.active = True
        self.mvp_enabled = False
        self.algorithm_policy_ids = []
        self.python_code = False
        self.company_id = self.env.company
        for key, value in values.items():
            setattr(self, key, value)
        self.env.cr = RevisionCursor(self)

    def ensure_one(self):
        return self

    def invalidate_cache(self, fnames=None, ids=None):
        self.cache_invalidated = (fnames, ids)

    def with_context(self, **values):
        self.env.context.update(values)
        return self

    def new(self, values):
        candidate = SimpleNamespace(**values)
        candidate._check_profile = Mock()
        return candidate

    def __iter__(self):
        return iter([self])


class ChildProbe(registry.RegistryAccess):
    _name = 'oidc.issuer.subject'

    def __init__(self, groups=(), share=False, su=False):
        self.env = IssuerProbe(groups, share, su).env
        self.company_id = self.env.company
        self.ids = [20]
        self.invalidate_cache = Mock()

    def __iter__(self):
        return iter([self])


ADMIN = 'base.group_system'
TRUST = registry.TRUST_GROUP
CODE = registry.CODE_GROUP


class RegistryUnitTests(unittest.TestCase):
    def test_oidc_issuer_algorithm_policy_declares_concrete_orm_inheritance(self):
        model = next(node for node in ast.walk(ast.parse(
            (ROOT / 'models/trust_registry.py').read_text()))
                     if isinstance(node, ast.ClassDef) and node.name == 'OidcIssuerAlgorithmPolicy')
        expected_base = ast.Attribute(
            value=ast.Name(id='models', ctx=ast.Load()),
            attr='Model', ctx=ast.Load())
        self.assertEqual(ast.dump(model.bases[0]), ast.dump(expected_base))
        declarations = {node.targets[0].id: ast.literal_eval(node.value)
                        for node in model.body if isinstance(node, ast.Assign)
                        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                        and node.targets[0].id in {'_name', '_inherit'}}
        self.assertEqual(declarations['_name'], 'oidc.issuer.algorithm.policy')
        self.assertEqual(declarations['_inherit'], 'amr.resource.registry.access')

    def test_user_mapping_declares_concrete_orm_inheritance(self):
        model = next(node for node in ast.walk(ast.parse(
            (ROOT / 'models/trust_registry.py').read_text()))
                     if isinstance(node, ast.ClassDef) and node.name == 'AmrResourceUserMapping')
        expected_base = ast.Attribute(
            value=ast.Name(id='models', ctx=ast.Load()),
            attr='Model', ctx=ast.Load())
        self.assertEqual(ast.dump(model.bases[0]), ast.dump(expected_base))
        declarations = {node.targets[0].id: ast.literal_eval(node.value)
                        for node in model.body if isinstance(node, ast.Assign)
                        and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                        and node.targets[0].id in {'_name', '_inherit', '_description', '_rec_name'}}
        self.assertEqual(declarations['_name'], 'oidc.issuer.user.mapping')
        self.assertEqual(declarations['_inherit'], 'amr.resource.registry.access')
        self.assertEqual(declarations['_description'], 'Issuer User Claim Mapping')
        self.assertEqual(declarations['_rec_name'], 'jwt_key')
    def test_child_write_rejects_parent_change_observed_after_child_lock(self):
        parent_a = IssuerProbe((ADMIN, TRUST))
        parent_b = IssuerProbe((ADMIN, TRUST))
        parent_a.id, parent_b.id = 2, 9
        child = ChildProbe((ADMIN, TRUST))
        child.env = FakeChildEnvironment([parent_a, parent_b])
        locked = []
        child._lock_policy_child_rows = lambda: locked.append(True)
        reads = [FakeIssuerRecordset([parent_a]), FakeIssuerRecordset([parent_b])]
        child.mapped = lambda name: reads.pop(0)
        with self.assertRaises(AccessError):
            child.write({'sub': 'must-not-change'})
        self.assertTrue(locked)
        self.assertFalse(hasattr(child, 'written_values'))
        self.assertEqual((parent_a.policy_revision, parent_b.policy_revision), (1, 1))

    def test_child_and_parent_read_rules_are_rechecked_after_locks_before_mutation(self):
        events = []
        parent = IssuerProbe((ADMIN, TRUST))
        parent._lock_policy_state = lambda: events.append('parent-lock')
        parent.check_access_rights = lambda operation: events.append('parent-rights')
        parent.check_access_rule = lambda operation: events.append('parent-rule')
        child = ChildProbe((ADMIN, TRUST))
        child.env = FakeChildEnvironment([parent])
        child.mapped = lambda name: FakeIssuerRecordset([parent])
        child._lock_policy_child_rows = lambda: events.append('child-lock')
        child.check_access_rights = lambda operation: events.append('child-rights')
        child.check_access_rule = lambda operation: events.append('child-rule')
        original_parent_guard = child._guard_parent_values

        def observed_parent_guard(values):
            if 'issuer_id' in values:
                events.append('parent-read-check')
            return original_parent_guard(values)

        child._guard_parent_values = observed_parent_guard
        original_write = BoundaryModel.write

        def observed_write(record, values):
            events.append('mutate')
            return original_write(record, values)

        with patch.object(BoundaryModel, 'write', observed_write):
            child.write({'sub': 'checked'})
        self.assertLess(events.index('child-lock'),
                        max(i for i, event in enumerate(events) if event == 'child-rights'))
        self.assertLess(max(i for i, event in enumerate(events) if event == 'child-rule'),
                        events.index('mutate'))
        parent_checks = [i for i, event in enumerate(events) if event == 'parent-read-check']
        self.assertGreaterEqual(len(parent_checks), 2)
        self.assertLess(parent_checks[0], events.index('parent-lock'))
        self.assertLess(events.index('parent-lock'), parent_checks[-1])
        self.assertLess(parent_checks[-1], events.index('mutate'))

    def test_atomic_policy_revision_uses_database_increment_and_refreshes_cache(self):
        class Cursor:
            def __init__(self):
                self.sql = None
                self.params = None
            def execute(self, sql, params):
                self.sql, self.params = sql, params
            def fetchone(self):
                return (12,)
        cursor = Cursor()
        issuer = IssuerProbe(policy_revision=11)
        issuer._table = 'oidc_issuer_register'
        issuer.env.cr = cursor
        issuer.invalidate_cache = Mock()
        self.assertEqual(issuer._issue_policy_revision(), 12)
        self.assertEqual(cursor.sql,
            'UPDATE oidc_issuer_register SET policy_revision = policy_revision + 1 WHERE id = %s RETURNING policy_revision')
        self.assertEqual(cursor.params, (19,))
        issuer.invalidate_cache.assert_called_once_with(fnames=['policy_revision'], ids=[19])

    def test_policy_state_lock_uses_parameterized_sorted_ids_and_invalidates_cache(self):
        class Cursor:
            def __init__(self):
                self.calls = []
            def execute(self, sql, params):
                self.calls.append((sql, params))
        issuer = IssuerProbe((ADMIN, TRUST))
        issuer.ids = [29, 19, 29]
        cursor = Cursor()
        issuer.env.cr = cursor
        issuer._table = 'untrusted_table_name'
        issuer.invalidate_cache = Mock()
        issuer._lock_policy_state()
        self.assertEqual(cursor.calls, [
            ('SELECT id FROM oidc_issuer_register WHERE id = %s FOR UPDATE', (19,)),
            ('SELECT id FROM oidc_issuer_register WHERE id = %s FOR UPDATE', (29,)),
        ])
        issuer.invalidate_cache.assert_called_once_with(ids=[19, 29])

    def test_policy_child_lock_uses_code_owned_table_sorted_unique_ids_and_invalidates_issuer_cache(self):
        class Cursor:
            def __init__(self):
                self.calls = []
            def execute(self, sql, params):
                self.calls.append((sql, params))

        child = ChildProbe((ADMIN, TRUST))
        child.ids = [29, 19, 29]
        child._table = 'untrusted_child_table'
        cursor = Cursor()
        child.env.cr = cursor
        child.invalidate_cache = Mock()
        child._lock_policy_child_rows()
        self.assertEqual(cursor.calls, [
            ('SELECT id FROM oidc_issuer_subject WHERE id IN %s ORDER BY id FOR UPDATE', ((19, 29),)),
        ])
        child.invalidate_cache.assert_called_once_with(ids=[19, 29])

    def test_policy_bump_routes_through_atomic_helper(self):
        issuer = IssuerProbe((ADMIN, TRUST))
        issuer._issue_policy_revision = Mock(return_value=2)
        issuer._bump_policy_revision()
        issuer._issue_policy_revision.assert_called_once_with()

    def test_server_owned_rollback_snapshot_model_and_actions_exist(self):
        self.assertTrue(hasattr(registry, 'OidcPolicySnapshot'))
        self.assertEqual(registry.OidcPolicySnapshot._name, 'oidc.issuer.policy.snapshot')
        self.assertTrue(registry.OidcPolicySnapshot._description)
        self.assertTrue(hasattr(registry.AmrResourceIssuer, 'action_capture_policy_snapshot'))
        self.assertTrue(hasattr(registry.AmrResourceIssuer, 'action_restore_policy_snapshot'))
        self.assertEqual(list(inspect.signature(
            registry.AmrResourceIssuer.action_restore_policy_snapshot).parameters),
            ['self', 'snapshot_id', 'expected_revision', 'evidence_ref'])
        for field in ('issuer_id', 'captured_revision', 'payload', 'integrity_digest',
                      'evidence_ref', 'actor_id', 'captured_at', 'invalidated'):
            self.assertTrue(hasattr(registry.OidcPolicySnapshot, field))
        for field in ('write', 'unlink'):
            self.assertTrue(callable(getattr(registry.OidcPolicySnapshot, field)))

    def test_snapshot_capture_is_admin_only_complete_and_excludes_identity_state(self):
        payload = {'issuer': 'https://issuer.example', 'verification_source': 'jwks',
                   'credential_ref': 'credential.key', 'mappings': [], 'audiences': ['api'],
                   'algorithms': []}

        class Environment(dict):
            uid = 27
            su = False
            company = SimpleNamespace(id=7)
            context = {}
            user = SimpleNamespace(share=False, has_group=lambda name: name in (ADMIN, TRUST))

        class SnapshotCreateProbe(registry.OidcPolicySnapshot):
            def __init__(self):
                self.env = Environment()
                self.id = 88

            def sudo(self):
                return self

        snapshot_model = SnapshotCreateProbe()
        env = Environment({'oidc.issuer.policy.snapshot': snapshot_model})
        issuer = IssuerProbe((ADMIN, TRUST), policy_revision=9, issuer='https://issuer.example')
        issuer.env = env
        issuer._check_profile = Mock()
        issuer._policy_snapshot_tuple = Mock(return_value=payload)
        with patch.object(registry._logger, 'info') as audit:
            self.assertEqual(issuer.action_capture_policy_snapshot('approval-42'), 88)
        created = snapshot_model.created_values
        self.assertEqual(created['issuer_id'], 19)
        self.assertEqual(created['captured_revision'], 9)
        self.assertEqual(created['evidence_ref'], 'approval-42')
        self.assertEqual(created['actor_id'], 27)
        self.assertNotIn('user_id', created['payload'])
        self.assertNotIn('company_id', created['payload'])
        self.assertNotIn('binding_ids', created['payload'])
        self.assertIn('Trust policy snapshot captured', repr(audit.call_args_list))
        self.assertIn('snapshot_capture', repr(audit.call_args_list))

        unauthorized = IssuerProbe(issuer='https://issuer.example')
        unauthorized._policy_snapshot_tuple = Mock(return_value=payload)
        with self.assertRaises(AccessError):
            unauthorized.action_capture_policy_snapshot('approval-42')
        snapshot_model = SnapshotCreateProbe()
        issuer.env['oidc.issuer.policy.snapshot'] = snapshot_model
        for evidence in (None, 'https://secret.invalid'):
            with self.subTest(evidence=evidence), self.assertRaises(ValidationError):
                issuer.action_capture_policy_snapshot(evidence)
        self.assertFalse(hasattr(snapshot_model, 'created_values'))

    def test_snapshot_capture_rejects_opaque_policy(self):
        issuer = IssuerProbe((ADMIN, TRUST), issuer='https://issuer.example')
        profile = self.profile(token_profile='opaque', jwks_uri=False)
        issuer._check_profile = lambda: registry.AmrResourceIssuer._check_profile([profile])
        with self.assertRaises(ValidationError):
            issuer.action_capture_policy_snapshot('approval-opaque')

    def test_snapshot_model_denies_direct_mutation_and_acl_is_read_only(self):
        self.assertEqual(registry.OidcPolicySnapshot._inherit, 'amr.resource.registry.access')
        row = registry.OidcPolicySnapshot()
        for operation, args in ((row.create, ([{}],)), (row.write, ({'payload': 'forged'},)),
                                (row.unlink, ())):
            with self.assertRaises(AccessError):
                operation(*args)
        with (ROOT / 'security/ir.model.access.csv').open() as source:
            acl = next(item for item in csv.DictReader(source)
                       if item['model_id:id'] == 'model_oidc_issuer_policy_snapshot')
        self.assertEqual((acl['perm_read'], acl['perm_write'], acl['perm_create'], acl['perm_unlink']),
                         ('1', '0', '0', '0'))

    def test_snapshot_restore_requires_exact_inactive_issuer_revision_and_integrity(self):
        import json
        from types import SimpleNamespace
        payload = {
            'issuer': 'https://issuer.example', 'token_profile': 'jwt',
            'jwks_uri': 'https://issuer.example/keys', 'token_endpoint': False,
            'introspection_endpoint': False, 'client_id': 'client', 'azp': 'client',
            'allow_missing_azp': False, 'credential_ref': 'generation.key',
            'local_key_ref': False, 'resolver_mode': 'mapping', 'mvp_enabled': True,
            'metadata_mode': 'manual',
            'verification_source': 'jwks', 'introspection_source': 'none',
            'no_jwks_declaration': False, 'no_jwks_evidence_ref': False,
            'introspection_credential_ref': False, 'introspection_auth_client_id': False,
            'introspection_auth_method': False, 'introspection_basic_contract_ref': False,
            'introspection_credential_endpoint': False, 'allow_jwt_introspection': False,
            'allow_introspection_iss_absent': False, 'audiences': ['api'],
            'mappings': [{'sequence': 10, 'active': True, 'field_user': 'login', 'jwt_key': 'sub'}],
            'algorithms': [{'name': 'RS256', 'enabled': True}],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(encoded.encode('utf-8')).hexdigest()

        class Environment(dict):
            uid = 27
            su = False
            company = SimpleNamespace(id=7)
            context = {}
            user = SimpleNamespace(share=False, has_group=lambda name: name in (ADMIN, TRUST))

        class SnapshotRecord:
            id = 88
            issuer_id = SimpleNamespace(id=19)
            captured_revision = 9
            invalidated = False
            payload = encoded
            integrity_digest = digest

            def __len__(self):
                return 1

        class SnapshotModel:
            def sudo(self):
                return self

            def browse(self, identifier):
                self.identifier = identifier
                return self

            def exists(self):
                return SnapshotRecord()

        class AlgorithmModel:
            def search(self, domain, limit=None):
                self.domain = domain
                self.limit = limit
                class Algorithm(list):
                    id = 33
                return Algorithm([object()])

        snapshot_model = SnapshotModel()
        algorithms = AlgorithmModel()
        env = Environment({'oidc.issuer.policy.snapshot': snapshot_model, 'oidc.algorithm': algorithms})
        issuer = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=False,
                             policy_revision=12, issuer='https://issuer.example')
        issuer.env = env
        issuer.env.cr = RevisionCursor(issuer)
        issuer._policy_snapshot_tuple = Mock(return_value=payload)
        issuer.audience_ids = [SimpleNamespace(id=10, value='old-api')]
        with patch.object(registry._logger, 'info') as audit:
            self.assertTrue(issuer.action_restore_policy_snapshot(88, 12, 'approval-43'))
        self.assertEqual(issuer.policy_revision, 13)
        self.assertFalse(issuer.written_values['active'])
        self.assertEqual(issuer.written_values['credential_ref'], 'generation.key')
        self.assertEqual(issuer.written_values['audience_ids'][0], (1, 10, {'value': 'api'}))
        self.assertFalse(any(command[0] == 5 for command in issuer.written_values['audience_ids']))
        self.assertEqual(issuer.written_values['user_mapping_ids'][1][2]['jwt_key'], 'sub')
        self.assertNotIn('user_id', issuer.written_values)
        self.assertNotIn('company_id', issuer.written_values)
        self.assertEqual(snapshot_model.identifier, 88)
        self.assertIn('Trust policy snapshot restored', repr(audit.call_args_list))
        self.assertIn('snapshot_restore', repr(audit.call_args_list))

        unauthorized = IssuerProbe(active=False, policy_revision=12, issuer='https://issuer.example')
        with self.assertRaises(AccessError):
            unauthorized.action_restore_policy_snapshot(88, 12, 'approval-43')
        self.assertFalse(hasattr(unauthorized, 'written_values'))

        incomplete = json.dumps({key: value for key, value in payload.items()
                                 if key != 'algorithms'}, sort_keys=True, separators=(',', ':'))
        legacy_payload = json.loads(encoded)
        legacy_payload.update(discovery_unavailable_declared=False,
                              discovery_unavailable_evidence_ref='')
        legacy_encoded = json.dumps(legacy_payload, sort_keys=True, separators=(',', ':'))
        cases = (
            (False, 12, 11, encoded, digest, 19, False),
            (True, 12, 12, encoded, digest, 19, False),
            (False, 12, 12, encoded.replace('api', 'evil'), digest, 19, False),
            (False, 12, 12, encoded, digest, 20, False),
            (False, 12, 12, encoded, digest, 19, True),
            (False, 12, 12, incomplete,
             hashlib.sha256(incomplete.encode('utf-8')).hexdigest(), 19, False),
            (False, 12, 12, legacy_encoded,
             hashlib.sha256(legacy_encoded.encode('utf-8')).hexdigest(), 19, False),
        )
        for active, current_revision, expected_revision, changed_payload, changed_digest, \
                issuer_id, invalidated in cases:
            row = IssuerProbe((ADMIN, TRUST), active=active, mvp_enabled=False,
                              policy_revision=current_revision, issuer='https://issuer.example')
            row.env = env
            row._policy_snapshot_tuple = Mock(return_value=payload)
            original_exists = snapshot_model.exists
            def changed_snapshot():
                class ChangedSnapshot:
                    id = 88
                    captured_revision = 9
                    payload = changed_payload
                    integrity_digest = changed_digest

                    def __len__(self):
                        return 1
                snapshot = ChangedSnapshot()
                snapshot.issuer_id = SimpleNamespace(id=issuer_id)
                snapshot.invalidated = invalidated
                return snapshot
            snapshot_model.exists = changed_snapshot
            try:
                with self.subTest(active=active, expected_revision=expected_revision), self.assertRaises(ValidationError):
                    row.action_restore_policy_snapshot(88, expected_revision, 'approval-43')
                self.assertFalse(hasattr(row, 'written_values'))
            finally:
                snapshot_model.exists = original_exists

        payload['token_profile'] = 'opaque'
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        invalid_profile = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=False,
                                      policy_revision=12, issuer='https://issuer.example')
        invalid_profile.env = env
        invalid_profile._policy_snapshot_tuple = Mock(return_value=payload)
        candidate = SimpleNamespace()
        candidate._check_profile = lambda mvp_enabled=None: registry.AmrResourceIssuer._check_profile(
            [self.profile(token_profile='opaque', jwks_uri=False)], mvp_enabled)
        invalid_profile.new = Mock(return_value=candidate)
        with self.assertRaises(ValidationError):
            invalid_profile.action_restore_policy_snapshot(88, 12, 'approval-43')
        self.assertFalse(hasattr(invalid_profile, 'written_values'))

        for snapshot_id, revision, evidence in ((True, 12, 'approval-43'),
                                                 (88, True, 'approval-43'),
                                                 (88, 12, 'https://untrusted.invalid')):
            invalid_input = IssuerProbe((ADMIN, TRUST), active=False, policy_revision=12,
                                        issuer='https://issuer.example')
            with self.subTest(snapshot_id=snapshot_id, revision=revision), self.assertRaises(ValidationError):
                invalid_input.action_restore_policy_snapshot(snapshot_id, revision, evidence)
            self.assertFalse(hasattr(invalid_input, 'written_values'))

    def test_persistent_algorithm_catalog_and_issuer_policy_models_are_declared(self):
        catalog = registry.OidcAlgorithm
        policy = registry.OidcIssuerAlgorithmPolicy
        self.assertEqual(catalog._name, 'oidc.algorithm')
        self.assertEqual(policy._name, 'oidc.issuer.algorithm.policy')
        self.assertTrue(catalog._description)
        self.assertTrue(policy._description)
        self.assertTrue(hasattr(catalog, 'name'))
        for field in ('issuer_id', 'algorithm_id', 'enabled'):
            self.assertTrue(hasattr(policy, field), field)
        self.assertIn('unique(issuer_id, algorithm_id)', policy._sql_constraints[0][1])

        catalog = registry._ALGORITHM_CATALOG
        self.assertEqual(set(catalog), {'RS256'})
        self.assertEqual(catalog['RS256'], {'key_family': 'RSA', 'min_key_bits': 2048,
                                             'purpose': 'access_token_verification',
                                             'support_state': 'supported'})
        for enabled, supported in (([], ['RS256']), (['HS256'], ['RS256']),
                                   (['PS256'], ['RS256'])):
            with self.assertRaises(ValidationError):
                registry._effective_algorithms(enabled, supported)

    def test_issuer_policy_rejects_ps256_even_when_disabled(self):
        unsupported = SimpleNamespace(enabled=False, algorithm_id=SimpleNamespace(
            name='PS256', support_state='target'))
        with self.assertRaises(ValidationError):
            registry.OidcIssuerAlgorithmPolicy._check_supported_policy([unsupported])

    def test_policy_selection_intersects_code_support_enabled_policy_and_key(self):
        policy = [('RS256', True)]
        self.assertEqual(registry._policy_algorithms(policy, {'alg': 'RS256'}),
                         frozenset(['RS256']))
        self.assertEqual(registry._policy_algorithms(policy, {}), frozenset(['RS256']))
        for row in (('PS256', True), ('PS256', False)):
            with self.subTest(row=row), self.assertRaises(ValidationError):
                registry._policy_algorithms([row], {'alg': 'PS256'})
        with self.assertRaises(ValidationError):
            registry._policy_algorithms([('RS256', False)], {'alg': 'RS256'})
        with self.assertRaises(ValidationError):
            registry._policy_algorithms([('HS256', True)], {'alg': 'HS256'})

    def profile(self, **values):
        row = SimpleNamespace(issuer='https://issuer.example', token_profile='jwt',
                              jwks_uri='https://keys.example/jwks', token_endpoint=False,
                              introspection_endpoint=False, client_id='resource-client', azp='resource-client',
                              allow_missing_azp=False, local_public_key=False, local_key_ref=False, credential_ref=False, audience_ids=[object()],
                              resolver_mode=False, fixed_user_id=False, user_mapping_ids=[],
                              mvp_enabled=False, metadata_mode='manual',
                              discovery_unavailable_declared=False,
                              discovery_unavailable_evidence_ref=False,
                              verification_source='jwks', introspection_source='none',
                              no_jwks_declaration=False, no_jwks_evidence_ref=False,
                              introspection_credential_ref=False, introspection_auth_client_id=False,
                              introspection_auth_method=False, introspection_basic_contract_ref=False,
                              introspection_credential_endpoint=False, allow_jwt_introspection=False,
                              allow_introspection_iss_absent=False, company_id=7)
        row.__dict__.update(values)
        return row

    def check_profile(self, **values):
        registry.AmrResourceIssuer._check_profile([self.profile(**values)])

    def test_mapping_resolver_is_first_unique_and_rejects_ambiguity(self):
        rows = [
            {'sequence': 20, 'field_user': 'partner_id.email', 'jwt_key': 'email'},
            {'sequence': 10, 'field_user': 'login', 'jwt_key': 'preferred_username'},
        ]
        calls = []
        def lookup(field, value):
            calls.append((field, value))
            return [] if value == 'no-match' else [7]
        self.assertEqual(registry._mapping_candidate(rows, {
            'email': 'not-evaluated@example.invalid', 'preferred_username': 'user7'}, lookup), 7)
        self.assertEqual(calls, [('login', 'user7')])
        with self.assertRaises(ValidationError):
            registry._mapping_candidate(rows, {'preferred_username': 'ambiguous', 'email': 'later'},
                                        lambda field, value: [7, 8] if value == 'ambiguous' else [7])

    def test_mapping_configuration_bounds_and_sequence_validation(self):
        rows = [{'sequence': index + 1, 'field_user': 'login', 'jwt_key': 'sub', 'active': True}
                for index in range(20)]
        self.assertTrue(registry._validate_mapping_rows(rows))
        self.assertTrue(registry._validate_mapping_rows(
            rows + [dict(rows[-1], sequence=21, active=False)]))
        with self.assertRaises(ValidationError):
            registry._validate_mapping_rows(rows + [dict(rows[-1], sequence=21)])
        with self.assertRaises(ValidationError):
            registry._validate_mapping_rows(rows + [dict(rows[-1], sequence=1, active=False)])
        with self.assertRaises(ValidationError):
            registry._validate_mapping_rows([dict(rows[0], sequence=True)])

    def test_profile_valid_jwt_and_rejects_opaque_and_unselected_resolver(self):
        self.assertEqual(registry._validate_mapping_claim('claim', '  exact  '), '  exact  ')
        for value in ('', ' ', chr(0), chr(127), chr(128), 'x' * 1025, 12, True):
            with self.subTest(value_type=type(value).__name__, value_length=len(value) if isinstance(value, str) else None):
                with self.assertRaises(ValidationError):
                    registry._validate_mapping_claim('claim', value)
        for key in ('a.b', '$.sub', '__class__', '1claim', 'x' * 65):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                registry._validate_mapping_claim(key, 'valid')
        self.check_profile()
        with self.assertRaises(ValidationError):
            self.check_profile(mvp_enabled=False, token_profile='opaque', jwks_uri=False,
                               introspection_endpoint='https://issuer.example/introspect')
        self.check_profile(allow_missing_azp=True, azp=False)
        with self.assertRaises(ValidationError):
            self.check_profile(mvp_enabled=False, metadata_mode='oidc_discovery',
                               verification_source='jwks', jwks_uri=False,
                               introspection_source='none')

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

    def test_create_rejects_discovery_unavailable_context_defaults_even_if_false_or_empty(self):
        for field, value in (('discovery_unavailable_declared', False),
                             ('discovery_unavailable_evidence_ref', '')):
            candidate = IssuerProbe((ADMIN, TRUST))
            candidate.env.context = {'default_' + field: value}
            with self.subTest(field=field), self.assertRaises(ValidationError):
                candidate.create([{'issuer': 'https://issuer.example'}])
            self.assertFalse(hasattr(candidate, 'created_values'))

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

    def test_explicit_mvp_deactivation_is_admin_only_audited_and_fail_closed(self):
        admin = IssuerProbe((ADMIN, TRUST), mvp_enabled=True,
                            verification_source='jwks', policy_revision=7)
        admin.action_deactivate_mvp('operator_disabled')
        self.assertFalse(admin.active)
        self.assertEqual(admin.policy_revision, 8)
        self.assertEqual(admin.written_values, {'active': False})

        unauthorized = IssuerProbe(mvp_enabled=True, verification_source='jwks')
        with self.assertRaises(AccessError):
            unauthorized.action_deactivate_mvp('operator_disabled')
        self.assertTrue(unauthorized.active)
        self.assertEqual(unauthorized.policy_revision, 1)

        for reason in ('', 'free form reason', 'https://secret.example', 'x' * 65, 'café'):
            row = IssuerProbe((ADMIN, TRUST), mvp_enabled=True,
                              verification_source='jwks')
            with self.subTest(reason=reason), self.assertRaises(ValidationError):
                row.action_deactivate_mvp(reason)
            self.assertTrue(row.active)
            self.assertEqual(row.policy_revision, 1)

        repeated = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=True,
                               verification_source='jwks')
        with self.assertRaises(ValidationError):
            repeated.action_deactivate_mvp('operator_disabled')
        wrong_mode = IssuerProbe((ADMIN, TRUST), mvp_enabled=False,
                                 verification_source='jwks')
        with self.assertRaises(ValidationError):
            wrong_mode.action_deactivate_mvp('operator_disabled')

    def test_explicit_mvp_activation_is_admin_only_validated_and_audited(self):
        unsupported = IssuerProbe((ADMIN, TRUST), mvp_enabled=False, token_profile='jwt',
                                  verification_source='jwks')
        unsupported._check_profile = Mock()
        with self.assertRaises(ValidationError):
            unsupported.action_activate_mvp('approved_profile')
        self.assertFalse(unsupported.mvp_enabled)

        admin = IssuerProbe((ADMIN, TRUST), mvp_enabled=False,
                            verification_source='jwks', policy_revision=7,
                            algorithm_policy_ids=[SimpleNamespace(
                                algorithm_id=SimpleNamespace(name='RS256'), enabled=True)])
        admin._check_profile = Mock()
        with patch.object(registry._logger, 'info') as audit:
            admin.action_activate_mvp('approved_profile')
        admin._check_profile.assert_called_once_with(mvp_enabled=True)
        self.assertTrue(admin.mvp_enabled)
        self.assertEqual(admin.policy_revision, 8)
        self.assertEqual(admin.written_values, {'mvp_enabled': True})
        activation_audit = [call for call in audit.call_args_list
                            if 'Trust issuer activated' in call[0][0]]
        self.assertEqual(len(activation_audit), 1)
        self.assertIn('approved_profile', repr(activation_audit[0]))

        denied = IssuerProbe(mvp_enabled=False)
        with self.assertRaises(AccessError):
            denied.action_activate_mvp('approved_profile')
        self.assertFalse(denied.mvp_enabled)
        self.assertEqual(denied.policy_revision, 1)

        incomplete = IssuerProbe((ADMIN, TRUST), mvp_enabled=False,
                                 verification_source='jwks', policy_revision=4)
        incomplete._check_profile = Mock(side_effect=ValidationError('invalid profile'))
        with self.assertRaises(ValidationError):
            incomplete.action_activate_mvp('approved_profile')
        self.assertFalse(incomplete.mvp_enabled)
        self.assertEqual(incomplete.policy_revision, 4)

        for reason in ('', 'free form', 'https://private.invalid', 'x' * 65):
            candidate = IssuerProbe((ADMIN, TRUST), mvp_enabled=False,
                                    verification_source='jwks')
            with self.subTest(reason=reason), self.assertRaises(ValidationError):
                candidate.action_activate_mvp(reason)
            self.assertFalse(candidate.mvp_enabled)

        candidate = IssuerProbe((ADMIN, TRUST), mvp_enabled=False)
        with self.assertRaises(AccessError):
            candidate.write({'mvp_enabled': True})
        self.assertFalse(candidate.mvp_enabled)
        candidate = IssuerProbe((ADMIN, TRUST))
        with self.assertRaises(AccessError):
            candidate.create([{'issuer': 'https://issuer.example', 'mvp_enabled': True}])
        candidate.env.context = {'default_mvp_enabled': True}
        with self.assertRaises(AccessError):
            candidate.create([{'issuer': 'https://issuer.example'}])

    def test_trust_actions_repeat_access_checks_after_policy_lock(self):
        for action_name in ('action_activate_mvp', 'action_deactivate_mvp'):
            events = []
            values = {'mvp_enabled': action_name == 'action_deactivate_mvp',
                      'verification_source': 'jwks'}
            record = IssuerProbe((ADMIN, TRUST), **values)
            record.check_access_rights = lambda operation: events.append(('access', operation))
            record.check_access_rule = lambda operation: events.append(('rule', operation))
            record._lock_policy_state = lambda: events.append(('lock',))
            record._check_profile = Mock()
            record._verification_algorithms = Mock(return_value=frozenset(['RS256']))
            record._issue_policy_revision = Mock(return_value=2)
            original_getattribute = IssuerProbe.__getattribute__

            def tracked_getattribute(record, name):
                if name in ('active', 'mvp_enabled', 'verification_source', 'policy_revision'):
                    events.append(('read', name))
                return original_getattribute(record, name)

            with patch.object(IssuerProbe, '__getattribute__', tracked_getattribute):
                getattr(record, action_name)('approved-change')
            with self.subTest(action=action_name):
                lock_index = events.index(('lock',))
                self.assertEqual(events[lock_index + 1:lock_index + 3],
                                 [('access', 'write'), ('rule', 'write')])

    def test_mvp_active_flag_rejects_non_boolean_generic_writes(self):
        active = IssuerProbe((ADMIN, TRUST), active=True, mvp_enabled=True,
                             verification_source='jwks', policy_revision=6)
        for values in ({'active': False}, {'mvp_enabled': False}):
            with self.subTest(values=values), self.assertRaises(AccessError):
                active.write(values)
        self.assertTrue(active.active)
        self.assertTrue(active.mvp_enabled)

        inactive = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=True,
                               verification_source='jwks', policy_revision=6)
        for value in (1, 0, 'true', None):
            with self.subTest(value=value), self.assertRaises(AccessError):
                inactive.write({'active': value})
            self.assertFalse(inactive.active)
            self.assertEqual(inactive.policy_revision, 6)

        legacy = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=False)
        self.assertTrue(legacy.write({'active': 1}))
        self.assertEqual(legacy.active, 1)
        self.assertEqual(legacy.policy_revision, 2)

    def test_mvp_activation_bypasses_reject_malformed_defaults_and_require_action(self):
        for value in (1, 0, 'yes', None):
            candidate = IssuerProbe((ADMIN, TRUST), mvp_enabled=False)
            with self.subTest(value=value), self.assertRaises(AccessError):
                candidate.write({'mvp_enabled': value})
            self.assertFalse(candidate.mvp_enabled)
            self.assertEqual(candidate.policy_revision, 1)

            candidate = IssuerProbe((ADMIN, TRUST), mvp_enabled=False)
            with self.subTest(create_value=value), self.assertRaises(AccessError):
                candidate.create([{'issuer': 'https://issuer.example', 'mvp_enabled': value}])
            self.assertFalse(hasattr(candidate, 'created_values'))

            candidate = IssuerProbe((ADMIN, TRUST), mvp_enabled=False)
            candidate.env.context = {'default_mvp_enabled': value}
            with self.subTest(context_value=value), self.assertRaises(AccessError):
                candidate.create([{'issuer': 'https://issuer.example'}])
            self.assertFalse(hasattr(candidate, 'created_values'))
            self.assertEqual(candidate.policy_revision, 1)

        inactive = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=True,
                               verification_source='jwks')
        with self.assertRaises(AccessError):
            inactive.write({'active': True})
        self.assertFalse(inactive.active)
        self.assertEqual(inactive.policy_revision, 1)

        reactivated = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=True,
                                  verification_source='jwks', policy_revision=9)
        reactivated._check_profile = Mock()
        with patch.object(registry._logger, 'info') as audit:
            reactivated.action_activate_mvp('approved_profile')
        reactivated._check_profile.assert_called_once_with(mvp_enabled=True)
        self.assertTrue(reactivated.active)
        self.assertTrue(reactivated.mvp_enabled)
        self.assertEqual(reactivated.policy_revision, 10)
        self.assertEqual(reactivated.written_values, {'active': True})
        self.assertIn('activate_mvp', repr(audit.call_args_list))

        repeated = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=True,
                               verification_source='jwks', policy_revision=9)
        with self.assertRaises(ValidationError):
            repeated.action_activate_mvp('approved_profile')
        self.assertFalse(repeated.active)
        self.assertTrue(repeated.mvp_enabled)
        self.assertEqual(repeated.policy_revision, 9)

        invalid = IssuerProbe((ADMIN, TRUST), active=False, mvp_enabled=True,
                              verification_source='jwks', policy_revision=9)
        invalid._check_profile = Mock(side_effect=ValidationError('invalid profile'))
        with self.assertRaises(ValidationError):
            invalid.action_activate_mvp('approved_profile')
        self.assertFalse(invalid.active)
        self.assertTrue(invalid.mvp_enabled)
        self.assertEqual(invalid.policy_revision, 9)

    def test_policy_revision_is_monotonic_and_not_admin_writable(self):
        self.assertTrue(hasattr(registry.AmrResourceIssuer, 'policy_revision'))
        trust = IssuerProbe((ADMIN, TRUST), policy_revision=7, client_id='before')
        self.assertTrue(trust.write({'client_id': 'after'}))
        self.assertEqual(trust.policy_revision, 8)
        self.assertTrue(trust.write({'active': False}))
        self.assertEqual(trust.policy_revision, 9)
        self.assertFalse(trust.active)
        with self.assertRaises(AccessError):
            trust.write({'policy_revision': 100})
        self.assertEqual(trust.policy_revision, 9)

    def test_child_policy_mutations_advance_parent_revision(self):
        child = ChildProbe((ADMIN, TRUST))
        parent = IssuerProbe((ADMIN, TRUST), policy_revision=7)
        child.env = FakeChildEnvironment([parent])
        child.mapped = lambda name: [parent]
        self.assertTrue(child.write({'sub': 'changed-subject'}))
        self.assertEqual(parent.policy_revision, 8)
        self.assertTrue(child.unlink())
        self.assertEqual(parent.policy_revision, 9)

    def test_child_write_and_unlink_suppress_revision_only_during_restore(self):
        old_parent = IssuerProbe((ADMIN, TRUST), policy_revision=7)
        new_parent = IssuerProbe((ADMIN, TRUST), policy_revision=20)
        new_parent.id = 30
        child = ChildProbe((ADMIN, TRUST))
        child.issuer_id = old_parent
        child.mapped = lambda name: [new_parent if child.issuer_id == new_parent.id
                                     else child.issuer_id]

        child.env = FakeChildEnvironment([old_parent, new_parent])
        child.env.context['_policy_restore_token'] = registry._RESTORE_CONTEXT_TOKEN
        self.assertTrue(child.write({'sub': 'restored'}))
        self.assertEqual((old_parent.policy_revision, new_parent.policy_revision), (7, 20))
        self.assertTrue(child.unlink())
        self.assertEqual((old_parent.policy_revision, new_parent.policy_revision), (7, 20))

        child.env.context.clear()
        child.issuer_id = old_parent
        self.assertTrue(child.write({'issuer_id': new_parent.id, 'sub': 'reparented'}))
        self.assertEqual((old_parent.policy_revision, new_parent.policy_revision), (8, 21))

    def test_child_mutations_dedupe_duplicate_mapped_parents(self):
        events = []
        parent2 = IssuerProbe((ADMIN, TRUST))
        parent9 = IssuerProbe((ADMIN, TRUST))
        parent2.id, parent9.id = 2, 9
        for parent in (parent2, parent9):
            parent._lock_policy_state = lambda parent=parent: events.append(('lock', parent.id))
            parent._bump_policy_revision = lambda parent=parent: events.append(('bump', parent.id))
        child = ChildProbe((ADMIN, TRUST))
        child.env = FakeChildEnvironment([parent2, parent9])
        child.mapped = lambda name: FakeIssuerRecordset([parent9, parent2, parent9])

        original_create = BoundaryModel.create
        def observed_create(record, values):
            events.append(('mutate', 'create'))
            return original_create(record, values)
        with patch.object(BoundaryModel, 'create', observed_create):
            self.assertTrue(child.create([
                {'issuer_id': 9, 'sub': 'created-a'},
                {'issuer_id': 2, 'sub': 'created-b'},
                {'issuer_id': 9, 'sub': 'created-c'},
            ]))
        self.assertEqual(events, [('lock', 2), ('lock', 9), ('mutate', 'create'),
                                  ('bump', 2), ('bump', 9)])

        events[:] = []
        original_unlink = BoundaryModel.unlink
        def observed_unlink(record):
            events.append(('mutate', 'unlink'))
            return original_unlink(record)
        with patch.object(BoundaryModel, 'unlink', observed_unlink):
            self.assertTrue(child.unlink())
        self.assertEqual(events, [('lock', 2), ('lock', 9), ('mutate', 'unlink'),
                                  ('bump', 2), ('bump', 9)])

    def test_child_reparent_locks_old_and_new_before_mutation(self):
        events = []
        old_parent = IssuerProbe((ADMIN, TRUST))
        new_parent = IssuerProbe((ADMIN, TRUST))
        old_parent.id, new_parent.id = 2, 9
        for parent in (old_parent, new_parent):
            parent._lock_policy_state = lambda parent=parent: events.append(('lock', parent.id))
            parent._bump_policy_revision = lambda parent=parent: events.append(('bump', parent.id))
        child = ChildProbe((ADMIN, TRUST))
        child.env = FakeChildEnvironment([old_parent, new_parent])
        child.issuer_id = old_parent
        child.mapped = lambda name: FakeIssuerRecordset([old_parent, old_parent])

        original_write = BoundaryModel.write
        def observed_write(record, values):
            events.append(('mutate', 'write'))
            return original_write(record, values)
        with patch.object(BoundaryModel, 'write', observed_write):
            self.assertTrue(child.write({'issuer_id': new_parent.id}))
        self.assertEqual(events, [('lock', 2), ('lock', 9), ('mutate', 'write'),
                                  ('bump', 2), ('bump', 9)])

    def test_issuer_write_checks_and_locks_before_reading_state_values(self):
        events = []
        issuer = IssuerProbe((ADMIN, TRUST), active=True, python_code=False)
        issuer.check_access_rights = lambda operation: events.append(('access', operation))
        issuer.check_access_rule = lambda operation: events.append(('rule', operation))
        issuer._lock_policy_state = lambda: events.append(('lock',))
        issuer._guard_issuer_values = lambda values: events.append(('guard',))

        original_getattribute = IssuerProbe.__getattribute__

        def tracked_getattribute(record, name):
            if name in ('active', 'python_code'):
                events.append(('read', name))
            return original_getattribute(record, name)

        with patch.object(IssuerProbe, '__getattribute__', tracked_getattribute):
            issuer.write({'client_id': 'changed'})
        self.assertEqual(events[:6], [('access', 'write'), ('rule', 'write'),
                                      ('lock',), ('access', 'write'),
                                      ('rule', 'write'), ('guard',)])
        reads = [event for event in events if event[0] == 'read']
        self.assertTrue(reads)
        self.assertTrue(all(events.index(('guard',)) < events.index(event) for event in reads))

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
                self.invalidate_cache = Mock()
                target = MagicMock()
                target.__len__.return_value = 1
                target.company_id = self.env.company
                self.env.__getitem__.return_value.browse.return_value.exists.return_value = target

            def mapped(self, name):
                return self.parents

        for remaining in ([], [object()]):
            for operation in ('unlink', 'write'):
                model = AudienceProbe(Parents([SimpleNamespace(id=10, audience_ids=remaining)]))
                with self.subTest(remaining=bool(remaining), operation=operation):
                    if remaining:
                        result = model.unlink() if operation == 'unlink' else model.write({'issuer_id': 2})
                        self.assertTrue(result)
                    else:
                        with self.assertRaises(ValidationError):
                            model.unlink() if operation == 'unlink' else model.write({'issuer_id': 2})

    def test_manual_mvp_jwks_accepts_profile_without_discovery_fields(self):
        profile = self.profile(mvp_enabled=True, metadata_mode='manual', verification_source='jwks',
                               introspection_source='none')
        del profile.discovery_unavailable_declared
        del profile.discovery_unavailable_evidence_ref
        registry.AmrResourceIssuer._check_profile([profile])

    def test_discovery_unavailable_fields_are_rejected_on_create_and_write_even_empty(self):
        issuer = registry.AmrResourceIssuer()
        issuer.env = SimpleNamespace(context={}, su=True)
        for field, value in (('discovery_unavailable_declared', False),
                             ('discovery_unavailable_evidence_ref', '')):
            with self.subTest(field=field), self.assertRaises((AccessError, ValidationError)):
                issuer._guard_issuer_values({field: value}, creating=True)
            with self.subTest(field=field, write=True), self.assertRaises((AccessError, ValidationError)):
                issuer._guard_issuer_values({field: value})

    def test_persistent_mvp_source_and_introspection_fields_are_declared(self):
        model = registry.AmrResourceIssuer
        for name in ('metadata_mode', 'discovery_unavailable_declared',
                     'discovery_unavailable_evidence_ref', 'verification_source',
                     'introspection_source', 'no_jwks_declaration',
                     'no_jwks_evidence_ref', 'introspection_credential_ref',
                     'introspection_auth_client_id', 'introspection_auth_method',
                     'introspection_basic_contract_ref',
                     'introspection_credential_endpoint', 'allow_jwt_introspection',
                     'allow_introspection_iss_absent'):
            self.assertTrue(hasattr(model, name), name)
        self.assertEqual(model.metadata_mode.args[0], [
            ('manual', 'Manual'), ('oidc_discovery', 'OIDC Discovery')])
        self.assertEqual(model.verification_source.args[0], [
            ('jwks', 'JWKS'), ('local_public', 'Local public key'), ('none', 'No JWKS')])
        self.assertEqual(model.introspection_source.args[0], [
            ('none', 'None'), ('manual', 'Manual'), ('rfc8414', 'RFC 8414')])

    def test_mvp_rejects_non_rs256_and_non_mvp_source_modes(self):
        base = self.profile(token_profile='jwt', jwks_uri='https://issuer.example/jwks',
                            mvp_enabled=True, metadata_mode='manual',
                            discovery_unavailable_declared=True,
                            discovery_unavailable_evidence_ref='evidence-discovery',
                            verification_source='jwks', introspection_source='none')
        for changes in (
                {'metadata_mode': 'oidc_discovery'},
                {'introspection_source': 'manual'},
                {'introspection_source': 'rfc8414'},
                {'token_profile': 'opaque', 'jwks_uri': False,
                 'verification_source': 'none', 'introspection_source': 'manual',
                 'introspection_endpoint': 'https://issuer.example/introspect',
                 'no_jwks_declaration': True, 'no_jwks_evidence_ref': 'keys',
                 'introspection_credential_endpoint': 'https://issuer.example/introspect',
                 'introspection_credential_ref': 'secret',
                 'introspection_auth_client_id': 'auth-client',
                 'introspection_auth_method': 'client_secret_basic',
                 'introspection_basic_contract_ref': 'contract'},
                {'metadata_mode': 'rfc8414'},
                {'metadata_mode': 'manual', 'verification_source': 'ps256'},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                registry.AmrResourceIssuer._check_profile(
                    [self.profile(**dict(base.__dict__, **changes))])

    def test_mvp_rejects_stale_introspection_and_no_jwks_fields_on_jwks_profile(self):
        base = self.profile(token_profile='jwt', jwks_uri='https://issuer.example/jwks',
                            mvp_enabled=True, metadata_mode='manual',
                            discovery_unavailable_declared=True,
                            discovery_unavailable_evidence_ref='evidence-discovery',
                            verification_source='jwks', introspection_source='none')
        for field, value in (
                ('introspection_endpoint', 'https://issuer.example/introspect'),
                ('introspection_credential_ref', 'secret'),
                ('introspection_auth_client_id', 'client'),
                ('introspection_auth_method', 'client_secret_basic'),
                ('introspection_basic_contract_ref', 'contract'),
                ('introspection_credential_endpoint', 'https://issuer.example/introspect'),
                ('no_jwks_declaration', True), ('no_jwks_evidence_ref', 'keys'),
                ('allow_jwt_introspection', True), ('allow_introspection_iss_absent', True)):
            invalid = self.profile(**dict(base.__dict__, **{field: value}))
            with self.subTest(field=field), self.assertRaises(ValidationError):
                registry.AmrResourceIssuer._check_profile([invalid])

    def test_non_mvp_rejects_stale_introspection_fields_but_keeps_legacy_generator_fields(self):
        base = self.profile(token_profile='jwt', jwks_uri='https://issuer.example/jwks',
                            mvp_enabled=False, verification_source='jwks',
                            introspection_source='none')
        for field, value in (
                ('introspection_endpoint', 'https://issuer.example/introspect'),
                ('no_jwks_declaration', True)):
            invalid = self.profile(**dict(base.__dict__, **{field: value}))
            with self.subTest(field=field), self.assertRaises(ValidationError):
                registry.AmrResourceIssuer._check_profile([invalid])

        legacy = self.profile(**dict(base.__dict__, token_endpoint='https://issuer.example/token',
                                     credential_ref='generator.secret'))
        registry.AmrResourceIssuer._check_profile([legacy])
        class User(SimpleNamespace):
            def __len__(self):
                return 1

        fixed_user = self.profile(**dict(base.__dict__, resolver_mode='fixed_user',
                                         fixed_user_id=User(id=7, active=True, share=False,
                                             company_ids=[7], has_group=lambda name: False)))
        registry.AmrResourceIssuer._check_profile([fixed_user])

    def test_mvp_manual_no_jwks_requires_explicit_source_declarations(self):
        profile = self.profile(token_profile='opaque', jwks_uri=False,
                               mvp_enabled=True, metadata_mode='manual',
                               discovery_unavailable_declared=True,
                               discovery_unavailable_evidence_ref='evidence-discovery',
                               verification_source='none', introspection_source='manual',
                               no_jwks_declaration=True, no_jwks_evidence_ref='evidence-no-jwks',
                               introspection_endpoint='https://issuer.example/introspect',
                               introspection_credential_endpoint='https://issuer.example/introspect',
                               introspection_credential_ref='introspection.secret',
                               introspection_auth_client_id='auth-client',
                               introspection_auth_method='client_secret_basic',
                               introspection_basic_contract_ref='provider-contract')
        with self.assertRaises(ValidationError):
            registry.AmrResourceIssuer._check_profile([profile])
        # Excluded legacy auth remains rejected even when MVP is disabled.
        legacy = self.profile(**dict(profile.__dict__, mvp_enabled=False))
        with self.assertRaises(ValidationError):
            registry.AmrResourceIssuer._check_profile([legacy])
        for equality in (
                {'credential_ref': 'same.secret', 'introspection_credential_ref': 'same.secret'},
                {'client_id': 'auth-client', 'introspection_auth_client_id': 'auth-client'}):
            invalid = self.profile(**dict(profile.__dict__, **equality,
                introspection_source='rfc8414', introspection_endpoint=False,
                introspection_basic_contract_ref=False))
            with self.subTest(equality=equality), self.assertRaises(ValidationError):
                registry.AmrResourceIssuer._check_profile([invalid])
        jwt_profile = self.profile(**dict(profile.__dict__, token_profile='jwt',
                                          allow_jwt_introspection=True))
        with self.assertRaises(ValidationError):
            registry.AmrResourceIssuer._check_profile([jwt_profile])
        for field, value in (('discovery_unavailable_evidence_ref', False),
                             ('no_jwks_declaration', False),
                             ('introspection_credential_ref', False),
                             ('introspection_basic_contract_ref', False)):
            invalid = self.profile(**dict(profile.__dict__, **{field: value}))
            with self.subTest(field=field), self.assertRaises(ValidationError):
                registry.AmrResourceIssuer._check_profile([invalid])

    def test_introspection_client_id_requires_exact_builtin_string(self):
        class StringSubclass(str):
            pass

        # The helper remains available to legacy code, but MVP must reject
        # introspection configuration before interpreting its client ID.
        valid = self.profile(token_profile='opaque', jwks_uri=False,
                             mvp_enabled=True, metadata_mode='manual',
                             discovery_unavailable_declared=True,
                             discovery_unavailable_evidence_ref='evidence-discovery',
                             verification_source='none', introspection_source='manual',
                             no_jwks_declaration=True, no_jwks_evidence_ref='keys',
                             introspection_endpoint='https://issuer.example/introspect',
                             introspection_credential_endpoint='https://issuer.example/introspect',
                             introspection_credential_ref='secret',
                             introspection_auth_client_id='auth-client',
                             introspection_auth_method='client_secret_basic',
                             introspection_basic_contract_ref='contract')
        with self.assertRaises(ValidationError):
            registry.AmrResourceIssuer._check_profile([valid])
        for value in ('a', StringSubclass('auth-client'), '', 'a' * 1025):
            with self.subTest(value=repr(value)):
                self.assertEqual(type(value) is str, not isinstance(value, StringSubclass))


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
        self.assertEqual(sudo_methods, ['_compute_local_public_key', '_lookup', '_migrate_legacy_v2',
                                         'action_capture_policy_snapshot', 'action_invalidate',
                                         'action_restore_policy_snapshot'])

    def test_security_and_ui_files_are_wired_and_restricted(self):
        manifest = ast.literal_eval((ROOT / '__manifest__.py').read_text())
        for filename in ('security/res_groups.xml', 'security/ir.model.access.csv',
                         'security/registry_rules.xml', 'views/trust_registry_views.xml'):
            self.assertIn(filename, manifest['data'])
        with (ROOT / 'security/ir.model.access.csv').open() as source:
            acls = list(csv.DictReader(source))
        self.assertEqual(len(acls), 8)
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
