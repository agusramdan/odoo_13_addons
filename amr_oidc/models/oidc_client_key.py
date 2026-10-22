# -*- coding: utf-8 -*-

from odoo import fields, models


class OidcClientKey(models.Model):
    _name = 'oidc.client.key'
    _description = 'OIDC Client Key'

    client_id = fields.Many2one('oidc.client')
    kid = fields.Char()
    algorithm = fields.Char(default="RS256", )
    kty = fields.Selection([
        ("RSA", "RSA"),
        ("EC", "EC"),
        ("OKP", "OKP"),
    ])
    use = fields.Selection([
        ("sig", "Signature"),
        ("enc", "Encryption"),
    ], default="sig")

    public_key = fields.Text()
    active = fields.Boolean(default=True)
    expired_at = fields.Datetime()
    last_used_at = fields.Datetime()
