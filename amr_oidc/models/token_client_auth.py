# -*- coding: utf-8 -*-

import base64
import binascii
import json
import re
from urllib.parse import parse_qsl, unquote_to_bytes

from odoo import api, fields, models
from odoo.http import request
from werkzeug.exceptions import Unauthorized
from werkzeug.wrappers import Response


class OidcClientAuthenticationMethod(models.Model):
    _inherit = "oidc.client"

    authentication_method = fields.Selection(selection_add=[
        ("client_secret_basic", "Client Secret Basic"),
    ])


class TokenHelperClientAuth(models.AbstractModel):
    _inherit = "amr.oidc.helper"

    @api.model
    def _invalid_client(self, basic=False):
        payload = {
            "error": "invalid_client",
            "error_description": "Client authentication failed.",
        }
        headers = {"WWW-Authenticate": "Basic"} if basic else None
        response = Response(
            response=json.dumps(payload), status=401,
            content_type="application/json; charset=utf-8", headers=headers,
        )
        raise Unauthorized(response=response)

    @api.model
    def _authenticate_token_client(self):
        http = request.httprequest
        query = http.args
        if any(key in query for key in ("client_id", "client_secret")):
            self._invalid_client(basic=bool(http.headers.get("Authorization", "").lower().startswith("basic ")))

        auth = http.headers.get("Authorization")
        basic_values = None
        if auth:
            if not auth.lower().startswith("basic "):
                self._invalid_client()
            try:
                encoded = auth.split(None, 1)[1]
                decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
                if ":" not in decoded:
                    raise ValueError()
                client_id, secret = decoded.split(":", 1)
                for component in (client_id, secret):
                    if re.search(r"%(?![0-9A-Fa-f]{2})", component):
                        raise ValueError()
                basic_values = tuple(unquote_to_bytes(component.replace("+", " ")).decode("utf-8") for component in (client_id, secret))
            except (ValueError, UnicodeDecodeError, binascii.Error, IndexError):
                self._invalid_client(basic=True)

        if http.mimetype == "application/x-www-form-urlencoded":
            form = http.form
            body_has_credentials = any(key in form for key in ("client_id", "client_secret"))
            if not body_has_credentials:
                body = http.get_data(cache=True).decode("utf-8")
                body_has_credentials = any(
                    key in ("client_id", "client_secret")
                    for key, _value in parse_qsl(body, keep_blank_values=True)
                )
            if body_has_credentials:
                self._invalid_client(basic=basic_values is not None)

        if basic_values is None:
            self._invalid_client(basic=not auth)
        client_id, secret = basic_values
        client = self.env["oidc.client"].sudo().search(
            [("client_id", "=", client_id), ("active", "=", True)], limit=1
        )
        method = client.authentication_method if client else None
        accepted = {"client_secret", "client_secret_basic"}
        try:
            if method not in accepted:
                raise ValueError("Invalid credentials")
            client.check_credentials(secret)
        except (ValueError, TypeError):
            self._invalid_client(basic=True)
        return client

    @api.model
    def oidc_token(self, grant_type=None, **kwargs):
        self._authenticate_token_client()
        return super(TokenHelperClientAuth, self).oidc_token(grant_type=grant_type, **kwargs)
