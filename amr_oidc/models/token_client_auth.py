# -*- coding: utf-8 -*-

import base64
import binascii
import json
import re
from urllib.parse import parse_qsl, unquote_to_bytes

from odoo import api, fields, models
from odoo.http import request
from werkzeug.exceptions import BadRequest, Unauthorized
from werkzeug.wrappers import Response


_TOKEN_PARAMETERS = ("client_id", "client_secret", "grant_type")


def _form_pairs(raw, parsed=None):
    if raw:
        if isinstance(raw, bytes):
            text = raw.decode("ascii")
        else:
            text = raw.encode("ascii").decode("ascii")
        if re.search(r"%(?![0-9A-Fa-f]{2})", text):
            raise ValueError()
        return parse_qsl(
            text, keep_blank_values=True, strict_parsing=True,
            encoding="utf-8", errors="strict",
        )
    if parsed is None:
        return []
    pairs = []
    for key in parsed.keys():
        values = parsed.getlist(key) if hasattr(parsed, "getlist") else [parsed.get(key)]
        pairs.extend((key, value) for value in values)
    return pairs


class OidcClientAuthenticationMethod(models.Model):
    _inherit = "oidc.client"

    authentication_method = fields.Selection(selection_add=[
        ("client_secret_basic", "Client Secret Basic"),
        ("client_secret_post", "Client Secret Post"),
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
        status = 401 if basic else 400
        response = Response(
            response=json.dumps(payload), status=status,
            content_type="application/json; charset=utf-8", headers=headers,
        )
        error = Unauthorized if basic else BadRequest
        raise error(response=response)

    @api.model
    def _invalid_request(self):
        response = Response(
            response=json.dumps({
                "error": "invalid_request",
                "error_description": "Malformed token request.",
            }),
            status=400,
            content_type="application/json; charset=utf-8",
        )
        raise BadRequest(response=response)

    @api.model
    def _authenticate_token_client(self):
        http = request.httprequest
        try:
            query_pairs = _form_pairs(getattr(http, "query_string", b""), http.args)
        except (UnicodeDecodeError, ValueError):
            self._invalid_request()
        if any(key in _TOKEN_PARAMETERS for key, _value in query_pairs):
            self._invalid_request()
        if (http.method != "POST" or
                http.mimetype != "application/x-www-form-urlencoded"):
            self._invalid_request()

        header_values = http.headers.getlist("Authorization") if hasattr(http.headers, "getlist") else []
        if len(header_values) > 1:
            self._invalid_request()
        auth = header_values[0] if header_values else http.headers.get("Authorization")
        basic_values = None
        if header_values or auth:
            auth_parts = auth.strip().split() if auth is not None else []
            if not auth_parts or auth_parts[0].lower() != "basic":
                self._invalid_request()
            if "," in auth or ";" in auth:
                self._invalid_request()
            if len(auth_parts) > 2 and any(part.lower() == "basic" for part in auth_parts[2:]):
                self._invalid_request()
            if len(auth_parts) == 1:
                self._invalid_client(basic=True)
            if len(auth_parts) != 2:
                self._invalid_client(basic=True)
            try:
                decoded = base64.b64decode(auth_parts[1], validate=True).decode("ascii")
                if ":" not in decoded:
                    raise ValueError()
                client_id, secret = decoded.split(":", 1)
                for component in (client_id, secret):
                    if re.search(r"%(?![0-9A-Fa-f]{2})", component):
                        raise ValueError()
                basic_values = tuple(
                    unquote_to_bytes(component.replace("+", " ")).decode("utf-8")
                    for component in (client_id, secret)
                )
            except (ValueError, UnicodeDecodeError, binascii.Error, IndexError):
                self._invalid_client(basic=True)

        if http.mimetype == "application/x-www-form-urlencoded":
            body = http.get_data(cache=True)
            try:
                form_pairs = _form_pairs(body, None if body else http.form)
            except (UnicodeDecodeError, ValueError):
                self._invalid_request()
            for name in _TOKEN_PARAMETERS:
                if sum(1 for key, _value in form_pairs if key == name) > 1:
                    self._invalid_request()
            body_has_credentials = any(
                key in ("client_id", "client_secret") for key, _value in form_pairs
            )
            if body_has_credentials:
                if basic_values is not None:
                    self._invalid_request()
                client_id = next((value for key, value in form_pairs if key == "client_id"), None)
                secret = next((value for key, value in form_pairs if key == "client_secret"), None)
                client = self.env["oidc.client"].sudo().search(
                    [("client_id", "=", client_id), ("active", "=", True)], limit=1
                )
                if (not client or not client.is_confidential or
                        client.authentication_method != "client_secret_post"):
                    self._invalid_client()
                try:
                    client.check_credentials(secret)
                except (ValueError, TypeError):
                    self._invalid_client()
                return client

        if basic_values is None:
            self._invalid_client()
        client_id, secret = basic_values
        client = self.env["oidc.client"].sudo().search(
            [("client_id", "=", client_id), ("active", "=", True)], limit=1
        )
        method = client.authentication_method if client else None
        accepted = {"client_secret", "client_secret_basic"}
        try:
            if not client or not client.is_confidential or method not in accepted:
                raise ValueError("Invalid credentials")
            client.check_credentials(secret)
        except (ValueError, TypeError):
            self._invalid_client(basic=True)
        return client

    @api.model
    def oidc_token(self, grant_type=None, **kwargs):
        self._authenticate_token_client()
        result = super(TokenHelperClientAuth, self).oidc_token(grant_type=grant_type, **kwargs)
        if result.get("error") == "unsupported_grant_type":
            result["error_description"] = "Grant type is not supported."
        return result
