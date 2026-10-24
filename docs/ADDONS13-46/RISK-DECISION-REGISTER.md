ADDONS13-46 — RISK / DECISION REGISTER 05 — DRAFT

status=DRAFT; acceptance=false; fresh_lead_review=PENDING
step0_gate=PENDING_LEAD_REVIEW; step1_reassessment=PENDING; Step 2–4=PENDING
DB/QA/runtime/apply/cutover/prod: NOT AUTHORIZED / NOT RUN.

Referensi normatif: [PRD](PRD-DRAFT.md), [UAT](UAT-DRAFT.md), [scope addendum](DECISION-ADDENDUM-OWNER-SCOPE-DEFER-05.md), [revision note](REVISION-NOTE.md), [RESULT](RESULT.json).
Sumber per-risk historis yang diwarisi lengkap: [accepted register Rev.04](../analysis-20261024T133315+0800-analis-global-registry-decisions-04/RISK-DECISION-REGISTER.md). Pointer ke §3/baseline T:/blob di sana tetap provenance historis, tidak diatribusikan sebagai temuan current candidate. Revisi ini mempertahankan semua 21 risk IDs, mengganti hanya scope/trace migrasi dan pemisahan evidence historis vs acceptance sekarang. Tidak menghapus risiko atau mengubah raw evidence.

1. Field/semantik bersama, tidak ada blanket clearance

Semua risiko severity UNASSESSED; status OPEN / NOT ACCEPTED. Owner residual-risk decision per item: NO RESIDUAL RISK ACCEPTANCE. Lead disposition per item untuk revisi 05 PENDING fresh hash-bound review; security reviewer UNASSIGNED, review PENDING / NOT RUN. Owner/reviewer individu tidak diasumsikan ditugaskan oleh penyebutan role. Candidate untuk acceptance/final scope current PENDING; reported execution candidate 309c2d883b3475089e70567c3599b7a1858c57e1 bukan accepted candidate. Target ADDONS13-57 candidate PENDING. Common fields ini berlaku pada setiap blok di bawah bersama field eksplisit; historical Lead per-ID decisions Rev.04 tetap di [immutable disposition](../lead-dispositions/lead-disposition-20261024T134745+0800/LEAD-DISPOSITION.md), bukan fresh acceptance paket ini.

R-M01/R-M02/R-M03 DEFERRED_TO_FEATURE ADDONS13-57, OPEN / NOT ACCEPTED, bukan CLOSED/waived/accepted. Owner mengatakan belum production/tidak terlalu dikhawatirkan hanya alasan scope, tidak menyatakan migration safe atau actual DB contents berubah. Actual inventory/markers/duplicates UNKNOWN, NOT RUN; tidak mengarang no-conflict finding.

Current non-migration risk controls tetap di ADDONS13-46; target migration references bukan alasan menghapus global invariants/active-company authorization/security/access/HTTP/ACL/current model requirements. Risiko baseline R-LOG-01/R-SCOPE-01/R-SU-01/R-CALLKW-01 tetap undispositioned residual, tidak diperluas diam-diam menjadi coding task atau accepted karena out-of-delta. Masing-masing tetap memerlukan Lead/Owner/Security disposition sesuai gate.

2. Evidence registry dan provenance

