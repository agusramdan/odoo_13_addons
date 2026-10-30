import os
import unittest
import xml.etree.ElementTree as ET


class TestOidcAlgorithmCatalogSeed(unittest.TestCase):
    def test_xml_seeds_only_supported_rs256_algorithm(self):
        addon_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(addon_root, 'data', 'oidc_algorithms.xml')
        root = ET.parse(xml_path).getroot()

        records = root.findall('.//record')
        self.assertEqual(len(records), 1, 'expected exactly one algorithm seed record')
        record = records[0]
        self.assertEqual(record.get('id'), 'algorithm_rs256')

        fields = dict((field.get('name'), field.text) for field in record.findall('field'))
        self.assertEqual(fields.get('name'), 'RS256')
        self.assertEqual(fields.get('key_family'), 'RSA')
        self.assertEqual(fields.get('min_key_bits'), '2048')
        self.assertEqual(fields.get('purpose'), 'access_token_verification')
        self.assertEqual(fields.get('support_state'), 'supported')
