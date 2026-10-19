# -*- coding: utf-8 -*-

from odoo import api, models, tools
from odoo.tools import config
from .providers import (
    NoneAuthProvider,
    ApiKeyProvider,
    BearerProvider,
    BasicProvider,
    GetJWTTokenProvider,
    ClientSecretProvider,
    ServiceAccountProvider,
)


class ServiceAuthFactory(models.AbstractModel):
    _name = "service.auth.factory"
    _description = "Service Authentication Factory"

    PROVIDERS = {
        "none": NoneAuthProvider,
        "get_jwt": GetJWTTokenProvider,
        "api_key": ApiKeyProvider,
        "bearer": BearerProvider,
        "basic": BasicProvider,
        "client_secret": ClientSecretProvider,
        "service_account": ServiceAccountProvider,
    }

    def create_service_auth(self, credential,):
        if not credential:
            return NoneAuthProvider(self.env, credential)
        auth_type = credential.get("type")
        provider_class = self.PROVIDERS.get(auth_type)
        if not provider_class:
            raise ValueError("Unsupported authentication type: %s ." % auth_type)
        return provider_class(self.env, credential)
