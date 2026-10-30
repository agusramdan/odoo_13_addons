"""Safe-file profile presence contract, independent of SDK process policy."""
import importlib.util
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from support import ROOT

spec = importlib.util.spec_from_file_location(
    'safe_file_config_test', ROOT / 'amr_sentry/services/config.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

PROFILE = {
    'default_integrations': False, 'auto_enabling_integrations': False,
    'integrations': [], 'include_local_variables': False,
    'include_source_context': False, 'send_default_pii': False,
    'max_request_body_size': 'never', 'max_breadcrumbs': 0,
    'auto_session_tracking': False, 'send_client_reports': False,
    'enable_metrics': False, 'debug': False,
}


class SafeFileProfilePresenceTest(unittest.TestCase):
    def test_active_file_rejects_each_missing_safety_key(self):
        for key in PROFILE:
            with self.subTest(missing=key):
                sentry = dict(PROFILE, dsn='https://synthetic.invalid/1')
                del sentry[key]
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as stream:
                    json.dump({'sentry': sentry, 'service_client': {
                        'enabled': True, 'mode': 'error'}}, stream)
                    stream.flush()
                    with patch.dict(os.environ, {'AMR_SENTRY_CONFIG': stream.name}):
                        with self.assertRaises(config.SentryConfigError):
                            config.load_config()

    def _load(self, sentry, policy=None):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as stream:
            json.dump({'sentry': sentry, 'service_client': policy or {}}, stream)
            stream.flush()
            with patch.dict(os.environ, {'AMR_SENTRY_CONFIG': stream.name}):
                return config.load_config()

    def test_each_present_safety_value_has_exact_type_and_value(self):
        for key, expected in PROFILE.items():
            invalid = ([True, None, 'false', 0] if type(expected) is bool else
                       [False, 1, '0'] if type(expected) is int else
                       [['x'], None, '[]'] if type(expected) is list else
                       ['medium', None, False])
            for value in invalid:
                with self.subTest(key=key, value=value):
                    with self.assertRaises(config.SentryConfigError):
                        self._load(dict(PROFILE, **{key: value}))

    def test_rejects_non_allowlisted_sentry_options_even_when_disabled(self):
        for key in ('sample_rate', 'data_collection', 'with_locals', 'request_bodies',
                    'enable_logs', 'transport', 'before_send', 'unknown'):
            with self.subTest(key=key):
                with self.assertRaises(config.SentryConfigError):
                    self._load({key: False})

    def test_metadata_must_be_strings_when_present(self):
        for key in ('environment', 'release', 'server_name', 'project_root'):
            self.assertEqual(self._load({key: 'synthetic'})[0], {key: 'synthetic'})
            for value in (None, False, 0, [], {}):
                with self.subTest(key=key, value=value):
                    with self.assertRaises(config.SentryConfigError):
                        self._load({key: value})

    def test_dsn_must_be_null_or_string_even_when_disabled(self):
        for value in (None, '', 'https://synthetic.invalid/1'):
            self.assertEqual(self._load({'dsn': value})[0], {'dsn': value})
        for value in (False, 0, 1, [], {}, True):
            with self.subTest(value=value):
                with self.assertRaises(config.SentryConfigError):
                    self._load({'dsn': value})
