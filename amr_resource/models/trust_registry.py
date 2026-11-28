# -*- coding: utf-8 -*-
"""Global trust configuration; no discovery or stored-code execution."""

import base64
import os
import token
import jwt
import hashlib
import ipaddress
import json
import logging
import re

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from urllib.parse import quote_plus, urlsplit
from odoo import api, fields, models, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
from werkzeug.exceptions import Unauthorized

from ..transport import fetch_json
from .oidc_alogritma import ALGORITHM_CATALOG

_logger = logging.getLogger(__name__)

TRUST_GROUP = 'amr_resource.group_oidc_trust_admin'
CODE_GROUP = 'amr_resource.group_oidc_code_admin'
POLICY_CHILD_MODELS = {'oidc.issuer.register.audience', 'oidc.issuer.subject',
                       'oidc.issuer.user.mapping', 'oidc.issuer.algorithm.policy'}

_PROVENANCE = object()


def _invalidate_request_policy():
    try:
        current_request = request._get_current_object() if request else None
    except RuntimeError:
        current_request = None
    if current_request is not None:
        current_request._trust_generation = getattr(current_request, '_trust_generation', 0) + 1


def _string(value):
    return isinstance(value, str) and bool(value) and not any(ord(c) < 33 or ord(c) == 127 for c in value)


class _VerifiedClaims(dict):
    def __init__(self, claims, uid):
        super().__init__(claims)
        self._origin, self._uid = _PROVENANCE, uid
        self._request = request._get_current_object()
        self._generation = getattr(self._request, '_trust_generation', 0)
        self._snapshot = json.dumps(claims, sort_keys=True, allow_nan=False)

def _policy_algorithms(policy, key_metadata):
    """Return only algorithms supported by code, enabled for issuer and key."""
    if not isinstance(policy, (list, tuple)) or not isinstance(key_metadata, dict):
        raise ValidationError('Algorithm policy is invalid.')
    enabled = set()
    for row in policy:
        if (not isinstance(row, (list, tuple)) or len(row) != 2
                or not isinstance(row[0], str) or type(row[1]) is not bool
                or row[0] not in ALGORITHM_CATALOG):
            raise ValidationError('Algorithm policy is invalid.')
        if row[1]:
            enabled.add(row[0])
    allowed = {name for name in enabled
               if ALGORITHM_CATALOG[name]['support_state'] == 'supported'}
    key_algorithm = key_metadata.get('alg')
    if key_algorithm is not None:
        allowed = {name for name in allowed if name == key_algorithm}
    if not allowed:
        raise ValidationError('No configured algorithm is supported by the trusted key.')
    return frozenset(allowed)


def _exact_string(value):
    return isinstance(value, str) and bool(value) and not any(
        ord(char) < 33 or ord(char) == 127 for char in value)


def _https_url(value):
    """Configuration syntax only; DNS/address checks belong at connection time."""
    if not _exact_string(value):
        return False
    try:
        url = urlsplit(value)
        if (url.scheme != 'https' or not url.hostname or url.username is not None
                or url.password is not None or url.port not in (None, 443)
                or url.fragment or '\\' in value):
            return False
        host = url.hostname.rstrip('.').lower()
        if host == 'localhost' or host.endswith('.localhost'):
            return False
        try:
            address = ipaddress.ip_address(host)
            return (address.is_global and not address.is_multicast
                    and not address.is_reserved and not address.is_loopback
                    and not address.is_link_local and not address.is_unspecified)
        except ValueError:
            return True
    except ValueError:
        return False


