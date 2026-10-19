"""Offline workflow evidence. Live Plane and remote state are deliberately NOT queried."""
from support import *
import json
import subprocess

REPORTS = pathlib.Path('/home/ubuntu/docs/reports/ADDONS13-27')
ANALYSIS = REPORTS / 'analysis-revision-20261019T062301Z'
UAT = ANALYSIS / 'UAT.md'
BASE_SHA = 'd195390ffc1e5fd6fdb18d4bcd10e7fb1c10be59'


def local_git(*args):
    env = {
        'PATH': '/usr/bin:/bin',
        'HOME': str(ROOT),
        'LANG': 'C',
        'GIT_CONFIG_NOSYSTEM': '1',
        'GIT_CONFIG_GLOBAL': '/dev/null',
        'GIT_NO_LAZY_FETCH': '1',
        'GIT_TERMINAL_PROMPT': '0',
        'GIT_OPTIONAL_LOCKS': '0',
    }
    return subprocess.run(['git', '-c', 'core.fsmonitor=false', *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=20)


class WorkflowGate(OfflineCase):
    def test_local_worktree_is_task_branch_without_candidate_commit(self):
        branch = local_git('rev-parse', '--abbrev-ref', 'HEAD')
        head = local_git('rev-parse', 'HEAD')
        self.assertEqual(branch.returncode, 0, branch.stderr)
        self.assertEqual(head.returncode, 0, head.stderr)
        self.assertEqual(branch.stdout.strip(), 'ADDONS13-29')
        self.assertEqual(head.stdout.strip(), BASE_SHA)
        self.assertEqual(local_git('log', '-1', '--format=%H').stdout.strip(), BASE_SHA)
        status = local_git('status', '--porcelain').stdout.splitlines()
        self.assertTrue(any(line[3:].startswith('tests/') for line in status))
        analysis = json.loads((ANALYSIS / 'result.json').read_text())
        self.assertIsNone(analysis['candidate_sha'])
        self.assertFalse(analysis['acceptance'])
        self.assertFalse(analysis['published'])
        self.assertEqual(analysis['gate_status'], 'BLOCKED')

    def test_required_workflow_order_and_live_readback_provenance(self):
        uat = UAT.read_text()
        analysis = json.loads((ANALYSIS / 'result.json').read_text())
        self.assertIn('Analisis→Development→Deployment→Publish', uat)
        self.assertEqual(analysis['live_readback']['feature_state'], 'Todo')
        self.assertEqual(analysis['live_readback']['development_state'], 'Todo')
        self.assertIn('tidak diverifikasi ulang Analis',
                      analysis['live_readback']['provenance'])
        self.assertFalse(analysis['plane_changed'])
        # Historical readback only; this suite makes no current Plane claim.

    def test_odoo_and_paired_service_gates_are_not_run(self):
        uat = UAT.read_text()
        self.assertIn('U11 — Odoo13 registry', uat)
        self.assertIn('U13 — paired server/service/auth integration', uat)
        self.assertIn('NOT RUN/BLOCKED', uat)

    def test_tests_do_not_call_plane_or_remote_git_apis(self):
        tests = '\n'.join(p.read_text() for p in (ROOT / 'tests/addons13_27').glob('test_U*.py'))
        plane_host = 'plane' + '.agusramdan.web.id'
        remote_command = 'git ' + 'ls-remote'
        self.assertNotIn(plane_host, tests)
        self.assertNotIn(remote_command, tests)
