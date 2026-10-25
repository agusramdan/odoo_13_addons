# -*- coding: utf-8 -*-
"""Global trust configuration; no discovery or stored-code execution."""
import hashlib
import ipaddress
import json
import logging
from urllib.parse import urlsplit

from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessError, ValidationError
from werkzeug.exceptions import Unauthorized

_logger = logging.getLogger(__name__)
_RESTORE_CONTEXT_TOKEN = object()
TRUST_GROUP = 'amr_resource.group_oidc_trust_admin'
CODE_GROUP = 'amr_resource.group_oidc_code_admin'
AUDIT_FIELDS = {'code_revision', 'code_digest', 'code_actor_id', 'code_date', 'policy_revision'}
POLICY_CHILD_MODELS = {'oidc.issuer.register.audience', 'oidc.issuer.subject',
                       'oidc.issuer.user.mapping', 'oidc.issuer.algorithm.policy'}
_ALGORITHM_CATALOG = __import__('types').MappingProxyType({
    'RS256': __import__('types').MappingProxyType({
        'key_family': 'RSA', 'min_key_bits': 2048,
        'purpose': 'access_token_verification', 'support_state': 'supported'}),
    'PS256': __import__('types').MappingProxyType({
        'key_family': 'RSA', 'min_key_bits': 2048,
        'purpose': 'access_token_verification', 'support_state': 'target'}),
})


def _policy_algorithms(policy, key_metadata):
    """Return only algorithms supported by code, enabled for issuer and key."""
    if not isinstance(policy, (list, tuple)) or not isinstance(key_metadata, dict):
        raise ValidationError('Algorithm policy is invalid.')
    enabled = set()
    for row in policy:
        if (not isinstance(row, (list, tuple)) or len(row) != 2
                or not isinstance(row[0], str) or type(row[1]) is not bool
                or row[0] not in _ALGORITHM_CATALOG):
            raise ValidationError('Algorithm policy is invalid.')
        if row[1]:
            enabled.add(row[0])
    allowed = {name for name in enabled
               if _ALGORITHM_CATALOG[name]['support_state'] == 'supported'}
    key_algorithm = key_metadata.get('alg')
    if key_algorithm is not None:
        allowed = {name for name in allowed if name == key_algorithm}
    if not allowed:
        raise ValidationError('No configured algorithm is supported by the trusted key.')
    return frozenset(allowed)


def _effective_algorithms(enabled, supported):
    """Intersect issuer policy with a code-owned catalog and verified capability."""
    if not isinstance(enabled, (list, tuple, set, frozenset)) or not isinstance(
            supported, (list, tuple, set, frozenset)):
        raise ValidationError('Algorithm policy is invalid.')
    if not enabled or any(name not in _ALGORITHM_CATALOG for name in enabled):
        raise ValidationError('Algorithm policy is empty or unsupported.')
    effective = frozenset(enabled).intersection(supported)
    if not effective:
        raise ValidationError('No configured algorithm is supported.')
    return effective


def _exact_string(value):
    return isinstance(value, str) and bool(value) and not any(
        ord(char) < 33 or ord(char) == 127 for char in value)


def _introspection_client_id(value):
    return (type(value) is str and 1 <= len(value) <= 1024 and bool(value.strip())
            and not any(ord(char) <= 31 or 127 <= ord(char) <= 159 for char in value))


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


def _mapping_candidate(rows, claims, find_users):
    """Return the first uniquely matched user ID; caller enforces existing binding."""
    if not isinstance(claims, dict) or not isinstance(rows, (list, tuple)):
        raise ValidationError('Mapping configuration is invalid.')
    configured = [dict(row, active=True) for row in rows]
    _validate_mapping_rows(configured)
    for row in sorted(configured, key=lambda item: item['sequence']):
        if row['jwt_key'] not in claims:
            raise ValidationError('Mapping claim is missing or invalid.')
        value = _validate_mapping_claim(row['jwt_key'], claims[row['jwt_key']])
        matches = find_users(row['field_user'], value)
        identifiers = {match.id if hasattr(match, 'id') else match for match in matches}
        if len(identifiers) > 1:
            raise ValidationError('Mapping is ambiguous.')
        if identifiers:
            return next(iter(identifiers))
    raise ValidationError('No mapping matched a user.')