def _validate_mapping_claim(key, value):
    """Validate a literal top-level claim value without normalizing it."""
    import re

    if (not isinstance(key, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', key)
            or not isinstance(value, str) or not 1 <= len(value) <= 1024
            or not value.strip()
            or any(ord(char) <= 31 or 127 <= ord(char) <= 159 for char in value)):
        raise ValidationError('Mapping claim is missing or invalid.')
    return value


def _validate_mapping_rows(rows):
    """Validate the bounded, literal mapping schema shared by model and resolver."""
    if not isinstance(rows, (list, tuple)):
        raise ValidationError('Mapping configuration is invalid.')
    sequences = set()
    active = 0
    for row in rows:
        if (not isinstance(row, dict) or set(row) !=
                {'sequence', 'field_user', 'jwt_key', 'active'}
                or type(row['sequence']) is not int or row['sequence'] <= 0
                or row['field_user'] not in ('login', 'partner_id.email')
                or type(row['active']) is not bool or row['sequence'] in sequences):
            raise ValidationError('Mapping configuration is invalid.')
        _validate_mapping_claim(row['jwt_key'], 'valid')
        sequences.add(row['sequence'])
        active += int(row['active'])
    if active > 20:
        raise ValidationError('Mapping configuration is invalid.')
    return True


class OidcResourceIssuer(models.Model):
    _name = 'oidc.issuer.register'
    _description = 'Resource Token Issuer'
    _rec_name = 'issuer'
    _order = 'sequence, id'
    _inherit = ['mail.thread']

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=20)
    state = fields.Selection([('draft', 'Draft'), ('production', 'Production'), ('disable', 'Disable')], default='draft')
    issuer = fields.Char(required=True, index=True)
    token_profile = fields.Selection(
        [('jwt', 'JWT Access Token'), ('opaque', 'Opaque Access Token')], required=True, default='jwt'
    )
    jwks_uri = fields.Char()
    token_endpoint = fields.Char()
    introspection_endpoint = fields.Char()
    client_id = fields.Char(required=True)
    azp = fields.Char()
    allow_missing_azp = fields.Boolean(default=False)
    credential_source = fields.Selection(
        [
            ("none", "None"),
            ("database", "Database"),
            ("env", "Environment"),
            ("system_parameter", "System Parameter"),
        ],
        groups=TRUST_GROUP,
        default="none",
        required=True,
        help="Client credentials grant requires authentication regardless of source."
    )
    credential_ref = fields.Char(groups=TRUST_GROUP)
    credential_value = fields.Char(groups=TRUST_GROUP)

    resolver_mode = fields.Selection([('get_user_match', 'Default'),
                                      ('fixed_user', 'Fixed User'),
                                      ('mapping', 'Ordered Claim Mapping'),
                                      ('code', 'Python Code'),]) 
    python_code = fields.Text(groups=CODE_GROUP, copy=False, readonly=True,
                              help='Execution is disabled.')
    
    fixed_user_id = fields.Many2one('res.users', readonly=True, ondelete='restrict') 
    audience_ids = fields.One2many('oidc.issuer.register.audience', 'issuer_id')
    binding_ids = fields.One2many('oidc.issuer.subject', 'issuer_id')
    user_mapping_ids = fields.One2many('oidc.issuer.user.mapping', 'issuer_id')
    algorithm_policy_ids = fields.One2many('oidc.issuer.algorithm.policy', 'issuer_id')

    _sql_constraints = [('issuer_unique', 'unique(issuer)', 'Issuer must be unique.')]
    
    @api.constrains('issuer', 'token_profile', 'jwks_uri', 'token_endpoint', 'client_id')
    def _check_endpoints(self):
        for record in self:
            try:
                issuer = urlsplit(record.issuer or '')
                valid_issuer = (_exact_string(record.issuer) and issuer.scheme == 'https'
                                and issuer.hostname and issuer.username is None
                                and issuer.password is None and not issuer.query and not issuer.fragment
                                and '\\' not in record.issuer and issuer.port in (None, 443))
            except ValueError:
                valid_issuer = False
            if not valid_issuer or not _exact_string(record.client_id):
                raise ValidationError('A valid exact HTTPS issuer and client ID are required.')
            for endpoint in (record.jwks_uri, record.token_endpoint, record.introspection_endpoint):
                if endpoint and not _https_url(endpoint):
                    raise ValidationError('Endpoints must be public HTTPS URLs on port 443.')
    def _registry_role(self, group):
        return self.env.user.has_group(group)

    def _check_draft_state(self):
        if self.filtered(lambda issuer: issuer.state != 'draft'):
            raise ValidationError('Only Draft State can Edit')

    def action_set_state(self, target):
        if not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        transitions = {'draft': {'production', 'disable'},
                       'production': {'draft', 'disable'},
                       'disable': {'draft', 'production'}}
        for record in self:
            if (target not in transitions.get(record.state, set())
                    or (not record.active and target != 'draft')):
                raise ValidationError('Invalid issuer state transition.')
        result = super(OidcResourceIssuer, self).write(
            {'state': target, 'active': True} if target != 'disable' else {'state': target})
        _invalidate_request_policy()
        return result

    def action_to_production(self):
        return self.action_set_state('production')

    def action_to_draft(self):
        return self.action_set_state('draft')

    def action_to_disable(self):
        return self.action_set_state('disable')

    def copy(self, default=None):
        default = dict(default or {})
        default['state'] = 'draft'
        return super(OidcResourceIssuer, self).copy(default)

    def unlink(self):
        if not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        if self.filtered(lambda record: record.state != 'disable'):
            raise ValidationError('Only disabled issuers can be archived.')
        return super(OidcResourceIssuer, self).write({'active': False})

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for values in vals_list:
            values = dict(values)
            values['state'] = 'draft'
            prepared.append(values)
        _invalidate_request_policy()
        return super(OidcResourceIssuer, self).create(prepared)

    def write(self, values):
        _invalidate_request_policy()
        unarchiving = self.filtered(lambda record: not record.active) if values == {'active': True} else self.browse()
        if unarchiving and not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        others = self - unarchiving
        if not values.get('active',True):
            super(OidcResourceIssuer, others).write({'active': False})
        elif others:
            state = values.get('state',None)  
            if (state and values.get('state',None) != 'draft') or others.filtered(lambda record: record.state != 'draft'):
                raise ValidationError('Only Draft State can Edit')
            super(OidcResourceIssuer, others).write(values)
        if unarchiving:
            super(OidcResourceIssuer, unarchiving).write(dict(values, state='draft'))
        
        return True

    @staticmethod
    def _validate_snapshot_algorithms(payload):
        rows = payload.get('algorithms')
        if not isinstance(rows, list):
            raise ValidationError('Snapshot algorithm policy is invalid.')
        names, enabled = set(), set()
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {'name', 'enabled'}
                    or row['name'] not in ALGORITHM_CATALOG or type(row['enabled']) is not bool
                    or row['name'] in names):
                raise ValidationError('Snapshot algorithm policy is invalid.')
            names.add(row['name'])
            if row['enabled']:
                if ALGORITHM_CATALOG[row['name']]['support_state'] != 'supported':
                    raise ValidationError('Snapshot enables an unsupported algorithm.')
                enabled.add(row['name'])
        if payload.get('mvp_enabled') and not enabled:
            raise ValidationError('MVP snapshot requires a supported enabled algorithm.')

    def _verification_algorithms(self, key_metadata):
        self.ensure_one()
        policy = [(row.algorithm_id.name, row.enabled) for row in self.algorithm_policy_ids]
        return _policy_algorithms(policy, key_metadata)
    
    @api.model
    def _lookup_default(self):
        """Select a unique highest-priority active production opaque issuer."""
        # sudo: read only global trust configuration, independent of company.
        rows = self.sudo().with_context(active_test=False).search([
            ('active', '=', True), ('state', '=', 'production'),
            ('token_profile', '=', 'opaque')], order='sequence, id', limit=2)
        if not rows or (len(rows) > 1 and rows[0].sequence == rows[1].sequence):
            raise Unauthorized()
        return rows[0]
    
    @api.model
    def _lookup(self, issuer=None, token_profile=None):
        """Private runtime read only: never use this elevation to execute a resolver."""
        if not _exact_string(issuer) or token_profile not in (None, 'jwt', 'opaque'):
            raise Unauthorized()
        try:
            # sudo: read protected global trust rows; user eligibility remains request-scoped.
            records = self.sudo().with_context(active_test=False).search([
                ('issuer', '=', issuer), ('active', '=', True), ('state', '=', 'production')])
            if len(records) != 1 or (token_profile and records.token_profile != token_profile):
                raise Unauthorized()
            return records
        except Exception:
            raise Unauthorized() from None

    def _headers(self, required=False):
        if not _string(self.client_id):
            raise Unauthorized()
        if self.credential_source=='none':
            if required:
                raise ValueError("Invalid Configuration Issuer Credential Source")
            return {}
        else:    
            # sudo: resolve only the configured protected credential reference.
            secret = self._get_credential()
            if not _string(secret):
                if required:
                    raise Unauthorized()
                return {}

            value = base64.b64encode((quote_plus(self.client_id) + ':' + quote_plus(secret)).encode('ascii')).decode('ascii')
            return {'Authorization': 'Basic ' + value}
    
    def _profile(self, issuer=None, token_profile=None):
        registry = self.env['oidc.issuer.register']
        if issuer is not None:
            return registry._lookup(issuer, token_profile)
        # sudo: protected global registry read only; company context never chooses trust.
        rows = registry.sudo().search(
            [('active', '=', True), ('state', '=', 'production')] + ([('token_profile', '=', token_profile)] if token_profile else [])
        )
        if len(rows) != 1:
            raise Unauthorized()
        return registry._lookup(rows.issuer, token_profile)
    
    def encode(self, **kw):
        if set(kw) - {'grant_type', 'scope'} or kw.get('grant_type') != 'client_credentials':
            raise Unauthorized()
        if 'scope' in kw and not isinstance(kw['scope'], str):
            raise Unauthorized()
        if not self.token_endpoint:
            raise Unauthorized()
        result = fetch_json(self.token_endpoint, data=kw, headers=self._headers(required=True))
        if not isinstance(result, dict) or not _string(result.get('access_token')):
            raise Unauthorized()
        return result.get('access_token')

    def introspect_token(self, token, **kw):
        self.ensure_one()
        if not _string(self.client_id):
            raise Unauthorized()
        return fetch_json(self.introspection_endpoint, data={'token': token, 'client_id': self.client_id})

    def support_algorithm(self, alg):
        if any(getattr(getattr(policy, 'algorithm_id', None), 'name', None) != 'RS256'
               for policy in getattr(self, 'algorithm_policy_ids', ())):
            return False
        enabled_algorithms = (self._verification_algorithms({})
                              if getattr(self, 'mvp_enabled', False) else frozenset(['RS256']))
        if alg not in enabled_algorithms:
            return False

        return True

    def claims(self, claims, opaque=False, require_jti=True):
        import time
        import math
        profile = self.ensure_one()
        if not isinstance(claims, dict):
            raise Unauthorized()
        claims = dict(claims)
        if opaque:
            if claims.get('active') is not True:
                raise Unauthorized()
            if 'exp' not in claims:
                raise Unauthorized()
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
    
    def get_public_key(self, header):
        """alwaise return public key or raise Exception"""
        try:
            jwks_data = self.get_jwks_data()
            keys = jwks_data.get('keys')
            if not isinstance(keys, list) or not keys:
                raise Unauthorized()
        except Exception:
            raise Unauthorized()
        seen_kids = set()
        candidates = {}
        for candidate in keys:
            if not isinstance(candidate, dict):
                        continue
            candidate_kid = candidate.get('kid')
            if (type(candidate_kid) is not str or not candidate_kid or len(candidate_kid) > 256
                            or any(character.isspace() or ord(character) < 32 or ord(character) == 127
                                   or 0x80 <= ord(character) <= 0x9f for character in candidate_kid)
                            or candidate_kid in seen_kids):
                continue
                    
            if (candidate.get('kty') != 'RSA'
                            or candidate.get('use', 'sig') != 'sig'
                            or ('alg' in candidate and candidate['alg'] != header.get('alg'))
                            or any(name in candidate for name in ('d', 'p', 'q', 'dp', 'dq', 'qi', 'oth', 'k'))
                            or ('key_ops' in candidate and candidate['key_ops'] != ['verify'])):
                continue
            try:
                parsed_candidate = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(candidate))
            except Exception:
                continue
            if not isinstance(parsed_candidate, RSAPublicKey) or parsed_candidate.key_size < 2048:
                continue
            seen_kids.add(candidate_kid)
            candidates[candidate_kid] = parsed_candidate

        if header.get('kid') not in candidates:
            raise Unauthorized()
        return candidates[header['kid']]
    
    def is_local_token(self):
        return False
    
    def local_decode(self, token, **kw):
        raise Unauthorized()
    
    def decode(self, token, **kw):
        if not _string(token) or len(token) > 65536:
            raise Unauthorized()
        if token.count('.') != 2:
            profile = self._lookup_default()
            if self and self.ensure_one() != profile:
                raise Unauthorized()
            if profile.is_local_token():
                raise Unauthorized()
            try:
                claims = profile.claims(profile.introspect_token(token), opaque=True)
                return _VerifiedClaims(claims, self.env.uid)
            except Exception:
                raise Unauthorized() from None
        hint = jwt.decode(token, options={'verify_signature': False})
        if not _string(hint.get('iss')):
            raise Unauthorized()
        profile = self._lookup(hint['iss'], 'jwt')
        if self and self.ensure_one() != profile:
            raise Unauthorized()
        if profile.is_local_token():
            raise Unauthorized()

        header = jwt.get_unverified_header(token)
        if (not _string(header.get('kid')) or not profile.support_algorithm(header.get('alg'))
                or header.get('typ') != 'at+jwt'
                or any(name in header for name in ('jku', 'x5u', 'jwk', 'crit'))):
            raise Unauthorized()
        key = profile.get_public_key(header)
        claims = jwt.decode(token, key, algorithms=[header['alg']], issuer=profile.issuer,
                            audience=profile.audience_ids.mapped('value'), leeway=0,
                            options={'require': ['iss', 'aud', 'exp', 'iat', 'jti', 'sub', 'client_id']})
        claims = profile.claims(claims)
        claims.setdefault('kid', header.get('kid'))
        claims.setdefault('alg', header['alg'])
        return _VerifiedClaims(claims, self.env.uid)

    def _get_credential(self):
        if self.credential_source == 'database':
            return self.credential_value
        elif self.credential_source == 'system_parameter':
            return self.env['ir.config_parameter'].sudo().get_param(self.credential_ref)
        elif self.credential_source == 'env':
            return os.getenv(self.credential_ref)
        else:
            raise ValueError("Invalid credential_source")

    # @api.model
    # def get_validate_user(self, token):
        # return self.decode(token) or None
    
    @api.model
    def get_user_token_login(self, token):
        validation = self.decode(token)
        user = self.get_user_match(validation)
        return user

    def _rebind_verified(self, payload, uid):
        if not self._verified(payload):
            raise Unauthorized()
        return _VerifiedClaims(payload, uid)

    @api.model
    def get_uid(self, payload):
        user = self.get_user_match(payload)
        return user and user.id

    @api.model
    def is_user_match(self, user, payload):
        return bool(user) and user.id == self.get_uid(payload)
    
    def _eligible_user(self, user):
        # Read only eligibility attributes; return the original unprivileged record.
        checked = user.sudo()
        if (getattr(user, '_name', None) != 'res.users' or len(user) != 1
                or len(checked.exists()) != 1 or not checked.active or checked.id == SUPERUSER_ID
                or checked.share or checked.has_group('base.group_public') or checked.has_group('base.group_portal')):
            raise Unauthorized()
        return user

    def _bound_user(self, validation):
        if self:
            profile = self
        else:
            if not self._verified(validation):
                raise Unauthorized()
            profile = self._profile(validation['iss'])
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

    def _mapping_user(self, validation):
        if self:
            profile = self
        else:
            if not self._verified(validation):
                raise Unauthorized()
            profile = self._profile(validation['iss'])
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

    def get_user_match(self, validation):
        if not self._verified(validation):
            raise Unauthorized()
        profile = self._profile(validation['iss'])
        if self and self != profile:
            raise Unauthorized()

        if profile.resolver_mode == 'fixed_user':
            user = self.env['res.users'].browse(profile.fixed_user_id.id)
        elif profile.resolver_mode == 'get_user_match':
            user = self._bound_user(validation)
        elif profile.resolver_mode == 'mapping':
            user = self._mapping_user(validation)
        elif profile.resolver_mode == 'code':
            # Only this code-owned resolver exists in v1; no arbitrary ORM dispatch.
            # need implment code
            raise NotImplemented 
        else:
            raise Unauthorized()
        user = self._eligible_user(user)
        return user

    def _verified(self, payload, raise_exeption=True):
        import math
        import time
        try:
            if (type(payload) is not _VerifiedClaims or payload._origin is not _PROVENANCE
                    or payload._request is not request._get_current_object() or payload._uid != self.env.uid
                    or payload._generation != getattr(payload._request, '_trust_generation', 0)
                    or type(payload.get('exp')) not in (int, float)
                    or not math.isfinite(payload['exp']) or payload['exp'] <= time.time()
                    or payload._snapshot != json.dumps(dict(payload), sort_keys=True, allow_nan=False)):
                return False
            self._profile(payload['iss'])
            return True
        except Exception:
            return False
    
    def get_jwks_uri_default(self):
        return self.issuer + '/.well-known/jwks.json'
    
    def get_jwks_data(self):
        profile = self
        if profile.token_profile != 'jwt':
            raise Unauthorized()
        jwks_uri = profile.jwks_uri or profile.get_jwks_uri_default()
        result = fetch_json(jwks_uri)
        if not isinstance(result, dict) or not isinstance(result.get('keys'), list):
            raise Unauthorized()
        return result
    
    def get_openid_configuration_default(self):
        return self.issuer + '/.well-known/openid-configuration'
    
    def get_openid_configuration(self):
        profile = self
        openid_configuration_url = profile.issuer + '/.well-known/openid-configuration'
        result = fetch_json(openid_configuration_url)
        return result
    
