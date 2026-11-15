# -*- coding: utf-8 -*-

import hashlib
import hmac
import os
import time

from odoo import api, models, tools
from odoo.exceptions import AccessError, UserError


_AUDIENCE_UNSET = object()
_LEGACY_CACHE_REVISION_KEY = os.urandom(32)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def is_user_allow_create_token(self):
        return True

    @api.model
    def _legacy_cache_fingerprint(self, value):
        """Opaque, process-local fingerprint for potentially secret material."""
        return hmac.new(
            _LEGACY_CACHE_REVISION_KEY, repr(value).encode('utf-8'), hashlib.sha256
        ).hexdigest()

    @api.model
    def _legacy_cache_context(self, user, audience_key):
        helper = self.env['amr.oidc.helper']
        required = ('_check_token_issuance_access', 'get_expires_in',
                    'get_signature_type', 'get_signature_algorithm',
                    'get_issuer', '_get_encoder')
        if not all(callable(getattr(helper, name, None)) for name in required):
            return None

        # Authorization and effective config validation must precede every cache lookup.
        helper._check_token_issuance_access(user)
        ttl = helper.get_expires_in()
        if type(ttl) is not int:
            return None
        signature_type = helper.get_signature_type()
        algorithm = helper.get_signature_algorithm()
        issuer = helper.get_issuer()
        encoder = helper._get_encoder()
        if audience_key is _AUDIENCE_UNSET:
            effective_audience = helper.get_audience()
        else:
            effective_audience = audience_key

        parameter_keys = [
            'amr_token.signature_type',
            'amr_token.public_key_algorithm' if signature_type == 'public_key'
            else 'amr_token.secret_algorithm',
            'amr_token.expires_in',
            'web.base.url',
        ]
        if signature_type == 'secret':
            parameter_keys.append('amr_token.secret')
        if audience_key is _AUDIENCE_UNSET:
            parameter_keys.append('database.uuid')

        params = self.env['ir.config_parameter'].sudo()
        rows = params.search_read(
            [('key', 'in', parameter_keys)], ['key', 'value', 'write_date'])
        values = {row.get('key'): row.get('value') for row in rows}
        actual_type = values.get('amr_token.signature_type')
        if actual_type not in ('secret', 'public_key'):
            raise ValueError('A supported signature type is required')
        if actual_type != signature_type:
            raise ValueError('Signing configuration changed during token issuance')

        actual_algorithm_key = (
            'amr_token.public_key_algorithm' if actual_type == 'public_key'
            else 'amr_token.secret_algorithm'
        )
        actual_algorithm = values.get(actual_algorithm_key)
        if not actual_algorithm:
            raise ValueError('A configured signing algorithm is required')
        if actual_algorithm != algorithm:
            raise ValueError('Token algorithm does not match provider configuration')

        actual_issuer = values.get('web.base.url')
        if not isinstance(actual_issuer, str):
            raise ValueError('A valid HTTPS issuer is required')
        from urllib.parse import urlparse
        parsed_issuer = urlparse(actual_issuer)
        if (parsed_issuer.scheme != 'https' or not parsed_issuer.netloc
                or parsed_issuer.username or parsed_issuer.password
                or parsed_issuer.query or parsed_issuer.fragment):
            raise ValueError('A valid HTTPS issuer is required')
        if actual_issuer.rstrip('/') != issuer:
            raise ValueError('Signing configuration changed during token issuance')

        actual_ttl = int(values.get('amr_token.expires_in', 86400))
        if actual_ttl != ttl:
            raise ValueError('Signing configuration changed during token issuance')
        if audience_key is _AUDIENCE_UNSET:
            actual_audience = values.get('database.uuid')
            if not actual_audience:
                raise ValueError('A configured audience is required')
            if actual_audience != effective_audience:
                raise ValueError('Signing configuration changed during token issuance')

        if signature_type == 'secret':
            signing_material = getattr(encoder, 'secret', None)
            actual_secret = values.get('amr_token.secret')
            if not actual_secret:
                raise ValueError('JWT Secret not set')
            if actual_secret != signing_material:
                raise ValueError('Signing configuration changed during token issuance')
            key_revision = ()
        else:
            keys = self.env['amr.public.key'].sudo().search([
                ('algorithm', '=', algorithm), ('active', '=', True),
                ('is_signing', '=', True),
            ], limit=1)
            if len(keys) != 1:
                raise Exception('Private Key not set')
            signing_material = keys.private_key
            key_revision = (
                keys.id, keys.kid, keys.algorithm, keys.write_date,
                keys.active, keys.is_signing,
            )

        parameter_revision = tuple(sorted(
            (row.get('key'), row.get('id'), row.get('write_date'))
            for row in rows
        ))
        parameter_values = tuple((key, values.get(key)) for key in parameter_keys)
        config_revision = self._legacy_cache_fingerprint((
            parameter_revision, parameter_values, signature_type, algorithm,
            issuer, effective_audience, ttl, key_revision, signing_material,
        ))
        policy_revision = self._legacy_cache_fingerprint((
            user.id, getattr(user, 'write_date', None),
            getattr(user, 'login', None), getattr(user, 'email', None),
            getattr(user, 'active', None), getattr(user, 'share', None),
        ))
        return ttl, config_revision, policy_revision

    @api.model
    @tools.ormcache('uid', 'actor_uid', 'audience_key', 'dbname', 'registry_id',
                    'bucket', 'config_revision', 'policy_revision')
    def _get_access_token_cached(self, uid, actor_uid, audience_key, dbname,
                                 registry_id, bucket, config_revision,
                                 policy_revision):
        user = self.browse(uid)
        if audience_key is _AUDIENCE_UNSET:
            token, _, _ = self.env['amr.oidc.helper']._generate_user_token(user)
        else:
            audience = list(audience_key) if isinstance(audience_key, tuple) else audience_key
            token, _, _ = self.env['amr.oidc.helper']._generate_user_token(
                user, audience=audience
            )
        return token

    @api.model
    def _get_access_token(self, uid, audience_key, bucket=None):
        user = self.browse(uid)
        helper = self.env['amr.oidc.helper']
        # Accept the historical bucket argument but always derive the safe bucket here.
        context = self._legacy_cache_context(user, audience_key)
        if context is None:
            # Incomplete test doubles or older helper variants cannot safely cache.
            if audience_key is _AUDIENCE_UNSET:
                return helper._generate_user_token(user)[0]
            audience = list(audience_key) if isinstance(audience_key, tuple) else audience_key
            return helper._generate_user_token(user, audience=audience)[0]

        ttl, config_revision, policy_revision = context
        if ttl <= 0:
            token = self._get_access_token_fresh(user, audience_key)
        else:
            interval = min(300, ttl)
            bucket = int(time.time() / interval)
            token = self._get_access_token_cached(
                uid, self.env.uid, audience_key, self.env.cr.dbname,
                id(self.env.registry), bucket, config_revision, policy_revision,
            )

        if self._legacy_cache_context(user, audience_key) != context:
            raise ValueError('Signing configuration changed during token issuance')
        return token

    @api.model
    def _get_access_token_fresh(self, user, audience_key):
        helper = self.env['amr.oidc.helper']
        if audience_key is _AUDIENCE_UNSET:
            return helper._generate_user_token(user)[0]
        audience = list(audience_key) if isinstance(audience_key, tuple) else audience_key
        return helper._generate_user_token(user, audience=audience)[0]

    def get_access_token(self, create=False, audience=_AUDIENCE_UNSET, **kw):
        missing = object()
        resource = kw.pop('resource', missing)
        has_resource = resource is not missing
        if has_resource:
            if not isinstance(resource, str) or not resource.strip():
                raise ValueError('Invalid resource')
            audience = resource
        elif audience is not _AUDIENCE_UNSET and audience is None:
            raise ValueError('A valid audience is required')
        self.ensure_one()
        if self.id != self.env.uid and not self.env.user.has_group('base.group_system'):
            raise AccessError('You may only issue an access token for yourself.')
        if not self.is_user_allow_create_token():
            raise UserError('User not allowed to create access token')
        if audience is _AUDIENCE_UNSET:
            audience_key = audience
        else:
            audience = self.env['amr.oidc.helper']._validate_audience(audience)
            audience_key = tuple(audience) if isinstance(audience, list) else audience
        return self._get_access_token(self.id, audience_key)

    def create_access_token(self, audience='', **kw):
        raise UserError('Persistent access-token storage is not available')

    def add_url_access_token(self, url=None, create=True, param_name='access_token',
                             audience=_AUDIENCE_UNSET, url_type='access_token', **kw):
        raise UserError('URL access tokens are disabled')

    def get_auto_login_url(self, url=None, create=True, web_token_access_path='/web_token_access',
                           audience=_AUDIENCE_UNSET, **kw):
        raise UserError('URL access tokens are disabled')
