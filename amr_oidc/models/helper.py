# -*- coding: utf-8 -*-

import base64
import logging
import jwt
from odoo import api, fields, models
from odoo.http import request
from psycopg2 import IntegrityError
import jwt
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)

JWT_CLIENT_ASSERTION = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
JWT_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer"


class TokenHelper(models.AbstractModel):
    _inherit = 'amr.token.helper'

    # helper will call from Controller
    @api.model
    def get_bearer_token(self):
        auth = request.httprequest.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return None
        data = auth.split(" ", 1)
        return data[1] if len(data) > 1 else None

    @api.model
    def get_basic_auth(self):
        auth = request.httprequest.headers.get('Authorization')
        if not auth:
            return None, None

        try:
            scheme, encoded = auth.split(' ', 1)
            if scheme.lower() != 'basic':
                return None, None

            decoded = base64.b64decode(encoded).decode('utf-8')
            return decoded.split(':', 1)
        except Exception:
            return None, None

    @api.model
    def openid_configuration(self):
        result = super().openid_configuration()
        issuer = self.get_issuer()
        result.update(
            {
                "authorization_endpoint": f"{issuer}/oidc/authorize",
                # "userinfo_endpoint": f"{issuer}/oidc/userinfo",
                # "jwks_uri": f"{issuer}/oidc/jwks",
                "response_types_supported": [
                    "code",
                    "token",
                    "id_token",
                ],
                # "subject_types_supported": [
                #     "public",
                # ],
                # "id_token_signing_alg_values_supported": [
                #     "RS256",
                # ],
                "scopes_supported": [
                    "openid",
                    "profile",
                    "email",
                ],
                "token_endpoint_auth_methods_supported": [
                    "client_secret_post",
                    "client_secret_basic",
                ],
                "claims_supported": [
                    "uid",
                    "db",
                    "user_id",
                    "sub",
                    "name",
                    "email",
                ],
            }
        )
        return result

    @api.model
    def oidc_token(self, grant_type=None, **kwargs):
        if grant_type == JWT_GRANT_TYPE:
            return self.do_client_assertion(kwargs.pop('assertion'), kwargs)

        if grant_type == 'client_credentials':
            if kwargs.get('client_assertion_type') == JWT_CLIENT_ASSERTION:
                return self.do_client_assertion(kwargs.pop('client_assertion'), kwargs)

            return self.do_client_credentials(kwargs)

        if grant_type == 'refresh_token':
            return self.do_refresh_grant(kwargs.get('refresh_token'))

        return super().oidc_token(grant_type=grant_type, **kwargs)

    @api.model
    def do_password_grant(self, data):
        try:
            client_id = data.pop('client_id')
        except KeyError:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Missing client_id'}
        # sudo: preserve source client lookup; client-auth policy deferred.
        client = self.env['oidc.client'].sudo().search([('client_id', '=', client_id)])
        if not client:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Client not found.'}
        client_secret = data.pop('client_secret', None)
        if client_secret:
            user = client.user_id
            if not user:
                return {'status': 401, 'error': "invalid_grant", 'error_description': 'Client invalid.'}
            try:
                user.with_user(user)._check_credentials(client_secret)
            except Exception:
                _logger.warning("Error _check_credentials")
                return {'status': 401, 'error': "invalid_grant"}

        data['client_id'] = client_id
        data['azp'] = client.name or client_id
        data['sub_type'] = "user"

        return super().do_password_grant(data)

    @api.model
    def do_client_credentials(self, data):

        # try basic auth
        client_id, client_secret = self.get_basic_auth()
        if not client_id:
            client_id = data.pop('client_id', None)
            client_secret = data.pop('client_secret', None)

        if not client_id:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Missing client_id'}

        if not client_secret:
            return {'status': 401, 'error': "invalid_grant",'error_description': 'Missing client_secret'}

        # sudo: preserve source client lookup; client-auth policy deferred.
        client = self.env['oidc.client'].sudo().search([('client_id', '=', client_id)])

        if not client:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Client not found.'}

        user = client.user_id
        if not user:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Client invalid.'}

        if not client_secret:
            return {'status': 401, 'error': "invalid_grant"}
        try:
            client.check_credentials(client_secret)
        except Exception:
            _logger.warning("Error _check_credentials")
            return {'status': 401, 'error': "invalid_grant"}
        data['client_id'] = client_id
        data['azp'] = client.name or client_id
        data['sub_type'] = "client"

        access_token, _, expires_in = self.generate_user_token(user, type='machine', **data)
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
        }

    def do_client_assertion(self, assertion, data):
        token_endpoint = self.get_token_endpoint()
        if not assertion:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'No assertion.'}
        try:
            header = jwt.get_unverified_header(assertion)
        except jwt.InvalidTokenError as e:
            raise ValueError(f'Invalid JWT header: {e}')

        kid = header.get('kid')
        alg = header.get('alg')

        if not kid:
            raise ValueError('Missing kid in JWT header')

        if not alg:
            raise ValueError('Missing alg in JWT header')

        payload = jwt.decode(
            assertion,
            options={
                "verify_signature": False,
            }
        )
        client_id = payload.get('iss')
        if not client_id:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Missing client_id'}

        # sudo: preserve source client lookup; client-auth policy deferred.
        client = self.env['oidc.client'].sudo().search([('client_id', '=', client_id)])
        if not client:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Client not found.'}

        key = self.env['oidc.client.key'].search([
            ('client_id', '=', client.id),
            ('kid', '=', kid),
            ('active', '=', True),
        ], limit=1)
        if not key:
            raise ValueError(f'Unknown kid: {kid}')

        if key.algorithm != alg:
            raise ValueError(f'Algorithm mismatch. Expected {key.algorithm}, got {alg}')

        try:
            payload = jwt.decode(
                assertion,
                key.public_key,
                algorithms=[alg],
                audience=token_endpoint,
                options={
                    "require": [
                        "iss",
                        "sub",
                        "aud",
                        "exp",
                        "iat",
                        "jti",
                    ]
                },
            )

            # Umumnya untuk JWT Bearer Grant
            if payload["iss"] != payload["sub"]:
                raise ValueError("iss dan sub harus sama untuk client assertion")

            #Validasi iat (maksimal 5 menit)
            now = datetime.now(timezone.utc).timestamp()
            max_age = 300

            if now - payload["iat"] > max_age:
                raise ValueError("Assertion terlalu lama")

        except jwt.ExpiredSignatureError:
            _logger.error("ExpiredSignatureError %s",assertion)
            raise ValueError("Assertion sudah expired")

        except jwt.InvalidAudienceError:
            raise ValueError("Audience tidak valid")

        except jwt.InvalidTokenError as e:
            raise ValueError(f"JWT tidak valid: {e}")

        user = client.user_id
        if not user:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Client invalid.'}
        if not payload.get('jti'):
            raise ValueError("without jti")

        try:
            self.env['oidc.jwt.replay'].create({
                'jti': payload['jti'],
                'iss': payload['iss'],
                'expired_at': fields.Datetime.to_datetime(
                    datetime.fromtimestamp(payload['exp'])
                ),
            })
        except IntegrityError:
            raise ValueError('JWT assertion has already been used')
        access_token, _, expires_in = self.generate_user_token(user, type='machine', **data)

        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
        }

    @api.model
    def do_refresh_grant(self, refresh_token=None):
        if not refresh_token:
            return {'status': 400, 'error': "invalid_grant"}

        payload = self.env['oidc.refresh.token'].validate_token(refresh_token)

        if not payload or not payload.get('token'):
            return {'status': 400, 'error': "invalid_grant", 'error_description': "Invalid or expired token"}
        # sudo: preserve source refresh-user lookup; refresh policy deferred.
        user = self.env['res.users'].sudo().get_user_by_username(payload['sub'])
        return self.generate_user_token(user, payload)

    @api.model
    def oidc_introspect(self, **kwargs):
        active = False
        user = None
        payload = {}
        token = kwargs.get('access_token') or kwargs.get('token') or self.get_header_token() or self.get_bearer_token()
        if token:
            payload = self.env['oidc.client'].validate_token(token)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
                # sudo: preserve source introspection-user lookup; policy deferred.
                user = self.env['res.users'].sudo().browse(uid)
                active = user.exists()
        if active:
            data = dict(payload)
            data.update(
                active=True,
                uid=user.id,
                user_id=user.id,
                name=user.name,
                login=user.login,
            )
            return self.oidc_introspect_payload_response_enhance(data)
        else:
            return {'active': False, "error": "invalid_token"}

    @api.model
    def oidc_profile(self, **kwargs):
        active = False
        payload = None
        user = None
        token = kwargs.get('access_token') or kwargs.get('token') or self.get_header_token() or self.get_bearer_token()
        if token:
            payload = request.env['oidc.client'].validate_token(token)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
                # sudo: preserve source profile-user lookup; policy deferred.
                user = request.env['res.users'].sudo().browse(uid)
                active = user.exists()
        if active:
            data = dict(payload)
            data.update(
                uid=user.id,
                user_id=user.id,
                name=user.name,
                login=user.login,
                db=request.session.db,
            )
            if 'status' in data:
                data.pop('status')
            return self.oidc_profile_payload_response_enhance(data)
        else:
            return {'status': 401, "error": "invalid_token", "error_description": "Invalid token"}
