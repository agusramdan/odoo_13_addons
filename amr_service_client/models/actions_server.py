# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServerActions(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("service_client", "Service Client")],
    )

    service_client_id = fields.Many2one(
        "service.client",
        "Service Client",
        domain="[('model_id', '=', model_id)]",
        help="Service Client to use for Http Request or RCP.",
    )

    @api.constrains('state', 'model_id')
    def _check_service_client_capability(self):
        for action in self:
            if action.state == 'service_client':
                if not action.service_client_id:
                    raise ValidationError(_("Call service_client_id mandatory."))

                if action.service_client_id.model_id != action.model_id:
                    raise ValidationError(_("Call service_client_id model miss match."))

    @api.model
    def run_action_service_client_multi(self, action, eval_context=None):
        # TDE CLEANME: when going to new api with server action, remove action
        if not action.service_client_id or action._is_recompute(action):
            return False
        return action.service_client_id.run_action_service_client(eval_context=eval_context)
