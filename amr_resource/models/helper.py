"""Access-token verification with opt-in metadata sources; no cache or stored code."""
import base64
import functools
import json
import math
import re
import time
from urllib.parse import quote_plus, urlsplit, urlunsplit

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from odoo import api, models, SUPERUSER_ID
from odoo.http import request
from werkzeug.exceptions import Unauthorized
from ..transport import fetch_json, preflight_endpoint

AUTHORIZATION_RE = re.compile(r'^Bearer ([A-Za-z0-9\-._~+/]+=*)$')
_PROVENANCE = object()
_UNSET = object()


def _introspection_basic_header(client_id, secret):
    if not isinstance(client_id, str) or not client_id or not isinstance(secret, str) or not secret:
        raise Unauthorized()
    credentials = '%s:%s' % (quote_plus(client_id, safe=''), quote_plus(secret, safe=''))
    return 'Basic ' + base64.b64encode(credentials.encode('ascii')).decode('ascii')


def _introspection_client_id(value):
    return (type(value) is str and 1 <= len(value) <= 1024 and bool(value.strip())
            and not any(ord(char) <= 31 or 127 <= ord(char) <= 159 for char in value))


def _issuer_parts(issuer):
    if (not isinstance(issuer, str) or not issuer or any(ord(char) <= 32 or ord(char) >= 127 for char in issuer)
            or '\\' in issuer):
        raise Unauthorized()
    try:
        parsed = urlsplit(issuer)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 443)
                or parsed.query or parsed.fragment):
            raise Unauthorized()
        return parsed
    except (TypeError, ValueError):
        raise Unauthorized() from None


def _metadata_endpoint(value):
    if (not isinstance(value, str) or not value or any(ord(char) <= 32 or ord(char) >= 127 for char in value)
            or '\\' in value):
        raise Unauthorized()
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 443) or parsed.fragment):
            raise Unauthorized()
    except (TypeError, ValueError):
        raise Unauthorized() from None
    return value


def _oidc_discovery_url(issuer):
    parsed = _issuer_parts(issuer)
    path = parsed.path[:-1] if parsed.path.endswith('/') else parsed.path
    return urlunsplit((parsed.scheme, parsed.netloc, path + '/.well-known/openid-configuration', '', ''))


def _rfc8414_metadata_url(issuer):
    parsed = _issuer_parts(issuer)
    path = parsed.path.lstrip('/')
    metadata_path = '/.well-known/oauth-authorization-server'
    if path:
        metadata_path += '/' + path
    return urlunsplit((parsed.scheme, parsed.netloc, metadata_path, '', ''))


def _metadata_string_list(metadata, name):
    value = metadata.get(name)
    if (not isinstance(value, list) or not value
            or any(not isinstance(item, str) or not item for item in value)):
        raise Unauthorized()
    return value


def _parse_oidc_metadata(metadata, issuer):
    if not isinstance(metadata, dict) or metadata.get('issuer') != issuer:
        raise Unauthorized()
    _issuer_parts(issuer)
    for name in ('authorization_endpoint', 'jwks_uri'):
        _metadata_endpoint(metadata.get(name))
    response_types = _metadata_string_list(metadata, 'response_types_supported')
    _metadata_string_list(metadata, 'subject_types_supported')
    _metadata_string_list(metadata, 'id_token_signing_alg_values_supported')
    if 'token_endpoint' in metadata:
        _metadata_endpoint(metadata['token_endpoint'])
    elif any('code' in item.split() or 'token' in item.split() for item in response_types):
        raise Unauthorized()
    return metadata


