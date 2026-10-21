# -*- coding: utf-8 -*-

import base64
import logging
import time
import uuid
import jwt

from odoo import _, api, models
from odoo.http import request

_logger = logging.getLogger(__name__)


def get_algorith_config():
    from cryptography.hazmat.primitives.asymmetric import (rsa, ec, )
    return {
        # RSA PKCS1
        "RS256": lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048),
        "RS384": lambda: rsa.generate_private_key(public_exponent=65537, key_size=3072),
        "RS512": lambda: rsa.generate_private_key(public_exponent=65537, key_size=4096),
        # RSA PSS
        "PS256": lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048),
        "PS384": lambda: rsa.generate_private_key(public_exponent=65537, key_size=3072),
        "PS512": lambda: rsa.generate_private_key(public_exponent=65537, key_size=4096),
        # ECDSA
        "ES256": lambda: ec.generate_private_key(ec.SECP256R1()),
        "ES384": lambda: ec.generate_private_key(ec.SECP384R1()),
        "ES512": lambda: ec.generate_private_key(ec.SECP521R1()),
        # Bitcoin / Blockchain
        "ES256K": lambda: ec.generate_private_key(ec.SECP256K1()),
    }


class ResourceAccessToken(models.AbstractModel):
    _inherit = 'amr.resource.helper'

    @api.model
    def introspect_token(self, token, **kw):
        if self.is_local_token(token):
            _logger.info("introspect_token local token")
            return self.env['amr.token.helper'].validate(token)
        _logger.info("Remote validate token")
        return super().introspect_token(token, **kw)

    def validate(self, token):
        if self.is_local_token(token):
            _logger.info("local validate token")
            return self.env['amr.token.helper'].validate(token)
        _logger.info("Remote validate token")
        return super().validate(token)

    def encode(self, **kw):
        return self.env['amr.token.helper'].encode(**kw)

    def decode(self, token, **kw):
        if self.is_local_token(token):
            _logger.info("local validate token")
            return self.env['amr.token.helper'].decode(token, **kw)
        _logger.info("Remote validate token")
        return super().decode(token, **kw)


