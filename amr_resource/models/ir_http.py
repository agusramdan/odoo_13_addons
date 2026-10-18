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
    def _auth_method_machine(cls):
        # Menggunakan token oidc untuk handle API call
        helper = request.env['amr.resource.helper'].sudo()
        token = helper.get_bearer_token()
        # VALIDASI TOKEN
        validate = helper.get_validate_user(token)
        if not validate:
            raise Unauthorized('Invalid token')

        user = helper.get_user_match(validate)

        if not user:
            raise Unauthorized('User not found')

        if request.uid != user.id:
            request.uid = user.id
            request.jwt_token = token
            request.jwt_payload = validate

    @classmethod
    def _auth_method_params(cls):
        # Menggunakan token oidc untuk handle API call
        helper = request.env['amr.resource.helper'].sudo()
        token = helper.get_param_token()
        # VALIDASI TOKEN
        validate = helper.get_validate_user(token)
        if not validate:
            raise Unauthorized('Invalid token')

        user = helper.get_user_match(validate)

        if not user:
            raise Unauthorized('User not found')

        if request.uid != user.id:
            request.uid = user.id
            request.jwt_token = token
            request.jwt_payload = validate

    @classmethod
    def _auth_method_user_or_param(cls):
        try:
            return cls._auth_method_user()
        except:
            pass
        # Menggunakan token oidc untuk handle API call
        try:
            return cls._auth_method_params()
        except:
            pass

        helper = request.env['amr.resource.helper'].sudo()
        token = helper.get_bearer_token()
        # VALIDASI TOKEN
        validate = helper.get_validate_user(token)
        if not validate:
            raise Unauthorized('Invalid token')

        user = helper.get_user_match(validate)

        if not user:
            raise Unauthorized('User not found')

        if request.uid != user.id:
            request.uid = user.id
            request.jwt_token = token
            request.jwt_payload = validate


    # @classmethod
    # def _auth_method_user_or_apikey_or_param_or_jwt(cls):
    #     try:
    #         return cls._auth_method_user()
    #     except:
    #         pass
    #     try:
    #         return cls._auth_method_apikey()
    #     except:
    #         pass
    #     try:
    #         cls._auth_method_params()
    #     except:
    #         cls._auth_method_jwt()

    @classmethod
    def get_jwt_payload(cls):
        return getattr(request, 'jwt_payload', {})

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
