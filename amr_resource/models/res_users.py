# -*- coding: utf-8 -*-

import logging

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = 'base'

    def user_machine_sudo(self, user):
        """ with_user(user)

        Return a new version of this recordset attached to the given user_machine, in
        superuser mode
        """
        if not user:
            return self

        return self.with_user(user)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def is_user_machine(self):
        self.ensure_one()
        return bool(self.has_group('amr_resource.group_machine'))

    def is_user_technical(self):
        self.ensure_one()
        return bool(self.has_group('amr_resource.group_technical'))

    def is_user_business(self):
        self.ensure_one()
        return not self.share and not self.is_user_technical() and self.is_user_machine()

    def is_user_allow_create_token(self):
        self.ensure_one()
        return True

    def decode(self, token, **kw):
        self.ensure_one()
        helper = self.env['amr.resource.helper']
        payload = helper.decode(token, **kw)
        uid = helper.get_uid(payload)
        if uid == self.id:
            return payload
        return None

    def get_access_token(self, **kw):
        if not self.is_user_allow_create_token():
            raise UserError('User not allowed to create access token')

        raise NotImplemented

    def create_access_token(self, **kw):
        if not self.is_user_allow_create_token():
            raise UserError('User not allowed to create access token')

        raise NotImplemented

    @api.model
    def add_url_access_token(self, url=None, url_type='access_token', **kw):
        if url_type != 'access_token':
            return self.get_auto_login_url(url=url, **kw)
        return url

    @api.model
    def get_auto_login_url(self, url=None, **kw):
        return url

    def with_access_token_context(self, validate=True):
        helper = self.env['amr.resource.helper']
        marker = self.env.context.get('__access_token_context')
        if helper._verified(marker) and helper.get_uid(marker) == self.id:
            return self
        if validate:
            payload = helper.validate(helper.get_bearer_token())
        else:
            payload = self.env['ir.http'].get_jwt_payload()
        if not helper._verified(payload):
            from werkzeug.exceptions import Unauthorized
            raise Unauthorized()
        if helper.get_uid(payload) != self.id:
            return self
        return self.with_context(__access_token_context=payload)
