# -*- coding: utf-8 -*-

import logging
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import werkzeug

from odoo import api, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_user_by_username(self, username):
        user = self.search([('login', '=', username)], order=self._get_login_order(), limit=1)
        if user:
            return user
        user = self.search([('email', '=', username)], order=self._get_login_order(), limit=1)
        if user:
            return user
        user = self.search(self._get_login_domain(username), order=self._get_login_order(), limit=1)
        return user

    @api.model
    def is_user_allow_create_token(self):
        return True

    def get_mobile_access_token(self, create=False):
        return self.get_access_token(create=create)

    @tools.ormcache('uid', 'audience', 'bucket')
    def _get_access_token(self, uid, audience, bucket):
        user = self
        if uid != user.id:
            user = self.browse(uid)
        access_token, _, _ = self.env['amr.token.helper'].generate_user_token(user, audience=audience)
        return access_token

    def get_access_token(self, create=False, audience="", **kw):
        if not self.is_user_allow_create_token():
            raise UserError('User not allowed to create access token')
        bucket = int(time.time() / 300)
        return self._get_access_token(self.id, audience, bucket)

    def create_access_token(self, audience="", **kw):
        access_token, _, _ = self.env['amr.token.helper'].generate_user_token(self, audience=audience)
        return self.env['amr.token'].create_access_token(user=self, **kw)

    def add_url_access_token(self, url=None, create=True, param_name='access_token', audience=None, url_type='access_token', **kw):
        if url_type != 'access_token':
            return self.get_auto_login_url(url=url, **kw)
        if not self.is_user_allow_create_token():
            return url
        parsed_url = urlparse(url)
        if not audience:
            audience = "%s://%s" % (parsed_url.scheme, parsed_url.netloc)
        access_token = self.get_access_token(create=create, audience=audience, **kw)
        query_params = parse_qs(parsed_url.query)
        query_params[param_name] = access_token
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment,
        ))

    def get_auto_login_url(self, url=None, create=True, web_token_access_path='/web_token_access', audience=None, **kw):
        if not self.is_user_allow_create_token():
            return url

        url = url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        parsed_url = urlparse(url)
        if not audience:
            audience = "%s://%s" % (parsed_url.scheme, parsed_url.netloc)
        token = self.get_access_token(create=create, audience=audience, **kw)
        query = {'token_access': token}
        redirect = parsed_url.path
        if parsed_url.fragment:
            if redirect:
                redirect = f"{redirect}#{parsed_url.fragment}"
            else:
                redirect = f"/#{parsed_url.fragment}"
        if redirect:
            query['redirect'] = redirect
        query_str = werkzeug.url_encode(query)
        return "%s://%s%s?%s" % (parsed_url.scheme, parsed_url.netloc, web_token_access_path, query_str)
