"""N3 component regression: extracted call method, synthetic HTTP; not ORM."""
import types
import unittest
from test_U11_sentry_behavior import extracted_method
from support import ROOT

class N3(unittest.TestCase):
    def test_http_error_true_preserves_exception_identity_and_single_report(self):
        original = RuntimeError('synthetic-http')
        requests, reports = [], []
        class Response:
            def raise_for_status(self):
                raise original
        response = Response()
        def request(**kwargs):
            requests.append(kwargs)
            return response
        class Client:
            def prepare_request_context(self, *args, **kwargs):
                return {'method': 'POST'}
            def _report_sentry(self, **kwargs):
                reports.append(kwargs)
        call = extracted_method(ROOT / 'amr_service_client/models/service_client.py', 'ServiceClient', 'call', {'requests': types.SimpleNamespace(request=request)})
        with self.assertRaises(RuntimeError) as caught:
            call(Client(), method='POST', raise_exception=True)
        self.assertIs(caught.exception, original)
        self.assertEqual(len(requests), 1)
        self.assertEqual(len(reports), 1)
        self.assertIs(reports[0]['exception'], original)
        self.assertNotIn('response', reports[0])
