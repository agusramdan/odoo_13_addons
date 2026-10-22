"""Actual candidate Python methods with inert verifier/log boundaries, not UAT."""
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from support import ParentHelper, load


class SyntheticVerifierFailure(Exception):
    def __init__(self):
        super().__init__('synthetic-verifier-marker')
        self.str_calls = 0
        self.repr_calls = 0

    def __str__(self):
        self.str_calls += 1
        return 'synthetic-verifier-marker'

    def __repr__(self):
        self.repr_calls += 1
        return 'synthetic-verifier-marker'


class MemoryHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class FailureLogging(unittest.TestCase):
    def capture(self, logger):
        handler = MemoryHandler()
        original = (logger.handlers[:], logger.filters[:], logger.level,
                    logger.propagate, logger.disabled)
        def restore():
            (logger.handlers, logger.filters, logger.level,
             logger.propagate, logger.disabled) = original
            handler.records.clear()
            handler.close()
        self.addCleanup(restore)
        logger.handlers = [handler]
        logger.filters = []
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.disabled = False
        return handler.records

    def assert_log_contract(self, records, failure):
        # Inspect only in memory: never format a traceback or persist a record.
        rendered = [record.getMessage() for record in records]
        self.assertTrue(all('synthetic-verifier-marker' not in text
                            for text in rendered))
        self.assertTrue(all(not record.args for record in records))
        self.assertTrue(all(not record.exc_info for record in records))
        self.assertTrue(all(not record.stack_info for record in records))
        self.assertEqual(failure.str_calls, 0)
        self.assertEqual(failure.repr_calls, 0)
        self.assertTrue(all(text == 'Error _check_credentials' for text in rendered))

    def test_password_verifier_failure_log_contract(self):
        module = load('models/helper.py')
        helper = module.TokenHelper()
        failure = SyntheticVerifierFailure()
        user = Mock()
        user.with_user.return_value = user
        user._check_credentials.side_effect = failure
        client = SimpleNamespace(user_id=user, name='synthetic-client')
        store = Mock()
        store.sudo.return_value = store
        store.search.return_value = client
        helper.env = {'oidc.client': store}
        helper.generate_user_token = Mock()
        records = self.capture(module._logger)
        with patch.object(ParentHelper, 'do_password_grant', create=True,
                          return_value={}) as parent:
            result = helper.do_password_grant({'client_id': 'synthetic-client',
                                               'client_secret': 'synthetic-input'})
            self.assertEqual(result, {'status': 401, 'error': 'invalid_grant'})
            user.with_user.assert_called_once_with(user)
            user._check_credentials.assert_called_once_with('synthetic-input')
            parent.assert_not_called()
            helper.generate_user_token.assert_not_called()
            self.assert_log_contract(records, failure)

    def test_client_credentials_verifier_failure_log_contract(self):
        module = load('models/helper.py')
        helper = module.TokenHelper()
        failure = SyntheticVerifierFailure()
        client = Mock()
        client.check_credentials.side_effect = failure
        store = Mock()
        store.sudo.return_value = store
        store.search.return_value = client
        helper.env = {'oidc.client': store}
        helper.get_basic_auth = Mock(return_value=(None, None))
        helper.generate_user_token = Mock(return_value=(object(), None, 1))
        records = self.capture(module._logger)
        result = helper.do_client_credentials({'client_id': 'synthetic-client',
                                                'client_secret': 'synthetic-input'})
        self.assertEqual(result, {'status': 401, 'error': 'invalid_grant'})
        client.check_credentials.assert_called_once_with('synthetic-input')
        helper.generate_user_token.assert_not_called()
        self.assert_log_contract(records, failure)
