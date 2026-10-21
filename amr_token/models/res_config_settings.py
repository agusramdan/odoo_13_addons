# -*- coding: utf-8 -*-

from odoo import api, fields, models


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

    # module_amr_oidc = fields.Boolean("OIDC")
    # module_amr_oauth = fields.Boolean("Client OAuth")
    # module_amr_auto_login = fields.Boolean("Auto Login OAuth")

    @api.depends("amr_token_algorithm")
    def _compute_amr_token_using_secret(self):
        for record in self:
            record.amr_token_using_secret = record.amr_token_algorithm == "HS256"

    # will remove
    module_amr_token_oauth = fields.Boolean("Token OAuth")

    def action_create_public_key(self):
        self.env['amr.token.helper'].sudo().create_public_key(self.amr_token_public_key_algorithm)