class TokenHelper(models.AbstractModel):
    _name = 'amr.token.helper'
    _description = 'Token Helper call from Controller'
    ALGORITHM_CONFIG = get_algorith_config()

    @classmethod
    def generate_key(cls, algorithm):
        """Generate private/public key pair and a key identifier."""
        generator = cls.ALGORITHM_CONFIG.get(algorithm)
        if not generator:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        private_key = generator()
        public_key = private_key.public_key()
        kid = str(uuid.uuid4())
        return {
            "private_key": cls.private_key_to_pem(private_key),
            "public_key": cls.public_key_to_pem(public_key),
            "algorithm": algorithm,
            "kid": kid,
        }

    @staticmethod
    def private_key_to_pem(private_key):
        from cryptography.hazmat.primitives import serialization
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    @staticmethod
    def public_key_to_pem(public_key):
        from cryptography.hazmat.primitives import serialization
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def create_public_key(self, algorithm):
        data = self.generate_key(algorithm)
        data['name'] = data['kid']
        self.env["amr.public.key"].create(data)

    # helper will call from Controller
    @api.model
    def get_header_token(self):
        return self.env['amr.resource.helper'].get_header_token()

    @api.model
    def get_bearer_token(self):
        return self.env['amr.resource.helper'].get_bearer_token()

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
    def get_signature_type(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        return config_parameter.get_param('amr_token.signature_type', 'secret')

    @api.model
    def get_signature_algorithm(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        if config_parameter.get_param('amr_token.signature_type') == 'public_key':
            return config_parameter.get_param('amr_token.public_key_algorithm', "RS256")
        return config_parameter.get_param('amr_token.secret_algorithm', "HS256")

    @api.model
    def get_expires_in(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.expires_in', 60 * 60 * 24))

    @api.model
    def get_retention_in(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.retention_in', 60 * 60 * 4))

    @api.model
    def get_secret(self):
        return self.env['ir.config_parameter'].sudo().get_param('amr_token.secret')

    @api.model
    def get_issuer(self):
        return self.env['amr.resource.helper'].get_issuer()

    @api.model
    def get_audience(self):
        return self.env['amr.resource.helper'].get_audience()

    @api.model
    def get_token_endpoint(self, issuer=None):
        issuer = issuer or self.get_issuer()
        return f"{issuer}/oidc/token"

    @api.model
    def openid_configuration(self):
        issuer = self.get_issuer()
        return {
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/oidc/authorize",
            "introspection_endpoint": f"{issuer}/oidc/introspect",
            "token_endpoint": self.get_token_endpoint(issuer),
            "userinfo_endpoint": f"{issuer}/oidc/userinfo",
            "jwks_uri": f"{issuer}/.well-known/jwks.json",
            "response_types_supported": ["code", "token", "id_token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": [self.get_signature_algorithm()],
            "scopes_supported": ["openid", "profile", "email"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
            "claims_supported": ["uid", "db", "user_id", "sub", "name", "email"],
        }

    @api.model
    def oidc_jwks(self):
        return {"keys": self.env["amr.public.key"].sudo().get_jwks()}

    @api.model
    def oidc_token(self, grant_type=None, **kwargs):
        if grant_type == 'password':
            return self.do_password_grant(kwargs)
        if grant_type == 'challenge_approval':
            return self.do_challenge_grant(kwargs)
        if grant_type == 'digital_signature':
            # server version
            return self.do_digital_signature_grant(kwargs)
        return {
            'status': 401,
            'error': "unsupported_grant_type",
            "error_description": _("Grant Type '%s' is not supported") % grant_type
        }

    @api.model
    def do_password_grant(self, data):
        try:
            username = data.pop('username')
            password = data.pop('password')
        except KeyError:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'Missing username or password'}

        user = self.env['res.users'].sudo().get_user_by_username(username)
        if not user:
            return {'status': 401, 'error': "invalid_grant", 'error_description': 'User not found'}
        try:
            user.with_user(user)._check_credentials(password)
        except Exception:
            _logger.exception("Error _check_credentials")
            return {'status': 401, 'error': "invalid_grant"}

        client_id = data.pop('client_id', None)
        client_secret = data.pop('client_secret', None)
        access_token, _, expires_in = self.generate_user_token(user, **data)
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': expires_in,
        }

    @api.model
    def do_challenge_grant(self, data):
        client_id = data.pop('client_id', None)
        client_secret = data.pop('client_secret', None)
        grant_type = data.pop('grant_type', None)
        audience = data.pop('audience', None) or data.pop('aud', None)
        scope = data.pop('scope', "challenge")
        data.update({
            'iss': self.get_issuer(),
            'aud': audience or self.get_audience(),
            'scope': scope,
        })
        challenge, _ = self.generate_token_asymmetric(data)
        return {'challenge': challenge}

    @api.model
    def do_digital_signature_grant(self, data):
        client_id = data.pop('client_id', None)
        client_secret = data.pop('client_secret', None)
        grant_type = data.pop('grant_type', None)
        audience = data.pop('audience', None) or data.pop('aud', None)
        data.update({
            'iss': self.get_issuer(),
            'aud': audience or self.get_audience(),
        })
        digital_signature, _ = self.generate_token_asymmetric(data)
        return {'digital_signature': digital_signature}

    @api.model
    def generate_user_token(self, user, audience=None, expires_in=None, scope='', **kw):
        audience = audience or kw.pop('aud', None)
        payload = dict(kw)
        if user.is_user_machine():
            payload['type'] = 'machine'
        elif user.is_user_business():
            payload['type'] = 'user'
        elif user.is_user_technical():
            payload['type'] = 'technical'

        payload.update({
            'uid': user.id,
            'user_id': user.login,
            'sub': user.login,
            'email': user.email,
            'db': self.env.cr.dbname,
        })
        resource = kw.get('resource')
        if resource:
            payload['aud'] = resource
        expires_in = expires_in or self.get_expires_in()
        access_token, payload = self.generate_token(
            payload, audience=audience, expires_in=expires_in, scope=scope
        )
        return access_token, payload, expires_in

    @api.model
    def encode(self, algorithm=None, alg=None, audience=None, aud=None, **kw):
        algorithm = alg or algorithm
        audience = aud or audience
        scope = kw.pop('scope', '')
        kw.pop('iss', None)
        kw.pop('issuer', None)
        return self.generate_token(kw, algorithm=algorithm, audience=audience, scope=scope)

    @api.model
    def generate_token(self, payload, algorithm=None, issuer=None, expires_in=None, audience=None, scope=''):
        algorithm = algorithm or self.get_signature_algorithm()
        expires_in = expires_in or self.get_expires_in()
        expire = int(time.time()) + expires_in
        payload.update({
            'iss': self.get_issuer() or issuer,
            'aud': audience or self.get_audience(),
            'exp': expire,
            'scope': scope,
        })
        if algorithm.startswith('HS'):
            _logger.warning("Token signed with HS algorithm, validating via introspection endpoint")
            return self.generate_token_secret(payload, algorithm)
        return self.generate_token_asymmetric(payload, algorithm)

    @api.model
    def generate_token_asymmetric(self, payload, algorithm="RS256"):
        jwt_key = self.env['amr.public.key'].sudo().search([('algorithm', '=', algorithm)])
        if not jwt_key:
            raise Exception("Private Key not set")
        return jwt_key.generate_token(payload), payload

    @api.model
    def generate_token_secret(self, payload, algorithm="HS256"):
        jwt_secret = self.get_secret()
        if not jwt_secret:
            raise Exception("JWT Secret not set")
        return jwt.encode(payload, jwt_secret, algorithm=algorithm), payload

    @api.model
    def decode(self, token, **kw):
        return self.validate(token, **kw)

    @api.model
    def validate(self, token, **kw):
        header = jwt.get_unverified_header(token)
        algorithm = header.get('alg')
        audience = kw.pop('audience', None)
        if algorithm.startswith('HS'):
            _logger.warning("Token signed with HS algorithm, validating via introspection endpoint")
            return self.validate_secret(token, algorithm=algorithm, audience=audience)
        return self.validate_asymmetric(token, header.get('kid'), algorithm=algorithm, audience=audience)

    @api.model
    def validate_secret(self, token, algorithm="HS256", audience=None):
        jwt_secret = self.get_secret()
        if audience:
            _logger.info("with audience %s.", audience)
            options = {"verify_aud": True}
        else:
            audience = None
            options = {"verify_aud": False}
        if not jwt_secret:
            raise Exception("JWT Secret not set")
        issuer = self.get_issuer()
        return jwt.decode(token, jwt_secret, algorithms=[algorithm], issuer=issuer, audience=audience, options=options)

    @api.model
    def validate_asymmetric(self, token, kid, algorithm="RS256", audience=None):
        jwt_key = self.env['amr.public.key'].sudo().search([('algorithm', '=', algorithm), ('kid', '=', kid)])
        if not jwt_key:
            raise Exception("Public Key not set")
        if audience:
            _logger.info("with audience %s.", audience)
            options = {"verify_aud": True}
        else:
            audience = None
            options = {"verify_aud": False}
        issuer = self.get_issuer()
        return jwt_key.validate_token(token, issuer=issuer, audience=audience, options=options)

    @api.model
    def oidc_introspect(self, **kwargs):
        active = False
        user = None
        payload = {}
        token = kwargs.get('access_token') or kwargs.get('token') or self.get_header_token() or self.get_bearer_token()
        if token:
            payload = self.validate(token)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
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
        return {'active': False, "error": "invalid_token"}

    @api.model
    def oidc_introspect_payload_response_enhance(self, data):
        data['db'] = self.env.cr.dbname
        return data

    @api.model
    def oidc_profile(self, **kwargs):
        active = False
        user = None
        payload = {}
        token = kwargs.get('access_token') or kwargs.get('token') or self.get_header_token() or self.get_bearer_token()
        if token:
            payload = self.validate(token)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
                user = self.env['res.users'].sudo().browse(uid)
                active = user.exists()
        if active:
            data = dict(payload)
            data.update(
                uid=user.id,
                user_id=user.id,
                name=user.name,
                login=user.login,
            )
            return self.oidc_profile_payload_response_enhance(data)
        return {'active': False, "error": "invalid_token"}

    @api.model
    def oidc_profile_payload_response_enhance(self, data):
        data['db'] = self.env.cr.dbname
        return data
