# ADDONS13-79 — V/U crosswalk

> **DRAFT SANITIZED DERIVATIVE — NOT ACCEPTED.** Bukan rebind, waiver, persetujuan konfigurasi, atau izin runtime.

Sumber internal adalah inventaris draft; PRD/UAT yang disetujui tetap otoritatif dan tidak diubah. SCOPE-01 **OPEN**. Gen5 adalah bukti diagnostik pada commit `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`, bukan HEAD teramati `5f1f0f9433f723f850df8640fdc1db261476df91`; tidak ada rebind otomatis.

Seluruh 32 kasus tetap **NOT ASSESSED pada tingkat oracle lengkap**; tidak ada klaim full-case PASS. Klaim eksekusi historis yang detail assertion dan hasilnya tidak dapat direkonstruksi secara publik diturunkan menjadi REDACTED / NOT ASSESSED; ini bukan penyangkalan adanya eksekusi historis. STATIC UNIT adalah label historis pemeriksaan sumber, bukan bukti test dijalankan atau hasil yang dapat diaudit di sini. Data detail assertion, selector, target operasional dan bukti mentah **REDACTED / NOT ASSESSED** dalam dokumen publik ini. Tidak ada eksekusi baru untuk derivatif ini.

Fixture bersama: database fresh disposable terverifikasi dan terotorisasi; komposisi per varian; issuer, client, user, company, credential dan RSA sintetis; actor public, portal, internal, system, trust-admin dan service sesuai kasus; jam terkendali serta observer signer/cache/transport dan baseline legacy sesuai kebutuhan. Observer zero self-provider HTTP harus terkalibrasi dan mencakup transport serta process/socket.

V06 helper/no-token-regardless-of-MRO BLOCKED sampai review/approval kontrak; review keamanan redirect/model terpisah. V10 default tanpa bearer URL berlaku; rincian denial menunggu persetujuan dan exception tidak diasumsikan. Lifecycle, security, final configuration dan fresh mapping tetap gate.

## Kasus, oracle dan gap

### V01

**Oracle sumber (bukan acceptance derivatif):** Fresh provider-only: five provider declarations absent from provider; no glue selected; independent provider `_generate_user_token`→`decode` succeeds for explicitly configured synthetic fixture and malformed/missing configuration fails. Verify provider declaration of `get_access_token` is glue-only; record effective public method status and legacy impact without assuming core/third-party absence or a particular exception.

**Gap Gen5:** five declarations/effective public method and legacy impact; malformed config matrix. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V01.01`: Fresh provider-only: five provider declarations absent from provider;
- `V01.02`: no glue selected;
- `V01.03`: independent provider `_generate_user_token`→`decode` succeeds for explicitly configured synthetic fixture and malformed/missing configuration fails.
- `V01.04`: Verify provider declaration of `get_access_token` is glue-only;
- `V01.05`: record effective public method status and legacy impact without assuming core/third-party absence or a particular exception.

### V02

**Oracle sumber (bukan acceptance derivatif):** RS-only: all five existing RS declarations retained, actual signatures and policy verified, direct issuance fails, URL wrappers pass through. Exercise separately configured synthetic RS verifier positive/negative, no provider/glue in closure.

**Gap Gen5:** five signatures/policy; independent closure and full RS verifier matrix. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V02.01`: RS-only: all five existing RS declarations retained, actual signatures and policy verified, direct issuance fails, URL wrappers pass through.
- `V02.02`: Exercise separately configured synthetic RS verifier positive/negative, no provider/glue in closure.

### V03

**Oracle sumber (bukan acceptance derivatif):** Both bases no glue in both fresh install orders: provider independent helper operation; RS independent positive and unknown issuer negative; compare registry/MRO, signatures, actual method dispatch and default nonsecret trust snapshots, no glue, issuer, fallback/discovery or trust introduced. Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; do not demand an unaccepted public-method fixture or assert sibling pass here.

**Gap Gen5:** both orders, actual MRO/dispatch, trust snapshots and sibling-owner review. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V03.01`: Both bases no glue in both fresh install orders: provider independent helper operation;
- `V03.02`: RS independent positive and unknown issuer negative;
- `V03.03`: compare registry/MRO, signatures, actual method dispatch and default nonsecret trust snapshots, no glue, issuer, fallback/discovery or trust introduced.
- `V03.04`: Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle;
- `V03.05`: do not demand an unaccepted public-method fixture or assert sibling pass here.

### V04

**Oracle sumber (bukan acceptance derivatif):** Glue explicitly installed in both orders, `auto_install=False`, no cyclic/base-to-glue dependency; verify moved five plus private helper/sentinel owner, retained RS source declarations and actual effective MRO, no implicit trust and no accidental activation. Dependency failure tested only using authorized isolated fixture.

**Gap Gen5:** both orders, effective MRO, sentinel ownership, accidental activation and authorized dependency-failure fixture. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V04.01`: Glue explicitly installed in both orders, `auto_install=False`, no cyclic/base-to-glue dependency;
- `V04.02`: verify moved five plus private helper/sentinel owner, retained RS source declarations and actual effective MRO, no implicit trust and no accidental activation.
- `V04.03`: Dependency failure tested only using authorized isolated fixture.

### V05

**Oracle sumber (bukan acceptance derivatif):** Login template on provider-only, RS+provider in both no-glue orders, glue: proposed provider-specific UI hook has baseline `True`, without `super`, context flags or registry sniffing; true/false override shows/hides Continue; public and authenticated user rendering stays controlled; no call to moved policy, glue, signer or token; verify no issuance. Exercise direct authorize/continue and submit routes: remain unsupported. Document old override/custom addon impact.

**Gap Gen5:** actual public/authenticated rendering, true/false override, direct routes and no-issuance observer. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V05.01`: Login template on provider-only, RS+provider in both no-glue orders, glue: proposed provider-specific UI hook has baseline `True`, without `super`, context flags or registry sniffing;
- `V05.02`: true/false override shows/hides Continue;
- `V05.03`: public and authenticated user rendering stays controlled;
- `V05.04`: no call to moved policy, glue, signer or token;
- `V05.05`: verify no issuance.
- `V05.06`: Exercise direct authorize/continue and submit routes: remain unsupported.
- `V05.07`: Document old override/custom addon impact.

### V06

**Oracle sumber (bukan acceptance derivatif):** Both RS GET routes in RS-only, both no-glue orders and glue, supported `auto_login`/`access_token`, URL branch, malformed type, absent URL, internal/public model paths, model `get_url_access_token` direct-result branch and auth failures; compare actual status/shape/Location/headers with approved contract. The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. Obtain independent security review of generic redirect/open-redirect and model-generated URL risks, not a blanket safety claim.

**Gap Gen5:** both routes and compositions, URL/type/model/auth/status/Location/header variants and independent redirect review. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V06.01`: Both RS GET routes in RS-only, both no-glue orders and glue, supported `auto_login`/`access_token`, URL branch, malformed type, absent URL, internal/public model paths, model `get_url_access_token` direct-result branch and auth failures;
- `V06.02`: compare actual status/shape/Location/headers with approved contract.
- `V06.03`: The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval;
- `V06.04`: pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN.
- `V06.05`: If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety.
- `V06.06`: Obtain independent security review of generic redirect/open-redirect and model-generated URL risks, not a blanket safety claim.

### V07

**Oracle sumber (bukan acceptance derivatif):** Glue direct access: self vs ordinary different actor vs system, singleton/empty/multiple, policy false, inactive/unauthorized where contract says; denied before cache and signing, even warm hit, across RPC/machine/public/portal and forged context. Test persistent `create_access_token` explicit controlled denial with no storage/signature.

**Gap Gen5:** empty/multiple, policy/inactive, warm-cache denial, RPC/public/portal/machine and forged context. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V07.01`: Glue direct access: self vs ordinary different actor vs system, singleton/empty/multiple, policy false, inactive/unauthorized where contract says;
- `V07.02`: denied before cache and signing, even warm hit, across RPC/machine/public/portal and forged context.
- `V07.03`: Test persistent `create_access_token` explicit controlled denial with no storage/signature.

### V08

**Oracle sumber (bukan acceptance derivatif):** Glue omission sentinel survives defaults/wrappers/cache/private boundary; omitted argument causes helper call with no audience argument, explicit None rejects; empty/malformed vs valid string/list, list tuple roundtrip, resource precedence and invalid resource rejection. No sentinel identity substitution from token_helper.

**Gap Gen5:** sentinel identity/private boundary, empty and malformed shapes, wrapper/cache tuple roundtrip. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V08.01`: Glue omission sentinel survives defaults/wrappers/cache/private boundary;
- `V08.02`: omitted argument causes helper call with no audience argument, explicit None rejects;
- `V08.03`: empty/malformed vs valid string/list, list tuple roundtrip, resource precedence and invalid resource rejection.
- `V08.04`: No sentinel identity substitution from token_helper.

### V09

**Oracle sumber (bukan acceptance derivatif):** Cache: same/different uid and normalized audiences, bucket rollover, actual expiry, policy/key/user/company/revision changes and explicit invalidation including concurrent changes, DB isolation; a stale/unauthorized hit never mints/returns a usable token. Expectations need approved lifecycle; verify no cross-context leakage.

**Gap Gen5:** key removal assertion hanya ValueError, bukan signer/stale hit; expiry, policy/user/company/revision invalidation, concurrency termasuk explicit invalidation and real DB isolation; approved lifecycle. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V09.01`: Cache: same/different uid and normalized audiences, bucket rollover, actual expiry, policy/key/user/company/revision changes and explicit invalidation including concurrent changes, DB isolation;
- `V09.02`: a stale/unauthorized hit never mints/returns a usable token.
- `V09.03`: Expectations need approved lifecycle;
- `V09.04`: verify no cross-context leakage.

### V10

**Oracle sumber (bukan acceptance derivatif):** Glue direct URL helpers and RPC: default must issue no bearer into URLs; proposed controlled denial with no signer/cache use and sanitized failure for all types, including auto-login and explicit audience/resource, is pending exact contract approval. If Owner separately approves an exception, specify reviewed origin/redirect, audience, caller, expiry/replay and leak-control cases; do not infer approval. No bearer in evidence.

**Gap Gen5:** all URL helper types and RPC, signer/cache observation and sanitized failure contract approval. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V10.01`: Glue direct URL helpers and RPC: default must issue no bearer into URLs;
- `V10.02`: proposed controlled denial with no signer/cache use and sanitized failure for all types, including auto-login and explicit audience/resource, is pending exact contract approval.
- `V10.03`: If Owner separately approves an exception, specify reviewed origin/redirect, audience, caller, expiry/replay and leak-control cases;
- `V10.04`: do not infer approval.
- `V10.05`: No bearer in evidence.

