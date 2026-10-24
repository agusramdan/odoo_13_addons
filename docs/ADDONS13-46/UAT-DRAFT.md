ADDONS13-46 — UAT DRAFT — Owner scope deferral 05

Issue UUID: 0932b9ca-60ee-44b7-8c88-3e98a173b15b
status=DRAFT; acceptance=false; fresh_lead_review=PENDING
step0_gate=PENDING_LEAD_REVIEW; step1_reassessment=PENDING; Step 2–4=PENDING
DB/QA/runtime/apply/cutover/prod: NOT AUTHORIZED / NOT RUN.

Referensi: [PRD](PRD-DRAFT.md), [scope decision](DECISION-ADDENDUM-OWNER-SCOPE-DEFER-05.md), [risk register](RISK-DECISION-REGISTER.md), [revision note](REVISION-NOTE.md), [hasil validasi](RESULT.json), [UAT predecessor immutable](../analysis-20261024T133315+0800-analis-global-registry-decisions-04/UAT-DRAFT.md).

1. Makna status dan prasyarat

Kasus planned tetap stable IDs. Semua acceptance case revisi ini belum dijalankan, NOT RUN; UAT-24/UAT-29 tetap DEFERRED / NOT RUN karena runtime authorization belum ada, bukan dipindah seluruhnya ke target. Suffix -M adalah ledger cross-reference bagian migrasi ke ADDONS13-57, bukan kasus target baru yang telah disetujui. Tidak menulis PRD/UAT target; Step 0 target tetap PENDING dan candidate target PENDING. Tidak ada implementation/test authorization ditransfer.

Kontrak D-01–D-11 / O-04/O-05 pada PRD tetap, khususnya global trust/mapping, active-company membership, token profiles, backend ACL/security, no-cache dan API/provenance. OPN-01/02 CLOSED_BY_EXPLICIT_OWNER_DECISION, tidak dibuka ulang. G-MIG-01–04 APPROVED_FOR_MIGRATION_CODE_IMPLEMENTATION_ONLY, bukan DB/QA/apply/cutover/prod authorization. Full tuple restore/upgrade dan legacy conversion dipisah, tidak menghapus perilaku current code/config/identity/access.

Hasil execution historis 76/76 PASS pada candidate 309c2d883b3475089e70567c3599b7a1858c57e1 ada dalam [raw Developer report](../developer-step1-20261024T1413+0800/REPORT.md), yang tetap STEP1_VERDICT=NOT_PASS atas predecessor migration scope. User menyatakan Lead independently verified suite SHA sama. Unit aggregate bukan UAT run atau fresh acceptance; tidak mengisi actual case dengan PASS. Tidak ada product tests dijalankan ulang oleh Analis. Fresh Lead hash-bound review dan Step 1 reassessment PENDING.

Target produk Odoo 13 / Python 3.7.9, pinned dependencies; actual disposable isolated runtime/DB/module/MRO matrix, actor/target/runner/cleanup scope dan separate authorization wajib sebelum Step 3, setelah eligible Step 1 dan accepted unified Code Review Step 2. Target yang memerlukan legacy upgrade/cleanup harus STOP dan minta separate authorization/scope; tidak boleh mengganti menjadi migration apply terselubung. Fresh synthetic fixture/current registry evaluation tetap scope ADDONS13-46, bukan bukti old DB upgrade.

Unit rules inherited: actual candidate methods (bukan reimplementation/success stubs); mocks hanya external HTTP/JWKS/key-provider/ORM/clock/request/cache boundaries, tidak mengganti subject validator/resolver. Synthetic claims/users/ephemeral in-memory keys, reserved .invalid endpoints, no real DNS/HTTP/private-key file. Guard DNS/socket/requests/redirect/PyJWKClient/file/env/logger, measure zero-network; no raw token/secret logs. Boundary sequencing bukan crypto proof: pinned actual JWT library positive/negative vectors terpisah. Odoo SavepointCase/ORM suite tidak dijalankan lewat standalone command rekaan; future runner dipilih pada scope terotorisasi dan command/runtime/candidate/test hashes dicatat. Tidak menuliskan command produk executable baru di sini.

