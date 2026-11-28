"""Access-token verification with opt-in metadata sources; no cache or stored code."""

from odoo import api, models
from werkzeug.exceptions import Unauthorized


class ResourceHelper(models.AbstractModel):
    _inherit = 'amr.resource.helper'

    @api.model
    def is_local_issuer(self, issuer):
        raise Unauthorized('Local issuer classification is not configured.')

    @api.model
    def get_issuer(self):
        raise Unauthorized('Local issuer selection is not configured.')

    def encode(self, **kw):

        return self.generate_token(**kw).get('access_token')