### V11

**Oracle sumber (bukan acceptance derivatif):** Delete mobile method in controlled first-party closure provider-only, RS-only, both orders, glue, legacy adapter: first-party declaration removal and no alias/shim; record effective registry resolution and direct/RPC result without assuming absence in Odoo core or third-party addons or any particular exception. Audit external/dynamic consumers separately.

**Gap Gen5:** all first-party closures, alias/shim, effective registry/direct/RPC and external dynamic consumers. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V11.01`: Delete mobile method in controlled first-party closure provider-only, RS-only, both orders, glue, legacy adapter: first-party declaration removal and no alias/shim;
- `V11.02`: record effective registry resolution and direct/RPC result without assuming absence in Odoo core or third-party addons or any particular exception.
- `V11.03`: Audit external/dynamic consumers separately.

### V12

**Oracle sumber (bukan acceptance derivatif):** Move relevant registered provider integration tests and source-loaded standalone/security fixtures to correct glue target; preserve all applicable actor, audience, cache, rejection and security assertions; independently run remaining provider issuer tests and reconcile applicable `amr_token` legacy loader/alias coverage. No silently dropped cases.

**Gap Gen5:** pemetaan fixture relevan source→target dan preservation assertion tidak dibuktikan daftar modul target; historical assertion inventory and amr_token loader/alias reconciliation; no silent drops. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V12.01`: Move relevant registered provider integration tests and source-loaded standalone/security fixtures to correct glue target;
- `V12.02`: preserve all applicable actor, audience, cache, rejection and security assertions;
- `V12.03`: independently run remaining provider issuer tests and reconcile applicable `amr_token` legacy loader/alias coverage.
- `V12.04`: No silently dropped cases.

### V13

**Oracle sumber (bukan acceptance derivatif):** Explicit local trusted binding off by default; wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user all reject. Approved valid provider access token passes same RS verifier. No ID token or generic JWT; no weakening, implicit trust or fallback.

**Gap Gen5:** negative issuer/signature di atas adalah remote mocked JWKS, bukan trusted-local provider→RS; approved actual provider-to-RS binding positive and full DB/provider/key/class/claim/company/user negative matrix. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V13.01`: Explicit local trusted binding off by default;
- `V13.02`: wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user all reject.
- `V13.03`: Approved valid provider access token passes same RS verifier.
- `V13.04`: No ID token or generic JWT;
- `V13.05`: no weakening, implicit trust or fallback.

### V14

**Oracle sumber (bukan acceptance derivatif):** Exercise actual merged-registry classification/backend path with no classification mock; backend selected once with bounded call count; verify the bounded internal interface receives explicit identity/arguments and does not consume bearer or Basic from ambient request, including when ambient headers differ; local errors fail closed, zero introspection/self-provider HTTP including key/metadata/failure; calibrated transport instrumentation. Remote branch independently retains approved security and transport.

**Gap Gen5:** L216–217 positive sebelum removal; L224 Unauthorized sesudah removal; fetch_json mock bukan observasi seluruh jaringan. Merged-registry classification, explicit-vs-ambient credentials, bounded backend and calibrated HTTP/socket egress, remote branch. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V14.01`: Exercise actual merged-registry classification/backend path with no classification mock;
- `V14.02`: backend selected once with bounded call count;
- `V14.03`: verify the bounded internal interface receives explicit identity/arguments and does not consume bearer or Basic from ambient request, including when ambient headers differ;
- `V14.04`: local errors fail closed, zero introspection/self-provider HTTP including key/metadata/failure;
- `V14.05`: calibrated transport instrumentation.
- `V14.06`: Remote branch independently retains approved security and transport.

### V15

**Oracle sumber (bukan acceptance derivatif):** Pada Odoo 13 dan CPython 3.7.3 yang disetujui, dengan dependency terkwalifikasi dan database fresh terisolasi yang diotorisasi, periksa import, route, ACL, registry, urutan addon dan seluruh hasil test yang berlaku. Catat runtime aktual dan cleanup/readback; jangan mengekstrapolasi ke upgrade atau addon pihak ketiga.

**Gap Gen5:** full approved dependency qualification, order/ACL/registry/route matrix, unit suites and runtime readback. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V15.01`: Pada Odoo 13 dan CPython 3.7.3 yang disetujui, dengan dependency terkwalifikasi dan database fresh terisolasi yang diotorisasi, periksa import, route, ACL, registry, urutan addon dan seluruh hasil test yang berlaku.
- `V15.02`: Catat runtime aktual dan cleanup/readback;
- `V15.03`: jangan mengekstrapolasi ke upgrade atau addon pihak ketiga.

### V16

**Oracle sumber (bukan acceptance derivatif):** Review release and cross-issue impact: explicitly list five public API compatibility changes, deletion and external unknowns; preserve applicable sibling requirements and clarify that the proposed fixture is not accepted. Owner decisions, security risk and hash approval separately recorded; no waiver inferred.

**Gap Gen5:** five API compatibility changes, deletion/external impacts, sibling requirements and owner/security/hash decisions. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `V16.01`: Review release and cross-issue impact: explicitly list five public API compatibility changes, deletion and external unknowns;
- `V16.02`: preserve applicable sibling requirements and clarify that the proposed fixture is not accepted.
- `V16.03`: Owner decisions, security risk and hash approval separately recorded;
- `V16.04`: no waiver inferred.

### U01

**Oracle sumber (bukan acceptance derivatif):** Fresh provider only and RS only: each starts, imports and works in its own existing bounded capability without the other/integration; no implicit trust. Verify actual installed closures.

**Gap Gen5:** complete installed closures/no implicit trust and bounded capability of each. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U01.01`: Fresh provider only and RS only: each starts, imports and works in its own existing bounded capability without the other/integration;
- `U01.02`: no implicit trust.
- `U01.03`: Verify actual installed closures.

### U02

**Oracle sumber (bukan acceptance derivatif):** Fresh both install orders without integration: both load; no new trusted profile/key or local acceptance. Record closure, effective registry/method ownership, ACL and configuration.

**Gap Gen5:** both install orders, no trust/local acceptance, effective ownership, ACL and config. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U02.01`: Fresh both install orders without integration: both load;
- `U02.02`: no new trusted profile/key or local acceptance.
- `U02.03`: Record closure, effective registry/method ownership, ACL and configuration.

### U03

**Oracle sumber (bukan acceptance derivatif):** With chosen integration installed but disabled: baseline unaffected, no new trust; remove/disable backend while enabled => fail closed, no silent HTTP/introspection. Include provider-only, RS-only and optional amr_token legacy adapter if supported.

**Gap Gen5:** disabled integration vs disabled backend, fail closed/no fallback and optional legacy adapter. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U03.01`: With chosen integration installed but disabled: baseline unaffected, no new trust;
- `U03.02`: remove/disable backend while enabled => fail closed, no silent HTTP/introspection.
- `U03.03`: Include provider-only, RS-only and optional amr_token legacy adapter if supported.

### U04

**Oracle sumber (bukan acceptance derivatif):** Positive: approved local issuer uses real selected issuance path with approved authenticated user/client and real synthetic RS256 key. Confirm actual header and required claims, valid exact RS policy, resolver/binding, eligible user; verify RS returns accepted verified provenance and correct user. Not a handcrafted token standing in for issuer.

**Gap Gen5:** authenticated selected issuance through actual RS verifier, policy/binding/user/provenance. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U04.01`: Positive: approved local issuer uses real selected issuance path with approved authenticated user/client and real synthetic RS256 key.
- `U04.02`: Confirm actual header and required claims, valid exact RS policy, resolver/binding, eligible user;
- `U04.03`: verify RS returns accepted verified provenance and correct user.
- `U04.04`: Not a handcrafted token standing in for issuer.

### U05

**Oracle sumber (bukan acceptance derivatif):** Signature tamper, different key, wrong kty, RSA <2048, none/HS256/other alg, invalid key, malformed/oversize token, forbidden jku/x5u/jwk/crit, wrong/missing typ, ID-token confusion => reject, no user/session.

**Gap Gen5:** tamper, kty, short RSA, algorithm matrix, oversize, forbidden headers, typ/ID confusion, no user dan no session untuk setiap negative. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U05.01`: Signature tamper, different key, wrong kty, RSA <2048, none/HS256/other alg, invalid key, malformed/oversize token, forbidden jku/x5u/jwk/crit, wrong/missing typ, ID-token confusion => reject, no user/session.

### U06

**Oracle sumber (bukan acceptance derivatif):** Exact issuer wrong/untrusted/inactive/ambiguous or wrong DB/provider binding; absent/revoked/mismatched/duplicate kid and missing/ambiguous backend; caller-injected key reference => reject, never fallback. Apply selected local kid contract explicitly.

**Gap Gen5:** wrong DB/provider binding, revoked/duplicate/ambiguous kid/backend, injected key and no fallback. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U06.01`: Exact issuer wrong/untrusted/inactive/ambiguous or wrong DB/provider binding;
- `U06.02`: absent/revoked/mismatched/duplicate kid and missing/ambiguous backend;
- `U06.03`: caller-injected key reference => reject, never fallback.
- `U06.04`: Apply selected local kid contract explicitly.

### U07

**Oracle sumber (bukan acceptance derivatif):** Missing/wrong/malformed iss, aud (empty, mixed invalid, nonmatching), exp, iat, jti, sub, client_id; future iat/nbf, expired or exact boundary; optional nbf absent accepted only per agreed policy; strict claim typing and issuer/aud/client/azp independence. Each negative rejects.

**Gap Gen5:** all required claim/type/time boundary/optional nbf and azp variants in selected RS path. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U07.01`: Missing/wrong/malformed iss, aud (empty, mixed invalid, nonmatching), exp, iat, jti, sub, client_id;
- `U07.02`: future iat/nbf, expired or exact boundary;
- `U07.03`: optional nbf absent accepted only per agreed policy;
- `U07.04`: strict claim typing and issuer/aud/client/azp independence.
- `U07.05`: Each negative rejects.

### U08

**Oracle sumber (bukan acceptance derivatif):** Matching single/list audience, configured allowlist with one matching value, correct client_id, allowed azp present or explicitly allowed absent; mismatch, malformed, absent when required => reject. Never equate aud, client_id and azp.