2. Current cases — seluruh expected normatif mengikuti PRD tanpa weakening

CASE UAT-01 — Unknown/non-HS issuer
Feature: ADDONS13-46
AC: AC-01, AC-09
Target/gate: actual ResourceHelper.validate dan trust lookup; future authorized Step 1 unit/replay Step 3. D-01/D-02.
Data/steps: synthetic missing/malformed/unknown/inactive/ambiguous issuer JWT; call actual chain, spy DNS/socket/Discovery/JWKS/introspection/token/key/credential/resolver boundaries.
Expected: exact global active profile only; invalid reject sebelum seluruh outbound/credential/resolver, zero egress. Unsupported token class bukan success fixture.
Actual: NOT RUN

CASE UAT-02 — HS reject / opaque contract
Feature: ADDONS13-46
AC: AC-01, AC-09, AC-11, AC-12
Target/gate: actual validate_hs/introspect_token and validation chain; unit/replay. D-01/D-02/D-04/O-04.
Data/steps: HS JWT rejection terpisah; selected trusted opaque profile, object/array/null responses; active true/false/missing/string/number; sub/client_id empty/missing/non-string; aud/iss/azp variations; optional exp/iat/nbf absent/valid/expired/future/malformed frozen-clock zero-leeway; jti/typ absent; forged extra uid/company/roles. Mutate satu field, spy ordering/identity tanpa mengganti subject validator.
Expected: HS reject no opaque fallback; opaque seluruh O-04 schema/time tepat seperti PRD, active boolean true only, nonempty sub/client_id, issuer exact-or-bound, aud/azp D-04. Optional absent time/jti/typ tidak reject, present invalid time reject sebelum resolver; extra claims tidak memberi identity/rights. Unknown/inactive profile zero outbound.
Actual: NOT RUN

CASE UAT-03 — Static only / zero Discovery
Feature: ADDONS13-46
AC: AC-02, AC-05
Target/gate: actual get_oidc_config/profile selection; unit/replay. D-02/D-03.
Data/steps: registered static .invalid profile, invalid/missing endpoint, caller Discovery/metadata hint/unknown issuer; invoke and mutate selector/config, spy all metadata paths.
Expected: only exact trusted global static configuration; zero Discovery; invalid/missing required endpoint reject, no web.base.url/fallback/resolver; permitted transport D-03.
Actual: NOT RUN

CASE UAT-04 — Generation/encode wrappers
Feature: ADDONS13-46
AC: AC-01, AC-02, AC-04, AC-05
Target/gate: actual generate_token/encode; unit/replay. D-02/D-03/D-11/O-05.
Data/steps: configured client ID/protected credential_ref synthetic boundary; each alias and exact-identical combinations, conflicts/absent/malformed/unknown, client_secret including empty, client_id absent/equal/wrong/type-invalid, client_credentials/other grants, scope absent/string/empty/non-string, extra keys, invalid reference, HTTP/JSON failure. Invoke wrappers; spy selected credential target structurally, no values/real access.
Expected: entire O-05 contract PRD; forbidden/conflicting/unknown inputs reject before credential/outbound; no defaults/alias precedence/caller-secret fallback. Only selected protected profile credential, client_credentials, optional string scope (empty allowed). Static zero Discovery; generation JSON/encode access_token/error shapes D-11, no inbound resolver invocation.
Actual: NOT RUN

CASE UAT-05 — Static opaque introspection/direct URL reject
Feature: ADDONS13-46
AC: AC-01, AC-02, AC-04, AC-05
Target/gate: actual introspect_token; unit/replay. D-01/D-02/D-03/D-11/O-04.
Data/steps: explicit selected global profile, synthetic opaque, arbitrary URL/caller iss conflict/caller credentials/legacy GET-body vs POST form, invalid response; record structural destination/auth/error only.
Expected: no untrusted URL/credential bypass; trusted static POST application/x-www-form-urlencoded only; unsupported/no selected profile reject before network, no class/default fallback. Complete O-04 schema/time/aud/azp before resolver; missing optional jti/typ/time allowed, invalid present claims reject, extra claims ignored. O-05 does not authorize inbound caller credentials.
Actual: NOT RUN

