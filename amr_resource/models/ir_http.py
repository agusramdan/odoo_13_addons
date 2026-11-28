# -*- coding: utf-8 -*-

import re

from werkzeug.exceptions import Unauthorized

from odoo import models
from odoo.http import request
from odoo.service import security

AUTHORIZATION_RE = re.compile(r'^Bearer ([A-Za-z0-9\-._~+/]+=*)$')
def get_param_token():
    return (request.httprequest.args.get('access_token') or request.httprequest.form.get('access_token')
                or request.httprequest.args.get('token') or request.httprequest.form.get('token')
                or request.httprequest.args.get('token_access') or request.httprequest.form.get('token_access'))

def get_header_token():
    return request.httprequest.headers.get('access_token') or request.httprequest.headers.get('token')

def get_bearer_token():
    authorization = (request.httprequest.environ.get('HTTP_AUTHORIZATION')
                     or request.httprequest.headers.get('Authorization'))
    if authorization is None:
        return None
    match = AUTHORIZATION_RE.fullmatch(authorization)
    if not match:
        raise Unauthorized()
    return match.group(1)

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def set_session(cls, user, session_token=None):
        session = request.session
        session.rotate = True
        session.uid = user.id
        session.login = user.login
        if user:
            session.session_token = security.compute_session_token(session, request.env)
        else:
            session.session_token = session_token
        # v16 handle session berbeda dengan 13
        # if not session.session_token:
        #     request.update_env()
        #     session.uid = None
        #     session.login = None
        # else:
        #     request.update_env(user=request.session.uid)

        # v13 handle session berbeda dengan 16
        if session.session_token:
            request.uid = user.id
            request.disable_db = False
            session.get_context()
        else:
            request.uid = None
            session.uid = None
            session.login = None

    @classmethod
    def _authenticate_token(cls, token):
        try:
            helper = request.env['oidc.issuer.register']
            payload = helper.decode(token)
            user = helper.get_user_match(payload)
            if not user:
                raise Unauthorized()
            if request.uid != user.id:
                request.uid = user.id
                request.jwt_token = token
                request.jwt_payload = payload
            return None
        except Exception:
            pass
        raise Unauthorized() from None

    @classmethod
    def _auth_method_machine(cls):
        return cls._authenticate_token(get_bearer_token())

    @classmethod
    def _auth_method_params(cls):
        return cls._authenticate_token(get_param_token())

    @classmethod
    def _auth_method_user_or_param(cls):
        try:
            return cls._auth_method_user()
        except Unauthorized:
            pass
        token = get_bearer_token()
        if token is not None:
            return cls._authenticate_token(token)
        return cls._auth_method_params()

    @classmethod
    def get_jwt_payload(cls):
        payload = getattr(request, 'jwt_payload', {})
        helper = request.env['oidc.issuer.register']
        return payload if helper._verified(payload) else {}

    @classmethod
    def check_scope(cls, required_scope):
        pass
        # jwt_payload = cls.get_jwt_payload()
        # scopes = jwt_payload.get("scope", [])
        # if isinstance(scopes, str):
        #     scopes = scopes.split()
        #
        # if required_scope not in scopes:
        #     raise Forbidden()
