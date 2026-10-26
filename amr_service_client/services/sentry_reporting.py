# -*- coding: utf-8 -*-
"""Best-effort, data-minimizing Sentry reporting for outbound service calls."""

import logging
import os

_logger = logging.getLogger(__name__)
_ALLOWED_MODES = ('all', 'error', 'selected', 'none')

# Initialize once when this addon module is imported. The DSN is supplied by the
# runtime environment; never hardcode it or attach request/customer data by default.
amr_service_client_sentry_enabled = os.environ.get('AMR_SERVICE_CLIENT_SENTRY_ENABLED', 'True').lower() == 'true'
sentry_default_integrations= os.environ.get('SENTRY_DEFAULT_INTEGRATIONS', 'false').lower() == 'true'
try:
    _dsn = os.environ.get('SENTRY_DSN')
    if _dsn and amr_service_client_sentry_enabled:
        import sentry_sdk
        sentry_sdk.init(
            dsn=_dsn, default_integrations=sentry_default_integrations,
            # 1. Matikan atau batasi Tracing Performa (Paling krusial untuk overhead)
            traces_sample_rate=0.0,  # Set 0.0 jika tidak butuh APM/Performance monitoring
            # traces_sample_rate=0.01, # Atau set 1% saja untuk sampling di production
            
            # 2. Batasi Profiling (Jika menggunakan fitur profiling)
            profiles_sample_rate=0.0,
            
            # 3. Batasi pengumpulan data variabel lokal saat error (Menghemat memori)
            send_default_pii=False,
            include_local_variables=False, # Mematikan inspeksi variabel lokal di stack trace
            
            # 4. Batasi jumlah Breadcrumbs maksimal yang disimpan di memori
            max_breadcrumbs=20, # Defaultnya 100, kurangi untuk hemat RAM
            
            # 5. Batasi ukuran payload yang dikirim ke Sentry (Mengurangi penggunaan bandwidth)
            max_request_body_size='small', # Bisa 'none', 'small', 'medium',
            
            # 6. Batasi jumlah event yang dikirim per detik (Rate limiting)
            # max_events_per_second=5, # Uncomment jika ingin membatasi event per detik
            
            # 7. Batasi jumlah event yang disimpan di memori sebelum dikirim (Queue size)
            # max_queue_size=30, # Defaultnya 30, kurangi jika ingin lebih
            
            # 8. Batasi jumlah event yang dikirim per session (Session limit)
            # max_sessions_per_minute=10, # Uncomment jika ingin membatasi session per menit
            
            # 9. Batasi jumlah event yang dikirim per project (Project limit)
            # max_events_per_minute=100, # Uncomment jika ingin membatasi event per menit
        )
except Exception:
    _logger.debug('Sentry initialization unavailable', exc_info=False)


def report_outcome(env, mode, opted_in, outcome, method=None, status_code=None):
    """Send only fixed, safe metadata; never allow reporting to affect callers."""
    if not amr_service_client_sentry_enabled:
        _logger.debug('Sentry reporting disabled by environment variable')
        return
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

def report_sentry(env, outcome, response=None, exception=None):
        try:
            mode = (env['ir.config_parameter'].sudo().get_param('amr_service_client.sentry_mode', 'none') or 'none').lower()
            report_outcome(env, mode or 'none', bool(getattr(self, 'sentry_opt_in', False)),
                           outcome, method=self.method,
                           status_code=getattr(response, 'status_code', None))
        except Exception:
            _logger.debug('Sentry reporting configuration unavailable', exc_info=False)