**Gap Gen5:** matching single/list, allowlist and independent client_id/azp present/absent/malformed. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U08.01`: Matching single/list audience, configured allowlist with one matching value, correct client_id, allowed azp present or explicitly allowed absent;
- `U08.02`: mismatch, malformed, absent when required => reject.
- `U08.03`: Never equate aud, client_id and azp.

### U09

**Oracle sumber (bukan acceptance derivatif):** Unknown/ambiguous/disabled user, invalid binding, duplicate mapping, wrong company, portal/public/share/superuser, inactive and policy revision changed mid-validation => deny; fabricated or modified verified dict and wrong request context denied.

**Gap Gen5:** unknown/disabled/ambiguous users, company/role, mid-validation revision and forged verified context. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U09.01`: Unknown/ambiguous/disabled user, invalid binding, duplicate mapping, wrong company, portal/public/share/superuser, inactive and policy revision changed mid-validation => deny;
- `U09.02`: fabricated or modified verified dict and wrong request context denied.

### U10

**Oracle sumber (bukan acceptance derivatif):** Rotation: provision new key through selected trust-admin path; explicitly retain old key for approved window, validate both while allowed, switch signer, revoke/remove old then reject old and unknown kid; duplicates and stale cache fail closed; no private-key exposure. Validate expiry policy/backup/rollback per decided contract.

**Gap Gen5:** trust-admin rotation with overlap/revocation, stale caches, private exposure, expiry/backup/rollback. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U10.01`: Rotation: provision new key through selected trust-admin path;
- `U10.02`: explicitly retain old key for approved window, validate both while allowed, switch signer, revoke/remove old then reject old and unknown kid;
- `U10.03`: duplicates and stale cache fail closed;
- `U10.04`: no private-key exposure.
- `U10.05`: Validate expiry policy/backup/rollback per decided contract.

### U11

**Oracle sumber (bukan acceptance derivatif):** Failure isolation: no profile/provider, malformed key, policy mutation, ambiguous issuer, backend exception and disabled integration deny; existing remote configured profile still uses its established path and validation; no recursion in real merged registry/MRO and bounded backend call count.

**Gap Gen5:** backend exception/policy mutation/disabled integration, real merged MRO recursion and remote branch. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U11.01`: Failure isolation: no profile/provider, malformed key, policy mutation, ambiguous issuer, backend exception and disabled integration deny;
- `U11.02`: existing remote configured profile still uses its established path and validation;
- `U11.03`: no recursion in real merged registry/MRO and bounded backend call count.

### U12

**Oracle sumber (bukan acceptance derivatif):** Network oracle: instrument outbound HTTP client/transport plus process/socket egress for the entire selected validation call, including classification, discovery, JWKS/key and exception paths. Positive + negatives and unavailable provider: zero introspection AND zero outbound self-provider requests; retain captures/counters and prove observer with a controlled known request in separately authorized setup. Scope does not forbid unrelated traffic or remote validation; distinguish normal frontchannel and test harness.

**Gap Gen5:** entire validation instrumentation incl process/socket, positive/negative/unavailable, calibrated known request. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U12.01`: Network oracle: instrument outbound HTTP client/transport plus process/socket egress for the entire selected validation call, including classification, discovery, JWKS/key and exception paths.
- `U12.02`: Positive + negatives and unavailable provider: zero introspection AND zero outbound self-provider requests;
- `U12.03`: retain captures/counters and prove observer with a controlled known request in separately authorized setup.
- `U12.04`: Scope does not forbid unrelated traffic or remote validation;
- `U12.05`: distinguish normal frontchannel and test harness.

### U13

**Oracle sumber (bukan acceptance derivatif):** Security/operations: only trust-admin can change binding/key/algorithm; ordinary users cannot spoof profile or fetch private material; sanitize logs/response, no bearer/key/secret leakage; policy revisions invalidate stale provenance.

**Gap Gen5:** trust-admin write matrix, spoof/private access, response/log sanitization and revision invalidation. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U13.01`: Security/operations: only trust-admin can change binding/key/algorithm;
- `U13.02`: ordinary users cannot spoof profile or fetch private material;
- `U13.03`: sanitize logs/response, no bearer/key/secret leakage;
- `U13.04`: policy revisions invalidate stale provenance.

### U14

**Oracle sumber (bukan acceptance derivatif):** Install graph and contracts: no hard reverse dependency/import; verify selected optional composition, native registry, existing helper API/return types, disabled failure and legacy consumers without implicit trust. If upgrade/rollback becomes in scope, obtain separate requirements, authorization and evidence; no claim now.

**Gap Gen5:** reverse imports, installed optional composition/registry/API return types, disabled failure and legacy consumers. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U14.01`: Install graph and contracts: no hard reverse dependency/import;
- `U14.02`: verify selected optional composition, native registry, existing helper API/return types, disabled failure and legacy consumers without implicit trust.
- `U14.03`: If upgrade/rollback becomes in scope, obtain separate requirements, authorization and evidence;
- `U14.04`: no claim now.

### U15

**Oracle sumber (bukan acceptance derivatif):** Issuance security: unauthorized caller cannot set arbitrary sub/client_id/iss/alg; valid issuance generates fresh jti, approved iat/exp and typ, client identity derives from authenticated context; generic JWT, forged claim and replay-policy expectations per decision.

**Gap Gen5:** authenticated caller claim control, fresh jti, approved lifetime/typ, replay and forged claims. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U15.01`: Issuance security: unauthorized caller cannot set arbitrary sub/client_id/iss/alg;
- `U15.02`: valid issuance generates fresh jti, approved iat/exp and typ, client identity derives from authenticated context;
- `U15.03`: generic JWT, forged claim and replay-policy expectations per decision.

### U16

**Oracle sumber (bukan acceptance derivatif):** Pada kandidat tepat dan Odoo 13 / CPython 3.7.3 yang disetujui, verifikasi dependency closure serta instalasi/import, jalankan unit dan native integration suites yang berlaku, periksa API cryptography/PyJWT dan nama manifest; rekam command, jumlah, hasil, runtime dan dependency aktual. Jangan mengasumsikan kompatibilitas dari pin atau interpreter lain.

**Gap Gen5:** all applicable unit/native suites, actual full dependency closure, cryptography/PyJWT API and manifest names. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Klausa induk:**
- `U16.01`: Pada kandidat tepat dan Odoo 13 / CPython 3.7.3 yang disetujui, verifikasi dependency closure serta instalasi/import, jalankan unit dan native integration suites yang berlaku, periksa API cryptography/PyJWT dan nama manifest;
- `U16.02`: rekam command, jumlah, hasil, runtime dan dependency aktual.
- `U16.03`: Jangan mengasumsikan kompatibilitas dari pin atau interpreter lain.

## Status klausa induk Gen5

Status oracle lengkap tetap NOT ASSESSED. Klaim EXECUTED PARTIAL sebelumnya tidak dapat diaudit dari bukti publik: setiap baris terdampak kini REDACTED / NOT ASSESSED, bukan hasil tes. STATIC UNIT dipertahankan sebagai klasifikasi historis, bukan bukti publik yang terverifikasi; rincian assertion dan hasilnya juga REDACTED / NOT ASSESSED. Residual dan koreksi adalah catatan historis, bukan pembuktian ulang. Lihat juga [G01, K01 dan V09-RT1](STEP4-CROSSWALK-RK-RUNTIME.md). U04 berkaitan dengan [D01-COMP-04](STEP4-CROSSWALK-D01.md) dan M07; U15 berkaitan dengan C01, C05, C06, M01, M06, T01, T04, T05, I01 dan I03 di [crosswalk C/T/M/I](STEP4-CROSSWALK-CT-MI.md). Referensi silang ini bukan bukti eksekusi.

