"""Mock-isolated behavioral tests for the API controller response contract."""
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


ADDON = pathlib.Path(__file__).resolve().parents[2]


def load_controllers():
    """Load committed controller modules with narrow framework doubles."""
    package_names = (
        "amr_data_sync",
        "amr_data_sync.controllers",
        "amr_data_sync.exceptions",
    )
    previous = {name: sys.modules.get(name) for name in package_names}
    previous_modules = {
        name: sys.modules.get(name)
        for name in ("odoo", "odoo.http", "werkzeug", "werkzeug.exceptions",
                     "werkzeug.wrappers")
    }

    odoo = types.ModuleType("odoo")
    odoo_http = types.ModuleType("odoo.http")
    odoo_http.request = Mock(name="request")
    odoo_http.route = lambda *args, **kwargs: (lambda method: method)
    odoo_http.Controller = type("Controller", (object,), {})
    odoo.http = odoo_http
    odoo.Controller = odoo_http.Controller

    class HTTPException(Exception):
        pass

    class Response(object):
        def __init__(self, response, headers=None, status=200):
            self.response = response
            self.headers = headers or []
            self.status_code = status

        def get_data(self, as_text=False):
            if as_text:
                return self.response
            return self.response.encode("utf-8")

    werkzeug = types.ModuleType("werkzeug")
    werkzeug_exceptions = types.ModuleType("werkzeug.exceptions")
    werkzeug_exceptions.HTTPException = HTTPException
    werkzeug_wrappers = types.ModuleType("werkzeug.wrappers")
    werkzeug_wrappers.Response = Response
    werkzeug.exceptions = werkzeug_exceptions
    werkzeug.wrappers = werkzeug_wrappers

    api_exception_module = types.ModuleType("amr_data_sync.exceptions.api_exception")

    class ApiException(Exception):
        def __init__(self, error="api_error", description="API failure", status=400):
            super(ApiException, self).__init__(description)
            self.error = error
            self.error_description = description
            self.status = status

        def to_dict(self):
            return {"success": False, "error": self.error,
                    "error_description": self.error_description}

    api_exception_module.ApiException = ApiException
    for name, path in (
        ("amr_data_sync", ADDON),
        ("amr_data_sync.controllers", ADDON / "controllers"),
        ("amr_data_sync.exceptions", ADDON / "exceptions"),
    ):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        sys.modules[name] = package
    sys.modules["amr_data_sync.exceptions.api_exception"] = api_exception_module
    sys.modules["odoo"] = odoo
    sys.modules["odoo.http"] = odoo_http
    sys.modules["werkzeug"] = werkzeug
    sys.modules["werkzeug.exceptions"] = werkzeug_exceptions
    sys.modules["werkzeug.wrappers"] = werkzeug_wrappers

    try:
        loaded = {}
        for short_name in ("mixin", "main"):
            name = "amr_data_sync.controllers." + short_name
            path = ADDON / "controllers" / (short_name + ".py")
            sys.modules.pop(name, None)
            spec = importlib.util.spec_from_file_location(name, str(path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[short_name] = module
        return loaded["mixin"], loaded["main"], odoo_http.request, ApiException, HTTPException
    finally:
        for name in ("amr_data_sync.controllers.main", "amr_data_sync.controllers.mixin",
                     "amr_data_sync.exceptions.api_exception"):
            sys.modules.pop(name, None)
        for name, module in previous_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class ApiControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mixin_module, cls.main_module, cls.request, cls.ApiException, cls.HTTPException = load_controllers()
        cls.mixin = cls.mixin_module.ApiControllerMixin

    def test_empty_request_body_is_an_empty_json_object(self):
        self.request.httprequest.data = b""
        self.assertEqual(self.mixin.get_json_payload(), {})

    def test_json_body_is_decoded_to_python_payload(self):
        payload = {"record_id": 17, "active": True}
        self.request.httprequest.data = json.dumps(payload).encode("utf-8")
        self.assertEqual(self.mixin.get_json_payload(), payload)

    def test_json_success_sets_contract_envelope_and_http_status(self):
        result = self.mixin.json_success({"updated": 3}, status=202)
        self.assertEqual(result.status_code, 202)
        self.assertIn(("Content-Type", "application/json"), result.headers)
        self.assertEqual(json.loads(result.get_data(as_text=True)),
                         {"success": True, "data": {"updated": 3}})

    def test_api_exception_handler_preserves_structured_error_and_status(self):
        error = self.ApiException("bad_payload", "Invalid input", status=422)
        result = self.mixin.handle_exception(error)
        self.assertEqual(result.status_code, 422)
        self.assertEqual(json.loads(result.get_data(as_text=True)), error.to_dict())

    def test_http_exception_is_reraised_for_framework_handling(self):
        error = self.HTTPException("not found")
        with self.assertRaises(self.HTTPException) as raised:
            self.mixin.handle_exception(error)
        self.assertIs(raised.exception, error)

    def test_unknown_error_has_generic_response_and_http_500(self):
        result = self.mixin.handle_exception(ValueError("internal detail"))
        self.assertEqual(result.status_code, 500)
        self.assertEqual(json.loads(result.get_data(as_text=True)), {
            "success": False, "error": "general_error",
            "error_description": "internal detail"})

    def test_controller_sends_decoded_payload_to_sudo_service_and_wraps_result(self):
        controller = self.main_module.DataUpdateController()
        payload = {"record_id": 23}
        self.request.httprequest.data = json.dumps(payload).encode("utf-8")
        service = Mock()
        service.sudo.return_value.data_update.return_value = {"accepted": True}
        self.request.env = {"data.update.service": service}

        response = controller.data_update()

        service.sudo.assert_called_once_with()
        service.sudo.return_value.data_update.assert_called_once_with(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True)),
                         {"success": True, "data": {"accepted": True}})

    def test_controller_converts_service_api_exception_to_structured_response(self):
        controller = self.main_module.DataUpdateController()
        self.request.httprequest.data = b'{"record_id": 1}'
        service = Mock()
        service.sudo.return_value.data_update.side_effect = self.ApiException(
            "rejected", "Request rejected", status=409)
        self.request.env = {"data.update.service": service}

        response = controller.data_update()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(json.loads(response.get_data(as_text=True)), {
            "success": False, "error": "rejected",
            "error_description": "Request rejected"})

    def test_controller_converts_invalid_json_to_general_error_response(self):
        controller = self.main_module.DataUpdateController()
        self.request.httprequest.data = b"{invalid"
        service = Mock()
        self.request.env = {"data.update.service": service}

        response = controller.data_update()

        service.sudo.assert_not_called()
        self.assertEqual(response.status_code, 500)
        body = json.loads(response.get_data(as_text=True))
        self.assertEqual(body["success"], False)
        self.assertEqual(body["error"], "general_error")
        self.assertTrue(body["error_description"])


if __name__ == "__main__":
    unittest.main()
