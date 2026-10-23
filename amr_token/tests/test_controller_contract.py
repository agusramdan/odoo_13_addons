"""P-07 offline HTTP/controller response and route contract with Odoo/Werkzeug doubles."""
import json
import unittest
from unittest import mock

if __package__:
    from .support import ADDON, StubHTTPException, load_controller_module
else:
    from support import ADDON, StubHTTPException, load_controller_module


class TestControllerContract(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ADDON / "controllers" / "main.py").is_file(), "candidate OIDC controller is missing")
        self.module = load_controller_module()
        self.controller = object.__new__(self.module.ControllerToken)

    def _require(self, method):
        self.assertTrue(callable(getattr(self.module.ControllerToken, method, None)), f"candidate controller method {method} is missing")

    def _json(self, response):
        return json.loads(response.get_data(as_text=True))

    def test_json_response_helpers_and_unknown_fallback(self):
        self._require("make_response")
        response = self.module.ControllerToken.make_response(201, result="ok")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers["Content-Type"],
            "application/json; charset=utf-8",
        )
        self.assertEqual(self._json(response), {"result": "ok"})

        empty = self.module.ControllerToken.make_response(500)
        self.assertEqual(self._json(empty), {
            "error": "unknown_error", "error_description": "An unknown error occurred.",
        })

    def test_valid_and_invalid_response_shapes(self):
        self._require("valid_response")
        self._require("invalid_response")
        valid = self.module.ControllerToken.valid_response(202, {"active": True})
        self.assertEqual(valid.status_code, 202)
        self.assertEqual(valid.headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(self._json(valid), {"active": True})

        invalid = self.controller.invalid_response(401, "invalid_token", "not valid")
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(self._json(invalid), {"error": "invalid_token", "error_description": "not valid"})

    def test_exception_handler_preserves_http_exception_and_maps_other_errors(self):
        self._require("handle_exception")
        with self.assertLogs(self.module._logger, level="ERROR"):
            mapped = self.module.ControllerToken.handle_exception(
                ValueError("synthetic failure"), 401, "invalid_request",
            )
        self.assertEqual(mapped.status_code, 401)
        mapped_json = self._json(mapped)
        self.assertEqual(mapped_json, {
            "success": False,
            "error": "invalid_request",
            "error_description": "Request could not be processed.",
        })
        self.assertNotIn("synthetic failure", json.dumps(mapped_json))

        with self.assertRaises(StubHTTPException):
            self.module.ControllerToken.handle_exception(StubHTTPException("already handled"))

    def test_base_controller_does_not_publish_oidc_discovery_but_keeps_jwks(self):
        self.assertFalse(hasattr(self.module.ControllerToken, "well_known_openid_configuration"))
        self._require("well_known_jwks")
        service = mock.Mock()
        service.oidc_jwks.return_value = {"keys": [{"kid": "synthetic-kid"}]}
        self.module.request.env = {"amr.token.helper": service}

        jwks = self.controller.well_known_jwks()

        self.assertEqual(self._json(jwks), {"keys": [{"kid": "synthetic-kid"}]})

    def test_token_endpoint_passes_unsupported_grant_status_and_maps_exceptions(self):
        self._require("api_oidc_token")
        service = mock.Mock()
        service.sudo.return_value = service
        service.oidc_token.return_value = {
            "status": 400,
            "error": "unsupported_grant_type",
        }
        self.module.request.env = {"amr.token.helper": service}
        response = self.controller.api_oidc_token(grant_type="password")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._json(response), {"error": "unsupported_grant_type"})
        self.assertNotIn("access_token", self._json(response))

        service.oidc_token.side_effect = ValueError("bad request")
        with self.assertLogs(self.module._logger, level="ERROR") as captured:
            response = self.controller.api_oidc_token(grant_type="password")
        self.assertIn("Error oidc_token", captured.output[0])
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self._json(response)["error"], "invalid_request")

    def test_introspection_and_profile_status_mapping(self):
        self._require("oidc_introspect")
        self._require("api_oidc_profile")
        service = mock.Mock()
        service.sudo.return_value = service
        service.oidc_introspect.return_value = {"active": True, "sub": "synthetic-user"}
        service.oidc_profile.return_value = {"sub": "synthetic-user"}
        self.module.request.env = {"amr.token.helper": service}

        active = self.controller.oidc_introspect(token="synthetic-token")
        self.assertEqual(active.status_code, 200)
        self.assertEqual(self._json(active)["active"], True)
        service.oidc_introspect.return_value = {"active": False, "error": "invalid_token"}
        inactive = self.controller.oidc_introspect(token="invalid-token")
        self.assertEqual(inactive.status_code, 401)
        profile = self.controller.api_oidc_profile(token="synthetic-token")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(self._json(profile), {"sub": "synthetic-user"})

    def test_routes_remain_public_no_csrf_and_expected_http_methods(self):
        expected = {
            "well_known_jwks": ("/.well-known/jwks.json", ["GET"]),
            "api_oidc_token": ("/oidc/token", ["POST"]),
            "api_oidc_introspect": ("/oidc/introspect", ["GET", "POST"]),
            "api_oidc_profile": (["/oidc/profile", "/oidc/userinfo"], ["GET"]),
        }
        for method, (paths, methods) in expected.items():
            route = self.module.ControllerToken.__dict__[method]
            self.assertEqual(route._route_paths, paths)
            self.assertEqual(route._route_options["methods"], methods)
            self.assertFalse(route._route_options["csrf"])
            expected_auth = "public" if method.startswith("well_known_") else "none"
            self.assertEqual(route._route_options["auth"], expected_auth)


if __name__ == "__main__":
    unittest.main()