| ID | Status historis | Residual / koreksi |
|---|---|---|
| `V01.01` | STATIC UNIT | Tidak membuktikan registry, instalasi fresh atau seluruh varian; aspek tersebut **NOT ASSESSED**; lihat gap Gen5 V01. |
| `V01.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V01; tidak membuktikan oracle lengkap. |
| `V01.03` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V01; tidak membuktikan oracle lengkap. |
| `V01.04` | STATIC UNIT | Hanya deklarasi statis, bukan resolusi method efektif atau bukti runtime; sisa klausa dan varian **NOT ASSESSED**. |
| `V01.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V01; tidak membuktikan oracle lengkap. |
| `V02.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V02; tidak membuktikan oracle lengkap. |
| `V02.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V02; tidak membuktikan oracle lengkap. |
| `V03.01` | REDACTED / NOT ASSESSED | Selector terpisah dari V03.02; tidak membuktikan komposisi berpasangan kedua basis tanpa glue maupun kedua urutan fresh install. Sisa klausa dan varian **NOT ASSESSED**. |
| `V03.02` | REDACTED / NOT ASSESSED | Selector terpisah dari V03.01; tidak membuktikan komposisi berpasangan kedua basis tanpa glue maupun kedua urutan fresh install; unknown issuer tidak dibuktikan oleh assertion ini. Sisa klausa dan varian **NOT ASSESSED**. |
| `V03.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V03; tidak membuktikan oracle lengkap. |
| `V03.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V03; tidak membuktikan oracle lengkap. **Koreksi:** Review bersama Lead dan sibling owners, bukan keputusan terpisah. |
| `V03.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V03; tidak membuktikan oracle lengkap. |
| `V04.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V04; tidak membuktikan oracle lengkap. |
| `V04.02` | STATIC UNIT | Tidak membuktikan effective MRO, dispatch, sentinel, seluruh retained RS declarations, trust atau activation; aspek tersebut dan varian lainnya **NOT ASSESSED**. |
| `V04.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V04; tidak membuktikan oracle lengkap. |
| `V05.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.06` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.07` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V06.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. **Koreksi:** Satu review/approval kontrak usulan helper/pass-through dan oracle terkait; jangan mengarang keputusan terpisah. |
| `V06.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.06` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V07.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V07; tidak membuktikan oracle lengkap. |
| `V07.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V07; tidak membuktikan oracle lengkap. **Koreksi:** Penolakan hanya untuk kombinasi actor/channel yang menurut kontrak memang ditolak, termasuk forged context; untuk setiap denial buktikan sebelum cache dan signing termasuk warm hit. Gen5 hanya cross-user sebelum signing; unit warm-cache statis bukan bukti semua channel. |
| `V07.03` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V07; tidak membuktikan oracle lengkap. **Koreksi:** L131,133,135 hanya denial dan pesan; tidak mengobservasi storage atau signer. |
| `V08.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. |
| `V08.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. **Koreksi:** Decoded default audience dan rejection explicit None tidak membuktikan invocation helper tanpa argumen audience. |
| `V08.03` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. |
| `V08.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. |
| `V09.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. **Koreksi:** Concurrency mencakup explicit invalidation, bukan hanya perubahan lain. |
| `V09.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. **Koreksi:** Key removal setelah warm issuance hanya mengassert ValueError; tidak mengobservasi signer atau stale cache hit/return. |
| `V09.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. |
| `V09.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. |
| `V10.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V10.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. **Koreksi:** L97 hanya mengassert exception, bukan no signer/cache; detail denial menunggu approval kontrak. Exception terhadap default hanya jika Owner menyetujui secara terpisah. |
| `V10.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V10.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V10.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V11.01` | STATIC UNIT | Tidak membuktikan penghapusan pada closure first-party lain, alias/shim, instalasi atau resolusi runtime; aspek tersebut dan varian lainnya **NOT ASSESSED**. **Koreksi:** Both orders tidak menetapkan no-glue; jangan menambah pembatasan itu pada oracle. |
| `V11.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V11; tidak membuktikan oracle lengkap. |
| `V11.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V11; tidak membuktikan oracle lengkap. |
| `V12.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. **Koreksi:** Rekonsiliasi fixture relevan dan pemetaan sumber→target serta assertion actor/audience/cache/rejection/security dan legacy loader; kesetaraan daftar modul di target saja tidak membuktikan relokasi atau preservation. |
| `V12.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. |
| `V12.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. |
| `V12.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. |
| `V13.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V13.02` | NOT ASSESSED (trusted-local) | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. **Koreksi:** Dua negative test yang dikutip memakai remote mocked JWKS; bukan trusted-local provider→RS. Binding local dan negative terkait NOT ASSESSED. |
| `V13.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V13.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V13.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V14.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.04` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. **Koreksi:** L216–217 adalah positive sebelum key removal; L224 sesudah removal adalah Unauthorized. Mock fetch_json bukan observasi semua jaringan atau bukti zero introspection/self-provider HTTP. |
| `V14.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.06` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V15.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V15; tidak membuktikan oracle lengkap. **Koreksi:** Syarat bersama seluruh child: Odoo 13 dan CPython 3.7.3 yang disetujui, dependency terkwalifikasi, DB fresh terisolasi yang diotorisasi; static manifest/pin tidak membuktikan runtime atau closure. |
| `V15.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V15; tidak membuktikan oracle lengkap. **Koreksi:** Catat runtime aktual dan cleanup beserta readback; bukan hanya rencana cleanup. |
| `V15.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V15; tidak membuktikan oracle lengkap. |
| `V16.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. **Koreksi:** Lima metode: `is_user_allow_create_token`, `get_access_token`, `create_access_token`, `add_url_access_token`, `get_auto_login_url`; review kompatibilitas masing-masing, penghapusan mobile dan external unknowns tetap NOT ASSESSED. |
| `V16.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. |
| `V16.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. |
| `V16.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. |
| `U01.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U01; tidak membuktikan oracle lengkap. |
| `U01.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U01; tidak membuktikan oracle lengkap. |
| `U01.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U01; tidak membuktikan oracle lengkap. |
| `U02.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U02; tidak membuktikan oracle lengkap. |
| `U02.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U02; tidak membuktikan oracle lengkap. |
| `U02.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U02; tidak membuktikan oracle lengkap. |
| `U03.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U03; tidak membuktikan oracle lengkap. **Koreksi:** Evaluasi integrasi terpilih disabled dan baseline/no new trust dalam komposisi yang berlaku bersama U03.03; jangan menciptakan cross-product wajib yang tidak diterima. |
| `U03.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U03; tidak membuktikan oracle lengkap. **Koreksi:** Backend removed/disabled saat integrasi enabled: fail closed tanpa silent HTTP/introspection; rekonsiliasi komposisi yang berlaku tanpa mewajibkan cross-product tambahan. |
| `U03.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U03; tidak membuktikan oracle lengkap. **Koreksi:** Provider-only, RS-only dan adapter opsional jika didukung harus direkonsiliasi dengan kondisi disabled/backend U03.01/.02; applicability spesifik belum dipastikan. |
| `U04.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** U04.01–.04 adalah satu alur terintegrasi: issuer lokal yang disetujui memakai real selected issuance dengan user/client dan synthetic RS256 key; token yang sama divalidasi RS. |
| `U04.02` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** Header/claims, policy, resolver/binding dan eligible user harus diperiksa dalam satu alur U04.01–.04; static signer unit terpisah bukan pembukti end-to-end. |
| `U04.03` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** Verified provenance dan user harus keluar dari RS untuk token yang sama pada alur U04.01–.04; unit RS terpisah bukan alur issuer→RS. |
| `U04.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** Bukan handcrafted token sebagai pengganti issuer; ini syarat satu alur U04.01–.04. |
| `U05.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U05; tidak membuktikan oracle lengkap. |
| `U06.01` | NOT ASSESSED (trusted-local) | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. **Koreksi:** Setiap negative yang berlaku wajib reject DAN never fallback; test Gen5 remote JWKS bukan bukti trusted-local issuer/DB/provider binding atau semua varian. |
| `U06.02` | NOT ASSESSED (trusted-local) | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. **Koreksi:** Setiap negative yang berlaku wajib reject DAN never fallback sesuai selected local kid contract; Gen5 remote mocked JWKS bukan bukti local kid/backend matrix. |
| `U06.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. |
| `U06.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. |
| `U07.01` | REDACTED / NOT ASSESSED (klaim historis provider decoder; selected RS NOT ASSESSED) | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. **Koreksi:** Wrong/malformed nilai harus ditentukan oleh policy dan konteks; jangan menciptakan setiap nilai sebagai negative wajib. |
| `U07.02` | REDACTED / NOT ASSESSED | Selected RS verifier **NOT ASSESSED**; future iat, exact boundary, sisa klausa dan varian **NOT ASSESSED**. L236 memeriksa missing required claims, bukan time boundary. **Koreksi:** Future/boundary mengikuti agreed policy dan konteks; jangan mengasumsikan semua waktu tepat boundary selalu reject. |
| `U07.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. |
| `U07.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. **Koreksi:** Typing dan independence mengikuti policy/kontrak terpilih; bukan aturan nilai baru. |
| `U07.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. |
| `U08.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U08; tidak membuktikan oracle lengkap. **Koreksi:** Positive single/list, allowlist dan azp hadir/absent berlaku menurut policy yang disetujui, bukan semua kombinasi wajib. |
| `U08.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U08; tidak membuktikan oracle lengkap. **Koreksi:** Mismatch/malformed/absent hanya negative jika diwajibkan policy; jangan menambah bentuk atau cross-product wajib. |
| `U08.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U08; tidak membuktikan oracle lengkap. |
| `U09.01` | NOT ASSESSED (validation denial) | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U09; tidak membuktikan oracle lengkap. **Koreksi:** L40–41 menguji penolakan penulisan mapping/audience duplikat; L42–43 menguji penghapusan audience, bukan denial saat validasi token; seluruh denial validasi tetap NOT ASSESSED. |
| `U09.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U09; tidak membuktikan oracle lengkap. |
| `U10.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U10.02` | NOT ASSESSED | Retain/validate old and new, signer switch, trust-store revoke/remove old dan old/unknown kid rejection **NOT ASSESSED**. |
| `U10.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U10.04` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U10.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U11.01` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U11; tidak membuktikan oracle lengkap. **Koreksi:** Evidence yang dikutip hanya missing selected local key: positive sebelum removal dan Unauthorized setelahnya; tidak membuktikan failure matrix lainnya. |
| `U11.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U11; tidak membuktikan oracle lengkap. |
| `U11.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U11; tidak membuktikan oracle lengkap. |
| `U12.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U12.02` | NOT ASSESSED | Bukan process/socket-wide egress atau introspection observer; zero introspection dan zero self-provider outbound untuk positive, negatives dan unavailable provider **NOT ASSESSED**. |
| `U12.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U12.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U12.05` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U13.01` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. |
| `U13.02` | REDACTED / NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. **Koreksi:** ACL registry dan pembacaan client/verifier hanya slice akses; bukan bukti anti-spoof profile atau tidak tereksposnya seluruh private material. |
| `U13.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. |
| `U13.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. |
| `U14.01` | NOT ASSESSED | Assertion tersebut tidak memeriksa manifest addon dasar atau import-nya, sehingga tidak membuktikan ketiadaan hard reverse dependency maupun hard reverse import. |
| `U14.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U14; tidak membuktikan oracle lengkap. |
| `U14.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U14; tidak membuktikan oracle lengkap. |
| `U14.04` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U14; tidak membuktikan oracle lengkap. |
| `U15.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U15; tidak membuktikan oracle lengkap. **Koreksi:** Unit menggunakan fake/mocks client, mapping dan signer; tidak membuktikan unauthorized issuance end-to-end. |
| `U15.02` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U15; tidak membuktikan oracle lengkap. **Koreksi:** Unit menggunakan fake signer/provenance; tidak membuktikan fresh jti/claims atau authenticated identity pada real issuance. |
| `U15.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U15; tidak membuktikan oracle lengkap. |
| `U16.01` | STATIC UNIT | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U16; tidak membuktikan oracle lengkap. **Koreksi:** L95–96 hanya version dan license manifest; bukan dependency closure, runtime, instalasi atau suites. |
| `U16.02` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U16; tidak membuktikan oracle lengkap. |
| `U16.03` | NOT ASSESSED | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U16; tidak membuktikan oracle lengkap. |

## Subatom U10/U12 historis

Actor dan fixture berikut historis; rincian assertion, selector dan hasil REDACTED / NOT ASSESSED. Catatan residual bukan bukti publik yang dapat memverifikasi hasil, lifecycle atau egress.

| ID | Varian / fixture-actor | Status | Residual |
|---|---|---|---|
| U10.02.a | Retain old key untuk approved window; trust-admin | NOT ASSESSED | Overlap trust-store belum dibuktikan. |
| U10.02.b | Validasi old key selama window; trust-admin | NOT ASSESSED | Selected RS verifier belum dibuktikan. |
| U10.02.c | Validasi new key selama window; trust-admin | NOT ASSESSED | Selected RS verifier belum dibuktikan. |
| U10.02.d | Switch signer; trust-admin | NOT ASSESSED | Switch signer dalam lifecycle trust-store belum dibuktikan. |
| U10.02.e | Revoke/remove old key; trust-admin | NOT ASSESSED | Revocation trust-store belum dibuktikan. |
| U10.02.f | Reject old token sesudah revoke; selected RS | NOT ASSESSED | Tidak disamakan dengan local HS256 di bawah. |
| U10.02.g | Reject unknown kid; selected RS | NOT ASSESSED | Rotation lifecycle belum dibuktikan. |
| U10.related.a | Old-token decode dengan new local secret; synthetic user | REDACTED / NOT ASSESSED | Klaim historis `InvalidSignatureError` tidak dapat diverifikasi publik; bukan bukti trust-store revocation. |
| U12.02.a | Positive: zero introspection; selected call | NOT ASSESSED | Mock fetch bukan introspection monitor. |
| U12.02.b | Positive: zero self-provider outbound; selected call | NOT ASSESSED | Process/socket observer belum dibuktikan. |
| U12.02.c | Negatives: zero introspection; selected call | NOT ASSESSED | Mencakup semua negative yang berlaku, bukan hanya missing key. |
| U12.02.d | Negatives: zero self-provider outbound; selected call | NOT ASSESSED | Process/socket observer belum dibuktikan. |
| U12.02.e | Unavailable provider: zero introspection; selected call | NOT ASSESSED | Fixture unavailable belum dibuktikan. |
| U12.02.f | Unavailable provider: zero self-provider outbound; selected call | NOT ASSESSED | Fixture dan process/socket observer belum dibuktikan. |
| U12.related.a | Positive local key: patched fetch_json tidak dipanggil; synthetic profile | REDACTED / NOT ASSESSED | Klaim historis hanya mock; assertion dan hasil tidak dapat diverifikasi publik. |
| U12.related.b | Missing local key: patched fetch_json tidak dipanggil; synthetic profile | REDACTED / NOT ASSESSED | Klaim historis hanya mock dan tidak dapat diverifikasi publik; bukan semua outbound/introspection. |

