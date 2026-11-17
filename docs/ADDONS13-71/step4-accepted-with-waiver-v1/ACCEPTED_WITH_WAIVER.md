# ADDONS13-71 — Step 4 disposition

**Disposition: ACCEPTED_WITH_WAIVER**
**Decision:** Owner’s instruction on 2026-11-17 was: “Commit dan push; untuk AU13 dan AU14 buat Task feature terpisah; Accept_with_skip; step 4 done ; PR open; task done.”
**Scope:** Waive only the baseline-comparison portions of AU13 and AU14. This is a gate disposition, not acceptance of the underlying provider-compatibility risk.

## Accepted artifacts and candidate identity

- Accepted PRD v6 SHA-256: `3d724eb1fffd74cf6532f7aa67c456c2fb74e231f6afecaab92a5f534c86225d`
- Accepted UAT v6 SHA-256: `3501f674678c83b35a0439285dcc99fe160921003379c3d3eaa54074e3684725`
- Source base: `f28d6053f87cf71c9e87584e4d39909c697f1331`
- Native test snapshot: `f28d605-step4-prep-v5`
- Candidate test manifest SHA-256: `c092c83f6052475570dea2ec62b0579b007b954e864908df3b25e475e655ae54`
- Snapshot tree manifest SHA-256: `44f430150e825a24278657841005ff09cd80fbb8befac8e2663da64072f0e4b0`
- Runtime: Odoo 13 / CPython 3.7.3; synthetic data; disposable database; transport mocked; no host ports or production database.
- Odoo image ID: `sha256:2dfed693791e137016a1dd74cb4f370bd0bbdff0910584311141f729d00c1bba`
- PostgreSQL image ID: `sha256:b2baf8998630663d21370da06387c950e587071bdd307ee34e661cdcc7442bcc`
- Dependency-lock SHA-256: `006fb0156bed9e05672570e91160b92915b0ef7e23a3f28fdd9d7b0eea758706`

The five test/discovery files in the native snapshot match the committed-source base plus the test overlay byte-for-byte. Snapshot file SHA-256 values:

- `amr_service_client/tests/__init__.py` — `8f2df9036b59d7286473611f1822d30e21397cae1c0821ab999e676fa7b42fe6`
- `amr_service_client/tests/integration/test_i06_log.py` — `5b142e3a6f7c7418fff9571a869763238a96b9937ef013b54863576207635333`
- `amr_service_client/tests/integration/test_uat_addons13_71_logging.py` — `309db518aa919f2887b6219f7d16f58a5f2a0f13222b3040565fd8691060de12`
- `amr_service_client/tests/integration/test_uat_addons13_71_refactor.py` — `d995ac272d3d34e1e8aa26f5e3ca7f9ad7e5532b3f0dd6113085a85819d34792`
- `amr_service_client/tests/integration/test_uat_addons13_71_url_headers.py` — `734d4ff35a0d6104baeff8a83ad6fe5710da7b99c18bc80376af19353ee9770d`

## Raw execution results

- **Attempt 1 — FAIL / incomplete:** 54 test methods started; 1 failure and 2 errors. The preserved report is `docs/reports/ADDONS13-71/step4-testprep-f28d605/ATTEMPT-1-RESULTS-2026-11-17.md`; the private raw log remains in the task UAT state directory. This result is not rewritten or counted as a pass.
- **Attempt 2 — candidate suite passed:** 54 test methods started; 0 failure/error records; task-scoped runner exited 0. Private raw log: `/home/ubuntu/.hermes/uat-state/ADDONS13-71/ADDONS13-71-amr_service_client-904d7a7c2afc4000ac4aa27e5514d53e.log` (mode 0600).
- Two of the three authorized attempts were consumed. No third attempt was made; the remaining attempt is not needed for the Owner-waived comparisons.

## Waived points and follow-up Features

| Point | Candidate-side actual | Baseline comparison | Disposition | Follow-up |
|---|---|---|---|---|
| AU13 — strict provider reads `context['headers']` when headers are falsy/absent | Ran without a recorded failure/error in attempt 2 | NOT RUN | ACCEPTED_WITH_WAIVER | Plane Feature `ADDONS13-99`, UUID `73b554f3-1c82-49c4-9a1b-5862851f3220` |
| AU14 — strict provider reads `context['url']` when URL is falsy/absent | Ran without a recorded failure/error in attempt 2 | NOT RUN | ACCEPTED_WITH_WAIVER | Plane Feature `ADDONS13-100`, UUID `5598fc44-abda-479b-959c-b5b48c5686c8` |
| F15 — aggregate cross-acceptance regression gate | Candidate suite ran: 54 methods, no failure/error records | Baseline portions of AU13/AU14 remain NOT RUN | ACCEPTED_WITH_WAIVER, not PASS | Tracked by the two Features above |

The Owner’s disposition waives these missing comparisons for ADDONS13-71’s Step 4 only. It does not establish backward compatibility for every custom provider, accept the residual risk, authorize follow-up implementation/runtime work, or change any raw execution result. Follow-up Feature creation is tracking only; each remains in Backlog with Step 0 pending.

## Handoff boundary

Step 4 is accepted with the scoped waiver. The PR must be opened and its URL/head SHA recorded on the source Plane Feature before marking that task Done. PR review/acceptance, merge, release, and deployment remain separate and are not authorized by this disposition.
