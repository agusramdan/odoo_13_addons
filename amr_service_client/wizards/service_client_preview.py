# -*- coding: utf-8 -*-

import json

from odoo import api, fields, models


class Preview(models.TransientModel):
    _inherit = "service.client"
    _name = "service_client.preview"
    _description = "Service Client Preview"

    @api.model
    def _get_records(self):
        service_client_id = self._context.get('service_client_id')
        default_res_id = self._context.get('default_res_id')
        if not service_client_id:
            return []
        service_client = self.env['service.client'].browse(int(service_client_id))
        records = self.env[service_client.model_id.model].search([], order="id desc", limit=10)
        records |= records.browse(default_res_id)
        return records.name_get()

    @api.model
    def _get_languages(self):
        return self.env['res.lang'].get_installed()

    @api.model
    def default_get(self, fields):
        result = super(Preview, self).default_get(fields)

        service_client = self._context.get('service_client_id') and self.env['service.client'].browse(
            self._context['service_client_id']) or False
        if 'res_id' in fields and not result.get('res_id'):
            records = self._get_records()
            result['res_id'] = records and records[0][0] or False  # select first record as a Default
        if service_client and 'model_id' in fields and not result.get('model_id'):
            result['model_id'] = service_client.model_id.id
        if service_client and 'preview_lang' in fields and not result.get('preview_lang') and result.get('res_id'):
            result['preview_lang'] = service_client.lang and service_client.generate_email(result['res_id'], ['lang'])[
                'lang'] or service_client._context.get('lang')
        return result

    res_id = fields.Selection(_get_records, 'Sample Document')
    # partner_ids = fields.Many2many('res.partner', string='Recipients')
    # attachment_ids = fields.Many2many(string='Attachments', store=False)
    # preview_lang = fields.Selection(_get_languages, string='service_client Preview Language')
    status_code = fields.Integer()
    send_request = fields.Boolean()
    method = fields.Selection(
        [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH"), ("DELETE", "DELETE"), ],
    )
    path = fields.Char(default="/api/test/connection/machine")
    params = fields.Text()
    headers = fields.Text()
    payload = fields.Text()
    response_text = fields.Text()

    @api.onchange('res_id', 'send_request')
    def on_change_res_id(self):
        if not self.res_id:
            return {}
        # mail_values = {}
        if self._context.get('service_client_id'):
            service_client = self.env['service.client'].browse(self._context['service_client_id'])
            records = self.env[service_client.model_id.model].browse(self.res_id)
            ctx = {}
            eval_context = service_client._get_eval_context()
            eval_context['record'] = records
            request_values = service_client.prepare_request(records, ctx, eval_context)
            # self.name = service_client.name
            self.path = request_values.get('path') or None
            self.method = request_values.get('method') or None
            self.params = json.dumps(request_values.get('params', None))
            self.headers = json.dumps(request_values.get('headers', None))
            self.payload = json.dumps(request_values.get('payload', None))
            if self.send_request:
                client = service_client.get_service_client(
                    service_client.endpoint_id,
                    credential=service_client.credential_id
                )
                self.headers = json.dumps(client.provider.authenticate(request_values).get('headers', None))
                request_values['raise_exception'] = False
                response = client.call(**request_values)
                self.response_text = response.text
                self.status_code = response.status_code
