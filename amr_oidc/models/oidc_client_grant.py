# -*- coding: utf-8 -*-
from odoo import fields, models


class OidcClientGrant(models.Model):
    _name = "oidc.client.grant"
    _description = "OIDC Client Grant"
    _order = "code"
    _sql_constraints = [("code_unique", "unique(code)", "Grant code must be unique.")]

    code = fields.Selection([
        ("client_credentials", "Client Credentials"),
        ("authorization_code", "Authorization Code"),
        ("refresh_token", "Refresh Token"),
    ], required=True, index=True)
    name = fields.Char(required=True)
