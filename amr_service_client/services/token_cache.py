# -*- coding: utf-8 -*-

import logging

from odoo import api, models, tools
from odoo.exceptions import UserError
from odoo import models

from datetime import datetime

_logger = logging.getLogger(__name__)

TOKEN_CACHE = {}


class ServiceTokenCache(models.AbstractModel):
    _name = "service.token.cache"

    @api.model
    def get_cache(self, key, ):
        token_data = TOKEN_CACHE.get(key)
        if token_data and token_data.get("expires_at") > datetime.now():
            return token_data.get("token")
        TOKEN_CACHE.pop(key, None, )
        return None

    @api.model
    def set_cache(self, key, token, expires_in):
        expires_at = datetime.now() + tools.timedelta(seconds=expires_in)
        TOKEN_CACHE[key] = {"token": token, "expires_at": expires_at, }
