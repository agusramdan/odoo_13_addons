> **Riwayat f26 — bukan status saat ini.** Bagian historis di bawah mempertahankan inventaris statis kandidat `f26a674270467c85b7750073e085e9955e5461e1` dan pernyataan NOT RUN pada saat itu. Untuk Gen5 dan batas bukti terbaru lihat rekonsiliasi di akhir; tidak ada rebind otomatis.

# ADDONS13-79 — Step 4 V/U: inventaris statis belum lengkap

Source kandidat `f26a674270467c85b7750073e085e9955e5461e1`. UAT accepted `UAT.md` SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`, berdasarkan `ACCEPTANCE-METADATA.md`, meskipun label draft di byte UAT tetap ada. Acceptance bukan rebind, persetujuan final config atau izin runtime. Semua actual NOT RUN.

## Metode dan batas

Tiap kasus mempertahankan oracle lengkap verbatim dan membaginya menjadi klausa awal; daftar dipisahkan koma masih mengandung beberapa varian atomik. **Seluruh 32 kasus NOT ASSESSED pada tingkat oracle lengkap**: dekomposisi dan mapping tiap varian belum selesai. Ini bukan crosswalk atomik lengkap; belum dinilai bukan berarti test tidak ada. Mapping parsial disalin dari `STEP4-ASSERTION-CROSSWALK-STATIC.md` pada kandidat sebelumnya; AST memastikan class/method ada di kandidat ini dan diff pada tiga direktori test kosong. Assertion belum semuanya dinilai ulang; mock bukan bukti ORM, ACL, registry atau network.

Fixture/actor bersama menurut UAT: DB fresh disposable terverifikasi, komposisi per varian, synthetic issuer/client/user/company/credential/RSA, actor public/portal/internal/system/trust-admin/service sesuai kasus, jam terkendali, observer signer/cache/transport dan baseline legacy bila diperlukan. Observer zero self-provider HTTP harus dikalibrasi dan meliputi transport dan process/socket.

**Selector maksud, bukan command yang disetujui:** masing-masing mapping memakai `path::class::method`; unit adalah target runner unit repo, bukan registrasi native; integration adalah target method Odoo pada addon terkait. Sintaks runner/tag dan koleksi belum diverifikasi. `amr_oidc/tests/__init__.py` langsung mengimpor sebagian modul integration, tidak langsung `test_access_token_audience_presence`, dan tidak mengimpor `test_helper_decode`; `amr_oidc_resource/tests/__init__.py` langsung mengimpor dua modul integration; `amr_resource/tests/__init__.py` hanya mengimpor paket `integration` yang mengimpor tiga modul. Import source bukan bukti native loader menemukan atau menjalankan test tepat sekali. Tidak mengubah guard atau memakai alias untuk mengakali discovery.

V06: usulan helper route RS dan oracle no-token-regardless-of-MRO BLOCKED sampai kontrak disetujui; branch model dan risiko redirect perlu review independen. V10: default tidak boleh memasukkan bearer ke URL; denial rinci tetap usulan menunggu persetujuan. Pertahankan seluruh regresi dan assertion legacy termasuk `amr_token` loader/alias; jangan infer konversi dari nama test. Gate fresh mapping/RS-compatible profile, SCOPE-01, lifecycle, security dan final config tetap berlaku.

## Kasus

### V01

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L249; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Fresh provider-only: five provider declarations absent from provider; no glue selected; independent provider `_generate_user_token`→`decode` succeeds for explicitly configured synthetic fixture and malformed/missing configuration fails. Verify provider declaration of `get_access_token` is glue-only; record effective public method status and legacy impact without assuming core/third-party absence or a particular exception.

**Klausa awal — NOT ASSESSED:**
- V01.01: Fresh provider-only: five provider declarations absent from provider; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V01.02: no glue selected; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V01.03: independent provider `_generate_user_token`→`decode` succeeds for explicitly configured synthetic fixture and malformed/missing configuration fails. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V01.04: Verify provider declaration of `get_access_token` is glue-only; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V01.05: record effective public method status and legacy impact without assuming core/third-party absence or a particular exception. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.11 D01-COMP-01; v0.6 V01; v0.1 U01 | `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` L23 — synthetic secret and real provider helper path: decoded legacy sub/login and uid; missing secret raises ValueError. | integration; directly exposed by provider initializer; No independent fresh installation/closure or malformed full matrix; native execution NOT RUN.

### V02

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L255; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** RS-only: all five existing RS declarations retained, actual signatures and policy verified, direct issuance fails, URL wrappers pass through. Exercise separately configured synthetic RS verifier positive/negative, no provider/glue in closure.

**Klausa awal — NOT ASSESSED:**
- V02.01: RS-only: all five existing RS declarations retained, actual signatures and policy verified, direct issuance fails, URL wrappers pass through. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V02.02: Exercise separately configured synthetic RS verifier positive/negative, no provider/glue in closure. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V02 | PARTIAL | `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut08_user_predicates_environment_and_stubs` L170 asserts machine direct issuance raises UserError and three URL helper calls return the input URL. `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` L428 checks a synthetic RS256 positive and missing-claim negatives. Nested integration exposure only; no independently installed RS-only closure, five signatures or full policy matrix.

### V03

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L261; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Both bases no glue in both fresh install orders: provider independent helper operation; RS independent positive and unknown issuer negative; compare registry/MRO, signatures, actual method dispatch and default nonsecret trust snapshots, no glue, issuer, fallback/discovery or trust introduced. Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; do not demand an unaccepted public-method fixture or assert sibling pass here.

**Klausa awal — NOT ASSESSED:**
- V03.01: Both bases no glue in both fresh install orders: provider independent helper operation; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V03.02: RS independent positive and unknown issuer negative; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V03.03: compare registry/MRO, signatures, actual method dispatch and default nonsecret trust snapshots, no glue, issuer, fallback/discovery or trust introduced. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V03.04: Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V03.05: do not demand an unaccepted public-method fixture or assert sibling pass here. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V03 | PARTIAL | `amr_oidc/tests/unit/test_standalone_package.py::StandalonePackageTests::test_provider_manifest_does_not_require_token_or_resource_addons` L39 asserts those two manifest exclusions; `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314 rejects unknown issuer in a fake environment. Neither exercises both orders, registry/MRO, default trust snapshots, or #84 review.

### V04

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L267; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Glue explicitly installed in both orders, `auto_install=False`, no cyclic/base-to-glue dependency; verify moved five plus private helper/sentinel owner, retained RS source declarations and actual effective MRO, no implicit trust and no accidental activation. Dependency failure tested only using authorized isolated fixture.

**Klausa awal — NOT ASSESSED:**
- V04.01: Glue explicitly installed in both orders, `auto_install=False`, no cyclic/base-to-glue dependency; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V04.02: verify moved five plus private helper/sentinel owner, retained RS source declarations and actual effective MRO, no implicit trust and no accidental activation. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V04.03: Dependency failure tested only using authorized isolated fixture. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.11 D01-COMP-02; v0.11 D01-COMP-06; v0.8 G01; v0.6 V04; v0.6 V11; v0.1 U14 | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197 — manifest/AST checks exact dependencies, auto_install false; moved methods absent provider and present glue/RS; mobile absent provider. | offline unit; Source declarations only, not effective registry, all addons, install orders or no-alias audit.

### V05

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L273; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Login template on provider-only, RS+provider in both no-glue orders, glue: proposed provider-specific UI hook has baseline `True`, without `super`, context flags or registry sniffing; true/false override shows/hides Continue; public and authenticated user rendering stays controlled; no call to moved policy, glue, signer or token; verify no issuance. Exercise direct authorize/continue and submit routes: remain unsupported. Document old override/custom addon impact.

**Klausa awal — NOT ASSESSED:**
- V05.01: Login template on provider-only, RS+provider in both no-glue orders, glue: proposed provider-specific UI hook has baseline `True`, without `super`, context flags or registry sniffing; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V05.02: true/false override shows/hides Continue; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V05.03: public and authenticated user rendering stays controlled; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V05.04: no call to moved policy, glue, signer or token; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V05.05: verify no issuance. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V05.06: Exercise direct authorize/continue and submit routes: remain unsupported. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V05.07: Document old override/custom addon impact. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V05 | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_login_template_uses_provider_owned_visibility_hook` L262 — AST/XML source asserts provider hook exists and template calls it rather than moved policy. | offline unit; No actual render, route, actor or signer observation.

### V06

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L279; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Both RS GET routes in RS-only, both no-glue orders and glue, supported `auto_login`/`access_token`, URL branch, malformed type, absent URL, internal/public model paths, model `get_url_access_token` direct-result branch and auth failures; compare actual status/shape/Location/headers with approved contract. The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. Obtain independent security review of generic redirect/open-redirect and model-generated URL risks, not a blanket safety claim.

**Klausa awal — NOT ASSESSED:**
- V06.01: Both RS GET routes in RS-only, both no-glue orders and glue, supported `auto_login`/`access_token`, URL branch, malformed type, absent URL, internal/public model paths, model `get_url_access_token` direct-result branch and auth failures; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V06.02: compare actual status/shape/Location/headers with approved contract. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V06.03: The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V06.04: pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V06.05: If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V06.06: Obtain independent security review of generic redirect/open-redirect and model-generated URL risks, not a blanket safety claim. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V06; v0.11 D01-COMP-05 | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_resource_routes_use_resource_owned_url_passthrough` L250 — AST/source checks resource helper declaration and controller references it rather than add_url_access_token. | offline unit; No live dispatch, headers, model branch or both compositions.

### V07

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L285; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Glue direct access: self vs ordinary different actor vs system, singleton/empty/multiple, policy false, inactive/unauthorized where contract says; denied before cache and signing, even warm hit, across RPC/machine/public/portal and forged context. Test persistent `create_access_token` explicit controlled denial with no storage/signature.

**Klausa awal — NOT ASSESSED:**
- V07.01: Glue direct access: self vs ordinary different actor vs system, singleton/empty/multiple, policy false, inactive/unauthorized where contract says; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V07.02: denied before cache and signing, even warm hit, across RPC/machine/public/portal and forged context. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V07.03: Test persistent `create_access_token` explicit controlled denial with no storage/signature. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V07: actor vs target | `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims` — synthetic secret, self and system actor; decoded uid/sub equal target and not system actor | Glue top-level exposes module; legacy claims only, not fresh RS flow; full actor matrix absent. | PARTIAL
- v0.6 V07: unauthorized cross-user | `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_non_system_cross_user_denial_precedes_signing` — two internal users; AccessError and jwt.encode spy not called | Glue directly exposed; no warm-cache, RPC, public/portal or policy matrix in this method. | PARTIAL
- v0.8 C06; v0.7 T05; v0.6 V07; v0.6 V09 | `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup` L407 — fake warm cache: policy denial, cross-user actor denial, empty TTL error; no extra signer and lookup guard checked. | offline unit; Legacy fake only; not scoped fresh config, RPC or native cache.

### V08

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L291; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Glue omission sentinel survives defaults/wrappers/cache/private boundary; omitted argument causes helper call with no audience argument, explicit None rejects; empty/malformed vs valid string/list, list tuple roundtrip, resource precedence and invalid resource rejection. No sentinel identity substitution from token_helper.

**Klausa awal — NOT ASSESSED:**
- V08.01: Glue omission sentinel survives defaults/wrappers/cache/private boundary; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V08.02: omitted argument causes helper call with no audience argument, explicit None rejects; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V08.03: empty/malformed vs valid string/list, list tuple roundtrip, resource precedence and invalid resource rejection. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V08.04: No sentinel identity substitution from token_helper. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V08: omitted vs explicit null | `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_access_token_omission_defaults_but_explicit_none_is_rejected` — configured synthetic signer; omitted decoded aud equals database UUID; explicit None public/private raise ValueError | Glue directly exposed; this method does not assert signer not called after invalid input nor all sentinel boundaries. | PARTIAL

### V09

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L297; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Cache: same/different uid and normalized audiences, bucket rollover, actual expiry, policy/key/user/company/revision changes and explicit invalidation including concurrent changes, DB isolation; a stale/unauthorized hit never mints/returns a usable token. Expectations need approved lifecycle; verify no cross-context leakage.

**Klausa awal — NOT ASSESSED:**
- V09.01: Cache: same/different uid and normalized audiences, bucket rollover, actual expiry, policy/key/user/company/revision changes and explicit invalidation including concurrent changes, DB isolation; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V09.02: a stale/unauthorized hit never mints/returns a usable token. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V09.03: Expectations need approved lifecycle; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V09.04: verify no cross-context leakage. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V09: legacy bucket behavior | `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_legacy_cache_reuses_within_ttl_bucket_and_rolls_over` — controlled clocks; same token/one signer in bucket, changed token/two signers next bucket | Glue directly exposed; no concurrency, DB/company isolation or full invalidation matrix. | PARTIAL
- v0.8 C06; v0.7 T05; v0.6 V09 | `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_legacy_issuance_reuses_only_within_full_scoped_cache_key` L332 — fake ORM-cache simulator and controlled clock: same audience hits; audience, bucket, actor, secret, db name, registry and target changes increase signer count. | offline unit; Not real ORM cache, separate DBs, companies, expiry or concurrent workers.
- v0.8 C06; v0.7 T05; v0.6 V07; v0.6 V09 | `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup` L407 — fake warm cache: policy denial, cross-user actor denial, empty TTL error; no extra signer and lookup guard checked. | offline unit; Legacy fake only; not scoped fresh config, RPC or native cache.
- v0.8 C06; v0.7 T05; v0.6 V09; v0.7 K01 | `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_database_signing_key_material_change_cannot_cross_hit` L378 — fake key material changes with same timestamp; rotated token differs and fake signer count reaches two. | offline unit; No verifier propagation, real DB or incident containment.
- v0.7 T05; v0.6 V09 | `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_signing_configuration_change_during_cache_fill_fails_closed` L444 — fake signer rotates secret mid-call; ValueError and one signer call. | offline unit; No concurrent actual workers or signed-token validation.
- v0.7 T05; v0.6 V09 | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_legacy_cache_key_is_scoped_and_guarded_by_live_validation` L34 — AST checks cache dimensions and absence of secret literals; context before cache and access/TTL calls. | offline unit; Source ordering only, cannot establish live authorization, cache or isolation.
- v0.9 V09-RT1 historical version assertion | `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_pinned_dependency_and_python_runtime` L99–109: checks Python 3.8.20 and exact jwt, cryptography, cffi and pycparser versions. | Static test expectation only, not measured runtime, image, command or logs. v0.11 retargets runtime to 3.7.3; this historical assertion conflicts with that current target and is not evidence of compatibility.

### V10

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L303; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Glue direct URL helpers and RPC: default must issue no bearer into URLs; proposed controlled denial with no signer/cache use and sanitized failure for all types, including auto-login and explicit audience/resource, is pending exact contract approval. If Owner separately approves an exception, specify reviewed origin/redirect, audience, caller, expiry/replay and leak-control cases; do not infer approval. No bearer in evidence.

**Klausa awal — NOT ASSESSED:**
- V10.01: Glue direct URL helpers and RPC: default must issue no bearer into URLs; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V10.02: proposed controlled denial with no signer/cache use and sanitized failure for all types, including auto-login and explicit audience/resource, is pending exact contract approval. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V10.03: If Owner separately approves an exception, specify reviewed origin/redirect, audience, caller, expiry/replay and leak-control cases; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V10.04: do not infer approval. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V10.05: No bearer in evidence. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V10: URL denial | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_url_helpers_reject_bearer_creation` — offline loaded model, mock get_access_token; URLs and auto_login raise UserError, mock not called | Offline unit, not native; no real RPC, MRO or route assertions. | PARTIAL

### V11

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L309; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Delete mobile method in controlled first-party closure provider-only, RS-only, both orders, glue, legacy adapter: first-party declaration removal and no alias/shim; record effective registry resolution and direct/RPC result without assuming absence in Odoo core or third-party addons or any particular exception. Audit external/dynamic consumers separately.

**Klausa awal — NOT ASSESSED:**
- V11.01: Delete mobile method in controlled first-party closure provider-only, RS-only, both orders, glue, legacy adapter: first-party declaration removal and no alias/shim; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V11.02: record effective registry resolution and direct/RPC result without assuming absence in Odoo core or third-party addons or any particular exception. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V11.03: Audit external/dynamic consumers separately. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.11 D01-COMP-02; v0.11 D01-COMP-06; v0.8 G01; v0.6 V04; v0.6 V11; v0.1 U14 | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197 — manifest/AST checks exact dependencies, auto_install false; moved methods absent provider and present glue/RS; mobile absent provider. | offline unit; Source declarations only, not effective registry, all addons, install orders or no-alias audit.

### V12

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L315; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Move relevant registered provider integration tests and source-loaded standalone/security fixtures to correct glue target; preserve all applicable actor, audience, cache, rejection and security assertions; independently run remaining provider issuer tests and reconcile applicable `amr_token` legacy loader/alias coverage. No silently dropped cases.

