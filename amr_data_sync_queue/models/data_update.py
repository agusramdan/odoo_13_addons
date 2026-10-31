# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ExternalDataUpdate(models.Model):
    _inherit = 'external.data.update'

    def dispatch_process(self,run_immediate=False):
        self.with_delay().process_data()