def _check_parent_issuers_draft(records, issuer_field='issuer_id'):
    records.mapped(issuer_field)._check_draft_state()
    _invalidate_request_policy()


class OidcPolicySnapshot(models.Model):
    _name = 'oidc.issuer.policy.snapshot'
    _description = 'Immutable Issuer Policy Recovery Snapshot'
    #_inherit = 'amr.resource.registry.access'
    _rec_name = 'id'

    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='restrict', index=True)
    captured_revision = fields.Integer(required=True, readonly=True)
    payload = fields.Text(required=True, readonly=True)
    integrity_digest = fields.Char(required=True, readonly=True, size=64)
    evidence_ref = fields.Char(required=True, readonly=True, size=512)
    actor_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')
    captured_at = fields.Datetime(required=True, readonly=True)
    invalidated = fields.Boolean(default=False, readonly=True)
    invalidated_actor_id = fields.Many2one('res.users', readonly=True, ondelete='restrict')
    invalidated_at = fields.Datetime(readonly=True)
    invalidation_reason = fields.Char(readonly=True, size=64)

    @api.model_create_multi
    def create(self, vals_list):
        raise AccessError('Snapshots are created only by the validated issuer action.')

    def write(self, values):
        raise AccessError('Snapshot content is immutable.')

    def unlink(self):
        raise AccessError('Snapshots are append-only.')

    def action_invalidate(self):
        if not self.env['oidc.issuer.register']._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        self.check_access_rights('read')
        self.check_access_rule('read')
        for snapshot in self:
            if snapshot.invalidated:
                raise ValidationError('Snapshot is already invalidated.')
        for snapshot in self:
            super(OidcPolicySnapshot, snapshot.sudo()).write({
                'invalidated': True, 'invalidated_actor_id': self.env.uid,
                'invalidated_at': fields.Datetime.now(), 'invalidation_reason': 'snapshot_invalidated'})
            _logger.info(
                'Trust policy snapshot invalidated issuer_id=%s snapshot_id=%s actor=%s reason_code=%s timestamp=%s',
                snapshot.issuer_id.id, snapshot.id, self.env.uid,
                'snapshot_invalidated', fields.Datetime.now())
        return True


