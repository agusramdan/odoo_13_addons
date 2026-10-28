"""Optional service-client integration for Sentry reporting."""

import logging

from odoo import models

try:
    from ..services import REPORTER
except ImportError:
    # Offline contract tests load this file without its Odoo addon package.
    from amr_sentry.services import REPORTER


class ServiceClient(models.Model):
    _inherit = 'service.client'

    def _report_sentry(self, service_client=None, response=None, exception=None,
                       method=None, **kw):
        try:
            REPORTER.report(
                success=(exception is None),
                service_client=service_client,
                exception=exception,
            )
        except Exception:
            # Keep optional telemetry failures isolated and diagnostics secret-free.
            logging.getLogger(__name__).warning(
                'Sentry reporting failed; outcome retained')
