# -*- coding: utf-8 -*-
"""OIDC-owned standalone base for token engine behavior."""
import base64
import hashlib
import hmac
import logging
import os
import time
import uuid
import jwt
from odoo import SUPERUSER_ID, _, api, models
from odoo.exceptions import AccessError


_AUDIENCE_UNSET = object()
_FRESH_TTL_UNSET = object()
_FRESH_INSTANCE_MARKER = 'AMR_OIDC_FRESH_PROFILE_INSTANCE_ID'
_FRESH_INSTANCE_BINDING = 'amr_token.fresh_profile_instance_binding'


class _FreshIssuanceProvenance(object):
    __slots__ = ('client_id', 'user_id', 'issuer', 'audience', 'subject')

    def __init__(self, client_id, user_id, issuer, audience, subject):
        self.client_id = client_id
        self.user_id = user_id
        self.issuer = issuer
        self.audience = audience
        self.subject = subject


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


class TokenSecret:
    def __init__(self, env, algorithm, issuer, secret):
        self.env = env
        self.algorithm = algorithm
        self.issuer = issuer
        self.secret = secret

    def encode(self, payload):
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode(self, token, **kwargs):
        audience = kwargs.get('audience') or kwargs.get('aud')
        options = dict(kwargs.get('options') or {})
        options.update({
            "verify_signature": True,
            "verify_iss": True,
            "verify_aud": True,
            "verify_exp": True,
            "verify_nbf": True,
            "require": ["exp", "iss", "aud"],
        })

        return jwt.decode(token, self.secret, algorithms=[self.algorithm], issuer=self.issuer, audience=audience,
                          options=options)


class TokenAsymmetric:
    def __init__(self, env, algorithm, issuer):
        self.env = env
        self.algorithm = algorithm
        self.issuer = issuer

    def encode(self, payload):
        # sudo: preserve source parameter lookup; parameter policy deferred.
        jwt_key = self.env['amr.public.key'].sudo().search(
            [('algorithm', '=', self.algorithm), ('active', '=', True), ('is_signing', '=', True)], limit=1
        )
        if len(jwt_key) != 1:
            raise Exception("Private Key not set")
        return jwt.encode(payload, jwt_key.private_key, algorithm=self.algorithm, headers={'kid': jwt_key.kid})

    def decode(self, token, kid=None, **kwargs):
        if not kid:
            raise ValueError('kid are required')
        audience = kwargs.get('audience') or kwargs.get('aud')
        if not audience:
            raise ValueError('A key identifier and non-empty audience are required')
        if jwt.get_unverified_header(token).get("kid") != kid:
            raise ValueError("Token kid does not match active key")
        # sudo: preserve source parameter lookup; parameter policy deferred.
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
        return jwt.decode(token, jwt_key.public_key, issuer=self.issuer, audience=audience, algorithms=[self.algorithm],
                          options=options)


