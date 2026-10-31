"""Pure optional Sentry policy reporter; SDK is injected by the caller."""
import logging


_logger = logging.getLogger(__name__)
_ALLOWED_MODES = ('all', 'error', 'selected', 'none')


class _Reporter(object):
    def __init__(self, sdk, mode):
        self._sdk = sdk
        self._mode = mode

    def report(self, success, service_client=None, exception=None):
        if self._mode == 'none':
            return
        if self._mode == 'selected' and not getattr(service_client, 'sentry_opt_in', False):
            return
        if success:
            if self._mode not in ('all', 'selected'):
                return
            try:
                self._sdk.capture_message('Service client request completed', level='info')
            except Exception:
                _logger.warning('Sentry reporting failed; outcome retained')
            return
        try:
            self._sdk.capture_exception(exception or RuntimeError('Service client request failed'))
        except Exception:
            _logger.warning('Sentry reporting failed; outcome retained')


def build_reporter(sentry_options, service_client_policy, sdk):
    """Initialize injected SDK only when enabled, configured, and reportable."""
    policy = service_client_policy or {}
    mode = policy.get('mode', 'none')
    dsn = (sentry_options or {}).get('dsn')
    if not policy.get('enabled') or mode == 'none' or mode not in _ALLOWED_MODES or not dsn:
        return _Reporter(None, 'none')
    try:
        sdk.init(**sentry_options)
    except Exception:
        _logger.warning('Sentry initialization failed; reporting disabled')
        return _Reporter(None, 'none')
    return _Reporter(sdk, mode)
