# -*- coding: utf-8 -*-

from werkzeug.exceptions import Unauthorized

from odoo import models
from odoo.http import request
from odoo.service import security


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
            helper = request.env['amr.resource.helper']
            payload = helper.get_validate_user(token)
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
        return cls._authenticate_token(request.env['amr.resource.helper'].get_bearer_token())

    @classmethod
    def _auth_method_params(cls):
        return cls._authenticate_token(request.env['amr.resource.helper'].get_param_token())

    @classmethod
    def _auth_method_user_or_param(cls):
        try:
            return cls._auth_method_user()
        except Unauthorized:
            pass
        helper = request.env['amr.resource.helper']
        token = helper.get_bearer_token()
        if token is not None:
            return cls._authenticate_token(token)
        return cls._auth_method_params()

    @classmethod
    def get_jwt_payload(cls):
        payload = getattr(request, 'jwt_payload', {})
        helper = request.env['amr.resource.helper']
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
