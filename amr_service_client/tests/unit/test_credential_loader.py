"""U04 offline regression characterization; not Odoo ORM or security UAT."""
import importlib.util
import builtins
import io
import json

import os
from pathlib import Path
import socket
import sys
import traceback
import types
import unittest
from unittest import mock


def load_module():
    odoo = types.ModuleType("odoo")
    tools = types.ModuleType("odoo.tools")
    odoo.api = types.SimpleNamespace(model=lambda fn: fn)
    odoo.models = types.SimpleNamespace(AbstractModel=object)
    odoo.__dict__['models'] = odoo.models
    odoo.tools = tools
    tools.config = {}
    tools.ormcache = lambda *args: lambda fn: fn
    path = Path(__file__).resolve().parents[2] / "services" / "credential_loader.py"
    spec = importlib.util.spec_from_file_location("isolated_credential_loader_u04", str(path))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"odoo": odoo, "odoo.tools": tools}):
        spec.loader.exec_module(module)
    return module


# Import bootstrap precedes the per-test guard; it is not guarded.
# Selected Python APIs only: not native calls or child processes.
loader = load_module()


class FakeEnv(dict):
    def __init__(self, record=None, fallback=None):
        super().__init__()
        self.record = record
        self.fallback = fallback
        self.searches = []
        self.refs = []
        self["service.credential"] = self
        self["service.credential.loader.database"] = loader.ServiceCredentialLoaderDatabase()
        self["service.auth.factory"] = types.SimpleNamespace(
            is_supported=lambda kind: kind in {
                "api_key", "bearer", "basic", "client_secret", "service_account"})

    def search(self, domain, limit=None):
        self.searches.append((domain, limit))
        return self.record

    def ref(self, value):
        self.refs.append(value)
        if value is None:
            raise ValueError("Credential 'None' not found")
        return self.fallback


def credential(data, scopes=""):
    return types.SimpleNamespace(source="database", credential_json=data, scopes=scopes)


class OfflineGuardedTestCase(unittest.TestCase):
    """Block selected Python I/O APIs process-locally during each test."""

    def setUp(self):
        self.stack = __import__('contextlib').ExitStack()
        self.addCleanup(self.stack.close)
        def deny(*args, **kwargs):
            raise RuntimeError('offline access denied')
        for target in ('builtins.open', 'io.open', 'os.open', 'os.getenv',
                       'socket.socket.connect', 'socket.socket.connect_ex',
                       'socket.create_connection', 'socket.getaddrinfo'):
            self.stack.enter_context(mock.patch(target, side_effect=deny))

    def assert_guard_controls(self, subject):
        for action in (lambda: builtins.open('synthetic'), lambda: io.open('synthetic'),
                       lambda: os.open('synthetic', os.O_RDONLY), lambda: os.getenv('synthetic'),
                       lambda: socket.create_connection(('synthetic.invalid', 9)),
                       lambda: socket.getaddrinfo('synthetic.invalid', 9)):
            with self.assertRaisesRegex(RuntimeError, 'offline access denied'):
                action()
        self.assertEqual(subject.load_credential(credential('{"type":"bearer"}'))['type'], 'bearer')
        sock = socket.socket()
        self.addCleanup(sock.close)
        for action in (lambda: sock.connect(('127.0.0.1', 9)), lambda: sock.connect_ex(('127.0.0.1', 9))):
            with self.assertRaisesRegex(RuntimeError, 'offline access denied'):
                action()


