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

    active = fields.Boolean(default=True)
    name = fields.Char(help="Authorized Party (client yang meminta token, umum di OpenID Connect)")
    user_id = fields.Many2one('res.users', help="machine user or bot", default=1)
    client_id = fields.Char(
        "Client ID",
        help="Use web.base.url + redirect_path as redirect_uri if redirect_uri is not set."
    )
    client_email = fields.Char()
    client_type = fields.Selection([
        ("machine", "Machine"),
        ("mobile", "Mobile"),
        ("web", "Web"),
        ("atm", "ATM"),
        ("cdm", "CDM"),
    ], default="machine")
    client_secret = fields.Char(groups="base.group_erp_manager")
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

    def check_credentials(self, client_secret):
        self.ensure_one()
        # todo next using hash method to check secret like user credentials
        if client_secret != self.client_secret:
            raise ValueError("Invalid secret")
        return True

    def validate_redirect_uri(self, redirect_uri):
        if self.redirect_path:
            path = REDIRECT_MODE.get(self.redirect_path)
            if not path or not self.web_base_url:
                return False
            callback = self.web_base_url + path
            return not redirect_uri or redirect_uri == callback
        if not self.redirect_uri or not redirect_uri:
            return False
        parsed = urlparse(redirect_uri)
        return bool(parsed.scheme and parsed.netloc
                    and redirect_uri in self.redirect_uri.splitlines())

    @api.model
    def client_auth(self, token):
        try:
            decoded = base64.b64decode(token).decode()
            client_id, client_secret = decoded.split(':', 1)
            # sudo: preserve source credential lookup; access review deferred.
            client = self.sudo().search([('client_id', '=', client_id)], limit=1)
            if client.client_secret == client_secret:
                return client
            else:
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
        return self.env['amr.token.helper'].validate(token, audience=audience)

    def validate_refresh_token(self, token):
        return self.env['oidc.refresh.token'].validate_token(token, self.client_id)

    def export_service_account(self, algorithm):
        self.ensure_one()
        key_pair = self.env['amr.token.helper'].generate_key(algorithm)
        result = self.env['amr.token.helper'].openid_configuration()
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
