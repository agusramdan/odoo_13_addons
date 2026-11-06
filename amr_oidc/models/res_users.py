# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import ormcache
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import werkzeug


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

    @ormcache('uid', 'audience', 'bucket')
    def _get_access_token(self, uid, audience, bucket):
        user = self if uid == self.id else self.browse(uid)
        return self.env['amr.oidc.helper'].generate_user_token(user, audience=audience)[0]

    def get_access_token(self, create=False, audience=None, **kw):
        if not self.is_user_allow_create_token():
            raise UserError('User not allowed to create access token')
        import time
        return self._get_access_token(self.id, audience, int(time.time() / 300))

    def create_access_token(self, audience='', **kw):
        raise UserError('Persistent access-token storage is not available')

    def add_url_access_token(self, url=None, create=True, param_name='access_token', audience=None,
                             url_type='access_token', **kw):
        if url_type != 'access_token':
            return self.get_auto_login_url(url=url, **kw)
        if not self.is_user_allow_create_token():
            return url
        parsed = urlparse(url)
        if audience is None:
            audience = '%s://%s' % (parsed.scheme, parsed.netloc)
        query = parse_qs(parsed.query)
        query[param_name] = self.get_access_token(create=create, audience=audience, **kw)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params,
                           urlencode(query, doseq=True), parsed.fragment))

    def get_auto_login_url(self, url=None, create=True, web_token_access_path='/web_token_access',
                           audience=None, **kw):
        if not self.is_user_allow_create_token():
            return url
        url = url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        parsed = urlparse(url)
        if audience is None:
            audience = '%s://%s' % (parsed.scheme, parsed.netloc)
        query = {'token_access': self.get_access_token(create=create, audience=audience, **kw)}
        redirect = parsed.path
        if parsed.fragment:
            redirect = '%s#%s' % (redirect or '/', parsed.fragment)
        if redirect:
            query['redirect'] = redirect
        return '%s://%s%s?%s' % (parsed.scheme, parsed.netloc, web_token_access_path,
                                 werkzeug.url_encode(query))