CASE UAT-06 — Actual crypto/profile/claims
Feature: ADDONS13-46
AC: AC-01, AC-02, AC-10, AC-11, AC-12
Target/gate: actual validate/key/profile and pinned JWT library; unit/replay. D-01/D-03/D-04.
Data/steps: synthetic valid/invalid signatures, allowed/disallowed alg/key type/kid/JWKS, malformed header/claims, missing/expired exp, future iat/nbf, zero-leeway boundaries, wrong iss/aud/azp; sequence spies separate from actual crypto vectors with ephemeral in-memory keys and mocked transport, never mocked signature success for crypto evidence.
Expected: only RS256/RSA; required typ=at+jwt or exact equivalent actually designated in profile, iss/aud/exp/iat/jti/sub/client_id; exp future, iat not future, optional nbf effective, leeway 0; invalid alg/key/signature/claim reject before resolver. Mock sequencing and actual library proof reported separately, not Odoo proof.
Actual: NOT RUN

CASE UAT-08 — Local classification only
Feature: ADDONS13-46
AC: AC-03
Target/gate: actual is_local_issuer/is_local_token/profile lookup; unit/replay. D-02.
Data/steps: configured issuer same/different web.base.url, slash/case variants, unknown/missing/forged token; compare exact classification and count egress/resolver.
Expected: classification bound to registered rule, no principal/signature acceptance/local bypass; zero network/loopback. Protected local key reference D-02 unchanged. No amr_token round-trip/compatibility claim.
Actual: NOT RUN

CASE UAT-09 — In-addon consumers/precedence
Feature: ADDONS13-46
AC: AC-04, AC-12
Target/gate: actual _auth_method_machine/_params/_user_or_param, ResUsers.decode/with_access_token_context; unit/replay. D-01/D-05/D-06/D-11.
Data/steps: real helper chain with mocked request/session/core auth/ORM/transport boundaries, same/changed UID; session valid/invalid, bearer present valid/invalid, bearer absent params valid/invalid; validate=False/untrusted payload/context marker. No always-success helper stub.
Expected: session → bearer → explicit params, valid session accepted independently; invalid presented bearer reject no params fallback; params only bearer absent+own validation. UID after validated principal, same-UID metadata preserved, payload/context marker not verification. Runtime MRO proof remains UAT-29.
Actual: NOT RUN

CASE UAT-12 — All-path transport controls
Feature: ADDONS13-46
AC: AC-05
Target/gate: actual endpoint/HTTP/PyJWKClient adapter; unit/replay. D-03.
Data/steps: invalid scheme/port/userinfo/origin, redirect to forbidden host, DNS/public→private/rebinding, loopback/private/etc classes, timeouts/oversize/HTTP/JSON; simulate all metadata/token/introspection/direct JWKS/library paths without DNS/network; inspect structural flags/limits/errors.
Expected: HTTPS/TLS verify/443, deny address classes with connection-time DNS revalidation, no redirects/cross-origin credentials, connect 3s/read 5s/total 8s, retry0/max1MiB; fail closed/sanitized. Unsupported compliant path reject, no real secret evidence.
Actual: NOT RUN

CASE UAT-14 — Current no-cache/config revision simulation
Feature: ADDONS13-46
AC: AC-06
Target/gate: actual profile selection/cache adapter; unit/replay, not runtime restore. D-02/D-09.
Data/steps: synthetic A/B profile/policy/endpoint/key/credential-ref revisions, fake clock/cache boundary; switch, rotate, expiry/negative-cache fixtures, restore synthetic accepted code/config revision and invoke real helper each time. If no addon cache inspect actual pinned library boundary.
Expected: token/introspection/metadata/JWKS caches absent/disabled including helper/PyJWKClient, no stale revision/profile reuse; unsupported no-cache path reject. Simulated code/config coherence does not prove DB/schema/deployment recovery. Full tuple backup/restore rehearsal only UAT-14-M/UAT-29-M.
Actual: NOT RUN

