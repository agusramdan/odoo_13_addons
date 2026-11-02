"""Offline behavior tests for optional Sentry reporting policy."""
import unittest

import amr_sentry.services.sentry_reporting as reporting


class FakeSDK(object):
    def __init__(self):
        self.init_calls = []
        self.message_calls = []
        self.exception_calls = []

    def init(self, **kwargs):
        self.init_calls.append(kwargs)

    def capture_message(self, message, level=None):
        self.message_calls.append((message, level))

    def capture_exception(self, exception):
        self.exception_calls.append(exception)


class SentryPolicyTests(unittest.TestCase):
    def test_disabled_policy_never_initializes_or_captures(self):
        sdk = FakeSDK()
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1'}, {'enabled': False, 'mode': 'all'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False, exception=RuntimeError('private'))
        self.assertEqual([], sdk.init_calls)
        self.assertEqual([], sdk.message_calls)
        self.assertEqual([], sdk.exception_calls)

    def test_none_mode_never_initializes_or_captures(self):
        sdk = FakeSDK()
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1'}, {'enabled': True, 'mode': 'none'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False, exception=RuntimeError('private'))
        self.assertEqual([], sdk.init_calls)
        self.assertEqual([], sdk.message_calls)
        self.assertEqual([], sdk.exception_calls)

    def test_missing_dsn_never_initializes_or_captures(self):
        sdk = FakeSDK()
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({}, {'enabled': True, 'mode': 'all'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False)
        self.assertEqual([], sdk.init_calls)
        self.assertEqual([], sdk.message_calls)
        self.assertEqual([], sdk.exception_calls)

    def test_all_mode_initializes_only_sdk_options_and_reports_both_outcomes(self):
        sdk = FakeSDK()
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1', 'environment': 'test'}, {'enabled': True, 'mode': 'all'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False, exception=RuntimeError('private'))
        self.assertEqual([{'dsn': 'https://example.invalid/1', 'environment': 'test'}], sdk.init_calls)
        self.assertEqual([('Service client request completed', 'info')], sdk.message_calls)
        self.assertEqual(1, len(sdk.exception_calls))
        self.assertIsInstance(sdk.exception_calls[0], RuntimeError)

    def test_error_mode_reports_only_errors(self):
        sdk = FakeSDK()
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1'}, {'enabled': True, 'mode': 'error'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False, exception=RuntimeError('private'))
        self.assertEqual([], sdk.message_calls)
        self.assertEqual(1, len(sdk.exception_calls))

    def test_selected_mode_requires_opt_in_and_reports_both(self):
        sdk = FakeSDK()
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1'}, {'enabled': True, 'mode': 'selected'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True, service_client=type('Client', (), {'sentry_opt_in': False})())
            reporter.report(success=True, service_client=type('Client', (), {'sentry_opt_in': True})())
            reporter.report(success=False, service_client=type('Client', (), {'sentry_opt_in': True})(), exception=RuntimeError('private'))
        self.assertEqual([('Service client request completed', 'info')], sdk.message_calls)
        self.assertEqual(1, len(sdk.exception_calls))

    def test_init_failure_disables_reporter_without_exposing_exception(self):
        sdk = FakeSDK()
        def fail_init(**kwargs):
            sdk.init_calls.append(kwargs)
            raise RuntimeError('secret DSN and private config')
        sdk.init = fail_init
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1'}, {'enabled': True, 'mode': 'all'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False)
        self.assertEqual(1, len(sdk.init_calls))
        self.assertEqual([], sdk.message_calls)
        self.assertEqual([], sdk.exception_calls)

    def test_capture_failures_are_swallowed(self):
        sdk = FakeSDK()
        def fail_message(*args, **kwargs):
            raise RuntimeError('private capture failure')
        def fail_exception(*args, **kwargs):
            raise RuntimeError('private transport failure')
        sdk.capture_message = fail_message
        sdk.capture_exception = fail_exception
        factory = getattr(reporting, 'build_reporter', None)
        reporter = factory({'dsn': 'https://example.invalid/1'}, {'enabled': True, 'mode': 'all'}, sdk) if callable(factory) else None
        if reporter is not None:
            reporter.report(success=True)
            reporter.report(success=False)
        self.assertEqual(1, len(sdk.init_calls))


if __name__ == '__main__':
    unittest.main()
