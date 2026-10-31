# -*- coding: utf-8 -*-

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ExternalServerSync(models.Model):
    _name = 'external.server.sync'
    _inherit = 'service.endpoint.mixin'
    _description = 'External Server Sync Configuration'

    active = fields.Boolean(default=True)
    name = fields.Char()
    app_name = fields.Char("Application Name")
    authorized_party = fields.Char(
        "Authorized Party",
        help="Fungsinya adalah mengidentifikasi OAuth 2.0 Client ID yang sebenarnya menerima ID Token. "
             "Claim ini bersifat opsional dan biasanya hanya muncul ketika pihak yang meminta token "
             "berbeda dengan nilai aud (Audience)."
             "Value ini wajib di isi bila ingin menerima data event"
    )
    audience = fields.Char('Audience')

    def get_application_name(self):
        return self.app_name

    def get_endpoint_url(self):
        return self.base_url

    def create_remote_model(self, external_model, **kwargs):
        return self.env['service.client'].get_remote_object(self, external_model, **kwargs)
