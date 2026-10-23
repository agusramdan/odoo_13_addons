"""Standalone: python -m unittest discover -s amr_resource/tests -p test_transport_unit.py.

Load the file directly so discovery never imports the Odoo addon package.
Only DNS/socket/TLS boundaries (and the clock) are replaced; HTTP is real stdlib.
"""
import importlib.util
from pathlib import Path
import socket
import ssl
import threading
import time
import traceback
import unittest
from typing import Callable, Optional
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    'amr_transport_standalone', str(Path(__file__).resolve().parents[1] / 'transport.py'))
assert SPEC is not None and SPEC.loader is not None
transport = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transport)

PUBLIC = '93.184.216.34'
URL = 'https://issuer.example/json?key=secret'


def answer(ip=PUBLIC):
    family = socket.AF_INET6 if ':' in ip else socket.AF_INET
    address = (ip, 443, 0, 0) if family == socket.AF_INET6 else (ip, 443)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', address)


def response(body=b'{"ok": true}', status=200, headers=()):
    lines = ['HTTP/1.1 %s Result' % status]
    if not any(name.lower() in ('content-length', 'transfer-encoding')
               for name, value in headers):
        lines.append('Content-Length: %s' % len(body))
    lines.extend('%s: %s' % item for item in headers)
    return ('\r\n'.join(lines) + '\r\n\r\n').encode('ascii') + body