class AmrResourceAudience(models.Model):
    _name = 'oidc.issuer.register.audience'
    _description = 'Resource Issuer Audience'
    #_inherit = 'amr.resource.registry.access'
    _rec_name = 'value'

    @api.model_create_multi
    def create(self, vals_list):
        self.env['oidc.issuer.register'].browse([v['issuer_id'] for v in vals_list if v.get('issuer_id')])._check_draft_state()
        _invalidate_request_policy()
        return super(AmrResourceAudience, self).create(vals_list)

    value = fields.Char(required=True)
    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    _sql_constraints = [('audience_unique', 'unique(issuer_id, value)', 'Audience must be unique per issuer.')]

    @api.constrains('value')
    def _check_value(self):
        for record in self:
            if not _exact_string(record.value):
                raise ValidationError('An exact nonempty audience is required.')

    def write(self, values):
        _check_parent_issuers_draft(self)
        if values.get('issuer_id'):
            self.env['oidc.issuer.register'].browse(values['issuer_id'])._check_draft_state()
        parents = self.mapped('issuer_id') if 'issuer_id' in values else self.env['oidc.issuer.register']
        result = super(AmrResourceAudience, self).write(values)
        if parents.exists().filtered(lambda record: not record.audience_ids):
            raise ValidationError('At least one audience is required.')
        return result

    def unlink(self):
        _check_parent_issuers_draft(self)
        parents = self.mapped('issuer_id')
        result = super(AmrResourceAudience, self).unlink()
        if parents.exists().filtered(lambda record: not record.audience_ids):
            raise ValidationError('At least one audience is required.')
        return result


