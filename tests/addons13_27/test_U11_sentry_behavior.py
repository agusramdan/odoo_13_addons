"""Isolated tests for data-minimizing Sentry reporting policy."""
from support import ROOT
import importlib.util
import sys
import types
import ast
import json
import unittest

_REPORTER_PATH = ROOT / 'amr_service_client/services/sentry_reporting.py'
_spec = importlib.util.spec_from_file_location('sentry_reporting_test', _REPORTER_PATH)
reporter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reporter)


def extracted_method(path, class_name, method_name, namespace):
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    module = ast.Module(body=[method], type_ignores=[])
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace[method_name]


class SentryReporting(unittest.TestCase):
    def test_modes_gate_reporting_and_selected_requires_opt_in(self):
        calls = []
        scope = types.SimpleNamespace(set_tag=lambda *a: None, set_extra=lambda *a: None)
        class Context:
            def __enter__(self): return scope
            def __exit__(self, *a): pass
        sdk = types.SimpleNamespace(push_scope=lambda: Context(),
            capture_message=lambda *a, **k: calls.append(('message', a, k)),
            capture_exception=lambda *a, **k: calls.append(('exception', a, k)))
        sys.modules['sentry_sdk'] = sdk
        reporter.report_outcome(None, 'selected', False, 'error')
        self.assertEqual(calls, [])
        reporter.report_outcome(None, 'error', True, 'success')
        self.assertEqual(calls, [])
        reporter.report_outcome(None, 'selected', True, 'error', method='POST', status_code=503)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('credentials', repr(calls))

    def test_sentry_failure_is_best_effort(self):
        sys.modules['sentry_sdk'] = types.SimpleNamespace(push_scope=lambda: (_ for _ in ()).throw(RuntimeError('offline')))
        reporter.report_outcome(None, 'all', False, 'error')

    def test_real_log_send_reports_http_failure_and_preserves_logged_error(self):
        path = ROOT / 'amr_service_client/models/service_client_log.py'
        events = []
        class Response:
            status_code = 503
            text = 'private response body'
            def raise_for_status(self): raise RuntimeError('http 503')
        class Provider:
            def authenticate(self, context, audience): return context
        class Client:
            provider = Provider()
            def _report_sentry(self, outcome, **kwargs): events.append((outcome, kwargs.get('response').status_code))
        class Endpoint:
            audience = 'a'
            def request_headers_default(self, headers): return headers
        class Owner:
            def get_service_client(self, *a): return Client()
        class Log:
            client_id, endpoint_id, credential_id = Owner(), Endpoint(), None
            request_context = json.dumps({'url': 'https://example.invalid'})
            updates = None
            def format_error(self, exc): return str(exc)
            def sanitize_sensitive_data(self, value): return value
            def write(self, values): self.updates = values
        namespace = {'json': json, 'requests': types.SimpleNamespace(request=lambda **kw: Response())}
        send = extracted_method(path, 'ServiceClientLog', 'send', namespace)
        result = send(Log())
        self.assertEqual(events, [('error', 503)])
        self.assertEqual(result.updates, {'state': 'error', 'response': 'http 503'})

    def test_real_service_client_call_outcomes_privacy_and_transport_semantics(self):
        path = ROOT / 'amr_service_client/models/service_client.py'
        calls = []
        class Response:
            status_code = 503
            text = 'private response body'
        def run(response=None, error=None):
            namespace = {'requests': types.SimpleNamespace(request=lambda **kw: (_ for _ in ()).throw(error) if error else response)}
            method = extracted_method(path, 'ServiceClient', 'call', namespace)
            class Client:
                method = 'POST'
                def prepare_request_context(self, *a, **kw): return {'url': 'https://example.invalid', 'headers': {'Authorization': 'secret'}}
                def _report_sentry(self, outcome, **kwargs): calls.append((outcome, kwargs))
            client = Client()
            return method(client)
        self.assertIs(run(Response()).status_code, 503)
        self.assertEqual(calls[-1][0], 'error')
        self.assertIs(calls[-1][1]['response'].status_code, 503)
        success = types.SimpleNamespace(status_code=200, text='private')
        self.assertIs(run(success), success)
        self.assertEqual(calls[-1][0], 'success')
        transport = RuntimeError('transport secret')
        with self.assertRaises(RuntimeError) as caught: run(error=transport)
        self.assertIs(caught.exception, transport)
        self.assertEqual(calls[-1][0], 'error')
        self.assertIs(calls[-1][1]['exception'], transport)
        self.assertNotIn('private response body', repr(calls))
        self.assertNotIn('Authorization', repr(calls))

    def test_real_dispatch_send_success_and_failure_reporting_are_best_effort(self):
        path = ROOT / 'amr_service_client/models/service_client.py'
        for status, outcome in ((200, 'success'), (503, 'error')):
            events = []
            class Response:
                status_code = status
                text = 'private response body'
                def raise_for_status(self):
                    if status >= 400: raise RuntimeError('http failure')
            client = types.SimpleNamespace(prepare_request_context=lambda **kw: {'url': 'https://example.invalid'},
                _report_sentry=lambda result, **kw: events.append((result, kw)))
            namespace = {'requests': types.SimpleNamespace(request=lambda **kw: Response()),
                '_logger': types.SimpleNamespace(exception=lambda *a: None)}
            method = extracted_method(path, 'ServiceClientSend', 'dispatch_send', namespace)
            sender = types.SimpleNamespace(active_log=False, payload={'token': 'secret'}, service_client=client,
                client_id=None, endpoint_id=None, credential_id=None,
                env={'service.client.log': types.SimpleNamespace(create_error=lambda *a, **kw: events.append(('logged', a)))})
            method(sender)
            self.assertEqual(events[0][0], outcome)
            self.assertNotIn('private response body', repr(events))
            if status == 503:
                def report_best_effort(*a, **kw):
                    try: raise RuntimeError('sentry offline')
                    except Exception: pass
                client._report_sentry = report_best_effort
                method(sender)
                self.assertTrue(any(e[0] == 'logged' for e in events))

    def test_real_log_send_reports_success(self):
        path = ROOT / 'amr_service_client/models/service_client_log.py'
        events = []
        class Response:
            status_code = 201
            text = 'ok'
            def raise_for_status(self): pass
        class Provider:
            def authenticate(self, context, audience): return context
        class Client:
            provider = Provider()
            def _report_sentry(self, outcome, **kwargs): events.append(outcome)
        class Endpoint:
            audience = 'a'
            def request_headers_default(self, headers): return headers
        class Owner:
            def get_service_client(self, *a): return Client()
        class Log:
            client_id, endpoint_id, credential_id = Owner(), Endpoint(), None
            request_context = json.dumps({'url': 'https://example.invalid'})
            def format_error(self, exc): return str(exc)
            def sanitize_sensitive_data(self, value): return value
            def write(self, values): self.updates = values
        send = extracted_method(path, 'ServiceClientLog', 'send', {'json': json, 'requests': types.SimpleNamespace(request=lambda **kw: Response())})
        result = send(Log())
        self.assertEqual(events, ['success'])
        self.assertEqual(result.updates['state'], 'done')
