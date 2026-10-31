# Independent static QA — Step0 v3.1

## Verdict

**PASS — static draft/review readiness. HOLD — unconditional approval, implementation, runtime acceptance and release.** Candidate binding, exact artifact hashes, 12 AC / 24 UAT coverage, all-NOT-RUN status and the 12 proposed safety assertions are internally consistent. No implementation/runtime result is established. Owner must decide M1, D-EX and D-GLOBAL; review readiness is not acceptance of those proposals.

Scope: read-only local Git/source/evidence inspection, host text/JSON/AST/hash checks only. No addon import, SDK execution, product tests, containers, installation, network lookup, ref updates, Plane changes, commit or push. Only this new report was written, outside the repository. Existing accepted artifacts and superseding drafts were not edited.

## Exact identity and artifacts

| Item | Independently observed |
|---|---|
| Worktree | `/home/ubuntu/worktrees/ADDONS13-64` |
| Branch / HEAD | `ADDONS13-64` / `4c39fd76cb3818f0fd29cd8c7738fb647e85fde5` |
| Initial/final tracked and untracked status | `git status --porcelain=v1` empty on both reads |
| Historical product source | `6a51c81493b339c67fb97c6615a3e7d758c60251` |
| Intervening diff | Only `AGENTS.md`; no product-source changes |
| Local tracking feature / target | `origin/ADDONS13-64=6a51c81493b339c67fb97c6615a3e7d758c60251`; `origin/main=ac1bcbd66261b92c10078f2a8744a657a3b6490c` |
| PRD SHA-256 | `cf17ac528211a9661f35c1d1c4561937a7d48f41a68a0236b8e1b6c769424f5f` |
| UAT SHA-256 | `508da8bd2bc6ed6d1f6f98568a2e61418d204750152a8a21f59b3620579eb81e` |

Both computed hashes exactly match `REBIND-v3.1.json` and the supplied review identity. This QA read local tracking refs only; the drafts' live-remote assertions remain Lead provenance, not an independent remote check here. AGENTS attribution/authorization remains unknown and was not inferred from a clean tree. No push authorization is implied.

Every non-AGENTS source-blob SHA-256 in `SOURCE-EVIDENCE.json` matches the committed current candidate. The old candidate fields in SOURCE-EVIDENCE/TRACEABILITY are explicitly preserved prebinding provenance; REBIND-v3.1 plus the two v3.1 drafts govern this review. Do not treat those old fields as current implementation/UAT identity. Historical RESULT, QA-EXPERIMENT and the four cited SDK consts/client/scope/api files also match their recorded evidence hashes.

## Programmatic checks actually performed

Host Python parsed the documents and JSON (without executing repository or SDK code):

- Exactly **12 unique AC IDs**, **24 unique UAT case headings**, and **24 explicit `Status: NOT RUN`** entries.
- Exactly **35 AC↔UAT edges**. PRD forward mapping equals case-level reverse mapping; every AC has cases and all 24 cases are covered.
- TRACEABILITY AC mapping equals the PRD. All 24 machine-readable cases match the UAT document's AC references, preconditions, steps, expected oracle, gate and status. Field mismatches: **0**. JSON NOT RUN cases: **24**.
- Restricted extraction of the profile's JSON-compatible scalar/list literals equals `safe_profile_proposal`, including exact Python value types: **12 assertions**. This restricted check is **not** YAML parsing.
- Full YAML parser check: **NOT RUN**. Host `import yaml` returned `ImportError`; no package was installed and no runtime/container was used to compensate. The snippet was visually inspected; no syntax defect was identified, but it is not recorded as parser-verified. UAT-21 still requires actual YAML/JSON example parsing.
- SDK constructor AST inspection confirms all 12 key names exist in SDK2.73's keyword-only `ClientConstructor.__init__` signature (`sdk273-consts.py:1376–1449`); `enable_logs` default is `False`. This is API-name/default evidence, not proof of effective privacy or hook-only behavior.

### Exact profile checked

| Assertion | Required value/type |
|---|---|
| default_integrations | boolean false |
| auto_enabling_integrations | boolean false |
| integrations | empty list |
| include_local_variables | boolean false |
| include_source_context | boolean false |
| send_default_pii | boolean false |
| max_request_body_size | string `never` |
| max_breadcrumbs | integer 0, not boolean false |
| auto_session_tracking | boolean false |
| send_client_reports | boolean false |
| enable_metrics | boolean false |
| debug | boolean false |