class AmrResourceBinding(models.Model):
    _name = 'oidc.issuer.subject'
    _description = 'Resource Issuer Subject Binding'
    #_inherit = 'amr.resource.registry.access'
    _rec_name = 'sub'

    @api.model_create_multi
    def create(self, vals_list):
        issuers = self.env['oidc.issuer.register'].browse([v['issuer_id'] for v in vals_list if v.get('issuer_id')])
        issuers._check_draft_state()
        _invalidate_request_policy()
        return super(AmrResourceBinding, self).create(vals_list)

    def write(self, values):
        _check_parent_issuers_draft(self)
        if values.get('issuer_id'):
            self.env['oidc.issuer.register'].browse(values['issuer_id'])._check_draft_state()
        return super(AmrResourceBinding, self).write(values)

    def unlink(self):
        _check_parent_issuers_draft(self)
        return super(AmrResourceBinding, self).unlink()

    sub = fields.Char(required=True)
    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    _sql_constraints = [('binding_unique', 'unique(issuer_id, sub)', 'Subject must be unique per issuer.')]

    @api.constrains('sub', 'user_id', 'issuer_id')
    def _check_binding(self):
        for record in self:
            if not _exact_string(record.sub):
                raise ValidationError('An exact nonempty subject is required.')
            user = record.user_id
            if (not user.active or user.id == SUPERUSER_ID or user.share
                    or user.has_group('base.group_public') or user.has_group('base.group_portal')):
                raise ValidationError('Binding requires an active eligible internal user.')