## Inventaris ekspansi semantik

Child baru NOT ASSESSED / NOT RUN dan tidak mewarisi status induk. Dimensi adalah kandidat yang berlaku hanya menurut oracle dan kontrak terpilih, bukan kewajiban seluruh produk kartesian. Dari 92 disposisi SPLIT historis, tiga diperiksa terarah; **89 SPLIT parents belum diperiksa individual sepenuhnya**. Ekspansi tidak membuktikan kelengkapan semantik maupun acceptance.

| Induk | Disposisi |
|---|---|
| `V01.01` | SPLIT — `V01.01.01` each of five provider declarations absent |
| `V01.02` | BELUM DIPECAH — review semantik diperlukan; oracle asli: no glue selected; |
| `V01.03` | SPLIT — `V01.03.01` configured synthetic helper generate/decode succeeds; `V01.03.02` malformed configuration fails; `V01.03.03` missing configuration fails |
| `V01.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Verify provider declaration of `get_access_token` is glue-only; |
| `V01.05` | SPLIT — `V01.05.01` record effective public method status; `V01.05.02` record legacy impact |
| `V02.01` | SPLIT — `V02.01.01` each of five RS declarations retained; `V02.01.02` actual signatures verified; `V02.01.03` actual policy verified; `V02.01.04` direct issuance fails; `V02.01.05` URL wrappers pass through |
| `V02.02` | SPLIT — `V02.02.01` synthetic RS verifier positive; `V02.02.02` synthetic RS verifier negative; `V02.02.03` provider absent from closure; `V02.02.04` glue absent from closure |
| `V03.01` | SPLIT — `V03.01.01` provider helper operation in provider-first fresh order; `V03.01.02` provider helper operation in RS-first fresh order |
| `V03.02` | SPLIT — `V03.02.01` RS positive; `V03.02.02` RS unknown issuer negative |
| `V03.03` | SPLIT — `V03.03.01` compare registry; `V03.03.02` compare MRO; `V03.03.03` compare signatures; `V03.03.04` compare actual method dispatch; `V03.03.05` compare nonsecret default trust snapshots; `V03.03.06` no glue introduced; `V03.03.07` no issuer introduced; `V03.03.08` no fallback introduced; `V03.03.09` no discovery introduced; `V03.03.10` no trust introduced |
| `V03.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; **Koreksi:** Review bersama Lead dan sibling owners, bukan keputusan terpisah. |
| `V03.05` | BELUM DIPECAH — review semantik diperlukan; oracle asli: do not demand an unaccepted public-method fixture or assert sibling pass here. |
| `V04.01` | SPLIT — `V04.01.01` glue explicit in provider-first order; `V04.01.02` glue explicit in RS-first order; `V04.01.03` auto_install false; `V04.01.04` no cyclic dependency; `V04.01.05` no base-to-glue dependency |
| `V04.02` | SPLIT — `V04.02.01` each moved method owner; `V04.02.02` private helper owner; `V04.02.03` sentinel owner; `V04.02.04` each retained RS declaration; `V04.02.05` effective MRO; `V04.02.06` no implicit trust; `V04.02.07` no accidental activation |
| `V04.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Dependency failure tested only using authorized isolated fixture. |
| `V05.01` | SPLIT — `V05.01.01` provider-only baseline hook true; `V05.01.02` provider-first no-glue baseline hook true; `V05.01.03` RS-first no-glue baseline hook true; `V05.01.04` glue baseline hook true; `V05.01.05` no super; `V05.01.06` no context flags; `V05.01.07` no registry sniffing |
| `V05.02` | SPLIT — `V05.02.01` true override shows Continue; `V05.02.02` false override hides Continue |
| `V05.03` | SPLIT — `V05.03.01` public rendering controlled; `V05.03.02` authenticated user rendering controlled |
| `V05.04` | SPLIT — `V05.04.01` no moved policy call; `V05.04.02` no glue call; `V05.04.03` no signer call; `V05.04.04` no token call |
| `V05.05` | BELUM DIPECAH — review semantik diperlukan; oracle asli: verify no issuance. |
| `V05.06` | SPLIT — `V05.06.01` direct authorize/continue unsupported; `V05.06.02` direct submit unsupported |
| `V05.07` | SPLIT — `V05.07.01` old override impact documented; `V05.07.02` custom addon impact documented |
| `V06.01` | SPLIT — `V06.01.01` first RS GET route; `V06.01.02` second RS GET route; `V06.01.03` RS-only composition; `V06.01.04` provider-first no-glue composition; `V06.01.05` RS-first no-glue composition; `V06.01.06` glue composition; `V06.01.07` auto_login type; `V06.01.08` access_token type; `V06.01.09` URL branch; `V06.01.10` malformed type; `V06.01.11` absent URL; `V06.01.12` internal model path; `V06.01.13` public model path; `V06.01.14` model get_url_access_token direct-result branch; `V06.01.15` authentication failures |
| `V06.02` | SPLIT — `V06.02.01` status versus approved contract; `V06.02.02` shape versus approved contract; `V06.02.03` Location versus approved contract; `V06.02.04` headers versus approved contract |
| `V06.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; **Koreksi:** Satu review/approval kontrak usulan helper/pass-through dan oracle terkait; jangan mengarang keputusan terpisah. |
| `V06.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. |
| `V06.05` | BELUM DIPECAH — review semantik diperlukan; oracle asli: If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. |
| `V06.06` | SPLIT — `V06.06.01` independent generic redirect/open-redirect review; `V06.06.02` independent model-generated URL risk review |
| `V07.01` | SPLIT — `V07.01.01` self actor; `V07.01.02` ordinary different actor; `V07.01.03` system actor; `V07.01.04` singleton; `V07.01.05` empty recordset; `V07.01.06` multiple recordset; `V07.01.07` policy false; `V07.01.08` inactive target where contract says; `V07.01.09` unauthorized target where contract says |
| `V07.02` | SPLIT — `V07.02.01` RPC denial; `V07.02.02` machine denial; `V07.02.03` public denial; `V07.02.04` portal denial; `V07.02.05` forged context denial; `V07.02.06` warm hit denial before cache; `V07.02.07` denial before signing **Koreksi:** Penolakan hanya untuk kombinasi actor/channel yang menurut kontrak memang ditolak, termasuk forged context; untuk setiap denial buktikan sebelum cache dan signing termasuk warm hit. Gen5 hanya cross-user sebelum signing; unit warm-cache statis bukan bukti semua channel. |
| `V07.03` | SPLIT — `V07.03.01` persistent create_access_token controlled denial; `V07.03.02` no storage; `V07.03.03` no signature **Koreksi:** L131,133,135 hanya denial dan pesan; tidak mengobservasi storage atau signer. |
| `V08.01` | SPLIT — `V08.01.01` sentinel in defaults; `V08.01.02` sentinel in wrappers; `V08.01.03` sentinel in cache; `V08.01.04` sentinel at private boundary |
| `V08.02` | SPLIT — `V08.02.01` omitted audience passes no helper audience argument; `V08.02.02` explicit None rejects **Koreksi:** Decoded default audience dan rejection explicit None tidak membuktikan invocation helper tanpa argumen audience. |
| `V08.03` | SPLIT — `V08.03.01` empty audience; `V08.03.02` malformed audience; `V08.03.03` valid string audience; `V08.03.04` valid list audience; `V08.03.05` list tuple roundtrip; `V08.03.06` resource precedence; `V08.03.07` invalid resource rejects |
| `V08.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: No sentinel identity substitution from token_helper. |
| `V09.01` | SPLIT — `V09.01.01` same uid; `V09.01.02` different uid; `V09.01.03` same normalized audience; `V09.01.04` different normalized audience; `V09.01.05` bucket rollover; `V09.01.06` actual expiry; `V09.01.07` policy change; `V09.01.08` key change; `V09.01.09` user change; `V09.01.10` company change; `V09.01.11` revision change; `V09.01.12` explicit invalidation; `V09.01.13` concurrent changes termasuk explicit invalidation; `V09.01.14` DB isolation **Koreksi:** Concurrency mencakup explicit invalidation, bukan hanya perubahan lain. |
| `V09.02` | SPLIT — `V09.02.01` stale hit never mints usable token; `V09.02.02` stale hit never returns usable token; `V09.02.03` unauthorized hit never mints usable token; `V09.02.04` unauthorized hit never returns usable token **Koreksi:** Key removal setelah warm issuance hanya mengassert ValueError; tidak mengobservasi signer atau stale cache hit/return. |
| `V09.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Expectations need approved lifecycle; |
| `V09.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: verify no cross-context leakage. |
| `V10.01` | SPLIT — `V10.01.01` direct URL helpers issue no default bearer into URLs; `V10.01.02` RPC issues no default bearer into URLs |
| `V10.02` | SPLIT — `V10.02.01` controlled denial pending contract; `V10.02.02` no signer use pending contract; `V10.02.03` no cache use pending contract; `V10.02.04` sanitized failure pending contract; `V10.02.05` auto-login type pending contract; `V10.02.06` explicit audience pending contract; `V10.02.07` explicit resource pending contract **Koreksi:** L97 hanya mengassert exception, bukan no signer/cache; detail denial menunggu approval kontrak. Exception terhadap default hanya jika Owner menyetujui secara terpisah. |
| `V10.03` | SPLIT — `V10.03.01` exception origin and redirect review; `V10.03.02` exception audience review; `V10.03.03` exception caller review; `V10.03.04` exception expiry review; `V10.03.05` exception replay review; `V10.03.06` exception leak-control review |
| `V10.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: do not infer approval. |
| `V10.05` | BELUM DIPECAH — review semantik diperlukan; oracle asli: No bearer in evidence. |
| `V11.01` | SPLIT — `V11.01.01` provider-only first-party removal and no alias/shim; `V11.01.02` RS-only first-party removal and no alias/shim; `V11.01.03` provider-first removal and no alias/shim; `V11.01.04` RS-first removal and no alias/shim; `V11.01.05` glue removal and no alias/shim; `V11.01.06` legacy adapter removal and no alias/shim **Koreksi:** Both orders tidak menetapkan no-glue; jangan menambah pembatasan itu pada oracle. |
| `V11.02` | SPLIT — `V11.02.01` record effective registry resolution; `V11.02.02` record direct result; `V11.02.03` record RPC result |
| `V11.03` | SPLIT — `V11.03.01` external consumers audit; `V11.03.02` dynamic consumers audit |
| `V12.01` | SPLIT — `V12.01.01` move relevant registered provider integration tests; `V12.01.02` move source-loaded standalone fixtures; `V12.01.03` move source-loaded security fixtures **Koreksi:** Rekonsiliasi fixture relevan dan pemetaan sumber→target serta assertion actor/audience/cache/rejection/security dan legacy loader; kesetaraan daftar modul di target saja tidak membuktikan relokasi atau preservation. |
| `V12.02` | SPLIT — `V12.02.01` preserve actor assertions; `V12.02.02` preserve audience assertions; `V12.02.03` preserve cache assertions; `V12.02.04` preserve rejection assertions; `V12.02.05` preserve security assertions |
| `V12.03` | SPLIT — `V12.03.01` independently run remaining provider issuer tests; `V12.03.02` reconcile amr_token legacy loader coverage; `V12.03.03` reconcile amr_token legacy alias coverage |
| `V12.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: No silently dropped cases. |
| `V13.01` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Explicit local trusted binding off by default; |
| `V13.02` | SPLIT — `V13.02.01` wrong provider; `V13.02.02` missing provider; `V13.02.03` ambiguous provider; `V13.02.04` wrong DB; `V13.02.05` missing DB; `V13.02.06` ambiguous DB; `V13.02.07` wrong issuer; `V13.02.08` missing issuer; `V13.02.09` ambiguous issuer; `V13.02.10` wrong client; `V13.02.11` missing client; `V13.02.12` ambiguous client; `V13.02.13` wrong kid; `V13.02.14` missing kid; `V13.02.15` ambiguous kid; `V13.02.16` wrong key; `V13.02.17` missing key; `V13.02.18` ambiguous key; `V13.02.19` wrong algorithm; `V13.02.20` missing algorithm; `V13.02.21` ambiguous algorithm; `V13.02.22` wrong token class; `V13.02.23` missing token class; `V13.02.24` ambiguous token class; `V13.02.25` wrong signature; `V13.02.26` missing signature; `V13.02.27` ambiguous signature; `V13.02.28` wrong claims; `V13.02.29` missing claims; `V13.02.30` ambiguous claims; `V13.02.31` wrong timing; `V13.02.32` missing timing; `V13.02.33` ambiguous timing; `V13.02.34` wrong audience; `V13.02.35` missing audience; `V13.02.36` ambiguous audience; `V13.02.37` wrong azp; `V13.02.38` missing azp; `V13.02.39` ambiguous azp; `V13.02.40` stale policy; `V13.02.41` stale provenance; `V13.02.42` wrong company; `V13.02.43` wrong user **Koreksi:** Dua negative test yang dikutip memakai remote mocked JWKS; bukan trusted-local provider→RS. Binding local dan negative terkait NOT ASSESSED. |
| `V13.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Approved valid provider access token passes same RS verifier. |
| `V13.04` | SPLIT — `V13.04.01` ID token rejected; `V13.04.02` generic JWT rejected |
| `V13.05` | SPLIT — `V13.05.01` no weakening; `V13.05.02` no implicit trust; `V13.05.03` no fallback |
| `V14.01` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Exercise actual merged-registry classification/backend path with no classification mock; |
| `V14.02` | BELUM DIPECAH — review semantik diperlukan; oracle asli: backend selected once with bounded call count; |
| `V14.03` | SPLIT — `V14.03.01` explicit identity passed; `V14.03.02` explicit arguments passed; `V14.03.03` ambient bearer not consumed; `V14.03.04` ambient Basic not consumed; `V14.03.05` different ambient headers do not control interface |
| `V14.04` | SPLIT — `V14.04.01` local errors fail closed; `V14.04.02` zero introspection; `V14.04.03` zero self-provider key HTTP; `V14.04.04` zero self-provider metadata HTTP; `V14.04.05` zero self-provider failure-path HTTP **Koreksi:** L216–217 adalah positive sebelum key removal; L224 sesudah removal adalah Unauthorized. Mock fetch_json bukan observasi semua jaringan atau bukti zero introspection/self-provider HTTP. |
| `V14.05` | BELUM DIPECAH — review semantik diperlukan; oracle asli: calibrated transport instrumentation. |
| `V14.06` | SPLIT — `V14.06.01` remote approved security retained; `V14.06.02` remote approved transport retained |
| `V15.01` | SPLIT — `V15.01.01` import; `V15.01.02` route; `V15.01.03` ACL; `V15.01.04` registry; `V15.01.05` addon order; `V15.01.06` applicable test results **Koreksi:** Syarat bersama seluruh child: Odoo 13 dan CPython 3.7.3 yang disetujui, dependency terkwalifikasi, DB fresh terisolasi yang diotorisasi; static manifest/pin tidak membuktikan runtime atau closure. |
| `V15.02` | SPLIT — `V15.02.01` record actual runtime; `V15.02.02` cleanup readback **Koreksi:** Catat runtime aktual dan cleanup beserta readback; bukan hanya rencana cleanup. |
| `V15.03` | SPLIT — `V15.03.01` no upgrade extrapolation; `V15.03.02` no third-party addon extrapolation |
| `V16.01` | SPLIT — `V16.01.01` each of five public API compatibility changes; `V16.01.02` deletion impact; `V16.01.03` external unknowns **Koreksi:** Lima metode: `is_user_allow_create_token`, `get_access_token`, `create_access_token`, `add_url_access_token`, `get_auto_login_url`; review kompatibilitas masing-masing, penghapusan mobile dan external unknowns tetap NOT ASSESSED. |
| `V16.02` | SPLIT — `V16.02.01` preserve applicable sibling requirements; `V16.02.02` proposed fixture not accepted |
| `V16.03` | SPLIT — `V16.03.01` record Owner decisions; `V16.03.02` record security risk; `V16.03.03` record hash approval |
| `V16.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: no waiver inferred. |
| `U01.01` | SPLIT — `U01.01.01` provider-only starts; `U01.01.02` provider-only imports; `U01.01.03` provider-only bounded capability; `U01.01.04` RS-only starts; `U01.01.05` RS-only imports; `U01.01.06` RS-only bounded capability |
| `U01.02` | BELUM DIPECAH — review semantik diperlukan; oracle asli: no implicit trust. |
| `U01.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Verify actual installed closures. |
| `U02.01` | SPLIT — `U02.01.01` provider-first no-integration loads; `U02.01.02` RS-first no-integration loads |
| `U02.02` | SPLIT — `U02.02.01` no new trusted profile; `U02.02.02` no new trusted key; `U02.02.03` no new local acceptance |
| `U02.03` | SPLIT — `U02.03.01` record closure; `U02.03.02` record effective registry; `U02.03.03` record method ownership; `U02.03.04` record ACL; `U02.03.05` record configuration |
| `U03.01` | SPLIT — `U03.01.01` disabled integration baseline unaffected; `U03.01.02` disabled integration no new trust **Koreksi:** Evaluasi integrasi terpilih disabled dan baseline/no new trust dalam komposisi yang berlaku bersama U03.03; jangan menciptakan cross-product wajib yang tidak diterima. |
| `U03.02` | SPLIT — `U03.02.01` enabled integration backend removed fails closed; `U03.02.02` enabled integration backend disabled fails closed; `U03.02.03` no silent HTTP; `U03.02.04` no silent introspection **Koreksi:** Backend removed/disabled saat integrasi enabled: fail closed tanpa silent HTTP/introspection; rekonsiliasi komposisi yang berlaku tanpa mewajibkan cross-product tambahan. |
| `U03.03` | SPLIT — `U03.03.01` provider-only; `U03.03.02` RS-only; `U03.03.03` optional amr_token legacy adapter if supported **Koreksi:** Provider-only, RS-only dan adapter opsional jika didukung harus direkonsiliasi dengan kondisi disabled/backend U03.01/.02; applicability spesifik belum dipastikan. |
| `U04.01` | SPLIT — `U04.01.01` approved authenticated user; `U04.01.02` approved authenticated client; `U04.01.03` real selected issuance path; `U04.01.04` real synthetic RS256 key **Koreksi:** U04.01–.04 adalah satu alur terintegrasi: issuer lokal yang disetujui memakai real selected issuance dengan user/client dan synthetic RS256 key; token yang sama divalidasi RS. |
| `U04.02` | SPLIT — `U04.02.01` actual header; `U04.02.02` required claims; `U04.02.03` exact RS policy; `U04.02.04` resolver; `U04.02.05` binding; `U04.02.06` eligible user **Koreksi:** Header/claims, policy, resolver/binding dan eligible user harus diperiksa dalam satu alur U04.01–.04; static signer unit terpisah bukan pembukti end-to-end. |
| `U04.03` | SPLIT — `U04.03.01` accepted verified provenance; `U04.03.02` correct user **Koreksi:** Verified provenance dan user harus keluar dari RS untuk token yang sama pada alur U04.01–.04; unit RS terpisah bukan alur issuer→RS. |
| `U04.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Not a handcrafted token standing in for issuer. **Koreksi:** Bukan handcrafted token sebagai pengganti issuer; ini syarat satu alur U04.01–.04. |
| `U05.01` | SPLIT — `U05.01.01` signature tamper; `U05.01.02` different key; `U05.01.03` wrong kty; `U05.01.04` RSA below 2048; `U05.01.05` none algorithm; `U05.01.06` HS256 algorithm; `U05.01.07` other algorithm; `U05.01.08` invalid key; `U05.01.09` malformed token; `U05.01.10` oversize token; `U05.01.11` forbidden jku; `U05.01.12` forbidden x5u; `U05.01.13` forbidden jwk; `U05.01.14` forbidden crit; `U05.01.15` wrong typ; `U05.01.16` missing typ; `U05.01.17` ID-token confusion |
| `U06.01` | SPLIT — `U06.01.01` wrong issuer; `U06.01.02` untrusted issuer; `U06.01.03` inactive issuer; `U06.01.04` ambiguous issuer; `U06.01.05` wrong DB binding; `U06.01.06` wrong provider binding **Koreksi:** Setiap negative yang berlaku wajib reject DAN never fallback; test Gen5 remote JWKS bukan bukti trusted-local issuer/DB/provider binding atau semua varian. |
| `U06.02` | SPLIT — `U06.02.01` absent kid; `U06.02.02` revoked kid; `U06.02.03` mismatched kid; `U06.02.04` duplicate kid; `U06.02.05` missing backend; `U06.02.06` ambiguous backend **Koreksi:** Setiap negative yang berlaku wajib reject DAN never fallback sesuai selected local kid contract; Gen5 remote mocked JWKS bukan bukti local kid/backend matrix. |
| `U06.03` | SPLIT — `U06.03.01` caller-injected key reference rejected; `U06.03.02` no fallback |
| `U06.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Apply selected local kid contract explicitly. |
| `U07.01` | SPLIT — `U07.01.01` missing iss; `U07.01.02` wrong iss; `U07.01.03` malformed iss; `U07.01.04` missing aud; `U07.01.05` wrong aud; `U07.01.06` malformed aud; `U07.01.07` empty aud; `U07.01.08` mixed invalid aud; `U07.01.09` nonmatching aud; `U07.01.10` missing exp; `U07.01.11` wrong exp; `U07.01.12` malformed exp; `U07.01.13` missing iat; `U07.01.14` wrong iat; `U07.01.15` malformed iat; `U07.01.16` missing jti; `U07.01.17` wrong jti; `U07.01.18` malformed jti; `U07.01.19` missing sub; `U07.01.20` wrong sub; `U07.01.21` malformed sub; `U07.01.22` missing client_id; `U07.01.23` wrong client_id; `U07.01.24` malformed client_id **Koreksi:** Wrong/malformed nilai harus ditentukan oleh policy dan konteks; jangan menciptakan setiap nilai sebagai negative wajib. |
| `U07.02` | SPLIT — `U07.02.01` future iat; `U07.02.02` future nbf; `U07.02.03` expired; `U07.02.04` exact time boundary **Koreksi:** Future/boundary mengikuti agreed policy dan konteks; jangan mengasumsikan semua waktu tepat boundary selalu reject. |
| `U07.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: optional nbf absent accepted only per agreed policy; |
| `U07.04` | SPLIT — `U07.04.01` strict claim typing; `U07.04.02` issuer independence; `U07.04.03` audience independence; `U07.04.04` client_id independence; `U07.04.05` azp independence **Koreksi:** Typing dan independence mengikuti policy/kontrak terpilih; bukan aturan nilai baru. |
| `U07.05` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Each negative rejects. |
| `U08.01` | SPLIT — `U08.01.01` matching single audience; `U08.01.02` matching list audience; `U08.01.03` allowlist one match; `U08.01.04` correct client_id; `U08.01.05` allowed azp present; `U08.01.06` explicitly allowed azp absent **Koreksi:** Positive single/list, allowlist dan azp hadir/absent berlaku menurut policy yang disetujui, bukan semua kombinasi wajib. |
| `U08.02` | SPLIT — `U08.02.01` aud mismatch; `U08.02.02` aud malformed; `U08.02.03` aud absent when required; `U08.02.04` client_id mismatch; `U08.02.05` client_id malformed; `U08.02.06` client_id absent when required; `U08.02.07` azp mismatch; `U08.02.08` azp malformed; `U08.02.09` azp absent when required **Koreksi:** Mismatch/malformed/absent hanya negative jika diwajibkan policy; jangan menambah bentuk atau cross-product wajib. |
| `U08.03` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Never equate aud, client_id and azp. |
| `U09.01` | SPLIT — `U09.01.01` unknown user; `U09.01.02` ambiguous user; `U09.01.03` disabled user; `U09.01.04` invalid binding; `U09.01.05` duplicate mapping; `U09.01.06` wrong company; `U09.01.07` portal user; `U09.01.08` public user; `U09.01.09` share user; `U09.01.10` superuser; `U09.01.11` inactive user; `U09.01.12` policy revision changed mid-validation **Koreksi:** L40–41 menguji penolakan penulisan mapping/audience duplikat; L42–43 menguji penghapusan audience, bukan denial saat validasi token; seluruh denial validasi tetap NOT ASSESSED. |
| `U09.02` | SPLIT — `U09.02.01` fabricated verified dict; `U09.02.02` modified verified dict; `U09.02.03` wrong request context |
| `U10.01` | BELUM DIPECAH — review semantik diperlukan; oracle asli: Rotation: provision new key through selected trust-admin path; |
| `U10.02` | SPLIT: child yang telah ada di bagian U10/U12 di atas; tidak diduplikasi. |
| `U10.03` | SPLIT — `U10.03.01` duplicate keys fail closed; `U10.03.02` stale cache fails closed |
| `U10.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: no private-key exposure. |
| `U10.05` | SPLIT — `U10.05.01` expiry policy per decided contract; `U10.05.02` backup per decided contract; `U10.05.03` rollback per decided contract |
| `U11.01` | SPLIT — `U11.01.01` no profile; `U11.01.02` no provider; `U11.01.03` malformed key; `U11.01.04` policy mutation; `U11.01.05` ambiguous issuer; `U11.01.06` backend exception; `U11.01.07` disabled integration **Koreksi:** Evidence yang dikutip hanya missing selected local key: positive sebelum removal dan Unauthorized setelahnya; tidak membuktikan failure matrix lainnya. |
| `U11.02` | SPLIT — `U11.02.01` remote established path retained; `U11.02.02` remote validation retained |
| `U11.03` | SPLIT — `U11.03.01` no recursion in real merged registry/MRO; `U11.03.02` bounded backend call count |
| `U12.01` | SPLIT — `U12.01.01` HTTP client observer; `U12.01.02` transport observer; `U12.01.03` process egress observer; `U12.01.04` socket egress observer; `U12.01.05` classification path; `U12.01.06` discovery path; `U12.01.07` JWKS path; `U12.01.08` key path; `U12.01.09` exception path |
| `U12.02` | SPLIT: child yang telah ada di bagian U10/U12 di atas; tidak diduplikasi. |
| `U12.03` | SPLIT — `U12.03.01` retain captures; `U12.03.02` retain counters; `U12.03.03` calibrate observer with separately authorized known request |
| `U12.04` | SPLIT — `U12.04.01` unrelated traffic not forbidden; `U12.04.02` remote validation not forbidden |
| `U12.05` | SPLIT — `U12.05.01` distinguish normal frontchannel; `U12.05.02` distinguish test harness |
| `U13.01` | SPLIT — `U13.01.01` trust-admin binding changes; `U13.01.02` trust-admin key changes; `U13.01.03` trust-admin algorithm changes |
| `U13.02` | SPLIT — `U13.02.01` ordinary user cannot spoof profile; `U13.02.02` ordinary user cannot fetch private material **Koreksi:** ACL registry dan pembacaan client/verifier hanya slice akses; bukan bukti anti-spoof profile atau tidak tereksposnya seluruh private material. |
| `U13.03` | SPLIT — `U13.03.01` sanitized logs; `U13.03.02` sanitized response; `U13.03.03` no bearer leakage; `U13.03.04` no key leakage; `U13.03.05` no secret leakage |
| `U13.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: policy revisions invalidate stale provenance. |
| `U14.01` | SPLIT — `U14.01.01` no hard reverse dependency; `U14.01.02` no hard reverse import |
| `U14.02` | SPLIT — `U14.02.01` selected optional composition; `U14.02.02` native registry; `U14.02.03` existing helper API; `U14.02.04` existing helper return types; `U14.02.05` disabled failure; `U14.02.06` legacy consumers; `U14.02.07` no implicit trust |
| `U14.03` | SPLIT — `U14.03.01` separate requirements for upgrade/rollback; `U14.03.02` separate authorization for upgrade/rollback; `U14.03.03` separate evidence for upgrade/rollback |
| `U14.04` | BELUM DIPECAH — review semantik diperlukan; oracle asli: no claim now. |
| `U15.01` | SPLIT — `U15.01.01` unauthorized arbitrary sub; `U15.01.02` unauthorized arbitrary client_id; `U15.01.03` unauthorized arbitrary iss; `U15.01.04` unauthorized arbitrary alg **Koreksi:** Unit menggunakan fake/mocks client, mapping dan signer; tidak membuktikan unauthorized issuance end-to-end. |
| `U15.02` | SPLIT — `U15.02.01` fresh jti; `U15.02.02` approved iat; `U15.02.03` approved exp; `U15.02.04` approved typ; `U15.02.05` client identity from authenticated context **Koreksi:** Unit menggunakan fake signer/provenance; tidak membuktikan fresh jti/claims atau authenticated identity pada real issuance. |
| `U15.03` | SPLIT — `U15.03.01` generic JWT expectations per decision; `U15.03.02` forged claim expectations per decision; `U15.03.03` replay policy expectations per decision |
| `U16.01` | SPLIT — `U16.01.01` dependency closure; `U16.01.02` installation; `U16.01.03` import; `U16.01.04` applicable unit suite; `U16.01.05` applicable native integration suite; `U16.01.06` cryptography API; `U16.01.07` PyJWT API; `U16.01.08` manifest names **Koreksi:** L95–96 hanya version dan license manifest; bukan dependency closure, runtime, instalasi atau suites. |
| `U16.02` | SPLIT — `U16.02.01` record command; `U16.02.02` record count; `U16.02.03` record result; `U16.02.04` record actual runtime; `U16.02.05` record actual dependencies |
| `U16.03` | SPLIT — `U16.03.01` no compatibility assumption from pin; `U16.03.02` no compatibility assumption from other interpreter |