`dsn` is separate from the 12 assertions. Optional environment/release/server_name/project_root strings are separate metadata. The narrow allowlist excludes arbitrary SDK kwargs and `enable_logs`; no nested data_collection, custom scrubber, SDK downgrade or Hub redesign is silently introduced. Active files must supply all assertions; unsafe/missing values are rejected before init, not repaired/injected. Disabled/none omissions do not activate anything. This is a **proposed breaking validation delta**, not present validated behavior in current config.py.

## Source correctness, privacy and claim boundaries

PASS, with unresolved product gates preserved:

1. Current config.py parses path/mappings/policy but does not yet enforce M1's sentry allowlist/profile. runtime.py is import-time/process-wide; reporting calls global SDK capture APIs after sdk.init. The draft correctly labels M1 as a proposal requiring separate approval and implementation.
2. The historical minimal-config experiment establishes outside-hook logging and privacy FAIL, not failure of the unexecuted safe profile. Header/body/credential marker presence in envelopes does not establish raw HTTP forwarding: locals/message can carry the same markers. The draft states this distinction and retains bounded ORM/transport/cleanup limitations.
3. Locals/source/body/PII flags do not promise arbitrary exception messages, chained causes or path/URL text are secret-free. D-EX remains OPEN. UAT-12 separates non-text channels; UAT-13 evaluates original exception residuals. No exception-text PASS is claimed.
4. SDK scope `_merge_scopes` (`sdk273-scope.py:425–460`) copies global, isolation and current scopes; `get_client` (`463–495`) selects ambient clients. Disabling integrations does not isolate metadata/processors/routing or defeat another SDK initialization. D-GLOBAL and UAT-14/18 explicitly retain FAIL/HOLD or a separately reviewed design if exclusivity cannot satisfy the oracle. No fresh-scope safety guarantee is asserted.
5. Explicit metadata fixtures, real-SDK envelope/integration tests, persisted dispatch/log/action evidence, outside-hook unhandled exceptions, separate capture failures, exact Python3.7.3, no-egress and volume-ID cleanup remain future checks. Historical L1/install smoke is not promoted into these 24 UAT cases.
6. Owner-selected legacy A/Requests adjustment remains sandbox-only. No production pin/security waiver, automatic integrations, kwargs selected fallback, legacy tags, major-version migration or ref/tracker/deploy action is authorized by this review.

## Concrete document clarifications before a frozen acceptance revision

No structural count/hash/source-binding defect was found. Two small wording fixes are recommended; neither requires a product redesign:

- **PRD line 113, G0:** replace `Owner menerima exact hashes v3` with `Owner menerima exact hashes PRD-v3.1-DRAFT.md dan UAT-v3.1-DRAFT.md dalam REBIND-v3.1.json`. The current header/rebind is clear, but the operative approval sentence still names v3. Regenerate hashes/rebinding if edited; do not edit the reviewed artifacts in place under their old identity.
- **UAT-12 oracle (line 132), and matching TRACEABILITY case:** replace `off/absent client nol` with `selected + opted-out/absent client => nol; all/error mengikuti matriks UAT-08 tanpa syarat opt-in`. Context suggests selected, but an unqualified reading would contradict all/error eligibility in PRD section 3. Preserve the zero-private-marker and per-channel attribution oracle.

YAML parser verification remains explicitly NOT RUN, not a fabricated PASS and not evidence the snippet is invalid. Obtain it before claiming example parsing is verified.

## Owner decisions and gates still required

- **M1:** accept/reject the breaking active-file validation and narrow allowlist; approve exact current or revised document hashes. Approval alone does not authorize implementation/runtime.
- **D-EX:** choose EX-A with specifically bounded text/path residual acceptance, or EX-B strict zero-data requiring a separately approved telemetry contract redesign. Do not convert historical privacy FAIL to PASS by waiver.
- **D-GLOBAL:** decide whether an exclusive process/deployment eligibility constraint is acceptable, including worker/multi-DB boundaries. Prove it under the approved oracle; otherwise HOLD and request a separate adapter design. Exclusivity is not a claim that the current global API rejects hostile ambient SDK mutations.
- Separate bounded implementation and test-only sandbox authorization, new remediation SHA/rebinding, full per-case QA evidence, and production advisory/security/release decisions remain mandatory.

**Bottom line:** approval-review-ready static draft, with the two precise clarifications above recommended before freezing a new accepted revision. Not approved; not implementation-ready by authorization; all **24 UAT cases remain NOT RUN**. D-EX/D-GLOBAL are substantive Owner gates, not defects that the 12 safety assertions can independently solve.