def _legacy_plan(get_param, values, audiences, bindings):
    """Resolve legacy *keys* once; require an administrator-authored exact plan."""
    import json
    import re

    allowed = {'issuer', 'client_id', 'token_profile', 'jwks_uri', 'token_endpoint',
               'introspection_endpoint', 'credential_ref', 'local_key_ref',
               'azp', 'allow_missing_azp', 'resolver_mode', 'fixed_user_id'}
    if (not isinstance(values, dict) or set(values) - allowed or
            values.get('resolver_mode') not in ('get_user_match', 'fixed_user', 'resolver')):
        raise ValidationError('An explicit supported migration plan is required.')
    selectors, resolved = [], []
    for name in ('issuer', 'audience'):
        selector = get_param('amr_resource.' + name)
        if not isinstance(selector, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', selector):
            raise ValidationError('Legacy configuration must contain an explicit parameter key.')
        value = get_param(selector)
        if not _exact_string(value):
            raise ValidationError('Legacy configuration reference is missing or invalid.')
        selectors.append(selector)
        resolved.append(value)
    if (values.get('issuer') != resolved[0] or not isinstance(audiences, list) or
            not audiences or any(not _exact_string(a) for a in audiences) or
            len(set(audiences)) != len(audiences) or resolved[1] not in audiences):
        raise ValidationError('Legacy issuer or audience conflicts with the migration plan.')
    if not isinstance(bindings, list):
        raise ValidationError('Explicit subject bindings are required.')
    subjects = set()
    for binding in bindings:
        if (not isinstance(binding, dict) or set(binding) != {'sub', 'user_id'} or
                not _exact_string(binding['sub']) or type(binding['user_id']) is not int or
                binding['user_id'] <= 0 or binding['sub'] in subjects):
            raise ValidationError('Ambiguous or invalid subject binding.')
        subjects.add(binding['sub'])
    normalized = dict(jwks_uri=False, token_endpoint=False, introspection_endpoint=False,
                      credential_ref=False, local_key_ref=False, azp=False,
                      allow_missing_azp=False, fixed_user_id=False)
    normalized.update(values)
    plan: dict = dict(version=2, values=normalized,
                audiences=sorted(audiences), bindings=sorted(
                    [dict(b) for b in bindings], key=lambda b: b['sub']),
                legacy_selectors=selectors, legacy_values=resolved)
    plan['digest'] = hashlib.sha256(json.dumps(
        plan, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return plan

class RegistryAccess(models.AbstractModel):
    _name = 'amr.resource.registry.access'
    _description = 'Trust Registry Access Guard'

    def _registry_role(self, group):
        user = self.env.user
        return (not user.share and user.has_group('base.group_system')
                and user.has_group(group))

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        if not self.env.su:
            allowed = self._registry_role(TRUST_GROUP)
            if self._name == 'oidc.issuer.register' and operation in ('read', 'write'):
                allowed = allowed or self._registry_role(CODE_GROUP)
            if not allowed:
                if raise_exception:
                    raise AccessError('Registry access denied.')
                return False
        return super(RegistryAccess, self).check_access_rights(operation, raise_exception)

    def _guard_parent_values(self, values):
        if 'issuer_id' in values:
            parent = self.env['oidc.issuer.register'].browse(values['issuer_id']).exists()
            parent.check_access_rights('read')
            parent.check_access_rule('read')
            if len(parent) != 1:
                raise AccessError('Registry access denied.')

    def _bump_parent_revisions(self, records):
        if self.env.context.get('_policy_restore_token') is _RESTORE_CONTEXT_TOKEN:
            return
        if self._name in POLICY_CHILD_MODELS:
            for issuer in records.mapped('issuer_id'):
                if hasattr(issuer, '_bump_policy_revision'):
                    issuer._bump_policy_revision()

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access_rights('create')
        for values in vals_list:
            self._guard_parent_values(values)
        records = super(RegistryAccess, self).create(vals_list)
        self._bump_parent_revisions(records)
        _logger.info('Trust registry create model=%s ids=%s actor=%s',
                     self._name, records.ids, self.env.uid)
        return records

    def write(self, values):
        self.check_access_rights('write')
        self.check_access_rule('write')
        self._guard_parent_values(values)
        parents = self.mapped('issuer_id') if self._name in POLICY_CHILD_MODELS else []
        result = super(RegistryAccess, self).write(values)
        if self._name in POLICY_CHILD_MODELS and self.env.context.get(
                '_policy_restore_token') is not _RESTORE_CONTEXT_TOKEN:
            seen = set()
            for issuer in list(parents) + list(self.mapped('issuer_id')):
                if issuer.id not in seen:
                    if hasattr(issuer, '_bump_policy_revision'):
                        issuer._bump_policy_revision()
                    seen.add(issuer.id)
        _logger.info('Trust registry write model=%s ids=%s actor=%s',
                     self._name, self.ids, self.env.uid)
        return result

    def unlink(self):
        self.check_access_rights('unlink')
        self.check_access_rule('unlink')
        ids = self.ids
        parents = self.mapped('issuer_id') if self._name in POLICY_CHILD_MODELS else []
        result = super(RegistryAccess, self).unlink()
        if self.env.context.get('_policy_restore_token') is not _RESTORE_CONTEXT_TOKEN:
            for issuer in parents:
                if hasattr(issuer, '_bump_policy_revision'):
                    issuer._bump_policy_revision()
        _logger.info('Trust registry unlink model=%s ids=%s actor=%s',
                     self._name, ids, self.env.uid)
        return result

    def name_get(self):
        self.check_access_rights('read')
        self.check_access_rule('read')
        return super(RegistryAccess, self).name_get()


class AmrResourceIssuer(models.Model):
    _name = 'oidc.issuer.register'
    _description = 'Resource Token Issuer'
    _inherit = 'amr.resource.registry.access'
    _rec_name = 'issuer'

    issuer = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    token_profile = fields.Selection([('jwt', 'JWT Access Token'),
                                      ('opaque', 'Opaque Access Token')], required=True)
    jwks_uri = fields.Char()
    token_endpoint = fields.Char()
    introspection_endpoint = fields.Char()
    client_id = fields.Char(required=True)
    azp = fields.Char()
    allow_missing_azp = fields.Boolean(default=False)
    credential_ref = fields.Char(groups=TRUST_GROUP)
    local_key_ref = fields.Char(groups='amr_resource.group_oidc_trust_admin',
                                help='Protected ir.config_parameter key containing an RSA public PEM.')
    local_public_key = fields.Text(compute='_compute_local_public_key', groups=TRUST_GROUP,
                                   help='Protected RSA public PEM; no loopback key fetch.')
    resolver_mode = fields.Selection([('get_user_match', 'Default'),
                                      ('fixed_user', 'Fixed User'),
                                      ('mapping', 'Ordered Claim Mapping'),
                                      ('resolver', 'Allowlisted Resolver')])
    mvp_enabled = fields.Boolean(default=False)
    metadata_mode = fields.Selection([('manual', 'Manual'),
                                      ('oidc_discovery', 'OIDC Discovery')])
    discovery_unavailable_declared = fields.Boolean(default=False)
    discovery_unavailable_evidence_ref = fields.Char(size=512, groups=TRUST_GROUP)
    verification_source = fields.Selection([('jwks', 'JWKS'),
                                            ('local_public', 'Local public key'),
                                            ('none', 'No JWKS')])
    introspection_source = fields.Selection([('none', 'None'), ('manual', 'Manual'),
                                             ('rfc8414', 'RFC 8414')])
    no_jwks_declaration = fields.Boolean(default=False)
    no_jwks_evidence_ref = fields.Char(size=512, groups=TRUST_GROUP)
    introspection_credential_ref = fields.Char(size=256, groups=TRUST_GROUP)
    introspection_auth_client_id = fields.Char(groups=TRUST_GROUP)
    introspection_auth_method = fields.Selection([('client_secret_basic', 'Client Secret Basic')])
    introspection_basic_contract_ref = fields.Char(size=512, groups=TRUST_GROUP)
    introspection_credential_endpoint = fields.Char(groups=TRUST_GROUP)
    allow_jwt_introspection = fields.Boolean(default=False)
    allow_introspection_iss_absent = fields.Boolean(default=False)
    resolver_key = fields.Selection([('get_user_match', 'Default')],
                                    readonly=True, default='get_user_match', required=True)
    python_code = fields.Text(groups=CODE_GROUP, copy=False,
                              help='Source storage only. Execution is disabled in v1.')
    code_revision = fields.Integer(readonly=True, copy=False, groups=CODE_GROUP)
    code_digest = fields.Char(readonly=True, copy=False, groups=CODE_GROUP)
    code_date = fields.Datetime(readonly=True, copy=False, groups=CODE_GROUP)
    policy_revision = fields.Integer(readonly=True, copy=False, default=1, groups=TRUST_GROUP)

    fixed_user_id = fields.Many2one('res.users', ondelete='restrict')
    code_actor_id = fields.Many2one('res.users', readonly=True, copy=False,
                                   ondelete='restrict', groups=CODE_GROUP)
    audience_ids = fields.One2many('oidc.issuer.register.audience', 'issuer_id')
    binding_ids = fields.One2many('oidc.issuer.subject', 'issuer_id')
    user_mapping_ids = fields.One2many('oidc.issuer.user.mapping', 'issuer_id')
    algorithm_policy_ids = fields.One2many('oidc.issuer.algorithm.policy', 'issuer_id')

    _sql_constraints = [('issuer_unique', 'unique(issuer)', 'Issuer must be unique.')]

    @api.model
    def _migrate_legacy_v2(self, values, audiences, bindings, dry_run=True):
        """Explicit additive migration; never called during install or token handling."""
        if type(dry_run) is not bool or not self._registry_role('amr_resource.group_oidc_trust_admin'):
            raise AccessError('Registry access denied.')
        self.check_access_rights('create')
        # sudo: legacy parameters/marker are read only after the designated admin guard.
        params = self.env['ir.config_parameter'].sudo()
        plan = _legacy_plan(params.get_param, values, audiences, bindings)
        data = plan['values']
        marker = 'amr_resource.migration.v2.global'
        previous = params.get_param(marker)
        if previous and previous != plan['digest']:
            raise ValidationError('Migration revision conflicts with the recorded plan.')
        domain = [('issuer', '=', data['issuer'])]
        # sudo: inspect archived and active global rows after the admin guard.
        global_rows = self.sudo().with_context(active_test=False).search(domain)
        if len(global_rows) > 1:
            raise ValidationError('Migration issuer conflict.')
        rows = global_rows
        commands = [(0, 0, {'value': value}) for value in plan['audiences']]
        candidate = self.new(dict(data, audience_ids=commands))
        candidate._check_profile()
        for binding in plan['bindings']:
            user = self.env['res.users'].browse(binding['user_id']).exists()
            if (len(user) != 1 or not user.active or user.id == SUPERUSER_ID or user.share
                    or user.has_group('base.group_public') or user.has_group('base.group_portal')):
                raise ValidationError('Migration requires an eligible exact subject binding.')
        if rows:
            if not rows.active or any(rows[field] != value if field != 'fixed_user_id'
                                      else rows[field].id != value
                                      for field, value in data.items()):
                raise ValidationError('Existing issuer configuration conflicts with migration.')
            if sorted(rows.audience_ids.mapped('value')) != plan['audiences']:
                raise ValidationError('Existing issuer audience conflict.')
            actual = sorted([{'sub': b.sub, 'user_id': b.user_id.id} for b in rows.binding_ids],
                            key=lambda b: b['sub'])
            if actual != plan['bindings']:
                raise ValidationError('Existing subject bindings conflict with migration.')
        elif previous:
            raise ValidationError('Recorded migration issuer is missing.')
        result = {'version': 2, 'issuer_count': 1, 'binding_count': len(bindings),
                  'dry_run': dry_run, 'already_applied': bool(previous)}
        if dry_run or previous:
            return result
        # A savepoint keeps registry creation and the revision marker atomic even for a caught error.
        with self.env.cr.savepoint():
            if not rows:
                self.create(dict(data, audience_ids=commands, binding_ids=[
                    (0, 0, binding) for binding in plan['bindings']]))
            params.set_param(marker, plan['digest'])
            for xml_id in ('rule_oidc_issuer_company', 'rule_oidc_audience_company',
                           'rule_oidc_binding_company'):
                rule = self.env.ref('amr_resource.' + xml_id, raise_if_not_found=False)
                if rule:
                    # sudo: remove obsolete company rules after the designated migration-admin guard.
                    rule.sudo().unlink()
        _logger.info('Trust migration version=2 actor=%s bindings=%s',
                     self.env.uid, len(bindings))
        return result

    @api.depends('local_key_ref')
    def _compute_local_public_key(self):
        # sudo: read only the protected administrator-selected public key reference.
        params = self.env['ir.config_parameter'].sudo()
        for record in self:
            record.local_public_key = (params.get_param(record.local_key_ref)
                                       if record.local_key_ref else False)

    def _guard_issuer_values(self, values, creating=False):
        if 'local_public_key' in values or (creating and 'default_local_public_key' in self.env.context):
            raise AccessError('Use a protected local key reference.')
        if 'mvp_enabled' in values:
            if type(values['mvp_enabled']) is not bool or values['mvp_enabled']:
                raise AccessError('Use the explicit MVP activation action.')
            if any(getattr(record, 'mvp_enabled', False) for record in self):
                raise AccessError('Use the explicit MVP deactivation action.')
        if 'active' in values and any(getattr(record, 'mvp_enabled', False) for record in self):
            if type(values['active']) is not bool:
                raise AccessError('Use a Boolean active value for MVP issuers.')
            if not values['active'] or any(
                    getattr(record, 'mvp_enabled', False) and not record.active for record in self):
                raise AccessError('Use the explicit MVP activation/deactivation action.')
        if AUDIT_FIELDS.intersection(values):
            raise AccessError('Registry access denied.')
        if 'resolver_key' in values and (not creating or values['resolver_key'] != 'get_user_match'):
            raise AccessError('Registry access denied.')
        if 'python_code' in values and not self._registry_role(CODE_GROUP):
            raise AccessError('Registry access denied.')
        if set(values) - {'python_code'} and not self.env.su and not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')

    def _source_audit(self, source, revision):
        digest = hashlib.sha256((source or '').encode('utf-8')).hexdigest()
        _logger.info('Trust source revision issuer_ids=%s revision=%s digest=%s actor=%s',
                     self.ids, revision, digest, self.env.uid)
        return {'code_revision': revision, 'code_digest': digest,
                'code_actor_id': self.env.uid, 'code_date': fields.Datetime.now()}

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for values in vals_list:
            values = dict(values)
            # Context defaults are RPC input too; audit/source checks must see them.
            for name in AUDIT_FIELDS | {'python_code', 'resolver_key', 'mvp_enabled'}:
                if name not in values and 'default_' + name in self.env.context:
                    values[name] = self.env.context['default_' + name]
            self._guard_issuer_values(values, creating=True)
            if 'python_code' in values:
                values.update(self._source_audit(values['python_code'], 1))
            prepared.append(values)
        return super(AmrResourceIssuer, self).create(prepared)

    def write(self, values):
        self._guard_issuer_values(values)
        self.check_access_rights('write')
        self.check_access_rule('write')
        for record in self:
            updated = dict(values)
            previous_active = record.active
            if values and set(values) - AUDIT_FIELDS:
                updated['policy_revision'] = record.policy_revision + 1
            if 'python_code' in values and values['python_code'] != record.python_code:
                updated.update(record._source_audit(values['python_code'], record.code_revision + 1))
            super(AmrResourceIssuer, record).write(updated)
            if 'policy_revision' in updated:
                _logger.info('Trust policy revision issuer_id=%s revision=%s actor=%s',
                             record.ids[0], updated['policy_revision'], self.env.uid)
                if 'active' in values and values['active'] != previous_active:
                    _logger.info('Trust activation issuer_id=%s active=%s revision=%s actor=%s',
                                 record.ids[0], values['active'], updated['policy_revision'], self.env.uid)
        return True

    def _bump_policy_revision(self):
        for record in self:
            revision = record.policy_revision + 1
            super(AmrResourceIssuer, record).write({'policy_revision': revision})
            _logger.info('Trust policy revision issuer_id=%s revision=%s actor=%s',
                         record.ids[0], revision, self.env.uid)

    def action_activate_mvp(self, reason_code):
        """Enable a fully validated MVP profile via an audited trust-admin action."""
        import re

        if not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        self.check_access_rights('write')
        self.check_access_rule('write')
        if (not isinstance(reason_code, str)
                or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', reason_code)):
            raise ValidationError('A bounded reason code is required.')
        for record in self:
            if (record.active and record.mvp_enabled) or (not record.active and not record.mvp_enabled):
                raise ValidationError('Issuer is not in an activatable state.')
            if record.token_profile == 'jwt':
                record._verification_algorithms({})
            record._check_profile(mvp_enabled=True)
        for record in self:
            revision = record.policy_revision + 1
            timestamp = fields.Datetime.now()
            source_kind = record.verification_source
            changes = {'policy_revision': revision}
            if record.active:
                changes['mvp_enabled'] = True
            else:
                changes['active'] = True
            super(AmrResourceIssuer, record).write(changes)
            _logger.info('Trust issuer activated issuer_id=%s action=%s source_kind=%s '
                         'revision=%s actor=%s reason_code=%s timestamp=%s',
                         record.id, 'activate_mvp', source_kind, revision,
                         self.env.uid, reason_code, timestamp)
        return True

    def action_deactivate_mvp(self, reason_code):
        """Disable one active MVP issuer through an explicit audited admin action."""
        import re

        if not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        self.check_access_rights('write')
        self.check_access_rule('write')
        if (not isinstance(reason_code, str)
                or not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}', reason_code)):
            raise ValidationError('A bounded reason code is required.')
        for record in self:
            if not record.active or not record.mvp_enabled:
                raise ValidationError('Only an active MVP issuer can be deactivated.')
            source_kind = record.verification_source
            if source_kind not in ('jwks', 'local_public', 'none'):
                raise ValidationError('MVP issuer source state is invalid.')
        for record in self:
            revision = record.policy_revision + 1
            timestamp = fields.Datetime.now()
            super(AmrResourceIssuer, record).write({
                'active': False, 'policy_revision': revision})
            _logger.info('Trust issuer deactivated issuer_id=%s action=%s source_kind=%s '
                         'revision=%s actor=%s reason_code=%s timestamp=%s',
                         record.id, 'deactivate_mvp', record.verification_source,
                         revision, self.env.uid, reason_code, timestamp)
        return True

    def _policy_snapshot_tuple(self):
        self.ensure_one()
        if self.resolver_mode == 'fixed_user':
            raise ValidationError('Fixed-user identity state cannot be snapshotted.')
        return {
            'issuer': self.issuer, 'token_profile': self.token_profile,
            'jwks_uri': self.jwks_uri or False, 'token_endpoint': self.token_endpoint or False,
            'introspection_endpoint': self.introspection_endpoint or False,
            'client_id': self.client_id, 'azp': self.azp or False,
            'allow_missing_azp': self.allow_missing_azp,
            'credential_ref': self.credential_ref or False, 'local_key_ref': self.local_key_ref or False,
            'resolver_mode': self.resolver_mode or False, 'mvp_enabled': self.mvp_enabled,
            'metadata_mode': self.metadata_mode or False,
            'discovery_unavailable_declared': self.discovery_unavailable_declared,
            'discovery_unavailable_evidence_ref': self.discovery_unavailable_evidence_ref or False,
            'verification_source': self.verification_source or False,
            'introspection_source': self.introspection_source or False,
            'no_jwks_declaration': self.no_jwks_declaration,
            'no_jwks_evidence_ref': self.no_jwks_evidence_ref or False,
            'introspection_credential_ref': self.introspection_credential_ref or False,
            'introspection_auth_client_id': self.introspection_auth_client_id or False,
            'introspection_auth_method': self.introspection_auth_method or False,
            'introspection_basic_contract_ref': self.introspection_basic_contract_ref or False,
            'introspection_credential_endpoint': self.introspection_credential_endpoint or False,
            'allow_jwt_introspection': self.allow_jwt_introspection,
            'allow_introspection_iss_absent': self.allow_introspection_iss_absent,
            'audiences': sorted(self.audience_ids.mapped('value')),
            'mappings': sorted([{'sequence': row.sequence, 'active': row.active,
                                 'field_user': row.field_user, 'jwt_key': row.jwt_key}
                                for row in self.user_mapping_ids], key=lambda row: row['sequence']),
            'algorithms': sorted([{'name': row.algorithm_id.name, 'enabled': row.enabled}
                                  for row in self.algorithm_policy_ids], key=lambda row: row['name']),
        }

    def action_capture_policy_snapshot(self, evidence_ref):
        import re
        if not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        self.ensure_one()
        if not isinstance(evidence_ref, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,512}', evidence_ref):
            raise ValidationError('A sanitized evidence reference is required.')
        self._check_profile()
        payload = self._policy_snapshot_tuple()
        self._validate_snapshot_algorithms(payload)
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        model = self.env['oidc.issuer.policy.snapshot'].sudo()
        snapshot = super(OidcPolicySnapshot, model).create({
            'issuer_id': self.id, 'captured_revision': self.policy_revision,
            'payload': json.dumps(payload, sort_keys=True, separators=(',', ':')),
            'integrity_digest': digest, 'evidence_ref': evidence_ref,
            'actor_id': self.env.uid, 'captured_at': fields.Datetime.now(),
        })
        _logger.info('Trust policy snapshot captured issuer_id=%s snapshot_id=%s revision=%s actor=%s source=%s reason_code=%s timestamp=%s',
                     self.id, snapshot.id, self.policy_revision, self.env.uid,
                     self.verification_source or 'legacy', 'snapshot_capture', fields.Datetime.now())
        return snapshot.id

    def action_restore_policy_snapshot(self, snapshot_id, expected_revision, evidence_ref):
        import re
        if not self._registry_role(TRUST_GROUP):
            raise AccessError('Registry access denied.')
        self.ensure_one()
        if (type(snapshot_id) is not int or snapshot_id <= 0 or type(expected_revision) is not int
                or not isinstance(evidence_ref, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,512}', evidence_ref)):
            raise ValidationError('Rollback identifiers or evidence are invalid.')
        self.check_access_rights('write')
        self.check_access_rule('write')
        if self.active or self.policy_revision != expected_revision:
            raise ValidationError('Issuer must be inactive at the expected policy revision.')
        snapshot = self.env['oidc.issuer.policy.snapshot'].sudo().browse(snapshot_id).exists()
        if len(snapshot) != 1 or snapshot.issuer_id.id != self.id or snapshot.invalidated:
            raise ValidationError('Snapshot is unavailable for this issuer.')
        try:
            payload = json.loads(snapshot.payload)
            if not isinstance(payload, dict):
                raise ValidationError('Snapshot is invalid.')
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        except (TypeError, ValueError):
            raise ValidationError('Snapshot is invalid.')
        if (digest != snapshot.integrity_digest or payload.get('issuer') != self.issuer
                or snapshot.captured_revision <= 0 or snapshot.captured_revision > expected_revision):
            raise ValidationError('Snapshot integrity or issuer binding failed.')
        if set(payload) != set(self._policy_snapshot_tuple()) or payload.get('resolver_mode') == 'fixed_user':
            raise ValidationError('Snapshot tuple is incomplete or contains identity state.')
        if (not isinstance(payload['audiences'], list) or not payload['audiences']
                or any(not _exact_string(value) for value in payload['audiences'])
                or len(set(payload['audiences'])) != len(payload['audiences'])
                or not isinstance(payload['mappings'], list)
                or not isinstance(payload['algorithms'], list)):
            raise ValidationError('Snapshot configuration is incomplete.')
        self._validate_snapshot_algorithms(payload)
        candidate = self.new({key: value for key, value in payload.items()
                               if key not in ('audiences', 'mappings', 'algorithms')})
        candidate.audience_ids = [(0, 0, {'value': value}) for value in payload['audiences']]
        candidate.user_mapping_ids = [(0, 0, row) for row in payload['mappings']]
        candidate._check_profile(mvp_enabled=payload['mvp_enabled'])
        algorithm_commands = []
        for row in payload['algorithms']:
            algorithm = self.env['oidc.algorithm'].search([('name', '=', row['name'])], limit=1)
            if len(algorithm) != 1:
                raise ValidationError('Snapshot algorithm is no longer available.')
            algorithm_commands.append((0, 0, {'algorithm_id': algorithm.id, 'enabled': row['enabled']}))
        current_audiences = list(self.audience_ids)
        audience_commands = [(0, 0, {'value': value})
                             for value in payload['audiences'][len(current_audiences):]]
        audience_commands += [(1, current.id, {'value': value})
                              for current, value in zip(current_audiences, payload['audiences'])]
        audience_commands += [(2, current.id, 0)
                              for current in current_audiences[len(payload['audiences']):]]
        values = {key: value for key, value in payload.items()
                  if key not in ('issuer', 'audiences', 'mappings', 'algorithms')}
        values.update({'audience_ids': audience_commands,
                       'user_mapping_ids': [(5, 0, 0)] + [(0, 0, row) for row in payload['mappings']],
                       'algorithm_policy_ids': [(5, 0, 0)] + algorithm_commands,
                       'active': False, 'policy_revision': expected_revision + 1})
        for record in self:
            restoring = record.with_context(_policy_restore_token=_RESTORE_CONTEXT_TOKEN)
            super(AmrResourceIssuer, restoring).write(values)
        _logger.info('Trust policy snapshot restored issuer_id=%s snapshot_id=%s revision=%s actor=%s source=%s reason_code=%s evidence_ref=%s timestamp=%s',
                     self.id, snapshot.id, expected_revision + 1, self.env.uid,
                     payload.get('verification_source') or 'legacy', 'snapshot_restore', evidence_ref,
                     fields.Datetime.now())
        return True

    @staticmethod
    def _validate_snapshot_algorithms(payload):
        rows = payload.get('algorithms')
        if not isinstance(rows, list):
            raise ValidationError('Snapshot algorithm policy is invalid.')
        names, enabled = set(), set()
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {'name', 'enabled'}
                    or row['name'] not in _ALGORITHM_CATALOG or type(row['enabled']) is not bool
                    or row['name'] in names):
                raise ValidationError('Snapshot algorithm policy is invalid.')
            names.add(row['name'])
            if row['enabled']:
                if _ALGORITHM_CATALOG[row['name']]['support_state'] != 'supported':
                    raise ValidationError('Snapshot enables an unsupported algorithm.')
                enabled.add(row['name'])
        if payload.get('mvp_enabled') and not enabled:
            raise ValidationError('MVP snapshot requires a supported enabled algorithm.')

    @api.constrains('issuer', 'token_profile', 'jwks_uri', 'token_endpoint',
                    'introspection_endpoint', 'client_id', 'azp', 'allow_missing_azp',
                    'local_public_key', 'local_key_ref', 'credential_ref', 'resolver_mode', 'fixed_user_id',
                    'audience_ids', 'mvp_enabled', 'metadata_mode', 'discovery_unavailable_declared',
                    'discovery_unavailable_evidence_ref', 'verification_source', 'introspection_source',
                    'no_jwks_declaration', 'no_jwks_evidence_ref', 'introspection_credential_ref',
                    'introspection_auth_client_id', 'introspection_auth_method',
                    'introspection_basic_contract_ref', 'introspection_credential_endpoint',
                    'allow_jwt_introspection', 'allow_introspection_iss_absent', 'user_mapping_ids')
    def _check_profile(self, mvp_enabled=None):
        for record in self:
            import re
            enabled = record.mvp_enabled if mvp_enabled is None else mvp_enabled
            for reference in (record.local_key_ref, record.credential_ref):
                if reference and (not isinstance(reference, str) or
                                  not re.fullmatch(r'[A-Za-z0-9_.-]+', reference)):
                    raise ValidationError('Configure an exact protected parameter key, not a URL.')
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
            if (record.token_profile == 'jwt' and bool(record.jwks_uri) == bool(record.local_public_key)
                    and not (enabled and (record.verification_source == 'none'
                         or (record.metadata_mode == 'oidc_discovery'
                             and record.verification_source == 'jwks')))):
                raise ValidationError('JWT requires exactly one static JWKS URL or local public key.')
            if record.local_public_key:
                if record.token_profile != 'jwt':
                    raise ValidationError('Local keys require the JWT profile.')
                try:
                    from cryptography.hazmat.backends import default_backend
                    from cryptography.hazmat.primitives import serialization
                    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
                    key = serialization.load_pem_public_key(
                        record.local_public_key.encode('ascii'), backend=default_backend())
                    if not isinstance(key, RSAPublicKey) or key.key_size < 2048:
                        raise ValueError()
                except (ValueError, TypeError, UnicodeError):
                    raise ValidationError('A valid RSA public PEM of at least 2048 bits is required.')
            if (record.token_profile == 'opaque' and not record.introspection_endpoint
                    and not enabled):
                raise ValidationError('Opaque profiles require a static introspection endpoint.')
            if (not record.allow_missing_azp and not record.azp) or (record.azp and not _exact_string(record.azp)):
                raise ValidationError('Configure one exact azp or explicitly allow its absence.')
            if not record.audience_ids:
                raise ValidationError('At least one audience is required.')
            if record.resolver_mode == 'fixed_user':
                user = record.fixed_user_id
                if (len(user) != 1 or not user.active or user.id == SUPERUSER_ID
                        or user.share or user.has_group('base.group_public')
                        or user.has_group('base.group_portal')):
                    raise ValidationError('Fixed user must be an active eligible internal user.')
            if record.resolver_mode == 'mapping' and not enabled:
                raise ValidationError('Mapping resolver requires explicit MVP enablement.')
            mapping_rows = [dict(sequence=row.sequence, field_user=row.field_user,
                                 jwt_key=row.jwt_key, active=row.active)
                            for row in record.user_mapping_ids]
            _validate_mapping_rows(mapping_rows)
            if record.resolver_mode == 'mapping' and not any(row['active'] for row in mapping_rows):
                raise ValidationError('Mapping resolver requires an active mapping.')
            if enabled:
                if (record.metadata_mode not in ('manual', 'oidc_discovery')
                        or record.verification_source not in ('jwks', 'local_public', 'none')
                        or record.introspection_source not in ('none', 'manual', 'rfc8414')):
                    raise ValidationError('MVP source configuration is incomplete.')
                for reference in (record.discovery_unavailable_evidence_ref,
                                  record.no_jwks_evidence_ref,
                                  record.introspection_credential_ref,
                                  record.introspection_basic_contract_ref):
                    if reference and (not isinstance(reference, str)
                                      or len(reference) > 512
                                      or not re.fullmatch(r'[A-Za-z0-9_.-]+', reference)):
                        raise ValidationError('MVP evidence or credential reference is invalid.')
                if record.metadata_mode == 'manual' and (
                        not record.discovery_unavailable_declared
                        or not record.discovery_unavailable_evidence_ref):
                    raise ValidationError('Manual metadata requires declared Discovery unavailability.')
                if record.metadata_mode == 'oidc_discovery' and (
                        record.token_profile != 'jwt' or record.verification_source != 'jwks'
                        or record.introspection_source != 'none'):
                    raise ValidationError('OIDC Discovery requires JWT/JWKS and no introspection source.')
                if record.verification_source == 'jwks' and (
                        record.token_profile != 'jwt' or
                        (not record.jwks_uri and record.metadata_mode != 'oidc_discovery')
                        or record.local_key_ref or record.local_public_key
                        or record.introspection_source != 'none'):
                    raise ValidationError('JWKS source configuration conflicts.')
                if record.verification_source == 'local_public' and (
                        record.token_profile != 'jwt' or record.jwks_uri
                        or not record.local_key_ref or record.introspection_source != 'none'):
                    raise ValidationError('Local public-key source configuration conflicts.')
                if record.verification_source == 'none':
                    if (record.metadata_mode != 'manual' or record.jwks_uri
                            or record.local_key_ref or record.local_public_key
                            or not record.no_jwks_declaration or not record.no_jwks_evidence_ref
                            or record.introspection_source not in ('manual', 'rfc8414')):
                        raise ValidationError('NO_JWKS requires an explicit compatible declaration.')
                    endpoint = (record.introspection_endpoint if record.introspection_source == 'manual'
                                else record.introspection_credential_endpoint)
                    if (not endpoint or not record.introspection_credential_endpoint
                            or endpoint != record.introspection_credential_endpoint
                            or not _https_url(endpoint)
                            or not record.introspection_credential_ref
                            or not _introspection_client_id(record.introspection_auth_client_id)
                            or record.introspection_auth_method != 'client_secret_basic'
                            or (record.introspection_source == 'manual'
                                and not record.introspection_basic_contract_ref)
                            or ((record.credential_ref == record.introspection_credential_ref
                                 or record.client_id == record.introspection_auth_client_id)
                                and not record.introspection_basic_contract_ref)):
                        raise ValidationError('Introspection requires a separate authorized Basic configuration.')
                elif record.introspection_source != 'none':
                    raise ValidationError('Introspection metadata requires a genuine NO_JWKS source.')
                if record.allow_jwt_introspection and (
                        record.token_profile != 'jwt' or record.verification_source != 'none'):
                    raise ValidationError('JWT introspection requires explicit JWT NO_JWKS mode.')
                if record.allow_introspection_iss_absent and record.token_profile != 'opaque':
                    raise ValidationError('Absent issuer policy is only valid for opaque tokens.')

    def _verification_algorithms(self, key_metadata):
        self.ensure_one()
        policy = [(row.algorithm_id.name, row.enabled) for row in self.algorithm_policy_ids]
        return _policy_algorithms(policy, key_metadata)

    @api.model
    def _lookup(self, issuer=None, token_profile=None):
        """Private runtime read only: never use this elevation to execute a resolver."""
        if not _exact_string(issuer) or token_profile not in (None, 'jwt', 'opaque'):
            raise Unauthorized()
        try:
            # sudo: read protected global trust rows; user eligibility remains request-scoped.
            records = self.sudo().with_context(active_test=False).search([
                ('issuer', '=', issuer), ('active', '=', True)])
            if len(records) != 1 or (token_profile and records.token_profile != token_profile):
                raise Unauthorized()
            return records
        except Exception:
            raise Unauthorized() from None


class OidcPolicySnapshot(models.Model):
    _name = 'oidc.issuer.policy.snapshot'
    _description = 'Immutable Issuer Policy Recovery Snapshot'
    _inherit = 'amr.resource.registry.access'
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
            _logger.info('Trust policy snapshot invalidated issuer_id=%s snapshot_id=%s actor=%s reason_code=%s timestamp=%s',
                         snapshot.issuer_id.id, snapshot.id, self.env.uid,
                         'snapshot_invalidated', fields.Datetime.now())
        return True


class AmrResourceAudience(models.Model):
    _name = 'oidc.issuer.register.audience'
    _description = 'Resource Issuer Audience'
    _inherit = 'amr.resource.registry.access'
    _rec_name = 'value'

    value = fields.Char(required=True)
    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    _sql_constraints = [('audience_unique', 'unique(issuer_id, value)', 'Audience must be unique per issuer.')]

    @api.constrains('value')
    def _check_value(self):
        for record in self:
            if not _exact_string(record.value):
                raise ValidationError('An exact nonempty audience is required.')

    def write(self, values):
        parents = self.mapped('issuer_id') if 'issuer_id' in values else self.env['oidc.issuer.register']
        result = super(AmrResourceAudience, self).write(values)
        if parents.exists().filtered(lambda record: not record.audience_ids):
            raise ValidationError('At least one audience is required.')
        return result

    def unlink(self):
        parents = self.mapped('issuer_id')
        result = super(AmrResourceAudience, self).unlink()
        if parents.exists().filtered(lambda record: not record.audience_ids):
            raise ValidationError('At least one audience is required.')
        return result


class AmrResourceBinding(models.Model):
    _name = 'oidc.issuer.subject'
    _description = 'Resource Issuer Subject Binding'
    _inherit = 'amr.resource.registry.access'
    _rec_name = 'sub'

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


class AmrResourceUserMapping(RegistryAccess):
    _name = 'oidc.issuer.user.mapping'
    _description = 'Issuer User Claim Mapping'
    _rec_name = 'jwt_key'

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
        if 'issuer_id' in values:
            raise ValidationError('Mappings cannot be moved to another issuer.')
        return super(AmrResourceUserMapping, self).write(values)


class OidcAlgorithm(models.Model):
    _name = 'oidc.algorithm'
    _description = 'Code-Owned OIDC Verification Algorithm'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    key_family = fields.Selection([('RSA', 'RSA')], required=True, readonly=True)
    min_key_bits = fields.Integer(required=True, readonly=True, default=2048)
    purpose = fields.Selection([('access_token_verification', 'Access Token Verification')],
                               required=True, readonly=True)
    support_state = fields.Selection([('supported', 'Supported'), ('target', 'Target')],
                                     required=True, readonly=True)

    _sql_constraints = [('algorithm_name_unique', 'unique(name)', 'Algorithm must be unique.')]

    @api.model_create_multi
    def create(self, vals_list):
        expected = _ALGORITHM_CATALOG
        for values in vals_list:
            name = values.get('name') if isinstance(values, dict) else None
            if name not in expected or any(
                    values.get(field) != value for field, value in expected[name].items()):
                raise AccessError('Algorithm catalog is code-owned.')
        return super(OidcAlgorithm, self).create(vals_list)

    def write(self, values):
        raise AccessError('Algorithm catalog is immutable; update it in code.')

    def unlink(self):
        raise AccessError('Algorithm catalog is immutable; update it in code.')


class OidcIssuerAlgorithmPolicy(RegistryAccess):
    _name = 'oidc.issuer.algorithm.policy'
    _description = 'Issuer Enabled OIDC Algorithm Policy'
    _rec_name = 'algorithm_id'

    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    algorithm_id = fields.Many2one('oidc.algorithm', required=True, ondelete='restrict')
    enabled = fields.Boolean(default=False)

    _sql_constraints = [('issuer_algorithm_unique', 'unique(issuer_id, algorithm_id)',
                         'Algorithm policy must be unique per issuer.')]

    @api.constrains('issuer_id', 'algorithm_id', 'enabled')
    def _check_supported_policy(self):
        for policy in self:
            if policy.enabled and policy.algorithm_id.support_state != 'supported':
                raise ValidationError('Algorithm is not enabled for runtime support.')