class WireSocket:
    def __init__(self, payload):
        self.payload = payload
        self.sent = bytearray()
        self.addresses = []
        self.timeouts = []
        self.closed = False
        self.on_connect = None  # type: Optional[Callable[[], None]]
        self.on_read = None  # type: Optional[Callable[[], None]]
        self.read_size = None  # type: Optional[int]

    def settimeout(self, value):
        self.timeouts.append(value)

    def connect(self, address):
        self.addresses.append(address)
        if self.on_connect:
            self.on_connect()

    def sendall(self, data):
        self.sent.extend(data)

    def recv_into(self, buffer):
        if self.on_read:
            self.on_read()
        size = min(len(buffer), len(self.payload))
        if self.read_size is not None:
            size = min(size, self.read_size)
        buffer[:size] = self.payload[:size]
        self.payload = self.payload[size:]
        return size

    def close(self):
        self.closed = True


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.wire = WireSocket(response())
        self.dns = self.enter_patch('socket.getaddrinfo', return_value=[answer()])
        self.factory = self.enter_patch('socket.socket', return_value=self.wire)
        self.tls = self.enter_patch('ssl.SSLContext.wrap_socket', return_value=self.wire)

    def enter_patch(self, name, **kwargs):
        patcher = patch(name, **kwargs)
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def rejected(self, url: Optional[str] = URL, **kwargs):
        with self.assertRaises(transport.TransportError) as caught:
            transport.fetch_json(url, **kwargs)
        error = caught.exception
        self.assertEqual(str(error), 'HTTPS JSON request failed')
        self.assertTrue(error.__suppress_context__)
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        formatted = ''.join(traceback.format_exception_only(type(error), error))
        self.assertNotIn('secret', formatted)
        self.assertNotIn('issuer.example', formatted)
        return error

    def test_get_uses_real_http_pinned_socket_and_hostname_tls(self):
        self.assertEqual(transport.fetch_json(URL), {'ok': True})
        self.dns.assert_called_once_with('issuer.example', 443, socket.AF_UNSPEC,
                                         socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.factory.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM,
                                             socket.IPPROTO_TCP)
        self.assertEqual(self.wire.addresses, [(PUBLIC, 443)])
        self.tls.assert_called_once_with(self.wire, server_hostname='issuer.example')
        sent = bytes(self.wire.sent)
        self.assertTrue(sent.startswith(b'GET /json?key=secret HTTP/1.1\r\n'))
        for header in (b'Host: issuer.example\r\n', b'Accept-Encoding: identity\r\n',
                       b'Cache-Control: no-store, no-cache\r\n', b'Pragma: no-cache\r\n',
                       b'Connection: close\r\n'):
            self.assertIn(header, sent)
        self.assertTrue(self.wire.closed)
        self.assertTrue(all(0 < timeout <= 5 for timeout in self.wire.timeouts))
        self.assertLessEqual(self.wire.timeouts[0], 3)

    def test_default_context_verifies_certificate_and_hostname(self):
        contexts = []
        original = ssl.create_default_context

        def context():
            value = original()
            contexts.append(value)
            return value

        self.enter_patch('ssl.create_default_context', side_effect=context)
        transport.fetch_json(URL)
        self.assertEqual(contexts[0].verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(contexts[0].check_hostname)

    def test_form_post_credentials_only_at_original_endpoint(self):
        transport.fetch_json(URL, data={'token': 'a+b &', 'scope': ['x', 'y']},
                             headers={'Authorization': 'Basic synthetic-secret'})
        sent = bytes(self.wire.sent)
        self.assertTrue(sent.startswith(b'POST '))
        self.assertIn(b'Content-Type: application/x-www-form-urlencoded\r\n', sent)
        self.assertIn(b'Authorization: Basic synthetic-secret\r\n', sent)
        self.assertTrue(sent.endswith(b'token=a%2Bb+%26&scope=x&scope=y'))

    def test_empty_form_is_post(self):
        transport.fetch_json(URL, data={})
        self.assertTrue(bytes(self.wire.sent).startswith(b'POST '))
        self.assertIn(b'Content-Length: 0\r\n', self.wire.sent)

    def test_no_cross_request_cache_or_credentials(self):
        transport.fetch_json(URL, headers={'Authorization': 'Bearer secret'})
        second = WireSocket(response(b'{"ok": false}'))
        self.factory.return_value = second
        self.tls.return_value = second
        self.assertEqual(transport.fetch_json(URL), {'ok': False})
        self.assertEqual(self.dns.call_count, 2)
        self.assertNotIn(b'Authorization:', second.sent)

    def test_reject_malformed_or_unsafe_urls_before_dns(self):
        for url in ('http://issuer.example', 'https://u:secret@issuer.example',
                    'https://issuer.example:444/', 'https://issuer.example/#',
                    'https://issuer.example/#secret', 'https://issuer.example:/',
                    'https://[2606:4700:4700::1111]evil/',
                    'https://issuer.example/\r\nX: secret',
                    ' https://issuer.example', 'https://issuer.example\\@evil.test',
                    'https://bad_host/', 'https://%31%32%37.0.0.1/',
                    'https://[fe80::1%25eth0]/', None):
            with self.subTest(url=url):
                self.rejected(url)
        self.dns.assert_not_called()
        self.factory.assert_not_called()

    def test_reject_nonpublic_literals_before_dns(self):
        for ip in ('127.0.0.1', '10.1.2.3', '172.16.0.1', '192.168.1.1',
                   '169.254.169.254', '100.64.0.1', '0.0.0.0', '224.0.0.1',
                   '240.0.0.1', '192.0.2.1', '192.0.0.8', '192.88.99.1',
                   '198.18.0.1', '198.51.100.1', '203.0.113.1', '255.255.255.255',
                   '::', '::1', 'fc00::1', 'fe80::1', 'ff02::1', '2001:db8::1',
                   '::ffff:127.0.0.1', '64:ff9b::7f00:1', '2002:7f00:1::',
                   '3fff::1'):
            with self.subTest(ip=ip):
                host = '[%s]' % ip if ':' in ip else ip
                self.rejected('https://%s/' % host)
        self.dns.assert_not_called()
        self.factory.assert_not_called()

    def test_public_literals_use_no_dns(self):
        for ip in (PUBLIC, '2606:4700:4700::1111'):
            with self.subTest(ip=ip):
                self.wire.payload = response()
                self.wire.closed = False
                host = '[%s]' % ip if ':' in ip else ip
                self.assertEqual(transport.fetch_json('https://%s:443/' % host), {'ok': True})
                self.assertEqual(self.wire.addresses[-1][0], ip)
                self.assertEqual(self.tls.call_args[1]['server_hostname'], ip)
        self.dns.assert_not_called()

    def test_dns_all_answers_checked_before_connect(self):
        for ip in ('127.0.0.1', '10.0.0.1', '169.254.1.1', '::1', 'ff02::1',
                   '::ffff:10.0.0.1', '192.0.2.1'):
            with self.subTest(ip=ip):
                self.dns.return_value = [answer(), answer(ip)]
                self.rejected()
        self.factory.assert_not_called()

    def test_rebinding_cannot_resolve_during_connect(self):
        self.dns.side_effect = [[answer()], [answer('127.0.0.1')]]
        transport.fetch_json(URL)
        self.assertEqual(self.dns.call_count, 1)
        self.assertEqual(self.wire.addresses, [(PUBLIC, 443)])

    def test_empty_and_failed_dns_are_sanitized(self):
        self.dns.return_value = []
        self.rejected()
        self.dns.side_effect = socket.gaierror('secret from issuer.example')
        self.rejected()
        self.factory.assert_not_called()

    def test_dns_is_bounded_even_when_resolver_blocks(self):
        entered = threading.Event()
        release = threading.Event()
        finished = threading.Event()

        def lookup(*args):
            entered.set()
            try:
                release.wait(2)
                return [answer()]
            finally:
                finished.set()

        self.dns.side_effect = lookup
        with patch.object(transport, 'CONNECT_TIMEOUT', 0.04):
            started = time.monotonic()
            try:
                self.rejected()
                elapsed = time.monotonic() - started
                self.assertTrue(entered.is_set())
                self.assertLess(elapsed, 1)
                self.factory.assert_not_called()
            finally:
                release.set()
                self.assertTrue(finished.wait(1))

    def test_dns_worker_limit_fails_closed(self):
        slots = transport._DNS_SLOTS
        for _ in range(8):
            self.assertTrue(slots.acquire(False))
        try:
            self.rejected()
            self.dns.assert_not_called()
        finally:
            for _ in range(8):
                slots.release()

    def test_no_retry_on_connect_failure(self):
        self.dns.return_value = [answer(), answer('1.1.1.1')]
        self.wire.on_connect = lambda: (_ for _ in ()).throw(OSError('secret'))
        self.rejected()
        self.assertEqual(self.wire.addresses, [(PUBLIC, 443)])
        self.assertEqual(self.factory.call_count, 1)
        self.assertTrue(self.wire.closed)

    def test_tls_failure_never_sends_credentials(self):
        self.tls.side_effect = ssl.SSLError('secret certificate failure')
        self.rejected(headers={'Authorization': 'Bearer secret'})
        self.assertEqual(self.wire.sent, b'')
        self.assertTrue(self.wire.closed)

    def test_tls_connect_budget_includes_dns(self):
        clock = [0.0]
        self.enter_patch('time.monotonic', side_effect=lambda: clock[0])

        def lookup(*args):
            clock[0] = 2.5
            return [answer()]

        def handshake(*args, **kwargs):
            clock[0] = 3.01
            return self.wire

        self.dns.side_effect = lookup
        self.tls.side_effect = handshake
        self.rejected(headers={'Authorization': 'Bearer secret'})
        self.assertEqual(self.wire.timeouts[:2], [0.5, 0.5])
        self.assertEqual(self.wire.sent, b'')
        self.assertTrue(self.wire.closed)

    def test_read_timeout_is_five_seconds(self):
        self.enter_patch('time.monotonic', return_value=0.0)
        self.wire.on_read = lambda: (_ for _ in ()).throw(socket.timeout('secret'))
        self.rejected()
        self.assertEqual(self.wire.timeouts[-1], 5)
        self.assertTrue(self.wire.closed)

    def test_upload_timeout_is_sanitized_without_retry(self):
        def fail(data):
            raise socket.timeout('secret upload')

        with patch.object(self.wire, 'sendall', side_effect=fail):
            self.rejected(data={'token': 'secret'})
        self.assertEqual(self.factory.call_count, 1)
        self.assertTrue(self.wire.closed)

    def test_close_failure_does_not_leak_remote_exception(self):
        self.wire.payload = response(status=401)
        with patch.object(self.wire, 'close', side_effect=OSError('secret close')):
            self.rejected(headers={'Authorization': 'Bearer secret'})

    def test_total_deadline_bounds_slow_headers_and_body(self):
        for chunk in (1, 80):
            with self.subTest(chunk=chunk):
                self.wire.payload = response(b' ' * 1000 + b'{}')
                self.wire.closed = False
                self.wire.read_size = chunk
                clock = [0.0]

                def tick():
                    clock[0] += 1.0

                self.wire.on_read = tick
                with patch('time.monotonic', side_effect=lambda: clock[0]):
                    self.rejected()
                self.assertEqual(clock[0], 8.0)
                self.assertEqual(self.wire.timeouts[-1], 1.0)
                self.assertTrue(self.wire.closed)

    def test_redirects_and_http_errors_do_not_follow_or_retry(self):
        for status in (301, 302, 303, 307, 308, 400, 401, 429, 500, 503):
            with self.subTest(status=status):
                self.wire.payload = response(status=status, headers=(
                    ('Location', 'https://other.example/secret'),))
                self.factory.reset_mock()
                self.dns.reset_mock()
                self.rejected(data={'token': 'secret'},
                              headers={'Authorization': 'Bearer secret'})
                self.assertEqual(self.factory.call_count, 1)
                self.assertEqual(self.dns.call_count, 1)
                self.assertEqual(self.dns.call_args[0][0], 'issuer.example')

    def test_caller_cannot_override_host_framing_cache_or_inject_headers(self):
        for headers in ({'Host': 'other.example'}, {'Proxy-Authorization': 'secret'},
                        {'Content-Length': '0'}, {'Transfer-Encoding': 'chunked'},
                        {'Cache-Control': 'public'}, {'Accept-Encoding': 'gzip'},
                        {'Content-Type': 'text/plain'}, {'Connection': 'keep-alive'},
                        {'Authorization': 'secret\r\nHost: other.example'},
                        {'Bad\r\nName': 'secret'}, {'Authorization': 1},
                        {'Authorization': 'a', 'authorization': 'b'}):
            with self.subTest(headers=headers):
                self.rejected(headers=headers)
        self.dns.assert_not_called()
        self.factory.assert_not_called()

    def test_size_limit_content_length_and_streamed_body(self):
        limit = transport.MAX_RESPONSE_BYTES
        exact = b'"' + b'a' * (limit - 2) + b'"'
        self.wire.payload = response(exact)
        self.assertEqual(len(transport.fetch_json(URL)), limit - 2)
        for payload in (
                response(exact + b' ', headers=(('Content-Length', str(limit + 1)),)),
                b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n' + exact + b' ',
                b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n' +
                ('%x\r\n' % (limit + 1)).encode() + exact + b' \r\n0\r\n\r\n'):
            self.wire.payload = payload
            self.rejected()

    def test_chunked_success_uses_real_http_parser(self):
        self.wire.payload = (b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
                             b'2\r\n{}\r\n0\r\n\r\n')
        self.assertEqual(transport.fetch_json(URL), {})

    def test_invalid_json_encoding_compression_and_truncation(self):
        for payload in (response(b'not-json-secret'), response(b'\xff'),
                        response(b'{}', headers=(('Content-Encoding', 'gzip'),)),
                        response(b'{}', headers=(('Content-Length', '20'),)),
                        response(b'{}', headers=(('Content-Length', '-1'),)),
                        response(b'{}', headers=(('Content-Length', 'bad'),)),
                        b'not-http-secret\r\n\r\n'):
            with self.subTest(payload=payload[:80]):
                self.wire.payload = payload
                self.rejected()
                self.assertTrue(self.wire.closed)

    def test_no_environment_proxy(self):
        with patch.dict('os.environ', {'HTTPS_PROXY': 'http://127.0.0.1:1234',
                                       'https_proxy': 'http://127.0.0.1:1234'}):
            transport.fetch_json(URL)
        self.assertEqual(self.wire.addresses, [(PUBLIC, 443)])
        self.assertNotIn(b'CONNECT ', self.wire.sent)


if __name__ == '__main__':
    unittest.main()
