"""Static access-token verification; no Discovery, cache, or stored code."""
import base64
import functools
import json
import math
import re
import time

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from odoo import api, models, SUPERUSER_ID
from odoo.http import request
from werkzeug.exceptions import Unauthorized
from ..transport import fetch_json

AUTHORIZATION_RE = re.compile(r'^Bearer ([A-Za-z0-9\-._~+/]+=*)$')
_PROVENANCE = object()
_UNSET = object()


def _sanitized(method):
    @functools.wraps(method)
    def wrapped(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception:
            pass
        raise Unauthorized() from None
    return wrapped


def _string(value):
    return isinstance(value, str) and bool(value) and not any(ord(c) < 33 or ord(c) == 127 for c in value)


class _VerifiedClaims(dict):
    def __init__(self, claims, company, uid):
        super().__init__(claims)
        self._origin, self._company, self._uid = _PROVENANCE, company, uid
        self._snapshot = json.dumps(claims, sort_keys=True, allow_nan=False)


class ResourceHelper(models.AbstractModel):
    _name = 'amr.resource.helper'
    _description = 'Resource Server'

    def _profile(self, issuer=None, token_profile=None):
        registry = self.env['oidc.issuer.register']
        if issuer is not None:
            return registry._lookup(issuer, token_profile)
        # sudo: protected global registry read only; company context never chooses trust.
        rows = registry.sudo().with_context(active_test=False).search([
            ('active', '=', True)] +
            ([('token_profile', '=', token_profile)] if token_profile else []))
        if len(rows) != 1:
            raise Unauthorized()
        return registry._lookup(rows.issuer, token_profile)

    def _verified(self, payload):
        try:
            return (type(payload) is _VerifiedClaims and payload._origin is _PROVENANCE
                    and payload._company == self.env.company.id and payload._uid == self.env.uid
                    and payload._snapshot == json.dumps(dict(payload), sort_keys=True, allow_nan=False))
        except Exception:
            return False

    @api.model
    @_sanitized
    def is_local_issuer(self, issuer):
        return bool(self._profile(issuer).local_key_ref)

    @api.model
    @_sanitized
    def get_issuer(self):
        return self._profile().issuer

    @api.model
    def get_audience(self):
        return self.get_audiences()[0]

    @api.model
    @_sanitized
    def get_audiences(self, issuer=None):
        values = self._profile(issuer).audience_ids.mapped('value')
        if not values or any(not _string(value) for value in values) or len(set(values)) != len(values):
            raise Unauthorized()
        return values

    @api.model
    @_sanitized
    def get_oidc_config(self, issuer):
        profile = self._profile(issuer)
        return {'issuer': profile.issuer, 'jwks_uri': profile.jwks_uri or None,
                'token_endpoint': profile.token_endpoint or None,
                'introspection_endpoint': profile.introspection_endpoint or None}

    @api.model
    @_sanitized
    def get_jwks_data(self, issuer):
        profile = self._profile(issuer, 'jwt')
        if profile.local_public_key or not profile.jwks_uri:
            raise Unauthorized()
        result = fetch_json(profile.jwks_uri)
        if not isinstance(result, dict) or not isinstance(result.get('keys'), list):
            raise Unauthorized()
        return result

    def _local_public_key(self, profile):
        if not profile.local_key_ref:
            raise Unauthorized()
        # sudo: public key access only after exact trusted-profile selection.
        value = self.env['ir.config_parameter'].sudo().get_param(profile.local_key_ref)
        if not isinstance(value, str) or not value:
            raise Unauthorized()
        return value

    def _headers(self, profile, required=False):
        if not _string(profile.credential_ref):
            if required:
                raise Unauthorized()
            return {}
        # sudo: resolve only the configured protected credential reference.
        secret = self.env['ir.config_parameter'].sudo().get_param(profile.credential_ref)
        if not isinstance(secret, str) or not secret:
            raise Unauthorized()
        value = base64.b64encode((profile.client_id + ':' + secret).encode('utf-8')).decode('ascii')
        return {'Authorization': 'Basic ' + value}

    def encode(self, **kw):
        return self.generate_token(**kw).get('access_token')

    def decode(self, token, **kw):
        return self.validate(token)

    @api.model
    @_sanitized
    def generate_token(self, client_id=_UNSET, client_secret=_UNSET, iss=_UNSET,
                       issuer=_UNSET, issuer_url=_UNSET, **kw):
        selectors = [value for value in (iss, issuer, issuer_url) if value is not _UNSET]
        if (not selectors or any(not _string(value) for value in selectors)
                or any(value != selectors[0] for value in selectors[1:])):
            raise Unauthorized()
        profile = self._profile(selectors[0])
        if (client_secret is not _UNSET or
                (client_id is not _UNSET and
                 (not _string(client_id) or client_id != profile.client_id))):
            raise Unauthorized()
        if set(kw) - {'grant_type', 'scope'} or kw.get('grant_type') != 'client_credentials':
            raise Unauthorized()
        if 'scope' in kw and not isinstance(kw['scope'], str):
            raise Unauthorized()
        if not profile.token_endpoint:
            raise Unauthorized()
        result = fetch_json(profile.token_endpoint, data=kw, headers=self._headers(profile, required=True))
        if not isinstance(result, dict) or not _string(result.get('access_token')):
            raise Unauthorized()
        return result

    @api.model
    def is_local_token(self, token):
        return self.is_local_issuer(self.validate(token)['iss'])

    def _claims(self, claims, profile, opaque=False):
        if not isinstance(claims, dict):
            raise Unauthorized()
        claims = dict(claims)
        if opaque:
            if claims.get('active') is not True:
                raise Unauthorized()
            claims.setdefault('iss', profile.issuer)
        required = ('iss', 'sub', 'client_id') if opaque else ('iss', 'sub', 'client_id', 'jti')
        if any(not _string(claims.get(name)) for name in required):
            raise Unauthorized()
        if claims['iss'] != profile.issuer or claims['client_id'] != profile.client_id:
            raise Unauthorized()
        now = time.time()
        for name in ('exp', 'iat', 'nbf'):
            if name not in claims:
                if not opaque and name in ('exp', 'iat'):
                    raise Unauthorized()
                continue
            value = claims[name]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise Unauthorized()
            if (name == 'exp' and value <= now) or (name != 'exp' and value > now):
                raise Unauthorized()
        audiences = claims.get('aud')
        audiences = [audiences] if isinstance(audiences, str) else audiences
        configured = profile.audience_ids.mapped('value')
        if (not isinstance(audiences, list) or not audiences
                or any(not _string(value) for value in audiences)
                or not configured or len(set(configured)) != len(configured)
                or not any(value in configured for value in audiences)):
            raise Unauthorized()
        if 'azp' in claims:
            if not _string(claims['azp']) or claims['azp'] != profile.azp:
                raise Unauthorized()
        elif not profile.allow_missing_azp:
            raise Unauthorized()
        return claims

    @api.model
    @_sanitized
    def introspect_token(self, token, client_id=None, client_secret=None, url=None, iss=None, **kw):
        if url is not None or client_secret is not None or kw or not _string(token) or '.' in token:
            raise Unauthorized()
        profile = self._profile(iss, 'opaque')
        if client_id is not None and client_id != profile.client_id:
            raise Unauthorized()
        if not profile.introspection_endpoint:
            raise Unauthorized()
        result = fetch_json(profile.introspection_endpoint, data={'token': token}, headers=self._headers(profile))
        return _VerifiedClaims(self._claims(result, profile, opaque=True), self.env.company.id, self.env.uid)

    @api.model
    def validate_hs(self, token, **kw):
        raise Unauthorized()

    @api.model
    @_sanitized
    def validate(self, token):
        if not _string(token) or len(token) > 65536:
            raise Unauthorized()
        if '.' not in token:
            return self.introspect_token(token)
        if token.count('.') != 2:
            raise Unauthorized()
        header = jwt.get_unverified_header(token)
        if (header.get('typ') != 'at+jwt' or header.get('alg') != 'RS256'
                or any(name in header for name in ('jku', 'x5u', 'jwk', 'crit'))):
            raise Unauthorized()
        hint = jwt.decode(token, options={'verify_signature': False})
        if not _string(hint.get('iss')):
            raise Unauthorized()
        profile = self._profile(hint['iss'], 'jwt')
        self._claims(hint, profile)
        if profile.local_key_ref:
            key = serialization.load_pem_public_key(self._local_public_key(profile).encode('ascii'), default_backend())
        else:
            if not _string(header.get('kid')):
                raise Unauthorized()
            keys = self.get_jwks_data(profile.issuer)['keys']
            matches = [key for key in keys if isinstance(key, dict) and key.get('kid') == header['kid']]
            if len(matches) != 1:
                raise Unauthorized()
            jwk = matches[0]
            if (jwk.get('kty') != 'RSA' or jwk.get('alg', 'RS256') != 'RS256'
                    or jwk.get('use', 'sig') != 'sig' or any(name in jwk for name in ('d', 'p', 'q'))
                    or ('key_ops' in jwk and jwk['key_ops'] != ['verify'])):
                raise Unauthorized()
            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        if not isinstance(key, RSAPublicKey) or key.key_size < 2048:
            raise Unauthorized()
        claims = jwt.decode(token, key, algorithms=['RS256'], issuer=profile.issuer,
                            audience=profile.audience_ids.mapped('value'), leeway=0,
                            options={'require': ['iss', 'aud', 'exp', 'iat', 'jti', 'sub', 'client_id']})
        claims = self._claims(claims, profile)
        claims.setdefault('kid', header.get('kid'))
        claims.setdefault('alg', 'RS256')
        return _VerifiedClaims(claims, self.env.company.id, self.env.uid)

    @api.model
    def get_validate_user(self, token):
        return self.validate(token) or None

    def _eligible_user(self, user):
        if (getattr(user, '_name', None) != 'res.users' or len(user) != 1
                or len(user.exists()) != 1 or not user.active or user.id == SUPERUSER_ID
                or user.share or user.has_group('base.group_public') or user.has_group('base.group_portal')
                or self.env.company not in user.company_ids):
            raise Unauthorized()
        return user

    def _bound_user(self, profile, validation):
        matches = profile.binding_ids.filtered(lambda row: row.sub == validation['sub'])
        if len(matches) != 1:
            raise Unauthorized()
        return self.env['res.users'].browse(matches.user_id.id)

    @api.model
    @_sanitized
    def get_user_match(self, validation):
        if not self._verified(validation):
            raise Unauthorized()
        profile = self._profile(validation['iss'])
        if profile.resolver_mode == 'fixed_user':
            user = self.env['res.users'].browse(profile.fixed_user_id.id)
        elif profile.resolver_mode == 'get_user_match':
            user = self._bound_user(profile, validation)
        elif profile.resolver_mode == 'resolver' and profile.resolver_key == 'get_user_match':
            # Only this code-owned resolver exists in v1; no arbitrary ORM dispatch.
            user = self._bound_user(profile, validation)
        else:
            raise Unauthorized()
        return self._eligible_user(user)

    @api.model
    def get_user_token_login(self, token):
        return self.get_user_match(self.validate(token))

    @api.model
    def get_uid(self, payload):
        user = self.get_user_match(payload)
        return user and user.id

    @api.model
    def is_user_match(self, user, payload):
        return bool(user) and user.id == self.get_uid(payload)

    @classmethod
    def get_param_token(cls):
        return (request.httprequest.args.get('access_token') or request.httprequest.form.get('access_token')
                or request.httprequest.args.get('token') or request.httprequest.form.get('token')
                or request.httprequest.args.get('token_access') or request.httprequest.form.get('token_access'))

    @classmethod
    def get_header_token(cls):
        return request.httprequest.headers.get('access_token') or request.httprequest.headers.get('token')

    @classmethod
    def get_bearer_token(cls):
        authorization = (request.httprequest.environ.get('HTTP_AUTHORIZATION')
                         or request.httprequest.headers.get('Authorization'))
        if authorization is None:
            return None
        match = AUTHORIZATION_RE.fullmatch(authorization)
        if not match:
            raise Unauthorized()
        return match.group(1)