EV-S0-LEAD: exact new PRD/UAT/addendum/register/revision/RESULT hashes + fresh per-risk review dan Step 1 scope reassessment PENDING, acceptance=false.
EV-OWNER-SCOPE-05: exact Owner decision dalam addendum tercatat sebagai scope provenance, bukan test/waiver/risk acceptance; timestamp/message ID tidak tersedia.
EV-OPN01 / EV-OPN02: OWNER_SELECTION_RECORDED O-04/O-05 pada predecessor; OPN-01/02 CLOSED_BY_EXPLICIT_OWNER_DECISION. Tidak diminta ulang, bukan implementation/test evidence.
EV-S1-UNIT: historical recorded full offline Python 3.7.9 76/76 PASS, exit0, candidate 309c2d883b3475089e70567c3599b7a1858c57e1; [Developer raw report](../developer-step1-20261024T1413+0800/REPORT.md) tetap STEP1_VERDICT=NOT_PASS predecessor scope. Test IDs/command/digests/mock limits tersedia di report, bukan acceptance individual UAT. User menyatakan Lead independent full-suite verification SHA sama; tidak ada run/replay Analis atau local raw Lead run artifact ditemukan lewat pencarian reports. Tidak menjadikan per-risk mitigation verified atau gate accepted.
EV-S2-GENERAL: independent general/scope/provenance exact candidate review PENDING / NOT RUN.
EV-S2-SEC: manual security exact candidate+code/context/config revision, reviewer UNASSIGNED, PENDING / NOT RUN; bagian unified Code Review.
EV-S2-SCAN: offline Semgrep exact candidate, tool/ruleset/version/command/findings/triage PENDING / NOT RUN; exit0 bukan verdict otomatis.
EV-S2-RESIDUAL: per-ID baseline-vs-delta dan explicit Owner residual disposition PENDING, tidak ada waiver.
EV-TARGET: separately authorized isolated Odoo13/Python3.7.9 runtime/dependencies/module/MRO/DB/runner target PENDING / NOT RUN; unit container tidak mengganti target proof.
EV-S3-UAT: current acceptance cases NOT RUN; UAT-24/29 DEFERRED / NOT RUN, no authorization dari deferral.
EV-M01: ADDONS13-57 actual inventory active/archived/selectors/resolved references/markers/revisions UNKNOWN / NOT RUN, owner administrator data UNASSIGNED; separate authorization required.
EV-M02: ADDONS13-57 canonical config/user/identical duplicate disposition OWNER_PENDING_CONDITIONAL jika actual conflicts ditemukan; decision owner/data steward UNASSIGNED, no auto-choice.
EV-M03: ADDONS13-57 target-specific schema/metadata/upgrade/apply order/atomicity/backup-restore rehearsal PENDING / NOT RUN; operator/Developer/Lead assignment UNASSIGNED.
EV-APPLY-PLAN: ADDONS13-57 accepted exact target plan + known-good tuple + authorization/readback for apply/cutover/prod NOT AUTHORIZED / NOT RUN; bukan Development gate baru.

3. Per-risk current Feature — semua mandatory common fields bagian 1 berlaku

RISK R-GLOBAL-01 — Shared global trust blast radius / tenant separation
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-GLOBAL-01, PRD §8/Owner-02/global historical blob; inherited static/document, bukan exploit/runtime finding baru.
Owner design/scope: global trust/config O-01/O-02, active-company eligibility D-06 tetap; bukan shared tenant authorization.
Action/accountable role: Developer pertahankan global lookup/config, D-06 tiap request/switch; trust admin least privilege/audit; Lead per-ID blast-radius disposition. Individu UNASSIGNED.
Target gates: Step 1 reassessment; Step 2 review; separately authorized Step 3; apply/deployment tidak diberikan.
AC: AC-01, AC-09, AC-10, AC-12, AC-16
UAT: UAT-16, UAT-17, UAT-19, UAT-20, UAT-24, UAT-25, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: missing candidate-bound review/tenant enforcement evidence holds relevant gate; migration deferral tidak waive invariants.

RISK R-BIND-01 — Exact global identity collision/mismatched mode
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-BIND-01, historical helper/PRD D-05; inherited static/document, current ORM unverified.
Owner design/scope: one exact global pair→user, no email/login/auto-binding; semua mode konsisten binding.
Action/accountable role: Developer unique including archived/mode-result comparison/reject ambiguity, administrator audited bindings; Lead review. Individu UNASSIGNED.
Target gates: Step 1/2/3 current identity constraints; legacy inventory/reconciliation hanya R-M02 target.
AC: AC-09, AC-12, AC-16, AC-17
UAT: UAT-19, UAT-23, UAT-24, UAT-25, UAT-26, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: mocks bukan DB uniqueness proof; no current subject fallback/alternative permitted. EV-M02 contextual dependency only, not current completion gate.

