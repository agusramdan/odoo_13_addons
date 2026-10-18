# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    amr_select_issuer = fields.Selection([
        ('web.base.url', 'Web Base URL'),
    ], "Select Issuer", config_parameter='amr_resource.issuer', default='web.base.url')
    amr_resource_issuer = fields.Char(
        "Issuer",
        compute='_compute_resource_issuer',
    )

    amr_select_audience = fields.Selection([
        ('web.base.url', 'Web Base URL'),
        ('database.uuid', 'Database UUID'),
    ], "Select Audience", config_parameter='amr_resource.audience', default='web.base.url')
    amr_resource_audience = fields.Char(
        "Audience",
        compute='_compute_resource_audience',
    )
    amr_web_base_url_freeze = fields.Boolean(
        string="Freeze",
        config_parameter='web.base.url.freeze',
        help="Prevent Odoo from automatically updating web.base.url."
    )

    module_amr_approval_aggregator = fields.Boolean("Approval Aggregator")

    # Token
    module_amr_oidc = fields.Boolean("OIDC")
    module_amr_oidc_client = fields.Boolean("OIDC Client")
    module_amr_token = fields.Boolean("Token Provider")
    module_amr_oauth = fields.Boolean("Client OAuth")
    module_amr_auto_login = fields.Boolean("Auto Login OAuth")
    module_amr_signature = fields.Boolean("Signature")
    module_amr_esign_pdf = fields.Boolean("E Sign PDF")

    # Integration/Connection to other system
    module_amr_service_client = fields.Boolean("Service Client")
    module_amr_data_push = fields.Boolean("Data Event Push")
    module_amr_data_sync = fields.Boolean("Data Sync")

    module_amr_approval_task_client = fields.Boolean("Approval Task Client")
    module_amr_notification_client = fields.Boolean("Notification Client")

    @api.depends('amr_select_issuer')
    def _compute_resource_issuer(self):
        for record in self:
            if record.amr_select_issuer:
                record.amr_resource_issuer = self.env['ir.config_parameter'].sudo().get_param(record.amr_select_issuer, '')
            else:
                record.amr_resource_issuer = ''

    @api.depends('amr_select_audience')
    def _compute_resource_audience(self):
        for record in self:
            if record.amr_select_audience:
                record.amr_resource_audience = self.env['ir.config_parameter'].sudo().get_param(
                    record.amr_select_audience, ''
                )
            else:
                record.amr_resource_audience = ''

    def action_edit_web_base_url(self):
        param = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'web.base.url')],
            limit=1
        )
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.config_parameter',
            'res_id': param.id,
            'view_mode': 'form',
        }
