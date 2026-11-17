"""Security regression tests against the real amr_data_sync controller."""
import importlib.util
import json
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock


ADDON = pathlib.Path(__file__).resolve().parents[2]


def load_controller():
    """Import controller source with narrow Odoo/Werkzeug doubles."""
    saved = {name: sys.modules.get(name) for name in (
        "odoo", "odoo.http", "werkzeug", "werkzeug.exceptions",
        "werkzeug.wrappers", "amr_data_sync", "amr_data_sync.controllers",
        "amr_data_sync.controllers.mixin", "amr_data_sync.controllers.main",
        "amr_data_sync.exceptions", "amr_data_sync.exceptions.api_exception",
    )}
    odoo = types.ModuleType("odoo")
    http = types.ModuleType("odoo.http")
    http.request = Mock(name="request")
    http.route = lambda *args, **kwargs: lambda method: method
    http.Controller = type("Controller", (object,), {})
    odoo.http = http
    odoo.Controller = http.Controller

    class HTTPException(Exception):
        pass

    class Response(object):
        def __init__(self, response, headers=None, status=200):
            self.response, self.headers, self.status_code = response, headers or [], status

        def get_data(self, as_text=False):
            return self.response if as_text else self.response.encode("utf-8")

    werkzeug = types.ModuleType("werkzeug")
    exceptions = types.ModuleType("werkzeug.exceptions")
    exceptions.HTTPException = HTTPException
    wrappers = types.ModuleType("werkzeug.wrappers")
    wrappers.Response = Response
    werkzeug.exceptions, werkzeug.wrappers = exceptions, wrappers

    api_exc = types.ModuleType("amr_data_sync.exceptions.api_exception")
    class ApiException(Exception):
        status = 400
        def to_dict(self):
            return {"success": False, "error": "api_error"}
    api_exc.ApiException = ApiException

    for name, path in (("amr_data_sync", ADDON),
                       ("amr_data_sync.controllers", ADDON / "controllers"),
                       ("amr_data_sync.exceptions", ADDON / "exceptions")):
        pkg = types.ModuleType(name)
        pkg.__path__ = [str(path)]
        sys.modules[name] = pkg
    sys.modules.update({"odoo": odoo, "odoo.http": http,
                        "werkzeug": werkzeug, "werkzeug.exceptions": exceptions,
                        "werkzeug.wrappers": wrappers,
                        "amr_data_sync.exceptions.api_exception": api_exc})
    loaded = {}
    try:
        for short in ("mixin", "main"):
            name = "amr_data_sync.controllers." + short
            spec = importlib.util.spec_from_file_location(
                name, str(ADDON / "controllers" / (short + ".py")))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[short] = module
        return loaded["main"].DataUpdateController(), loaded["mixin"].ApiControllerMixin, http.request
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class Security101ControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller, cls.mixin, cls.request = load_controller()

    @unittest.skip("ADDONS13-101-SEC-01: existing error response exposes exception; Owner requested skip")
    def test_unexpected_service_error_does_not_echo_synthetic_secret(self):
        marker = "SECURITY101-SYNTHETIC-SECRET"
        service = Mock()
        service.sudo.return_value.data_update.side_effect = RuntimeError(marker)
        self.request.env = {"data.update.service": service}
        self.request.httprequest.data = b'{"event":"synthetic"}'

        response = self.controller.data_update()
        body = response.get_data(as_text=True)
        # This deliberately remains a failing security assertion if controller
        # error handling exposes exception text; do not alter production here.
        self.assertNotIn(marker, body)
        self.assertEqual(json.loads(body), {
            "success": False, "error": "general_error",
            "error_description": "Unknown error."})

    def test_issuer_boundary_is_delegated_to_service_not_body_echo(self):
        service = Mock()
        service.sudo.return_value.data_update.return_value = {"status": "error"}
        self.request.env = {"data.update.service": service}
        self.request.httprequest.data = json.dumps({
            "issuer": "body-untrusted-issuer", "res_model": "x.synthetic",
            "res_id": 7, "operation": "upsert",
            "event_datetime": "2026-01-15 10:00:00"}).encode("utf-8")

        response = self.controller.data_update()
        service.sudo.return_value.data_update.assert_called_once()
        supplied_payload = service.sudo.return_value.data_update.call_args[0][0]
        self.assertEqual(supplied_payload["issuer"], "body-untrusted-issuer")
        self.assertEqual(json.loads(response.get_data(as_text=True)), {
            "success": True, "data": {"status": "error"}})
        self.assertNotIn("body-untrusted-issuer", response.get_data(as_text=True))

    def test_controller_source_is_the_actual_security_boundary_under_test(self):
        source = (ADDON / "controllers" / "main.py").read_text()
        self.assertIn("self.handle_exception(ex)", source)
        self.assertIn("data.update.service", source)


if __name__ == "__main__":
    unittest.main()
