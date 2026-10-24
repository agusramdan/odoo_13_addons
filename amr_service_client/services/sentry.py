# -*- coding: utf-8 -*-
"""Best-effort Sentry reporting without transmitting integration data."""

import logging

_logger = logging.getLogger(__name__)


def capture_service_event(env, record_type, record_id, state, endpoint_id=None,
                         client_id=None, error_type=None):
    """Capture metadata only; Sentry SDK/DSN initialization belongs to deployment."""
    try:
        settings = env['ir.config_parameter'].sudo()
        mode = settings.get_param('amr_service_client.sentry_mode', 'none')
        if mode not in ('all', 'error', 'selected'):
            return
        if mode == 'error' and state != 'error':
            return
        if mode == 'selected' and (state != 'error' or not client_id or
                                   not client_id.sentry_enabled):
            return
        try:
            import sentry_sdk
        except ImportError:
            return
        with sentry_sdk.push_scope() as scope:
            scope.set_tag('service_client.record_type', record_type)
            scope.set_tag('service_client.state', state)
            scope.set_tag('service_client.record_id', record_id)
            if endpoint_id:
                scope.set_tag('service_client.endpoint_id', endpoint_id)
            if client_id:
                scope.set_tag('service_client.client_id', client_id.id)
            if error_type:
                scope.set_tag('service_client.error_type', error_type)
            sentry_sdk.capture_message(
                'Service client request %s' % state,
                level='error' if state == 'error' else 'info',
            )
    except Exception:
        _logger.debug('Sentry reporting failed', exc_info=True)
