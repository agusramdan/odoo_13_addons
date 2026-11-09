# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import ormcache
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import werkzeug


_AUDIENCE_UNSET = object()


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_user_by_username(self, username):
        user = self.search([('login', '=', username)], order=self._get_login_order(), limit=1)
        if user:
            return user
        user = self.search([('email', '=', username)], order=self._get_login_order(), limit=1)
        return user or self.search(self._get_login_domain(username), order=self._get_login_order(), limit=1)

    @api.model
    def is_user_allow_create_token(self):
        return True

    def get_mobile_access_token(self, create=False):
        return self.get_access_token(create=create)

    @api.model
    @ormcache('uid', 'audience', 'bucket')
    def _get_access_token(self, uid, audience, bucket):
        user = self.browse(uid)
        if audience is _AUDIENCE_UNSET:
            token, _, _ = self.env['amr.oidc.helper']._generate_user_token(user)
        elif audience is None:
            raise ValueError('A valid audience is required')
        else:
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
        import time
        return self._get_access_token(self.id, audience, int(time.time() / 300))

    def create_access_token(self, audience='', **kw):
        raise UserError('Persistent access-token storage is not available')

    def add_url_access_token(self, url=None, create=True, param_name='access_token',
                             audience=_AUDIENCE_UNSET, url_type='access_token', **kw):
        if url_type != 'access_token':
            return self.get_auto_login_url(url=url, audience=audience, **kw)
        if not self.is_user_allow_create_token():
            return url
        parsed = urlparse(url)
        if audience is _AUDIENCE_UNSET:
            audience = '%s://%s' % (parsed.scheme, parsed.netloc)
        query = parse_qs(parsed.query)
        query[param_name] = self.get_access_token(create=create, audience=audience, **kw)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params,
                           urlencode(query, doseq=True), parsed.fragment))

    def get_auto_login_url(self, url=None, create=True, web_token_access_path='/web_token_access',
                           audience=_AUDIENCE_UNSET, **kw):
        if not self.is_user_allow_create_token():
            return url
        # sudo: preserve source parameter lookup; parameter policy deferred.
        url = url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        parsed = urlparse(url)
        if audience is _AUDIENCE_UNSET:
            audience = '%s://%s' % (parsed.scheme, parsed.netloc)
        query = {'token_access': self.get_access_token(create=create, audience=audience, **kw)}
        redirect = parsed.path
        if parsed.fragment:
            redirect = '%s#%s' % (redirect or '/', parsed.fragment)
        if redirect:
            query['redirect'] = redirect
        return '%s://%s%s?%s' % (parsed.scheme, parsed.netloc, web_token_access_path,
                                 werkzeug.url_encode(query))
