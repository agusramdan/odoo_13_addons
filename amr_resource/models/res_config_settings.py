# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"


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

    def action_open_resource_issuers(self):
        registry = self.env['oidc.issuer.register']
        registry.check_access_rights('read')
        if not registry._registry_role('amr_resource.group_oidc_trust_admin'):
            from odoo.exceptions import AccessError
            raise AccessError('Registry access denied.')
        return self.env.ref('amr_resource.action_resource_issuers').read()[0]