class AmrResourceUserMapping(models.Model):
    _name = 'oidc.issuer.user.mapping'
    #_inherit = 'amr.resource.registry.access'
    _description = 'Issuer User Claim Mapping'
    _rec_name = 'jwt_key'

    @api.model_create_multi
    def create(self, vals_list):
        self.env['oidc.issuer.register'].browse([v['issuer_id'] for v in vals_list if v.get('issuer_id')])._check_draft_state()
        _invalidate_request_policy()
        return super(AmrResourceUserMapping, self).create(vals_list)

    def unlink(self):
        _check_parent_issuers_draft(self)
        return super(AmrResourceUserMapping, self).unlink()

    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(required=True, default=10)
    active = fields.Boolean(default=True)
    field_user = fields.Selection([('login', 'User Login'),
                                   ('partner_id.email', 'Partner Email')], required=True)
    jwt_key = fields.Char(required=True)

    _sql_constraints = [
        ('sequence_positive', 'CHECK(sequence > 0)', 'Mapping sequence must be positive.'),
        ('issuer_sequence_unique', 'unique(issuer_id, sequence)',
         'Mapping sequence must be unique per issuer.'),
    ]

    @api.constrains('sequence', 'active', 'field_user', 'jwt_key', 'issuer_id')
    def _check_mapping(self):
        for row in self:
            _validate_mapping_claim(row.jwt_key, 'schema-check')
            if row.field_user not in ('login', 'partner_id.email'):
                raise ValidationError('Mapping user field is invalid.')
            _validate_mapping_rows([dict(sequence=item.sequence, field_user=item.field_user,
                                         jwt_key=item.jwt_key, active=item.active)
                                    for item in row.issuer_id.user_mapping_ids])
            if (row.issuer_id.resolver_mode == 'mapping' and
                    not any(item.active for item in row.issuer_id.user_mapping_ids)):
                raise ValidationError('Mapping resolver requires an active mapping.')

    def write(self, values):
        _check_parent_issuers_draft(self)
        if 'issuer_id' in values:
            raise ValidationError('Mappings cannot be moved to another issuer.')
        return super(AmrResourceUserMapping, self).write(values)


