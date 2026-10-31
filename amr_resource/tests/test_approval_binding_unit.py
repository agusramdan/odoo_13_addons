"""Offline synthetic tracer, not an approved global canonical schema.

Proposed internal tracer wire format: ASCII magic plus NUL, then four
unsigned 32-bit big-endian length-prefixed byte strings: domain, UTF-8 key
version, UTF-8 environment, and opaque payload. Domains are b'plan' and
b'inventory'. Production verification must compare MACs in constant time.
No input in these fixtures is a real secret or production payload.
"""
import copy
import hashlib
import hmac
import importlib.util
from pathlib import Path
import unittest


KEY = b'synthetic-test-key-not-for-production'
OLD_KEY = b'synthetic-old-key-not-for-production'
VERSION = 'synthetic-v1'
ENVIRONMENT = 'synthetic-env-a'
PLAN = b'synthetic plan: sensitive value'
INVENTORY = b'synthetic inventory: row active'


def framed(domain, version, environment, payload):
    fields = (domain, version.encode('utf-8'), environment.encode('utf-8'), payload)
    return b'AMR-APPROVAL-TRACER\x00' + b''.join(
        len(field).to_bytes(4, 'big') + field for field in fields)


def make_approval(key=KEY, version=VERSION, environment=ENVIRONMENT):
    def mac(domain, payload):
        return hmac.new(key, framed(domain, version, environment, payload),
                        hashlib.sha256).digest()
    return {'key_version': version, 'environment': environment,
            'plan_mac': mac(b'plan', PLAN),
            'inventory_mac': mac(b'inventory', INVENTORY)}


def load_eligible():
    path = Path(__file__).resolve().parents[1] / '_approval_binding.py'
    if path.is_file():
        spec = importlib.util.spec_from_file_location('approval_binding_tracer', str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module._approval_eligible
    # A missing feature is fail-closed; valid approvals remain ineligible.
    def missing(approval, plan, inventory, key, key_version, environment):
        return False
    return missing


class ApprovalBindingUnitTests(unittest.TestCase):
    def test_explicit_wire_and_mac_vectors(self):
        vectors = (
            (b'plan', PLAN,
             '414d522d415050524f56414c2d5452414345520000000004706c616e'
             '0000000c73796e7468657469632d76310000000f73796e7468657469632d656e762d61'
             '0000001f73796e74686574696320706c616e3a2073656e7369746976652076616c7565',
             'a14491e2f780336294e4dc8b224d3cba84b61c9b3ebb437433a75788ce921e92'),
            (b'inventory', INVENTORY,
             '414d522d415050524f56414c2d5452414345520000000009696e76656e746f7279'
             '0000000c73796e7468657469632d76310000000f73796e7468657469632d656e762d61'
             '0000001f73796e74686574696320696e76656e746f72793a20726f7720616374697665',
             '07197fb4080e46d0212ade0b1087e45f060aa374abb3c84becc7bcfb38a7a299'),
        )
        for domain, payload, expected_bytes, expected_mac in vectors:
            with self.subTest(domain=domain):
                message = framed(domain, VERSION, ENVIRONMENT, payload)
                self.assertEqual(message.hex(), expected_bytes)
                self.assertEqual(hmac.new(KEY, message, hashlib.sha256).hexdigest(), expected_mac)

    def test_valid_approval_and_rotation_old_key_remain_eligible(self):
        eligible = load_eligible()
        for key, version in ((KEY, VERSION), (OLD_KEY, 'synthetic-old-v0')):
            with self.subTest(version=version):
                approval = make_approval(key, version)
                before = copy.deepcopy(approval)
                self.assertTrue(eligible(approval, PLAN, INVENTORY, key, version, ENVIRONMENT))
                self.assertEqual(approval, before)

    def test_rejects_replay_tampering_and_malformed_tags(self):
        eligible = load_eligible()
        approval = make_approval()
        before = copy.deepcopy(approval)
        cases = [
            ('changed plan', approval, b'changed plan', INVENTORY, KEY, VERSION, ENVIRONMENT),
            ('changed inventory', approval, PLAN, b'changed inventory', KEY, VERSION, ENVIRONMENT),
            ('missing key', approval, PLAN, INVENTORY, None, VERSION, ENVIRONMENT),
            ('wrong key', approval, PLAN, INVENTORY, OLD_KEY, VERSION, ENVIRONMENT),
            ('stored version mismatch', approval, PLAN, INVENTORY, KEY, 'synthetic-v2', ENVIRONMENT),
            ('missing version', approval, PLAN, INVENTORY, KEY, None, ENVIRONMENT),
            ('stored environment mismatch', approval, PLAN, INVENTORY, KEY, VERSION, 'synthetic-env-b'),
            ('missing environment', approval, PLAN, INVENTORY, KEY, VERSION, None),
            # Matching relabel and expected context still must fail: MAC covers labels.
            ('version relabel', dict(approval, key_version='synthetic-v2'), PLAN, INVENTORY,
             KEY, 'synthetic-v2', ENVIRONMENT),
            ('environment relabel', dict(approval, environment='synthetic-env-b'), PLAN, INVENTORY,
             KEY, VERSION, 'synthetic-env-b'),
            ('swapped tags', dict(approval, plan_mac=approval['inventory_mac'],
                                  inventory_mac=approval['plan_mac']),
             PLAN, INVENTORY, KEY, VERSION, ENVIRONMENT),
        ]
        for tag in ('plan_mac', 'inventory_mac'):
            for malformed in (None, b'', b'\x00' * 31, b'\x00' * 33, 'not-bytes'):
                cases.append(('malformed ' + tag, dict(approval, **{tag: malformed}),
                              PLAN, INVENTORY, KEY, VERSION, ENVIRONMENT))
        for label, candidate, plan, inventory, key, version, environment in cases:
            with self.subTest(case=label, candidate=candidate):
                candidate_before = copy.deepcopy(candidate)
                self.assertFalse(eligible(candidate, plan, inventory, key, version, environment))
                self.assertEqual(candidate, candidate_before)
        self.assertEqual(approval, before)
