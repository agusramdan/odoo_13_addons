# -*- coding: utf-8 -*-

import json

from werkzeug.exceptions import HTTPException
from werkzeug.utils import redirect
from werkzeug.wrappers import Response

from odoo.api import call_kw
from odoo.http import Controller, request, route
from odoo.models import check_method_name


class RedirectController(Controller):

    @classmethod
    def handle_exception(cls, ex, status=500, error=None, error_description=None):

        if isinstance(ex, HTTPException):
            raise ex

        return cls.make_response(
            status=status,
            success=False,
            error=error or "general_error",
            error_description=error_description or str(ex)
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
        return Response(
            response=json.dumps(
                payload
                or {"error": "unknown_error", "error_description": "An unknown error occurred"}
            ),
            status=status,
            headers=[("Content-Type", "application/json")],
        )

    @route('/redirect', type='http', auth='user_or_param', methods=['GET'], csrf=False)
    def redirect_url(self, url=None):
        url = request.env.user.add_url_access_token(url)
        return redirect(url)

    @route('/api/v1/access_token/url', type='http', auth='user_or_param', methods=['GET'], csrf=False)
    def access_url(self, **kwargs):
        data = dict(kwargs)
        url = data.get("url", None)
        url_type = data.get("type", "auto_login")
        result = None
        if not url:
            res_id = data.get("res_id", None)
            res_model = data.get("res_model", None)
            model_object = request.env[res_model].browse(res_id)
            if callable(getattr(model_object, 'get_url_access_token', None)):
                result = model_object.get_url_access_token()
            else:
                type_url = data.get("type_url", "internal")
                if type_url == 'internal':
                    if callable(getattr(model_object, 'get_internal_url', None)):
                        url = model_object.get_internal_url()
                    else:
                        return self.invalid_response(400, "invalid type_url", "get_internal_url not found")
                else:
                    if callable(getattr(model_object, 'get_internal_url', None)):
                        url = model_object.get_public_url()
                    else:
                        return self.invalid_response(400, "invalid type_url", "get_public_url not found")

        if not result and url:
            if url_type in ['auto_login', 'access_token']:
                access_url = request.env.user.add_url_access_token(url, url_type=url_type)
            else:
                return self.invalid_response(400, "invalid type", "type[%s] accept only auto_login or access_token" % url_type)
            result = {
                'url': url,
                'url_access_token': access_url,
            }

        return self.valid_response(200, result)

    @route('/api/test/connection/machine', auth="machine")
    def connection_test(self, **kwargs):
        return self.valid_response(200, {"data": "test connection machine ok"})


class JsonRpcApi(Controller):

    def _call_kw(self, model, method, args, kwargs):
        check_method_name(method)
        return call_kw(request.env[model], method, args, kwargs)

    @route('/api/dataset/call_kw', type='json', auth="machine")
    def call_kw(self, model, method, args, kwargs):
        return self._call_kw(model, method, args, kwargs)