**Klausa awal — NOT ASSESSED:**
- V12.01: Move relevant registered provider integration tests and source-loaded standalone/security fixtures to correct glue target; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V12.02: preserve all applicable actor, audience, cache, rejection and security assertions; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V12.03: independently run remaining provider issuer tests and reconcile applicable `amr_token` legacy loader/alias coverage. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V12.04: No silently dropped cases. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V12 | PARTIAL | `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestOdoo13TestDiscoveryContract::test_integration_modules_are_registered_in_root_tests_package` L502 compares glue integration filenames with root import bindings. It does not compare historical assertion inventory, prove native discovery, run remaining issuer tests or reconcile legacy loader.

### V13

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L321; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Explicit local trusted binding off by default; wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user all reject. Approved valid provider access token passes same RS verifier. No ID token or generic JWT; no weakening, implicit trust or fallback.

**Klausa awal — NOT ASSESSED:**
- V13.01: Explicit local trusted binding off by default; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V13.02: wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user all reject. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V13.03: Approved valid provider access token passes same RS verifier. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V13.04: No ID token or generic JWT; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V13.05: no weakening, implicit trust or fallback. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M07; v0.6 V13; v0.1 U04; v0.1 U05 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302 — synthetic RSA signed token against resource helper and fake environment: verified provenance, resolved user and claims; wrong signing key rejected. | offline unit; Handcrafted token and mocked registry/transport, not issuance route or installed RS.
- v0.8 M07; v0.6 V13; v0.1 U05; v0.1 U06 | `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_local_profile_loads_only_selected_key_on_valid_and_wrong_key_tokens` L84 — profile fixtures: selected issuer/key lookups exactly, no global search/fetch, wrong key Unauthorized. | integration; not in either initializer; Provider helper not actual selected RS route; module not exposed by either initializer; native discovery unverified.

### V14

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L327; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Exercise actual merged-registry classification/backend path with no classification mock; backend selected once with bounded call count; verify the bounded internal interface receives explicit identity/arguments and does not consume bearer or Basic from ambient request, including when ambient headers differ; local errors fail closed, zero introspection/self-provider HTTP including key/metadata/failure; calibrated transport instrumentation. Remote branch independently retains approved security and transport.

**Klausa awal — NOT ASSESSED:**
- V14.01: Exercise actual merged-registry classification/backend path with no classification mock; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V14.02: backend selected once with bounded call count; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V14.03: verify the bounded internal interface receives explicit identity/arguments and does not consume bearer or Basic from ambient request, including when ambient headers differ; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V14.04: local errors fail closed, zero introspection/self-provider HTTP including key/metadata/failure; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V14.05: calibrated transport instrumentation. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V14.06: Remote branch independently retains approved security and transport. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U12; v0.6 V14 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_local_key_no_loopback_or_local_bypass` L536 — synthetic local key fake profile verifies and mock fetch is not called. | offline unit; Not full selected call, classification, sockets or calibrated transport instrumentation.

### V15

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L333; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Pada Odoo 13 dan CPython 3.7.3 yang disetujui, dengan dependency terkwalifikasi dan database fresh terisolasi yang diotorisasi, periksa import, route, ACL, registry, urutan addon dan seluruh hasil test yang berlaku. Catat runtime aktual dan cleanup/readback; jangan mengekstrapolasi ke upgrade atau addon pihak ketiga.

**Klausa awal — NOT ASSESSED:**
- V15.01: Pada Odoo 13 dan CPython 3.7.3 yang disetujui, dengan dependency terkwalifikasi dan database fresh terisolasi yang diotorisasi, periksa import, route, ACL, registry, urutan addon dan seluruh hasil test yang berlaku. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V15.02: Catat runtime aktual dan cleanup/readback; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V15.03: jangan mengekstrapolasi ke upgrade atau addon pihak ketiga. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.6 V15 | PARTIAL | `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_native_loader_and_dependency_declarations` L111 asserts declared dependency names/pins and initializer imports, not a native loader run; `test_pinned_dependency_and_python_runtime` L99 asserts historical 3.8.20, conflicting with current v0.11 3.7.3 target. No installed runtime, DB, route/ACL or cleanup evidence.

### V16

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L339; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Review release and cross-issue impact: explicitly list five public API compatibility changes, deletion and external unknowns; preserve applicable sibling requirements and clarify that the proposed fixture is not accepted. Owner decisions, security risk and hash approval separately recorded; no waiver inferred.

**Klausa awal — NOT ASSESSED:**
- V16.01: Review release and cross-issue impact: explicitly list five public API compatibility changes, deletion and external unknowns; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V16.02: preserve applicable sibling requirements and clarify that the proposed fixture is not accepted. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V16.03: Owner decisions, security risk and hash approval separately recorded; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- V16.04: no waiver inferred. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Mapping NOT ASSESSED:** tidak ada mapping assertion-level teridentifikasi dalam review sebelumnya; selector dan registrasi yang memadai belum ditetapkan. Ini bukan pernyataan test tidak ada.

### U01

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L345; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Fresh provider only and RS only: each starts, imports and works in its own existing bounded capability without the other/integration; no implicit trust. Verify actual installed closures.

**Klausa awal — NOT ASSESSED:**
- U01.01: Fresh provider only and RS only: each starts, imports and works in its own existing bounded capability without the other/integration; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U01.02: no implicit trust. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U01.03: Verify actual installed closures. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.11 D01-COMP-01; v0.6 V01; v0.1 U01 | `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` L23 — synthetic secret and real provider helper path: decoded legacy sub/login and uid; missing secret raises ValueError. | integration; directly exposed by provider initializer; No independent fresh installation/closure or malformed full matrix; native execution NOT RUN.

### U02

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L351; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Fresh both install orders without integration: both load; no new trusted profile/key or local acceptance. Record closure, effective registry/method ownership, ACL and configuration.

**Klausa awal — NOT ASSESSED:**
- U02.01: Fresh both install orders without integration: both load; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U02.02: no new trusted profile/key or local acceptance. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U02.03: Record closure, effective registry/method ownership, ACL and configuration. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U02 | PARTIAL | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197 asserts static glue dependency list and opt-in setting and source method ownership. No installation orders, actual registry/ACL or trust configuration.

### U03

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L357; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** With chosen integration installed but disabled: baseline unaffected, no new trust; remove/disable backend while enabled => fail closed, no silent HTTP/introspection. Include provider-only, RS-only and optional amr_token legacy adapter if supported.

**Klausa awal — NOT ASSESSED:**
- U03.01: With chosen integration installed but disabled: baseline unaffected, no new trust; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U03.02: remove/disable backend while enabled => fail closed, no silent HTTP/introspection. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U03.03: Include provider-only, RS-only and optional amr_token legacy adapter if supported. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U03 | PARTIAL | `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileControllerTests::test_disabled_fresh_profile_preserves_unsupported_grant_contract` L157 asserts a fake disabled fresh profile delegates unsupported grant to legacy handler and does not issue fresh token. Disabled fresh issuance is not disabled integration/backend, and no real HTTP, introspection, base-only or adapter composition is established.

### U04

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L363; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Positive: approved local issuer uses real selected issuance path with approved authenticated user/client and real synthetic RS256 key. Confirm actual header and required claims, valid exact RS policy, resolver/binding, eligible user; verify RS returns accepted verified provenance and correct user. Not a handcrafted token standing in for issuer.

**Klausa awal — NOT ASSESSED:**
- U04.01: Positive: approved local issuer uses real selected issuance path with approved authenticated user/client and real synthetic RS256 key. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U04.02: Confirm actual header and required claims, valid exact RS policy, resolver/binding, eligible user; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U04.03: verify RS returns accepted verified provenance and correct user. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U04.04: Not a handcrafted token standing in for issuer. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.11 D01-COMP-04; v0.8 M07; v0.1 U04 | `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signing_produces_verifiable_rs256_at_jwt` L550 — generated synthetic RSA key and manual claims; signer output decoded by PyJWT; header RS256/kid/at+jwt and decoded claims equal. | offline unit; Not authenticated registered route, full issuer or actual RS verifier.
- v0.8 M07; v0.6 V13; v0.1 U04; v0.1 U05 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302 — synthetic RSA signed token against resource helper and fake environment: verified provenance, resolved user and claims; wrong signing key rejected. | offline unit; Handcrafted token and mocked registry/transport, not issuance route or installed RS.

### U05

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L369; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Signature tamper, different key, wrong kty, RSA <2048, none/HS256/other alg, invalid key, malformed/oversize token, forbidden jku/x5u/jwk/crit, wrong/missing typ, ID-token confusion => reject, no user/session.

**Klausa awal — NOT ASSESSED:**
- U05.01: Signature tamper, different key, wrong kty, RSA <2048, none/HS256/other alg, invalid key, malformed/oversize token, forbidden jku/x5u/jwk/crit, wrong/missing typ, ID-token confusion => reject, no user/session. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M07; v0.6 V13; v0.1 U04; v0.1 U05 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302 — synthetic RSA signed token against resource helper and fake environment: verified provenance, resolved user and claims; wrong signing key rejected. | offline unit; Handcrafted token and mocked registry/transport, not issuance route or installed RS.
- v0.8 M07; v0.1 U05 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat04_27_unsupported_token_classes_zero_egress` L331 — synthetic JWT headers typ JWT/None, jku/x5u/crit; HS256 and malformed shapes rejected; fake fetch not called. | offline unit; Not process/socket egress or complete algorithm/header matrix.
- v0.8 M07; v0.1 U05 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_x5c_does_not_replace_selected_trusted_rsa_key` L382 — fake JWKS x5c plus attacker header accepts trusted signature, rejects other key; two fetches. | offline unit; No transport or all forbidden header cases.
- v0.8 M07; v0.6 V13; v0.1 U05; v0.1 U06 | `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_local_profile_loads_only_selected_key_on_valid_and_wrong_key_tokens` L84 — profile fixtures: selected issuer/key lookups exactly, no global search/fetch, wrong key Unauthorized. | integration; not in either initializer; Provider helper not actual selected RS route; module not exposed by either initializer; native discovery unverified.

### U06

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L375; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Exact issuer wrong/untrusted/inactive/ambiguous or wrong DB/provider binding; absent/revoked/mismatched/duplicate kid and missing/ambiguous backend; caller-injected key reference => reject, never fallback. Apply selected local kid contract explicitly.

**Klausa awal — NOT ASSESSED:**
- U06.01: Exact issuer wrong/untrusted/inactive/ambiguous or wrong DB/provider binding; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U06.02: absent/revoked/mismatched/duplicate kid and missing/ambiguous backend; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U06.03: caller-injected key reference => reject, never fallback. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U06.04: Apply selected local kid contract explicitly. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M07; v0.1 U06; v0.1 U10 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` L369 — fake JWKS fetch twice; empty, duplicate, wrong key type/algorithm/use/key_ops and private fields reject. | offline unit; No real distributed rotation or PEM/JWKS independent trust inventory.
- v0.8 M07; v0.1 U06; v0.1 U09 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314 — synthetic signed tokens: unknown/malformed issuer, inactive/duplicate profile rejected; wrong company user resolution rejected. | offline unit; One fetch occurs on positive/wrong-company path; fake fetch only, no general zero-egress proof.
- v0.8 M07; v0.6 V13; v0.1 U05; v0.1 U06 | `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_local_profile_loads_only_selected_key_on_valid_and_wrong_key_tokens` L84 — profile fixtures: selected issuer/key lookups exactly, no global search/fetch, wrong key Unauthorized. | integration; not in either initializer; Provider helper not actual selected RS route; module not exposed by either initializer; native discovery unverified.
- v0.1 U06; v0.1 U11 | `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_registry_rejects_opaque_profile_and_consumer_fails_closed` L200 — profile fixture ValidationError, consumer Unauthorized and fetch mock not called. | integration; not in either initializer; Provider helper; unregistered module; no real merged-registry HTTP boundary.

### U07

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L381; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Missing/wrong/malformed iss, aud (empty, mixed invalid, nonmatching), exp, iat, jti, sub, client_id; future iat/nbf, expired or exact boundary; optional nbf absent accepted only per agreed policy; strict claim typing and issuer/aud/client/azp independence. Each negative rejects.

**Klausa awal — NOT ASSESSED:**
- U07.01: Missing/wrong/malformed iss, aud (empty, mixed invalid, nonmatching), exp, iat, jti, sub, client_id; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U07.02: future iat/nbf, expired or exact boundary; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U07.03: optional nbf absent accepted only per agreed policy; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U07.04: strict claim typing and issuer/aud/client/azp independence. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U07.05: Each negative rejects. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M07; v0.1 U07 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_required_claims_and_zero_leeway` L341 — synthetic signed claims missing iss/aud/exp/iat/jti/sub/client_id or invalid time/type/client rejected; fake fetch not called. | offline unit; No exact clock-at-exp assertion or native RS.

### U08

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L387; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Matching single/list audience, configured allowlist with one matching value, correct client_id, allowed azp present or explicitly allowed absent; mismatch, malformed, absent when required => reject. Never equate aud, client_id and azp.

**Klausa awal — NOT ASSESSED:**
- U08.01: Matching single/list audience, configured allowlist with one matching value, correct client_id, allowed azp present or explicitly allowed absent; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U08.02: mismatch, malformed, absent when required => reject. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U08.03: Never equate aud, client_id and azp. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M07; v0.1 U08 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat17_audience_any_exact` L352 — synthetic signed tokens with matching string/list verified, malformed or unmatched audiences rejected; fake fetch not called for negatives. | offline unit; No installed trust profile or live route.
- v0.8 M07; v0.1 U08 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat18_azp_optional_only_by_profile` L360 — fake profile toggles missing azp: rejects then verifies; invalid azp values rejected. | offline unit; No native profile or separate client mismatch matrix.

### U09

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L393; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Unknown/ambiguous/disabled user, invalid binding, duplicate mapping, wrong company, portal/public/share/superuser, inactive and policy revision changed mid-validation => deny; fabricated or modified verified dict and wrong request context denied.

**Klausa awal — NOT ASSESSED:**
- U09.01: Unknown/ambiguous/disabled user, invalid binding, duplicate mapping, wrong company, portal/public/share/superuser, inactive and policy revision changed mid-validation => deny; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U09.02: fabricated or modified verified dict and wrong request context denied. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M08; v0.1 U09 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat19_binding_exact_no_email_login_or_autobind` L586 — fake binding environment checks exact binding; no user reads for negative paths. | offline unit; Mock environment does not establish installed ACL, actual network or full actor matrix.
- v0.8 M07; v0.1 U06; v0.1 U09 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314 — synthetic signed tokens: unknown/malformed issuer, inactive/duplicate profile rejected; wrong company user resolution rejected. | offline unit; One fetch occurs on positive/wrong-company path; fake fetch only, no general zero-egress proof.

### U10

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L399; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Rotation: provision new key through selected trust-admin path; explicitly retain old key for approved window, validate both while allowed, switch signer, revoke/remove old then reject old and unknown kid; duplicates and stale cache fail closed; no private-key exposure. Validate expiry policy/backup/rollback per decided contract.

