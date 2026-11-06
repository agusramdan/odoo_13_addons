# -*- coding: utf-8 -*-
from odoo import models


class TokenHelper(models.AbstractModel):
    _name = 'amr.token.helper'
    _inherit = 'amr.oidc.helper'
    _description = 'Legacy token helper compatibility alias'
