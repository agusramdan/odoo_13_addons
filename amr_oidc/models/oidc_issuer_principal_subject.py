# -*- coding: utf-8 -*-
"""Fresh-profile issuer-owned opaque subjects."""
import re
import secrets

import psycopg2
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_CREATE_CAPABILITY = object()
_WRITE_CAPABILITY = object()
_SUBJECT_RE = re.compile(r'\A[0-9a-f]{64}\Z')


class OidcIssuerPrincipalSubject(models.Model):
    _name = 'oidc.issuer.principal.subject'
    _description = 'OIDC Issuer Principal Subject'
    _rec_name = 'namespace'
    _sql_constraints = [
        ('issuer_principal_unique', 'unique(namespace, user_id)',
         'An issuer principal can have only one subject.'),
        ('issuer_subject_unique', 'unique(namespace, subject)',
         'An issuer subject can identify only one principal.'),
    ]

    namespace = fields.Char(required=True, readonly=True)
    user_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')
    subject = fields.Char(required=True, readonly=True)
    active = fields.Boolean(default=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_oidc_subject_capability') is not _CREATE_CAPABILITY:
            raise AccessError('Issuer subjects can only be provisioned by the issuer service.')
        for value in vals_list:
            if (set(value) != {'namespace', 'user_id', 'subject', 'active'}
                    or not isinstance(value.get('namespace'), str) or not value['namespace']
                    or type(value.get('user_id')) is not int
                    or not isinstance(value.get('subject'), str)
                    or not _SUBJECT_RE.match(value['subject']) or value['active'] is not True):
                raise UserError('Invalid issuer subject record.')
        return super(OidcIssuerPrincipalSubject, self).create(vals_list)

    def write(self, vals):
        if self.env.context.get('_oidc_subject_capability') is not _WRITE_CAPABILITY:
            raise AccessError('Issuer subjects are immutable.')
        if set(vals) != {'active'} or vals['active'] is not False:
            raise AccessError('Only issuer subject tombstoning is allowed.')
        return super(OidcIssuerPrincipalSubject, self).write(vals)

    def unlink(self):
        raise AccessError('Issuer subject reservations cannot be deleted.')

    @api.model
    def _get_or_create_subject(self, namespace, user_id):
        if not namespace or type(user_id) is not int:
            raise UserError('Invalid issuer principal.')
        # sudo: this private issuer-service path is reached after client auth.
        service = self.sudo().with_context(active_test=False)
        for _attempt in range(3):
            existing = service.search([
                ('namespace', '=', namespace), ('user_id', '=', user_id),
            ])
            if existing:
                if len(existing) != 1 or not existing.active or not _SUBJECT_RE.fullmatch(existing.subject):
                    raise UserError('Issuer principal is unavailable.')
                return existing.subject
            subject = secrets.token_bytes(32).hex()
            try:
                with self.env.cr.savepoint():
                    service.with_context(_oidc_subject_capability=_CREATE_CAPABILITY).create({
                        'namespace': namespace, 'user_id': user_id,
                        'subject': subject, 'active': True,
                    })
                return subject
            except psycopg2.IntegrityError:
                existing = service.search([
                    ('namespace', '=', namespace), ('user_id', '=', user_id),
                ])
                if existing:
                    if (len(existing) != 1 or not existing.active
                            or not _SUBJECT_RE.fullmatch(existing.subject)):
                        raise UserError('Issuer principal is unavailable.')
                    return existing.subject
                collision = service.search([
                    ('namespace', '=', namespace), ('subject', '=', subject),
                ])
                if not collision:
                    raise UserError('Issuer subject reservation failed.')
        raise UserError('Unable to reserve a unique issuer subject.')

    @api.model
    def _archive_subject(self, namespace, user_id):
        # sudo: preserve the tombstone reservation through the internal service path.
        record = self.sudo().search([
            ('namespace', '=', namespace), ('user_id', '=', user_id),
        ])
        if len(record) != 1:
            raise UserError('Issuer principal is unavailable.')
        return record.with_context(_oidc_subject_capability=_WRITE_CAPABILITY).write({'active': False})
