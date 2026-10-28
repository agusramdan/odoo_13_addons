"""Import-time, process-wide optional Sentry reporter bootstrap."""
import logging

from .config import load_config
from .sentry_reporting import build_reporter

_logger = logging.getLogger(__name__)


def _initialize():
    try:
        sentry_options, policy = load_config()
    except Exception:
        _logger.warning('Sentry configuration unavailable; reporting disabled')
        return build_reporter({}, {"enabled": False, "mode": "none"}, None)

    reportable = (policy or {}).get('mode') in ('all', 'error', 'selected')
    if not (policy or {}).get('enabled') or not reportable or not (sentry_options or {}).get('dsn'):
        return build_reporter(sentry_options, policy, None)
    try:
        import sentry_sdk
    except Exception:
        _logger.warning('Sentry SDK unavailable; reporting disabled')
        return build_reporter({}, {"enabled": False, "mode": "none"}, None)
    return build_reporter(sentry_options, policy, sentry_sdk)


REPORTER = _initialize()
