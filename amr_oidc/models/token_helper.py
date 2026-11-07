# -*- coding: utf-8 -*-
"""OIDC-owned standalone base for token engine behavior."""
import base64
import logging
import time
import uuid
import jwt
from odoo import _, api, models
from odoo.exceptions import AccessError


def get_algorith_config():
    from cryptography.hazmat.primitives.asymmetric import ec, rsa
    return {
        "RS256": lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048),
        "RS384": lambda: rsa.generate_private_key(public_exponent=65537, key_size=3072),
        "RS512": lambda: rsa.generate_private_key(public_exponent=65537, key_size=4096),
        "PS256": lambda: rsa.generate_private_key(public_exponent=65537, key_size=2048),
        "PS384": lambda: rsa.generate_private_key(public_exponent=65537, key_size=3072),
        "PS512": lambda: rsa.generate_private_key(public_exponent=65537, key_size=4096),
        "ES256": lambda: ec.generate_private_key(ec.SECP256R1()),
        "ES384": lambda: ec.generate_private_key(ec.SECP384R1()),
        "ES512": lambda: ec.generate_private_key(ec.SECP521R1()),
        "ES256K": lambda: ec.generate_private_key(ec.SECP256K1()),
    }


from odoo.http import request

_logger = logging.getLogger(__name__)


class ValidatorSecret:
    def __init__(self, env, algorithm, issuer, secret):
        self.env = env
        self.algorithm = algorithm
        self.issuer = issuer
        self.secret = secret

    def decode(self, token, **kwargs):
        audience = kwargs.get('audience') or kwargs.get('aud')
        options = kwargs.get('options')
        if not options:
            options = {"verify_aud": True, "require": ["exp", "iss", "aud"]}

        return jwt.decode(token, self.secret, algorithms=[self.algorithm], issuer=self.issuer, audience=audience, options=options)


class ValidatorAsymmetric:
    def __init__(self, env, algorithm, issuer):
        self.env = env
        self.algorithm = algorithm
        self.issuer = issuer

    def decode(self, token, **kwargs):
        audience = kwargs.get('audience') or kwargs.get('aud')
        kid = kwargs.get('kid')
        if not kid or not audience:
            raise ValueError('A key identifier and non-empty audience are required')
        if jwt.get_unverified_header(token).get("kid") != kid:
            raise ValueError("Token kid does not match active key")
        jwt_key = self.env['amr.public.key'].sudo().search(
            [('algorithm', '=', self.algorithm), ('kid', '=', kid), ('active', '=', True)])
        if len(jwt_key) != 1 or not jwt_key.active:
            raise Exception("Public Key not set")
        options = dict(kwargs.get('options') or {})
        options.update({
            "verify_signature": True,
            "verify_iss": True,
            "verify_aud": True,
            "verify_exp": True,
            "verify_nbf": True,
            "require": ["exp", "iss", "aud"],
        })
        return jwt.decode(token, jwt_key.public_key, issuer=self.issuer, audience=audience, algorithms=[self.algorithm], options=options)


