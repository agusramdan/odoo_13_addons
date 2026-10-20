# -*- coding: utf-8 -*-

from odoo import models, fields
import json
import logging

_logger = logging.getLogger(__name__)


class ServiceEndpointTestWizard(models.TransientModel):
    _name = "service.endpoint.test.wizard"
    _description = "Service Endpoint Test"

    endpoint_id = fields.Integer()
    endpoint_model = fields.Char()
    method = fields.Selection(
        [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH"), ("DELETE", "DELETE"), ],
        required=True, default="GET",
    )
    path = fields.Char(required=True, default="/api/test/connection/machine")
    params = fields.Text()
    headers = fields.Text()
    payload = fields.Text()

    response_status = fields.Integer(readonly=True,)
    response_body = fields.Text(readonly=True,)
    success = fields.Boolean(readonly=True,)

    def action_test(self):
        self.ensure_one()
        params = json.loads(self.params) if self.params else None
        headers = json.loads(self.headers) if self.headers else None
        payload = json.loads(self.payload) if self.payload else None
        endpoint = self.env[self.endpoint_model].browse(self.endpoint_id)
        client = self.env["service.client"].get_service_client(endpoint, credential=None)
        self.response_status = 0
        try:
            response = client.call(
                method=self.method,
                path=self.path,
                params=params,
                headers=headers,
                payload=payload,
            )
            self.response_status = response.status_code
            response.raise_for_status()
            self.response_body = json.dumps(response.json(), indent=2)
            self.success = True
        except Exception as e:
            _logger.exception("Error testing service endpoint: %s", e)
            self.response_body = str(e)
            self.success = False

        return {
            "type": "ir.actions.act_window",
            "name": self._description,
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context
        }