CASE UAT-15 — Scope/evidence/harness safety
Feature: ADDONS13-46
AC: AC-07, AC-08
Target/gate: future authorized candidate delta and actual harness, Step 1 evidence/Step 2 repeat/Step 3 verification. E-01/D-10.
Data/steps: candidate/base/test digests, amr_resource allowlist, DNS/socket/HTTP/file/env/logger sentinels; inspect actual-method coverage, fail guard violations, compare SHA/counts/runtime/mock limits. No Semgrep or Git/product commands in this document task.
Expected: no sibling edits/Discovery/provider/cache changes, zero network/private secret reads/raw-token logs; evidence bound exact candidate+test hashes; structural check not product/security PASS.
Actual: NOT RUN

CASE UAT-16 — Exact active global lookup
Feature: ADDONS13-46
AC: AC-01, AC-09
Target/gate: actual registration lookup; unit/replay. D-02/D-08.
Data/steps: exact/missing/inactive/duplicate/archived/malformed/slash/case fixtures, A/B allowed-company order variants; call validation/generation/opaque selector, compare domains/IDs and zero egress invalid cases.
Expected: same exact active global profile/policy A/B, no company filter/default, auto-create or limit=1; ambiguous reject. Archived uniqueness actual DB proof UAT-24, not mocked constraint proof.
Actual: NOT RUN

CASE UAT-17 — Global multiple audiences/ANY
Feature: ADDONS13-46
AC: AC-10
Target/gate: actual audience/profile validation; unit/replay. E-02/D-01/D-04.
Data/steps: global two child audiences same azp/policy A/B; aud string/list/one/all/none match/missing/empty/non-string/nested/duplicate vectors; compare IDs/set/result and issuer separation.
Expected: multiple distinct configured child values shared A/B, ANY exact valid match, malformed/missing/empty reject; audience not issuer trust or company eligibility. No audience union permission.
Actual: NOT RUN

CASE UAT-18 — Optional single azp
Feature: ADDONS13-46
AC: AC-11
Target/gate: actual accepted-class claim validation; unit/replay. E-03/D-01/D-04.
Data/steps: absent/exact/wrong/empty/non-string azp, required without configured value, multiple configuration values; accepted JWT/opaque versus rejected ID/HS/untyped, combine aud cardinality, spy ordering.
Expected: absence only permitted profile; present single nonempty string exact single configured value; invalid profile/claim reject before resolver, never import ID Token semantics.
Actual: NOT RUN

CASE UAT-19 — Global exact identity/collisions
Feature: ADDONS13-46
AC: AC-09, AC-12, AC-16
Target/gate: actual binding/result chain; unit/replay. D-05/D-06.
Data/steps: I1/I2 same sub S, I1/S→U_AB eligible A/B, colliding email/login V, unmapped/archived/duplicate/mismatched fixed/method result and exact variants; invoke after validation A/B across modes, compare user and lookup domains.
Expected: same global I1/S user, independent I2/S, no normalization/company discriminator/email/login/auto-binding/mode fallback/limit=1. Unbound/ambiguous/inactive/mismatched reject; actual CRUD/constraints UAT-24. Legacy dataset reconciliation UAT-26-M, not current live collision removal.
Actual: NOT RUN

CASE UAT-20 — Fixed user/current-company eligibility
Feature: ADDONS13-46
AC: AC-12, AC-13
Target/gate: actual fixed resolver/entry chain; unit/replay. D-06.
Data/steps: global binding+fixed ref U_A active internal/non-superuser/non-public/non-portal only A, U_AB A/B; deleted/archived/disallowed/high-privilege/claim uid/token-invalid/mismatch fixtures; A→B/switch invokes actual eligibility.
Expected: U_A accepted A, generic reject B despite same global trust; U_AB same user A/B, no alternative/membership expansion/all-company configuration requirement. Invalid token zero resolver; current request eligibility not stale context/provenance.
Actual: NOT RUN