RISK R-RESOLVER-01 — Fixed-user privilege / ORM dispatch / eligibility
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-RESOLVER-01/historical helper and D-06; static/document only.
Owner design/scope: typed single internal active non-superuser/non-public/non-portal user, current-company membership, code-owned allowlist, no implicit sudo/mode fallback.
Action/accountable role: Developer enforce dispatcher/result/current request checks, Reviewer/Security privilege analysis; individuals UNASSIGNED.
Target gates: Step 1/2/3; relevant missing controls/review blocks gate, no claim consumer privilege residual fixed.
AC: AC-12, AC-13, AC-14, AC-16
UAT: UAT-19, UAT-20, UAT-21, UAT-23, UAT-25, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: actual eligibility/allowlist/provenance must be reviewed/proven, migration scope change irrelevant to these requirements.

RISK R-PYTHON-01 — Stored Python executable capability
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-PYTHON-01/D-07 historical design, no sandbox test/exploit claim.
Owner design/scope: disabled v1; edit not activation, safe_eval not sandbox.
Action/accountable role: Developer enforce non-execution/role separation/audit; Owner separate future enable decision+control/threat model; Security UNASSIGNED exact revision review.
Target gates: Step 1/2/3 current disable/audit; activation outside v1.
AC: AC-12, AC-15
UAT: UAT-22, UAT-23, UAT-24
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: execution/activation without explicit separate authority blocked; unit PASS never arbitrary-code safety.

RISK R-LOG-01 — Baseline raw-token logging
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-LOG-01; historical T:amr_resource/models/helper.py:117–121 base dae519..., not candidate verification.
Owner design/scope: no implicit baseline fix scope or risk acceptance; sanitized errors not evidence logger fixed.
Action/accountable role: Lead scope disposition, Owner explicit residual if requested, Security UNASSIGNED assess baseline/delta; Developer/Tester no token evidence output; fix UNASSIGNED.
Target gates: fresh scope review/Step 2 residual; harness safety Step 1/3.
AC: AC-08
UAT: UAT-15
Evidence IDs: EV-S2-RESIDUAL, EV-S1-UNIT
Blocker: out-of-delta not accepted; dedicated baseline remediation test NONE/PENDING, linked case only harness safety; raw token harness output blocks execution.

RISK R-SCOPE-01 — Baseline check_scope no-op
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-SCOPE-01; historical T:amr_resource/models/ir_http.py:126–139 base dae519..., no exploit proof.
Owner design/scope: no new authorization-scope policy/fix added; selected token claims not proof check_scope enforced.
Action/accountable role: Lead per-ID scope, Owner residual, Security UNASSIGNED baseline/delta; fix implementer UNASSIGNED.
Target gates: fresh scope review/Step 2; Step 3 consumer evidence not whole baseline remediation.
AC: AC-04, AC-08
UAT: UAT-09, UAT-15, UAT-27
Evidence IDs: EV-S2-RESIDUAL
Blocker: no blanket clearance, dedicated fix test NONE/PENDING, no silent scope-policy invention.

RISK R-SU-01 — Baseline machine su=True
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-SU-01; historical T:amr_resource/models/res_users.py:14–26 base dae519..., current exploitation UNKNOWN.
Owner design/scope: resolver non-superuser/no sudo does not prove all consumer escalation removed or accepted.
Action/accountable role: Lead scope, Security UNASSIGNED assess consumer vs resolver on exact candidate, Owner residual; fix UNASSIGNED.
Target gates: Step 2 residual; Step 1/3 consumer delta evidence.
AC: AC-04, AC-12
UAT: UAT-09, UAT-23, UAT-29
Evidence IDs: EV-S2-RESIDUAL, EV-S2-SEC
Blocker: introduced escalation cannot be waived by migration deferral; baseline remains separately undispositioned, dedicated baseline fix test NONE/PENDING.

