from odoo import api, models, fields
from odoo.exceptions import ValidationError, AccessError


class ServiceCredentialWizard(models.TransientModel):
    _inherit = 'service.credential.wizard'

    @api.model_create_multi
    def create(self, vals_list):
        if (not self.env.user.has_group('amr_resource.group_oidc_trust_admin')
                and any('issuer_profile_id' in values for values in vals_list)):
            raise AccessError('You are not allowed to use issuer profiles.')
        return super(ServiceCredentialWizard, self).create(vals_list)

    def write(self, values):
        if ('issuer_profile_id' in values
                and not self.env.user.has_group('amr_resource.group_oidc_trust_admin')):
            raise AccessError('You are not allowed to use issuer profiles.')
        return super(ServiceCredentialWizard, self).write(values)

    issuer_profile_id = fields.Many2one(
        'oidc.issuer.register',
        string='Issuer Profile',
        groups='amr_resource.group_oidc_trust_admin',
    )

    def _oauth_token_uri(self):
        self.ensure_one()
        if self.credential_type not in ('client_secret', 'service_account'):
            return self.token_uri
        profile = self.issuer_profile_id
        if not profile:
            return self.token_uri
        if not self.env.user.has_group('amr_resource.group_oidc_trust_admin'):
            raise AccessError('You are not allowed to use issuer profiles.')
        if self.token_uri:
            raise ValidationError('Choose an issuer profile or enter a token URI, not both.')
        if not profile.active or not profile.token_endpoint or profile.client_id != self.client_id:
            raise ValidationError('The issuer profile is inactive or does not match this client.')
        return profile.token_endpoint
