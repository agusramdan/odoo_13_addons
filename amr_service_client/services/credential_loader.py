# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.tools import config

import os
import json

from odoo import tools


class ServiceCredentialLoaderDatabase(models.AbstractModel):
    _name = "service.credential.loader.database"

    @api.model
    def load_credential(self, credential):
        result = json.loads(credential.credential_json)
        scope = result.get("scope") or result.get("scopes") or []
        if isinstance(scope, str):
            scope = scope.split()
        if credential.scopes:
            scope.extend(credential.scopes.split())
        result["scope"] = list(set(scope))
        return result


class ServiceCredentialLoaderFilePath(models.AbstractModel):
    _name = "service.credential.loader.file_path"

    @api.model
    def load_credential(self, credential):
        with open(credential.reference, "r", encoding="utf-8") as fp:
            return json.load(fp)


class ServiceCredentialLoaderEnvJson(models.AbstractModel):
    _name = "service.credential.loader.env_json"

    @api.model
    def load_credential(self, credential):
        env_value = os.getenv(credential.reference)
        if not env_value:
            raise ValueError("Environment variable '%s' not found" % credential.reference)

        return json.loads(env_value)


class ServiceCredentialLoaderEnvPath(models.AbstractModel):
    _name = "service.credential.loader.env_path"

    @api.model
    def load_credential(self, credential):
        env_value = os.getenv(credential.reference)
        if not env_value:
            raise ValueError("Environment variable '%s' not found" % credential.reference)

        with open(env_value, "r", encoding="utf-8") as fp:
            return json.load(fp)


class ServiceCredentialLoaderConfigPath(models.AbstractModel):
    _name = "service.credential.loader.config_path"

    @api.model
    def load_credential(self, credential):
        config_path = config.get(credential.reference)
        if not config_path:
            raise ValueError("Config parameter '%s' not found" % credential.reference)

        with open(config_path, "r", encoding="utf-8") as fp:
            return json.load(fp)


class ServiceCredentialLoaderParameterJson(models.AbstractModel):
    _name = "service.credential.loader.system_parameter_json"

    @api.model
    def load_credential(self, credential):
        parameter_value = self.env["ir.config_parameter"].sudo().get_param(credential.reference)
        if not parameter_value:
            raise ValueError("System parameter '%s' not found" % credential.reference)

        return json.loads(parameter_value)


class ServiceCredentialLoaderParameterPath(models.AbstractModel):
    _name = "service.credential.loader.system_parameter_path"

    @api.model
    def load_credential(self, credential):
        parameter_value = self.env["ir.config_parameter"].sudo().get_param(credential.reference)
        if not parameter_value:
            raise ValueError("System parameter '%s' not found" % credential.reference)

        with open(parameter_value, "r", encoding="utf-8") as fp:
            return json.load(fp)


supported = [
    "service_account",
    "client_secret",
    "api_key",
    "bearer",
    "basic",
]


class ServiceCredentialLoader(models.AbstractModel):
    _name = "service.credential.loader"
    _description = "Service Credential Loader"

    def get_credential(self, credential):
        if isinstance(credential, str):
            credential = self.env["service.credential"].search([("name", "=", credential)], limit=1)
            if not credential:
                credential = self.env.ref(credential)
            if not credential:
                raise ValueError("Credential '%s' not found" % credential)
        return credential

    @tools.ormcache("credential.id", "credential.write_date")
    def load_cached(self, credential, ):
        return self.load_credential(credential)

    def load_credential(self, credential):
        if isinstance(credential, str):
            credential = self.env["service.credential"].search([("name", "=", credential)], limit=1)
            if not credential:
                credential = self.env.ref(credential)
            if not credential:
                raise ValueError("Credential '%s' not found" % credential)

        source = credential.source
        model_loader = "service.credential.loader.%s" % source
        if model_loader in self.env:
            credential_data = self.env[model_loader].load_credential(credential)
            self._validate(credential_data)
            return credential_data
        raise ValueError("Unsupported credential source '%s'" % source)

    @api.model
    def _validate(self, credential, ):
        if "type" not in credential:
            raise ValueError("Missing credential type")
        if credential["type"] not in supported:
            raise ValueError("Unsupported credential type")

    def get_credential_provider(self,credential):
        loader = self.env["service.credential.loader"]
        credential_data = loader.load_credential(credential)
        return self.env["service.auth.factory"].create_service_auth(credential_data)