**Klausa awal — NOT ASSESSED:**
- U10.01: Rotation: provision new key through selected trust-admin path; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U10.02: explicitly retain old key for approved window, validate both while allowed, switch signer, revoke/remove old then reject old and unknown kid; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U10.03: duplicates and stale cache fail closed; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U10.04: no private-key exposure. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U10.05: Validate expiry policy/backup/rollback per decided contract. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 M07; v0.1 U06; v0.1 U10 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` L369 — fake JWKS fetch twice; empty, duplicate, wrong key type/algorithm/use/key_ops and private fields reject. | offline unit; No real distributed rotation or PEM/JWKS independent trust inventory.

### U11

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L405; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Failure isolation: no profile/provider, malformed key, policy mutation, ambiguous issuer, backend exception and disabled integration deny; existing remote configured profile still uses its established path and validation; no recursion in real merged registry/MRO and bounded backend call count.

**Klausa awal — NOT ASSESSED:**
- U11.01: Failure isolation: no profile/provider, malformed key, policy mutation, ambiguous issuer, backend exception and disabled integration deny; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U11.02: existing remote configured profile still uses its established path and validation; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U11.03: no recursion in real merged registry/MRO and bounded backend call count. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U06; v0.1 U11 | `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_registry_rejects_opaque_profile_and_consumer_fails_closed` L200 — profile fixture ValidationError, consumer Unauthorized and fetch mock not called. | integration; not in either initializer; Provider helper; unregistered module; no real merged-registry HTTP boundary.

### U12

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L411; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Network oracle: instrument outbound HTTP client/transport plus process/socket egress for the entire selected validation call, including classification, discovery, JWKS/key and exception paths. Positive + negatives and unavailable provider: zero introspection AND zero outbound self-provider requests; retain captures/counters and prove observer with a controlled known request in separately authorized setup. Scope does not forbid unrelated traffic or remote validation; distinguish normal frontchannel and test harness.

**Klausa awal — NOT ASSESSED:**
- U12.01: Network oracle: instrument outbound HTTP client/transport plus process/socket egress for the entire selected validation call, including classification, discovery, JWKS/key and exception paths. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U12.02: Positive + negatives and unavailable provider: zero introspection AND zero outbound self-provider requests; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U12.03: retain captures/counters and prove observer with a controlled known request in separately authorized setup. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U12.04: Scope does not forbid unrelated traffic or remote validation; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U12.05: distinguish normal frontchannel and test harness. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U12; v0.6 V14 | `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_local_key_no_loopback_or_local_bypass` L536 — synthetic local key fake profile verifies and mock fetch is not called. | offline unit; Not full selected call, classification, sockets or calibrated transport instrumentation.

### U13

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L417; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Security/operations: only trust-admin can change binding/key/algorithm; ordinary users cannot spoof profile or fetch private material; sanitize logs/response, no bearer/key/secret leakage; policy revisions invalidate stale provenance.

**Klausa awal — NOT ASSESSED:**
- U13.01: Security/operations: only trust-admin can change binding/key/algorithm; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U13.02: ordinary users cannot spoof profile or fetch private material; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U13.03: sanitize logs/response, no bearer/key/secret leakage; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U13.04: policy revisions invalidate stale provenance. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U13 / v0.8 M08: ordinary registry denial | `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_no_default_mapping_or_ordinary_registry_access` — ordinary internal user read/write/migrate denied; no default resolver and inline key write rejected | Only nested integration package exposed at resource top-level; native discovery unverified; does not prove all actors or binding RPC. | PARTIAL
- v0.8 M06; v0.1 U13 | `amr_oidc/tests/integration/test_client_secret_verifier.py::TestClientSecretVerifier::test_ordinary_user_can_read_client_but_not_verifier` L51 — ORM ordinary user reads client_id; secret verifier field read raises AccessError. | integration; directly exposed by provider initializer; No public/portal/trust-admin actors or actual RPC.
- v0.1 U13 | `amr_oidc/tests/integration/test_public_key_orm.py::TestPublicKeyORM::test_rsa_ec_jwks_active_signing_and_public_only` L128 — synthetic key ORM fixtures check JWKS key ids/types/alg and private RSA members disjoint. | integration; directly exposed by provider initializer; No full trust-admin ACL, response logging or deployed key material checks.

### U14

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L423; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Install graph and contracts: no hard reverse dependency/import; verify selected optional composition, native registry, existing helper API/return types, disabled failure and legacy consumers without implicit trust. If upgrade/rollback becomes in scope, obtain separate requirements, authorization and evidence; no claim now.

**Klausa awal — NOT ASSESSED:**
- U14.01: Install graph and contracts: no hard reverse dependency/import; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U14.02: verify selected optional composition, native registry, existing helper API/return types, disabled failure and legacy consumers without implicit trust. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U14.03: If upgrade/rollback becomes in scope, obtain separate requirements, authorization and evidence; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U14.04: no claim now. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.11 D01-COMP-02; v0.11 D01-COMP-06; v0.8 G01; v0.6 V04; v0.6 V11; v0.1 U14 | `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197 — manifest/AST checks exact dependencies, auto_install false; moved methods absent provider and present glue/RS; mobile absent provider. | offline unit; Source declarations only, not effective registry, all addons, install orders or no-alias audit.

### U15

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L429; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Issuance security: unauthorized caller cannot set arbitrary sub/client_id/iss/alg; valid issuance generates fresh jti, approved iat/exp and typ, client identity derives from authenticated context; generic JWT, forged claim and replay-policy expectations per decision.

**Klausa awal — NOT ASSESSED:**
- U15.01: Issuance security: unauthorized caller cannot set arbitrary sub/client_id/iss/alg; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U15.02: valid issuance generates fresh jti, approved iat/exp and typ, client identity derives from authenticated context; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U15.03: generic JWT, forged claim and replay-policy expectations per decision. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.8 C01; v0.8 C05; v0.8 C06; v0.8 M01; v0.8 M06; v0.7 T01; v0.7 T04; v0.7 T05; v0.7 I01; v0.7 I03; v0.1 U15 | `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` L363 — fake active client, mapping and signer: response TTL and exp-iat 900; issuer/audience/sub/client_id/azp, identifying claims absent; repeat reauth/config/signer twice; invalid overrides reject before signer/mapping; 60 response/claims. | offline unit; Signer mocked, no route/RS/DB; configured-TTL override, persistence, workers and full matrix remain.
- v0.8 M06; v0.1 U15 | `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signer_requires_bound_provenance_single_rs256_key_and_at_jwt` L514 — fake key and jwt.encode spy: bad provenance denied; positive header kid/at+jwt and RS256; secret mode and duplicate key denied without signer. | offline unit; Mock signer, not RS verifier or genuine authentication.

### U16

**Sumber accepted:** `docs/ADDONS13-79/UAT.md` L435; prasyarat dan fixture bersama L7–13; actual NOT RUN.

**Oracle accepted lengkap:** Pada kandidat tepat dan Odoo 13 / CPython 3.7.3 yang disetujui, verifikasi dependency closure serta instalasi/import, jalankan unit dan native integration suites yang berlaku, periksa API cryptography/PyJWT dan nama manifest; rekam command, jumlah, hasil, runtime dan dependency aktual. Jangan mengasumsikan kompatibilitas dari pin atau interpreter lain.

**Klausa awal — NOT ASSESSED:**
- U16.01: Pada kandidat tepat dan Odoo 13 / CPython 3.7.3 yang disetujui, verifikasi dependency closure serta instalasi/import, jalankan unit dan native integration suites yang berlaku, periksa API cryptography/PyJWT dan nama manifest; — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U16.02: rekam command, jumlah, hasil, runtime dan dependency aktual. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.
- U16.03: Jangan mengasumsikan kompatibilitas dari pin atau interpreter lain. — fixture/actor sesuai klausa dan prasyarat bersama; assertion, selector dan batas yang memadai untuk semua varian belum dipetakan.

**Petunjuk parsial review sebelumnya** (fixture/assertion dan keterbatasan; tidak membuktikan keseluruhan klausa):
- v0.1 U16 | PARTIAL | `amr_oidc/tests/unit/test_package_contract.py::PackageContract::test_candidate_manifest_identity_and_dependencies` L93 asserts manifest identity/dependency strings, explicitly not distribution/import-name compatibility. `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_pinned_dependency_and_python_runtime` L99 instead expects historical 3.8.20, not current 3.7.3. Neither proves runtime, suites or actual APIs.

## Rekonsiliasi

- 32 kasus: V01, V02, V03, V04, V05, V06, V07, V08, V09, V10, V11, V12, V13, V14, V15, V16, U01, U02, U03, U04, U05, U06, U07, U08, U09, U10, U11, U12, U13, U14, U15, U16.
- 31 kasus mempunyai petunjuk parsial, 1 tanpa petunjuk: V16. Semua 32 tetap NOT ASSESSED pada tingkat oracle lengkap; jumlah atomik total belum diketahui.
- Odoo loader/discovery, unit/integration suites dan UAT NOT RUN. Tidak ada akses DB, container, build atau pull dan tidak ada klaim PASS. Binding kandidat, keputusan gate, persetujuan konfigurasi final serta otorisasi yang berlaku dibutuhkan sebelum runtime.


## Indeks assertion kandidat (pemeriksaan statis tambahan)

Indeks ini melengkapi petunjuk per kasus, **bukan** mapping atomik yang selesai. `assertRaises` juga mungkin muncul sebagai context manager; deteksi nama tidak membuktikan assertion tercapai atau semantiknya benar. Nama modul dalam initializer bukan bukti Odoo discovery. `patch` yang dibuat melalui helper/setUp dapat tidak terlihat. Baris menunjukkan lokasi pada kandidat yang dipin.