class OidcIssuerAlgorithmPolicy(models.Model):
    _name = 'oidc.issuer.algorithm.policy'
    #_inherit = 'amr.resource.registry.access'
    _description = 'Issuer Enabled OIDC Algorithm Policy'
    _rec_name = 'algorithm_id'

    @api.model_create_multi
    def create(self, vals_list):
        issuers = self.env['oidc.issuer.register'].browse([v['issuer_id'] for v in vals_list if v.get('issuer_id')])
        issuers._check_draft_state()
        _invalidate_request_policy()
        return super(OidcIssuerAlgorithmPolicy, self).create(vals_list)

    def write(self, values):
        _check_parent_issuers_draft(self)
        if values.get('issuer_id'):
            self.env['oidc.issuer.register'].browse(values['issuer_id'])._check_draft_state()
        return super(OidcIssuerAlgorithmPolicy, self).write(values)

    def unlink(self):
        _check_parent_issuers_draft(self)
        return super(OidcIssuerAlgorithmPolicy, self).unlink()

    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    algorithm_id = fields.Many2one('oidc.algorithm', required=True, ondelete='restrict')
    enabled = fields.Boolean(default=False)

    _sql_constraints = [('issuer_algorithm_unique', 'unique(issuer_id, algorithm_id)',
                         'Algorithm policy must be unique per issuer.')]

    @api.constrains('issuer_id', 'algorithm_id', 'enabled')
    def _check_supported_policy(self):
        for policy in self:
            if policy.algorithm_id.name not in ALGORITHM_CATALOG:
                raise ValidationError('Algorithm is not supported by this build.')
            if policy.enabled and policy.algorithm_id.support_state != 'supported':
                raise ValidationError('Algorithm is not enabled for runtime support.')
