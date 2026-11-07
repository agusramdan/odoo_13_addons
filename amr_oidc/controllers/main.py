# -*- coding: utf-8 -*-

from odoo import api
from odoo.http import Controller, request, route
from werkzeug.wrappers import Response
import json


class ControllerOIDC(Controller):

    @classmethod
    def make_response(cls, status=200, **payload):
        return Response(json.dumps(payload or {"error": "unknown_error"}), status=status, content_type="application/json; charset=utf-8")

    def invalid_response(self, status, error, info=""):
        return self.make_response(status=status, error=error, error_description=info)

    @route('/.well-known/jwks.json', type='http', auth='public', methods=['GET'], csrf=False)
    def well_known_jwks(self):
        payload = request.env['amr.oidc.helper'].oidc_jwks()
        return self.make_response(**payload)

    @route('/oidc/token', type='http', auth='none', methods=['POST'], csrf=False)
    def api_oidc_token(self, **kwargs):
        try:
            payload = request.env['amr.oidc.helper'].sudo().oidc_token(**kwargs)
            return self.make_response(**payload)
        except Exception as ex:
            return self.handle_exception(ex, 401, "invalid_request")

    @route('/.well-known/openid-configuration', type='http', auth='public', methods=['GET'], csrf=False)
    def well_known_openid_configuration(self):
        return self.make_response(status=404)

    def _unsupported_authorization_response(self):
        return self.invalid_response(400, 'unsupported_response_type')

    @route(['/oidc/authorize', '/oidc/auth'], type='http', auth='public', csrf=False)
    def authorize(self, **params):
        return self._unsupported_authorization_response()

    @route('/oidc/continue', type='http', auth='public', website=True, methods=['GET'])
    def continue_page(self, params=None, client_name=None):
        return request.render('amr_oidc.custom_oidc_continue_template', {'params': params, 'client_name': client_name})

    @route('/oidc/login_form', type='http', auth='public', website=True, methods=['GET'])
    def login_page(self, params=None, client_name=None):
        return request.render('amr_oidc.custom_login_template', {'params': params, 'client_name': client_name})

    @route('/oidc/authorize_continue', type='http', auth='user', csrf=False)
    def authorize_continue(self, params=None):
        return self._unsupported_authorization_response()

    @route('/oidc/login/submit', type='http', auth='public', methods=['POST'], csrf=False)
    def login_submit(self, login=None, password=None, params=None):
        return self._unsupported_authorization_response()

    @api.model
    def is_invalid_parameter_authorize(self, **params):
        return self._unsupported_authorization_response()

    def oidc_authorize(self, **params):
        return self._unsupported_authorization_response()

    @route('/oidc/introspect', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def api_oidc_introspect(self, **kwargs):
        http_request = request.httprequest
        if http_request.method != 'POST' or not http_request.is_secure:
            return self.invalid_response(400, 'invalid_request')
        if http_request.args:
            return self.invalid_response(400, 'invalid_request')
        token = http_request.form.get('token')
        if (not token or len(http_request.form) != 1
                or kwargs and kwargs != {'token': token}):
            return self.invalid_response(400, 'invalid_request')
        try:
            client_id, client_secret = request.env['amr.oidc.helper'].get_basic_auth()
            # sudo: resolve the registered client before checking its verifier.
            client = request.env['oidc.client'].sudo().search([
                ('client_id', '=', client_id), ('active', '=', True),
            ], limit=1)
            if not client or not client.allow_introspection:
                raise ValueError()
            client.check_credentials(client_secret)
        except Exception:
            return self.invalid_response(401, 'invalid_client')
        try:
            claims = request.env['amr.oidc.helper'].validate(token, audience=client.client_id)
        except Exception:
            return self.make_response(active=False)
        allowed = ('sub', 'aud', 'iss', 'exp', 'iat', 'scope', 'jti', 'token_type', 'client_id')
        payload = {'active': True}
        payload.update((key, claims[key]) for key in allowed if key in claims)
        return self.make_response(**payload)

    @route(['/oidc/profile', '/oidc/userinfo'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def api_oidc_profile(self, **kwargs):
        auth = request.httprequest.headers.get('Authorization', '')
        if (not auth.startswith('Bearer ') or kwargs or request.httprequest.args
                or request.httprequest.form or request.httprequest.get_data(cache=True)):
            return self.invalid_response(400, 'invalid_request')
        try:
            claims = request.env['amr.oidc.helper'].validate(auth[7:])
        except Exception:
            return self.invalid_response(401, 'invalid_token')
        if not claims.get('sub'):
            return self.invalid_response(401, 'invalid_token')
        return self.make_response(sub=claims['sub'])
