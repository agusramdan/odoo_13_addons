"""Offline characterization tests for the push data-update decision boundary."""
import importlib.util
import pathlib
import sys
import types
from unittest import TestCase
from unittest.mock import Mock


ADDON = pathlib.Path(__file__).resolve().parents[2]


def load_service():
    """Load the real module with only the Odoo decorators/model names stubbed."""
    odoo = types.ModuleType("odoo")
    odoo.api = types.SimpleNamespace(model=lambda fn: fn)
    odoo.models = types.SimpleNamespace(AbstractModel=object)
    packages = {
        "amr_data_sync": str(ADDON),
        "amr_data_sync.exceptions": str(ADDON / "exceptions"),
        "amr_data_sync.services": str(ADDON / "services"),
    }
    previous = {name: sys.modules.get(name) for name in packages}
    previous_service = sys.modules.get("amr_data_sync.services.data_update")
    for name, path in packages.items():
        package = types.ModuleType(name)
        package.__path__ = [path]
        sys.modules[name] = package
    old_odoo = sys.modules.get("odoo")
    old_werkzeug = sys.modules.get("werkzeug")
    old_werkzeug_exceptions = sys.modules.get("werkzeug.exceptions")
    werkzeug = types.ModuleType("werkzeug")
    werkzeug_exceptions = types.ModuleType("werkzeug.exceptions")
    class Unauthorized(Exception):
        def __init__(self, description=None):
            super(Unauthorized, self).__init__(description)
    werkzeug_exceptions.Unauthorized = Unauthorized
    werkzeug.exceptions = werkzeug_exceptions
    sys.modules["werkzeug"] = werkzeug
    sys.modules["werkzeug.exceptions"] = werkzeug_exceptions
    sys.modules["odoo"] = odoo
    try:
        name = "amr_data_sync.services.data_update"
        sys.modules.pop(name, None)
        spec = importlib.util.spec_from_file_location(name, ADDON / "services" / "data_update.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.DataUpdateService
    finally:
        if previous_service is None:
            sys.modules.pop("amr_data_sync.services.data_update", None)
        else:
            sys.modules["amr_data_sync.services.data_update"] = previous_service
        if old_odoo is None:
            sys.modules.pop("odoo", None)
        else:
            sys.modules["odoo"] = old_odoo
        if old_werkzeug is None:
            sys.modules.pop("werkzeug", None)
        else:
            sys.modules["werkzeug"] = old_werkzeug
        if old_werkzeug_exceptions is None:
            sys.modules.pop("werkzeug.exceptions", None)
        else:
            sys.modules["werkzeug.exceptions"] = old_werkzeug_exceptions
        for name, package in previous.items():
            if package is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = package


class Recordset(object):
    def __init__(self, **values):
        self.__dict__.update(values)

    def __bool__(self):
        return bool(getattr(self, "ids", []))

    __nonzero__ = __bool__


class ServiceTest(TestCase):
    def test_loader_restores_existing_module_entry(self):
        name = "amr_data_sync.services.data_update"
        previous = sys.modules.get(name)
        sentinel = types.ModuleType(name)
        try:
            sys.modules[name] = sentinel
            loaded = load_service()
            self.assertEqual(loaded.__name__, "DataUpdateService")
            self.assertIs(sys.modules.get(name), sentinel)
        finally:
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    @classmethod
    def setUpClass(cls):
        cls.service_class = load_service()

    def service(self, env):
        service = self.service_class()
        service.env = env
        return service

    def test_required_rejects_missing_and_falsey_values(self):
        for payload in ({}, {"issuer": ""}, {"issuer": None}, {"issuer": 0}):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(Exception, "issuer is required"):
                    self.service_class._required(payload, "issuer")
        self.assertEqual(self.service_class._required({"issuer": "synthetic"}, "issuer"), "synthetic")

    def test_known_issuer_and_company_strategy_create_acceptance_without_dispatch(self):
        service = self.service_class()
        update = Mock()
        update.prepare_data_update.return_value = {"res_model": "x"}
        update.create.side_effect = lambda vals: Recordset(state=vals["state"], values=dict(vals))
        server = Recordset(ids=[7])
        company = Recordset(ids=[12], company_id=Recordset(ids=[23], id=23))
        strategy = Recordset(ids=[41], id=41)
        env = {
            "external.data.update": update,
            "external.server.sync": Recordset(search=Mock(return_value=server)),
            "external.data.company": Recordset(search=Mock(return_value=company)),
            "external.data.sync.strategy": Recordset(search=Mock(return_value=strategy)),
        }
        service.env = env
        payload = {"issuer": "issuer-A", "res_model": "x", "res_id": 9,
                   "operation": "upsert", "event_datetime": "synthetic-time",
                   "data": {"company_id": [5]}}
        result = service.create_data_update(payload)
        self.assertEqual(result.state, "accept")
        self.assertEqual(result.values["company_id"], 23)
        self.assertEqual(result.values["strategy_id"], 41)
        self.assertNotIn("error_message", result.values)
        self.assertEqual(env["external.data.company"].search.call_args[0][0][-1][-1], 5)

    def test_unmapped_issuer_is_saved_as_error_and_does_not_lookup_company(self):
        service = self.service_class()
        update = Mock()
        update.prepare_data_update.return_value = {}
        update.create.side_effect = lambda vals: Recordset(state=vals["state"], values=dict(vals))
        server_model = Recordset(search=Mock(return_value=Recordset(ids=[])))
        company_model = Recordset(search=Mock())
        env = {"external.data.update": update, "external.server.sync": server_model,
               "external.data.company": company_model}
        service.env = env
        result = service.create_data_update({"issuer": "unknown", "res_model": "x",
            "res_id": 1, "operation": "upsert", "event_datetime": "t"})
        self.assertEqual(result.state, "error")
        self.assertFalse(result.values["strategy_id"])
        self.assertEqual(result.values["error_message"], "authorized_party unknown not found.")
        company_model.search.assert_not_called()

    def test_secure_mode_rejects_missing_token_issuer_before_persisting(self):
        service = self.service_class()
        params = Recordset(sudo=Mock(return_value=Recordset(get_param=Mock(return_value="secure"))))
        updates = Recordset(create_data_update=Mock())
        env = {"ir.config_parameter": params, "ir.http": Recordset(get_jwt_payload=Mock(return_value={}),
                                                                   ),
               "data.update.service": updates}
        service.env = env
        with self.assertRaises(Exception) as caught:
            service.data_update({"issuer": "untrusted"})
        self.assertEqual(type(caught.exception).__name__, "Unauthorized")
        updates.create_data_update.assert_not_called()

    def test_token_strategy_uses_sudo_parameter_and_secure_log_default(self):
        service = self.service_class()
        parameter_model = Recordset(sudo=Mock())
        elevated = Recordset(get_param=Mock(return_value="not_secure"))
        parameter_model.sudo.return_value = elevated
        service.env = {"ir.config_parameter": parameter_model}

        self.assertEqual(service.get_token_strategy(), "not_secure")
        parameter_model.sudo.assert_called_once_with()
        elevated.get_param.assert_called_once_with(
            "amr_data_sync.date_update_security_option", "secure_log")

    def test_create_update_prefers_top_level_company_and_uses_unscoped_strategy_fallback(self):
        service = self.service_class()
        update = Mock()
        update.prepare_data_update.return_value = {"state": "pending"}
        update.create.side_effect = lambda vals: Recordset(state=vals["state"], values=dict(vals))
        server = Recordset(ids=[3])
        company = Recordset(ids=[5], company_id=Recordset(ids=[8], id=8))
        fallback = Recordset(ids=[11], id=11)
        server_model = Recordset(search=Mock(return_value=server))
        company_model = Recordset(search=Mock(return_value=company))
        strategy_model = Recordset(search=Mock(side_effect=[Recordset(ids=[]), fallback]))
        service.env = {"external.data.update": update,
                       "external.server.sync": server_model,
                       "external.data.company": company_model,
                       "external.data.sync.strategy": strategy_model}
        payload = {"issuer": "issuer-B", "res_model": "res.partner", "res_id": 17,
                   "operation": "upsert", "event_datetime": "2026-01-01T00:00:00Z",
                   "company_id": 6, "data": {"company_id": [99]}}

        result = service.create_data_update(payload)

        self.assertEqual(result.state, "accept")
        self.assertEqual(result.values["company_id"], 8)
        self.assertEqual(result.values["strategy_id"], 11)
        self.assertEqual(company_model.search.call_args[0][0][-1], ("external_id", "=", 6))
        self.assertEqual(strategy_model.search.call_count, 2)
        self.assertEqual(strategy_model.search.call_args[0][0][-1], ("company_ids", "=", False))
        self.assertEqual(strategy_model.search.call_args[1], {"limit": 1})

    def test_data_update_overwrites_issuer_from_token_and_dispatches_only_acceptance(self):
        service = self.service_class()
        service.get_token_strategy = Mock(return_value="secure_log")
        auth = Recordset(get_jwt_payload=Mock(return_value={"azp": "token-issuer"}))
        accepted = Recordset(state="accept", id=31, dispatch_process=Mock())
        service.env = {"ir.http": auth}
        service.create_data_update = Mock(return_value=accepted)
        payload = {"issuer": "caller-issuer"}

        response = service.data_update(payload)

        self.assertEqual(payload["issuer"], "token-issuer")
        self.assertEqual(response, {"data_accept": 31, "status": "accepted"})
        service.create_data_update.assert_called_once_with(payload)
        accepted.dispatch_process.assert_called_once_with()

    def test_data_update_reports_error_without_dispatching_rejected_record(self):
        service = self.service_class()
        service.get_token_strategy = Mock(return_value="not_secure")
        rejected = Recordset(state="error", id=44, dispatch_process=Mock())
        service.create_data_update = Mock(return_value=rejected)
        service.env = {}

        response = service.data_update({"issuer": "caller-issuer"})

        self.assertEqual(response, {"data_accept": 44, "status": "error"})
        service.create_data_update.assert_called_once_with({"issuer": "caller-issuer"})
        rejected.dispatch_process.assert_not_called()
