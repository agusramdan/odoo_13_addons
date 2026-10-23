# -*- coding: utf-8 -*-

import json
import logging

from odoo.http import Controller, request, route
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


class ControllerToken(Controller):

    @classmethod
    def handle_exception(cls, ex, status=500, error=None, error_description=None):
        if isinstance(ex, HTTPException):
            raise ex
        _logger.exception("Error in request: %s", ex)
        return cls.make_response(
            status=status,
            success=False,
            error=error or "general_error",
            error_description=error_description or "Request could not be processed.",
        )

    @classmethod
    def valid_response(cls, status, data):
        return Response(
            status=status,
            content_type='application/json; charset=utf-8',
            response=json.dumps(data),
        )

    def invalid_response(self, status, error, info=""):
        return self.make_response(status=status, error=error, error_description=info)

    @classmethod
    def make_response(cls, status=200, **payload):
        body = payload if payload else {
            "error": "unknown_error",
            "error_description": "An unknown error occurred.",
        }

        return Response(
            response=json.dumps(body, ensure_ascii=False),
            status=status,
            content_type="application/json; charset=utf-8",
        )

    @route("/.well-known/jwks.json", type='http', auth='public', methods=['GET'], csrf=False)
    def well_known_jwks(self):
        payload = request.env['amr.token.helper'].oidc_jwks()
        return self.make_response(**payload)

    @route('/oidc/token', type='http', auth='none', methods=['POST'], csrf=False)
    def api_oidc_token(self, **kwargs):
        try:
            payload = request.env['amr.token.helper'].sudo().oidc_token(**kwargs)
        except Exception as ex:
            _logger.exception("Error oidc_token")
            return self.handle_exception(ex, 401, "invalid_request")
        return self.make_response(**payload)

    @route('/oidc/introspect', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def api_oidc_introspect(self, **kwargs):
        return self.oidc_introspect(**kwargs)

    def oidc_introspect(self, **kwargs):
        try:
            data = request.env['amr.token.helper'].sudo().oidc_introspect(**kwargs)
        except Exception as ex:
            _logger.exception("Error oidc_introspect")
            return self.handle_exception(ex, 401, "invalid_token")

        active = data.get('active')
        if active:
            return self.make_response(**data)
        return self.make_response(401, **data)

    @route(['/oidc/profile', '/oidc/userinfo'], type='http', auth='none', methods=['GET'], csrf=False)
    def api_oidc_profile(self, **kwargs):
        try:
            payload = request.env['amr.token.helper'].sudo().oidc_profile(**kwargs)
        except Exception as ex:
            _logger.exception("Error oidc_profile")
            return self.handle_exception(ex, 401, "invalid_token")
        return self.make_response(**payload)
