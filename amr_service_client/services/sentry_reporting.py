# -*- coding: utf-8 -*-
"""Optional-addon bridge for service-client outcome reporting."""

import logging

_logger = logging.getLogger(__name__)


def report_outcome(env, service_client=None, response=None, exception=None, method=None, **kw):
    """Delegate reporting to the optional addon without affecting service calls."""
    try:
        env['service.client']._report_sentry(
            service_client=service_client,
            response=response,
            exception=exception,
            method=method,
            **kw
        )
    except Exception:
        _logger.debug('Sentry reporting unavailable', exc_info=False)


def report_sentry(env, service_client=None, response=None, exception=None, method=None, **kw):
    try:
        report_outcome(env, service_client=service_client, response=response, exception=exception, method=method, **kw)
    except Exception:
        _logger.debug('Sentry reporting configuration unavailable', exc_info=False)