- `amr_oidc/tests/integration/test_client_secret_verifier.py::TestClientSecretVerifier::test_ordinary_user_can_read_client_but_not_verifier` L51–59; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L57 `self.assertEqual(client.read(['client_id'])[0]['client_id'], 'secret-verifier-client')`; L58 `self.assertRaises(AccessError)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_local_profile_loads_only_selected_key_on_valid_and_wrong_key_tokens` L84–139; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L128 `self.assertEqual(verified['iss'], profile_a.issuer)`; L129 `self.assertEqual(key_reads, [profile_a.issuer])`; L130 `self.assertEqual(selections, [([('issuer', '=', profile_a.issuer), ('active', '=', True)], [profile_a.issuer])])`; L131 `self.assertEqual(lookups, [(profile_a.issuer, 'jwt', [profile_a.issuer])])`; L133 `self.assertRaises(Unauthorized)`; L135 `self.assertEqual(key_reads, [profile_a.issuer])`; L136 `self.assertEqual(selections, [([('issuer', '=', profile_a.issuer), ('active', '=', True)], [profile_a.issuer])])`; L137 `self.assertEqual(lookups, [(profile_a.issuer, 'jwt', [profile_a.issuer])])`; L138 `self.assertEqual(global_searches, [])`; L139 `self.assertEqual(fetches, [])`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/integration/test_helper_decode.py::TestOidcHelperDecode::test_registry_rejects_opaque_profile_and_consumer_fails_closed` L200–225; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L209 `self.assertRaises(ValidationError)`; L219 `self.assertEqual(raised.exception.args[0], 'Only manual JWT/JWKS or local-public profiles without introspection are supported.')`; L223 `self.assertRaises(Unauthorized)`; L225 `fetch.assert_not_called()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` L23–37; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L24 `self.assertIn('amr.oidc.helper', self.env.registry.models)`; L30 `self.assertEqual(decoded['sub'], self.env.user.login)`; L31 `self.assertEqual(decoded['uid'], self.env.user.id)`; L32 `self.assertEqual(claims['uid'], self.env.user.id)`; L35 `self.assertRaisesRegex(ValueError, 'JWT Secret not set')`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/integration/test_public_key_orm.py::TestPublicKeyORM::test_rsa_ec_jwks_active_signing_and_public_only` L128–157; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L145 `self.assertEqual(len(jwks), len(expected))`; L146 `self.assertEqual({jwk['kid'] for jwk in jwks}, set(expected))`; L149 `self.assertEqual(jwk['alg'], algorithm)`; L150 `self.assertEqual(jwk['kty'], key_type)`; L152 `self.assertEqual(jwk['use'], 'sig')`; L154 `self.assertNotIn('use', jwk)`; L155 `self.assertTrue({'d', 'p', 'q', 'dp', 'dq', 'qi', 'oth', 'k'}.isdisjoint(jwk))`; L157 `self.assertTrue(jwk[name])`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileControllerTests::test_disabled_fresh_profile_preserves_unsupported_grant_contract` L157–170; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L163 `self.assertEqual(response.status_code, 400)`; L164 `self.assertEqual(response.headers.get('Cache-Control'), 'no-store')`; L165 `self.assertEqual(response.headers.get('Pragma'), 'no-cache')`; L166 `self.assertEqual(self.support.json.loads(response.data), {'error': 'unsupported_grant_type'})`; L169 `self.helper._issue_fresh_client_token.assert_not_called()`; L170 `self.helper.sudo.return_value.oidc_token.assert_called_once_with()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` L363–438; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L396 `self.assertRaises(ValueError)`; L398 `mapping._get_or_create_subject.assert_not_called()`; L399 `signed.assert_not_called()`; L405 `self.assertEqual(result, {'access_token': 'signed-jwt', 'token_type': 'Bearer', 'expires_in': 900})`; L408 `self.assertEqual(claims['iss'], 'https://issuer.invalid')`; L409 `self.assertEqual(claims['aud'], 'service-a')`; L410 `self.assertEqual(claims['sub'], 'a' * 64)`; L411 `self.assertEqual(claims['client_id'], 'machine-a')`; L412 `self.assertEqual(claims['azp'], 'machine-a')`; L413 `self.assertEqual(claims['exp'] - claims['iat'], 900)`; L414 `self.assertFalse({'uid', 'user_id', 'login', 'db', 'email'}.intersection(claims))`; L415 `self.assertEqual(provenance.user_id, 7)`; L416 `client.check_credentials.assert_called_once_with('secret')`; L417 `mapping._get_or_create_subject.assert_called_once_with('https://issuer.invalid', 7)`; L419 `self.assertEqual(second['expires_in'], 900)`; L420 `self.assertEqual(signed.call_count, 2)`; L421 `self.assertEqual(client.check_credentials.call_count, 2)`; L422 `self.assertEqual(self.helper._get_fresh_profile_issuer.call_count, 2)`; L423 `self.assertEqual(self.helper._get_fresh_profile_ttl.call_count, 2)`; L429 `self.assertRaises(ValueError)`; L432 `self.assertEqual(mapping._get_or_create_subject.call_count, mappings_before_invalid_override)`; L434 `signed.assert_not_called()`; L436 `self.assertEqual(result['expires_in'], 60)`; L438 `self.assertEqual(claims['exp'] - claims['iat'], 60)`.
  - Mock/patch terdeteksi: L379 `mock.Mock(return_value=True)`; L383 `mock.Mock(return_value='a' * 64)`; L386 `mock.Mock(return_value='https://issuer.invalid')`; L387 `mock.Mock()`; L388 `mock.Mock(return_value=900)`; L389 `mock.Mock(return_value='public_key')`; L390 `mock.Mock(return_value='RS256')`; L391 `mock.Mock(return_value='signed-jwt')`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signer_requires_bound_provenance_single_rs256_key_and_at_jwt` L514–548; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L529 `self.assertRaises(self.support.AccessError)`; L533 `self.assertEqual(self.helper._sign_fresh_profile_token(claims, provenance), 'signed')`; L534 `signer.assert_called_once_with(claims, 'synthetic-private-key', algorithm='RS256', headers={'kid': 'fresh-rs-key', 'typ': 'at+jwt'})`; L540 `self.assertRaises(ValueError)`; L542 `signer.assert_not_called()`; L546 `self.assertRaises(ValueError)`; L548 `signer.assert_not_called()`.
  - Mock/patch terdeteksi: L522 `mock.Mock(return_value=keys)`; L524 `mock.Mock(return_value='public_key')`; L525 `mock.Mock(return_value='RS256')`; L528 `mock.patch.object(self.module.jwt, 'encode', return_value='signed', create=True)`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signing_produces_verifiable_rs256_at_jwt` L550–582; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L581 `self.assertEqual(header, {'alg': 'RS256', 'kid': 'synthetic-rs-kid', 'typ': 'at+jwt'})`; L582 `self.assertEqual(decoded, claims)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_package_contract.py::PackageContract::test_candidate_manifest_identity_and_dependencies` L93–102; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L95 `self.assertEqual(manifest['version'], '13.0.1.0.0')`; L96 `self.assertEqual(manifest['license'], 'LGPL-3')`; L97 `self.assertEqual(manifest['depends'], ['base', 'base_setup', 'web'])`; L99 `self.assertEqual(manifest['external_dependencies']['python'], ['pyjwt', 'cryptography'])`; L101 `self.assertTrue(manifest['data'])`; L102 `self.assertFalse(manifest.get('auto_install', False))`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_legacy_cache_key_is_scoped_and_guarded_by_live_validation` L34–83; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L43 `self.assertEqual(len(cache_decorators), 1)`; L60 `self.assertTrue({'uid', 'actor_uid', 'audience_key', 'dbname', 'registry_id', 'bucket', 'config_revision', 'policy_revision'} <= cache_dimensions)`; L64 `self.assertFalse(any((value in cache_dimensions for value in ('secret', 'private_key', 'signing_material'))))`; L75 `self.assertLess(calls.index('_legacy_cache_context'), calls.index('_get_access_token_cached'))`; L82 `self.assertIn('_check_token_issuance_access', context_calls)`; L83 `self.assertIn('get_expires_in', context_calls)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_login_template_uses_provider_owned_visibility_hook` L262–271; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L266 `self.assertIn('_oidc_can_show_continue', {node.name for node in provider_class.body if isinstance(node, ast.FunctionDef)})`; L270 `self.assertIn('request.env.user._oidc_can_show_continue()', template)`; L271 `self.assertNotIn('request.env.user.is_user_allow_create_token()', template)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197–223; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L199 `self.assertEqual(glue_manifest['depends'], ['amr_oidc', 'amr_resource'])`; L200 `self.assertFalse(glue_manifest.get('auto_install', False))`; L207 `self.assertTrue(MOVED.isdisjoint(provider_methods))`; L208 `self.assertNotIn('get_mobile_access_token', provider_methods)`; L209 `self.assertIn('get_user_by_username', provider_methods)`; L215 `self.assertTrue(MOVED <= glue_methods)`; L216 `self.assertIn('_get_access_token', glue_methods)`; L223 `self.assertTrue(MOVED <= resource_methods)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_resource_routes_use_resource_owned_url_passthrough` L250–260; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L255 `self.assertIn('_resource_access_url', {node.name for node in resource_class.body if isinstance(node, ast.FunctionDef)})`; L259 `self.assertNotIn('request.env.user.add_url_access_token', controller)`; L260 `self.assertIn('request.env.user._resource_access_url', controller)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_url_helpers_reject_bearer_creation` L225–248; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L242 `self.assertRaisesRegex(glue_module.UserError, 'URL access tokens are disabled')`; L244 `self.assertRaisesRegex(glue_module.UserError, 'URL access tokens are disabled')`; L246 `self.assertRaisesRegex(glue_module.UserError, 'URL access tokens are disabled')`; L248 `model.get_access_token.assert_not_called()`.
  - Mock/patch terdeteksi: L235 `mock.Mock(side_effect=AssertionError('URL issuance attempted'))`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc/tests/unit/test_standalone_package.py::StandalonePackageTests::test_provider_manifest_does_not_require_token_or_resource_addons` L39–46; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L45 `self.assertNotIn('amr_token', dependencies)`; L46 `self.assertNotIn('amr_resource', dependencies)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_access_token_omission_defaults_but_explicit_none_is_rejected` L13–36; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L23 `self.assertTrue(expected_audience)`; L27 `self.assertEqual(payload['aud'], expected_audience)`; L30 `self.assertRaisesRegex(ValueError, 'audience')`; L33 `self.assertRaisesRegex(ValueError, 'audience')`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_legacy_cache_reuses_within_ttl_bucket_and_rolls_over` L73–93; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L84 `self.assertEqual(repeated, first)`; L85 `self.assertEqual(signer.call_count, 1)`; L92 `self.assertNotEqual(rolled, first)`; L93 `self.assertEqual(signer.call_count, 2)`.
  - Mock/patch terdeteksi: L77 `mock.patch('jwt.encode', wraps=jwt.encode)`; L78 `mock.patch('odoo.addons.amr_oidc.models.token_helper.time.time', return_value=1800000000)`; L80 `mock.patch('odoo.addons.amr_oidc_resource.models.res_users.time.time', return_value=1800000000)`; L87 `mock.patch('odoo.addons.amr_oidc.models.token_helper.time.time', return_value=1800000060)`; L89 `mock.patch('odoo.addons.amr_oidc_resource.models.res_users.time.time', return_value=1800000060)`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_non_system_cross_user_denial_precedes_signing` L95–103; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L100 `self.assertRaises(AccessError)`; L103 `signer.assert_not_called()`.
  - Mock/patch terdeteksi: L99 `mock.patch('jwt.encode', wraps=jwt.encode)`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims` L36–52; selector identitas saja. parent init menyebut modul; root init menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L37 `self.assertIn('amr.oidc.helper', self.env.registry.models)`; L42 `self.assertEqual(own_claims['uid'], self.env.user.id)`; L43 `self.assertEqual(own_claims['sub'], self.env.user.login)`; L50 `self.assertEqual(claims['uid'], target.id)`; L51 `self.assertEqual(claims['sub'], target.login)`; L52 `self.assertNotEqual(claims['uid'], system_actor.id)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestOdoo13TestDiscoveryContract::test_integration_modules_are_registered_in_root_tests_package` L502–519; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L510 `self.assertEqual(len(integration_modules), len(registered_modules), 'each integration test module must be registered exactly once')`; L515 `self.assertCountEqual(integration_modules, registered_modules, 'tests/__init__.py must bind every integration test module by its test_* name')`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup` L407–442; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L415 `self.assertRaisesRegex(self.module.UserError, 'not allowed')`; L417 `self.assertEqual(helper._generate_user_token.call_count, 1)`; L419 `self.assertEqual(lookup_stats['lookups'], before)`; L424 `self.assertRaises(self.module.AccessError)`; L427 `self.assertEqual(lookup_stats['lookups'], before)`; L435 `self.assertRaises(ValueError)`; L439 `self.assertRaises(ValueError)`; L441 `lookup.assert_not_called()`; L442 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
  - Mock/patch terdeteksi: L434 `mock.patch.object(user, '_get_access_token', return_value='warm-token')`; L438 `mock.patch.object(user, '_get_access_token_cached', wraps=cached_method)`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_database_signing_key_material_change_cannot_cross_hit` L378–405; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L398 `self.assertEqual(first, repeated)`; L399 `self.assertEqual(helper._generate_user_token.call_count, 1)`; L404 `self.assertNotEqual(rotated, first)`; L405 `self.assertEqual(helper._generate_user_token.call_count, 2)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_legacy_issuance_reuses_only_within_full_scoped_cache_key` L332–376; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L342 `self.assertEqual(repeated, first)`; L343 `self.assertEqual(helper._generate_user_token.call_count, 1)`; L347 `self.assertEqual(default_repeated, default_first)`; L348 `self.assertEqual(helper._generate_user_token.call_count, 2)`; L351 `self.assertEqual(helper._generate_user_token.call_count, 3)`; L355 `self.assertEqual(helper._generate_user_token.call_count, 4)`; L359 `self.assertEqual(helper._generate_user_token.call_count, 5)`; L363 `self.assertEqual(helper._generate_user_token.call_count, 6)`; L366 `self.assertEqual(helper._generate_user_token.call_count, 7)`; L370 `self.assertEqual(helper._generate_user_token.call_count, 8)`; L373 `self.assertEqual(helper._generate_user_token.call_count, 9)`; L375 `self.fail('test ORM cache simulator was not installed')`; L376 `self.assertGreaterEqual(cache_stats['hits'], 2)`.
  - Mock/patch terdeteksi: L339 `mock.patch.object(self.module.time, 'time', return_value=1800000000)`; L353 `mock.patch.object(self.module.time, 'time', return_value=1800000060)`.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_signing_configuration_change_during_cache_fill_fails_closed` L444–456; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L454 `self.assertRaisesRegex(ValueError, 'Signing configuration changed during token issuance')`; L456 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut08_user_predicates_environment_and_stubs` L170–201; selector identitas saja. parent init menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L177 `self.assertTrue(machine.is_user_machine())`; L178 `self.assertTrue(machine.is_user_business())`; L179 `self.assertFalse(ordinary.is_user_machine())`; L180 `self.assertFalse(ordinary.is_user_business())`; L181 `self.assertTrue(technical.is_user_technical())`; L182 `self.assertFalse(technical.is_user_business())`; L183 `self.assertIs(self.helper.user_machine_sudo(self.env['res.users']), self.helper)`; L185 `self.assertEqual(elevated.env.uid, machine.id)`; L186 `self.assertFalse(elevated.env.su)`; L187 `self.assertEqual(self.helper.user_machine_sudo(ordinary).env.uid, ordinary.id)`; L188 `self.assertTrue(machine.is_user_allow_create_token())`; L190 `self.assertRaises(UserError)`; L193 `self.assertEqual(machine.add_url_access_token(url), url)`; L194 `self.assertEqual(machine.add_url_access_token(url, url_type='auto_login'), url)`; L195 `self.assertEqual(machine.get_auto_login_url(url), url)`; L199 `self.assertEqual(machine.decode(self.token), payload)`; L201 `self.assertIsNone(machine.decode(self.token))`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` L428–504; selector identitas saja. parent init menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L447 `self.assertTrue(self.helper._verified(result))`; L448 `self.assertTrue(self.helper.is_local_token(token))`; L452 `self.assertRaises(Unauthorized)`; L454 `self.assertRaises(Unauthorized)`; L456 `fetch.assert_not_called()`; L457 `self.assertEqual(result, dict(claims, kid=None, alg='RS256'))`; L459 `self.assertEqual(self.helper.validate(token), result)`; L460 `jwks.assert_not_called()`; L462 `self.assertRaises(Unauthorized)`; L468 `self.assertRaises(Unauthorized)`; L480 `self.assertEqual(remote_result, dict(claims, kid='synthetic-key', alg='RS256'))`; L481 `self.assertTrue(self.helper._verified(remote_result))`; L482 `fetch.assert_called_once_with(self.profile.jwks_uri)`; L483 `self.assertEqual(decode.call_args[0][0], remote_token)`; L484 `self.assertEqual(decode.call_args[1], {'algorithms': ['RS256'], 'issuer': self.profile.issuer, 'audience': ['resource-a'], 'leeway': 0, 'options': {'require': ['iss', 'aud', 'exp', 'iat', 'jti', 'sub', 'client_id']}})`; L491 `self.assertRaises(Unauthorized)`; L496 `self.assertRaises(Unauthorized)`; L498 `self.assertEqual(decode.call_count, 2)`; L503 `self.assertEqual(self.helper.validate(retained_token), retained)`; L504 `self.assertFalse(self.logger.called)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_no_default_mapping_or_ordinary_registry_access` L17–32; selector identitas saja. parent init menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L18 `self.assertFalse(self.registry.default_get(['resolver_mode']).get('resolver_mode'))`; L25 `self.assertRaises(AccessError)`; L27 `self.assertRaises(AccessError)`; L29 `self.assertRaises(AccessError)`; L31 `self.assertRaises(AccessError)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_native_loader_and_dependency_declarations` L111–139; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L114 `self.assertEqual(manifest['external_dependencies']['python'], ['jwt', 'cryptography'])`; L116 `self.assertIn('PyJWT==2.8.0', pins)`; L117 `self.assertIn('cryptography==39.0.2', pins)`; L129 `self.assertEqual(root_imports, {'integration'})`; L131 `self.assertEqual(integration_imports, {'test_helper', 'test_contracts', 'test_registry'})`; L132 `self.assertNotIn('test_security_unit', root_imports | integration_imports)`; L133 `self.assertTrue(all(((test_root / 'integration' / (module + '.py')).is_file() for module in integration_imports)))`; L138 `self.assertNotIn('amr_select_issuer', [n.targets[0].id for n in ast.walk(settings) if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)])`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_pinned_dependency_and_python_runtime` L99–109; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L103 `self.assertEqual(sys.version_info[:3], (3, 8, 20))`; L104 `self.assertEqual(jwt.__version__, '2.8.0')`; L105 `self.assertEqual(cryptography.__version__, '39.0.2')`; L108 `self.assertEqual(cffi.__version__, '1.15.1')`; L109 `self.assertEqual(pycparser.__version__, '2.21')`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314–329; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L327 `self.fetch.assert_called_once()`; L328 `self.env.parameters.get_param.assert_not_called()`; L329 `self.assertEqual(self.env.user_reads, [self.user.id])`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat04_27_unsupported_token_classes_zero_egress` L331–339; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L339 `self.fetch.assert_not_called()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302–312; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L305 `self.assertTrue(self.helper._verified(payload))`; L306 `self.assertIsInstance(payload, dict)`; L307 `self.assertEqual(self.helper.get_uid(payload), self.user.id)`; L308 `self.assertTrue(self.helper.is_user_match(self.user, payload))`; L309 `self.assertEqual(self.helper.get_user_token_login(token), self.user)`; L310 `self.assertEqual(self.helper.decode(token)['sub'], 'subject')`; L311 `self.assertEqual(self.helper.get_validate_user(token)['alg'], 'RS256')`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` L369–380; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L372 `self.assertEqual(self.fetch.call_count, 2)`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_local_key_no_loopback_or_local_bypass` L536–547; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L541 `self.assertTrue(self.helper.is_local_token(self.token()))`; L542 `self.assertTrue(self.helper._verified(self.helper.validate(self.token())))`; L544 `self.fetch.assert_not_called()`; L547 `self.fetch.assert_not_called()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_required_claims_and_zero_leeway` L341–350; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L350 `self.fetch.assert_not_called()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat17_audience_any_exact` L352–358; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L354 `self.assertTrue(self.helper._verified(self.helper.validate(self.token(dict(self.claims, aud=audience)))))`; L358 `self.fetch.assert_not_called()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat18_azp_optional_only_by_profile` L360–367; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L365 `self.assertTrue(self.helper._verified(self.helper.validate(self.token(claims))))`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat19_binding_exact_no_email_login_or_autobind` L586–595; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L590 `self.assertEqual(self.env.user_reads, [])`; L595 `self.assertEqual(self.env.user_reads, [])`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.
- `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_x5c_does_not_replace_selected_trusted_rsa_key` L382–389; selector identitas saja. parent init tidak menyebut modul; root init tidak menyebut modul; koleksi aktual NOT RUN.
  - Assertion terdeteksi: L384 `self.assertTrue(self.helper._verified(self.helper.validate(self.token(headers={'x5c': ['attacker-cert']}))))`; L388 `self.assertEqual(self.fetch.call_count, 2)`; L389 `self.env.parameters.get_param.assert_not_called()`.
  - Mock/patch terdeteksi: tidak terdeteksi otomatis — NOT ASSESSED.
  - Keterbatasan: ekstraksi AST hanya indeks statis; helper, fixture inherited, subTest, coverage varian dan kecocokan oracle belum dibuktikan; NOT ASSESSED.


## Koreksi terarah empat review V/U

Koreksi pada baris evidence dan child overlay di bawah **mengungguli interpretasi historis yang bertentangan**; kutipan oracle accepted tetap dipertahankan, bukan requirement baru. Label slice tidak menyatakan full-case PASS. Semua child mekanis tetap NOT ASSESSED kecuali bukti yang dibatasi secara eksplisit; tidak ada eksekusi baru. Varian dan requirement yang belum diperiksa individual tetap NOT ASSESSED.

## Rekonsiliasi Gen5 — 32 kasus accepted
Sumber oracle: `docs/ADDONS13-79/UAT.md`, SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; prasyarat L7–13. Byte UAT diverifikasi. Mapping di bawah diperiksa langsung dari `git show 49b5a739ce25b8feeb74b8d7c91641e2c98c5978:<path>`; nomor baris merujuk commit itu, bukan HEAD. Gen5 menggunakan kandidat `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`; HEAD teramati `5f1f0f9433f723f850df8640fdc1db261476df91`. **Tidak ada rebind atau persetujuan baru.**
Gen5 `safe-summary.json` dan controller/log di `/home/ubuntu/.hermes/profiles/lead/cache/scratch/addons13-79-gen5-preflight/` adalah bukti sementara, bukan arsip permanen; raw log terbatas, jangan salin secrets/bearer. Tiga selector `amr_resource`, `amr_oidc_resource`, `amr_oidc` masing-masing exit 0, started/unique 28/28, 18/18, 44/44 (total 90 test ID unik per selector); tidak ada test failure line pada summary. Ini bukan bukti seluruh oracle atau full-case PASS. Controller mencatat Python 3.7.3, snapshot cocok pascarun, katalog DB sebelum/sesudah 0 dan resource test/network/DB terhapus. Log memuat SQL ERROR masing-masing **3/0/6**, sehingga exit 0 bukan bukti log bersih; jangan menghapus atau menafsirkan semuanya sebagai kegagalan test tanpa investigasi. `--proxy-mode` pada provider mensimulasikan konteks proxy, bukan TLS end-to-end. Isolasi jaringan bukan monitoring seluruh egress/socket; bukan bukti U12.
**Pembacaan:** “Dijalankan” hanya slice metode integrasi yang tercantum dalam summary Gen5; outcome slice disandarkan pada selector exit 0 + started ID + summary tanpa test failure line, bukan hasil oracle lengkap. “Statis unit” berarti source test diverifikasi di commit, **tidak dibuktikan dijalankan pada Gen5**. Assertion baris merupakan cuplikan terpilih; fixture/helper dan varian lain tidak otomatis terjamin. Tidak ada kasus dinyatakan PASS. V06 helper/no-token-regardless-of-MRO BLOCKED sampai kontrak disetujui; security review redirect/model tetap terpisah. V10 default tanpa bearer URL tetap berlaku, denial detail menunggu persetujuan; pengecualian tidak diasumsikan. SCOPE-01, lifecycle, security dan final config tetap gate.
### Gen5 V01 — UAT.md L249

**Varian/oracle:** Fresh provider-only: five provider declarations absent from provider; no glue selected; independent provider `_generate_user_token`→`decode` succeeds for explicitly configured synthetic fixture and malformed/missing configuration fails. Verify provider declaration of `get_access_token` is glue-only; record effective public method status and legacy impact without assuming core/third-party absence or a particular exception.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` L23–37: L30 `self.assertEqual(decoded["sub"], self.env.user.login)`; L31 `self.assertEqual(decoded["uid"], self.env.user.id)`; L32 `self.assertEqual(claims["uid"], self.env.user.id)`. ID started; selector exit 0.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** five declarations/effective public method and legacy impact; malformed config matrix. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V02 — UAT.md L255

**Varian/oracle:** RS-only: all five existing RS declarations retained, actual signatures and policy verified, direct issuance fails, URL wrappers pass through. Exercise separately configured synthetic RS verifier positive/negative, no provider/glue in closure.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut08_user_predicates_environment_and_stubs` L170–201: L189–191 direct issuance methods raise `UserError`; L193–195 both `add_url_access_token` types and `get_auto_login_url` return input URL. ID started; selector exit 0.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` L430–509: L450 `self.assertTrue(self.helper._verified(result))`; L451 `self.assertTrue(self.helper.is_local_token(token))`; L455 `with self.assertRaises(Unauthorized):`. ID started; selector exit 0.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** five signatures/policy; independent closure and full RS verifier matrix. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V03 — UAT.md L261

**Varian/oracle:** Both bases no glue in both fresh install orders: provider independent helper operation; RS independent positive and unknown issuer negative; compare registry/MRO, signatures, actual method dispatch and default nonsecret trust snapshots, no glue, issuer, fallback/discovery or trust introduced. Lead and sibling owners review whether this fixture establishes the applicable accepted sibling oracle; do not demand an unaccepted public-method fixture or assert sibling pass here.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` L23–37: L30 `self.assertEqual(decoded["sub"], self.env.user.login)`; L31 `self.assertEqual(decoded["uid"], self.env.user.id)`; L32 `self.assertEqual(claims["uid"], self.env.user.id)`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` L430–509: L450 `self.assertTrue(self.helper._verified(result))`; L451 `self.assertTrue(self.helper.is_local_token(token))`; L455 `with self.assertRaises(Unauthorized):`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_standalone_package.py::StandalonePackageTests::test_provider_manifest_does_not_require_token_or_resource_addons` L39–46: L45 `self.assertNotIn("amr_token", dependencies)`; L46 `self.assertNotIn("amr_resource", dependencies)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314–329: L327 `self.fetch.assert_called_once()`; L328 `self.env.parameters.get_param.assert_not_called()`.
**Gap / belum terbukti:** both orders, actual MRO/dispatch, trust snapshots and sibling-owner review. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V04 — UAT.md L267

**Varian/oracle:** Glue explicitly installed in both orders, `auto_install=False`, no cyclic/base-to-glue dependency; verify moved five plus private helper/sentinel owner, retained RS source declarations and actual effective MRO, no implicit trust and no accidental activation. Dependency failure tested only using authorized isolated fixture.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197–223: L199 `self.assertEqual(glue_manifest["depends"], ["amr_oidc", "amr_resource"])`; L200 `self.assertFalse(glue_manifest.get("auto_install", False))`.
**Gap / belum terbukti:** both orders, effective MRO, sentinel ownership, accidental activation and authorized dependency-failure fixture. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V05 — UAT.md L273

**Varian/oracle:** Login template on provider-only, RS+provider in both no-glue orders, glue: proposed provider-specific UI hook has baseline `True`, without `super`, context flags or registry sniffing; true/false override shows/hides Continue; public and authenticated user rendering stays controlled; no call to moved policy, glue, signer or token; verify no issuance. Exercise direct authorize/continue and submit routes: remain unsupported. Document old override/custom addon impact.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_login_template_uses_provider_owned_visibility_hook` L262–271: L266 `self.assertIn("_oidc_can_show_continue", {`; L270 `self.assertIn("request.env.user._oidc_can_show_continue()", template)`.
**Gap / belum terbukti:** actual public/authenticated rendering, true/false override, direct routes and no-issuance observer. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V06 — UAT.md L279

