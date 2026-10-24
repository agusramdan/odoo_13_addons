"""Odoo-native registry/ACL/migration checks; not part of the offline runner."""
from odoo.exceptions import AccessError, ValidationError
from psycopg2 import IntegrityError

from .test_helper import ResourceCase


class TestResourceRegistry(ResourceCase):
    def test_registry_unique_issuer_including_archived(self):
        self.profile.active = False
        values = dict(issuer=self.profile.issuer, client_id='client-a', token_profile='jwt',
                      jwks_uri='https://keys.invalid/jwks', allow_missing_azp=True,
                      audience_ids=[(0, 0, {'value': 'resource-a'})])
        with self.assertRaises((ValidationError, IntegrityError)), self.cr.savepoint():
            self.registry.create(values)

    def test_no_default_mapping_or_ordinary_registry_access(self):
        self.assertFalse(self.registry.default_get(['resolver_mode']).get('resolver_mode'))
        ordinary = self.env['res.users'].create({
            'name': 'Synthetic ordinary user', 'login': 'ordinary-registry-unit',
            'groups_id': [(6, 0, self.env.ref('base.group_user').ids)],
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
        })
        with self.assertRaises(AccessError):
            self.profile.with_user(ordinary).read(['issuer'])
        with self.assertRaises(AccessError):
            self.profile.with_user(ordinary).write({'python_code': 'not executed'})
        with self.assertRaises(AccessError):
            self.registry.with_user(ordinary)._migrate_legacy_v2({}, [], [])
        with self.assertRaises(AccessError):
            self.profile.write({'local_public_key': 'inline input is forbidden'})

    def test_binding_and_audience_uniqueness(self):
        self.profile.binding_ids = [(0, 0, {'sub': 'subject-a', 'user_id': self.admin.id})]
        for field, value in (
            ('binding_ids', {'sub': 'subject-a', 'user_id': self.admin.id}),
            ('audience_ids', {'value': 'resource-a'}),
        ):
            with self.assertRaises((ValidationError, IntegrityError)), self.cr.savepoint():
                self.profile.write({field: [(0, 0, value)]})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.profile.audience_ids.unlink()

    def test_explicit_migration_is_additive_idempotent_and_conflict_rejecting(self):
        params = self.env['ir.config_parameter'].sudo()
        for key, value in {
            'amr_resource.issuer': 'amr_resource.legacy.synthetic_issuer',
            'amr_resource.audience': 'amr_resource.legacy.synthetic_audience',
            'amr_resource.legacy.synthetic_issuer': self.profile.issuer,
            'amr_resource.legacy.synthetic_audience': 'resource-a',
        }.items():
            params.set_param(key, value)
        values = dict(issuer=self.profile.issuer, client_id='client-a', token_profile='jwt',
                      jwks_uri=self.profile.jwks_uri, token_endpoint=self.profile.token_endpoint,
                      allow_missing_azp=True, resolver_mode='get_user_match')
        self.profile.unlink()
        bindings = [{'sub': 'subject-a', 'user_id': self.admin.id}]
        result = self.registry._migrate_legacy_v2(values, ['resource-a'], bindings)
        self.assertTrue(result['dry_run'])
        self.assertFalse(self.registry.search([('issuer', '=', values['issuer'])]))
        self.assertFalse(params.get_param('amr_resource.migration.v2.global'))
        self.registry._migrate_legacy_v2(values, ['resource-a'], bindings, dry_run=False)
        self.assertTrue(self.registry._migrate_legacy_v2(values, ['resource-a'], bindings,
                                                       dry_run=False)['already_applied'])
        rows = self.registry.search([('issuer', '=', values['issuer'])])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.binding_ids.sub, 'subject-a')
        self.assertEqual(params.get_param('amr_resource.issuer'), 'amr_resource.legacy.synthetic_issuer')
        rows.client_id = 'conflicting-client'
        with self.assertRaises(ValidationError):
            self.registry._migrate_legacy_v2(values, ['resource-a'], bindings, dry_run=False)

    def test_stored_source_audit_without_execution(self):
        self.profile.python_code = 'raise RuntimeError("must never execute")'
        self.assertEqual(self.profile.code_revision, 1)
        self.assertEqual(len(self.profile.code_digest), 64)
        self.assertEqual(self.profile.code_actor_id, self.admin)
        self.assertTrue(self.profile.code_date)
        with self.assertRaises(AccessError):
            self.profile.write({'code_revision': 10})
