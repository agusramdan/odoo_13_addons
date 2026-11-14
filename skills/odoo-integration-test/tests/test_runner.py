import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'scripts' / 'run_integration.py'
spec = importlib.util.spec_from_file_location('runner', path)
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)

class TestRunner(unittest.TestCase):
    def setUp(self):
        self.args = ['--odoo-bin', __file__, '--database', 'integration_test_db', '--addon', 'demo_integration', '--mode', 'update', '--ack-test-db']
    def test_command_and_extra(self):
        cmd, dry = runner.build_command(self.args + ['--', '--config', 'test.conf'])
        self.assertFalse(dry)
        self.assertEqual(cmd[2:7], ['-d', 'integration_test_db', '-u', 'demo_integration', '--test-tags=/demo_integration'])
        self.assertEqual(cmd[-2:], ['--config', 'test.conf'])
    def test_requires_acknowledgement(self):
        with self.assertRaises(SystemExit): runner.build_command(self.args[:-1])
    def test_rejects_production_and_conflicts(self):
        bad = self.args.copy(); bad[3] = 'company_prod'
        with self.assertRaises(SystemExit): runner.build_command(bad)
        with self.assertRaises(SystemExit): runner.build_command(self.args + ['--', '-d', 'prod'])
    def test_failure_propagates(self):
        with patch.object(runner.subprocess, 'call', return_value=3) as call:
            self.assertEqual(runner.main(self.args), 3); call.assert_called_once()
    def test_dry_run_does_not_execute(self):
        with patch.object(runner.subprocess, 'call') as call:
            self.assertEqual(runner.main(self.args + ['--dry-run']), 0); call.assert_not_called()