RISK R-CALLKW-01 — Baseline generic call_kw
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-CALLKW-01; historical T:amr_resource/controllers/main.py:98–106 base dae519..., no new reachability/exploit proof.
Owner design/scope: resolver allowlist not controller-wide safety or accepted residual.
Action/accountable role: Lead separate scope disposition, Security UNASSIGNED exact candidate RPC exposure assessment, Owner residual; fix UNASSIGNED.
Target gates: fresh scope review/Step 2 residual.
AC: AC-08, AC-09
UAT: UAT-15, UAT-24
Evidence IDs: EV-S2-RESIDUAL
Blocker: UAT-24 registry RPC controls only, dedicated whole-controller remediation test NONE/PENDING; no blanket clearance.

RISK R-TRANSPORT-01 — Untrusted endpoints/egress/conditional SSRF-like risk
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-TRANSPORT-01/historical helper metadata/JWKS/introspection paths; static/document, network/callers/config UNKNOWN.
Owner design/scope: D-02 static exact profile and full D-03 transport policy remain, not verified runtime controls.
Action/accountable role: Developer all paths fail closed/policy, Reviewer/Security coverage, Tester authorized evidence; individuals UNASSIGNED.
Target gates: Step 1/2/3.
AC: AC-01, AC-02, AC-05
UAT: UAT-01, UAT-03, UAT-04, UAT-05, UAT-06, UAT-12, UAT-28
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: all-path transport missing coverage/review holds relevant gate; neither proven exploit nor risk accepted.

RISK R-PROFILE-01 — Token class/algorithm/claims/local uncertainty
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-PROFILE-01/D-01/D-02/O-04 inherited contract; library/runtime behavior not newly inspected.
Owner design/scope: RS256/RSA access JWT required claims/zero-leeway; opaque complete O-04 optional times, active true/sub/client_id/aud/iss/azp; reject HS/ID/untyped, no class/local bypass. OPN-01 closed.
Action/accountable role: Developer preserve frozen profile and actual crypto vectors/local key/pinned library, Reviewer/Security candidate review; individuals UNASSIGNED. No repeat Owner selection requested.
Target gates: fresh review/Step 1 reassessment/Step 2/3.
AC: AC-01, AC-02, AC-03, AC-04, AC-10, AC-11, AC-12
UAT: UAT-02, UAT-05, UAT-06, UAT-08, UAT-27
Evidence IDs: EV-OPN01, EV-S1-UNIT, EV-S2-SEC, EV-TARGET
Blocker: implementation/library proof pending; optional opaque schema does not weaken required JWT policy.

RISK R-AUDIENCE-01 — aud/azp type/profile/global trust expansion
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-AUDIENCE-01/D-04 and global design history; document/static only.
Owner design/scope: valid aud ANY exact, global distinct set; single nonempty azp exact when present/required config, no ID Token semantics.
Action/accountable role: Developer strict types/uniqueness/policy, Reviewer/Security coverage; migration no-union requirement linked separately R-M02, no auto-expansion; individuals UNASSIGNED.
Target gates: Step 1/2/3 current validation; migration decisions target ADDONS13-57 only.
AC: AC-10, AC-11
UAT: UAT-02, UAT-06, UAT-17, UAT-18, UAT-24, UAT-25, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: policy choices closed but evidence pending; no ANY/ALL decision reopened.

RISK R-PROVENANCE-01 — Caller payload/context/auth fallback/stale same-UID
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-PROVENANCE-01/D-11/helper consumers historical; document/static, not current proof.
Owner design/scope: session→bearer→explicit params, invalid bearer no params fallback; internal verified provenance, same-UID metadata/current-company checks; O-05 generation fixed.
Action/accountable role: Developer guard all entries/switch/revoke, Reviewer/Security review actual path; individuals UNASSIGNED.
Target gates: Step 1/2/3.
AC: AC-04, AC-08, AC-12
UAT: UAT-04, UAT-05, UAT-09, UAT-23, UAT-27, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: no payload/marker shortcut or stale tenant proof; parameter/logging exposure baseline separately R-LOG-01.

