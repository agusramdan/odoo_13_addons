# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResPartnerUsers(models.Model):
    _inherit = 'res.partner'

    def lookup_internal_from_external_data(self, item, **kwargs):
        item_dict = {}
        if isinstance(item, list):
            if len(item) > 0:
                item_dict['id'] = item[0]
            if len(item) > 1:
                item_dict['name'] = item[1]
        elif isinstance(item, dict):
            item_dict = item

        if item_dict:
            domain = []
            if item_dict.get('email'):
                domain.append(('email', '=', item_dict.get('email')))
                return self.sudo().search(domain, limit=1)
        return self.browse()
