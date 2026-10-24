# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    service_client_sentry_mode = fields.Selection([
        ('all', 'All outcomes'), ('error', 'Errors only'),
        ('selected', 'Selected clients only'), ('none', 'Disabled'),
    ], string='Service Client Sentry reporting', default='none',
       config_parameter='amr_service_client.sentry_mode')
