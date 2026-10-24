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
            _logger.error("Credential test failed (exception_type=%s)", type(e).__name__)
            raise UserError(f"Credential is invalid: {e}")

    def sanitize_headers(self, headers_dict):
        """
        Fungsi untuk membersihkan header response dari data sensitif.
        """
        if not headers_dict:
            return headers_dict

        # Daftar key header yang dianggap sensitif dan harus disamarkan
        sensitive_keys = [
            'authorization', 'set-cookie', 'cookie',
            'x-auth-token', 'x-api-key', 'www-authenticate', 'token'
        ]

        # Buat salinan dictionary agar data asli tidak berubah
        filtered_headers = {}
        for key, value in headers_dict.items():
            # Cek apakah nama header termasuk sensitif (case-insensitive)
            if key.lower() in sensitive_keys:
                filtered_headers[key] = "[REDACTED]"
            else:
                filtered_headers[key] = value

        return filtered_headers

    def sanitizer_request_context(self, request_context):
        if request_context:
            request_context['headers'] = self.sanitize_headers(request_context.get('headers', None))

        return request_context