RISK R-ACCESS-01 — Global ACL/RPC/roles/enumeration/secrets
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-ACCESS-01/D-08/Owner-02 global override; inherited static/document, runtime controls unverified.
Owner design/scope: global registry never public ACL; trust/code roles separate/manual, backend field/RPC guards/credential refs/internal field-limited lookup remain.
Action/accountable role: Developer deny non-approved registry/code enumeration/CRUD, protect audit/fields, Security UNASSIGNED review; Tester authorized actual ORM/RPC proof later.
Target gates: Step 1/2/3 current ACL/rules/UI, legacy metadata removal R-M03 target only.
AC: AC-09, AC-12, AC-15, AC-16
UAT: UAT-19, UAT-24, UAT-25, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: view-only/mock proof insufficient; real current registry controls remain mandatory even migration deferred.

RISK R-CACHE-01 — Stale policy/JWKS/config/library caching
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-CACHE-01/D-09; inherited document, no operational recovery verified.
Owner design/scope: no addon/library token/introspection/metadata/JWKS cache v1, including PyJWKClient; unsupported no-cache path reject; synthetic code/config revision simulation current. Full tuple/restore portion cross-reference R-M03/ADDONS13-57; no RTO/RPO chosen.
Action/accountable role: Developer actual no-cache paths, Tester current cross-worker/company refresh only after authorization; migration full tuple operator UNASSIGNED in target, no code-only recovery claim.
Target gates: Step 1/2/3 current no-cache; full backup/restore/apply gates target R-M03, no target operation authorization.
AC: AC-06
UAT: UAT-14, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: library no-cache mismatch holds current path; operational recovery not proven by synthetic config restore. Migration reference no longer UAT-26 current completion.

RISK R-TARGET-01 — Unverified target/dependencies/MRO/compatibility
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-TARGET-01/D-10; inherited target design, unit report only Python3.7.9 offline suite not Odoo target.
Owner design/scope: Odoo13/Python3.7.9 pinned dependencies/module matrix and isolated actual target proof, no sibling compatibility.
Action/accountable role: Lead assign Tester/authorize target, Developer pinned compatibility, Tester matrix/runner validation stop on mismatch; individuals UNASSIGNED.
Target gates: Step 1 unit evidence reassessment/Step 2/Step 3 target.
AC: AC-04, AC-07, AC-08
UAT: UAT-09, UAT-15, UAT-24, UAT-27, UAT-29
Evidence IDs: EV-TARGET, EV-S1-UNIT, EV-S2-GENERAL, EV-S3-UAT
Blocker: runtime/DB/QA unavailable or unauthorized holds Step 3; legacy upgrade needed means stop/cross-feature authorization, not implicit apply.

RISK R-HARNESS-01 — Fabricated/mocked proof/accidental I/O/secret exposure
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-HARNESS-01/AC-08/test plan; report 76 aggregate is historical unit only, no new UAT/security outcome.
Owner design/scope: actual candidate methods, measured zero-network/file/env/logger guards, sanitized evidence, no stubs/waiver.
Action/accountable role: Developer/Tester actual authorized runner/command/digests/mock limits/crypto vectors, Lead completeness; individuals UNASSIGNED.
Target gates: Step 1/2/3, no execution authorized in this task.
AC: AC-07, AC-08
UAT: UAT-15, UAT-27, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-GENERAL, EV-S2-SCAN, EV-S3-UAT
Blocker: missing guards/runner/scan evidence or fabricated PASS blocks relevant gate; document validation not product proof.

RISK R-API-01 — Generation selector/credential/compatibility
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-API-01/D-11/O-05, historical helper; contract not conformance finding.
Owner design/scope: complete O-05 exact selector aliases/credential_ref/client_credentials/string scope/key allowlist, no caller secret/default; public shapes and sanitized errors D-11 remain. OPN-02 closed.
Action/accountable role: Developer preserve strict contract and negative/compatibility vectors, Lead fresh review not reselection; individuals UNASSIGNED.
Target gates: fresh review/Step 1 reassessment/Step 2/3.
AC: AC-01, AC-02, AC-04, AC-05, AC-08
UAT: UAT-04, UAT-05, UAT-09, UAT-27, UAT-29
Evidence IDs: EV-OPN02, EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT
Blocker: actual contract/negative vectors review pending; closed decision not accepted gate or waived compatibility.

