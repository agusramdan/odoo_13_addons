# -*- coding: utf-8 -*-
import importlib.util
import os
import unittest


MODULE_PATH = os.path.join(os.path.dirname(__file__), '..', 'services', 'request_errors.py')
SPEC = importlib.util.spec_from_file_location('request_errors', MODULE_PATH)
request_errors = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(request_errors)


class TestRequestExceptionText(unittest.TestCase):
    def test_connection_error_without_response_is_safe(self):
        error = ConnectionError('connection failed')
        self.assertEqual(request_errors.request_exception_text(error), 'connection failed')

    def test_response_body_and_exception_text_are_preserved(self):
        class Response(object):
            text = 'server error'

        class RequestError(Exception):
            response = Response()

        self.assertEqual(
            request_errors.request_exception_text(RequestError('bad status')),
            'server errorbad status',
        )

    def test_broken_response_text_accessor_does_not_mask_error(self):
        class Response(object):
            @property
            def text(self):
                raise RuntimeError('unavailable')

        class RequestError(Exception):
            response = Response()

        self.assertEqual(
            request_errors.request_exception_text(RequestError('network error')),
            'network error',
        )


if __name__ == '__main__':
    unittest.main()
