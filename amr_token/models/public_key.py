# -*- coding: utf-8 -*-

import logging
import os
import jwt

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from jwt import InvalidTokenError
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class PublicKey(models.Model):
    _name = "amr.public.key"
    _description = "OIDC JWKS Key"

    name = fields.Char()
    kid = fields.Char(required=True, index=True)
    source = fields.Selection(
        [
            ("database", "Database"),
            ("hsm", "HSM"),
            ("file_path", "File Path"),
            ("env_pem", "Environment Pem"),
            ("env_path", "Environment Path"),
            ("config_path", "Config Path"),
            ("config_pem", "Config pem"),
            ("system_parameter_pem", "System Parameter pem"),
            ("system_parameter_path", "System Parameter Path"),
        ],
        required=True,
        default="database",
    )
    hsm_key_id = fields.Char()
    algorithm = fields.Selection(
        [
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
    )
    public_key = fields.Text(required=True)
    # Optional (development/internal only) in the pinned source.
    reference = fields.Char()
    private_key = fields.Text()
    active = fields.Boolean(default=True)
    is_signing = fields.Boolean(default=False)

    created_at = fields.Datetime(default=fields.Datetime.now)
    expires_at = fields.Datetime()

    @api.constrains('public_key')
    def _check_public_key(self):
        for rec in self:
            try:
                serialization.load_pem_public_key(
                    rec.public_key.encode()
                )
            except (ValueError, UnsupportedAlgorithm):
                raise ValidationError("Invalid public key.")

    def load_pem_public_key(self):
        from cryptography.hazmat.primitives import serialization
        public_key = serialization.load_pem_public_key(self.public_key.encode('utf-8'))
        return public_key

    def get_private_key(self):
        record = self
        source = record.source
        if source == "database":
            return record.private_key
        elif source == "env_pem":
            return os.getenv(record.reference)
        elif source == "config_pem":
            return config.get(record.reference)
        elif source == "system_parameter_pem":
            return self.env["ir.config_parameter"].sudo().get_param(record.reference)
        elif source == "file_path":
            return self._read_file(record.reference)

        if source == "env_path":
            path = os.getenv(record.reference)
        elif source == "config_path":
            path = config.get(record.reference)
        elif source == "system_parameter_path":
            path = self.env["ir.config_parameter"].sudo().get_param(record.reference)
        else:
            raise ValueError(f"Unsupported source: {source}")

        return self._read_file(path)

    @api.model
    def _read_file(self, path):
        if not path:
            raise ValueError("Private key path not configured")

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @api.model
    def get_jwks(self):
        list_key = []
        for key in self.search([('active', '=', True)]):
            public_key = key.load_pem_public_key()
            if key.algorithm in ['ES256', 'ES256K', 'ES384', 'ES512']:
                jwk_dict = ECAlgorithm.to_jwk(public_key, as_dict=True)
            else:
                jwk_dict = RSAAlgorithm.to_jwk(public_key, as_dict=True)
            if key.is_signing:
                jwk_dict['use'] = "sig"
            jwk_dict['kid'] = key.kid
            jwk_dict['alg'] = key.algorithm
            list_key.append(jwk_dict)
        return list_key

    def generate_token(self, payload):
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm, headers={'kid': self.kid})

    def validate_token(self, token, issuer=None, audience=None, options=None):
        try:
            options = options or {"verify_aud": False}
            return jwt.decode(token, self.public_key, issuer=issuer, audience=audience or None, algorithms=[self.algorithm], options=options)
        except InvalidTokenError as e:
            _logger.warning("Failed to validate token with public key: %s", e)
            raise

    def action_generate_key(self):
        data = self.env['amr.token.helper'].generate_key(self.algorithm)
        data.pop('source', None)
        self.write(data)