RISK R-SCOPE-BOUNDARY-01 — Sibling overrides/scope leakage/baseline attribution
Feature: ADDONS13-46
Evidence pointer/kind: Rev.04 R-SCOPE-BOUNDARY-01/E-01; inherited scope matrix/static history.
Owner design/scope: amr_resource only, sibling routes/provider/cache/consumers excluded; ADDONS13-57 receives migration deliverable only, not all global/security requirements.
Action/accountable role: Lead explicit dependency contracts if needed, Developer amr_resource delta only, Reviewer/Tester report effective-path limits without sibling clearance; individuals UNASSIGNED.
Target gates: fresh scope review/Step 1/2/3.
AC: AC-04, AC-07, AC-08
UAT: UAT-09, UAT-15, UAT-27, UAT-29
Evidence IDs: EV-S1-UNIT, EV-S2-GENERAL, EV-TARGET
Blocker: outside-addon changes or compatibility overclaim blocked; no automatic transfer of gates/acceptance to target Feature.

4. Transfer records — tetap OPEN / NOT ACCEPTED di ADDONS13-57

RISK R-M01 — Unknown actual global legacy inventory/markers/archived rows
Feature: ADDONS13-57
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Status: OPEN / NOT ACCEPTED
Severity: UNASSESSED
Evidence pointer/kind: predecessor register R-M01, PRD §6a G-MIG-01; Developer report known blocker §42 (single issuer plan, no complete global inventory). Historical static/report/document evidence only; no actual DB inspection.
Historical links, non-normative current completion: predecessor AC-06/09/16/17 and UAT-26/29. These refer to migration portions, not removal of current registry/identity/Default requirements.
Owner scope/design: O-06 transfers inventory/migration completion; O-03 G-MIG-01–04 approved design/implementation code only. Owner not-in-production/not-too-worried is scope rationale, not risk decision.
Owner residual-risk decision: NO RESIDUAL RISK ACCEPTANCE
Owner/accountable individual: UNASSIGNED; future roles Owner/Lead authorization, data administrator inventory, Developer defensive global plan. Reviewer: UNASSIGNED; Security reviewer UNASSIGNED.
Lead disposition: PENDING fresh review; target Step 0 PENDING, no acceptance transferred.
Action: after separately accepted target scope and authorization, inventory all active/archived profiles/children/bindings/legacy selectors and resolved values/markers/revisions/references globally; reject missing/invalid refs without web.base.url/key-as-URL; no fabricated inventory/no-conflict result. Actual DB contents/markers UNKNOWN / NOT RUN until authorized.
Target gates: ADDONS13-57 Step 0 analysis/acceptance PENDING; authorized Step 1 code/offline tests; Step 2 review; separately authorized Step 3 synthetic QA; target apply/cutover blocked until actual inventory and accepted plan. Tidak menjadi migration completion gate ADDONS13-46 setelah fresh scope acceptance.
AC: AC-06-M
UAT: UAT-26-M, UAT-29-M
Evidence IDs: EV-M01, EV-S1-UNIT, EV-S3-UAT, EV-APPLY-PLAN
Source report test IDs (historical offline unit, not global inventory proof): test_actual_migration_dry_run_apply_repeat_and_conflicts; test_key_indirection_is_never_treated_as_url_or_default; test_explicit_versioned_plan_is_deterministic_and_preserves_inputs.
Candidate: PENDING (ADDONS13-57); source 309c report only, not target acceptance.
Execution/authorization: DB/QA/runtime/apply/cutover/prod NOT AUTHORIZED / NOT RUN; source offline unit results preserved, no target tests run.
Blocker: target inventory UNKNOWN blocks target apply/cutover; safe migration not inferred from source unit PASS or Owner scope choice.

