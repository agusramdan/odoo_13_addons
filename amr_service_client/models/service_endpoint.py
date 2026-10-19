# -*- coding: utf-8 -*-

import logging
import os

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import config
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)


class ServiceEndpointMixin(models.AbstractModel):
    _name = "service.endpoint.mixin"

    base_url = fields.Char(compute='_compute_base_url')
    url = fields.Char(compute='_compute_base_url')
    base_url_value = fields.Char()
    source = fields.Selection(
        [
            ("value", "Value"),
            ("env", "OS Environment"),
            ("config", "Odoo Config"),
            ("config_parameter", "System Parameter"),
        ],
        required=True, default="value"
    )
    content_type_default = fields.Selection(
        [
            ("text/plain", "text/plain"),
            ("application/json", "application/json"),
        ],
        required=True, default="text/plain"
    )
    config_param_name = fields.Char()
    base_path = fields.Char(help="/api/v1")
    audience = fields.Char()
    credential_id = fields.Many2one("service.credential")
    timeout = fields.Integer(default=30, )
    active = fields.Boolean(default=True, )
    active_log = fields.Boolean()

    def open_config_parameter(self):
        param = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', self.config_param_name)],
            limit=1
        ) or self.env['ir.config_parameter'].sudo().create({'key': self.config_param_name, 'value': ""})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.config_parameter',
            'res_id': param.id,
            'view_mode': 'form',
        }

    def get_value_config_param(self, config_param_name=None, value_without_config_param=None):
        config_param_name = config_param_name or self and self.config_param_name
        if config_param_name:
            return self.env['ir.config_parameter'].sudo().get_param(config_param_name) or None
        else:
            return value_without_config_param

    @api.depends('base_url_value', 'config_param_name', 'source', 'base_path')
    def _compute_base_url(self):
        for rec in self:
            url = None
            base_url = False
            endpoint = False
            if "value" == rec.source:
                url = rec.base_url_value
            elif rec.config_param_name:
                if "env" == rec.source:
                    url = os.getenv(rec.config_param_name)
                elif "config" == rec.source:
                    url = config.get(rec.config_param_name)
                elif "config_parameter" == rec.source:
                    url = rec.get_value_config_param(config_param_name=rec.config_param_name)
            if url:
                try:
                    parsed = urlparse(url)
                    base_path = (self.base_path or "").rstrip("/")
                    if base_path in ["", "/"]:
                        base_path = None
                    base_path = base_path or parsed.path or ""
                    if base_path and not base_path.startswith('/'):
                        base_path = f"/{base_path}"
                    if parsed.scheme and parsed.netloc:
                        base_url = f"{parsed.scheme}://{parsed.netloc}"
                        endpoint = f"{parsed.scheme}://{parsed.netloc}{base_path}".rstrip("/")
                    else:
                        _logger.info("Parse url %s , %s ",url, parsed)
                        endpoint = base_url = url
                except:
                    _logger.error("Parse url %s", url)
                    endpoint = base_url = url

            rec.base_url, rec.url = base_url, endpoint

    def get_base_url(self):
        return (self.base_url or "").rstrip("/")

    def get_path_url(self):
        return (self.base_path or "").rstrip("/")

    def get_url(self, path=None):
        if path is None or path is False:
            return self.url
        base_url = (self.base_url or "").rstrip("/")
        if path in ["", "/"]:
            return base_url
        base_path = (self.base_path or "").rstrip("/")
        path = path.rstrip("/")
        if not path and not base_path:
            return base_url

        if base_path:
            if path and not path.startswith('/'):
                path = f"{base_path}/{path}"
            elif not path:
                path = base_path

        _logger.info("path %s .", path)
        if path.startswith('/'):
            return f"{base_url}{path}"
        else:
            return f"{base_url}/{path}"

    def request_headers_default(self, headers=None):
        request_headers = {}
        # request_headers.update(auth_headers)
        request_headers.update(headers or {})
        # Content - Type: text / plain
        if self:
            request_headers.setdefault("Content-Type", self.content_type_default or "text/plain")
        else:
            request_headers.setdefault("Content-Type", "text/plain")
        request_headers.setdefault("Accept", "application/json")
        return request_headers

    def action_test_connection(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Test Endpoint",
            "res_model": "service.endpoint.test.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_endpoint_id": self.id,
                "default_endpoint_model": self._name,
            }
        }

    def get_service_client(self, credential=None):
        return self.env['service.client'].get_service_client(self, credential=credential or self.credential_id)

    def get_remote_object(self, model_name, credential=None, **kwargs):
        return self.env['service.client'].get_remote_object(
            self, model_name, credential=credential or self.credential_id, **kwargs
        )


class ServiceEndpoint(models.Model):
    _name = "service.endpoint"
    _inherit = 'service.endpoint.mixin'

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True, )
