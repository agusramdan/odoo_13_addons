"""Access-token verification with opt-in metadata sources; no cache or stored code."""

from odoo import api, models


class ResourceHelper(models.AbstractModel):
    _inherit = 'amr.resource.helper'

    @api.model
    def is_local_issuer(self, issuer):
        return bool(self._profile(issuer).local_oidc)

    @api.model
    def get_issuer(self):
        registry = self.env['oidc.issuer.register']
        # sudo: protected global registry read only; company context never chooses trust.
        rows = registry.sudo().search(
            [('local_oidc', '=', True)], limit=1
        )
        if rows:
            return rows.issuer

        return super(ResourceHelper, self).get_issuer()

    def encode(self, **kw):

        return self.generate_token(**kw).get('access_token')
