import ast
import json

from lxml import etree

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestIssuerLifecycle(TransactionCase):
    def setUp(self):
        super(TestIssuerLifecycle, self).setUp()
        self.issuer = self.env['oidc.issuer.register'].create({
            'issuer': 'https://lifecycle.test', 'client_id': 'synthetic-client',
        })

    def test_unarchive_batch_validation_is_atomic(self):
        archived = self.issuer
        archived.action_to_disable()
        archived.unlink()
        production = self.env['oidc.issuer.register'].create({
            'issuer': 'https://batch-production.test', 'client_id': 'client',
        })
        production.action_to_production()
        for batch in (archived | production, production | archived):
            with self.assertRaises(ValidationError):
                batch.write({'active': True})
            self.assertEqual((archived.active, archived.state), (False, 'disable'))
            self.assertEqual((production.active, production.state), (True, 'production'))

    def test_unarchive_requires_trust_admin(self):
        self.issuer.action_to_disable()
        self.issuer.unlink()
        user = self.env['res.users'].create({
            'name': 'Code admin', 'login': 'unarchive-code-admin',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('amr_resource.group_oidc_code_admin').id])],
        })
        self.assertTrue(self.issuer.with_user(user).check_access_rights('write', raise_exception=False))
        with self.assertRaises(AccessError):
            self.issuer.with_user(user).write({'active': True})
        self.assertEqual((self.issuer.active, self.issuer.state), (False, 'disable'))
        self.issuer.action_unarchive()
        self.assertEqual((self.issuer.active, self.issuer.state), (True, 'draft'))

    def test_new_form_defaults_to_draft(self):
        defaults = self.env['oidc.issuer.register'].default_get(['state'])
        self.assertEqual(defaults.get('state'), 'draft')

    def test_transitions_archive_and_invalid(self):
        issuer = self.issuer
        self.assertEqual(issuer.state, 'draft')
        with self.assertRaises(ValidationError):
            issuer.action_to_draft()
        with self.assertRaises(ValidationError):
            issuer.unlink()
        for action, state in [('action_to_production', 'production'),
                              ('action_to_draft', 'draft'),
                              ('action_to_disable', 'disable')]:
            getattr(issuer, action)()
            self.assertEqual(issuer.state, state)
        issuer.unlink()
        self.assertFalse(issuer.active)
        self.assertTrue(issuer.exists())
        with self.assertRaises(ValidationError):
            issuer.action_to_production()
        self.assertEqual((issuer.state, issuer.active), ('disable', False))
        issuer.action_unarchive()
        self.assertEqual((issuer.state, issuer.active), ('draft', True))
        issuer.action_to_production()
        self.assertEqual((issuer.state, issuer.active), ('production', True))
        issuer.action_to_disable()
        issuer.unlink()
        issuer.action_to_draft()
        self.assertEqual((issuer.state, issuer.active), ('draft', True))

    def test_matrix_and_search_context(self):
        issuer = self.issuer
        for source in ('draft', 'production', 'disable'):
            if issuer.state != source:
                getattr(issuer, 'action_to_' + source)()
            for target in ('draft', 'production', 'disable'):
                if source == target:
                    with self.assertRaises(ValidationError):
                        getattr(issuer, 'action_to_' + target)()
                    self.assertEqual((issuer.state, issuer.active), (source, True))
                else:
                    getattr(issuer, 'action_to_' + target)()
                    self.assertEqual((issuer.state, issuer.active), (target, True))
                    getattr(issuer, 'action_to_' + source)()
            with self.assertRaises(ValidationError):
                issuer.action_set_state('invalid')
            self.assertEqual((issuer.state, issuer.active), (source, True))
            if source != 'disable':
                with self.assertRaises(ValidationError):
                    issuer.unlink()
                self.assertEqual((issuer.state, issuer.active), (source, True))
        issuer.unlink()
        self.assertFalse(issuer.active)
        action = self.env.ref('amr_resource.action_resource_issuers')
        context = ast.literal_eval(action.context)
        self.assertFalse(context['active_test'])
        domain = [('id', '=', issuer.id)]
        self.assertFalse(self.env['oidc.issuer.register'].search(domain))
        self.assertEqual(self.env['oidc.issuer.register'].with_context(**context).search(domain), issuer)
        with self.assertRaises(ValidationError):
            issuer.action_to_production()
        issuer.action_to_draft()
        issuer.action_to_production()
        self.assertEqual((issuer.state, issuer.active), ('production', True))

    def test_children_non_draft_matrix(self):
        issuer = self.issuer
        algorithm = self.env['oidc.algorithm'].search([], limit=1)
        fixtures = [
            ('oidc.issuer.register.audience', {'value': 'audience'}, {'value': 'changed'}, {'value': 'denied'}),
            ('oidc.issuer.subject', {'sub': 'subject', 'user_id': self.env.ref('base.user_admin').id}, {'sub': 'changed'}, {'sub': 'denied'}),
            ('oidc.issuer.user.mapping', {'field_user': 'login', 'jwt_key': 'email'}, {'jwt_key': 'changed'}, {'jwt_key': 'preferred_username'}),
            ('oidc.issuer.algorithm.policy', {'algorithm_id': algorithm.id}, {'enabled': False}, {'enabled': True}),
        ]
        children = []
        for model, values, update, rejected in fixtures:
            values['issuer_id'] = issuer.id
            child = self.env[model].create(values)
            child.write(update)
            children.append(child)
        for state in ('production', 'disable'):
            getattr(issuer, 'action_to_' + state)()
            with self.assertRaises(ValidationError):
                issuer.write({'client_id': 'denied'})
            self.assertEqual(issuer.client_id, 'synthetic-client')
            for (model, values, update, rejected), child in zip(fixtures, children):
                before = child.read(list(update))[0]
                for key in rejected:
                    self.assertNotEqual(before[key], rejected[key])
                with self.assertRaises(ValidationError):
                    self.env[model].create(values)
                with self.assertRaises(ValidationError):
                    child.write(rejected)
                with self.assertRaises(ValidationError):
                    child.unlink()
                self.assertTrue(child.exists())
                self.assertEqual(child.read(list(update))[0], before)
        issuer.action_to_draft()
        self.env['oidc.issuer.register.audience'].create({'issuer_id': issuer.id, 'value': 'second'})
        for child in children:
            child.unlink()
            self.assertFalse(child.exists())
        last_audience = issuer.audience_ids
        self.assertEqual(len(last_audience), 1)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            last_audience.unlink()
        self.assertTrue(last_audience.exists())

    def test_view_modifiers_and_groups(self):
        user = self.env['res.users'].create({'name': 'View ordinary', 'login': 'view-ordinary',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        view = self.env.ref('amr_resource.view_resource_issuer_form')
        admin = etree.fromstring(self.env['oidc.issuer.register'].fields_view_get(view.id, 'form')['arch'].encode())
        ordinary = etree.fromstring(self.env['oidc.issuer.register'].with_user(user).fields_view_get(view.id, 'form')['arch'].encode())
        states = {'action_to_production': ('draft', 'disable'), 'action_to_draft': ('production', 'disable'),
                  'action_to_disable': ('draft', 'production'), 'unlink': ('disable',)}
        for name, allowed in states.items():
            node = admin.xpath('//button[@name="%s"]' % name)[0]
            ordinary_node = ordinary.xpath('//button[@name="%s"]' % name)
            if ordinary_node:
                self.assertTrue(any(json.loads(node.get('modifiers', '{}')).get('invisible') is True
                                    for node in [ordinary_node[0]] + list(ordinary_node[0].iterancestors())),
                                etree.tostring(ordinary_node[0].getparent()))
            modifier = json.loads(node.get('modifiers'))['invisible']
            for state in ('draft', 'production', 'disable'):
                if name in ('action_to_production', 'unlink'):
                    self.assertEqual(modifier[1], ['active', '=', False])
                    condition = modifier[2]
                    hidden = state not in condition[2] if condition[1] == 'not in' else state != condition[2]
                    self.assertEqual(state not in allowed, hidden)
                else:
                    self.assertEqual(state not in allowed, state not in modifier[0][2])
        for field in ('issuer', 'client_id', 'audience_ids', 'binding_ids', 'user_mapping_ids', 'algorithm_policy_ids'):
            node = admin.xpath('//field[@name="%s"]' % field)[0]
            self.assertEqual(json.loads(node.get('modifiers'))['readonly'], [['state', '!=', 'draft']])
        self.assertTrue(json.loads(admin.xpath('//field[@name="state"]')[0].get('modifiers'))['readonly'])

    def test_batch_atomicity(self):
        other = self.env['oidc.issuer.register'].create({
            'issuer': 'https://other-lifecycle.test', 'client_id': 'synthetic-client',
        })
        other.action_to_production()
        with self.assertRaises(ValidationError):
            (self.issuer | other).action_to_production()
        self.assertEqual((self.issuer.state, other.state), ('draft', 'production'))

    def test_parent_and_children(self):
        issuer = self.issuer
        issuer.write({'client_id': 'updated'})
        audience = self.env['oidc.issuer.register.audience'].create({'issuer_id': issuer.id, 'value': 'audience'})
        binding = self.env['oidc.issuer.subject'].create({'issuer_id': issuer.id, 'sub': 'subject', 'user_id': self.env.ref('base.user_admin').id})
        mapping = self.env['oidc.issuer.user.mapping'].create({'issuer_id': issuer.id, 'field_user': 'login', 'jwt_key': 'email'})
        algorithm = self.env['oidc.algorithm'].search([], limit=1)
        self.assertTrue(algorithm)
        policy = self.env['oidc.issuer.algorithm.policy'].create({'issuer_id': issuer.id, 'algorithm_id': algorithm.id})
        audience.write({'value': 'changed'})
        binding.write({'sub': 'changed'})
        mapping.write({'jwt_key': 'preferred_username'})
        policy.write({'enabled': False})
        issuer.action_to_production()
        with self.assertRaises(ValidationError):
            issuer.write({'client_id': 'denied'})
        for child in (audience, binding, mapping, policy):
            with self.assertRaises(ValidationError):
                child.unlink()
        with self.assertRaises(ValidationError):
            self.env['oidc.issuer.register.audience'].create({'issuer_id': issuer.id, 'value': 'denied'})
        issuer.action_to_draft()
        binding.unlink()
        mapping.unlink()
        policy.unlink()
        self.env['oidc.issuer.register.audience'].create({'issuer_id': issuer.id, 'value': 'second'})
        audience.unlink()

    def test_access_and_view(self):
        user = self.env['res.users'].create({'name': 'Lifecycle ordinary', 'login': 'lifecycle-ordinary',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        issuer = self.issuer.with_user(user)
        for action in ('action_to_production', 'action_to_draft', 'action_to_disable', 'unlink'):
            with self.assertRaises(AccessError):
                getattr(issuer, action)()
        self.assertFalse(self.env['oidc.issuer.register'].with_user(user).check_access_rights('read', raise_exception=False))
        arch = self.env.ref('amr_resource.view_resource_issuer_form').read_combined(['arch'])['arch']
        root = etree.fromstring(arch.encode())
        attrs = ast.literal_eval(root.xpath('//button[@name="action_to_production"]')[0].get('attrs'))
        self.assertIn(('state', 'not in', ['draft', 'disable']), attrs['invisible'])
        self.assertIn(('active', '=', False), attrs['invisible'])
        for field in ('audience_ids', 'binding_ids', 'user_mapping_ids', 'algorithm_policy_ids'):
            self.assertIn('readonly', root.xpath('//field[@name="%s"]' % field)[0].get('attrs'))
