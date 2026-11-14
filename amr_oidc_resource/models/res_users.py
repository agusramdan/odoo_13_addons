# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import AccessError, UserError


_AUDIENCE_UNSET = object()


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def is_user_allow_create_token(self):
        return True

    @api.model
    def _get_access_token(self, uid, audience_key):
        user = self.browse(uid)
        if audience_key is _AUDIENCE_UNSET:
            token, _, _ = self.env['amr.oidc.helper']._generate_user_token(user)
        else:
            audience = list(audience_key) if isinstance(audience_key, tuple) else audience_key
            token, _, _ = self.env['amr.oidc.helper']._generate_user_token(
                user, audience=audience
            )
        return token

    def get_access_token(self, create=False, audience=_AUDIENCE_UNSET, **kw):
        missing = object()
        resource = kw.pop('resource', missing)
        has_resource = resource is not missing
        if has_resource:
            if not isinstance(resource, str) or not resource.strip():
                raise ValueError('Invalid resource')
            audience = resource
        elif audience is not _AUDIENCE_UNSET and audience is None:
            raise ValueError('A valid audience is required')
        self.ensure_one()
        if self.id != self.env.uid and not self.env.user.has_group('base.group_system'):
            raise AccessError('You may only issue an access token for yourself.')
        if not self.is_user_allow_create_token():
            raise UserError('User not allowed to create access token')
        if audience is _AUDIENCE_UNSET:
            audience_key = audience
        else:
            audience = self.env['amr.oidc.helper']._validate_audience(audience)
            audience_key = tuple(audience) if isinstance(audience, list) else audience
        return self._get_access_token(self.id, audience_key)

    def create_access_token(self, audience='', **kw):
        raise UserError('Persistent access-token storage is not available')

    def add_url_access_token(self, url=None, create=True, param_name='access_token',
                             audience=_AUDIENCE_UNSET, url_type='access_token', **kw):
        raise UserError('URL access tokens are disabled')

    def get_auto_login_url(self, url=None, create=True, web_token_access_path='/web_token_access',
                           audience=_AUDIENCE_UNSET, **kw):
        raise UserError('URL access tokens are disabled')
