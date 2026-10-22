# -*- coding: utf-8 -*-

from odoo import fields, models


class OidcJwtReplay(models.Model):
    _name = 'oidc.jwt.replay'
    _description = 'Used JWT Assertions'

    jti = fields.Char(required=True, index=True)
    iss = fields.Char(required=True, index=True)
    expired_at = fields.Datetime(required=True)

    _sql_constraints = [
        ('jti_issuer_unique',
         'unique(jti, iss)',
         'JWT assertion already used.')
    ]
