"""Offline gate evidence checks; these assert BLOCKED, never acceptance."""
from support import *
import json

REPORTS = pathlib.Path('/home/ubuntu/docs/reports/ADDONS13-27')
ANALYSIS = REPORTS / 'analysis-revision-20261019T062301Z'
LEAD = REPORTS / 'lead-disposition-20261019T063205Z.md'
SECURITY = REPORTS / 'security-read-only-20261019T095501Z/security-review.json'


class SecurityGate(OfflineCase):
    def test_lead_analysis_and_security_are_still_blocked(self):
        analysis = json.loads((ANALYSIS / 'result.json').read_text())
        security = json.loads(SECURITY.read_text())
        lead = LEAD.read_text()
        self.assertFalse(analysis['acceptance'])
        self.assertFalse(analysis['analysis_done'])
        self.assertFalse(analysis['development_ready'])
        self.assertEqual(analysis['gate_status'], 'BLOCKED')
        self.assertIsNone(analysis['candidate_sha'])
        self.assertIn('NOT ACCEPTED for the Analysis → Development gate', lead)
        self.assertIn('candidate SHA is still `PENDING`', lead)
        self.assertEqual(security['verdict'], 'BLOCKED')
        self.assertFalse(security['acceptance_claimed'])
        self.assertFalse(security['gate_promoted'])
        self.assertEqual(security['identity']['candidate_commit_sha'], None)
        self.assertEqual(security['identity']['candidate_sha_status'], 'MISSING')

    def test_owner_residual_risk_acceptance_is_not_reviewer_clearance(self):
        analysis = json.loads((ANALYSIS / 'result.json').read_text())
        security = json.loads(SECURITY.read_text())
        self.assertEqual(set(analysis['security_risks']['owner_accepted_ids']),
                         {f'F{i:02d}' for i in range(1, 10)})
        self.assertFalse(analysis['security_risks']['silent_hardening_allowed'])
        self.assertIn('belum diterima Lead/Security reviewer',
                      analysis['security_risks']['disposition'])
        for risk_id in (f'F{i:02d}' for i in range(1, 10)):
            risk = security['risks'][risk_id]
            self.assertIn(risk['status'], {'OPEN_RESIDUAL', 'ASSESSED_EVIDENCE_PENDING', 'UNPROVEN_BLOCKED'})
            self.assertTrue(risk['required_evidence'])
            self.assertFalse(risk['confirmed_vulnerability'])

    def test_semgrep_findings_are_not_a_security_pass(self):
        security = json.loads(SECURITY.read_text())
        scan = security['semgrep']['target_scan']
        self.assertEqual(security['semgrep']['status'], 'RUN')
        self.assertEqual(scan['command_exit'], 0)
        self.assertGreater(scan['findings'], 0)
        self.assertFalse(security['semgrep']['pass_claimed'])
        self.assertEqual(security['verdict'], 'BLOCKED')

    def test_analysis_report_is_not_candidate_bound(self):
        analysis = json.loads((ANALYSIS / 'result.json').read_text())
        self.assertIsNone(analysis['candidate_sha'])
        self.assertIsNone(analysis['tests']['actual_execution_evidence'])
        self.assertEqual(analysis['tests']['all_case_status'], 'NOT RUN')
        # This is the historical Analysis report, not a claim about the tests
        # executed in this offline Development attempt.
