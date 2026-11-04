"""Offline provider response-body and rendered-chain security regression."""
import json
import traceback
import unittest
from unittest import mock

import requests
from test_auth_providers import providers


def graph_contains_marker(exc, marker):
    """Inspect suppressed chains too, including retained HTTP and JSON data."""
    pending = [exc]
    seen = set()
    while pending:
        current = pending.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        if marker in str(current):
            return True
        if marker in getattr(current, "doc", ""):
            return True
        response = getattr(current, "response", None)
        if response is not None and marker in response.text:
            return True
        pending.extend((current.__context__, current.__cause__))
    return False


def provider_frame_marker(exc, marker):
    """Bounded response-marker check; never traverse provider/self or callers.

    Inspects scalar locals, direct mapping values and real Response body bytes/text.
    This does not inspect credential data reachable through self, caller frames,
    nested arbitrary objects, or establish a general no-secret guarantee.
    """
    def scalar(value):
        if isinstance(value, str):
            return marker in value
        if isinstance(value, bytes):
            return marker.encode("utf-8") in value
        return False

    def held(value):
        if scalar(value):
            return True
        if isinstance(value, dict):
            return any(scalar(item) for item in value.values())
        if isinstance(value, requests.Response):
            return scalar(value.content) or scalar(value.text)
        return False

    count = 0
    detected = False
    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        if frame.f_code.co_filename.endswith("services/providers.py"):
            count += 1
            detected = detected or any(held(value) for name, value in frame.f_locals.items()
                                       if name != "self")
        tb = tb.tb_next
    return count, detected