class TokenHelper(models.AbstractModel):
    _name = 'amr.oidc.helper'
    _description = 'Token Helper call from Controller'

    ALGORITHM_CONFIG = get_algorith_config()

    def get_validator(self, algorithm):
        if algorithm in self.ALGORITHM_CONFIG:
            return ValidatorAsymmetric(self.env, algorithm, self.get_issuer())
        else:
            return ValidatorSecret(self.env, algorithm, self.get_issuer(), self._get_secret())

    @classmethod
    def _generate_key(cls, algorithm):
        """Generate private/public key pair and a key identifier."""
        generator = cls.ALGORITHM_CONFIG.get(algorithm)
        if not generator:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        private_key = generator()
        public_key = private_key.public_key()
        kid = str(uuid.uuid4())
        return {
            "private_key": cls._private_key_to_pem(private_key),
            "public_key": cls._public_key_to_pem(public_key),
            "algorithm": algorithm,
            "kid": kid,
        }

    @staticmethod
    def _private_key_to_pem(private_key):
        from cryptography.hazmat.primitives import serialization
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    @staticmethod
    def _public_key_to_pem(public_key):
        from cryptography.hazmat.primitives import serialization
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def create_public_key(self, algorithm):
        data = self._generate_key(algorithm)
        data['name'] = data['kid']
        self.env["amr.public.key"].create(data)

    # helper will call from Controller
    @api.model
    def get_header_token(self):
        auth = request.httprequest.headers.get('Authorization', '')
        return auth.split(' ', 1)[1] if auth.lower().startswith('bearer ') else None

    @api.model
    def get_bearer_token(self):
        auth = request.httprequest.headers.get('Authorization', '')
        return auth.split(' ', 1)[1] if auth.lower().startswith('bearer ') else None

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
        value = config_parameter.get_param('amr_token.signature_type')
        if value not in ('secret', 'public_key'):
            raise ValueError('A supported signature type is required')
        return value

    @api.model
    def get_allowed_algorithms(self):
        return {
            'secret': ('HS256', 'HS384', 'HS512'),
            'public_key': self.ALGORITHM_CONFIG.keys(),
        }

    @api.model
    def get_signature_algorithm(self):
        config_parameter = self.env['ir.config_parameter'].sudo()
        signature_type = self.get_signature_type()
        algorithm = config_parameter.get_param(
            'amr_token.public_key_algorithm' if signature_type == 'public_key'
            else 'amr_token.secret_algorithm'
        )
        if not algorithm:
            raise ValueError('A configured signing algorithm is required')
        return algorithm

    @api.model
    def get_expires_in(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.expires_in', 60 * 60 * 24))

    @api.model
    def get_retention_in(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.retention_in', 60 * 60 * 4))

    @api.model
    def _get_secret(self):
        return self.env['ir.config_parameter'].sudo().get_param('amr_token.secret')

    @api.model
    def get_issuer(self):
        from urllib.parse import urlparse
        issuer = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        parsed = urlparse(issuer or '')
        if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('A valid HTTPS issuer is required')
        return issuer.rstrip('/')

    @api.model
    def get_audience(self):
        audience = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
        if not audience:
            raise ValueError('A configured audience is required')
        return audience

    @api.model
    def get_token_endpoint(self, issuer=None):
        issuer = issuer or self.get_issuer()
        return f"{issuer}/oidc/token"

    @api.model
    def _service_account_endpoint_defaults(self):
        issuer = self.get_issuer()
        return {
            "issuer": issuer,
            "authorization_endpoint": f"{issuer}/oidc/authorize",
            "token_endpoint": self.get_token_endpoint(issuer),
        }

    @api.model
    def oidc_jwks(self):
        return {"keys": self.env["amr.public.key"].sudo().get_jwks()}

    @api.model
    def oidc_token(self, grant_type=None, **kwargs):
        if grant_type == 'client_credentials':
            return self.env['oidc.client'].client_credentials(**kwargs)

        return {
            'status': 400,
            'error': "unsupported_grant_type",
            "error_description": _("Grant Type '%s' is not supported") % grant_type
        }

    @api.model
    def _check_token_issuance_access(self, user):
        if user.id != self.env.uid and not self.env.user.has_group('base.group_system'):
            raise AccessError(_('You may only issue a token for yourself.'))

    @api.model
    def _generate_user_token(self, user, audience=None, expires_in=None, scope='', **kw):
        self._check_token_issuance_access(user)
        if audience is None:
            audience = kw.pop('aud', None)
        payload = dict(kw)
        # User categories belong to amr_resource; the provider has no category policy.
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
        access_token, payload = self._generate_token(
            payload, audience=audience, expires_in=expires_in, scope=scope
        )
        return access_token, payload, expires_in

    def generate_user_token(self, user, audience=None, expires_in=None, scope='', **kw):
        access_token, payload, expires_in = self._generate_user_token(
            user, audience=audience, expires_in=expires_in, scope=scope, **kw
        )
        return access_token, payload, expires_in

    @api.model
    def encode(self, **kw):
        algorithm = kw.get('alg', None) or kw.get('algorithm')
        audience = kw.get('audience', None) or kw.get('aud', None) or ""
        scope = kw.pop('scope', '')
        kw.pop('alg', None)
        kw.pop('algorithm', None)
        kw.pop('audience', None)
        kw.pop('aud', None)
        kw.pop('iss', None)
        kw.pop('issuer', None)
        return self._generate_token(kw, algorithm=algorithm, audience=audience, scope=scope)

    @api.model
    def _validate_audience(self, audience):
        if isinstance(audience, str) and audience.strip():
            return audience
        if (isinstance(audience, list) and audience
                and all(isinstance(value, str) and value.strip() for value in audience)):
            return audience
        raise ValueError('A valid audience is required')

    @api.model
    def _generate_token(self, payload, algorithm=None, issuer=None, expires_in=None, audience=None, scope=''):
        signature_type = self.get_signature_type()
        configured_algorithm = self.get_signature_algorithm()
        allowed_algorithms = self.get_allowed_algorithms()
        if configured_algorithm not in allowed_algorithms[signature_type]:
            raise ValueError('Token algorithm does not match signature type')
        if algorithm and algorithm != configured_algorithm:
            raise ValueError('Token algorithm does not match provider configuration')
        algorithm = configured_algorithm
        if signature_type == 'secret' and not self._get_secret():
            raise ValueError('JWT Secret not set')
        expires_in = expires_in or self.get_expires_in()
        expire = int(time.time()) + expires_in
        audience = self.get_audience() if audience is None else audience
        audience = self._validate_audience(audience)
        payload.update({
            'iss': self.get_issuer() or issuer,
            'aud': audience,
            'exp': expire,
            'scope': scope,
        })
        if algorithm not in allowed_algorithms[signature_type]:
            raise ValueError('Unsupported token algorithm')
        if algorithm.startswith('HS'):
            _logger.warning("Token signed with HS algorithm, validating via introspection endpoint")
            return self._generate_token_secret(payload, algorithm)
        return self._generate_token_asymmetric(payload, algorithm)

    @api.model
    def _require_configured_algorithm(self, signature_type, algorithm):
        allowed = self.get_allowed_algorithms()
        if signature_type != self.get_signature_type():
            raise ValueError('Token signature type does not match provider configuration')
        configured = self.get_signature_algorithm()
        if configured not in allowed[signature_type] or algorithm != configured:
            raise ValueError('Token algorithm does not match provider configuration')

    @api.model
    def _generate_token_asymmetric(self, payload, algorithm="RS256"):
        self._require_configured_algorithm('public_key', algorithm)
        jwt_key = self.env['amr.public.key'].sudo().search([('algorithm', '=', algorithm), ('active', '=', True)])
        if len(jwt_key) != 1:
            raise Exception("Private Key not set")
        return jwt_key._generate_token(payload), payload

    @api.model
    def _generate_token_secret(self, payload, algorithm="HS256"):
        self._require_configured_algorithm('secret', algorithm)
        jwt_secret = self._get_secret()
        if not jwt_secret:
            raise Exception("JWT Secret not set")
        return jwt.encode(payload, jwt_secret, algorithm=algorithm), payload

    @api.model
    def decode(self, token, **kw):
        header = jwt.get_unverified_header(token)
        validator = self.get_validator(header.get('alg'))
        return validator.decode(token, **kw)

    @api.model
    def validate(self, token, **kw):
        self.decode(self, token, **kw)
        # header = jwt.get_unverified_header(token)
        # algorithm = header.get('alg')
        # signature_type = self.get_signature_type()
        # allowed_algorithms = self.get_allowed_algorithms()
        # if algorithm not in allowed_algorithms[signature_type]:
        #     raise ValueError('Token algorithm does not match signature type')
        # if algorithm != self.get_signature_algorithm():
        #     raise ValueError('Token algorithm does not match provider configuration')
        # audience = kw.pop('audience', None) or kw.get('aud', None)
        # if signature_type == 'secret':
        #     _logger.warning("Token signed with HS algorithm, validating via introspection endpoint")
        #     return self.validate_secret(token, algorithm=algorithm, audience=audience)
        # return self.validate_asymmetric(token, header.get('kid'), algorithm=algorithm, audience=audience)

    @api.model
    def validate_secret(self, token, algorithm="HS256", audience=None):
        self._require_configured_algorithm('secret', algorithm)
        if audience == '':
            raise ValueError('An explicit audience cannot be empty')
        jwt_secret = self._get_secret()
        audience = self.get_audience() if audience is None else audience
        options = {"verify_aud": True, "require": ["exp", "iss", "aud"]}
        if not jwt_secret:
            raise Exception("JWT Secret not set")
        issuer = self.get_issuer()
        return jwt.decode(token, jwt_secret, algorithms=[algorithm], issuer=issuer, audience=audience, options=options)

    @api.model
    def validate_asymmetric(self, token, kid, algorithm="RS256", audience=None):
        self._require_configured_algorithm('public_key', algorithm)
        if not kid or audience == '':
            raise ValueError('A key identifier and non-empty audience are required')
        jwt_key = self.env['amr.public.key'].sudo().search(
            [('algorithm', '=', algorithm), ('kid', '=', kid), ('active', '=', True)])
        if len(jwt_key) != 1 or not jwt_key.active:
            raise Exception("Public Key not set")
        audience = self.get_audience() if audience is None else audience
        options = {"verify_aud": True, "require": ["exp", "iss", "aud"]}
        issuer = self.get_issuer()
        return jwt_key.validate_token(token, issuer=issuer, audience=audience, options=options)

    @api.model
    def oidc_introspect(self, **kwargs):
        token = self.get_bearer_token()
        if not token or kwargs:
            return {'status': 401, 'active': False}
        if token:
            payload = self.env['oidc.client'].decode(token, **kwargs)
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
        else:
            return {'status': 401, 'active': False, "error": "invalid_token"}

    @api.model
    def oidc_introspect_payload_response_enhance(self, data):
        return data

    @api.model
    def oidc_profile(self, **kwargs):
        active = False
        payload = None
        user = None
        token = self.get_bearer_token()
        if not token or kwargs:
            return {'status': 401, 'active': False}
        if token:
            payload = request.env['oidc.client'].decode(token, **kwargs)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
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

    @api.model
    def oidc_profile_payload_response_enhance(self, data):
        return data
