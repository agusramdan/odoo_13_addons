# -*- coding: utf-8 -*-
"""Best-effort, data-minimizing Sentry reporting for outbound service calls."""

import logging

_logger = logging.getLogger(__name__)
_ALLOWED_MODES = ('all', 'error', 'selected', 'none')


def report_outcome(env, mode, opted_in, outcome, method=None, status_code=None):
    """Send only fixed, safe metadata; never allow reporting to affect callers."""
    if mode not in _ALLOWED_MODES or mode == 'none':
        return
    if mode == 'selected' and not opted_in:
        return
    if mode == 'error' and outcome == 'success':
        return
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            scope.set_tag('component', 'amr_service_client')
            scope.set_tag('outcome', outcome)
            if method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'):
                scope.set_tag('http.method', method)
            if isinstance(status_code, int):
                scope.set_tag('http.status_code', status_code)
            scope.set_extra('integration', 'service_client')
            if outcome == 'success':
                sentry_sdk.capture_message('Service client request completed', level='info')
            else:
                # Fixed exception text; raw exception/request data is intentionally excluded.
                sentry_sdk.capture_exception(RuntimeError('Service client request failed'))
    except Exception:
        _logger.debug('Sentry reporting unavailable', exc_info=False)
