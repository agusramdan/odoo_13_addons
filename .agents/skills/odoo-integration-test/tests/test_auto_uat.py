import dataclasses
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'auto_uat.py'
spec = importlib.util.spec_from_file_location('auto_uat', SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def fixture():
    return module.Fixture(candidate='a'*64, current_candidate='a'*64, clean=True,
        spec_hash='b'*64, evidence_refs=('synthetic-ref',), newer_stop=False,
        wrapper='wrapper', expected_wrapper='wrapper', accepted_cases=('case',),
        mapped_cases=('case',), runtime=('synthetic','denied','disabled','disposable','exact-run-owned-only'),
        expected_runtime=('synthetic','denied','disabled','disposable','exact-run-owned-only'),
        ledger_count=0, ledger_limit=1, ledger_locked=True, reset_requested=False,
        owned=True, occupied=False, snapshot=True)


class AutoUATTests(unittest.TestCase):
    def test_positive_is_fake_only(self):
        backend = module.FakeBackend()
        result = module.simulate(fixture(), backend)
        self.assertEqual(result.state, module.State.SIMULATED_PASS)
        self.assertEqual(backend.events, ['launch', 'cleanup'])

    def test_gate_failures(self):
        checks = [({'newer_stop': True}, 'policy'), ({'clean': False}, 'candidate/spec'),
                  ({'spec_hash': ''}, 'candidate/spec'), ({'current_candidate': 'c'*64}, 'candidate/spec'),
                  ({'occupied': True}, 'resources'), ({'owned': False}, 'resources'),
                  ({'ledger_count': 1}, 'ledger'), ({'reset_requested': True}, 'ledger'),
                  ({'ledger_locked': False}, 'ledger'), ({'mapped_cases': ()}, 'cases'),
                  ({'wrapper': 'other'}, 'policy'), ({'snapshot': False}, 'snapshot'),
                  ({'runtime': ('real',)*5}, 'runtime')]
        for changes, stage in checks:
            with self.subTest(changes=changes):
                backend = module.FakeBackend()
                result = module.simulate(dataclasses.replace(fixture(), **changes), backend)
                self.assertEqual((result.state, result.stage), (module.State.BLOCKED, stage))
                self.assertEqual(backend.events, [])

    def test_fake_adapter_forgery_blocked(self):
        class Forged(module.FakeBackend):
            pass
        self.assertEqual(module.simulate(fixture(), Forged()).stage, 'adapter')
        self.assertEqual(module.simulate(fixture(), object()).state, module.State.BLOCKED)

    def test_cleanup_and_zero(self):
        for backend, stage in [(module.FakeBackend(cleanup_ok=False), 'cleanup'), (module.FakeBackend(count=0), 'results')]:
            result = module.simulate(fixture(), backend)
            self.assertEqual((result.state, result.stage), (module.State.SIMULATED_FAIL, stage))
            self.assertEqual(backend.events, ['launch', 'cleanup'])

    def test_secret_not_emitted(self):
        secret = 'sensitive-fixture-value'
        result = module.simulate(dataclasses.replace(fixture(), evidence_refs=(secret,), newer_stop=True), module.FakeBackend())
        self.assertNotIn(secret, repr(result))
        proc = subprocess.run([sys.executable, str(SCRIPT), secret], capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn(secret, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['state'], 'BLOCKED')

    def test_precedence(self):
        sources = {'default': {'x':'d', 'y':'d'}, 'profile': {'x':'p'}, 'accepted': {'x':'a'}, 'instruction': {'x':'i'}}
        self.assertEqual(module.resolve_config(sources, ('x','y','z')), {'x':'i','y':'d'})


if __name__ == '__main__':
    unittest.main()
