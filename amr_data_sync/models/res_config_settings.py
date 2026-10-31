# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    amr_date_update_option = fields.Selection([
        ('secure', 'Secure'),
        ('secure_log', 'Secure Log'),
        ('not_secure', 'Not Secure'),
    ], "Security Op.", config_parameter='amr_data_sync.date_update_security_option', default='secure_log')
