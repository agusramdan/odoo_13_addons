# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    amr_token_algorithm = fields.Selection(
        [("HS256", "HS256"), ("RS256", "RS256"), ("ES256", "ES256")],
        default="RS256",
        config_parameter="amr_token.algorithm",
    )

    amr_token_signature_type = fields.Selection(
        [("secret", "Secret"), ("public_key", "Public Key")],
        required=True,
        config_parameter="amr_token.signature_type",
    )
    amr_token_secret = fields.Char("Secret", config_parameter="amr_token.secret")
    amr_token_secret_algorithm = fields.Selection(
        [
            # https://pyjwt.readthedocs.io/en/stable/algorithms.html
            ("HS256", "HS256 - HMAC using SHA-256 hash algorithm"),
            ("HS384", "HS384 - HMAC using SHA-384 hash algorithm"),
            ("HS512", "HS512 - HMAC using SHA-512 hash algorithm"),
        ],
        default="HS256",
        config_parameter="amr_token.secret_algorithm",
    )
    amr_token_public_key_algorithm = fields.Selection(
        [
            # https://pyjwt.readthedocs.io/en/stable/algorithms.html
            ("ES256", "ES256 - ECDSA using SHA-256"),
            ("ES256K", "ES256K - ECDSA with secp256k1 curve using SHA-256"),
            ("ES384", "ES384 - ECDSA using SHA-384"),
            ("ES512", "ES512 - ECDSA using SHA-512"),
            ("RS256", "RS256 - RSASSA-PKCS1-v1_5 using SHA-256"),
            ("RS384", "RS384 - RSASSA-PKCS1-v1_5 using SHA-384"),
            ("RS512", "RS512 - RSASSA-PKCS1-v1_5 using SHA-512"),
            ("PS256", "PS256 - RSASSA-PSS using SHA-256 and MGF1 padding with SHA-256"),
            ("PS384", "PS384 - RSASSA-PSS using SHA-384 and MGF1 padding with SHA-384"),
            ("PS512", "PS512 - RSASSA-PSS using SHA-512 and MGF1 padding with SHA-512"),
        ],
        default="RS256",
        config_parameter="amr_token.public_key_algorithm",
    )
    amr_token_using_secret = fields.Boolean(
        "Using Secret",
        compute="_compute_amr_token_using_secret",
    )

    amr_token_retention_in = fields.Integer(
        "Retention In (Seconds)",
        config_parameter="amr_token.retention_in",
    )
    amr_token_expires_in = fields.Integer(
        "Expires In (Seconds)",
        config_parameter="amr_token.expires_in",
    )
    amr_token_audience = fields.Char("Audience", config_parameter="database.uuid")
    amr_token_fresh_profile_issuer = fields.Char(
        "Fresh Issuer Profile", config_parameter="amr_token.fresh_profile_issuer",
        groups="base.group_system",
    )

    def _validate_fresh_profile_settings(self, values):
        # sudo: read only the opt-in flag before enforcing scoped settings rules.
        configured = self.env['ir.config_parameter'].sudo().get_param(
            'amr_token.fresh_profile_issuer')
        selected = values.get('amr_token_fresh_profile_issuer', configured)
        if (configured or selected) and not self.env.user.has_group('base.group_system'):
            raise AccessError('Only a system administrator may change fresh-profile settings.')
        if not selected or 'amr_token_expires_in' not in values:
            return
        ttl = values['amr_token_expires_in']
        canonical = (type(ttl) is int or
                     isinstance(ttl, str) and ttl.isascii() and ttl.isdecimal()
                     and len(ttl) <= 5 and str(int(ttl)) == ttl)
        if not canonical or not 60 <= int(ttl) <= 86400:
            raise UserError('Fresh-profile lifetime must be canonical seconds between 60 and 86400.')

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            self._validate_fresh_profile_settings(values)
        return super(ResConfigSettings, self).create(vals_list)

    def write(self, values):
        self._validate_fresh_profile_settings(values)
        return super(ResConfigSettings, self).write(values)

    def set_values(self):
        for record in self:
            # sudo: inspect the opt-in profile flag before guarding settings writes.
            profile_issuer = record.env['ir.config_parameter'].sudo().get_param(
                'amr_token.fresh_profile_issuer')
            is_system = record.env.user.has_group('base.group_system')
            if profile_issuer and not is_system:
                raise AccessError('Only a system administrator may change fresh-profile settings.')
            if not is_system:
                continue
            if record.amr_token_fresh_profile_issuer:
                helper = record.env['amr.oidc.helper']
                if record.amr_token_fresh_profile_issuer != helper.get_issuer():
                    raise UserError('Fresh issuer must exactly match the configured canonical issuer.')
                ttl = record.amr_token_expires_in
                if type(ttl) is not int or not 60 <= ttl <= 86400:
                    raise UserError('Fresh-profile lifetime must be between 60 and 86400 seconds.')
                if profile_issuer:
                    helper._require_fresh_profile_instance()
                else:
                    helper._bind_fresh_profile_instance()
        return super(ResConfigSettings, self).set_values()

    @api.depends("amr_token_algorithm")
    def _compute_amr_token_using_secret(self):
        for record in self:
            record.amr_token_using_secret = record.amr_token_algorithm == "HS256"

    def action_create_public_key(self):
        # sudo: preserve source refresh lookup; refresh policy deferred.
        self.env['amr.oidc.helper'].sudo().create_public_key(self.amr_token_public_key_algorithm)