class TokenHelper(models.AbstractModel):
    _name = 'amr.oidc.helper'
    _description = 'Token Helper call from Controller'

    ALGORITHM_CONFIG = get_algorith_config()
    ALGORITHM_SECRET_CONFIG = ('HS256', 'HS384', 'HS512')

    @api.model
    def _require_configured_algorithm(self, signature_type, algorithm):
        allowed = self.get_allowed_algorithms()
        configured = self.get_signature_algorithm()
        if (signature_type not in allowed
                or configured not in allowed[signature_type] or algorithm != configured):
            raise ValueError('Token algorithm does not match provider configuration')
        return configured

    @api.model
    def _get_encoder(self):
        # Signing uses the configured algorithm; asymmetric verification uses header alg.
        signature_type = self.get_signature_type()
        algorithm = self.get_signature_algorithm()
        if signature_type == 'secret':
            self._require_configured_algorithm('secret', algorithm)
        elif signature_type == 'public_key':
            self._require_configured_algorithm('public_key', algorithm)
        else:
            raise ValueError('A supported signature type is required')
        return self._token_strategy(algorithm)

    def _token_strategy(self, algorithm):
        if algorithm in self.ALGORITHM_CONFIG:
            # untuk Asymmetric token signature tidak terpaku pada config.
            return TokenAsymmetric(self.env, algorithm, self.get_issuer())
        elif algorithm in self.ALGORITHM_SECRET_CONFIG:
            if algorithm != self.get_signature_algorithm():
                raise ValueError('Token algorithm does not match provider configuration')
            secret = self._get_secret()
            if not secret:
                raise ValueError('JWT Secret not set')
            return TokenSecret(self.env, algorithm, self.get_issuer(), secret)
        else:
            raise ValueError('Invalid %s', algorithm)

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
        return self.env["amr.public.key"].create(data)

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
        # sudo: preserve source parameter lookup; parameter policy deferred.
        config_parameter = self.env['ir.config_parameter'].sudo()
        value = config_parameter.get_param('amr_token.signature_type')
        if value not in ('secret', 'public_key'):
            raise ValueError('A supported signature type is required')
        return value

    @api.model
    def get_allowed_algorithms(self):
        return {
            'secret': self.ALGORITHM_SECRET_CONFIG,
            'public_key': self.ALGORITHM_CONFIG.keys(),
        }

    @api.model
    def get_signature_algorithm(self):
        # sudo: preserve source parameter lookup; parameter policy deferred.
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
        # sudo: preserve source parameter lookup; parameter policy deferred.
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.expires_in', 60 * 60 * 24))

    @api.model
    def get_retention_in(self):
        # sudo: preserve source parameter lookup; parameter policy deferred.
        return int(self.env['ir.config_parameter'].sudo().get_param('amr_token.retention_in', 60 * 60 * 4))

    @api.model
    def _get_secret(self):
        # sudo: preserve source parameter lookup; parameter policy deferred.
        return self.env['ir.config_parameter'].sudo().get_param('amr_token.secret')

    @api.model
    def get_issuer(self):
        from urllib.parse import urlparse
        # sudo: preserve source parameter lookup; parameter policy deferred.
        issuer = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        parsed = urlparse(issuer or '')
        if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('A valid HTTPS issuer is required')
        return issuer.rstrip('/')

    @api.model
    def get_audience(self):
        # sudo: preserve source parameter lookup; parameter policy deferred.
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
        # sudo: preserve source parameter lookup; parameter policy deferred.
        return {"keys": self.env["amr.public.key"].sudo().get_jwks()}

    @api.model
    def _issue_fresh_client_token(self, client_id, client_secret, scope='',
                                  expires_in=_FRESH_TTL_UNSET):
        """Authenticate one registered client and mint the opt-in fresh profile."""
        if (type(client_id) is not str or not 1 <= len(client_id) <= 1024
                or any(ord(char) <= 31 or 127 <= ord(char) <= 159 for char in client_id)
                or type(client_secret) is not str or not 1 <= len(client_secret) <= 1024):
            raise AccessError(_('Invalid client.'))
        # sudo: resolve only the exact Basic-auth client before credential checks.
        client = self.env['oidc.client'].sudo().search([
            ('client_id', '=', client_id), ('active', '=', True),
        ])
        if (len(client) != 1 or client.authentication_method != 'client_secret'
                or not client.is_confidential):
            raise AccessError(_('Invalid client.'))
        grants = client.allowed_grants.filtered(lambda grant: grant.code == 'client_credentials')
        user = client.user_id
        if (not grants or not user or not user.active or user.id == SUPERUSER_ID
                or user.share or user.has_group('base.group_public')
                or user.has_group('base.group_portal')):
            raise AccessError(_('Client is not authorized.'))
        client.check_credentials(client_secret)
        self._require_fresh_profile_instance()
        issuer = self._get_fresh_profile_issuer()
        ttl = self._get_fresh_profile_ttl()
        if expires_in is not _FRESH_TTL_UNSET:
            if type(expires_in) is not int or not 60 <= expires_in <= ttl:
                raise ValueError('Invalid fresh-profile token lifetime')
            ttl = expires_in
        if type(scope) is not str or scope:
            raise ValueError('Client scope is not authorized')
        audience = client.name or client.client_id
        if (type(audience) is not str or not 1 <= len(audience) <= 1024
                or not audience.strip()
                or any(ord(char) < 33 or 127 <= ord(char) <= 159 for char in audience)):
            raise ValueError('Client audience is not configured')
        subject = self.env['oidc.issuer.principal.subject']._get_or_create_subject(
            issuer, user.id)
        provenance = _FreshIssuanceProvenance(
            client.client_id, user.id, issuer, audience, subject)
        if self.get_signature_type() != 'public_key' or self.get_signature_algorithm() != 'RS256':
            raise ValueError('Fresh profile requires RS256 public-key signing')
        now = int(time.time())
        payload = {
            'iss': issuer, 'aud': audience, 'sub': subject,
            'iat': now, 'exp': now + ttl, 'jti': str(uuid.uuid4()),
            'client_id': client.client_id, 'azp': client.client_id,
        }
        token = self._sign_fresh_profile_token(payload, provenance)
        return {'access_token': token, 'token_type': 'Bearer', 'expires_in': ttl}

    @api.model
    def _sign_fresh_profile_token(self, payload, provenance):
        if (not isinstance(provenance, _FreshIssuanceProvenance)
                or payload.get('client_id') != provenance.client_id
                or payload.get('azp') != provenance.client_id
                or payload.get('iss') != provenance.issuer
                or payload.get('aud') != provenance.audience
                or payload.get('sub') != provenance.subject):
            raise AccessError(_('Authenticated client provenance is required.'))
        if self.get_signature_type() != 'public_key' or self.get_signature_algorithm() != 'RS256':
            raise ValueError('Fresh profile requires RS256 public-key signing')
        # sudo: resolve the single active RS256 signing key after client authorization.
        keys = self.env['amr.public.key'].sudo().search([
            ('algorithm', '=', 'RS256'), ('active', '=', True), ('is_signing', '=', True),
        ])
        if len(keys) != 1:
            raise ValueError('Exactly one active RS256 signing key is required')
        return jwt.encode(payload, keys.private_key, algorithm='RS256',
                          headers={'kid': keys.kid, 'typ': 'at+jwt'})

    @api.model
    def _fresh_profile_is_enabled(self):
        # sudo: inspect only the opt-in issuer setting at the token boundary.
        issuer = self.env['ir.config_parameter'].sudo().get_param(
            'amr_token.fresh_profile_issuer')
        if not issuer:
            return False
        self._get_fresh_profile_issuer()
        self._require_fresh_profile_instance()
        return True

    @api.model
    def _fresh_profile_instance_digest(self):
        # Entropy is operator-provisioned; enforce only a minimum input length here.
        marker = os.environ.get(_FRESH_INSTANCE_MARKER)
        if not isinstance(marker, str) or len(marker) < 32:
            raise ValueError('Fresh profile instance marker is unavailable')
        return hashlib.sha256(marker.encode('utf-8')).hexdigest()

    @api.model
    def _bind_fresh_profile_instance(self):
        # sudo: persist only a digest of the deployment-only identity marker.
        parameter = self.env['ir.config_parameter'].sudo()
        digest = self._fresh_profile_instance_digest()
        binding = parameter.get_param(_FRESH_INSTANCE_BINDING, default=False)
        if binding is not False and binding is not None:
            if not isinstance(binding, str) or not hmac.compare_digest(binding, digest):
                raise ValueError('Fresh profile instance binding does not match')
            return
        parameter.set_param(_FRESH_INSTANCE_BINDING, digest)

    @api.model
    def _require_fresh_profile_instance(self):
        # sudo: compare only deployment digest; the marker is never stored or logged.
        binding = self.env['ir.config_parameter'].sudo().get_param(_FRESH_INSTANCE_BINDING)
        digest = self._fresh_profile_instance_digest()
        if not isinstance(binding, str) or not hmac.compare_digest(binding, digest):
            raise ValueError('Fresh profile instance is not authorized')

    @api.model
    def _get_fresh_profile_issuer(self):
        from urllib.parse import urlsplit

        # sudo: read only explicit profile configuration and canonical issuer.
        issuer = self.env['ir.config_parameter'].sudo().get_param(
            'amr_token.fresh_profile_issuer')
        try:
            parsed = urlsplit(issuer or '')
            valid = (isinstance(issuer, str) and 1 <= len(issuer) <= 2048
                     and all(32 < ord(char) < 127 for char in issuer)
                     and '\\' not in issuer and parsed.scheme == 'https'
                     and parsed.hostname and parsed.username is None
                     and parsed.password is None and parsed.port in (None, 443)
                     and not parsed.query and not parsed.fragment
                     and issuer == self.get_issuer())
        except (TypeError, ValueError):
            valid = False
        if not valid:
            raise ValueError('Fresh issuer profile is not configured')
        return issuer

    @api.model
    def _get_fresh_profile_ttl(self):
        # sudo: read only the shared token lifetime; validate before signing.
        value = self.env['ir.config_parameter'].sudo().get_param('amr_token.expires_in')
        if value is None or value is False or value == '':
            return 900
        if (not isinstance(value, str) or not value.isascii()
                or not value.isdecimal() or str(int(value)) != value):
            raise ValueError('Invalid fresh-profile token lifetime configuration')
        ttl = int(value)
        if not 60 <= ttl <= 86400:
            raise ValueError('Invalid fresh-profile token lifetime configuration')
        return ttl

    @api.model
    def oidc_token(self, grant_type=None, **kwargs):
        return {
            'status': 400,
            'error': "unsupported_grant_type",
            "error_description": _("Grant Type '%s' is not supported") % grant_type
        }

    @api.model
    def _check_token_issuance_access(self, user):
        if not self.env.uid:
            raise AccessError(_('You only login.'))

        if user.id != self.env.uid and not self.env.user.has_group('base.group_system'):
            raise AccessError(_('You may only issue a token for yourself.'))

    @api.model
    def _validate_audience(self, audience):
        if isinstance(audience, str) and audience.strip():
            return audience
        if (isinstance(audience, list) and audience
                and all(isinstance(value, str) and value.strip() for value in audience)):
            return audience
        raise ValueError('A valid audience is required')

    def update_user_payload(self, user, kw):
        payload = dict(kw)
        payload.update({
            'uid': user.id,
            'user_id': user.login,
            'sub': user.login,
            'email': user.email,
            'db': self.env.cr.dbname,
        })
        return payload

    @api.model
    def _generate_user_token(self, user, audience=_AUDIENCE_UNSET, expires_in=None, scope='', **kw):
        self._check_token_issuance_access(user)
        if audience is _AUDIENCE_UNSET and 'aud' in kw:
            audience = kw.pop('aud')
        if audience is not _AUDIENCE_UNSET and 'resource' not in kw:
            audience = self._validate_audience(audience)
        payload = self.update_user_payload(user, kw)
        expires_in = expires_in or self.get_expires_in()
        access_token, payload, expires_in = self._generate_token(
            payload, audience=audience, expires_in=expires_in, scope=scope
        )
        return access_token, payload, expires_in

    @api.model
    def generate_user_token(self, user, audience=_AUDIENCE_UNSET, expires_in=None, scope='', **kw):
        """Compatibility API retained for existing amr_token consumers."""
        return self._generate_user_token(user, audience, expires_in, scope, **kw)

    @api.model
    def _generate_token(self, payload, issuer=None, expires_in=None, audience=_AUDIENCE_UNSET, scope=''):
        if 'resource' in payload:
            resource = payload.pop('resource')
            if not isinstance(resource, str) or not resource.strip():
                raise ValueError('A valid resource is required')
            audience = resource
        expires_in = expires_in or self.get_expires_in()
        expire = int(time.time()) + expires_in
        if audience is _AUDIENCE_UNSET:
            audience = self.get_audience()
        audience = self._validate_audience(audience)
        payload.update({
            'iss': self.get_issuer() or issuer,
            'aud': audience,
            'exp': expire,
            'scope': scope,
        })
        encoder = self._get_encoder()
        return encoder.encode(payload), payload, expires_in

    @api.model
    def _encode(self, **kw):
        configured = self.get_signature_algorithm()
        if any(algorithm is not None and algorithm != configured
               for algorithm in (kw.get('alg'), kw.get('algorithm'))):
            raise ValueError('Token algorithm does not match provider configuration')
        audience = kw.get('audience', kw.get('aud', _AUDIENCE_UNSET))
        scope = kw.pop('scope', '')
        kw.pop('alg', None)
        kw.pop('algorithm', None)
        kw.pop('audience', None)
        kw.pop('aud', None)
        kw.pop('iss', None)
        kw.pop('issuer', None)
        kw = self.update_user_payload(self.env.user, kw)
        token, _, _ = self._generate_token(kw, audience=audience, scope=scope)
        return token

    @api.model
    def decode(self, token, **kw):
        header = jwt.get_unverified_header(token)
        decoder = self._token_strategy(header.get('alg'))
        return decoder.decode(token, kid=header.get('kid',None), ** kw)

    @api.model
    def oidc_introspect(self, **kwargs):
        token = self.get_bearer_token()
        if not token or kwargs:
            return {'status': 401, 'active': False}
        if token:
            if kwargs.get('client_id'):
                payload = self.env['oidc.client'].decode(token, **kwargs)
            else:
                payload = self.decode(token, **kwargs)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
                # sudo: preserve source parameter lookup; parameter policy deferred.
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
            if kwargs.get('client_id'):
                payload = self.env['oidc.client'].decode(token, **kwargs)
            else:
                payload = self.decode(token, **kwargs)
            if payload and payload.get('uid'):
                uid = payload.get('uid')
                # sudo: preserve source parameter lookup; parameter policy deferred.
                user = self.env['res.users'].sudo().browse(uid)
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
