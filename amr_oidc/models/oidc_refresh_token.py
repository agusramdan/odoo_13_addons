# -*- coding: utf-8 -*-

import logging
import time
import uuid
from datetime import timedelta

import jwt
from jwt import InvalidTokenError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class OidcRefreshToken(models.Model):
    _name = 'oidc.refresh.token'
    _description = "JWT Refresh Token"

    @api.model
    def get_expires_in(self):
        # sudo: preserve source configuration read; refresh policy deferred.
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.expires_in', 60 * 60 * 24))

    @api.model
    def get_secret(self):
        # sudo: preserve source configuration read; secret handling unchanged.
        return self.env['ir.config_parameter'].sudo().get_param('amr_token.secret')

    @api.model
    def get_issuer(self):
        # sudo: preserve source configuration read; refresh policy deferred.
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url')

    @api.model
    def get_algorithm(self):
        return 'HS256'

    token = fields.Char(required=True, index=True)
    user_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="cascade",
    )
    expires_at = fields.Datetime(required=True)
    revoked = fields.Boolean(default=False)

    _sql_constraints = [
        ("token_unique", "unique(token)", "Refresh token must be unique")
    ]

    @staticmethod
    def generate_token():
        return str(uuid.uuid4())

    @api.model
    def create_refresh_token(self, user, **kw):
        token = self.generate_token()
        expires_in = 60 * 60 * 24 * 14
        expire = int(time.time()) + expires_in
        expires_at = fields.Datetime.now() + timedelta(seconds=expires_in)

        self.create({
            "token": token,
            "user_id": user.id,
            "expires_at": expires_at,
        })
        payload = {
            'token': token,
            'data': f"{user.id}-{user.email}-{time.time()}-{self.env.cr.dbname}",
            'iss': self.get_issuer(),
            'exp': expire,
        }
        aud = kw.get('aud')
        resource = kw.get('resource')
        if resource:
            payload['aud'] = resource
        elif aud:
            payload['aud'] = aud
        return jwt.encode(
            payload,
            self.get_secret(),
            algorithm=self.get_algorithm(),
        )

    @api.model
    def _validate_token(self, token, audience, options=None):
        try:
            options = options or {"require": ["exp", "iss", "aud"]}
            payload = jwt.decode(
                token,
                self.get_secret(),
                issuer=self.get_issuer(),
                audience=audience,
                algorithms=[self.get_algorithm()],
                options=options,
            )
            token = payload.get("token")
            if token:
                # sudo: preserve source refresh lookup; refresh policy deferred.
                rec = self.sudo().search([
                    ("token", "=", token),
                    ("revoked", "=", False),
                    ('expires_at', '>', fields.Datetime.now())
                ], limit=1)
                if rec:
                    return payload
        # except InvalidIssuerError:
        #     pass
        # except InvalidAudienceError:
        #     pass
        # except ExpiredSignatureError:
        #     pass
        except InvalidTokenError:
            pass
        return None