class CredentialLoaderCharacterization(OfflineGuardedTestCase):
    def setUp(self):
        super().setUp()
        self.env = FakeEnv()
        self.subject = loader.ServiceCredentialLoader()
        self.subject.env = self.env

    def test_shared_guard_positive_controls(self):
        # Exercise the same full guard control in this test class too.
        self.assert_guard_controls(self.subject)

    def assert_scope_contract(self):
        record = credential('{"type":"bearer","scope":"alpha beta alpha","scopes":"ignored"}', 'beta gamma,delta')
        result = self.subject.load_credential(record)
        self.assertEqual(set(result["scope"]), {"alpha", "beta", "gamma,delta"})
        self.assertEqual(len(result["scope"]), 3)
        self.assertEqual(result["scopes"], "ignored")

    def test_database_scope_merge_dedup_precedence_and_whitespace(self):
        self.assert_scope_contract()

    def test_legacy_U03_database_scope_merge_and_dedup(self):
        obj = object.__new__(loader.ServiceCredentialLoaderDatabase)
        result = obj.load_credential(credential('{"type":"bearer","scope":"a b"}', 'b c'))
        self.assertEqual(set(result['scope']), {'a', 'b', 'c'})

    def test_legacy_U03_database_scope_is_whitespace_not_comma_parser(self):
        obj = object.__new__(loader.ServiceCredentialLoaderDatabase)
        result = obj.load_credential(credential('{"type":"bearer","scope":"read,write"}', 'team,member'))
        self.assertEqual(set(result['scope']), {'read,write', 'team,member'})

    def test_legacy_U03_name_lookup_hit_and_xmlid_fallback_bug_characterization(self):
        record = credential('{"type":"bearer"}')
        self.env.record = record
        self.assertIs(self.subject.get_credential('synthetic-name'), record)
        self.assertEqual(self.env.searches[-1], ([('name', '=', 'synthetic-name')], 1))
        self.env.record = None
        with self.assertRaisesRegex(ValueError, r"Credential 'None' not found"):
            self.subject.get_credential('module.synthetic_xmlid')
        self.assertEqual(self.env.refs, [None])

    def test_fallback_scopes_list_and_empty_scope(self):
        result = self.subject.load_credential(credential('{"type":"basic","scope":"","scopes":["x","y","x"]}', 'y z'))
        self.assertEqual(set(result["scope"]), {"x", "y", "z"})
        self.assertEqual(len(result["scope"]), 3)
        self.assertEqual(self.subject.load_credential(credential('{"type":"basic"}'))["scope"], [])

    def test_malformed_json_and_non_object_propagate(self):
        with self.assertRaises(json.JSONDecodeError):
            self.subject.load_credential(credential('{bad'))
        with self.assertRaises(AttributeError):
            self.subject.load_credential(credential('[]'))

    def test_missing_type_unsupported_type_and_source(self):
        with self.assertRaisesRegex(ValueError, "Missing credential type"):
            self.subject.load_credential(credential('{}'))
        with self.assertRaisesRegex(ValueError, "Unsupported credential type"):
            self.subject.load_credential(credential('{"type":"synthetic-unsupported"}'))
        with self.assertRaisesRegex(ValueError, "Unsupported credential source"):
            self.subject.load_credential(types.SimpleNamespace(source="synthetic-unknown"))

    def test_name_lookup_in_both_entrypoints_and_record_passthrough(self):
        record = credential('{"type":"bearer"}')
        self.env.record = record
        self.assertIs(self.subject.get_credential(record), record)
        self.assertIs(self.subject.get_credential('synthetic-name'), record)
        self.assertEqual(self.subject.load_credential('synthetic-name'), {"type": "bearer", "scope": []})
        self.assertEqual(self.env.searches, [([("name", "=", "synthetic-name")], 1)] * 2)
        self.assertEqual(self.env.refs, [])

    def test_legacy_U03_each_json_or_path_loader_returns_decoded_data(self):
        expected = {'type': 'basic', 'username': 'synthetic'}
        for name, attrs in (
                ('ServiceCredentialLoaderFilePath', {}),
                ('ServiceCredentialLoaderEnvPath', {'env': 'synthetic-path'}),
                ('ServiceCredentialLoaderConfigPath', {'config': 'synthetic-path'}),
                ('ServiceCredentialLoaderParameterPath', {})):
            with self.subTest(loader=name):
                obj = object.__new__(getattr(loader, name))
                obj.env = {'ir.config_parameter': types.SimpleNamespace(
                    sudo=lambda: types.SimpleNamespace(get_param=lambda key: 'synthetic-path'))}
                with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(expected))), \
                        mock.patch.object(loader.os, 'getenv', return_value=attrs.get('env', 'synthetic-path')), \
                        mock.patch.object(loader, 'config', {'SYNTHETIC': attrs.get('config', 'synthetic-path')}):
                    self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')), expected, name)

    def test_legacy_U03_env_json_decodes_synthetic_value(self):
        obj = object.__new__(loader.ServiceCredentialLoaderEnvJson)
        with mock.patch.object(loader.os, 'getenv', return_value='{"type":"api_key"}'):
            self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')), {'type': 'api_key'})

    def test_legacy_U03_system_parameter_json_and_path_loaders(self):
        expected = {'type': 'bearer'}
        params = types.SimpleNamespace(sudo=lambda: types.SimpleNamespace(
            get_param=lambda key: json.dumps(expected)))
        obj = object.__new__(loader.ServiceCredentialLoaderParameterJson)
        obj.env = {'ir.config_parameter': params}
        self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')), expected)
        obj = object.__new__(loader.ServiceCredentialLoaderParameterPath)
        obj.env = {'ir.config_parameter': types.SimpleNamespace(sudo=lambda: types.SimpleNamespace(
            get_param=lambda key: 'synthetic-path'))}
        with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(expected))):
            self.assertEqual(obj.load_credential(types.SimpleNamespace(reference='SYNTHETIC')), expected)

    def test_legacy_U03_missing_references_and_malformed_json_are_rejected(self):
        ref = types.SimpleNamespace(reference='SYNTHETIC')
        for cls in (loader.ServiceCredentialLoaderEnvJson, loader.ServiceCredentialLoaderEnvPath):
            with mock.patch.object(loader.os, 'getenv', return_value=None), self.assertRaises(ValueError):
                object.__new__(cls).load_credential(ref)
        for cls in (loader.ServiceCredentialLoaderConfigPath,):
            with mock.patch.object(loader, 'config', {}), self.assertRaises(ValueError):
                object.__new__(cls).load_credential(ref)
        for cls in (loader.ServiceCredentialLoaderParameterJson, loader.ServiceCredentialLoaderParameterPath):
            obj = object.__new__(cls)
            obj.env = {'ir.config_parameter': types.SimpleNamespace(sudo=lambda: types.SimpleNamespace(get_param=lambda key: None))}
            with self.assertRaises(ValueError):
                obj.load_credential(ref)
        for cls in (loader.ServiceCredentialLoaderEnvJson, loader.ServiceCredentialLoaderEnvPath):
            with mock.patch.object(loader.os, 'getenv', return_value=None), self.assertRaises(ValueError):
                object.__new__(cls).load_credential(ref)

    def test_legacy_U03_file_json_malformed_and_database_validation_cases(self):
        obj = object.__new__(loader.ServiceCredentialLoaderFilePath)
        with mock.patch('builtins.open', mock.mock_open(read_data='{bad')), self.assertRaises(json.JSONDecodeError):
            obj.load_credential(types.SimpleNamespace(reference='synthetic-path'))
        obj = object.__new__(loader.ServiceCredentialLoader)
        obj.env = self.env
        for data in ({}, {'type': 'not-supported'}):
            with self.assertRaises(ValueError): obj._validate(data)
        for kind in ('api_key', 'bearer', 'basic'):
            obj._validate({'type': kind})
        with self.assertRaises(ValueError): obj._validate({'type': 'none'})

    def assert_missing_reference_contract(self, method):
        with self.assertRaisesRegex(ValueError, "not found"):
            method('module.synthetic_ref')
        self.assertEqual(self.env.searches, [([("name", "=", "module.synthetic_ref")], 1)])
        # Current defect: ref receives the false search result, not the XML ID.
        self.assertEqual(self.env.refs, [None])

    def test_missing_reference_characterizes_overwritten_xmlid_in_both_entrypoints(self):
        for name in ('get_credential', 'load_credential'):
            with self.subTest(name=name):
                self.env.searches.clear()
                self.env.refs.clear()
                self.assert_missing_reference_contract(getattr(self.subject, name))

    def test_scope_mutation_control_is_detected(self):
        database = self.env['service.credential.loader.database']
        with mock.patch.object(database, 'load_credential', return_value={'type': 'bearer', 'scope': ['alpha'], 'scopes': 'ignored'}):
            with self.assertRaises(AssertionError):
                self.assert_scope_contract()

    def test_reference_mutation_control_is_detected(self):
        def wrong_lookup(name):
            self.env.search([('name', '=', name)], limit=1)
            self.env.ref(name)
            raise ValueError('not found')
        with self.assertRaises(AssertionError):
            self.assert_missing_reference_contract(wrong_lookup)


