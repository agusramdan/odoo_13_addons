"""Contracts for the optional Sentry addon's bootstrap and packaging."""
import importlib
import ast
import json
import logging
import os
import sys
import tempfile
import unittest
from unittest import mock

from test_U11_sentry_safe_file import PROFILE


class SentryBootstrapContractTest(unittest.TestCase):
    def setUp(self):
        self._saved_modules = self._remove_sentry_modules()
        self._saved_stubs = {}
        for name in ("sentry_sdk", "odoo", "odoo.models", "odoo.fields"):
            if name in sys.modules:
                self._saved_stubs[name] = sys.modules.pop(name)

    @staticmethod
    def _remove_sentry_modules():
        saved = {}
        for name in list(sys.modules):
            if name == "amr_sentry" or name.startswith("amr_sentry."):
                saved[name] = sys.modules.pop(name)
        return saved

    def tearDown(self):
        self._remove_sentry_modules()
        for name in ("sentry_sdk", "odoo", "odoo.models", "odoo.fields"):
            sys.modules.pop(name, None)
        sys.modules.update(self._saved_stubs)
        sys.modules.update(self._saved_modules)

    def _odoo_stubs(self):
        odoo = mock.MagicMock()
        odoo.models.Model = type("Model", (), {})
        odoo.fields.Boolean = mock.MagicMock()
        return {"odoo": odoo}

    def test_import_initializes_once_with_sentry_namespace_only(self):
        marker = "https://synthetic.invalid/never-send-this-dsn"
        sentry = dict(PROFILE, dsn=marker, environment="contract-test")
        config = {"sentry": sentry,
                  "service_client": {"enabled": True, "mode": "all"}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as stream:
            json.dump(config, stream)
            stream.flush()
            sdk = mock.MagicMock()
            with mock.patch.dict(os.environ, {"AMR_SENTRY_CONFIG": stream.name}), \
                    mock.patch.dict(sys.modules, dict(self._odoo_stubs(), sentry_sdk=sdk)):
                package = importlib.import_module("amr_sentry")
                importlib.import_module("amr_sentry")
                self.assertIs(package, importlib.import_module("amr_sentry"))
                self.assertEqual(
                    sdk.init.call_args_list,
                    [mock.call(**sentry)],
                    "optional addon import must initialize SDK exactly once using sentry config only",
                )

    def test_schema_and_inactive_cases_do_not_initialize_or_capture(self):
        base = dict(PROFILE, dsn="https://synthetic.invalid/1")
        cases = []
        for key in PROFILE:
            missing = dict(base)
            del missing[key]
            cases.append((missing, {"enabled": True, "mode": "all"}))
            unsafe = dict(base, **{key: None})
            cases.append((unsafe, {"enabled": True, "mode": "all"}))
        for key, value in (("unknown", True), ("environment", 1), ("dsn", 1)):
            cases.append((dict(base, **{key: value}), {"enabled": True, "mode": "all"}))
        cases.extend([({}, {"enabled": False, "mode": "all"}),
                      ({}, {"enabled": True, "mode": "none"}),
                      ({}, {"enabled": True, "mode": "all"}),
                      ({"dsn": None}, {"enabled": True, "mode": "all"}),
                      ({"dsn": ""}, {"enabled": True, "mode": "all"})])
        sdk = mock.MagicMock()
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json") as stream:
            with mock.patch.dict(os.environ, {"AMR_SENTRY_CONFIG": stream.name,
                                             "SENTRY_DSN": "https://environment.invalid/1"}), \
                    mock.patch.dict(sys.modules, dict(self._odoo_stubs(), sentry_sdk=sdk)):
                for sentry, policy in cases:
                    with self.subTest(sentry=sentry, policy=policy):
                        stream.seek(0)
                        stream.truncate()
                        json.dump({"sentry": sentry, "service_client": policy}, stream)
                        stream.flush()
                        self._remove_sentry_modules()
                        runtime = importlib.import_module("amr_sentry.services.runtime")
                        runtime.REPORTER.report(True)
                        runtime.REPORTER.report(False)
                        sdk.init.assert_not_called()
                        sdk.capture_message.assert_not_called()
                        sdk.capture_exception.assert_not_called()

    def test_invalid_override_is_nonfatal_and_warns_without_secrets(self):
        marker = "PRIVATE-SYNTHETIC-CONFIG-MARKER"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as stream:
            stream.write("{" + marker)
            stream.flush()
            sdk = mock.MagicMock()
            with self.assertLogs(level="WARNING") as captured:
                with mock.patch.dict(os.environ, {"AMR_SENTRY_CONFIG": stream.name}), \
                        mock.patch.dict(sys.modules, dict(self._odoo_stubs(), sentry_sdk=sdk)):
                    importlib.import_module("amr_sentry")
            self.assertEqual(sdk.init.call_count, 0, "invalid override must not initialize SDK")
            output = "\n".join(captured.output)
            self.assertTrue(output, "invalid override must emit a generic warning")
            self.assertNotIn(marker, output, "warning must not expose config/DSN markers")


class SentryPackagingContractTest(unittest.TestCase):
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _read_contract_file(self, relative_path):
        path = os.path.join(self.ROOT, relative_path)
        self.assertTrue(os.path.isfile(path), "required packaging contract file is absent: {}".format(relative_path))
        with open(path, "r") as stream:
            return stream.read()

    def _read_manifest(self, relative_path):
        return ast.literal_eval(self._read_contract_file(relative_path))

    def test_optional_addon_declares_dependencies_and_exact_pins(self):
        manifest = self._read_manifest("amr_sentry/__manifest__.py")
        requirements = self._read_contract_file("amr_sentry/requirements.txt")
        self.assertIn("amr_service_client", manifest.get("depends", []))
        python_dependencies = manifest.get("external_dependencies", {}).get("python", [])
        self.assertIn("sentry_sdk", python_dependencies)
        self.assertIn("yaml", python_dependencies)
        self.assertIn("sentry-sdk==2.73.0", requirements)
        self.assertIn("PyYAML==6.0.1", requirements)

    def test_core_packaging_no_longer_declares_sentry_dependencies(self):
        manifest = self._read_manifest("amr_service_client/__manifest__.py")
        service_requirements = self._read_contract_file("amr_service_client/requirements.txt")
        root_requirements = self._read_contract_file("requirement.txt")
        core_python_dependencies = manifest.get("external_dependencies", {}).get("python", [])
        self.assertNotIn("sentry_sdk", core_python_dependencies)
        self.assertNotIn("sentry-sdk", service_requirements)
        self.assertNotIn("sentry-sdk", root_requirements)
        self.assertNotIn("PyYAML", service_requirements)
        self.assertNotIn("PyYAML", root_requirements)