CASE UAT-21 — Allowlist/result type
Feature: ADDONS13-46
AC: AC-12, AC-14
Target/gate: actual dispatcher/result validator and code-allowlisted test method; unit/replay. D-06.
Data/steps: listed/unlisted/private/arbitrary method/model; zero/many/wrong model/int/dict/cross-DB-like result/exception, valid/invalid verified context; observe actual dispatch and no implicit sudo.
Expected: only code-owned allowlist invoked after validation, exactly one eligible res.users; all errors/wrong results reject without fixed/Default/Python fallback. Subject dispatcher not mocked to prove itself.
Actual: NOT RUN

CASE UAT-22 — Stored Python disabled/audit
Feature: ADDONS13-46
AC: AC-12, AC-15
Target/gate: actual disabled execution adapter and edit/audit metadata; unit/replay after scope authorization. E-05/D-07/D-08.
Data/steps: benign synthetic code as data only, revision/digest/actor; valid/invalid tokens; spy execution boundary zero. Structural activation/edit guards; no execution of snippets/capability probes in v1.
Expected: stored code never executed even valid token; fixed/allowlisted only. Edits restricted/audited, not activate. Owner activation/control/threat model/exact-candidate manual Security requirements remain outside v1; no sandbox-safety claim.
Actual: NOT RUN

CASE UAT-23 — All-mode no fallback/provenance
Feature: ADDONS13-46
AC: AC-12, AC-13, AC-14, AC-15, AC-16
Target/gate: actual resolver/result/consumer adapters; unit/replay. D-05/D-06/D-07/D-11.
Data/steps: selected modes zero/many/archived/disallowed/error, machine inactive, same UID/context payload provenance; external boundary responses only, bad token zero all modes; repeat A/B.
Expected: exactly one permitted user consistent global binding or explicit failure; no second mode, email/limit=1/membership expansion; company_ids eligibility each request. Resolver-mode fallback differs from permitted auth-source precedence D-11.
Actual: NOT RUN

CASE UAT-24 — Current real registry/constraints/ACL/RPC/UI
Feature: ADDONS13-46
AC: AC-09, AC-10, AC-12, AC-15, AC-16, AC-17
Target/gate: real candidate ORM/registry/views/RPC in authorized disposable isolated Odoo 13 QA; automated integration + reviewed manual evidence, Step 3. D-02/D-05/D-06/D-07/D-08/D-10.
Data/steps: after Step 2 accepted+separate runtime/DB authorization, clean synthetic target/current model initialization, roles trust admin/code editor/internal/portal/public, A/B, issuer/audiences/binding U_AB and U_A. Inspect current registered model declarations/rules/UI without legacy upgrade; assert no registry company_id/related/default/domain; A/B same row config, trust edit visibility; create exact archived duplicates/pair-to-other-user from B, child cascade/user delete restrict, I2/S independent. Exercise read/CRUD/search/name/RPC/field/context-default injection per role; Default key/label/no preselection; audit no secrets, edit code no activation; validate U_AB A/B, U_A A only.
Expected: actual global constraints/access effective, no company discriminator/current UI company rules; non-approved/code-role overreach denied by backend beyond view. User company_ids/business rules remain, no rights expansion. Stored Python disabled and Default exact. Legacy upgrade/schema/metadata/XML cleanup explicitly UAT-24-M, not silent deletion of current model assertions; if clean target requires legacy migration, stop pending authorization.
Actual: DEFERRED / NOT RUN

