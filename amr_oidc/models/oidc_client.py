# -*- coding: utf-8 -*-

import base64
import logging
from datetime import timedelta
from urllib.parse import urlparse

import jwt

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

REDIRECT_MODE = {
   'auth_oauth_oidc': '/auth_oauth/oidc',
   'auth_oauth_oea': '/auth_oauth/oea',
}


class OidcClient(models.Model):
    _name = 'oidc.client'
    _description = 'OIDC Client'
    _sql_constraints = [
        ('client_id_unique', 'unique(client_id)', 'Client ID must be unique.'),
    ]

    active = fields.Boolean(default=True)
    is_confidential = fields.Boolean(default=True)
    name = fields.Char(help="Authorized Party (client yang meminta token, umum di OpenID Connect)")
    user_id = fields.Many2one('res.users', help="machine user or bot", default=1)
    client_id = fields.Char(
        "Client ID",
        help="Use web.base.url + redirect_path as redirect_uri if redirect_uri is not set.",
        required=True,
    )
    client_email = fields.Char()
    client_type = fields.Selection([
        ("machine", "Machine"),
        ("mobile", "Mobile"),
        ("web", "Web"),
        ("atm", "ATM"),
        ("cdm", "CDM"),
    ], default="machine")
    client_secret_hash = fields.Char(groups="amr_oidc.group_provider_admin", copy=False)
    authentication_method = fields.Selection([
        ("client_secret", "Client Secret"),
        ("private_key_jwt", "Private Key JWT"),
        ("tls_client_auth", "TLS Client Auth"),
    ], default="client_secret")
    web_base_url = fields.Char()
    redirect_uri = fields.Text()
    redirect_path = fields.Selection(
        selection=list(REDIRECT_MODE.items()),
        default='auth_oauth_oidc'
    )
    authorization_ids = fields.One2many('oidc.authorization.code', 'client_id')
    key_ids = fields.One2many('oidc.client.key', 'client_id')

    @api.constrains('client_id')
    def _check_client_id_not_blank(self):
        from odoo.exceptions import ValidationError

        for client in self:
            if not client.client_id or not client.client_id.strip():
                raise ValidationError("Client ID is required.")

    def check_credentials(self, client_secret):
        self.ensure_one()
        context = self.env["res.users"]._crypt_context()
        # sudo: read only the verifier; field access is restricted to provider admins.
        verifier = self.sudo().client_secret_hash
        if not client_secret or not verifier:
            raise ValueError("Invalid secret")
        try:
            if context.identify(verifier) != "pbkdf2_sha512":
                raise ValueError("Invalid secret")
            if not context.verify(client_secret, verifier):
                raise ValueError("Invalid secret")
        except (ValueError, TypeError):
            raise ValueError("Invalid secret")
        return True

    def validate_redirect_uri(self, redirect_uri):
        if self.redirect_path:
            return True

        if not self.redirect_uri or not redirect_uri:
            return True

        parsed = urlparse(redirect_uri)

        if not parsed.scheme:
            _logger.error("Error %s parsed.scheme. %s", parsed.scheme, redirect_uri)
            return False

        if not parsed.netloc:
            _logger.error("Error %s parsed.netloc. %s", parsed.netloc, redirect_uri)
            return False
        # client.redirect_uri_ids
        # .mapped('uri')
        allowed_uris = (self.redirect_uri.splitlines() or []) + [self.redirect_uri]
        normalized_redirect = f'{parsed.scheme}://{parsed.netloc}{parsed.path}'.strip()

        for allowed_uri in allowed_uris:

            allowed_parsed = urlparse(allowed_uri)

            normalized_allowed = (
                f'{allowed_parsed.scheme}://'
                f'{allowed_parsed.netloc}'
                f'{allowed_parsed.path}'
            ).strip()

            if normalized_allowed == normalized_redirect:
                return True
            _logger.error("Error [%s] != [%s]", normalized_redirect, normalized_allowed)

        _logger.error("Error %s.", normalized_redirect)

        return False

    @api.model
    def client_auth(self, token):
        try:
            decoded = base64.b64decode(token).decode()
            client_id, client_secret = decoded.split(':', 1)
            # sudo: preserve source credential lookup; access review deferred.
            client = self.sudo().search([
                ('client_id', '=', client_id), ('active', '=', True)
            ], limit=1)
            try:
                client.check_credentials(client_secret)
                return client
            except ValueError:
                return None
        except:
            return None

    def create_authorization_code(self, redirect_uri=None, scope=''):
        if self.redirect_path:
            redirect_uri = self.web_base_url + REDIRECT_MODE.get(self.redirect_path)
        else:
            redirect_uri = redirect_uri or self.redirect_uri
        # sudo: preserve source code creation; code-record policy deferred.
        return self.env['oidc.authorization.code'].sudo().create({
            'client_id': self.client_id,
            'user_id': self.env.user.id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'expired_at': fields.Datetime.now() + timedelta(minutes=5),
        })

    def create_access_token(self, redirect_uri=None, scope='', **kw):
        if self.redirect_path:
            redirect_uri = self.web_base_url + REDIRECT_MODE.get(self.redirect_path)
        else:
            redirect_uri = redirect_uri or self.redirect_uri

        return self.env.user.create_access_token(
            scope=scope, audience=self.client_id, redirect_uri=redirect_uri
        )

    def validate_token(self, token):
        client = self
        if not client:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                    "verify_aud": False,
                    "verify_iss": False,
                }
            )
            # sudo: preserve source audience lookup; access review deferred.
            client = self.sudo().search([('client_id', '=', payload.get('aud'))], limit=1)
        audience = client.client_id
        return self.env['amr.oidc.helper'].validate(token, audience=audience)

    def validate_refresh_token(self, token):
        return self.env['oidc.refresh.token'].validate_token(token, self.client_id)

    def export_service_account(self, algorithm):
        self.ensure_one()
        key_pair = self.env['amr.oidc.helper'].generate_key(algorithm)
        result = self.env['amr.oidc.helper']._service_account_endpoint_defaults()
        # "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        # "token_uri": "https://oauth2.googleapis.com/token",
        # "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        # "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxx%40xxxx.iam.gserviceaccount.com",
        # "universe_domain": "googleapis.com"

        return {
            "type": "service_account",
            "client_id": self.client_id,
            "client_email": self.client_email,
            "auth_uri": result['authorization_endpoint'],
            "token_uri": result['token_endpoint'],
            "issuer": result['issuer'],
            "private_key_id": key_pair['kid'],
            "private_key": key_pair['private_key'],
            "public_key": key_pair['public_key'],
            "scope": "",
            "auth_method": "private_key_jwt",
            "algorithm": key_pair['algorithm'],
        }

    def action_export_service_account(self):
        self.ensure_one()
        context = {
            'default_client_id': self.id
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'oidc.service.account.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
