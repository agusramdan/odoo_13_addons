import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


def load_transport():
    path = Path(__file__).parents[2] / 'transport.py'
    spec = importlib.util.spec_from_file_location('amr_resource.transport_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTransportValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transport = load_transport()

    def test_endpoint_validates_https_authority_and_builds_target(self):
        self.assertEqual(self.transport._endpoint('https://example.test/path?q=1'),
                         ('example.test', '/path?q=1'))
        self.assertEqual(self.transport._endpoint('https://example.test'),
                         ('example.test', '/'))
        for value in ('http://example.test', 'https://u@example.test',
                      'https://example.test:444', 'https://127.0.0.1/x',
                      'https://example.test#frag', 'https://example.test\\x',
                      'https://bad host', 'https://example.test:', 'https://[::1]/'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.transport._endpoint(value)

    def test_public_address_rejects_special_ranges_and_accepts_global(self):
        for address in ('127.0.0.1', '10.0.0.1', '192.0.0.1', '224.0.0.1', '::1',
                        '::ffff:127.0.0.1', '2001:db8::1', '2002:0808:0808::'):
            with self.subTest(address=address):
                self.assertFalse(self.transport._public(address))
        self.assertTrue(self.transport._public('8.8.8.8'))
        self.assertTrue(self.transport._public('2606:4700:4700::1111'))

    def test_headers_block_framing_and_duplicate_names(self):
        headers = self.transport._headers({'X-Test': 'ok'}, b'data')
        self.assertEqual(headers['X-Test'], 'ok')
        self.assertEqual(headers['Content-Type'], 'application/x-www-form-urlencoded')
        self.assertEqual(headers['Cache-Control'], 'no-store, no-cache')
        for supplied in ({'Host': 'evil'}, {'bad name': 'x'}, {'X': 'a\nb'},
                         {'X-Test': 'a', 'x-test': 'b'}):
            with self.subTest(supplied=supplied), self.assertRaises(ValueError):
                self.transport._headers(supplied, None)

    def test_resolve_rejects_non_public_dns_answers(self):
        addresses = [(self.transport.socket.AF_INET, self.transport.socket.SOCK_STREAM,
                      self.transport.socket.IPPROTO_TCP, '', ('127.0.0.1', 443))]
        with patch.object(self.transport.socket, 'getaddrinfo', return_value=addresses):
            with self.assertRaises(ValueError):
                self.transport._resolve('example.test', self.transport.time.monotonic() + 2)

    def test_preflight_and_fetch_fail_closed_without_network(self):
        with self.assertRaises(self.transport.TransportError):
            self.transport.preflight_endpoint('http://example.test')
        with self.assertRaises(self.transport.TransportError):
            self.transport.fetch_json('http://example.test')
        with self.assertRaises(self.transport.TransportError):
            self.transport.fetch_json('https://example.test', preflight=('bad',))
        with patch.object(self.transport, '_resolve', return_value='8.8.8.8'):
            valid = self.transport.preflight_endpoint('https://example.test')
        with patch.object(self.transport, '_PinnedHTTPSConnection') as connection:
            for invalid in (valid[:-1] + (object(),), ('https://other.test',) + valid[1:]):
                with self.assertRaises(self.transport.TransportError):
                    self.transport.fetch_json('https://example.test', preflight=invalid)
            connection.assert_not_called()
            response = connection.return_value.getresponse.return_value
            response.status = 200
            response.getheader.side_effect = lambda key, default=None: default
            response.read.return_value = b'{"ok":true}'
            self.assertEqual(self.transport.fetch_json('https://example.test', preflight=valid), {'ok': True})
            connection.assert_called_once()
            self.assertEqual(connection.call_args[0][:2], ('example.test', '8.8.8.8'))


if __name__ == '__main__':
    unittest.main()