CASE UAT-25 — Default/global config/active-company split
Feature: ADDONS13-46
AC: AC-01, AC-09, AC-10, AC-12, AC-14, AC-16, AC-17
Target/gate: actual selection adapter/get_user_match, unit/replay; UI UAT-24. E-04/E-06/E-07/D-02/D-04/D-05/D-06/D-08.
Data/steps: get_user_match/Default, new/existing no selected mode, same issuer/audiences/azp/policy/pair→U_AB A/B and U_A A-only; collision V/inactive/deleted/unbound/ambiguous/forged uid/company/invalid token. Inspect no preselection, compare lookup/profile/audience/binding/result IDs A/B; duplicate attempts are fixtures, actual DB proof UAT-24.
Expected: exact key/label/no auto-preselection, shared global config/binding, same U_AB A/B; U_A reject B without V/fallback/rights update; no company filters; token invalid zero resolver. Historical email-first is characterization only, never expected authorization.
Actual: NOT RUN

CASE UAT-26 — Current fail-closed legacy fallback boundary
Feature: ADDONS13-46
AC: AC-01, AC-04, AC-09, AC-12, AC-16, AC-17
Target/gate: actual live helper/config selection/binding/default consumer behavior, unit/replay; not migration adapter. D-02/D-05/D-08/D-11.
Data/steps: synthetic unconfigured/invalid legacy selector KEY vs URL-looking value, missing referenced configuration/web.base.url, old email-only user mapping, new/existing unresolved resolver selection; invoke live helpers across A/B with external persistence mocked, spy no auto-create/write/network/resolver success. Do not inventory or convert existing rows, execute migrator or fabricate approved plan.
Expected: no key-as-URL/default issuer/web.base.url/legacy credential fallback, no per-company config creation/auto-union/email auto-binding/default preselection or membership change; unknown/unbound/unselected config fails closed, explicit audited configuration required. Complete registry/binding requirements remain. Historical migration dry-run/apply/idempotence/conflict code work now UAT-26-M, not PASS/removed live fail-closed assertions.
Actual: NOT RUN

CASE UAT-27 — Per-consumer profile/provenance matrix
Feature: ADDONS13-46
AC: AC-04, AC-08, AC-12
Target/gate: actual helpers/in-addon consumers per PRD D-01/D-10/D-11/O-04/O-05; unit/replay.
Data/steps: accepted/rejected JWT/opaque/local/ID/HS/untyped per operation, profile mismatch/marker/dict/stale payload, direct get_uid/is_user_match, validate=False/context branch; actual methods not duplicated algorithms.
Expected: explicit per-operation profile; get_validate_user/validate/decode before resolver, generate/encode not inbound identity, local classification not validation. JWT jti/typ/time requirements not imposed on opaque optional claims; no caller dict/marker principal; D-11 shape/precedence and O-05 generation strict. Session success not token acceptance, no silent signature compatibility change.
Actual: NOT RUN

CASE UAT-28 — Standalone JWKS trust
Feature: ADDONS13-46
AC: AC-01, AC-02, AC-05
Target/gate: actual get_jwks_data and profile/transport adapter; unit/replay. D-02/D-03.
Data/steps: direct helper known/unknown issuer, static/Discovery hints, malformed URI/wrong origin/timeout/JSON failure; spy trust selection/destination/limits/invalid zero egress, not assume validate invokes helper.
Expected: same exact trusted static endpoint/transport, no untrusted well-known construction/forwarding; consistent sanitized failure. PyJWKClient distinct path UAT-06/UAT-12 still required.
Actual: NOT RUN