def _parse_rfc8414_metadata(metadata, issuer):
    if not isinstance(metadata, dict) or metadata.get('issuer') != issuer:
        raise Unauthorized()
    _issuer_parts(issuer)
    if 'jwks_uri' in metadata:
        raise Unauthorized()
    _metadata_string_list(metadata, 'response_types_supported')
    grants = metadata.get('grant_types_supported', ['authorization_code', 'implicit'])
    if (not isinstance(grants, list) or not grants
            or any(not isinstance(item, str) or not item for item in grants)):
        raise Unauthorized()
    authorization_endpoint_optional_grants = (
        'client_credentials', 'password', 'refresh_token',
        'urn:ietf:params:oauth:grant-type:device_code')
    if 'authorization_endpoint' in metadata:
        _metadata_endpoint(metadata['authorization_endpoint'])
    elif any(grant not in authorization_endpoint_optional_grants for grant in grants):
        raise Unauthorized()
    if 'token_endpoint' in metadata:
        _metadata_endpoint(metadata['token_endpoint'])
    elif any(grant != 'implicit' for grant in grants):
        raise Unauthorized()
    if 'introspection_endpoint' not in metadata:
        raise Unauthorized()
    _metadata_endpoint(metadata['introspection_endpoint'])
    if 'introspection_endpoint_auth_methods_supported' in metadata:
        methods = _metadata_string_list(metadata, 'introspection_endpoint_auth_methods_supported')
        if 'client_secret_basic' not in methods:
            raise Unauthorized()
    return metadata


