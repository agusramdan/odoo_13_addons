# -*- coding: utf-8 -*-

import base64
import logging
import jwt
from odoo import api, fields, models
from odoo.http import request
from psycopg2 import IntegrityError
import jwt
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)

class TokenHelper(models.AbstractModel):
    _inherit = 'amr.oidc.helper'

    # helper will call from Controller
    @api.model
    def get_bearer_token(self):
        auth = request.httprequest.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return None
        data = auth.split(" ", 1)
        return data[1] if len(data) > 1 else None

    @api.model
    def get_basic_auth(self):
        auth = request.httprequest.headers.get('Authorization')
        if not auth:
            return None, None

        try:
            scheme, encoded = auth.split(' ', 1)
            if scheme.lower() != 'basic':
                return None, None

            decoded = base64.b64decode(encoded).decode('utf-8')
            return decoded.split(':', 1)
        except Exception:
            return None, None


    @api.model
    def oidc_introspect(self, **kwargs):
        return {'active': False}

    @api.model
    def oidc_profile(self, **kwargs):
        return {'active': False}