CASE UAT-29 — Current effective HTTP/MRO/company/cache behavior
Feature: ADDONS13-46
AC: AC-04, AC-06, AC-08, AC-09, AC-10, AC-12, AC-16
Target/gate: candidate actual HTTP/registry/current config behavior in authorized isolated Odoo13 QA, Step 3 Tester; not upgrade/apply/restore. D-02/D-05/D-06/D-08/D-09/D-10/D-11.
Data/steps: only after accepted Step 2+separate target authorization, record exact candidate/runtime/dependency/module list/MRO/runner/cleanup on clean synthetic DB. Exercise session/bearer/params/same-UID metadata; identical global issuer/audiences/pair U_AB A/B, U_A A-only; company switch/revoke and forged company claim. Edit current global policy across QA workers, replay actual auth/no-cache/revision probes; authorized fixture cleanup readback, not schema downgrade/known-good tuple restoration.
Expected: effective current paths enforce same trust/config/mapping across A/B and D-06 per-request eligibility, no stale proof/cache/user alternatives/rights expansion. Actual registry/ACL/HTTP evidence required; overrides reported limitation/dependency not sibling compatibility PASS. Old DB conversion/global marker/schema upgrade/apply/atomicity/rollback rehearsal only UAT-29-M. Fixture cleanup alone not recovery. No production operation.
Actual: DEFERRED / NOT RUN

3. Migration cross-reference ledger — bukan UAT ADDONS13-57 baru

Seluruh entri suffix -M di bawah memiliki status DRAFT / PENDING target Step 0. Hanya memindahkan bagian expected/steps yang sudah ada pada immutable UAT Rev.04; final target IDs/candidate/runner/acceptance/assignment belum ditetapkan. Original G-MIG-01–04/marker tetap approved-for-migration-code-only; tidak memberikan izin mulai implementasi/tests. Referensi dibaca bersama AC-06-M dan register R-M01/02/03; current acceptance ACs tidak menjadi migration completion gate lagi.

CASE UAT-14-M — Full rollback tuple / restore rehearsal portion
Feature: ADDONS13-57
AC: AC-06-M
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Source-only reference: predecessor UAT-14 warning vs actual restore UAT-29; D-09; G-MIG-04. Transfers operational code+schema+config/reference+audit/cache backup/restore evidence, not synthetic no-cache/config revision simulation. Evidence EV-M03, EV-APPLY-PLAN. Owner/operator/reviewer UNASSIGNED, target candidate PENDING; no run instructions/new target test authored.
Actual: DEFERRED_TO_FEATURE ADDONS13-57 / NOT RUN

CASE UAT-24-M — Legacy upgrade/schema/metadata cleanup portion
Feature: ADDONS13-57
AC: AC-06-M
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Source-only reference: predecessor UAT-24 install/upgrade/schema/metadata portion; G-MIG-03. Transfers explicit old columns/related metadata/rules/domains/views/XML cleanup according to accepted upgrade plan, not fresh current model global constraints/access/UI proof retained UAT-24. Evidence EV-M03, EV-APPLY-PLAN. Owner/operator/reviewer UNASSIGNED, candidate PENDING; no target operations/new test instructions.
Actual: DEFERRED_TO_FEATURE ADDONS13-57 / NOT RUN

CASE UAT-26-M — Migration code/global inventory/plan/conflict/idempotence portion
Feature: ADDONS13-57
AC: AC-06-M
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Source-only reference: predecessor UAT-26 migration adapter/mock persistence dry-run/apply/repeat/conflict/restore plan and G-MIG-01–04. Transfers global legacy key inventory/resolution/conversion, active/archived existing profiles/children/bindings/per-company markers, canonical/identical duplicate decisions, deterministic digest/global marker/no-op/drift/atomic/concurrency migration checks. No first/last wins, auto-merge/union/delete/email binding/membership expansion. Live helper refusal/default/no email fallback retained UAT-26. Evidence EV-M01, EV-M02, EV-M03, EV-APPLY-PLAN. Owner/reviewer UNASSIGNED, target candidate PENDING; this is transfer reference, not target PRD/UAT authorization.
Actual: DEFERRED_TO_FEATURE ADDONS13-57 / NOT RUN