def _require_policy_revision(profile, revision):
    if not getattr(profile, 'active', False) or getattr(profile, 'policy_revision', 0) != revision:
        raise Unauthorized()


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
    def __init__(self, claims, company, uid, policy_revision):
        super().__init__(claims)
        self._origin, self._company, self._uid = _PROVENANCE, company, uid
        self._policy_revision = policy_revision
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
            if (type(payload) is not _VerifiedClaims or payload._origin is not _PROVENANCE
                    or payload._company != self.env.company.id or payload._uid != self.env.uid
                    or payload._snapshot != json.dumps(dict(payload), sort_keys=True, allow_nan=False)):
                return False
            profile = self._profile(payload['iss'])
            return payload._policy_revision == getattr(profile, 'policy_revision', 0)
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
        return self._get_oidc_config(issuer)[0]

    def _get_oidc_config(self, issuer):
        profile = self._profile(issuer)
        if getattr(profile, 'mvp_enabled', False):
            metadata_mode = getattr(profile, 'metadata_mode', None)
            if metadata_mode == 'oidc_discovery':
                if profile.token_profile != 'jwt':
                    raise Unauthorized()
                metadata = _parse_oidc_metadata(
                    fetch_json(_oidc_discovery_url(profile.issuer)), profile.issuer)
                return ({'issuer': profile.issuer, 'jwks_uri': metadata['jwks_uri'],
                         'token_endpoint': metadata.get('token_endpoint'),
                         'introspection_endpoint': None}, None)
            if metadata_mode != 'manual' or not getattr(profile, 'discovery_unavailable_declared', False) or not getattr(
                    profile, 'discovery_unavailable_evidence_ref', False):
                raise Unauthorized()
            source = getattr(profile, 'verification_source', None)
            if source == 'none':
                if (not getattr(profile, 'no_jwks_declaration', False)
                        or not getattr(profile, 'no_jwks_evidence_ref', False)
                        or profile.jwks_uri or profile.local_key_ref or profile.local_public_key):
                    raise Unauthorized()
                introspection_source = getattr(profile, 'introspection_source', None)
                if introspection_source == 'rfc8414':
                    if profile.introspection_endpoint:
                        raise Unauthorized()
                    metadata = _parse_rfc8414_metadata(
                        fetch_json(_rfc8414_metadata_url(profile.issuer)), profile.issuer)
                    return ({'issuer': profile.issuer, 'jwks_uri': None,
                             'token_endpoint': metadata.get('token_endpoint'),
                             'introspection_endpoint': metadata['introspection_endpoint']},
                            metadata.get('introspection_endpoint_auth_methods_supported'))
                if introspection_source == 'manual' and profile.introspection_endpoint:
                    return ({'issuer': profile.issuer, 'jwks_uri': None,
                             'token_endpoint': profile.token_endpoint or None,
                             'introspection_endpoint': profile.introspection_endpoint}, None)
                raise Unauthorized()
        return ({'issuer': profile.issuer, 'jwks_uri': profile.jwks_uri or None,
                 'token_endpoint': profile.token_endpoint or None,
                 'introspection_endpoint': profile.introspection_endpoint or None}, None)

    @api.model
    @_sanitized
    def get_jwks_data(self, issuer):
        profile = self._profile(issuer, 'jwt')
        if profile.local_public_key:
            raise Unauthorized()
        jwks_uri = profile.jwks_uri
        if getattr(profile, 'mvp_enabled', False):
            config = self.get_oidc_config(profile.issuer)
            jwks_uri = config['jwks_uri']
        if not jwks_uri:
            raise Unauthorized()
        result = fetch_json(jwks_uri)
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

    def _claims(self, claims, profile, opaque=False, require_jti=True):
        if not isinstance(claims, dict):
            raise Unauthorized()
        claims = dict(claims)
        if opaque:
            if claims.get('active') is not True:
                raise Unauthorized()
            claims.setdefault('iss', profile.issuer)
        required = ('iss', 'sub', 'client_id') if opaque else (
            ('iss', 'sub', 'client_id', 'jti') if require_jti else ('iss', 'sub', 'client_id'))
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

    def _mvp_introspect(self, token, profile, jwt_shaped=False, policy_revision=None):
        if (not getattr(profile, 'mvp_enabled', False)
                or getattr(profile, 'verification_source', None) != 'none'
                or getattr(profile, 'metadata_mode', None) != 'manual'
                or not getattr(profile, 'no_jwks_declaration', False)
                or not getattr(profile, 'no_jwks_evidence_ref', False)
                or profile.jwks_uri or profile.local_key_ref or profile.local_public_key
                or getattr(profile, 'introspection_source', None) not in ('manual', 'rfc8414')
                or (jwt_shaped and not getattr(profile, 'allow_jwt_introspection', False))):
            raise Unauthorized()
        policy_revision = (getattr(profile, 'policy_revision', 0)
                           if policy_revision is None else policy_revision)
        config, auth_methods = self._get_oidc_config(profile.issuer)
        _require_policy_revision(profile, policy_revision)
        endpoint = config['introspection_endpoint']
        if (getattr(profile, 'introspection_source', None) == 'rfc8414'
                and (auth_methods is None
                     and not _string(getattr(profile, 'introspection_basic_contract_ref', None)))):
            raise Unauthorized()
        if (auth_methods is not None and 'client_secret_basic' not in auth_methods):
            raise Unauthorized()
        if (not endpoint or endpoint != getattr(profile, 'introspection_credential_endpoint', None)
                or getattr(profile, 'introspection_auth_method', None) != 'client_secret_basic'
                or not _introspection_client_id(getattr(profile, 'introspection_auth_client_id', None))
                or not _string(getattr(profile, 'introspection_credential_ref', None))
                or (getattr(profile, 'introspection_source', None) == 'manual'
                    and not _string(getattr(profile, 'introspection_basic_contract_ref', None)))
                or (getattr(profile, 'introspection_source', None) == 'rfc8414'
                    and auth_methods is None
                    and not _string(getattr(profile, 'introspection_basic_contract_ref', None)))
                or ((getattr(profile, 'credential_ref', None) == getattr(
                        profile, 'introspection_credential_ref', None)
                     or getattr(profile, 'client_id', None) == getattr(
                        profile, 'introspection_auth_client_id', None))
                    and not _string(getattr(profile, 'introspection_basic_contract_ref', None)))):
            raise Unauthorized()
        if getattr(profile, 'introspection_source', None) == 'manual' and not profile.introspection_endpoint:
            raise Unauthorized()
        try:
            preflight = preflight_endpoint(endpoint)
        except Exception:
            raise Unauthorized() from None
        # Resolve and pin the exact safe endpoint before reading its credential.
        secret = self.env['ir.config_parameter'].sudo().get_param(profile.introspection_credential_ref)
        authorization = _introspection_basic_header(profile.introspection_auth_client_id, secret)
        result = fetch_json(endpoint, data={'token': token},
                            headers={'Authorization': authorization}, preflight=preflight)
        _require_policy_revision(profile, policy_revision)
        if not jwt_shaped and isinstance(result, dict) and 'iss' not in result and not getattr(
                profile, 'allow_introspection_iss_absent', False):
            raise Unauthorized()
        if jwt_shaped:
            if not isinstance(result, dict) or result.get('active') is not True:
                raise Unauthorized()
            if 'iss' not in result:
                if not getattr(profile, 'allow_introspection_iss_absent', False):
                    raise Unauthorized()
                result = dict(result, iss=profile.issuer)
        claims = self._claims(result, profile, opaque=not jwt_shaped, require_jti=not jwt_shaped)
        if jwt_shaped and any(name not in claims for name in ('iss', 'exp', 'iat')):
            raise Unauthorized()
        if 'token_type' in claims and (not isinstance(claims['token_type'], str)
                or claims['token_type'].lower() != 'bearer'):
            raise Unauthorized()
        return _VerifiedClaims(claims, self.env.company.id, self.env.uid,
                               getattr(profile, 'policy_revision', 0))

    @api.model
    @_sanitized
    def introspect_token(self, token, client_id=None, client_secret=None, url=None, iss=None, **kw):
        if url is not None or client_secret is not None or kw or not _string(token) or '.' in token:
            raise Unauthorized()
        profile = self._profile(iss, 'opaque')
        policy_revision = getattr(profile, 'policy_revision', 0)
        if client_id is not None and client_id != profile.client_id:
            raise Unauthorized()
        if getattr(profile, 'mvp_enabled', False):
            return self._mvp_introspect(token, profile, policy_revision=policy_revision)
        if not profile.introspection_endpoint:
            raise Unauthorized()
        result = fetch_json(profile.introspection_endpoint, data={'token': token}, headers=self._headers(profile))
        return _VerifiedClaims(self._claims(result, profile, opaque=True), self.env.company.id,
                               self.env.uid, getattr(profile, 'policy_revision', 0))

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
        if (header.get('typ') != 'at+jwt' or header.get('alg') not in ('RS256', 'PS256')
                or any(name in header for name in ('jku', 'x5u', 'jwk', 'crit'))):
            raise Unauthorized()
        hint = jwt.decode(token, options={'verify_signature': False})
        if not _string(hint.get('iss')):
            raise Unauthorized()
        profile = self._profile(hint['iss'], 'jwt')
        policy_revision = getattr(profile, 'policy_revision', 0)
        enabled_algorithms = (profile._verification_algorithms({})
                              if getattr(profile, 'mvp_enabled', False) else frozenset(['RS256']))
        if header.get('alg') not in enabled_algorithms:
            raise Unauthorized()
        self._claims(hint, profile)
        if getattr(profile, 'mvp_enabled', False) and getattr(profile, 'verification_source', None) == 'none':
            if not getattr(profile, 'allow_jwt_introspection', False):
                raise Unauthorized()
            return self._mvp_introspect(token, profile, jwt_shaped=True,
                                        policy_revision=policy_revision)
        if profile.local_key_ref:
            key = serialization.load_pem_public_key(self._local_public_key(profile).encode('ascii'), default_backend())
        else:
            if not _string(header.get('kid')):
                raise Unauthorized()
            keys = self.get_jwks_data(profile.issuer)['keys']
            _require_policy_revision(profile, policy_revision)
            matches = [key for key in keys if isinstance(key, dict) and key.get('kid') == header['kid']]
            if len(matches) != 1:
                raise Unauthorized()
            jwk = matches[0]
            if (jwk.get('kty') != 'RSA' or jwk.get('alg', header['alg']) != header['alg']
                    or jwk.get('use', 'sig') != 'sig'
                    or any(name in jwk for name in ('d', 'p', 'q', 'dp', 'dq', 'qi', 'oth', 'k'))
                    or ('key_ops' in jwk and jwk['key_ops'] != ['verify'])):
                raise Unauthorized()
            if getattr(profile, 'mvp_enabled', False):
                if header['alg'] not in profile._verification_algorithms(jwk):
                    raise Unauthorized()
            elif header['alg'] != 'RS256':
                raise Unauthorized()
            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        if not isinstance(key, RSAPublicKey) or key.key_size < 2048:
            raise Unauthorized()
        claims = jwt.decode(token, key, algorithms=[header['alg']], issuer=profile.issuer,
                            audience=profile.audience_ids.mapped('value'), leeway=0,
                            options={'require': ['iss', 'aud', 'exp', 'iat', 'jti', 'sub', 'client_id']})
        claims = self._claims(claims, profile)
        claims.setdefault('kid', header.get('kid'))
        claims.setdefault('alg', 'RS256')
        _require_policy_revision(profile, policy_revision)
        return _VerifiedClaims(claims, self.env.company.id, self.env.uid, policy_revision)

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

    @staticmethod
    def _mapping_claim_value(key, value):
        if (not isinstance(key, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', key)
                or not isinstance(value, str) or not 1 <= len(value) <= 1024
                or not value.strip()
                or any(ord(char) <= 31 or 127 <= ord(char) <= 159 for char in value)):
            raise Unauthorized()
        return value

    def _find_mapping_users(self, field_name, exact_value):
        if field_name not in ('login', 'partner_id.email'):
            raise Unauthorized()
        users = self.env['res.users'].sudo().with_context(active_test=False).search(
            [(field_name, '=', exact_value)])
        matched = []
        seen = set()
        for user in users:
            actual = user.login if field_name == 'login' else user.partner_id.email
            if type(actual) is str and actual == exact_value and user.id not in seen:
                seen.add(user.id)
                matched.append(user)
        return matched

    def _mapping_user(self, profile, validation):
        if not getattr(profile, 'mvp_enabled', False):
            raise Unauthorized()
        rows = profile.user_mapping_ids
        seen_sequences = set()
        active_rows = []
        for row in rows:
            if (type(row.sequence) is not int or row.sequence <= 0
                    or type(row.active) is not bool
                    or row.field_user not in ('login', 'partner_id.email')
                    or row.sequence in seen_sequences):
                raise Unauthorized()
            self._mapping_claim_value(row.jwt_key, 'schema-check')
            seen_sequences.add(row.sequence)
            if row.active:
                active_rows.append(row)
        if not active_rows or len(active_rows) > 20:
            raise Unauthorized()
        candidate_ids = set()
        for row in sorted(active_rows, key=lambda item: item.sequence):
            if row.jwt_key not in validation:
                raise Unauthorized()
            value = self._mapping_claim_value(row.jwt_key, validation[row.jwt_key])
            matches = self._find_mapping_users(row.field_user, value)
            ids = {user.id for user in matches}
            if len(ids) > 1:
                raise Unauthorized()
            if ids:
                candidate_ids = ids
                break
        if len(candidate_ids) != 1:
            raise Unauthorized()
        candidate_id = next(iter(candidate_ids))
        bindings = profile.binding_ids.filtered(lambda row: row.sub == validation['sub'])
        if len(bindings) != 1 or bindings.user_id.id != candidate_id:
            raise Unauthorized()
        return self.env['res.users'].browse(candidate_id)

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
        elif profile.resolver_mode == 'mapping' and getattr(profile, 'mvp_enabled', False):
            user = self._mapping_user(profile, validation)
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
