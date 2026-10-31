# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResCountry(models.Model):
    _name = 'res.country'
    _inherit = [_name, 'internal.data.name.mixin']
