import importlib.util
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL_SCRIPTS = Path(__file__).parents[3] / '.agents' / 'skills' / 'odoo-unit-test' / 'scripts'
sys.path.insert(0, str(SKILL_SCRIPTS))
from mock_odoo import odoo_modules


def load_trust_registry():
    """Load real module code with framework imports isolated from the database."""
    path = Path(__file__).parents[2] / 'models' / 'trust_registry.py'
    helper = types.ModuleType('amr_resource.models.helper')
    setattr(helper, '_PROVENANCE', object())
    helper._string = helper._manual_key_source = helper._require_policy_revision = lambda *args: None
    helper.fetch_json = lambda *args, **kwargs: None
    spec = importlib.util.spec_from_file_location('amr_resource.models.trust_registry', path)
    module = importlib.util.module_from_spec(spec)
    packages = {
        'amr_resource': types.ModuleType('amr_resource'),
        'amr_resource.models': types.ModuleType('amr_resource.models'),
    }
    packages['amr_resource'].__path__ = []
    packages['amr_resource.models'].__path__ = [str(Path(__file__).parents[2] / 'models')]
    packages['amr_resource'].__path__ = [str(Path(__file__).parents[2])]
    with odoo_modules() as _:
        import odoo
        odoo.SUPERUSER_ID = 1
        with patch.dict(sys.modules, dict(packages, **{'amr_resource.models.helper': helper,
                                                        'amr_resource.models.trust_registry': module})):
            spec.loader.exec_module(module)
    return module


class TestIssuerViewAccess(unittest.TestCase):
    def test_issuer_edit_controls_are_trust_admin_only_and_child_editors_are_draft_only(self):
        view = Path(__file__).parents[2] / 'views' / 'trust_registry_views.xml'
        arch = view.read_text(encoding='utf-8')
        tree_match = re.search(r'<tree[^>]*>(.*?)</tree>', arch, re.S)
        form_match = re.search(r'<form string="Trusted Issuer"[^>]*>(.*?)</form>', arch, re.S)
        self.assertIsNotNone(tree_match)
        self.assertIsNotNone(form_match)
        tree = tree_match.group(0)
        form = form_match.group(0)
        self.assertRegex(form, r'<form[^>]*create="true"[^>]*edit="true"')
        self.assertRegex(form, r'<header[^>]*groups="amr_resource\.group_oidc_trust_admin"')
        self.assertNotRegex(tree.split('>', 1)[0], r'\bgroups=')
        self.assertNotRegex(form.split('>', 1)[0], r'\bgroups=')
        menu = (Path(__file__).parents[2] / 'views' / 'menuitems.xml').read_text(encoding='utf-8')
        self.assertRegex(menu, r'<menuitem[^>]*groups="amr_resource\.group_oidc_trust_admin"')
        action = re.search(r'<record id="action_resource_issuers" model="ir.actions.act_window">(.*?)</record>', arch, re.S)
        self.assertIsNotNone(action)
        self.assertIsNotNone(re.search(r'<field name="groups_id"', action.group(1)))
        for field in ('audience_ids', 'binding_ids', 'user_mapping_ids', 'algorithm_policy_ids'):
            self.assertRegex(form, rf'<field name="{field}"[^>]*groups="amr_resource\.group_oidc_trust_admin"')
        self.assertRegex(tree, r'create="true"[^>]*edit="true"')
        production_button = re.search(r'<button name="action_to_production"[^>]*/>', form)
        self.assertIsNotNone(production_button)
        self.assertIn("('state', 'not in', ['draft', 'disable'])", production_button.group(0))
        for name in ('action_to_production', 'unlink'):
            button = re.search(r'<button name="%s"[^>]*/>' % name, form)
            self.assertIsNotNone(button)
            self.assertIn("('active', '=', False)", button.group(0))
        for field in ('audience_ids', 'binding_ids', 'user_mapping_ids', 'algorithm_policy_ids'):
            self.assertRegex(form, rf'<field name="{field}"[^>]*attrs="[^"]*readonly[^"]*state[^"]*draft')
            self.assertRegex(form, rf'<field name="{field}"[^>]*>\s*<tree editable="bottom" create="true" delete="true"')


class TestTrustStateTransitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_trust_registry()
        base = cls.module.OidcResourceIssuer.__mro__[1]
        def orm_write(recordset, values):
            recordset.write_calls.append(dict(values))
            for record in recordset.records:
                record.__dict__.update(values)
            return True
        base.write = orm_write

    def test_policy_algorithms_match_supported_key_algorithm(self):
        self.assertEqual(
            self.module._policy_algorithms([('RS256', True)], {'alg': 'RS256'}),
            frozenset({'RS256'}))
        with self.assertRaises(self.module.ValidationError):
            self.module._policy_algorithms([('RS256', True)], {'alg': 'HS256'})
        with self.assertRaises(self.module.ValidationError):
            self.module._policy_algorithms([('none', True)], {})

    def test_policy_algorithms_reject_invalid_shapes_and_disabled_policy(self):
        for policy, metadata in ((None, {}), ([('RS256', 1)], {}),
                                 ([('RS256', False)], {})):
            with self.subTest(policy=policy):
                with self.assertRaises(self.module.ValidationError):
                    self.module._policy_algorithms(policy, metadata)

    def test_effective_algorithms_intersects_enabled_and_supported(self):
        self.assertEqual(
            self.module._policy_algorithms([('RS256', True)], {'alg': 'RS256'}),
            frozenset({'RS256'}))
        with self.assertRaises(self.module.ValidationError):
            self.module._policy_algorithms([('RS256', True)], {'alg': 'HS256'})

    def test_https_url_rejects_local_and_unsafe_endpoints(self):
        for url in ('http://issuer.example', 'https://localhost/token',
                    'https://user:pass@example.test/token', 'https://127.0.0.1/token'):
            with self.subTest(url=url):
                self.assertFalse(self.module._https_url(url))
        self.assertTrue(self.module._https_url('https://issuer.example/token'))

    def test_mapping_validation_requires_unique_positive_sequences(self):
        good = [{'sequence': 1, 'field_user': 'login', 'jwt_key': 'sub', 'active': True}]
        self.assertTrue(self.module._validate_mapping_rows(good))
        for rows in (good + [dict(good[0])],
                     [{'sequence': 0, 'field_user': 'login', 'jwt_key': 'sub', 'active': True}],
                     [{'sequence': 1, 'field_user': 'login', 'jwt_key': 'sub', 'active': 1}]):
            with self.subTest(rows=rows):
                with self.assertRaises(self.module.ValidationError):
                    self.module._validate_mapping_rows(rows)

    def test_mapping_candidate_returns_unique_first_match(self):
        rows = [types.SimpleNamespace(sequence=2, field_user='login', jwt_key='email', active=True),
                types.SimpleNamespace(sequence=1, field_user='login', jwt_key='sub', active=True)]
        user = types.SimpleNamespace(id=42)
        class Bindings(list):
            def filtered(self, predicate):
                result = Bindings(row for row in self if predicate(row))
                result.user_id = result[0].user_id if result else None
                return result
        class Issuer(self.module.OidcResourceIssuer):
            def __init__(self):
                self.user_mapping_ids = rows
                self.binding_ids = Bindings([types.SimpleNamespace(sub='alice', user_id=user)])
                self.env = {'res.users': types.SimpleNamespace(browse=lambda user_id: user_id)}
                self.calls = []
                self.matches = [user]
            def _find_mapping_users(self, field, value):
                self.calls.append((field, value))
                return self.matches
        issuer = Issuer()
        found = issuer._mapping_user({'sub': 'alice', 'email': 'a@example.test'})
        self.assertEqual(found, 42)
        self.assertEqual(issuer.calls, [('login', 'alice')])
        issuer.matches = [user, types.SimpleNamespace(id=43)]
        with self.assertRaises(self.module.Unauthorized):
            issuer._mapping_user({'sub': 'alice'})

    def test_mapping_claim_rejects_invalid_names_and_values(self):
        self.assertEqual(self.module._validate_mapping_claim('sub', 'alice'), 'alice')
        for key, value in (('bad-key', 'alice'), ('sub', ''), ('sub', 'x\n')):
            with self.subTest(key=key, value=value):
                with self.assertRaises(self.module.ValidationError):
                    self.module._validate_mapping_claim(key, value)

    
    def test_unarchive_batch_rejects_before_any_write_in_both_orders(self):
        for reverse in (False, True):
            class Issuer(self.module.OidcResourceIssuer):
                def _registry_role(self, group):
                    return True
                def __init__(self, state, active, calls):
                    self.state, self.active = state, active
                    self.records, self.write_calls = [self], calls
                def __iter__(self):
                    return iter(self.records)
                def filtered(self, predicate):
                    result = Issuer('draft', True, self.write_calls)
                    result.records = [record for record in self.records if predicate(record)]
                    return result
                def __sub__(self, other):
                    return self.filtered(lambda record: record not in other.records)
                def __bool__(self):
                    return bool(self.records)
            calls = []
            archived = Issuer('disable', False, calls)
            production = Issuer('production', True, calls)
            batch = Issuer('draft', True, calls)
            batch.records = [production, archived] if reverse else [archived, production]
            with self.subTest(reverse=reverse):
                with self.assertRaises(self.module.ValidationError):
                    batch.write({'active': True})
                self.assertEqual(calls, [])
                self.assertEqual((archived.state, archived.active), ('disable', False))
                self.assertEqual((production.state, production.active), ('production', True))

    def test_standard_unarchive_restores_draft(self):
        class Issuer(self.module.OidcResourceIssuer):
            def _registry_role(self, group):
                return True
            state = 'disable'
            active = False
            def __init__(self):
                self.records = [self]
                self.write_calls = []
            def __iter__(self):
                return iter(self.records)
            def filtered(self, predicate):
                result = Issuer()
                result.records = [record for record in self.records if predicate(record)]
                result.write_calls = self.write_calls
                return result
            def __sub__(self, other):
                return self.filtered(lambda record: record not in other.records)
            def __bool__(self):
                return bool(self.records)
        issuer = Issuer()
        self.assertTrue(issuer.write({'active': True}))
        self.assertEqual((issuer.state, issuer.active), ('draft', True))

    def test_archived_issuer_requires_draft_before_production(self):
        model, records = self.issuer_model('disable', active=False)
        with self.assertRaises(self.module.ValidationError):
            model.action_to_production()
        self.assertEqual(model.write_calls, [])
        self.assertEqual((records[0].state, records[0].active), ('disable', False))
        self.assertTrue(model.action_to_draft())
        self.assertEqual((records[0].state, records[0].active), ('draft', True))
        self.assertTrue(model.action_to_production())
        self.assertEqual((records[0].state, records[0].active), ('production', True))

    def test_action_set_state_allows_transitions_and_unlink_soft_archives(self):
        for source, target in (('draft', 'production'), ('draft', 'disable'),
                               ('production', 'draft'), ('production', 'disable'),
                               ('disable', 'draft'), ('disable', 'production')):
            with self.subTest(source=source, target=target):
                model, records = self.issuer_model(source, active=True)
                result = model.action_set_state(target)
                self.assertTrue(result)
                self.assertEqual(records[0].state, target)
                expected_values = {'state': target}
                if target != 'disable':
                    expected_values = {'state': target, 'active': True}
                self.assertTrue(records[0].active)
                self.assertEqual(model.write_calls, [expected_values])

        model, records = self.issuer_model('disable', active=True)
        self.assertTrue(model.unlink())
        self.assertEqual(records[0].active, False)
        self.assertEqual(records[0].state, 'disable')
        self.assertEqual(model.write_calls, [{'active': False}])

    def test_action_set_state_rejects_invalid_and_self_transitions_without_write(self):
        for state, target in (('draft', 'draft'), ('production', 'production'),
                              ('disable', 'disable')):
            with self.subTest(state=state, target=target):
                model, records = self.issuer_model(state)
                with self.assertRaises(self.module.ValidationError):
                    model.action_set_state(target)
                self.assertEqual(model.write_calls, [])
                self.assertEqual(records[0].state, state)

    def test_trust_admin_required_for_transition_and_unlink(self):
        for operation in ('transition', 'unlink'):
            model, _ = self.issuer_model('disable', allowed=False)
            with self.subTest(operation=operation):
                with self.assertRaises(self.module.AccessError):
                    model.action_set_state('draft') if operation == 'transition' else model.unlink()
                self.assertEqual(model.write_calls, [])

    def test_invalid_batch_transition_does_not_write_any_record(self):
        model, records = self.issuer_model('draft', states=('draft', 'production'))
        with self.assertRaises(self.module.ValidationError):
            model.action_set_state('production')
        self.assertEqual(model.write_calls, [])
        self.assertEqual([record.state for record in records], ['draft', 'production'])

    def test_unlink_rejects_non_disabled_batch_without_write(self):
        model, records = self.issuer_model('disable', states=('disable', 'draft'))
        with self.assertRaises(self.module.ValidationError):
            model.unlink()
        self.assertEqual(model.write_calls, [])
        self.assertEqual([record.active for record in records], [True, True])

    def issuer_model(self, state, states=None, allowed=True, active=True):
        records = [types.SimpleNamespace(state=item, active=active)
                   for item in (states or (state,))]
        class Issuer(self.module.OidcResourceIssuer):
            def __init__(self):
                self.env = types.SimpleNamespace(user=types.SimpleNamespace(
                    has_group=lambda group: allowed))
                self.records = records
                self.write_calls = []
            def __iter__(self): return iter(self.records)
            def filtered(self, predicate): return [record for record in self.records if predicate(record)]
            def write(self, values):
                raise AssertionError('override write must not be called')
        model = Issuer()
        return model, records

    def test_copy_delegates_with_draft_default_without_claiming_orm_record(self):
        for source_state in ('production', 'disable'):
            model, records = self.issuer_model(source_state)
            captured = []
            def orm_copy(recordset, default=None):
                captured.append(dict(default or {}))
                return {'state': default['state']}
            with patch.object(self.module.OidcResourceIssuer.__mro__[1], 'copy', orm_copy, create=True):
                result = self.module.OidcResourceIssuer.copy(model, {'state': source_state})
            with self.subTest(source_state=source_state):
                self.assertEqual(captured, [{'state': 'draft'}])
                self.assertEqual(result, {'state': 'draft'})
                self.assertEqual(records[0].state, source_state)

    def test_state_helper_actions_delegate(self):
        for method, source, target in (('action_to_production', 'disable', 'production'),
                                       ('action_to_disable', 'production', 'disable'),
                                       ('action_to_draft', 'disable', 'draft')):
            with self.subTest(method=method):
                model, records = self.issuer_model(source, active=True)
                self.assertTrue(getattr(model, method)())
                self.assertEqual(records[0].state, target)
                self.assertTrue(records[0].active)
                self.assertEqual(model.write_calls, [{'state': target, 'active': True}
                                                     if target != 'disable' else {'state': target}])
