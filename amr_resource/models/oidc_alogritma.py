"""Access-token verification with opt-in metadata sources; no cache or stored code."""
import re


from odoo import api, fields, models, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
from werkzeug.exceptions import Unauthorized

ALGORITHM_CATALOG = __import__('types').MappingProxyType({
    'RS256': __import__('types').MappingProxyType({
        'key_family': 'RSA', 'min_key_bits': 2048,
        'purpose': 'access_token_verification', 'support_state': 'supported'}),
})

class OidcAlgorithm(models.Model):
    _name = 'oidc.algorithm'
    _description = 'Code-Owned OIDC Verification Algorithm'
    _rec_name = 'name'
    _inherit = ['mail.thread']
    
    name = fields.Char(required=True, index=True)
    key_family = fields.Selection([('RSA', 'RSA')], required=True, readonly=True)
    min_key_bits = fields.Integer(required=True, readonly=True, default=2048)
    purpose = fields.Selection([('access_token_verification', 'Access Token Verification')],
                               required=True, readonly=True)
    support_state = fields.Selection([('supported', 'Supported'), ('target', 'Target')],
                                     required=True, readonly=True)

    _sql_constraints = [('algorithm_name_unique', 'unique(name)', 'Algorithm must be unique.')]

    @api.model_create_multi
    def create(self, vals_list):
        expected = ALGORITHM_CATALOG
        for values in vals_list:
            name = values.get('name') if isinstance(values, dict) else None
            if name not in expected or any(
                    values.get(field) != value for field, value in expected[name].items()):
                raise AccessError('Algorithm catalog is code-owned.')
        return super(OidcAlgorithm, self).create(vals_list)

    def write(self, values):
        raise AccessError('Algorithm catalog is immutable; update it in code.')

    def unlink(self):
        raise AccessError('Algorithm catalog is immutable; update it in code.')
