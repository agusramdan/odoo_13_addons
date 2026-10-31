# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _name = 'res.currency'
    _inherit = [_name, 'internal.data.name.mixin']
