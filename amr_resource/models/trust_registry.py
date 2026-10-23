# -*- coding: utf-8 -*-
"""Company-local trust configuration; no discovery or stored-code execution."""
import hashlib
import ipaddress
import logging
from urllib.parse import urlsplit

from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessError, ValidationError
from werkzeug.exceptions import Unauthorized

_logger = logging.getLogger(__name__)
TRUST_GROUP = 'amr_resource.group_oidc_trust_admin'
CODE_GROUP = 'amr_resource.group_oidc_code_admin'
AUDIT_FIELDS = {'code_revision', 'code_digest', 'code_actor_id', 'code_date'}


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



def _legacy_plan(get_param, values, audiences, bindings, company_id):
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
    plan: dict = dict(version=1, values=dict(normalized, company_id=company_id),
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

    def check_access_rule(self, operation):
        result = super(RegistryAccess, self).check_access_rule(operation)
        if not self.env.su and any(row.company_id != self.env.company for row in self):
            raise AccessError('Registry access denied.')
        return result

    def _guard_company_values(self, values):
        if 'company_id' in values and values['company_id'] != self.env.company.id:
            raise AccessError('Registry access denied.')
        if 'issuer_id' in values:
            parent = self.env['oidc.issuer.register'].browse(values['issuer_id']).exists()
            parent.check_access_rights('read')
            parent.check_access_rule('read')
            if len(parent) != 1 or parent.company_id != self.env.company:
                raise AccessError('Registry access denied.')

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access_rights('create')
        for values in vals_list:
            self._guard_company_values(values)
        records = super(RegistryAccess, self).create(vals_list)
        _logger.info('Trust registry create model=%s ids=%s actor=%s',
                     self._name, records.ids, self.env.uid)
        return records

    def write(self, values):
        self.check_access_rights('write')
        self.check_access_rule('write')
        self._guard_company_values(values)
        result = super(RegistryAccess, self).write(values)
        _logger.info('Trust registry write model=%s ids=%s actor=%s',
                     self._name, self.ids, self.env.uid)
        return result

    def unlink(self):
        self.check_access_rights('unlink')
        self.check_access_rule('unlink')
        ids = self.ids
        result = super(RegistryAccess, self).unlink()
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
                                      ('resolver', 'Allowlisted Resolver')])
    resolver_key = fields.Selection([('get_user_match', 'Default')],
                                    readonly=True, default='get_user_match', required=True)
    python_code = fields.Text(groups=CODE_GROUP, copy=False,
                              help='Source storage only. Execution is disabled in v1.')
    code_revision = fields.Integer(readonly=True, copy=False, groups=CODE_GROUP)
    code_digest = fields.Char(readonly=True, copy=False, groups=CODE_GROUP)
    code_date = fields.Datetime(readonly=True, copy=False, groups=CODE_GROUP)
    company_id = fields.Many2one('res.company', required=True, index=True,
                                default=lambda self: self.env.company, ondelete='restrict')
    fixed_user_id = fields.Many2one('res.users', ondelete='restrict')
    code_actor_id = fields.Many2one('res.users', readonly=True, copy=False,
                                   ondelete='restrict', groups=CODE_GROUP)
    audience_ids = fields.One2many('oidc.issuer.register.audience', 'issuer_id')
    binding_ids = fields.One2many('oidc.issuer.subject', 'issuer_id')

    _sql_constraints = [('issuer_unique', 'unique(issuer)', 'Issuer must be unique.')]

    @api.model
    def _migrate_legacy_v1(self, values, audiences, bindings, dry_run=True):
        """Explicit additive migration; never called during install or token handling."""
        if type(dry_run) is not bool or not self._registry_role('amr_resource.group_oidc_trust_admin'):
            raise AccessError('Registry access denied.')
        self.check_access_rights('create')
        # sudo: legacy parameters/marker are read only after the designated admin guard.
        params = self.env['ir.config_parameter'].sudo()
        plan = _legacy_plan(params.get_param, values, audiences, bindings, self.env.company.id)
        data = plan['values']
        marker = 'amr_resource.migration.v1.company.%s' % self.env.company.id
        previous = params.get_param(marker)
        if previous and previous != plan['digest']:
            raise ValidationError('Migration revision conflicts with the recorded plan.')
        domain = [('issuer', '=', data['issuer'])]
        rows = self.with_context(active_test=False).search(domain)
        # sudo: detect a global issuer collision without returning another company profile.
        global_rows = self.sudo().with_context(active_test=False).search(domain)
        if len(global_rows) != len(rows) or len(rows) > 1:
            raise ValidationError('Migration issuer conflict.')
        commands = [(0, 0, {'value': value}) for value in plan['audiences']]
        candidate = self.new(dict(data, audience_ids=commands))
        candidate._check_profile()
        for binding in plan['bindings']:
            user = self.env['res.users'].browse(binding['user_id']).exists()
            try:
                self.env['amr.resource.helper']._eligible_user(user)
            except Unauthorized:
                raise ValidationError('Migration requires an eligible exact subject binding.') from None
        if rows:
            if not rows.active or any(rows[field] != value if field != 'fixed_user_id'
                                      else rows[field].id != value
                                      for field, value in data.items() if field != 'company_id'):
                raise ValidationError('Existing issuer configuration conflicts with migration.')
            if rows.company_id != self.env.company or sorted(rows.audience_ids.mapped('value')) != plan['audiences']:
                raise ValidationError('Existing issuer scope or audience conflict.')
            actual = sorted([{'sub': b.sub, 'user_id': b.user_id.id} for b in rows.binding_ids],
                            key=lambda b: b['sub'])
            if actual != plan['bindings']:
                raise ValidationError('Existing subject bindings conflict with migration.')
        elif previous:
            raise ValidationError('Recorded migration issuer is missing.')
        result = {'version': 1, 'issuer_count': 1, 'binding_count': len(bindings),
                  'dry_run': dry_run, 'already_applied': bool(previous)}
        if dry_run or previous:
            return result
        # A savepoint keeps registry creation and the revision marker atomic even for a caught error.
        with self.env.cr.savepoint():
            if not rows:
                self.create(dict(data, audience_ids=commands, binding_ids=[
                    (0, 0, binding) for binding in plan['bindings']]))
            params.set_param(marker, plan['digest'])
        _logger.info('Trust migration version=1 company=%s actor=%s bindings=%s',
                     self.env.company.id, self.env.uid, len(bindings))
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
            for name in AUDIT_FIELDS | {'python_code', 'resolver_key'}:
                if name not in values and 'default_' + name in self.env.context:
                    values[name] = self.env.context['default_' + name]
            self._guard_issuer_values(values, creating=True)
            if 'python_code' in values:
                values.update(self._source_audit(values['python_code'], 1))
            prepared.append(values)
        return super(AmrResourceIssuer, self).create(prepared)

    def write(self, values):
        self._guard_issuer_values(values)
        if 'python_code' not in values:
            return super(AmrResourceIssuer, self).write(values)
        self.check_access_rights('write')
        self.check_access_rule('write')
        for record in self:
            updated = dict(values)
            if values['python_code'] != record.python_code:
                updated.update(record._source_audit(values['python_code'], record.code_revision + 1))
            super(AmrResourceIssuer, record).write(updated)
        return True

    @api.constrains('issuer', 'token_profile', 'jwks_uri', 'token_endpoint',
                    'introspection_endpoint', 'client_id', 'azp', 'allow_missing_azp',
                    'local_public_key', 'local_key_ref', 'credential_ref', 'resolver_mode', 'fixed_user_id', 'company_id',
                    'audience_ids')
    def _check_profile(self):
        for record in self:
            import re
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
            if record.token_profile == 'jwt' and bool(record.jwks_uri) == bool(record.local_public_key):
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
            if record.token_profile == 'opaque' and not record.introspection_endpoint:
                raise ValidationError('Opaque profiles require a static introspection endpoint.')
            if (not record.allow_missing_azp and not record.azp) or (record.azp and not _exact_string(record.azp)):
                raise ValidationError('Configure one exact azp or explicitly allow its absence.')
            if not record.audience_ids:
                raise ValidationError('At least one audience is required.')
            if record.resolver_mode == 'fixed_user':
                user = record.fixed_user_id
                if (len(user) != 1 or not user.active or user.id == SUPERUSER_ID
                        or user.share or user.has_group('base.group_public')
                        or user.has_group('base.group_portal')
                        or record.company_id not in user.company_ids):
                    raise ValidationError('Fixed user must be an active eligible internal company user.')

    @api.model
    def _lookup(self, issuer=None, token_profile=None):
        """Private runtime read only: never use this elevation to execute a resolver."""
        if not _exact_string(issuer) or token_profile not in (None, 'jwt', 'opaque'):
            raise Unauthorized()
        try:
            company_id = self.env.company.id
            # sudo: read protected trust rows only, pinned to the effective request company.
            records = self.sudo().with_context(active_test=False).search([
                ('issuer', '=', issuer), ('active', '=', True), ('company_id', '=', company_id)])
            if len(records) != 1 or (token_profile and records.token_profile != token_profile):
                raise Unauthorized()
            return records
        except Exception:
            raise Unauthorized() from None


class AmrResourceAudience(models.Model):
    _name = 'oidc.issuer.register.audience'
    _description = 'Resource Issuer Audience'
    _inherit = 'amr.resource.registry.access'
    _rec_name = 'value'

    value = fields.Char(required=True)
    issuer_id = fields.Many2one('oidc.issuer.register', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='issuer_id.company_id', store=True, readonly=True)

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
    company_id = fields.Many2one(related='issuer_id.company_id', store=True, readonly=True)

    _sql_constraints = [('binding_unique', 'unique(issuer_id, sub)', 'Subject must be unique per issuer.')]

    @api.constrains('sub', 'user_id', 'issuer_id')
    def _check_binding(self):
        for record in self:
            if not _exact_string(record.sub):
                raise ValidationError('An exact nonempty subject is required.')
            user = record.user_id
            if (not user.active or user.id == SUPERUSER_ID or user.share
                    or user.has_group('base.group_public') or user.has_group('base.group_portal')
                    or record.company_id not in user.company_ids):
                raise ValidationError('Binding requires an active eligible internal company user.')
