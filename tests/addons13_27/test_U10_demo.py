"""Safety checks for the documentation-only synthetic demo fixture."""
from support import *
import ast
import ipaddress
import json
import re
from urllib.parse import urlsplit


FIXTURE = ROOT / 'docs/examples/service-client-demo.json'


class Demo(OfflineCase):
    def fixture(self):
        self.assertTrue(FIXTURE.is_file())
        return json.loads(FIXTURE.read_text())

    def test_three_objects_and_alias_relationships_are_closed(self):
        demo = self.fixture()
        self.assertIs(demo['synthetic'], True)
        self.assertIs(demo['auto_load'], False)
        self.assertIs(demo['live_call'], False)
        self.assertEqual(demo['format'], 'documentation_metadata_not_installable_orm_data')
        objects = demo['objects']
        self.assertEqual([o['type'] for o in objects], ['Endpoint', 'Credential', 'Service Client'])
        self.assertEqual(len({o['alias'] for o in objects}), 3)
        endpoint, credential, client = objects
        self.assertEqual(endpoint['credential_alias'], credential['alias'])
        self.assertEqual(client['endpoint_alias'], endpoint['alias'])
        self.assertEqual(client['credential_alias'], credential['alias'])
        self.assertIsNone(credential['credential_json'])
        self.assertIs(credential['credential_material_present'], False)
        self.assertEqual(client['model_reference'], 'MODEL_SYNTHETIC_OWNER_APPROVED')
        self.assertIs(client['active'], False)
        self.assertIs(client['active_log'], False)

    def test_no_secret_pii_or_live_host_material(self):
        demo = self.fixture()
        forbidden_key = re.compile(r'(^|[_-])(password|private.?key|api.?key|access.?token|secret|authorization)([_-]|$)', re.I)
        email = re.compile(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b')
        phone = re.compile(r'(?<!\w)\+?\d[\d ().-]{7,}\d(?!\w)')
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        def visit(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertFalse(forbidden_key.search(str(key)), f'forbidden key: {key}')
                    if key == 'credential_json':
                        self.assertIsNone(item)
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
            elif isinstance(value, str):
                self.assertIsNone(email.search(value))
                self.assertIsNone(phone.search(value))
                for match in ip_pattern.findall(value):
                    ipaddress.ip_address(match)
                    self.fail('IP literals are not allowed in demo metadata')
        visit(demo)
        endpoint = demo['objects'][0]
        parsed = urlsplit(endpoint['base_url_value'])
        self.assertEqual(parsed.scheme, 'https')
        self.assertTrue(parsed.hostname.endswith('.invalid'))

    def test_fixture_is_not_install_or_runtime_input(self):
        manifest = ast.literal_eval((ADDON / '__manifest__.py').read_text())
        self.assertNotIn('demo', manifest)
        self.assertFalse(any('service-client-demo.json' in str(item) for item in manifest.get('data', [])))
        runtime_files = [p for p in ADDON.rglob('*') if p.is_file() and p.suffix in {'.py', '.xml', '.csv'}]
        for path in runtime_files:
            self.assertNotIn('service-client-demo.json', path.read_text(), str(path))
