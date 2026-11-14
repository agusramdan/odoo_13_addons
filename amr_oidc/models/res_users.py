# -*- coding: utf-8 -*-

from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_user_by_username(self, username):
        user = self.search([('login', '=', username)], order=self._get_login_order(), limit=1)
        if user:
            return user
        user = self.search([('email', '=', username)], order=self._get_login_order(), limit=1)
        return user or self.search(self._get_login_domain(username), order=self._get_login_order(), limit=1)

    @api.model
    def _oidc_can_show_continue(self):
        return True