**Rekonsiliasi:** 124 induk unik; 92 memiliki disposisi SPLIT (termasuk 2 induk dengan child lama), 32 belum dipecah dan memerlukan review semantik; 458 child baru. Semua child baru NOT ASSESSED. Induk belum dipecah: `V01.02`, `V01.04`, `V03.04`, `V03.05`, `V04.03`, `V05.05`, `V06.03`, `V06.04`, `V06.05`, `V08.04`, `V09.03`, `V09.04`, `V10.04`, `V10.05`, `V12.04`, `V13.01`, `V13.03`, `V14.01`, `V14.02`, `V14.05`, `V16.04`, `U01.02`, `U01.03`, `U04.04`, `U06.04`, `U07.03`, `U07.05`, `U08.03`, `U10.01`, `U10.04`, `U13.04`, `U14.04`. Ini bukan sertifikasi kelengkapan varian: daftar tersebut dan kemungkinan dimensi yang masih tergabung harus ditelaah sebelum SCOPE dapat ditutup.

## Review semantik 32 disposisi tertunda — inventaris, bukan acceptance

Sumber UAT SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; identitas crosswalk internal sebelumnya REDACTED. Label internal DRAFT FINAL dipertahankan byte-identical; `ACCEPTANCE-METADATA.md` mencatat persetujuan Owner atas hash UAT tersebut. Semua child (.01 dst adalah suffix ID induk) dan atomic berikut **NOT ASSESSED**, actual **NOT RUN**; tidak mewarisi status induk. Atomic berarti satu kewajiban atau gate dalam konteks kasus lengkap, bukan sudah dibuktikan. Fixture, actor, varian dan outcome UAT tetap berlaku; gate belum disetujui tetap BLOCKED. Label BELUM DIPECAH sebelumnya dipertahankan historis dan disupersedi review di sini.

