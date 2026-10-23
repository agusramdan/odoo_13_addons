# -*- coding: utf-8 -*-

from odoo import api
from odoo.addons.amr_token.controllers.main import ControllerToken
from odoo.http import request, route


class ControllerOIDC(ControllerToken):

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

    @route(['/oidc/profile', '/oidc/userinfo'], type='http', auth='none', methods=['GET'], csrf=False)
    def api_oidc_profile(self, **kwargs):
        payload = request.env['amr.token.helper'].oidc_profile(**kwargs)
        return self.make_response(**payload)