CASE UAT-29-M — Actual upgrade/apply/idempotence/restore portion
Feature: ADDONS13-57
AC: AC-06-M
Disposition: DEFERRED_TO_FEATURE ADDONS13-57
Source-only reference: predecessor UAT-29 global legacy-only/candidate-scoped install-upgrade/dry-run/apply/conflict/atomic failure/idempotence/schema cleanup/known-good tuple restore/replay/readback; G-MIG-01–04. Evidence EV-M01/EV-M02/EV-M03/EV-APPLY-PLAN. Current HTTP/MRO/company/no-cache checks retained UAT-29; target operation authorization separate. Owner/operator/reviewer UNASSIGNED; candidate PENDING. No migration safety/completion claim or new executable target test plan.
Actual: DEFERRED_TO_FEATURE ADDONS13-57 / NOT RUN

4. Normative AC → UAT trace; reverse adalah AC field setiap case

AC-01 -> UAT-01, UAT-02, UAT-04, UAT-05, UAT-06, UAT-16, UAT-25, UAT-26, UAT-28
AC-02 -> UAT-03, UAT-04, UAT-05, UAT-06, UAT-28
AC-03 -> UAT-08
AC-04 -> UAT-04, UAT-05, UAT-09, UAT-26, UAT-27, UAT-29
AC-05 -> UAT-03, UAT-04, UAT-05, UAT-12, UAT-28
AC-06 -> UAT-14, UAT-29
AC-06-M -> UAT-14-M, UAT-24-M, UAT-26-M, UAT-29-M
AC-07 -> UAT-15
AC-08 -> UAT-15, UAT-27, UAT-29
AC-09 -> UAT-01, UAT-02, UAT-16, UAT-19, UAT-24, UAT-25, UAT-26, UAT-29
AC-10 -> UAT-06, UAT-17, UAT-24, UAT-25, UAT-29
AC-11 -> UAT-02, UAT-06, UAT-18
AC-12 -> UAT-02, UAT-06, UAT-09, UAT-19, UAT-20, UAT-21, UAT-22, UAT-23, UAT-24, UAT-25, UAT-26, UAT-27, UAT-29
AC-13 -> UAT-20, UAT-23
AC-14 -> UAT-21, UAT-23, UAT-25
AC-15 -> UAT-22, UAT-23, UAT-24
AC-16 -> UAT-19, UAT-23, UAT-24, UAT-25, UAT-26, UAT-29
AC-17 -> UAT-24, UAT-25, UAT-26

5. Verdict/evidence contract

Current cases 25: 23 NOT RUN dan 2 DEFERRED / NOT RUN (UAT-24/UAT-29). Migration transfer references 4: UAT-14-M/UAT-24-M/UAT-26-M/UAT-29-M, seluruh DEFERRED_TO_FEATURE ADDONS13-57 / NOT RUN, tidak dihitung current completion. Executed acceptance cases revisi ini 0. Tidak ada PASS/FAIL/SKIP/waiver diciptakan. Document validation bukan product execution. Fresh Lead review tetap PENDING; acceptance=false. DB/QA/runtime/apply/cutover/prod NOT AUTHORIZED / NOT RUN.

Future pass hanya jika seluruh frozen expected terbukti pada actual authorized exact candidate+target; violated assertion fail; missing policy/runner/target/authorization/evidence blocked, NOT RUN bukan PASS. Raw failure/NOT_PASS tetap immutable; waiver hanya authority/per-ID sesuai canonical workflow, tidak dibuat di sini. Unit suite 76/76 tidak membuktikan registry/RPC/HTTP/rollback atau menutup residual risk.

Evidence per future run: issue/Feature/case+AC IDs, accepted PRD/UAT hashes, candidate branch/SHA/content manifest, test-file digest, code/config revision digests tanpa source code/secret dump, runtime/library/module/MRO matrix, actor/role/gate/authorized target, mock limits, exact sanitized command, expected/actual/exit/counts/run ID/path/cleanup readback. No raw tokens/credentials/private endpoint logs. Step 1 unit Developer/user, Step 3 Tester ditunjuk Lead; manual Security exact candidate/code/context/config revision dan offline Semgrep bersama general review hanya satu unified Code Review Step 2, bukan separate Security gate. Tidak ada DB/QA/runtime/apply/cutover/production authorization dari scope deferral, approved migration design atau dokumen ini.
