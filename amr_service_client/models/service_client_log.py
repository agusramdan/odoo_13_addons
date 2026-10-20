# -*- coding: utf-8 -*-

import json
import requests
import logging
import traceback

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ServiceClientLog(models.Model):
    _name = "service.client.log"
    _description = "Integration Log"
    _order = "id desc"

    state = fields.Selection([('outgoing', 'Outgoing'), ('done', 'Done'), ('error', 'Error')])
    endpoint_id = fields.Many2one("service.endpoint")
    credential_id = fields.Many2one("service.credential")
    client_id = fields.Many2one("service.client")
    request_context = fields.Text()
    response = fields.Text()

    def dispatch_send(self):
        # asynchronous mode
        self.send()
        return self

    def send(self):
        response_text = None
        try:
            client = self.client_id.get_service_client(self.endpoint_id, self.credential_id)
            request_context = json.loads(self.request_context)
            request_context["headers"] = self.endpoint_id.request_headers_default(request_context.get("headers"))
            request_context = client.provider.authenticate(request_context, self.endpoint_id.audience)
            response = requests.request(**request_context)
            response.raise_for_status()
            state = 'done'
            response_text = response.text
        except requests.RequestException as e:
            _logger.error("Failed to send %s ", self.request_context)
            response_text = getattr(e.response, 'text', '') + str(e)
            state = 'error'
        except Exception:
            # saat error lakukan log agar bisa send ullang
            state = 'error'
            response_text = traceback.format_exc()

        self.write({
            "state": state,
            "response": response_text
        })
        return self