| Induk / sumber | Teks induk persis | Disposisi |
|---|---|---|
| `V01.02` / UAT L249 | no glue selected; | Atomic: tidak ada glue dipilih pada fresh provider-only; periksa closure aktual. |
| `V01.04` / UAT L249 | Verify provider declaration of `get_access_token` is glue-only; | Atomic: deklarasi provider get_access_token glue-only; bukan klaim resolusi public method efektif. |
| `V03.04` / UAT L261 | Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; | ATOMIC — review bersama Lead dan sibling owners atas kecukupan fixture terhadap accepted sibling oracle; tidak mensyaratkan keputusan terpisah. |
| `V03.05` / UAT L261 | do not demand an unaccepted public-method fixture or assert sibling pass here. | SPLIT .01 jangan menuntut fixture public-method belum diterima; .02 jangan klaim sibling pass dari fixture ini. |
| `V04.03` / UAT L267 | Dependency failure tested only using authorized isolated fixture. | Atomic: dependency failure diuji hanya pada fixture terisolasi yang diotorisasi; mode/outcome tidak dispesifikasi. |
| `V05.05` / UAT L273 | verify no issuance. | Atomic: verifikasi tidak ada issuance saat login rendering untuk masing-masing komposisi dan actor V05 yang berlaku; terpisah dari tidak adanya pemanggilan signer. |
| `V06.03` / UAT L279 | The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; | Review/approval kontrak bersama untuk usulan RS-owned route helper/pass-through dan oracle no-token tanpa memandang MRO; tidak mengasumsikan beberapa keputusan terpisah. Assertion khusus helper BLOCKED, actual NOT RUN sampai keputusan kontrak. |
| `V06.04` / UAT L279 | pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. | Atomic gate: assertion khusus helper BLOCKED, actual NOT RUN sampai keputusan kontrak V06.03. |
| `V06.05` / UAT L279 | If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. | SPLIT jika disetujui .01 instrument helper; .02 instrument signer; .03 verifikasi oracle usulan tanpa asumsi keamanan model branch. |
| `V08.04` / UAT L291 | No sentinel identity substitution from token_helper. | Atomic: tidak ada substitusi identitas sentinel dari token_helper; berlaku di batas glue V08. |
| `V09.03` / UAT L297 | Expectations need approved lifecycle; | Atomic gate: ekspektasi cache memerlukan lifecycle yang disetujui; jangan invent hasil. |
| `V09.04` / UAT L297 | verify no cross-context leakage. | SPLIT .01 tidak bocor antar uid; .02 audience ternormalisasi; .03 database; .04 policy; .05 key; .06 user; .07 company; .08 revision; uji konteks yang berlaku. |
| `V10.04` / UAT L303 | do not infer approval. | Atomic: jangan menyimpulkan approval exception; keputusan Owner terpisah tetap diperlukan. |
| `V10.05` / UAT L303 | No bearer in evidence. | Atomic: tidak ada bearer dalam evidence V10. |
| `V12.04` / UAT L315 | No silently dropped cases. | Atomic: rekonsiliasi kasus sebelum/sesudah pemindahan agar tidak ada kasus yang diam-diam hilang; terkait seluruh fixture dan suite V12. |
| `V13.01` / UAT L321 | Explicit local trusted binding off by default; | SPLIT .01 trusted local binding eksplisit; .02 binding off by default. |
| `V13.03` / UAT L321 | Approved valid provider access token passes same RS verifier. | Atomic: approved valid provider access token diterima verifier RS yang sama; bukan ID token/generic JWT; tergantung approval. |
| `V14.01` / UAT L327 | Exercise actual merged-registry classification/backend path with no classification mock; | SPLIT .01 exercise classification merged-registry aktual tanpa classification mock; .02 exercise backend path aktual tanpa classification mock. |
| `V14.02` / UAT L327 | backend selected once with bounded call count; | SPLIT .01 backend dipilih sekali; .02 jumlah pemanggilan backend bounded; batas numerik tambahan tidak ditetapkan. |
| `V14.05` / UAT L327 | calibrated transport instrumentation. | Atomic: transport instrumentation terkalibrasi; UAT L11 juga memerlukan HTTP client/transport dan process/socket egress serta kontrol positif yang diotorisasi terpisah. |
| `V16.04` / UAT L339 | no waiver inferred. | Atomic: tidak menyimpulkan waiver dari release review, keputusan Owner, risiko atau approval hash. |
| `U01.02` / UAT L345 | no implicit trust. | SPLIT .01 tidak ada implicit trust pada provider-only fresh; .02 pada RS-only fresh. |
| `U01.03` / UAT L345 | Verify actual installed closures. | SPLIT .01 verifikasi installed closure provider-only tanpa RS/integration; .02 RS-only tanpa provider/integration. |
| `U04.04` / UAT L363 | Not a handcrafted token standing in for issuer. | Atomic: token bukan handcrafted sebagai pengganti issuer; harus berasal dari selected real issuance path dan approved local issuer. |
| `U06.04` / UAT L375 | Apply selected local kid contract explicitly. | Atomic: terapkan selected local kid contract secara eksplisit pada varian U06; jangan mengarang kontrak. |
| `U07.03` / UAT L381 | optional nbf absent accepted only per agreed policy; | Atomic bersyarat: optional nbf absent diterima hanya menurut agreed policy; tanpa policy jangan menyimpulkan hasil. |
| `U07.05` / UAT L381 | Each negative rejects. | Atomic lintas varian: masing-masing negative U07 menolak secara individual; bukan klaim optional nbf absent selalu negatif. |
| `U08.03` / UAT L387 | Never equate aud, client_id and azp. | SPLIT .01 aud tidak disamakan dengan client_id; .02 aud dengan azp; .03 client_id dengan azp; uji sesuai policy. |
| `U10.01` / UAT L399 | Rotation: provision new key through selected trust-admin path; | Atomic: trust-admin melakukan provision new key melalui selected path; API dan mekanisme tidak diasumsikan. |
| `U10.04` / UAT L399 | no private-key exposure. | Atomic: tidak ada private-key exposure dalam rotasi U10; bukti tersanitasi. |
| `U13.04` / UAT L417 | policy revisions invalidate stale provenance. | Atomic: policy revision menginvalidasi stale provenance; mekanisme tidak diasumsikan. |
| `U14.04` / UAT L423 | no claim now. | Atomic: tidak ada klaim upgrade/rollback sekarang; requirement, authorization dan evidence terpisah jika masuk scope. |

