"""Uncached, fail-closed HTTPS JSON transport (independent of Odoo)."""
import http.client
import io
import ipaddress
import json
import queue
import re
import socket
import ssl
import threading
import time
from urllib.parse import urlencode, urlsplit


CONNECT_TIMEOUT = 3.0
READ_TIMEOUT = 5.0
TOTAL_TIMEOUT = 8.0
MAX_RESPONSE_BYTES = 1024 * 1024
# A timed-out libc resolver cannot be cancelled; bound outstanding workers.
_DNS_SLOTS = threading.BoundedSemaphore(8)
_PREFLIGHT_TOKEN = object()


class TransportError(Exception):
    """Transport failed; deliberately contains no remote or caller data."""


def _remaining(deadline, limit):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError()
    return min(limit, remaining)


def _public(address):
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        return _public(str(ip.ipv4_mapped))
    # Older runtime address tables miss newer special-purpose allocations.
    if isinstance(ip, ipaddress.IPv4Address) and any(ip in network for network in (
            ipaddress.ip_network('192.0.0.0/24'),
            ipaddress.ip_network('192.88.99.0/24'))):
        return False
    # Only native IPv6 global unicast; no translation or tunnel destinations.
    if isinstance(ip, ipaddress.IPv6Address) and (
            ip not in ipaddress.ip_network('2000::/3') or ip.sixtofour or
            ip.teredo or ip in ipaddress.ip_network('3fff::/20')):
        return False
    return (ip.is_global and not (ip.is_private or ip.is_loopback or
            ip.is_link_local or ip.is_multicast or ip.is_reserved or
            ip.is_unspecified))


def _endpoint(url):
    if not isinstance(url, str) or not url or any(
            ord(c) <= 32 or ord(c) >= 127 for c in url):
        raise ValueError()
    if '#' in url or '\\' in url:
        raise ValueError()
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.netloc or
            '@' in parsed.netloc or parsed.port not in (None, 443)):
        raise ValueError()
    host = parsed.hostname
    if not host or '%' in host or parsed.netloc.endswith(':'):
        raise ValueError()
    authority = '[%s]' % host if ':' in host else host
    if parsed.netloc.lower() not in (authority, authority + ':443'):
        raise ValueError()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if (len(host) > 253 or not all(
                re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
                for label in host.rstrip('.').split('.'))):
            raise ValueError()
    else:
        if not _public(host):
            raise ValueError()
    target = parsed.path or '/'
    if parsed.query:
        target += '?' + parsed.query
    return host, target


def _resolve(host, deadline):
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if not _DNS_SLOTS.acquire(False):
            raise TimeoutError()
        result = queue.Queue(maxsize=1)

        def lookup():
            try:
                result.put((True, socket.getaddrinfo(
                    host, 443, socket.AF_UNSPEC, socket.SOCK_STREAM,
                    socket.IPPROTO_TCP)))
            except Exception:
                result.put((False, None))
            finally:
                _DNS_SLOTS.release()

        try:
            threading.Thread(target=lookup, daemon=True).start()
        except Exception:
            _DNS_SLOTS.release()
            raise
        ok, addresses = result.get(timeout=_remaining(deadline, CONNECT_TIMEOUT))
        if not ok:
            raise OSError()
    else:
        family = socket.AF_INET if ip.version == 4 else socket.AF_INET6
        addresses = [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '',
                      (str(ip), 443) if ip.version == 4 else (str(ip), 443, 0, 0))]
    if not addresses:
        raise ValueError()
    for family, kind, proto, _, address in addresses:
        if (family not in (socket.AF_INET, socket.AF_INET6) or
                kind != socket.SOCK_STREAM or proto != socket.IPPROTO_TCP or
                address[1] != 443 or not _public(address[0]) or
                (family == socket.AF_INET6 and address[2:] != (0, 0))):
            raise ValueError()
    _remaining(deadline, CONNECT_TIMEOUT)
    # No retries or secondary-address fallback.
    return addresses[0]


class _Reader(io.RawIOBase):
    def __init__(self, sock, deadline):
        super().__init__()
        self.sock = sock
        self.deadline = deadline

    def readable(self):
        return True

    def readinto(self, buffer):
        self.sock.settimeout(_remaining(self.deadline, READ_TIMEOUT))
        count = self.sock.recv_into(buffer)
        _remaining(self.deadline, READ_TIMEOUT)
        return count


