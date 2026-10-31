# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ResLang(models.Model):
    _name = 'res.lang'
    _inherit = [_name, 'internal.data.name.mixin']