**Varian/oracle:** Both RS GET routes in RS-only, both no-glue orders and glue, supported `auto_login`/`access_token`, URL branch, malformed type, absent URL, internal/public model paths, model `get_url_access_token` direct-result branch and auth failures; compare actual status/shape/Location/headers with approved contract. The proposed RS-owned route helper/pass-through and its no-token-regardless-of-MRO oracle require contract review/approval; pending that decision, the helper-specific assertion is BLOCKED, actual NOT RUN. If approved, instrument helper/signer to verify the proposed oracle without assuming model branch safety. Obtain independent security review of generic redirect/open-redirect and model-generated URL risks, not a blanket safety claim.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut09_direct_controller_contract` L269–335: L283 `self.assertEqual(response.status_code, 200)`; L284 `self.assertEqual(json.loads(response.get_data(as_text=True)),`; L286 `self.assertEqual(controller.access_url(url=url, type='unsupported').status_code, 400)`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_resource_routes_use_resource_owned_url_passthrough` L250–260: L255 `self.assertIn("_resource_access_url", {`; L259 `self.assertNotIn("request.env.user.add_url_access_token", controller)`.
**Gap / belum terbukti:** both routes and compositions, URL/type/model/auth/status/Location/header variants and independent redirect review. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V07 — UAT.md L285

**Varian/oracle:** Glue direct access: self vs ordinary different actor vs system, singleton/empty/multiple, policy false, inactive/unauthorized where contract says; denied before cache and signing, even warm hit, across RPC/machine/public/portal and forged context. Test persistent `create_access_token` explicit controlled denial with no storage/signature.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims` L36–52: L42 `self.assertEqual(own_claims["uid"], self.env.user.id)`; L43 `self.assertEqual(own_claims["sub"], self.env.user.login)`; L50 `self.assertEqual(claims["uid"], target.id)`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_non_system_cross_user_denial_precedes_signing` L95–103: L100 `with self.assertRaises(AccessError):`; L103 `signer.assert_not_called()`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_persistent_access_token_storage_remains_unsupported` L129–137: L131 `with self.assertRaises(UserError) as raised:`; L133 `self.assertEqual(raised.exception.args[0],`; L135 `self.assertEqual(raised.exception.args[1:], ("",))`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup` L407–442: L415 `with self.assertRaisesRegex(self.module.UserError, "not allowed"):`; L417 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
**Gap / belum terbukti:** empty/multiple, policy/inactive, warm-cache denial, RPC/public/portal/machine and forged context. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V08 — UAT.md L291

**Varian/oracle:** Glue omission sentinel survives defaults/wrappers/cache/private boundary; omitted argument causes helper call with no audience argument, explicit None rejects; empty/malformed vs valid string/list, list tuple roundtrip, resource precedence and invalid resource rejection. No sentinel identity substitution from token_helper.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_access_token_omission_defaults_but_explicit_none_is_rejected` L13–36: L23 `self.assertTrue(expected_audience)`; L27 `self.assertEqual(payload["aud"], expected_audience)`; L30 `with self.assertRaisesRegex(ValueError, "audience"):`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_user_resource_overrides_conflicting_audience_shapes` L45–55: L54 `self.assertEqual(payload["aud"], resource)`; L55 `self.assertNotIn("resource", payload)`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_user_invalid_resource_types_rejected_without_audience_fallback` L57–64: L61 `with self.assertRaisesRegex(ValueError, "resource"):`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_audience_list_is_supported_and_invalid_list_does_not_default` L54–71: L63 `self.assertEqual(signer.call_count, 2)`; L64 `with self.assertRaisesRegex(ValueError, "A valid audience is required"):`; L66 `self.assertEqual(signer.call_count, 2)`. ID started; selector exit 0.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** sentinel identity/private boundary, empty and malformed shapes, wrapper/cache tuple roundtrip. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V09 — UAT.md L297

**Varian/oracle:** Cache: same/different uid and normalized audiences, bucket rollover, actual expiry, policy/key/user/company/revision changes and explicit invalidation including concurrent changes, DB isolation; a stale/unauthorized hit never mints/returns a usable token. Expectations need approved lifecycle; verify no cross-context leakage.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_legacy_cache_reuses_within_ttl_bucket_and_rolls_over` L73–93: L84 `self.assertEqual(repeated, first)`; L85 `self.assertEqual(signer.call_count, 1)`; L92 `self.assertNotEqual(rolled, first)`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_key_removal_after_warm_issuance_rejects` L105–110: L109 `with self.assertRaisesRegex(ValueError, "JWT Secret not set"):`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_configuration_change_uses_new_key_and_ttl` L112–127: L123 `self.assertEqual(claims["exp"], fixed_time + 120)`; L124 `self.assertEqual(claims["aud"], "key-rotation-audience")`; L125 `with self.assertRaises(jwt.InvalidSignatureError):`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_legacy_issuance_reuses_only_within_full_scoped_cache_key` L332–376: L342 `self.assertEqual(repeated, first)`; L343 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup` L407–442: L415 `with self.assertRaisesRegex(self.module.UserError, "not allowed"):`; L417 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_database_signing_key_material_change_cannot_cross_hit` L378–405: L398 `self.assertEqual(first, repeated)`; L399 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_signing_configuration_change_during_cache_fill_fails_closed` L444–456: L454 `with self.assertRaisesRegex(ValueError, "Signing configuration changed during token issuance"):`; L456 `self.assertEqual(helper._generate_user_token.call_count, 1)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_legacy_cache_key_is_scoped_and_guarded_by_live_validation` L34–83: L43 `self.assertEqual(len(cache_decorators), 1)`; L60 `self.assertTrue({`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_pinned_dependency_and_python_runtime` L99–109: L103 `self.assertEqual(sys.version_info[:3], (3, 8, 20))`; L104 `self.assertEqual(jwt.__version__, '2.8.0')`.
**Gap / belum terbukti:** key removal assertion hanya ValueError, bukan signer/stale hit; expiry, policy/user/company/revision invalidation, concurrency termasuk explicit invalidation and real DB isolation; approved lifecycle. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V10 — UAT.md L303

**Varian/oracle:** Glue direct URL helpers and RPC: default must issue no bearer into URLs; proposed controlled denial with no signer/cache use and sanitized failure for all types, including auto-login and explicit audience/resource, is pending exact contract approval. If Owner separately approves an exception, specify reviewed origin/redirect, audience, caller, expiry/replay and leak-control cases; do not infer approval. No bearer in evidence.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_add_url_access_token_rejects_url_bearer_by_default` L74–77: L76 `with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_add_url_auto_login_rejects_explicit_audience_without_signing` L96–102: L97 `with self.assertRaisesRegex(UserError, "URL access tokens are disabled"):`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_url_helpers_reject_bearer_creation` L225–248: L242 `with self.assertRaisesRegex(glue_module.UserError, "URL access tokens are disabled"):`; L244 `with self.assertRaisesRegex(glue_module.UserError, "URL access tokens are disabled"):`.
**Gap / belum terbukti:** all URL helper types and RPC, signer/cache observation and sanitized failure contract approval. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V11 — UAT.md L309

**Varian/oracle:** Delete mobile method in controlled first-party closure provider-only, RS-only, both orders, glue, legacy adapter: first-party declaration removal and no alias/shim; record effective registry resolution and direct/RPC result without assuming absence in Odoo core or third-party addons or any particular exception. Audit external/dynamic consumers separately.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197–223: L199 `self.assertEqual(glue_manifest["depends"], ["amr_oidc", "amr_resource"])`; L200 `self.assertFalse(glue_manifest.get("auto_install", False))`.
**Gap / belum terbukti:** all first-party closures, alias/shim, effective registry/direct/RPC and external dynamic consumers. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V12 — UAT.md L315

**Varian/oracle:** Move relevant registered provider integration tests and source-loaded standalone/security fixtures to correct glue target; preserve all applicable actor, audience, cache, rejection and security assertions; independently run remaining provider issuer tests and reconcile applicable `amr_token` legacy loader/alias coverage. No silently dropped cases.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestOdoo13TestDiscoveryContract::test_integration_modules_are_registered_in_root_tests_package` L502–519: L510 `self.assertEqual(`; L515 `self.assertCountEqual(`.
**Gap / belum terbukti:** pemetaan fixture relevan source→target dan preservation assertion tidak dibuktikan daftar modul target; historical assertion inventory and amr_token loader/alias reconciliation; no silent drops. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V13 — UAT.md L321

**Varian/oracle:** Explicit local trusted binding off by default; wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user all reject. Approved valid provider access token passes same RS verifier. No ID token or generic JWT; no weakening, implicit trust or fallback.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_missing_selected_local_key_no_fallback` L185–228: L216 `self.assertEqual(self.helper.validate(token)['iss'], self.profile.issuer)`; L217 `fetch_json.assert_not_called()`; L224 `with self.assertRaises(Unauthorized) as error:`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_issuer_rejected_before_transport` L297–309: L300 `self._assert_uat04_jwks_positive_control(`; L304 `with self.assertRaises(Unauthorized) as error:`; L306 `self.assertEqual(error.exception.code, 401)`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_invalid_signature_rejected_without_fallback` L339–350: L342 `self._assert_uat04_jwks_positive_control(`; L345 `with self.assertRaises(Unauthorized) as error:`; L347 `self.assertEqual(error.exception.code, 401)`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302–312: L305 `self.assertTrue(self.helper._verified(payload))`; L306 `self.assertIsInstance(payload, dict)`.
**Gap / belum terbukti:** negative issuer/signature di atas adalah remote mocked JWKS, bukan trusted-local provider→RS; approved actual provider-to-RS binding positive and full DB/provider/key/class/claim/company/user negative matrix. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V14 — UAT.md L327

**Varian/oracle:** Exercise actual merged-registry classification/backend path with no classification mock; backend selected once with bounded call count; verify the bounded internal interface receives explicit identity/arguments and does not consume bearer or Basic from ambient request, including when ambient headers differ; local errors fail closed, zero introspection/self-provider HTTP including key/metadata/failure; calibrated transport instrumentation. Remote branch independently retains approved security and transport.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_missing_selected_local_key_no_fallback` L185–228: L216 `self.assertEqual(self.helper.validate(token)['iss'], self.profile.issuer)`; L217 `fetch_json.assert_not_called()`; L224 `with self.assertRaises(Unauthorized) as error:`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_local_key_no_loopback_or_local_bypass` L536–547: L541 `self.assertTrue(self.helper.is_local_token(self.token()))`; L542 `self.assertTrue(self.helper._verified(self.helper.validate(self.token())))`.
**Gap / belum terbukti:** L216–217 positive sebelum removal; L224 Unauthorized sesudah removal; fetch_json mock bukan observasi seluruh jaringan. Merged-registry classification, explicit-vs-ambient credentials, bounded backend and calibrated HTTP/socket egress, remote branch. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V15 — UAT.md L333

**Varian/oracle:** Pada Odoo 13 dan CPython 3.7.3 yang disetujui, dengan dependency terkwalifikasi dan database fresh terisolasi yang diotorisasi, periksa import, route, ACL, registry, urutan addon dan seluruh hasil test yang berlaku. Catat runtime aktual dan cleanup/readback; jangan mengekstrapolasi ke upgrade atau addon pihak ketiga.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_native_loader_and_dependency_declarations` L111–143: L114 `self.assertEqual(manifest['external_dependencies']['python'], ['jwt', 'cryptography'])`; L116 `self.assertIn('PyJWT==2.8.0', pins)`.
**Gap / belum terbukti:** full approved dependency qualification, order/ACL/registry/route matrix, unit suites and runtime readback. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 V16 — UAT.md L339

**Varian/oracle:** Review release and cross-issue impact: explicitly list five public API compatibility changes, deletion and external unknowns; preserve applicable sibling requirements and clarify that the proposed fixture is not accepted. Owner decisions, security risk and hash approval separately recorded; no waiver inferred.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** five API compatibility changes, deletion/external impacts, sibling requirements and owner/security/hash decisions. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U01 — UAT.md L345

**Varian/oracle:** Fresh provider only and RS only: each starts, imports and works in its own existing bounded capability without the other/integration; no implicit trust. Verify actual installed closures.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` L23–37: L30 `self.assertEqual(decoded["sub"], self.env.user.login)`; L31 `self.assertEqual(decoded["uid"], self.env.user.id)`; L32 `self.assertEqual(claims["uid"], self.env.user.id)`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat03_manual_config_and_jwks_boundary` L127–183: L135 `self.assertFalse(module_states, 'provider/token addon state must be absent')`; L152 `self.assertEqual(int.from_bytes(base64.urlsafe_b64decode(`; L155 `self.assertEqual(int.from_bytes(base64.urlsafe_b64decode(`. ID started; selector exit 0.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** complete installed closures/no implicit trust and bounded capability of each. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U02 — UAT.md L351

**Varian/oracle:** Fresh both install orders without integration: both load; no new trusted profile/key or local acceptance. Record closure, effective registry/method ownership, ACL and configuration.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197–223: L199 `self.assertEqual(glue_manifest["depends"], ["amr_oidc", "amr_resource"])`; L200 `self.assertFalse(glue_manifest.get("auto_install", False))`.
**Gap / belum terbukti:** both install orders, no trust/local acceptance, effective ownership, ACL and config. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U03 — UAT.md L357

**Varian/oracle:** With chosen integration installed but disabled: baseline unaffected, no new trust; remove/disable backend while enabled => fail closed, no silent HTTP/introspection. Include provider-only, RS-only and optional amr_token legacy adapter if supported.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileControllerTests::test_disabled_fresh_profile_preserves_unsupported_grant_contract` L157–170: L163 `self.assertEqual(response.status_code, 400)`; L164 `self.assertEqual(response.headers.get("Cache-Control"), "no-store")`.
**Gap / belum terbukti:** disabled integration vs disabled backend, fail closed/no fallback and optional legacy adapter. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U04 — UAT.md L363

**Varian/oracle:** Positive: approved local issuer uses real selected issuance path with approved authenticated user/client and real synthetic RS256 key. Confirm actual header and required claims, valid exact RS policy, resolver/binding, eligible user; verify RS returns accepted verified provenance and correct user. Not a handcrafted token standing in for issuer.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signing_produces_verifiable_rs256_at_jwt` L550–582: L581 `self.assertEqual(header, {"alg": "RS256", "kid": "synthetic-rs-kid", "typ": "at+jwt"})`; L582 `self.assertEqual(decoded, claims)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302–312: L305 `self.assertTrue(self.helper._verified(payload))`; L306 `self.assertIsInstance(payload, dict)`.
**Gap / belum terbukti:** authenticated selected issuance through actual RS verifier, policy/binding/user/provenance. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U05 — UAT.md L369

**Varian/oracle:** Signature tamper, different key, wrong kty, RSA <2048, none/HS256/other alg, invalid key, malformed/oversize token, forbidden jku/x5u/jwk/crit, wrong/missing typ, ID-token confusion => reject, no user/session.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_invalid_signature_rejected_without_fallback` L339–350: L342 `self._assert_uat04_jwks_positive_control(`; L345 `with self.assertRaises(Unauthorized) as error:`; L347 `self.assertEqual(error.exception.code, 401)`. ID started; selector exit 0.
- `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT08::test_malformed_serialized_token_rejected` L239–244: L243 `with self.assertRaises(jwt.DecodeError):`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` L302–312: L305 `self.assertTrue(self.helper._verified(payload))`; L306 `self.assertIsInstance(payload, dict)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat04_27_unsupported_token_classes_zero_egress` L331–339: L339 `self.fetch.assert_not_called()`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_x5c_does_not_replace_selected_trusted_rsa_key` L382–389: L384 `self.assertTrue(self.helper._verified(self.helper.validate(`; L388 `self.assertEqual(self.fetch.call_count, 2)`.
**Gap / belum terbukti:** tamper, kty, short RSA, algorithm matrix, oversize, forbidden headers, typ/ID confusion, no user dan no session untuk setiap negative. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U06 — UAT.md L375

**Varian/oracle:** Exact issuer wrong/untrusted/inactive/ambiguous or wrong DB/provider binding; absent/revoked/mismatched/duplicate kid and missing/ambiguous backend; caller-injected key reference => reject, never fallback. Apply selected local kid contract explicitly.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_issuer_rejected_before_transport` L297–309: L300 `self._assert_uat04_jwks_positive_control(`; L304 `with self.assertRaises(Unauthorized) as error:`; L306 `self.assertEqual(error.exception.code, 401)`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_kid_rejected_without_fallback` L325–337: L328 `self._assert_uat04_jwks_positive_control(`; L332 `with self.assertRaises(Unauthorized) as error:`; L334 `self.assertEqual(error.exception.code, 401)`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_registry_unique_issuer_including_archived` L9–15: L14 `with self.assertRaises((ValidationError, IntegrityError)), self.cr.savepoint():`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` L369–380: L372 `self.assertEqual(self.fetch.call_count, 2)`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314–329: L327 `self.fetch.assert_called_once()`; L328 `self.env.parameters.get_param.assert_not_called()`.
**Gap / belum terbukti:** wrong DB/provider binding, revoked/duplicate/ambiguous kid/backend, injected key and no fallback. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U07 — UAT.md L381

**Varian/oracle:** Missing/wrong/malformed iss, aud (empty, mixed invalid, nonmatching), exp, iat, jti, sub, client_id; future iat/nbf, expired or exact boundary; optional nbf absent accepted only per agreed policy; strict claim typing and issuer/aud/client/azp independence. Each negative rejects.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT08::test_required_issuer_audience_and_time_claims_reject_invalid_tokens` L201–237: L221 `with self.assertRaises(error_type):`; L236 `with self.assertRaises(jwt.MissingRequiredClaimError):`. ID started; selector exit 0. Ini hanya provider helper `_decode`: wrong iss/aud, expired exp, future nbf, exp None, dan omitted iss/aud/exp; bukan selected RS verifier, routing, user atau session.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_required_claims_and_zero_leeway` L341–350: L350 `self.fetch.assert_not_called()`.
**Gap / belum terbukti:** all required claim/type/time boundary/optional nbf and azp variants in selected RS path. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U08 — UAT.md L387

**Varian/oracle:** Matching single/list audience, configured allowlist with one matching value, correct client_id, allowed azp present or explicitly allowed absent; mismatch, malformed, absent when required => reject. Never equate aud, client_id and azp.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_audience_rejected_before_jwks` L311–323: L314 `self._assert_uat04_jwks_positive_control(`; L318 `with self.assertRaises(Unauthorized) as error:`; L320 `self.assertEqual(error.exception.code, 401)`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat17_audience_any_exact` L352–358: L354 `self.assertTrue(self.helper._verified(self.helper.validate(self.token(dict(self.claims, aud=audience)))))`; L358 `self.fetch.assert_not_called()`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat18_azp_optional_only_by_profile` L360–367: L365 `self.assertTrue(self.helper._verified(self.helper.validate(self.token(claims))))`.
**Gap / belum terbukti:** matching single/list, allowlist and independent client_id/azp present/absent/malformed. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U09 — UAT.md L393

**Varian/oracle:** Unknown/ambiguous/disabled user, invalid binding, duplicate mapping, wrong company, portal/public/share/superuser, inactive and policy revision changed mid-validation => deny; fabricated or modified verified dict and wrong request context denied.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut07_matching` L511–547: L524 `self.assertEqual(self.helper.get_user_match(claims), self.admin)`; L525 `self.assertEqual(self.helper.get_uid(claims), self.admin.id)`; L526 `self.assertTrue(self.helper.is_user_match(self.admin, claims))`. ID started; selector exit 0.
- `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_binding_and_audience_uniqueness` L34–43: L40 `with self.assertRaises((ValidationError, IntegrityError)), self.cr.savepoint():`; L42 `with self.assertRaises(ValidationError), self.cr.savepoint():`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat19_binding_exact_no_email_login_or_autobind` L586–595: L590 `self.assertEqual(self.env.user_reads, [])`; L595 `self.assertEqual(self.env.user_reads, [])`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat01_16_unknown_inactive_duplicate_company_zero_egress` L314–329: L327 `self.fetch.assert_called_once()`; L328 `self.env.parameters.get_param.assert_not_called()`.
**Gap / belum terbukti:** unknown/disabled/ambiguous users, company/role, mid-validation revision and forged verified context. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U10 — UAT.md L399

**Varian/oracle:** Rotation: provision new key through selected trust-admin path; explicitly retain old key for approved window, validate both while allowed, switch signer, revoke/remove old then reject old and unknown kid; duplicates and stale cache fail closed; no private-key exposure. Validate expiry policy/backup/rollback per decided contract.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_oidc/tests/integration/test_public_key_orm.py::TestPublicKeyORM::test_rsa_ec_jwks_active_signing_and_public_only` L128–157: L145 `self.assertEqual(len(jwks), len(expected))`; L146 `self.assertEqual({jwk["kid"] for jwk in jwks}, set(expected))`; L149 `self.assertEqual(jwk["alg"], algorithm)`. ID started; selector exit 0.
- `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_configuration_change_uses_new_key_and_ttl` L112–127: L123 `self.assertEqual(claims["exp"], fixed_time + 120)`; L124 `self.assertEqual(claims["aud"], "key-rotation-audience")`; L125 `with self.assertRaises(jwt.InvalidSignatureError):`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` L369–380: L372 `self.assertEqual(self.fetch.call_count, 2)`.
**Gap / belum terbukti:** trust-admin rotation with overlap/revocation, stale caches, private exposure, expiry/backup/rollback. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U11 — UAT.md L405

**Varian/oracle:** Failure isolation: no profile/provider, malformed key, policy mutation, ambiguous issuer, backend exception and disabled integration deny; existing remote configured profile still uses its established path and validation; no recursion in real merged registry/MRO and bounded backend call count.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_missing_selected_local_key_no_fallback` L185–228: L216 `self.assertEqual(self.helper.validate(token)['iss'], self.profile.issuer)`; L217 `fetch_json.assert_not_called()`; L224 `with self.assertRaises(Unauthorized) as error:`. ID started; selector exit 0.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** backend exception/policy mutation/disabled integration, real merged MRO recursion and remote branch. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U12 — UAT.md L411

**Varian/oracle:** Network oracle: instrument outbound HTTP client/transport plus process/socket egress for the entire selected validation call, including classification, discovery, JWKS/key and exception paths. Positive + negatives and unavailable provider: zero introspection AND zero outbound self-provider requests; retain captures/counters and prove observer with a controlled known request in separately authorized setup. Scope does not forbid unrelated traffic or remote validation; distinguish normal frontchannel and test harness.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_missing_selected_local_key_no_fallback` L185–228: L216 `self.assertEqual(self.helper.validate(token)['iss'], self.profile.issuer)`; L217 `fetch_json.assert_not_called()`; L224 `with self.assertRaises(Unauthorized) as error:`. ID started; selector exit 0.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_local_key_no_loopback_or_local_bypass` L536–547: L541 `self.assertTrue(self.helper.is_local_token(self.token()))`; L542 `self.assertTrue(self.helper._verified(self.helper.validate(self.token())))`.
**Gap / belum terbukti:** entire validation instrumentation incl process/socket, positive/negative/unavailable, calibrated known request. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U13 — UAT.md L417

**Varian/oracle:** Security/operations: only trust-admin can change binding/key/algorithm; ordinary users cannot spoof profile or fetch private material; sanitize logs/response, no bearer/key/secret leakage; policy revisions invalidate stale provenance.
**Dijalankan — slice relevan, bukan seluruh kasus:**
- `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_no_default_mapping_or_ordinary_registry_access` L17–32: L18 `self.assertFalse(self.registry.default_get(['resolver_mode']).get('resolver_mode'))`; L25 `with self.assertRaises(AccessError):`; L27 `with self.assertRaises(AccessError):`. ID started; selector exit 0.
- `amr_oidc/tests/integration/test_client_secret_verifier.py::TestClientSecretVerifier::test_ordinary_user_can_read_client_but_not_verifier` L51–59: L57 `self.assertEqual(client.read(["client_id"])[0]["client_id"], "secret-verifier-client")`; L58 `with self.assertRaises(AccessError):`. ID started; selector exit 0.
- `amr_oidc/tests/integration/test_public_key_orm.py::TestPublicKeyORM::test_rsa_ec_jwks_active_signing_and_public_only` L128–157: L145 `self.assertEqual(len(jwks), len(expected))`; L146 `self.assertEqual({jwk["kid"] for jwk in jwks}, set(expected))`; L149 `self.assertEqual(jwk["alg"], algorithm)`. ID started; selector exit 0.
**Statis unit:** NOT ASSESSED; tidak ada mapping unit yang diperiksa untuk kasus ini.
**Gap / belum terbukti:** trust-admin write matrix, spoof/private access, response/log sanitization and revision invalidation. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U14 — UAT.md L423

**Varian/oracle:** Install graph and contracts: no hard reverse dependency/import; verify selected optional composition, native registry, existing helper API/return types, disabled failure and legacy consumers without implicit trust. If upgrade/rollback becomes in scope, obtain separate requirements, authorization and evidence; no claim now.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` L197–223: L199 `self.assertEqual(glue_manifest["depends"], ["amr_oidc", "amr_resource"])`; L200 `self.assertFalse(glue_manifest.get("auto_install", False))`.
**Gap / belum terbukti:** reverse imports, installed optional composition/registry/API return types, disabled failure and legacy consumers. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U15 — UAT.md L429

**Varian/oracle:** Issuance security: unauthorized caller cannot set arbitrary sub/client_id/iss/alg; valid issuance generates fresh jti, approved iat/exp and typ, client identity derives from authenticated context; generic JWT, forged claim and replay-policy expectations per decision.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` L363–438: L396 `with self.assertRaises(ValueError):`; L398 `mapping._get_or_create_subject.assert_not_called()`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signer_requires_bound_provenance_single_rs256_key_and_at_jwt` L514–548: L529 `with self.assertRaises(self.support.AccessError):`; L533 `self.assertEqual(self.helper._sign_fresh_profile_token(claims, provenance), "signed")`.
**Gap / belum terbukti:** authenticated caller claim control, fresh jti, approved lifetime/typ, replay and forged claims. Full-case NOT ASSESSED; tidak ada klaim PASS.
### Gen5 U16 — UAT.md L435

**Varian/oracle:** Pada kandidat tepat dan Odoo 13 / CPython 3.7.3 yang disetujui, verifikasi dependency closure serta instalasi/import, jalankan unit dan native integration suites yang berlaku, periksa API cryptography/PyJWT dan nama manifest; rekam command, jumlah, hasil, runtime dan dependency aktual. Jangan mengasumsikan kompatibilitas dari pin atau interpreter lain.
**Dijalankan — slice relevan:** NOT ASSESSED; tidak dipetakan ke metode Gen5 yang diverifikasi di sini. Hasil selector umum bukan bukti oracle kasus.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_oidc/tests/unit/test_package_contract.py::PackageContract::test_candidate_manifest_identity_and_dependencies` L93–102: L95 `self.assertEqual(manifest["version"], "13.0.1.0.0")`; L96 `self.assertEqual(manifest["license"], "LGPL-3")`.
**Statis unit** (tidak dibuktikan dieksekusi): `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_pinned_dependency_and_python_runtime` L99–109: L103 `self.assertEqual(sys.version_info[:3], (3, 8, 20))`; L104 `self.assertEqual(jwt.__version__, '2.8.0')`.
**Gap / belum terbukti:** all applicable unit/native suites, actual full dependency closure, cryptography/PyJWT API and manifest names. Full-case NOT ASSESSED; tidak ada klaim PASS.

**Rekonsiliasi jumlah:** 32/32 kasus memiliki entri Gen5 (16 V + 16 U); 0 full-case PASS. Ini bukan hitungan sub-oracle yang lulus. Assertion unit sebelumnya yang tidak dapat diverifikasi terhadap commit ini tetap historis/NOT ASSESSED.


## Gen5 — status per klausa stabil (rekonsiliasi tambahan)

Indeks ini tidak mengubah riwayat di atas. Source oracle accepted pada commit `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`; lokasi L pada tabel menunjuk assertion UAT untuk kasus itu, dengan teks setiap klausa dan ID stabil persis pada inventaris historis di atas. Test dan lokasi assertion berikut adalah pada commit yang sama. **EXECUTED PARTIAL** hanya untuk irisan yang disebut, bila class/method tercatat started dan selector exit 0 di `safe-summary.json`; bukan bukti bahwa seluruh assertion dieksekusi atau seluruh klausa terpenuhi. **STATIC UNIT** adalah test source saja, bukan klaim dijalankan. **NOT ASSESSED** berarti belum ada mapping yang dibuktikan, bukan test tidak ada. Bukti tiap selector adalah `safe-summary.json` serta controller dan runner yang dirujuk di situ; runner mentah terbatas, tidak disalin. Jumlah/exit bukan bukti semantic coverage.

Variasi yang terkelompok dalam satu klausa **tidak diekspansi otomatis**: selain irisan assertion yang dirujuk eksplisit, setiap varian lain NOT ASSESSED. Gap Gen5 per kasus di atas tetap berlaku; tidak ada full UAT PASS. SCOPE-01 tetap OPEN. Keputusan, pengecualian dan kondisi approval tidak dinyatakan terjadi hanya karena dirujuk.

| Atom | Sumber assertion accepted | Status | Assertion/test yang dapat ditelusuri | Residual |
|---|---|---|---|---|
| `V01.01` | `docs/ADDONS13-79/UAT.md` L249 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` assertion L207 memeriksa secara statis bahwa `MOVED` tidak beririsan dengan metode kelas provider yang diparse. | Tidak membuktikan registry, instalasi fresh atau seluruh varian; aspek tersebut **NOT ASSESSED**; lihat gap Gen5 V01. |
| `V01.02` | `docs/ADDONS13-79/UAT.md` L249 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V01; tidak membuktikan oracle lengkap. |
| `V01.03` | `docs/ADDONS13-79/UAT.md` L249 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` assertion L30,31,32 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V01; tidak membuktikan oracle lengkap. |
| `V01.04` | `docs/ADDONS13-79/UAT.md` L249 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` assertion L207,215 (`get_access_token` termasuk MOVED pada L12–18): deklarasi tidak ada pada provider dan ada pada glue. | Hanya deklarasi statis, bukan resolusi method efektif atau bukti runtime; sisa klausa dan varian **NOT ASSESSED**. |
| `V01.05` | `docs/ADDONS13-79/UAT.md` L249 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V01; tidak membuktikan oracle lengkap. |
| `V02.01` | `docs/ADDONS13-79/UAT.md` L255 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut08_user_predicates_environment_and_stubs` assertion L193,195 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V02; tidak membuktikan oracle lengkap. |
| `V02.02` | `docs/ADDONS13-79/UAT.md` L255 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` assertion L450,451,455 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V02; tidak membuktikan oracle lengkap. |
| `V03.01` | `docs/ADDONS13-79/UAT.md` L261 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` assertion L30,31,32 | Selector terpisah dari V03.02; tidak membuktikan komposisi berpasangan kedua basis tanpa glue maupun kedua urutan fresh install. Sisa klausa dan varian **NOT ASSESSED**. |
| `V03.02` | `docs/ADDONS13-79/UAT.md` L261 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` assertion L450,451,455 | Selector terpisah dari V03.01; tidak membuktikan komposisi berpasangan kedua basis tanpa glue maupun kedua urutan fresh install; unknown issuer tidak dibuktikan oleh assertion ini. Sisa klausa dan varian **NOT ASSESSED**. |
| `V03.03` | `docs/ADDONS13-79/UAT.md` L261 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V03; tidak membuktikan oracle lengkap. |
| `V03.04` | `docs/ADDONS13-79/UAT.md` L261 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V03; tidak membuktikan oracle lengkap. **Koreksi:** Review bersama Lead dan sibling owners, bukan keputusan terpisah. |
| `V03.05` | `docs/ADDONS13-79/UAT.md` L261 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V03; tidak membuktikan oracle lengkap. |
| `V04.01` | `docs/ADDONS13-79/UAT.md` L267 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` assertion L199,200 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V04; tidak membuktikan oracle lengkap. |
| `V04.02` | `docs/ADDONS13-79/UAT.md` L267 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` assertion L207–208,215–216,223: pemeriksaan deklarasi source provider, glue dan RS secara statis. | Tidak membuktikan effective MRO, dispatch, sentinel, seluruh retained RS declarations, trust atau activation; aspek tersebut dan varian lainnya **NOT ASSESSED**. |
| `V04.03` | `docs/ADDONS13-79/UAT.md` L267 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V04; tidak membuktikan oracle lengkap. |
| `V05.01` | `docs/ADDONS13-79/UAT.md` L273 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_login_template_uses_provider_owned_visibility_hook` assertion L266,270 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.02` | `docs/ADDONS13-79/UAT.md` L273 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.03` | `docs/ADDONS13-79/UAT.md` L273 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.04` | `docs/ADDONS13-79/UAT.md` L273 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.05` | `docs/ADDONS13-79/UAT.md` L273 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.06` | `docs/ADDONS13-79/UAT.md` L273 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V05.07` | `docs/ADDONS13-79/UAT.md` L273 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V05; tidak membuktikan oracle lengkap. |
| `V06.01` | `docs/ADDONS13-79/UAT.md` L279 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_contracts.py::TestResourceContracts::test_ut09_direct_controller_contract` assertion L283,284,286 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.02` | `docs/ADDONS13-79/UAT.md` L279 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.03` | `docs/ADDONS13-79/UAT.md` L279 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. **Koreksi:** Satu review/approval kontrak usulan helper/pass-through dan oracle terkait; jangan mengarang keputusan terpisah. |
| `V06.04` | `docs/ADDONS13-79/UAT.md` L279 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.05` | `docs/ADDONS13-79/UAT.md` L279 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V06.06` | `docs/ADDONS13-79/UAT.md` L279 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V06; tidak membuktikan oracle lengkap. |
| `V07.01` | `docs/ADDONS13-79/UAT.md` L285 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims` assertion L42,43,50; EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_non_system_cross_user_denial_precedes_signing` assertion L100,103 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V07; tidak membuktikan oracle lengkap. |
| `V07.02` | `docs/ADDONS13-79/UAT.md` L285 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_non_system_cross_user_denial_precedes_signing` assertion L100,103; STATIC UNIT: `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestResourceGlueLifetimeContract::test_actor_and_invalid_ttl_are_checked_before_a_warm_cache_lookup` assertion L415,417 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V07; tidak membuktikan oracle lengkap. **Koreksi:** Penolakan hanya untuk kombinasi actor/channel yang menurut kontrak memang ditolak, termasuk forged context; untuk setiap denial buktikan sebelum cache dan signing termasuk warm hit. Gen5 hanya cross-user sebelum signing; unit warm-cache statis bukan bukti semua channel. |
| `V07.03` | `docs/ADDONS13-79/UAT.md` L285 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_persistent_access_token_storage_remains_unsupported` assertion L131,133,135 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V07; tidak membuktikan oracle lengkap. **Koreksi:** L131,133,135 hanya denial dan pesan; tidak mengobservasi storage atau signer. |
| `V08.01` | `docs/ADDONS13-79/UAT.md` L291 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. |
| `V08.02` | `docs/ADDONS13-79/UAT.md` L291 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_access_token_omission_defaults_but_explicit_none_is_rejected` assertion L23,27,30 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. **Koreksi:** Decoded default audience dan rejection explicit None tidak membuktikan invocation helper tanpa argumen audience. |
| `V08.03` | `docs/ADDONS13-79/UAT.md` L291 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_user_resource_overrides_conflicting_audience_shapes` assertion L54,55; EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_user_invalid_resource_types_rejected_without_audience_fallback` assertion L61; EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_audience_list_is_supported_and_invalid_list_does_not_default` assertion L63,64,66 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. |
| `V08.04` | `docs/ADDONS13-79/UAT.md` L291 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V08; tidak membuktikan oracle lengkap. |
| `V09.01` | `docs/ADDONS13-79/UAT.md` L297 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_legacy_cache_reuses_within_ttl_bucket_and_rolls_over` assertion L84,85,92; EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_key_removal_after_warm_issuance_rejects` assertion L109 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. **Koreksi:** Concurrency mencakup explicit invalidation, bukan hanya perubahan lain. |
| `V09.02` | `docs/ADDONS13-79/UAT.md` L297 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_key_removal_after_warm_issuance_rejects` assertion L109 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. **Koreksi:** Key removal setelah warm issuance hanya mengassert ValueError; tidak mengobservasi signer atau stale cache hit/return. |
| `V09.03` | `docs/ADDONS13-79/UAT.md` L297 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. |
| `V09.04` | `docs/ADDONS13-79/UAT.md` L297 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V09; tidak membuktikan oracle lengkap. |
| `V10.01` | `docs/ADDONS13-79/UAT.md` L303 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_add_url_access_token_rejects_url_bearer_by_default` assertion L76 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V10.02` | `docs/ADDONS13-79/UAT.md` L303 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc_resource/tests/integration/test_access_token_audience_presence.py::TestAccessTokenAudiencePresence::test_add_url_auto_login_rejects_explicit_audience_without_signing` assertion L97 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. **Koreksi:** L97 hanya mengassert exception, bukan no signer/cache; detail denial menunggu approval kontrak. Exception terhadap default hanya jika Owner menyetujui secara terpisah. |
| `V10.03` | `docs/ADDONS13-79/UAT.md` L303 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V10.04` | `docs/ADDONS13-79/UAT.md` L303 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V10.05` | `docs/ADDONS13-79/UAT.md` L303 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V10; tidak membuktikan oracle lengkap. |
| `V11.01` | `docs/ADDONS13-79/UAT.md` L309 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` assertion L208 memeriksa secara statis bahwa `get_mobile_access_token` tidak dideklarasikan sebagai metode kelas provider yang diparse. | Tidak membuktikan penghapusan pada closure first-party lain, alias/shim, instalasi atau resolusi runtime; aspek tersebut dan varian lainnya **NOT ASSESSED**. **Koreksi:** Both orders tidak menetapkan no-glue; jangan menambah pembatasan itu pada oracle. |
| `V11.02` | `docs/ADDONS13-79/UAT.md` L309 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V11; tidak membuktikan oracle lengkap. |
| `V11.03` | `docs/ADDONS13-79/UAT.md` L309 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V11; tidak membuktikan oracle lengkap. |
| `V12.01` | `docs/ADDONS13-79/UAT.md` L315 | STATIC UNIT | STATIC UNIT: `amr_oidc_resource/tests/unit/test_resource_glue_contract.py::TestOdoo13TestDiscoveryContract::test_integration_modules_are_registered_in_root_tests_package` assertion L510,515 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. **Koreksi:** Rekonsiliasi fixture relevan dan pemetaan sumber→target serta assertion actor/audience/cache/rejection/security dan legacy loader; kesetaraan daftar modul di target saja tidak membuktikan relokasi atau preservation. |
| `V12.02` | `docs/ADDONS13-79/UAT.md` L315 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. |
| `V12.03` | `docs/ADDONS13-79/UAT.md` L315 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. |
| `V12.04` | `docs/ADDONS13-79/UAT.md` L315 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V12; tidak membuktikan oracle lengkap. |
| `V13.01` | `docs/ADDONS13-79/UAT.md` L321 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V13.02` | `docs/ADDONS13-79/UAT.md` L321 | NOT ASSESSED (trusted-local) | Konteks remote mocked JWKS, bukan bukti local: EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_issuer_rejected_before_transport` assertion L300,304,306; EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_invalid_signature_rejected_without_fallback` assertion L342,345,347 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. **Koreksi:** Dua negative test yang dikutip memakai remote mocked JWKS; bukan trusted-local provider→RS. Binding local dan negative terkait NOT ASSESSED. |
| `V13.03` | `docs/ADDONS13-79/UAT.md` L321 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V13.04` | `docs/ADDONS13-79/UAT.md` L321 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V13.05` | `docs/ADDONS13-79/UAT.md` L321 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V13; tidak membuktikan oracle lengkap. |
| `V14.01` | `docs/ADDONS13-79/UAT.md` L327 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.02` | `docs/ADDONS13-79/UAT.md` L327 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.03` | `docs/ADDONS13-79/UAT.md` L327 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.04` | `docs/ADDONS13-79/UAT.md` L327 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_missing_selected_local_key_no_fallback` assertion L216,217,224 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. **Koreksi:** L216–217 adalah positive sebelum key removal; L224 sesudah removal adalah Unauthorized. Mock fetch_json bukan observasi semua jaringan atau bukti zero introspection/self-provider HTTP. |
| `V14.05` | `docs/ADDONS13-79/UAT.md` L327 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V14.06` | `docs/ADDONS13-79/UAT.md` L327 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V14; tidak membuktikan oracle lengkap. |
| `V15.01` | `docs/ADDONS13-79/UAT.md` L333 | STATIC UNIT | STATIC UNIT: `amr_resource/tests/unit/test_migration_unit.py::MigrationUnitTests::test_native_loader_and_dependency_declarations` assertion L114,116 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V15; tidak membuktikan oracle lengkap. **Koreksi:** Syarat bersama seluruh child: Odoo 13 dan CPython 3.7.3 yang disetujui, dependency terkwalifikasi, DB fresh terisolasi yang diotorisasi; static manifest/pin tidak membuktikan runtime atau closure. |
| `V15.02` | `docs/ADDONS13-79/UAT.md` L333 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V15; tidak membuktikan oracle lengkap. **Koreksi:** Catat runtime aktual dan cleanup beserta readback; bukan hanya rencana cleanup. |
| `V15.03` | `docs/ADDONS13-79/UAT.md` L333 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V15; tidak membuktikan oracle lengkap. |
| `V16.01` | `docs/ADDONS13-79/UAT.md` L339 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. **Koreksi:** Lima metode: `is_user_allow_create_token`, `get_access_token`, `create_access_token`, `add_url_access_token`, `get_auto_login_url`; review kompatibilitas masing-masing, penghapusan mobile dan external unknowns tetap NOT ASSESSED. |
| `V16.02` | `docs/ADDONS13-79/UAT.md` L339 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. |
| `V16.03` | `docs/ADDONS13-79/UAT.md` L339 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. |
| `V16.04` | `docs/ADDONS13-79/UAT.md` L339 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 V16; tidak membuktikan oracle lengkap. |
| `U01.01` | `docs/ADDONS13-79/UAT.md` L345 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT01::test_valid_provider_token_operation_and_missing_configuration_rejects` assertion L30,31,32; EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat03_manual_config_and_jwks_boundary` assertion L135,152,155 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U01; tidak membuktikan oracle lengkap. |
| `U01.02` | `docs/ADDONS13-79/UAT.md` L345 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U01; tidak membuktikan oracle lengkap. |
| `U01.03` | `docs/ADDONS13-79/UAT.md` L345 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U01; tidak membuktikan oracle lengkap. |
| `U02.01` | `docs/ADDONS13-79/UAT.md` L351 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U02; tidak membuktikan oracle lengkap. |
| `U02.02` | `docs/ADDONS13-79/UAT.md` L351 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U02; tidak membuktikan oracle lengkap. |
| `U02.03` | `docs/ADDONS13-79/UAT.md` L351 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U02; tidak membuktikan oracle lengkap. |
| `U03.01` | `docs/ADDONS13-79/UAT.md` L357 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U03; tidak membuktikan oracle lengkap. **Koreksi:** Evaluasi integrasi terpilih disabled dan baseline/no new trust dalam komposisi yang berlaku bersama U03.03; jangan menciptakan cross-product wajib yang tidak diterima. |
| `U03.02` | `docs/ADDONS13-79/UAT.md` L357 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U03; tidak membuktikan oracle lengkap. **Koreksi:** Backend removed/disabled saat integrasi enabled: fail closed tanpa silent HTTP/introspection; rekonsiliasi komposisi yang berlaku tanpa mewajibkan cross-product tambahan. |
| `U03.03` | `docs/ADDONS13-79/UAT.md` L357 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U03; tidak membuktikan oracle lengkap. **Koreksi:** Provider-only, RS-only dan adapter opsional jika didukung harus direkonsiliasi dengan kondisi disabled/backend U03.01/.02; applicability spesifik belum dipastikan. |
| `U04.01` | `docs/ADDONS13-79/UAT.md` L363 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** U04.01–.04 adalah satu alur terintegrasi: issuer lokal yang disetujui memakai real selected issuance dengan user/client dan synthetic RS256 key; token yang sama divalidasi RS. |
| `U04.02` | `docs/ADDONS13-79/UAT.md` L363 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signing_produces_verifiable_rs256_at_jwt` assertion L581,582 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** Header/claims, policy, resolver/binding dan eligible user harus diperiksa dalam satu alur U04.01–.04; static signer unit terpisah bukan pembukti end-to-end. |
| `U04.03` | `docs/ADDONS13-79/UAT.md` L363 | STATIC UNIT | STATIC UNIT: `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` assertion L305,306 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** Verified provenance dan user harus keluar dari RS untuk token yang sama pada alur U04.01–.04; unit RS terpisah bukan alur issuer→RS. |
| `U04.04` | `docs/ADDONS13-79/UAT.md` L363 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U04; tidak membuktikan oracle lengkap. **Koreksi:** Bukan handcrafted token sebagai pengganti issuer; ini syarat satu alur U04.01–.04. |
| `U05.01` | `docs/ADDONS13-79/UAT.md` L369 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_invalid_signature_rejected_without_fallback` assertion L342,345,347 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U05; tidak membuktikan oracle lengkap. |
| `U06.01` | `docs/ADDONS13-79/UAT.md` L375 | NOT ASSESSED (trusted-local) | Konteks remote mocked JWKS, bukan bukti local: EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_issuer_rejected_before_transport` assertion L300,304,306 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. **Koreksi:** Setiap negative yang berlaku wajib reject DAN never fallback; test Gen5 remote JWKS bukan bukti trusted-local issuer/DB/provider binding atau semua varian. |
| `U06.02` | `docs/ADDONS13-79/UAT.md` L375 | NOT ASSESSED (trusted-local) | Konteks remote mocked JWKS, bukan bukti local: EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_kid_rejected_without_fallback` assertion L328,332,334 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. **Koreksi:** Setiap negative yang berlaku wajib reject DAN never fallback sesuai selected local kid contract; Gen5 remote mocked JWKS bukan bukti local kid/backend matrix. |
| `U06.03` | `docs/ADDONS13-79/UAT.md` L375 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. |
| `U06.04` | `docs/ADDONS13-79/UAT.md` L375 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U06; tidak membuktikan oracle lengkap. |
| `U07.01` | `docs/ADDONS13-79/UAT.md` L381 | EXECUTED PARTIAL (provider decoder saja; selected RS NOT ASSESSED) | EXECUTED PARTIAL: `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT08::test_required_issuer_audience_and_time_claims_reject_invalid_tokens` assertion L221,236; provider `_decode`, bukan selected RS verifier | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. **Koreksi:** Wrong/malformed nilai harus ditentukan oleh policy dan konteks; jangan menciptakan setiap nilai sebagai negative wajib. |
| `U07.02` | `docs/ADDONS13-79/UAT.md` L381 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc/tests/integration/test_provider_selected_uat.py::TestProviderSelectedUAT08::test_required_issuer_audience_and_time_claims_reject_invalid_tokens` assertion L221,236: provider `_decode` saja (expired dan future nbf pada L214–215). | Selected RS verifier **NOT ASSESSED**; future iat, exact boundary, sisa klausa dan varian **NOT ASSESSED**. L236 memeriksa missing required claims, bukan time boundary. **Koreksi:** Future/boundary mengikuti agreed policy dan konteks; jangan mengasumsikan semua waktu tepat boundary selalu reject. |
| `U07.03` | `docs/ADDONS13-79/UAT.md` L381 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. |
| `U07.04` | `docs/ADDONS13-79/UAT.md` L381 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. **Koreksi:** Typing dan independence mengikuti policy/kontrak terpilih; bukan aturan nilai baru. |
| `U07.05` | `docs/ADDONS13-79/UAT.md` L381 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U07; tidak membuktikan oracle lengkap. |
| `U08.01` | `docs/ADDONS13-79/UAT.md` L387 | STATIC UNIT | STATIC UNIT: `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat17_audience_any_exact` assertion L354,358; STATIC UNIT: `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat18_azp_optional_only_by_profile` assertion L365 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U08; tidak membuktikan oracle lengkap. **Koreksi:** Positive single/list, allowlist dan azp hadir/absent berlaku menurut policy yang disetujui, bukan semua kombinasi wajib. |
| `U08.02` | `docs/ADDONS13-79/UAT.md` L387 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_untrusted_audience_rejected_before_jwks` assertion L314,318,320 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U08; tidak membuktikan oracle lengkap. **Koreksi:** Mismatch/malformed/absent hanya negative jika diwajibkan policy; jangan menambah bentuk atau cross-product wajib. |
| `U08.03` | `docs/ADDONS13-79/UAT.md` L387 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U08; tidak membuktikan oracle lengkap. |
| `U09.01` | `docs/ADDONS13-79/UAT.md` L393 | NOT ASSESSED (validation denial) | EXECUTED PARTIAL (penolakan penulisan duplikat saja): `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_binding_and_audience_uniqueness` assertion L40–41 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U09; tidak membuktikan oracle lengkap. **Koreksi:** L40–41 menguji penolakan penulisan mapping/audience duplikat; L42–43 menguji penghapusan audience, bukan denial saat validasi token; seluruh denial validasi tetap NOT ASSESSED. |
| `U09.02` | `docs/ADDONS13-79/UAT.md` L393 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U09; tidak membuktikan oracle lengkap. |
| `U10.01` | `docs/ADDONS13-79/UAT.md` L399 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U10.02` | `docs/ADDONS13-79/UAT.md` L399 | NOT ASSESSED | Gen5 `test_signing_configuration_change_uses_new_key_and_ttl` L112–127 hanya local HS256: old-token decode dengan new secret ditolak; bukan revocation trust-store. | Retain/validate old and new, signer switch, trust-store revoke/remove old dan old/unknown kid rejection **NOT ASSESSED**. |
| `U10.03` | `docs/ADDONS13-79/UAT.md` L399 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U10.04` | `docs/ADDONS13-79/UAT.md` L399 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_oidc/tests/integration/test_public_key_orm.py::TestPublicKeyORM::test_rsa_ec_jwks_active_signing_and_public_only` assertion L155 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U10.05` | `docs/ADDONS13-79/UAT.md` L399 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U10; tidak membuktikan oracle lengkap. |
| `U11.01` | `docs/ADDONS13-79/UAT.md` L405 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_addons13_83_uat04_missing_selected_local_key_no_fallback` assertion L216,217,224 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U11; tidak membuktikan oracle lengkap. **Koreksi:** Evidence yang dikutip hanya missing selected local key: positive sebelum removal dan Unauthorized setelahnya; tidak membuktikan failure matrix lainnya. |
| `U11.02` | `docs/ADDONS13-79/UAT.md` L405 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U11; tidak membuktikan oracle lengkap. |
| `U11.03` | `docs/ADDONS13-79/UAT.md` L405 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U11; tidak membuktikan oracle lengkap. |
| `U12.01` | `docs/ADDONS13-79/UAT.md` L411 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U12.02` | `docs/ADDONS13-79/UAT.md` L411 | NOT ASSESSED | Gen5 `test_addons13_83_uat04_missing_selected_local_key_no_fallback` L214–227: patched `helper_module.fetch_json` mock tidak dipanggil pada positive dan missing-key. | Bukan process/socket-wide egress atau introspection observer; zero introspection dan zero self-provider outbound untuk positive, negatives dan unavailable provider **NOT ASSESSED**. |
| `U12.03` | `docs/ADDONS13-79/UAT.md` L411 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U12.04` | `docs/ADDONS13-79/UAT.md` L411 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U12.05` | `docs/ADDONS13-79/UAT.md` L411 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U12; tidak membuktikan oracle lengkap. |
| `U13.01` | `docs/ADDONS13-79/UAT.md` L417 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. |
| `U13.02` | `docs/ADDONS13-79/UAT.md` L417 | EXECUTED PARTIAL | EXECUTED PARTIAL: `amr_resource/tests/integration/test_registry.py::TestResourceRegistry::test_no_default_mapping_or_ordinary_registry_access` assertion L18,25,27; EXECUTED PARTIAL: `amr_oidc/tests/integration/test_client_secret_verifier.py::TestClientSecretVerifier::test_ordinary_user_can_read_client_but_not_verifier` assertion L57,58 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. **Koreksi:** ACL registry dan pembacaan client/verifier hanya slice akses; bukan bukti anti-spoof profile atau tidak tereksposnya seluruh private material. |
| `U13.03` | `docs/ADDONS13-79/UAT.md` L417 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. |
| `U13.04` | `docs/ADDONS13-79/UAT.md` L417 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U13; tidak membuktikan oracle lengkap. |
| `U14.01` | `docs/ADDONS13-79/UAT.md` L423 | NOT ASSESSED | Assertion L199–200 pada `amr_oidc/tests/unit/test_resource_glue_contract.py::ResourceGlueContract::test_provider_methods_are_owned_by_optional_glue` hanya memeriksa dependensi dan `auto_install` manifest glue. | Assertion tersebut tidak memeriksa manifest addon dasar atau import-nya, sehingga tidak membuktikan ketiadaan hard reverse dependency maupun hard reverse import. |
| `U14.02` | `docs/ADDONS13-79/UAT.md` L423 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U14; tidak membuktikan oracle lengkap. |
| `U14.03` | `docs/ADDONS13-79/UAT.md` L423 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U14; tidak membuktikan oracle lengkap. |
| `U14.04` | `docs/ADDONS13-79/UAT.md` L423 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U14; tidak membuktikan oracle lengkap. |
| `U15.01` | `docs/ADDONS13-79/UAT.md` L429 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` assertion L396,398 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U15; tidak membuktikan oracle lengkap. **Koreksi:** Unit menggunakan fake/mocks client, mapping dan signer; tidak membuktikan unauthorized issuance end-to-end. |
| `U15.02` | `docs/ADDONS13-79/UAT.md` L429 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` assertion L396,398; STATIC UNIT: `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_signer_requires_bound_provenance_single_rs256_key_and_at_jwt` assertion L529,533 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U15; tidak membuktikan oracle lengkap. **Koreksi:** Unit menggunakan fake signer/provenance; tidak membuktikan fresh jti/claims atau authenticated identity pada real issuance. |
| `U15.03` | `docs/ADDONS13-79/UAT.md` L429 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U15; tidak membuktikan oracle lengkap. |
| `U16.01` | `docs/ADDONS13-79/UAT.md` L435 | STATIC UNIT | STATIC UNIT: `amr_oidc/tests/unit/test_package_contract.py::PackageContract::test_candidate_manifest_identity_and_dependencies` assertion L95,96 | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U16; tidak membuktikan oracle lengkap. **Koreksi:** L95–96 hanya version dan license manifest; bukan dependency closure, runtime, instalasi atau suites. |
| `U16.02` | `docs/ADDONS13-79/UAT.md` L435 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U16; tidak membuktikan oracle lengkap. |
| `U16.03` | `docs/ADDONS13-79/UAT.md` L435 | NOT ASSESSED | tidak ada assertion/test yang diverifikasi cocok untuk klausa ini | Sisa klausa dan seluruh varian yang belum diekspansi **NOT ASSESSED**; lihat gap Gen5 U16; tidak membuktikan oracle lengkap. |

## Ekspansi parsial U10/U12 — tidak mengubah 124 klausa induk

Subatom berikut memakai fixture synthetic dan identitas Gen5 yang dirujuk di atas; status EXECUTED hanya untuk assertion sempit, bukan keseluruhan oracle. Subatom trust-admin memerlukan actor trust-admin dan trust-store terpilih; subatom network memerlukan selected validation call serta observer terkalibrasi. Ekspansi ini **belum mencakup seluruh varian V01–V16/U01–U16**; varian lain tetap NOT ASSESSED sebagaimana tabel induk.

| ID | Varian / fixture-actor | Status | Bukti / residual |
|---|---|---|---|
| U10.02.a | Retain old key untuk approved window; trust-admin | NOT ASSESSED | Overlap trust-store belum dibuktikan. |
| U10.02.b | Validasi old key selama window; trust-admin | NOT ASSESSED | Selected RS verifier belum dibuktikan. |
| U10.02.c | Validasi new key selama window; trust-admin | NOT ASSESSED | Selected RS verifier belum dibuktikan. |
| U10.02.d | Switch signer; trust-admin | NOT ASSESSED | Switch signer dalam lifecycle trust-store belum dibuktikan. |
| U10.02.e | Revoke/remove old key; trust-admin | NOT ASSESSED | Revocation trust-store belum dibuktikan. |
| U10.02.f | Reject old token sesudah revoke; selected RS | NOT ASSESSED | Tidak disamakan dengan local HS256 di bawah. |
| U10.02.g | Reject unknown kid; selected RS | NOT ASSESSED | Rotation lifecycle belum dibuktikan. |
| U10.related.a | Old-token decode dengan new local secret; synthetic user | EXECUTED PARTIAL | Gen5 `test_signing_configuration_change_uses_new_key_and_ttl` L112–127: `InvalidSignatureError`; bukan trust-store revocation. |
| U12.02.a | Positive: zero introspection; selected call | NOT ASSESSED | Mock fetch bukan introspection monitor. |
| U12.02.b | Positive: zero self-provider outbound; selected call | NOT ASSESSED | Process/socket observer belum dibuktikan. |
| U12.02.c | Negatives: zero introspection; selected call | NOT ASSESSED | Mencakup semua negative yang berlaku, bukan hanya missing key. |
| U12.02.d | Negatives: zero self-provider outbound; selected call | NOT ASSESSED | Process/socket observer belum dibuktikan. |
| U12.02.e | Unavailable provider: zero introspection; selected call | NOT ASSESSED | Fixture unavailable belum dibuktikan. |
| U12.02.f | Unavailable provider: zero self-provider outbound; selected call | NOT ASSESSED | Fixture dan process/socket observer belum dibuktikan. |
| U12.related.a | Positive local key: patched fetch_json tidak dipanggil; synthetic profile | EXECUTED PARTIAL | Gen5 `test_addons13_83_uat04_missing_selected_local_key_no_fallback` L214–217; hanya mock. |
| U12.related.b | Missing local key: patched fetch_json tidak dipanggil; synthetic profile | EXECUTED PARTIAL | Test sama L219–227; hanya mock, bukan semua outbound/introspection. |

**Rekonsiliasi mekanis:** 124 ID klausa asli vs 124 ID terpetakan; exact multiset match = true; duplikat asli = 0; duplikat mapping = 0. Pemeriksaan ini hanya identitas, bukan kelengkapan semantik. SHA-256 dokumen sebelum tambahan `dccd0b56daaeec49e0c133b15ca907897cefbbdb452a77c9d99608930daf057c`; accepted UAT `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; accepted PRD `2495dfee5ecec88063b0db069267a0132f29969820fcaede5259117d1706ee43`; safe-summary `50c8f26e3082b6c3c5a3d6141e7e296cb856e801248a4f9b84a22a4223b0791d`.

## Ekspansi semantik tambahan — inventaris untuk review, NOT ASSESSED

Sumber: UAT SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`, fixture bersama L7–13 dan oracle lengkap setiap kasus di atas. Child adalah inventaris kandidat dimensi, bukan otomatis requirement: hanya varian yang didukung oracle accepted dan kontrak yang berlaku harus diperiksa; daftar dimensi bukan klaim seluruh produk kartesian telah dinilai. Expected diwarisi dari klausa induk; khusus U05/U06/U07/U09/U11/V13 negatif berarti penolakan sesuai oracle. Seluruh child baru **NOT ASSESSED**, actual **NOT RUN**; tidak mewarisi status EXECUTED PARTIAL induk. Irisan terverifikasi sebelumnya tetap berlaku hanya pada batasnya. U10 trust-store tetap NOT ASSESSED; U12 mock hanya fetch_json, bukan egress. SCOPE-01 OPEN. V06 helper dan V10 denial tetap menunggu approval; lifecycle/fresh mapping mengikuti gate UAT.

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

Sumber UAT SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; crosswalk sebelum tambahan `03ad47ae6ec81de2022f85d8959d5c7dc2976e81559145cba6a67f35024281c1`. Label internal DRAFT FINAL dipertahankan byte-identical; `ACCEPTANCE-METADATA.md` mencatat persetujuan Owner atas hash UAT tersebut. Semua child (.01 dst adalah suffix ID induk) dan atomic berikut **NOT ASSESSED**, actual **NOT RUN**; tidak mewarisi status induk. Atomic berarti satu kewajiban atau gate dalam konteks kasus lengkap, bukan sudah dibuktikan. Fixture, actor, varian dan outcome UAT tetap berlaku; gate belum disetujui tetap BLOCKED. Label BELUM DIPECAH sebelumnya dipertahankan historis dan disupersedi review di sini.

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

### Rekonsiliasi dan batas review 124 induk

124 ID disposisi unik diperiksa secara mekanis; 32 review di atas, 92 ekspansi sebelumnya dibandingkan dengan teks UAT V/U sebagai inventaris dimensi, belum diverifikasi individual terhadap test/assertion dan belum dinyatakan lengkap. Tidak ada hasil runtime atau acceptance disimpulkan. Semua child inventaris tetap NOT ASSESSED; status child lama U10/U12 tetap sesuai tabel asal.

- **U05.01:** 17 varian × dua outcome **no user** dan **no session** diuraikan pada overlay koreksi di bawah; seluruhnya NOT ASSESSED.
- **V02/V03:** tiap metode, komposisi dan urutan untuk hasil verifier, issuance dan pass-through belum dipetakan individual ke fixture/assertion.
- **V06/V07:** relevansi kombinasi actor, route, branch, komposisi dan denial sebelum cache/signing belum direkonsiliasi satu per satu; daftar dimensi bukan bukti produk kartesian.
- **V13.02/U07.01:** ekspansi mekanis dikualifikasi oleh overlay koreksi di bawah; applicability dan kontrak terpilih tidak boleh diasumsikan.
- **U03/U12:** hubungan masing-masing komposisi dan varian dengan backend disabled, seluruh validation call dan observer belum diverifikasi; mock fetch_json bukan observer egress.
- **U10.02/U12.02:** child terdahulu dipertahankan tanpa duplikasi atau peningkatan status; lifecycle trust-store, negative dan zero egress belum terbukti.
- **Seluruh 92:** pemeriksaan lengkap tiap actor, varian, boundary/outcome terhadap assertion masih terbuka; daftar temuan ini tidak lengkap.

SCOPE-01 tetap OPEN; approval kandidat/konfigurasi, Owner fresh mapping/profil, helper/denial, lifecycle, kid/nbf dan otorisasi terpisah tetap gate sesuai UAT. Tidak ada test, runtime, DB atau network dijalankan.

## Koreksi review U05, V13, U07 — overlay atas inventaris historis

Sumber oracle byte-identik UAT `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`, commit test `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`. Overlay ini mengoreksi interpretasi, bukan menambah acceptance atau menghapus inventaris historis. Semua child baru **NOT ASSESSED**, actual **NOT RUN**; historical EXECUTED PARTIAL tetap hanya untuk boundary semula.

### U05 — outcome independen untuk setiap negative

Setiap baris merujuk varian yang bernama pada U05.01 di atas. Selain rejection, `.a` adalah assertion **no user**, `.b` adalah assertion **no session**, masing-masing diamati pada boundary selected yang relevan; tidak boleh menyimpulkan salah satunya hanya dari exception. Semua 34 assertion berikut **NOT ASSESSED / NOT RUN**.

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

### V13.02 dan U07.01 — batas varian

- **V13.02:** teks L321 menuliskan “wrong/missing/ambiguous provider, DB, issuer, client, kid, key, algorithm, token class, signature, claims, timing, audience, azp, stale policy/provenance, wrong company/user”. Daftar `.01`–`.39` di atas adalah kandidat pembacaan, **bukan matriks wajib**: khususnya missing/ambiguous signature, timing, token class, algorithm, claims, audience dan azp bukan otomatis fixture atau requirement independen. Pertahankan hanya varian yang secara semantik berlaku menurut klausa dan selected contract; contoh yang tak berlaku bersifat ilustratif/tidak diwajibkan. Missing azp tidak otomatis negatif: lihat U08 dan policy yang disetujui. `.40`–`.43` tetap sesuai stale policy/provenance dan wrong company/user; semua NOT ASSESSED. Tidak memutuskan kontrak melalui overlay ini.
- **U07.01:** L381 menyebut missing/wrong/malformed untuk klaim yang tercantum, tetapi arti “wrong” untuk exp/iat/jti/sub dan bentuk malformed atau nilai yang mungkin tidak dapat ditentukan sebagai salah tanpa policy, binding dan konteks. `.01`–`.24` tetap kandidat; nilai konkret yang bukan negative menurut accepted oracle/selected contract hanya ilustratif, tidak diwajibkan. Aud empty/mixed invalid/nonmatching tetap eksplisit; exp expired, iat/nbf future dan exact boundary mengikuti L381 serta policy yang berlaku. Optional nbf absent bukan otomatis negative. Tiap negative yang berlaku harus reject; semua child NOT ASSESSED.
- **U07 evidence:** test Gen5 L201–237 menguji provider decoder `_decode` (wrong iss/aud, expired exp, future nbf, exp None, omission iss/aud/exp), bukan actual selected RS verification atau seluruh U07; selected RS dan child-child tetap NOT ASSESSED. Historical slice selector tidak dinaikkan menjadi bukti selected RS.

### Cakupan review

Tiga dari 92 disposisi SPLIT (`U05.01`, `V13.02`, `U07.01`) diperiksa terarah terhadap teks oracle dan batas evidence terkait; **89 lainnya belum diperiksa individual dalam review koreksi ini**. Tidak ada klaim verifikasi seluruh varian V/U, fixture, actor atau mapping test; 32 disposisi review sebelumnya dan batas historis tetap berlaku. Rekonsiliasi 458 child di atas adalah hitungan historis sebelum 34 child outcome tambahan, bukan jumlah baru yang telah disertifikasi. Tidak ada test, DB, network, ledger atau ref action dilakukan.
