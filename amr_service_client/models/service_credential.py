# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ServiceCredential(models.Model):
    _name = "service.credential"
    _description = "Credential"

    name = fields.Char(required=True)
    source = fields.Selection(
        [
            ("database", "Database"),
            ("file_path", "File Path"),
            ("env_json", "Environment JSON"),
            ("env_path", "Environment Path"),
            ("config_path", "Config Path"),
            ("system_parameter_json", "System Parameter JSON"),
            ("system_parameter_path", "System Parameter Path"),
        ],
        required=True,
    )
    reference = fields.Char()
    credential_json = fields.Text()
    scopes = fields.Char(help="Comma-separated scopes")

    def get_credential_provider(self):
        return self.env["service.credential.loader"].get_credential_provider(self)

    def action_config_credential(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Config Credential",
            "res_model": "service.credential.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_endpoint_id": self.id,
            }
        }

    def action_test_credential(self):
        self.ensure_one()
        try:
            provider = self.get_credential_provider()
            provider.test_credential()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Success",
                    "message": f"Credential {self.name} is valid",
                    "type": "success",
                }
            }
        except Exception as e:
            _logger.exception(f"Credential {self.name} is invalid: {e}")
            raise UserError(f"Credential is invalid: {e}")
