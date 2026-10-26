# ADDONS13-48 — UAT Execution Record r3 (latest-main candidate)

Date: 2026-10-26 (CST)

## Candidate and approvals

- Candidate worktree: `/home/ubuntu/worktrees/ADDONS13-48-step4-current-main-bc41f9e` (detached; no branch or commit created).
- Base: current `origin/main` at `bc41f9e3b76bf3519e77d43bd6ee4fbd7eac2207`.
- Source/test diff SHA-256 against that base: `8de59edc1e167386ef5d5177df9642d1eb2ca07e43508ba24dbb2dce6598fd43`.
- `bc41f9e` changes only `amr_service_client` files; it does not overlap the candidate. The `amr_oidc` manifest depends on `base`, `web`, and `amr_token`, not `amr_service_client`. The two changed Python base blobs at `bc41f9e` are byte-identical to those at `95dbf36`; the changed Python candidate files and source/test patch are also byte-identical to the previously reviewed inputs.
- PRD r8 and UAT r7 retain their historical Owner-approved Step 0 provenance at branch `ADDONS13-48`, HEAD `b1399abf3bcc0031983a39761d5b7d34850f59f5`. That approval snapshot is not being relabeled as the current code candidate base; this record binds execution to `bc41f9e`.
- Step 2 reviewer accepted the identical source/test diff. The accepted Semgrep 1.181.0 scan (`p/python` and `p/owasp-top-ten`, metrics disabled) reported one existing unverified-JWT-decode finding at `amr_oidc/models/oidc_client.py:174`; baseline and candidate findings were identical, with no scan errors or new finding. No rescan was needed after porting because the changed Python files and both base blobs are byte-identical to the reviewed scan inputs.
- Owner PR_ACCEPT and commit/push/PR/merge authorization were previously given for the prior `95dbf36` candidate. Before any branch or commit was created, the remote `main` advanced to `bc41f9e`. No branch, commit, push, or PR was created for that prior approval. This updated candidate uses the latest base and its own execution evidence; the prior PR_ACCEPT is not treated as approval of this revised manifest. Obtain Owner PR_ACCEPT for the exact candidate before Step 4 writes.

## Post-review execution on this base

Runtime: `addons13-48-odoo13-test:local`, network `addons13-48-test-net`; disposable PostgreSQL service `addons13-48-test-db`; candidate mounted read-only. Both runs used fresh databases, `--init=amr_oidc --test-enable --stop-after-init`, and `--log-level=test`.

- Focused selector `/amr_oidc:TestOidcHelperDecode`: exit 0; 12 tests started and ran, no failure/error test records. DB `addons13_48_bc41f9e_focused_6dcb4a76` was dropped; exact-name PostgreSQL readback count 0. Log: `/home/ubuntu/.hermes/profiles/lead/cache/scratch/addons13_48_bc41f9e_focused_6dcb4a76.log`.
- Full addon selector `/amr_oidc`: exit 0; 42 tests across 9 groups (7 + 5 + 12 + 4 + 2 + 3 + 6 + 1 + 2), no failure/error test records. DB `addons13_48_bc41f9e_full_addon_916f6785` was dropped; exact-name PostgreSQL readback count 0. Log: `/home/ubuntu/.hermes/profiles/lead/cache/scratch/addons13_48_bc41f9e_full_addon_916f6785.log`.
- `git diff --check` and `python3 -m py_compile amr_oidc/tests/test_helper_decode.py` passed in this candidate worktree.

## UAT disposition and evidence limits

UAT-01 through UAT-09 are PASS per the approved case mapping in UAT r7; UAT-04's separate verified-issuer-mismatch subcase remains Owner-approved structural N/A because selector and verifier consume the same signed `iss` claim. UAT-01's assertion that other unverified claims do not select the profile and UAT-05's no-retry conclusion beyond instrumented wrong-key/disallowed-audience failures include source-review conclusions; the tests instrument those critical rejection paths but not every possible failure path.

A prior Odoo-native `amr_resource` run had a separate `TestResourceHelper.test_ut06_verified_jwt_and_failures` logger assertion failure during fixture/audit setup. It is not represented as passing and is outside the `/amr_oidc` suite result above.

## Scope and gate boundary

- The candidate changes only `amr_oidc/models/oidc_client.py`, `amr_oidc/tests/test_helper_decode.py`, PRD r8, UAT r7, and this execution record. No grant/token-issuance changes and no `amr_token` changes.
- This records Step 3 verification for the detached latest-main candidate. No commit, push, PR creation, merge, deployment, release approval, or Plane state transition is included. Step 4 requires Owner PR_ACCEPT for the exact updated candidate.