RISK R-M02 — Conflict/canonical config-user/identical duplicate reconciliation
Feature: ADDONS13-57
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Status: OPEN / NOT ACCEPTED
Severity: UNASSESSED
Evidence pointer/kind: predecessor R-M02/G-MIG-02/D-05 and Developer blocker §42; inherited document/report only, actual conflicts UNKNOWN.
Historical links, non-normative current completion: predecessor AC-06/09/16/17; UAT-19/24/25/26/29 migration/global legacy reconciliation portions. Current live exact-binding/constraints/eligibility requirements UAT-19/24/25/26/29 remain ADDONS13-46; no current controls deferred wholesale.
Owner scope/design: conflict reject already approved, no canonical choice/automatic union/merge/first-last-wins/delete. Identical duplicates require explicit consolidation decision too. O-06 scope move not acceptance of unresolved data conflicts.
Owner residual-risk decision: NO RESIDUAL RISK ACCEPTANCE
Owner/accountable individual: UNASSIGNED; future roles Developer conflict detection/rejection, Owner/data steward conditional canonical/identical-duplicate choice. Reviewer: UNASSIGNED; Security reviewer UNASSIGNED.
Lead disposition: PENDING fresh review; target Step 0 PENDING.
Action: all active/archived issuer/pair duplicates and differing endpoint/credential ref/audience/policy/resolver/user BLOCKED; preserve references, no auto-normalization/union/selection/membership expansion. After authorized inventory only, explicit data-owner canonical/consolidation disposition if conflict found; no-conflict requires evidence, not assumption. Active/internal user eligibility checked; no all-company membership requirement or company_ids mutation.
Target gates: ADDONS13-57 Step 0 pending; authorized Step 1/2/3 conflict behavior; target apply/cutover blocked by any unresolved actual conflict. Source current identity constraints stay current gates; this transfer not a current-feature waiver.
AC: AC-06-M
UAT: UAT-26-M, UAT-29-M
Evidence IDs: EV-M02, EV-M01, EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT, EV-APPLY-PLAN
Source report test IDs (historical, not actual reconciliation evidence): test_conflicting_issuer_audience_and_ambiguous_binding_rejected; test_plan_fingerprint_detects_reference_and_binding_revision; test_actual_migration_dry_run_apply_repeat_and_conflicts.
Candidate: PENDING (ADDONS13-57)
Execution/authorization: actual inventory/canonical decisions PENDING conditional / NOT RUN; DB/QA/runtime/apply/cutover/prod NOT AUTHORIZED / NOT RUN.
Blocker: if conflicts exist, apply waits explicit canonical disposition; if none reported, authorized complete inventory proof still needed. No risk accepted.

