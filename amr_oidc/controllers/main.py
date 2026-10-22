# -*- coding: utf-8 -*-

import base64
import json
import logging
from urllib.parse import urlencode, urlsplit, urlunsplit

import werkzeug

from odoo import api
from odoo.addons.amr_token.controllers.main import ControllerToken
from odoo.http import request, route

_logger = logging.getLogger(__name__)


def _append_query_params(url, params):
    parts = urlsplit(url)
    query = parts.query
    if query:
        query += '&'
    query += urlencode(params)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def _append_fragment_params(url, params):
    parts = urlsplit(url)
    fragment = parts.fragment
    if fragment:
        fragment += '&'
    fragment += urlencode(params)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, fragment))


class ControllerOIDC(ControllerToken):

    @route(['/oidc/authorize', '/oidc/auth'], type='http', auth='public', csrf=False)
    def authorize(self, **params):
        invalid = self.is_invalid_parameter_authorize(**params)
        if invalid:
            return invalid
        user = request.env.user
        # params -> json -> base 64
        params_json = json.dumps(params)

        base64params = base64.urlsafe_b64encode(
            params_json.encode()
        ).decode()
        client_id = params.get('client_id')
        # sudo: preserve source client lookup before login; policy review deferred.
        client = request.env['oidc.client'].sudo().search([('client_id', '=', client_id), ], limit=1)
        # belum login

        if user._is_public():
            target = '/oidc/login_form?params=%s&client_name=%s' % (base64params, client.name)
        else:
            target = '/oidc/continue?params=%s&client_name=%s' % (base64params, client.name)
        return werkzeug.utils.redirect(target)

    @route('/oidc/continue', type='http', auth='public', website=True, methods=['GET'])
    def continue_page(self, params=None, client_name=None):
        return request.render('amr_oidc.custom_oidc_continue_template', {'params': params, 'client_name': client_name})

    @route('/oidc/login_form', type='http', auth='public', website=True, methods=['GET'])
    def login_page(self, params=None, client_name=None):
        return request.render('amr_oidc.custom_login_template', {'params': params, 'client_name': client_name})

    @route('/oidc/authorize_continue', type='http', auth='user', methods=['POST'], csrf=True)
    def authorize_continue(self, params=None):
        kwargs = json.loads(base64.urlsafe_b64decode(params.encode()).decode())
        return self.oidc_authorize(**kwargs)

    @route('/oidc/login/submit', type='http', auth='public', methods=['POST'], csrf=True)
    def login_submit(self, login=None, password=None, params=None):
        db = request.session.db
        try:
            uid = request.session.authenticate(db, login, password)
        except Exception:
            uid = False

        if not uid:
            return request.render(
                'amr_oidc.custom_login_template',
                {
                    'error': 'Invalid login/password',
                    'params': params,
                }
            )
        kwargs = json.loads(base64.urlsafe_b64decode(params.encode()).decode())
        return self.oidc_authorize(**kwargs)

    @api.model
    def is_invalid_parameter_authorize(self, **params):
        client_id = params.get('client_id')
        redirect_uri = params.get('redirect_uri')
        response_type = params.get('response_type')
        # sudo: preserve source client lookup during request validation.
        client = request.env['oidc.client'].sudo().search([('client_id', '=', client_id)], limit=1)
        if not client:
            return self.invalid_response(400, 'invalid_client')

        if not client._validate_redirect_uri(redirect_uri):
            return self.invalid_response(400, 'invalid_redirect_uri')

        if response_type not in ['code', 'token']:
            return self.invalid_response(400, 'unsupported_response_type')

        return False

    def oidc_authorize(self, **params):
        invalid = self.is_invalid_parameter_authorize(**params)
        if invalid:
            return invalid

        client_id = params.get('client_id')
        redirect_uri = params.get('redirect_uri')
        response_type = params.get('response_type')
        scope = params.get('scope')
        state = params.get('state')

        # sudo: resolve the protocol client only after redirect/client validation.
        client = request.env['oidc.client'].sudo().search([('client_id', '=', client_id)], limit=1)

        # hanya support authorization code flow
        if response_type == 'code':
            authorization_code = client._create_authorization_code(redirect_uri=redirect_uri, scope=scope)
            query = {'code': authorization_code.code}
            if state:
                query['state'] = state

            redirect_url = _append_query_params(authorization_code.redirect_uri, query)

        elif response_type == 'token':
            access_token = client._create_access_token(redirect_uri=redirect_uri, scope=scope)
            query = {
                'access_token': access_token.token,
                'token_type': 'Bearer',
                'expires_in': access_token.get_expires_in(),
            }

            if state:
                query['state'] = state

            redirect_url = _append_fragment_params(access_token.redirect_uri, query)
        else:
            return self.invalid_response(400, 'unsupported_response_type')

        return werkzeug.utils.redirect(redirect_url)

    @route(['/oidc/profile', '/oidc/userinfo'], type='http', auth='none', methods=['GET'], csrf=False)
    def api_oidc_profile(self, **kwargs):
        payload = request.env['amr.token.helper'].oidc_profile(**kwargs)
        return self.make_response(**payload)
