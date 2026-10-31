# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = [_name, 'internal.data.name.mixin']