## Overlay koreksi U05, V13 dan U07

Setiap negative U05 membutuhkan rejection, no user, dan no session secara independen; child outcome NOT ASSESSED / NOT RUN.

| Varian negative | No user | No session |
|---|---|---|
| `U05.01.01` signature tamper | `U05.01.01.a` no user | `U05.01.01.b` no session |
| `U05.01.02` different key | `U05.01.02.a` no user | `U05.01.02.b` no session |
| `U05.01.03` wrong kty | `U05.01.03.a` no user | `U05.01.03.b` no session |
| `U05.01.04` RSA below 2048 | `U05.01.04.a` no user | `U05.01.04.b` no session |
| `U05.01.05` none algorithm | `U05.01.05.a` no user | `U05.01.05.b` no session |
| `U05.01.06` HS256 algorithm | `U05.01.06.a` no user | `U05.01.06.b` no session |
| `U05.01.07` other algorithm | `U05.01.07.a` no user | `U05.01.07.b` no session |
| `U05.01.08` invalid key | `U05.01.08.a` no user | `U05.01.08.b` no session |
| `U05.01.09` malformed token | `U05.01.09.a` no user | `U05.01.09.b` no session |
| `U05.01.10` oversize token | `U05.01.10.a` no user | `U05.01.10.b` no session |
| `U05.01.11` forbidden jku | `U05.01.11.a` no user | `U05.01.11.b` no session |
| `U05.01.12` forbidden x5u | `U05.01.12.a` no user | `U05.01.12.b` no session |
| `U05.01.13` forbidden jwk | `U05.01.13.a` no user | `U05.01.13.b` no session |
| `U05.01.14` forbidden crit | `U05.01.14.a` no user | `U05.01.14.b` no session |
| `U05.01.15` wrong typ | `U05.01.15.a` no user | `U05.01.15.b` no session |
| `U05.01.16` missing typ | `U05.01.16.a` no user | `U05.01.16.b` no session |
| `U05.01.17` ID-token confusion | `U05.01.17.a` no user | `U05.01.17.b` no session |

- **V13.02:** teks L321 menuliskan “wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user”. Daftar `.01`–`.39` di atas adalah kandidat pembacaan, **bukan matriks wajib**: khususnya missing/ambiguous signature, timing, token class, algorithm, claims, audience dan azp bukan otomatis fixture atau requirement independen. Pertahankan hanya varian yang secara semantik berlaku menurut klausa dan selected contract; contoh yang tak berlaku bersifat ilustratif/tidak diwajibkan. Missing azp tidak otomatis negatif: lihat U08 dan policy yang disetujui. `.40`–`.43` tetap sesuai stale policy/provenance dan wrong company/user; semua NOT ASSESSED. Tidak memutuskan kontrak melalui overlay ini.
- **U07.01:** L381 menyebut missing/wrong/malformed untuk klaim yang tercantum, tetapi arti “wrong” untuk exp/iat/jti/sub dan bentuk malformed atau nilai yang mungkin tidak dapat ditentukan sebagai salah tanpa policy, binding dan konteks. `.01`–`.24` tetap kandidat; nilai konkret yang bukan negative menurut accepted oracle/selected contract hanya ilustratif, tidak diwajibkan. Aud empty/mixed invalid/nonmatching tetap eksplisit; exp expired, iat/nbf future dan exact boundary mengikuti L381 serta policy yang berlaku. Optional nbf absent bukan otomatis negative. Tiap negative yang berlaku harus reject; semua child NOT ASSESSED.

Evidence provider decoder historis bukan selected RS verifier. Semua child tersebut NOT ASSESSED. Tidak ada klaim approval atau penggantian oracle.
