# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    amr_service_client_sentry_mode = fields.Selection([
        ('all', 'All'), ('error', 'Error'), ('selected', 'Selected'), ('none', 'None'),
    ], string='Sentry reporting', default='none',
       config_parameter='amr_service_client.sentry_mode',
       help='All: successes and errors. Error: errors only. Selected: errors for opted-in clients. None: disabled.')