class _DeadlineSocket:
    def __init__(self, sock, deadline):
        self.sock = sock
        self.deadline = deadline

    def sendall(self, data):
        self.sock.settimeout(_remaining(self.deadline, READ_TIMEOUT))
        self.sock.sendall(data)
        _remaining(self.deadline, READ_TIMEOUT)

    def makefile(self, mode):
        if mode != 'rb':
            raise ValueError()
        return io.BufferedReader(_Reader(self.sock, self.deadline))

    def close(self):
        self.sock.close()


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, connect_deadline, deadline):
        self._tls_context = ssl.create_default_context()
        super().__init__(host, port=443, timeout=CONNECT_TIMEOUT,
                         context=self._tls_context)
        self._address = address
        self._connect_deadline = connect_deadline
        self._deadline = deadline

    def connect(self):
        family, kind, proto, _, address = self._address
        raw = socket.socket(family, kind, proto)
        secured = None
        try:
            raw.settimeout(_remaining(self._connect_deadline, CONNECT_TIMEOUT))
            raw.connect(address)
            raw.settimeout(_remaining(self._connect_deadline, CONNECT_TIMEOUT))
            secured = self._tls_context.wrap_socket(raw, server_hostname=self.host)
            _remaining(self._connect_deadline, CONNECT_TIMEOUT)
            self.sock = _DeadlineSocket(secured, self._deadline)
        except Exception:
            (secured or raw).close()
            raise


def preflight_endpoint(url):
    """Validate and resolve an endpoint before its caller releases credentials."""
    try:
        started = time.monotonic()
        host, target = _endpoint(url)
        address = _resolve(host, started + CONNECT_TIMEOUT)
        return url, host, target, address, _PREFLIGHT_TOKEN
    except Exception:
        raise TransportError('HTTPS JSON request failed') from None


def _headers(headers, body):
    result = {}
    # Do not let caller headers alter routing, framing, or no-cache policy.
    forbidden = {'host', 'connection', 'content-length', 'transfer-encoding',
                 'content-type', 'accept-encoding', 'cache-control', 'pragma',
                 'proxy-authorization', 'proxy-connection', 'upgrade', 'trailer',
                 'expect', 'te'}
    for name, value in (headers or {}).items():
        if (not isinstance(name, str) or
                not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name) or
                name.lower() in forbidden or not isinstance(value, str) or
                any(ord(c) < 32 or ord(c) > 126 for c in value)):
            raise ValueError()
        if name.lower() in {key.lower() for key in result}:
            raise ValueError()
        result[name] = value
    result.update({'Accept': 'application/json', 'Accept-Encoding': 'identity',
                   'Cache-Control': 'no-store, no-cache', 'Pragma': 'no-cache',
                   'Connection': 'close'})
    if body is not None:
        result['Content-Type'] = 'application/x-www-form-urlencoded'
    return result


def fetch_json(url, data=None, headers=None, preflight=None):
    """GET JSON, or POST form data, with no cache, redirect, proxy or retry.

    Authorization headers apply only to this exact endpoint; the caller must
    select a trusted endpoint before supplying any credentials.
    """
    connection = None
    response = None
    try:
        started = time.monotonic()
        deadline = started + TOTAL_TIMEOUT
        connect_deadline = started + CONNECT_TIMEOUT
        address = None
        if preflight is None:
            host, target = _endpoint(url)
        else:
            if (not isinstance(preflight, tuple) or len(preflight) != 5
                    or preflight[0] != url or preflight[4] is not _PREFLIGHT_TOKEN):
                raise ValueError()
            _, host, target, address, _ = preflight
        body = None if data is None else urlencode(data, doseq=True).encode('ascii')
        request_headers = _headers(headers, body)
        if address is None:
            address = _resolve(host, connect_deadline)
        connection = _PinnedHTTPSConnection(host, address, connect_deadline, deadline)
        connection.request('GET' if data is None else 'POST', target,
                           body=body, headers=request_headers)
        response = connection.getresponse()
        if not 200 <= response.status < 300:
            raise ValueError()
        if response.getheader('Content-Encoding', 'identity').lower() != 'identity':
            raise ValueError()
        length = response.getheader('Content-Length')
        if length is not None and (not re.fullmatch(r'[0-9]+', length) or
                                   int(length) > MAX_RESPONSE_BYTES):
            raise ValueError()
        content = response.read(MAX_RESPONSE_BYTES + 1)
        if (len(content) > MAX_RESPONSE_BYTES or
                (length is not None and len(content) != int(length))):
            raise ValueError()
        value = json.loads(content.decode('utf-8'))
        _remaining(deadline, TOTAL_TIMEOUT)
        return value
    except Exception:
        pass
    finally:
        for resource in (response, connection):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    pass
    # Raise outside the handler so even __context__ cannot retain remote errors.
    raise TransportError('HTTPS JSON request failed') from None