RISK R-M03 — Explicit schema/metadata/upgrade/atomicity/backup-restore/data loss
Feature: ADDONS13-57
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Status: OPEN / NOT ACCEPTED
Severity: UNASSESSED
Evidence pointer/kind: predecessor R-M03/G-MIG-03/04/D-09 and Developer §42 incomplete explicit upgrade column/schema metadata cleanup, obsolete rule removal only on explicit method invocation; historical report/static/document, not target schema inspection.
Historical links, non-normative current completion: predecessor AC-06/09/16, UAT-14/24/26/29 operational migration/schema/rehearsal portions; current no-cache/config simulation/declared models/current ACL/HTTP assertions remain current.
Owner scope/design: G-MIG-01–04 including amr_resource.migration.v2.global APPROVED_FOR_MIGRATION_CODE_IMPLEMENTATION_ONLY (design/code only), never DB/QA/apply/cutover/prod. O-06 changes delivery scope, not old approval boundary or proof schema safe.
Owner residual-risk decision: NO RESIDUAL RISK ACCEPTANCE
Owner/accountable individual: UNASSIGNED; future roles Developer explicit versioned global digest/transaction/upgrade cleanup, Lead/Owner accepted target order, operator backup/restore rehearsal after authority. Reviewer: UNASSIGNED; Security reviewer UNASSIGNED.
Lead disposition: PENDING fresh review; target Step 0 PENDING, no implementation authorization granted here.
Action: explicit target-specific schema/metadata/rule/domain/view/column cleanup plan, preserved references/nonsecret audit backup; deterministic global digest independent A/B, marker+actual rows checked (old per-company marker not success), no-op only same digest/rows, drift/different plan reject; atomic failure no partial trust/marker, constraint+transaction concurrent apply/create protection. Backup known-good code+schema+config/credential refs+revision/audit+cache tuple and authorized install/upgrade/conflict/idempotence/restore rehearsal before deletion/cutover. Full tuple restore, no silent remap/company expansion on downgrade, no code-only recovery claim.
Target gates: ADDONS13-57 Step 0 PENDING; authorized Step 1/2 migration code/plan; separate Step 3 QA/rehearsal authorization; apply/cutover/prod blocked absent accepted exact target plan+inventory/conflict disposition+backup/restore evidence+explicit authority. Not additional Development gate.
AC: AC-06-M
UAT: UAT-14-M, UAT-24-M, UAT-26-M, UAT-29-M
Evidence IDs: EV-M03, EV-M01, EV-M02, EV-S1-UNIT, EV-S2-SEC, EV-S3-UAT, EV-APPLY-PLAN
Source report test IDs (historical offline only): test_actual_migration_dry_run_apply_repeat_and_conflicts; test_explicit_versioned_plan_is_deterministic_and_preserves_inputs; test_plan_fingerprint_detects_reference_and_binding_revision. No real schema/restore test evidence available; do not invent test IDs or run results for it.
Candidate: PENDING (ADDONS13-57)
Execution/authorization: target order/schema/backup/restore PENDING; DB/QA/runtime/apply/cutover/prod NOT AUTHORIZED / NOT RUN.
Blocker: field deletion in source is not old column/metadata cleanup proof; unit/mocked restore not actual recovery; proposal approval remains closed but target operations remain blocked/unauthorized.

5. Decision closure, reverse links, review boundary

OPN-01 — CLOSED_BY_EXPLICIT_OWNER_DECISION / O-04. Frozen opaque schema/time in PRD; EV-OPN01 record only, R-PROFILE-01 mitigation/review still pending. Do not reopen.
OPN-02 — CLOSED_BY_EXPLICIT_OWNER_DECISION / O-05. Frozen generation selector/credentials/grant contract; EV-OPN02 record only, R-API-01 mitigation/review pending. Do not reopen.
UNRESOLVED-M01/M02/M03 transferred as R-M01/R-M02/R-M03 above with original evidence IDs, OPEN / NOT ACCEPTED; candidate PENDING, not implicit Source Feature current completion blockers after fresh Lead scope acceptance. Actual apply/cutover/prod remains blocked/unauthorized.

AC↔UAT complete normative reverse trace is in UAT, with each case AC field. Risk forward AC/UAT fields above are normative for this revision. Parsed forward risk trace and generated complete reverse AC/UAT→risk index are stored in RESULT.json; migration entries exclusively suffix -M, historical migration cross-links above are provenance only. Nonmigration risks remain on current IDs. Register citations use predecessor named risk IDs, not stale new line numbers; original evidence kind/source-location limitations inherited unchanged.

Owner scope decision does not waive security residuals, accept NOT_RUN cases or manufacture a new Step 1 verdict. Lead fresh per-ID disposition and exact-hash scope acceptance PENDING; then serial workflow only, Step 1 eligibility reassessment before Step 2, unified general/manual Security/offline Semgrep one Code Review verdict, separate authorized UAT, Owner PR_ACCEPT/merge readback. All current UAT cases remain NOT RUN/deferred, target references NOT RUN. No DB/QA/runtime/apply/cutover/prod authority; no source/tests/Git/Plane changes or product tests in this document task.