class OfflineSourceTests(OfflineGuardedTestCase):
    """Python process-local guard, installed after discovery/import bootstrap.

    It is not an OS sandbox and does not monitor native calls or child processes.
    Synthetic mocks override only the specific seam needed by each test.
    """

    def setUp(self):
        super().setUp()
        self.env = FakeEnv()
        self.subject = loader.ServiceCredentialLoader()
        self.subject.env = self.env
        for source, cls in (
            ('file_path', loader.ServiceCredentialLoaderFilePath),
            ('env_json', loader.ServiceCredentialLoaderEnvJson),
            ('env_path', loader.ServiceCredentialLoaderEnvPath),
            ('config_path', loader.ServiceCredentialLoaderConfigPath),
            ('system_parameter_json', loader.ServiceCredentialLoaderParameterJson),
            ('system_parameter_path', loader.ServiceCredentialLoaderParameterPath),
        ):
            instance = cls()
            instance.env = self.env
            self.env['service.credential.loader.' + source] = instance

    def run_source(self, source):
        return self.subject.load_credential(types.SimpleNamespace(source=source, reference='SYNTH_REF'))

    def test_guard_positive_controls_and_clean_control(self):
        self.assert_guard_controls(self.subject)

    def test_legacy_U03_each_json_or_path_loader_returns_decoded_data(self):
        for source in ('file_path', 'env_path', 'config_path', 'system_parameter_path'):
            with self.subTest(source=source):
                expected = {'type': 'bearer', 'username': 'synthetic'}
                payload = json.dumps(expected)
                self.env['ir.config_parameter'] = mock.Mock()
                self.env['ir.config_parameter'].sudo.return_value.get_param.return_value = '/synthetic/path'
                with mock.patch('builtins.open', mock.mock_open(read_data=payload)), \
                        mock.patch.object(loader.os, 'getenv', return_value='/synthetic/path'), \
                        mock.patch.object(loader, 'config', {'SYNTH_REF': '/synthetic/path'}):
                    self.assertEqual(self.run_source(source), expected)

    def test_legacy_U03_env_json_decodes_synthetic_value(self):
        with mock.patch.object(loader.os, 'getenv', return_value='{"type":"api_key"}'):
            self.assertEqual(self.run_source('env_json'), {'type': 'api_key'})

    def test_legacy_U03_system_parameter_json_and_path_loaders(self):
        expected = {'type': 'bearer'}
        params = mock.Mock()
        params.sudo.return_value.get_param.side_effect = [json.dumps(expected), '/synthetic/path']
        self.env['ir.config_parameter'] = params
        self.assertEqual(self.run_source('system_parameter_json'), expected)
        with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(expected))):
            self.assertEqual(self.run_source('system_parameter_path'), expected)

    def test_path_loader_sources_reject_malformed_json(self):
        for source in ('file_path', 'env_path', 'config_path', 'system_parameter_path'):
            with self.subTest(source=source):
                params = mock.Mock()
                params.sudo.return_value = params
                params.get_param.return_value = '/synthetic/path'
                self.env['ir.config_parameter'] = params
                with mock.patch('builtins.open', mock.mock_open(read_data='{bad')), \
                        mock.patch.object(loader.os, 'getenv', return_value='/synthetic/path'), \
                        mock.patch.object(loader, 'config', {'SYNTH_REF': '/synthetic/path'}):
                    with self.assertRaises(json.JSONDecodeError):
                        self.run_source(source)

    def test_legacy_U03_file_json_malformed_and_database_validation_cases(self):
        for data in ({}, {'type': 'not-supported'}):
            with self.assertRaises(ValueError): self.subject._validate(data)
        for kind in ('api_key', 'bearer', 'basic'):
            self.subject._validate({'type': kind})
        with self.assertRaises(ValueError): self.subject._validate({'type': 'none'})

    def test_synthetic_json_sources_and_path_sources(self):
        payload = '{"type":"bearer","key":"synthetic-value"}'
        expected = {'type': 'bearer', 'key': 'synthetic-value'}
        for source in ('env_json', 'system_parameter_json', 'file_path', 'env_path', 'config_path', 'system_parameter_path'):
            with self.subTest(source=source):
                params = mock.Mock()
                params.sudo.return_value = params
                params.get_param.return_value = payload if source.endswith('_json') else '/synthetic/path'
                self.env['ir.config_parameter'] = params
                content = mock.mock_open(read_data=payload)
                with mock.patch('builtins.open', content), mock.patch.object(loader.os, 'getenv', return_value=payload if source == 'env_json' else '/synthetic/path') as getenv, mock.patch.object(loader, 'config', {'SYNTH_REF': '/synthetic/path'}):
                    result = self.run_source(source)
                self.assertEqual(result, expected)
                if source in ('file_path', 'env_path', 'config_path', 'system_parameter_path'):
                    content.assert_called_once_with('SYNTH_REF' if source == 'file_path' else '/synthetic/path', 'r', encoding='utf-8')
                else:
                    content.assert_not_called()
                if source.startswith('env_'):
                    getenv.assert_called_once_with('SYNTH_REF')
                if source.startswith('system_parameter_'):
                    params.sudo.assert_called_once_with()
                    params.get_param.assert_called_once_with('SYNTH_REF')

    def test_missing_env_config_and_parameter_references(self):
        for source in ('env_json', 'env_path', 'config_path', 'system_parameter_json', 'system_parameter_path'):
            with self.subTest(source=source):
                params = mock.Mock()
                params.sudo.return_value = params
                params.get_param.return_value = None
                self.env['ir.config_parameter'] = params
                with mock.patch.object(loader.os, 'getenv', return_value=None), mock.patch.object(loader, 'config', {}):
                    with self.assertRaises(ValueError):
                        self.run_source(source)
                if source.startswith('system_parameter_'):
                    params.get_param.assert_called_once_with('SYNTH_REF')

    def test_missing_unreadable_and_malformed_paths(self):
        for source in ('file_path', 'env_path', 'config_path', 'system_parameter_path'):
            for failure in ('missing', 'unreadable', 'malformed'):
                with self.subTest(source=source, failure=failure):
                    params = mock.Mock()
                    params.sudo.return_value = params
                    params.get_param.return_value = '/synthetic/path'
                    self.env['ir.config_parameter'] = params
                    opener = mock.mock_open(read_data='{malformed')
                    expected = json.JSONDecodeError
                    if failure != 'malformed':
                        expected = FileNotFoundError if failure == 'missing' else PermissionError
                        opener.side_effect = expected('synthetic failure')
                    with mock.patch('builtins.open', opener), mock.patch.object(loader.os, 'getenv', return_value='/synthetic/path'), mock.patch.object(loader, 'config', {'SYNTH_REF': '/synthetic/path'}):
                        with self.assertRaises(expected):
                            self.run_source(source)
                    opener.assert_called_once_with('SYNTH_REF' if source == 'file_path' else '/synthetic/path', 'r', encoding='utf-8')

    def test_malformed_json_sources(self):
        for source in ('env_json', 'system_parameter_json'):
            with self.subTest(source=source):
                params = mock.Mock()
                params.sudo.return_value = params
                params.get_param.return_value = '{bad'
                self.env['ir.config_parameter'] = params
                with mock.patch.object(loader.os, 'getenv', return_value='{bad'):
                    with self.assertRaises(json.JSONDecodeError):
                        self.run_source(source)

    def test_xml_fallback_fake_returns_record_for_misdirected_none(self):
        """Legacy defect characterization only; not target security acceptance."""
        record = credential('{"type":"bearer","fallback_marker":"synthetic-fallback"}')
        for name in ('get_credential', 'load_credential'):
            with self.subTest(name=name):
                self.env.searches.clear()
                self.env.refs.clear()
                self.env.fallback = record
                with self.assertRaisesRegex(ValueError, r"Credential 'None' not found"):
                    getattr(self.subject, name)('module.synthetic_xmlid')
                self.assertEqual(self.env.searches,
                                 [([('name', '=', 'module.synthetic_xmlid')], 1)])
                self.assertEqual(self.env.refs, [None])

    def test_json_decode_error_retained_document_defect_characterization(self):
        marker = 'SYNTHETIC_SECRET_MARKER_46A2'
        def contains_marker(value):
            return marker in value
        self.assertTrue(contains_marker('prefix ' + marker))
        self.assertFalse(contains_marker('clean synthetic text'))
        with mock.patch.object(loader.os, 'getenv', return_value='{"type":' + marker):
            try:
                self.run_source('env_json')
            except json.JSONDecodeError as exc:
                # In-memory only; no production logger is exercised or captured.
                retained_document = contains_marker(exc.doc)
                in_message = contains_marker(str(exc))
                in_traceback = contains_marker(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
            except Exception:
                raise AssertionError('unexpected exception type during synthetic parse') from None
            else:
                self.fail('malformed synthetic input unexpectedly accepted')
        # Characterizes retention as a defect, not a security PASS.
        self.assertTrue(retained_document, 'synthetic document marker was not retained')
        self.assertFalse(in_message, 'synthetic marker detected in exception message')
        self.assertFalse(in_traceback, 'synthetic marker detected in formatted traceback')


if __name__ == '__main__':
    unittest.main()