class TokenErrorSafety(unittest.TestCase):
    def test_provider_frame_detector_controls(self):
        marker = "synthetic-frame-control"
        namespace = {}
        source = ("def trigger(value):\n"
                  "    local_value = value\n"
                  "    raise ValueError('safe')\n")
        exec(compile(source, "synthetic/services/providers.py", "exec"), namespace)
        response = requests.Response()
        response._content = marker.encode("utf-8")
        clean_response = requests.Response()
        clean_response._content = b"safe"
        cases = ((marker, True), (marker.encode("utf-8"), True),
                 ({"expires_in": marker}, True), (response, True),
                 ("safe", False), ({"expires_in": "safe"}, False),
                 (clean_response, False))
        for value, expected in cases:
            count, detected = 0, False
            try:
                namespace["trigger"](value)
            except ValueError as exc:
                count, detected = provider_frame_marker(exc, marker)
            self.assertEqual(count, 1)
            self.assertEqual(detected, expected)
        # Caller locals contain the marker, but are outside the bounded scope.
        try:
            raise ValueError("safe")
        except ValueError as exc:
            count, detected = provider_frame_marker(exc, marker)
        self.assertEqual((count, detected), (0, False))

    def check_provider_frame(self, cls, mode):
        marker = "synthetic-frame-private-" + cls.__name__ + "-" + mode
        response = requests.Response()
        response.url = "https://synthetic.invalid/token"
        response.status_code = 400 if mode == "http" else 200
        if mode == "expiry":
            response._content = json.dumps({"access_token": "synthetic-token",
                                            "expires_in": marker}).encode("utf-8")
        else:
            response._content = marker.encode("utf-8")
        provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                              "username": "user", "password": "password",
                              "client_id": "client", "client_secret": "secret"})
        provider._create_jwt_assertion = mock.Mock(return_value="assertion")
        correct_error = False
        frame_count = 0
        detected = False
        with mock.patch.object(requests, "post", return_value=response) as post:
            try:
                provider._request_token()
            except Exception as exc:
                correct_error = type(exc) is ValueError
                frame_count, detected = provider_frame_marker(exc, marker)
        self.assertTrue(correct_error, "expected exact ValueError")
        self.assertEqual(post.call_count, 1)
        self.assertGreater(frame_count, 0, "provider traceback frame not found")
        self.assertFalse(detected, "response marker retained in provider frame locals")

    def test_provider_frame_http_errors(self):
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_provider_frame(cls, "http")

    def test_provider_frame_invalid_json(self):
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_provider_frame(cls, "invalid_json")

    def test_provider_frame_malformed_expiry(self):
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_provider_frame(cls, "expiry")

    def test_exception_graph_detector_controls(self):
        marker = "synthetic-graph-control"
        response = requests.Response()
        response.status_code = 400
        response._content = marker.encode("utf-8")
        response.url = "https://synthetic.invalid/token"
        http_detected = False
        try:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                raise ValueError("safe") from None
        except ValueError as exc:
            http_detected = graph_contains_marker(exc, marker)
        try:
            try:
                raise json.JSONDecodeError("invalid", marker, 0)
            except json.JSONDecodeError as inner:
                raise ValueError("safe") from inner
        except ValueError as exc:
            json_detected = graph_contains_marker(exc, marker)
        clean = ValueError("safe")
        clean_response = requests.Response()
        clean_response._content = b"safe"
        clean.__context__ = requests.exceptions.HTTPError(response=clean_response)
        clean.__cause__ = json.JSONDecodeError("invalid", "safe", 0)
        self.assertTrue(http_detected)
        self.assertTrue(json_detected)
        self.assertFalse(graph_contains_marker(clean, marker))

    def check_exception_graph(self, cls, mode):
        marker = "synthetic-graph-private-" + cls.__name__ + "-" + mode
        response = requests.Response()
        response.url = "https://synthetic.invalid/token"
        response.status_code = 400 if mode == "http" else 200
        response._content = marker.encode("utf-8")
        if mode == "invalid_json":
            response.json = mock.Mock(side_effect=json.JSONDecodeError("invalid", marker, 0))
        provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                              "username": "user", "password": "password", "client_id": "client"})
        provider._create_jwt_assertion = mock.Mock(return_value="assertion")
        correct_error = False
        leaked = False
        with mock.patch.object(requests, "post", return_value=response) as post:
            try:
                provider._request_token()
            except Exception as exc:
                correct_error = type(exc) is ValueError
                leaked = graph_contains_marker(exc, marker)
        self.assertTrue(correct_error, "expected a ValueError")
        self.assertEqual(post.call_count, 1)
        self.assertFalse(leaked, "response marker retained in exception graph")

    def test_http_error_exception_graph_each_provider(self):
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_exception_graph(cls, "http")

    def test_invalid_json_exception_graph_each_provider(self):
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_exception_graph(cls, "invalid_json")

    def check_case(self, cls, mode):
        marker = "synthetic-private-" + cls.__name__ + "-" + mode
        response = mock.Mock()
        response.text = marker
        if mode.startswith("http"):
            response.raise_for_status.side_effect = requests.exceptions.HTTPError(marker)
        if mode == "http_json":
            response.json.return_value = {"error": marker}
        else:
            response.json.side_effect = json.JSONDecodeError("invalid", marker, 0)
        provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                              "username": "user", "password": "password", "client_id": "client"})
        provider._create_jwt_assertion = mock.Mock(return_value="assertion")
        outcome = None
        exposed_message = exposed_trace = True
        safe_category = False
        with mock.patch.object(requests, "post", return_value=response) as post, \
                mock.patch.object(requests, "request") as business:
            try:
                provider._request_token()
                outcome = "returned"
            except Exception as exc:
                outcome = "raised"
                safe_category = type(exc) is ValueError
                exposed_message = marker in str(exc)
                exposed_trace = marker in "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                expected = "Token request failed" if mode.startswith("http") else "Invalid token response"
                safe_category = safe_category and str(exc) == expected
        self.assertEqual(outcome, "raised")
        self.assertTrue(safe_category, "wrong exception type or category")
        self.assertFalse(exposed_message, "response marker in exception message")
        self.assertFalse(exposed_trace, "response marker in rendered traceback")
        self.assertEqual(post.call_count, 1)
        self.assertEqual(business.call_count, 0)

    def test_http_error_json_each_provider(self):
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_case(cls, "http_json")

    def test_http_error_non_json_each_provider(self):
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                self.check_case(cls, "http_non_json")

    def test_get_jwt_success_with_invalid_json(self):
        self.check_case(providers.GetJWTTokenProvider, "invalid_json")

    def test_malformed_expiry_detector_controls(self):
        marker = "synthetic-expiry-detector-control"

        def exposure(exc):
            return (
                marker in str(exc),
                marker in "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
                graph_contains_marker(exc, marker),
            )

        positive = negative = suppressed = None
        try:
            int(marker)
        except ValueError as exc:
            positive = exposure(exc)
        try:
            raise ValueError("safe")
        except ValueError as exc:
            negative = exposure(exc)
        try:
            try:
                raise ValueError(marker)
            except ValueError:
                raise ValueError("safe") from None
        except ValueError as exc:
            suppressed = exposure(exc)
        self.assertEqual(positive, (True, True, True))
        self.assertEqual(negative, (False, False, False))
        self.assertEqual(suppressed, (False, False, True))

    def test_malformed_expiry_does_not_disclose_response_data(self):
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                marker = "synthetic-expiry-private-" + cls.__name__

                class TokenResponse(dict):
                    expiry_accessed = False

                    def get(self, key, *args):
                        if key == "expires_in":
                            self.expiry_accessed = True
                        return super().get(key, *args)

                data = TokenResponse(access_token="synthetic-valid-token", expires_in=marker)
                response = mock.Mock()
                response.json.return_value = data
                provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                                      "client_id": "client", "client_secret": "secret"})
                provider._create_jwt_assertion = mock.Mock(return_value="assertion")
                correct_error = False
                message_leaked = trace_leaked = graph_leaked = True
                with mock.patch.object(requests, "post", return_value=response) as post, \
                        mock.patch.object(requests, "request") as business:
                    try:
                        provider._request_token()
                    except Exception as exc:
                        correct_error = type(exc) is ValueError
                        message_leaked = marker in str(exc)
                        trace_leaked = marker in "".join(
                            traceback.format_exception(type(exc), exc, exc.__traceback__))
                        graph_leaked = graph_contains_marker(exc, marker)
                self.assertTrue(correct_error, "expected exact ValueError")
                self.assertTrue(data.expiry_accessed, "expiry conversion path not reached")
                self.assertEqual(post.call_count, 1)
                self.assertEqual(business.call_count, 0)
                for surface, leaked in (("message", message_leaked),
                                        ("traceback", trace_leaked),
                                        ("exception graph", graph_leaked)):
                    with self.subTest(surface=surface):
                        self.assertFalse(leaked, "response data disclosed")

    def test_http_200_json_error_surfaces_each_provider(self):
        # Real requests JSON decoding; the only mocked boundary is the POST.
        cases = (
            ("scalar", AttributeError), ("list", AttributeError),
            ("missing_token", ValueError), ("expiry_none", TypeError),
            ("expiry_list", TypeError), ("expiry_dict", TypeError),
            ("expiry_infinity", OverflowError),
        )
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider,
                    providers.ServiceAccountProvider):
            # GetJWTTokenProvider does not parse expires_in.
            provider_cases = cases[:3] if cls is providers.GetJWTTokenProvider else cases
            for case, expected_type in provider_cases:
                with self.subTest(provider=cls.__name__, case=case):
                    marker = "synthetic-json-200-" + cls.__name__ + "-" + case
                    if case == "scalar":
                        data = marker
                    elif case == "list":
                        data = [marker]
                    elif case == "missing_token":
                        data = {"other": marker}
                    else:
                        expiry = {"expiry_none": None, "expiry_list": [],
                                  "expiry_dict": {}, "expiry_infinity": float("inf")}[case]
                        data = {"access_token": marker, "expires_in": expiry}
                    response = requests.Response()
                    response.status_code = 200
                    response.url = "https://synthetic.invalid/token"
                    response.headers["Content-Type"] = "application/json"
                    # A valid JSON number that decodes to positive infinity.
                    body = json.dumps(data).replace("Infinity", "1e999")
                    response._content = body.encode("utf-8")
                    provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                                          "client_id": "client", "client_secret": "secret"})
                    provider._create_jwt_assertion = mock.Mock(return_value="assertion")
                    correct_type = False
                    frame_count = 0
                    frame_leaked = graph_leaked = message_leaked = trace_leaked = False
                    with mock.patch.object(requests, "post", return_value=response) as post:
                        try:
                            provider._request_token()
                        except BaseException as exc:
                            correct_type = type(exc) is expected_type
                            frame_count, frame_leaked = provider_frame_marker(exc, marker)
                            graph_leaked = graph_contains_marker(exc, marker)
                            message_leaked = marker in str(exc)
                            trace_leaked = marker in "".join(traceback.format_exception(
                                type(exc), exc, exc.__traceback__))
                    self.assertEqual(post.call_count, 1, "expected one token POST")
                    self.assertTrue(correct_type, "unexpected exception type or no exception")
                    self.assertGreater(frame_count, 0, "provider traceback frame not found")
                    for surface, leaked in (("frame locals", frame_leaked),
                                            ("exception graph", graph_leaked),
                                            ("message", message_leaked),
                                            ("rendered traceback", trace_leaked)):
                        with self.subTest(surface=surface):
                            self.assertFalse(leaked, "response marker disclosed")

    def test_rendered_trace_detector_controls(self):
        marker = "synthetic-trace-control"
        try:
            try:
                raise RuntimeError(marker)
            except RuntimeError:
                raise ValueError("safe")
        except ValueError as exc:
            detected = marker in "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.assertTrue(detected)
        try:
            raise ValueError("safe")
        except ValueError as exc:
            detected = marker in "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.assertFalse(detected)

    def test_ambient_exception_not_in_provider_rendered_traceback(self):
        # This checks rendered tracebacks only: even `raise ... from None`
        # suppresses display but leaves direct __context__ accessible.
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider,
                    providers.ServiceAccountProvider):
            for mode in ("http", "invalid_json", "scalar", "list", "missing_token"):
                with self.subTest(provider=cls.__name__, mode=mode):
                    marker = "synthetic-ambient-private-" + cls.__name__ + "-" + mode
                    response = requests.Response()
                    response.url = "https://synthetic.invalid/token"
                    response.status_code = 400 if mode == "http" else 200
                    bodies = {"http": b'{"error": "safe"}', "invalid_json": b'not-json',
                              "scalar": b'"safe"', "list": b'[]',
                              "missing_token": b'{"other": "safe"}'}
                    response._content = bodies[mode]
                    provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                                          "username": "user", "password": "password",
                                          "client_id": "client", "client_secret": "secret"})
                    provider._create_jwt_assertion = mock.Mock(return_value="assertion")
                    correct_category = False
                    leaked = False
                    expected = {"http": "Token request failed",
                                "invalid_json": "Invalid token response"}.get(mode)
                    expected_type = AttributeError if mode in ("scalar", "list") else ValueError
                    with mock.patch.object(requests, "post", return_value=response) as post:
                        try:
                            raise RuntimeError(marker)
                        except RuntimeError:
                            try:
                                provider._request_token()
                            except BaseException as exc:
                                correct_category = (type(exc) is expected_type and
                                                    (expected is None or str(exc) == expected))
                                leaked = marker in "".join(traceback.format_exception(
                                    type(exc), exc, exc.__traceback__))
                    self.assertEqual(post.call_count, 1, "expected one token POST")
                    self.assertTrue(correct_category, "wrong exception type or category")
                    self.assertFalse(leaked, "ambient marker in rendered traceback")


    def test_ambient_expiry_surface_sensor_controls(self):
        marker = "synthetic-ambient-expiry-control"

        def surfaces(exc):
            return (marker in str(exc), marker in "".join(traceback.format_exception(
                type(exc), exc, exc.__traceback__)))

        try:
            raise RuntimeError(marker)
        except RuntimeError:
            try:
                raise ValueError("safe")
            except ValueError as exc:
                chained = surfaces(exc)
        try:
            raise ValueError(marker)
        except ValueError as exc:
            message = surfaces(exc)
        try:
            raise RuntimeError(marker)
        except RuntimeError:
            try:
                raise ValueError("safe") from None
            except ValueError as exc:
                suppressed = surfaces(exc)
        self.assertEqual(chained, (False, True))
        self.assertEqual(message, (True, True))
        self.assertEqual(suppressed, (False, False))

    def test_ambient_exception_not_in_invalid_expiry_surfaces(self):
        cases = (("bad_string", "not-an-integer", ValueError),
                 ("none", None, TypeError), ("list", [], TypeError),
                 ("dict", {}, TypeError), ("infinity", float("inf"), OverflowError))
        for cls in (providers.ClientSecretProvider, providers.ServiceAccountProvider):
            for case, expiry, expected_type in cases:
                with self.subTest(provider=cls.__name__, case=case):
                    marker = "synthetic-ambient-expiry-" + cls.__name__ + "-" + case
                    response = requests.Response()
                    response.url = "https://synthetic.invalid/token"
                    response.status_code = 200
                    response.headers["Content-Type"] = "application/json"
                    response._content = json.dumps({
                        "access_token": "synthetic-token", "expires_in": expiry
                    }).replace("Infinity", "1e999").encode("utf-8")
                    provider = cls(None, {"token_uri": response.url,
                                          "client_id": "client", "client_secret": "secret"})
                    provider._create_jwt_assertion = mock.Mock(return_value="assertion")
                    correct_type = False
                    message_leaked = trace_leaked = False
                    with mock.patch.object(requests, "post", return_value=response) as post:
                        try:
                            raise RuntimeError(marker)
                        except RuntimeError:
                            try:
                                provider._request_token()
                            except BaseException as exc:
                                correct_type = type(exc) is expected_type
                                message_leaked = marker in str(exc)
                                trace_leaked = marker in "".join(traceback.format_exception(
                                    type(exc), exc, exc.__traceback__))
                    self.assertEqual(post.call_count, 1, "expected one token POST")
                    self.assertTrue(correct_type, "unexpected exception type or no exception")
                    self.assertFalse(message_leaked, "ambient marker in exception message")
                    self.assertFalse(trace_leaked, "ambient marker in rendered traceback")


    def test_transport_rendered_detector_controls(self):
        transport_marker = "synthetic-transport-control"
        ambient_marker = "synthetic-transport-ambient-control"

        def surfaces(exc):
            rendered = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            return tuple((marker in str(exc), marker in rendered)
                         for marker in (transport_marker, ambient_marker))

        try:
            raise RuntimeError(ambient_marker)
        except RuntimeError:
            try:
                raise requests.exceptions.Timeout(transport_marker)
            except requests.exceptions.Timeout as exc:
                positive = surfaces(exc)
        try:
            raise ValueError("safe")
        except ValueError as exc:
            clean = surfaces(exc)
        self.assertEqual(positive, ((True, True), (False, True)))
        self.assertEqual(clean, ((False, False), (False, False)))

    def test_transport_errors_do_not_disclose_rendered_markers(self):
        # Direct __context__ and frame locals are outside this slice's scope.
        cases = ((providers.GetJWTTokenProvider, "Token endpoint timeout",
                  "Token to connect to token endpoint"),
                 (providers.ClientSecretProvider, "OIDC token endpoint timeout",
                  "Unable to connect to token endpoint"),
                 (providers.ServiceAccountProvider, "OIDC token endpoint timeout",
                  "Unable to connect to token endpoint"))
        for cls, timeout_message, connection_message in cases:
            for error_type, expected in ((requests.exceptions.Timeout, timeout_message),
                                         (requests.exceptions.ConnectionError, connection_message)):
                for ambient in (False, True):
                    with self.subTest(provider=cls.__name__, error=error_type.__name__, ambient=ambient):
                        transport_marker = "synthetic-transport-private"
                        ambient_marker = "synthetic-transport-ambient-private"
                        provider = cls(None, {"token_uri": "https://synthetic.invalid/token",
                                              "username": "user", "password": "password",
                                              "client_id": "client", "client_secret": "secret"})
                        provider._create_jwt_assertion = mock.Mock(return_value="assertion")
                        correct_type = correct_message = False
                        exposures = (True, True, True, True)
                        with mock.patch.object(requests, "post", side_effect=error_type(transport_marker)) as post:
                            def invoke():
                                try:
                                    provider._request_token()
                                except BaseException as exc:
                                    rendered = "".join(traceback.format_exception(
                                        type(exc), exc, exc.__traceback__))
                                    return (type(exc) is ValueError, str(exc) == expected,
                                            tuple(marker in surface for marker in
                                                  (transport_marker, ambient_marker)
                                                  for surface in (str(exc), rendered)))
                                return False, False, (True, True, True, True)

                            if ambient:
                                try:
                                    raise RuntimeError(ambient_marker)
                                except RuntimeError:
                                    correct_type, correct_message, exposures = invoke()
                            else:
                                correct_type, correct_message, exposures = invoke()
                        self.assertEqual(post.call_count, 1, "expected one token POST")
                        self.assertTrue(correct_type, "expected exact ValueError")
                        self.assertTrue(correct_message, "unexpected preexisting message")
                        for surface, leaked in zip(("transport message", "transport traceback",
                                                    "ambient message", "ambient traceback"), exposures):
                            with self.subTest(surface=surface):
                                self.assertFalse(leaked, "marker disclosed in rendered output")


    def test_missing_uri_rendered_trace_detector_controls(self):
        marker = "synthetic-missing-uri-control"

        def detected(exc):
            return marker in "".join(traceback.format_exception(
                type(exc), exc, exc.__traceback__))

        try:
            raise RuntimeError(marker)
        except RuntimeError:
            try:
                raise ValueError("token_uri is required")
            except ValueError as exc:
                positive = detected(exc)
        try:
            raise ValueError("token_uri is required")
        except ValueError as exc:
            clean = detected(exc)
        self.assertTrue(positive, "chained marker not detected")
        self.assertFalse(clean, "clean traceback falsely detected")

    def test_missing_uri_does_not_render_ambient_exception(self):
        # Only rendered traceback is in scope, not the retained exception graph.
        for cls in (providers.GetJWTTokenProvider, providers.ClientSecretProvider,
                    providers.ServiceAccountProvider):
            with self.subTest(provider=cls.__name__):
                marker = "synthetic-missing-uri-ambient-" + cls.__name__
                provider = cls(None, {"username": "user", "password": "password",
                                      "client_id": "client", "client_secret": "secret"})
                correct_type = correct_message = False
                leaked = True
                with mock.patch.object(requests, "post") as post:
                    try:
                        raise RuntimeError(marker)
                    except RuntimeError:
                        try:
                            provider._request_token()
                        except BaseException as exc:
                            correct_type = type(exc) is ValueError
                            correct_message = str(exc) == "token_uri is required"
                            leaked = marker in "".join(traceback.format_exception(
                                type(exc), exc, exc.__traceback__))
                self.assertEqual(post.call_count, 0, "unexpected token POST")
                self.assertTrue(correct_type, "expected exact ValueError")
                self.assertTrue(correct_message, "unexpected validation message")
                self.assertFalse(leaked, "ambient marker in rendered traceback")


if __name__ == "__main__":
    unittest.main()
