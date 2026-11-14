# -*- coding: utf-8 -*-
"""Fresh issuer subject ORM boundaries; run only in authorized Odoo DB tests."""
import unittest

try:
    import odoo
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
    raise unittest.SkipTest("Odoo unavailable; native issuer subject tests NOT RUN")

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import SavepointCase
from psycopg2 import IntegrityError

from odoo.addons.amr_oidc.models import oidc_issuer_principal_subject as subject_model


class TestFreshIssuerPrincipalSubject(SavepointCase):
    def _user(self, login, group_xmlids):
        return self.env['res.users'].create({
            'name': login, 'login': login,
            'groups_id': [(6, 0, [self.env.ref(xmlid).id for xmlid in group_xmlids])],
        })

    def test_every_human_role_has_no_mapping_acl(self):
        internal = self._user('subject-reader-internal', ['base.group_user'])
        system = self._user('subject-reader-system', ['base.group_system'])
        portal = self._user('subject-reader-portal', ['base.group_portal'])
        model = self.env['oidc.issuer.principal.subject']
        for user in (internal, system, portal):
            with self.subTest(user=user.login):
                scoped = model.with_user(user)
                self.assertFalse(scoped.check_access_rights('read', raise_exception=False))
                with self.assertRaises(AccessError):
                    scoped.search([])
                with self.assertRaises(AccessError):
                    scoped.create({})

    def test_sudo_rpc_cannot_create_or_mutate_a_subject(self):
        model = self.env['oidc.issuer.principal.subject'].sudo()
        with self.assertRaises(AccessError):
            model.create({
                'namespace': 'https://issuer.example.invalid', 'user_id': self.env.user.id,
                'subject': 'a' * 64, 'active': True,
            })
        with self.assertRaises(AccessError):
            model.with_context(_oidc_subject_capability='trusted').create({})
        with self.assertRaises(AccessError):
            model.write({'namespace': 'https://other.example.invalid'})
        with self.assertRaises(AccessError):
            model.unlink()

    def test_archived_subject_keeps_both_unique_reservations_and_denies_issuance(self):
        user = self._user('subject-mapped-user', ['base.group_user'])
        issuer = 'https://issuer.example.invalid'
        service = self.env['oidc.issuer.principal.subject'].sudo().with_context(
            _oidc_subject_capability=subject_model._CREATE_CAPABILITY)
        mapping = service.create({
            'namespace': issuer, 'user_id': user.id, 'subject': 'a' * 64, 'active': True,
        })
        self.env['oidc.issuer.principal.subject'].sudo()._archive_subject(issuer, user.id)
        self.assertFalse(mapping.active)
        with self.assertRaises(UserError):
            self.env['oidc.issuer.principal.subject'].sudo()._get_or_create_subject(issuer, user.id)

        with self.assertRaises(IntegrityError), self.cr.savepoint():
            service.create({
                'namespace': issuer, 'user_id': user.id, 'subject': 'b' * 64, 'active': True,
            })
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            service.create({
                'namespace': issuer, 'user_id': self.env.user.id,
                'subject': 'a' * 64, 'active': True,
            })

    def test_user_deletion_is_restricted_by_subject_foreign_key(self):
        user = self._user('subject-delete-user', ['base.group_user'])
        self.env['oidc.issuer.principal.subject'].sudo().with_context(
            _oidc_subject_capability=subject_model._CREATE_CAPABILITY).create({
                'namespace': 'https://issuer.example.invalid', 'user_id': user.id,
                'subject': 'c' * 64, 'active': True,
            })
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            user.sudo().unlink()
