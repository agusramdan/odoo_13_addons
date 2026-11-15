> **BATAS HISTORIS:** Seluruh pernyataan NOT RUN, belum diverifikasi, dan ketiadaan hasil pada bagian awal di bawah adalah status telaah statis pada kandidat `f26a674270467c85b7750073e085e9955e5461e1`, bukan pernyataan bahwa tidak pernah ada run berikutnya. Rekonsiliasi diagnostik Gen5 pada commit berbeda dicatat di lampiran akhir; tidak mengubah teks historis, bukan rebind, dan bukan PASS UAT penuh.

# ADDONS13-79 Step 4 — crosswalk atomik C/T dan M/I (statis)

Kandidat sumber HEAD `f26a674270467c85b7750073e085e9955e5461e1`; identitas ini bukan persetujuan rebind. UAT `docs/ADDONS13-79/UAT.md` SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; PRD `docs/ADDONS13-79/PRD.md` SHA-256 `2495dfee5ecec88063b0db069267a0132f29969820fcaede5259117d1706ee43`. `ACCEPTANCE-METADATA.md` menerima byte spesifikasi termasuk label DRAFT; bukan rebind, konfigurasi, run, waiver atau penerimaan risiko. Fresh issuer mapping/profile scope masih PENDING dan positive issuance terkait BLOCKED. SCOPE-01 OPEN. UAT dan seluruh tes NOT RUN.

Semua kasus juga mewarisi seluruh prasyarat/bukti UAT:7–13,17: synthetic isolated fresh disposable DB dengan identitas/kepemilikan diverifikasi; issuer/client/user/company/key/trust/jam dan signer/cache/transport observer; actor public/portal/internal/system/trust admin/service sesuai kasus; Tester berwenang, admin dan security/deployment owner sesuai tindakan; semua varian terpisah, readback/observasi tersanitasi, no secrets, full calibrated egress observer bila diminta, cleanup run-owned dan readback. Runtime Odoo 13/CPython 3.7.3, konfigurasi final, izin test/DB/runtime dan candidate binding belum disetujui untuk run ini. Tidak ada klaim eksekusi atau hasil historis.

Setiap butir adalah unit pemeriksaan (varian yang disebut tetap masing-masing wajib); referensi huruf berarti **hanya irisan** assertion di katalog, bukan cakupan penuh. `GAP/NOT ASSESSED` berarti belum ada assertion memadai yang dipetakan dalam telaah terbatas ini, bukan bukti tidak ada tes di seluruh repo. Semua butir selain rujukan irisan tetap GAP/NOT ASSESSED; tidak ada kasus dinyatakan lengkap. Fresh-invalid dan legacy-existing/unknown tidak boleh disamakan; legacy glue adalah jalur terpisah. Positive fresh issuer menunggu keputusan scope, meski ada fake.

## Katalog assertion kandidat dan discovery statis

Unit = selector niat `skills/odoo-unit-test/scripts/run_tests.py --addon <addon>`; fake/source-loaded, bukan native. Native = modul langsung diekspos di `amr_oidc/tests/__init__.py` atau `amr_oidc_resource/tests/__init__.py`; selector niat Odoo addon/test module, discovery/collection dan execution belum diverifikasi. Nama metode bukan bukti RPC/HTTP. SHA test file di bawah untuk identitas source saat telaah, bukan bukti execution.

- **A** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_ttl_defaults_in_memory_and_enforces_canonical_ascii_bounds` — unit mock/source-loaded; Fake absent parameter returns 900; configured strings 60/86400 return integers; selected malformed values raise ValueError. No persistence/readback. SHA-256 `b0385c50ec0619a8411d687a37efe4eda436683c04e224876109aae087b570c6`.
- **B** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` — unit mock/source-loaded; Fake authenticated client, mapper and signer: response TTL and exp−iat 900, claims and absent identifiers; two reauth/config/sign calls, invalid overrides denied, 60 override accepted. No actual signature, route or RS. SHA-256 `b0385c50ec0619a8411d687a37efe4eda436683c04e224876109aae087b570c6`.
- **C** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileModelBoundaryTests::test_settings_reject_noncanonical_and_out_of_range_fresh_ttl_before_persistence` — unit mock/source-loaded; Fake system settings create rejects 060, +60, 59, 86401, bool and float; not rendered Settings. SHA-256 `b0385c50ec0619a8411d687a37efe4eda436683c04e224876109aae087b570c6`.
- **D** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileModelBoundaryTests::test_settings_direct_rpc_requires_system_group_for_profile_and_ttl` — unit mock/source-loaded; Fake non-system set_values raises AccessError; direct Python, not RPC dispatch. SHA-256 `b0385c50ec0619a8411d687a37efe4eda436683c04e224876109aae087b570c6`.
- **E** `amr_oidc/tests/unit/test_subject_mapping_retry.py::SubjectMapperRetryTests::test_unique_collision_with_archived_subject_retries_new_random_value` — unit mock/source-loaded; Fake store, deterministic collision against archived subject then replacement; two random calls. SHA-256 `09f03fa9cce660c46e1af193af9bcd4010e564bf2068c98be9546da36a6a0d26`.
- **F** `amr_oidc/tests/unit/test_subject_mapping_retry.py::SubjectMapperRetryTests::test_unique_error_after_same_principal_winner_returns_existing_subject` — unit mock/source-loaded; Fake insertion hook simulates winning row; returned winner, one record; not parallel DB. SHA-256 `09f03fa9cce660c46e1af193af9bcd4010e564bf2068c98be9546da36a6a0d26`.
- **G** `amr_oidc/tests/unit/test_subject_mapping_retry.py::SubjectMapperRetryTests::test_repeated_unique_collisions_exhaust_three_attempts_without_reserving` — unit mock/source-loaded; Fake collisions thrice cause UserError and leave pre-existing row; no signer or real rollback. SHA-256 `09f03fa9cce660c46e1af193af9bcd4010e564bf2068c98be9546da36a6a0d26`.
- **H** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_archived_subject_keeps_both_unique_reservations_and_denies_issuance` — native exposure; ORM fixture archives mapping; rejects reissue and both duplicate dimensions via IntegrityError. SHA-256 `d9ee30182ded95345319583b20ed2c787823e8e434550d3a5a766e7bffb336d1`.
- **I** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerSubjectIdentity::test_subject_is_stable_across_user_rename_and_distinct_per_user` — native exposure; ORM direct mapping calls assert lowercase-hex length 64, unchanged across rename, different second user; not signed issuance. SHA-256 `d9ee30182ded95345319583b20ed2c787823e8e434550d3a5a766e7bffb336d1`.
- **J** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_user_deletion_is_restricted_by_subject_foreign_key` — native exposure; ORM sudo user unlink raises IntegrityError in savepoint. SHA-256 `d9ee30182ded95345319583b20ed2c787823e8e434550d3a5a766e7bffb336d1`.
- **K** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_every_human_role_has_no_mapping_acl` — native exposure; Internal/system/portal: read ACL false, search/create raise AccessError; not full actor/operation matrix. SHA-256 `d9ee30182ded95345319583b20ed2c787823e8e434550d3a5a766e7bffb336d1`.
- **L** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_profile_instance_binding_requires_external_marker_and_matches_digest` — unit mock/source-loaded; Fake environment/parameters reject missing or changed marker and preserve unchanged digest; not real clone/DB. SHA-256 `b0385c50ec0619a8411d687a37efe4eda436683c04e224876109aae087b570c6`.
- **M** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_bad_client_credential_stops_before_mapping_or_signer` — unit mock/source-loaded; Fake credential check raises, mapper/signer not called; not real HTTP. SHA-256 `b0385c50ec0619a8411d687a37efe4eda436683c04e224876109aae087b570c6`.
- **N** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` — unit mock/source-loaded; Synthetic signed RS256 fixture, fake environment checks valid verified provenance/user and rejects wrong key; not issuer-to-RS. SHA-256 `29f00d216c240fb297efbf34fbe38c34b54ebe8dd78d8c2bb6448e81a1345ec3`.
- **O** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat19_binding_exact_no_email_login_or_autobind` — unit mock/source-loaded; Fake binding environment exercises exact binding and negative no user reads; not native ACL/network. SHA-256 `29f00d216c240fb297efbf34fbe38c34b54ebe8dd78d8c2bb6448e81a1345ec3`.
- **P** `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims` — native exposure; Legacy synthetic signer; decoded uid and login sub correspond to self or system-selected target; no baseline diff. SHA-256 `ededf965d404c3fe36ebd3a1b988a26752d6a84c1240842b310f108d6aefe4e8`.
- **Q** `amr_oidc/tests/unit/test_token_issuer_security.py::TokenIssuerSecurityTests::test_glue_preserves_legacy_missing_ttl_default_end_to_end` — unit mock/source-loaded; Fake absent parameter and source-loaded glue/helper: mock signer gets expires_in 86400; no refresh behavior. SHA-256 `7a1277fbc0d8499edb9b2cae16002fd7d93909ff05b0ae9d99e88fd79990101c`.
- **R** `amr_oidc/tests/unit/test_token_issuer_security.py::TokenIssuerSecurityTests::test_fresh_client_route_rejects_caller_subject_before_issuance` — unit mock/source-loaded; Fake controller rejects caller subject before issuance, checks sanitized response; not HTTP dispatch. SHA-256 `7a1277fbc0d8499edb9b2cae16002fd7d93909ff05b0ae9d99e88fd79990101c`.
- **S** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_required_claims_and_zero_leeway` — unit mock/source-loaded; Synthetic signed negatives for required claims and invalid time/type/client; no controlled exact expiration boundary. SHA-256 `29f00d216c240fb297efbf34fbe38c34b54ebe8dd78d8c2bb6448e81a1345ec3`.
- **T** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` — unit mock/source-loaded; Fake JWKS selection exercises empty/duplicate and invalid key properties; not independently configured real PEM/JWKS. SHA-256 `29f00d216c240fb297efbf34fbe38c34b54ebe8dd78d8c2bb6448e81a1345ec3`.

## Crosswalk kasus

### C01

> **Teks accepted persis (UAT.md):** Explicit fresh provenance, key absent: scoped issuance reads 900 seconds; Settings may display 900 but read/issue does not create key. Refresh helper retains its baseline missing-key result 86400; refresh creation remains source 14 days. Verify signed exp minus iat and response TTL equal 900.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. fresh explicit provenance + absent key read 900 — PARTIAL statis [A] — irisan saja; sisanya GAP/NOT ASSESSED.
2. Settings displays 900 without read/issue creating key — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. refresh missing-key reader 86400 — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. refresh creation stays 14 days — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
5. signed exp−iat and response TTL 900 — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.

### C02

> **Teks accepted persis (UAT.md):** Fresh profile explicitly save 60 then 86400 as authorized settings actor: scoped issuance uses exact values; shared refresh reader sees the stored same value, no claim its creation lifetime changed. UI discloses coupling before save; no other setting or silent write.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. authorized fresh Settings save 60 and 86400; issuance uses each exact value — PARTIAL statis [A] — irisan saja; sisanya GAP/NOT ASSESSED.
2. shared refresh reader sees each stored value without asserting creation lifetime change — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. UI discloses coupling before save — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. no other setting/silent write — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### C03

> **Teks accepted persis (UAT.md):** Existing and unknown provenance, separately stored absent, 3600, 86400, 59, malformed: no key write, no new-profile issuance and no conversion. Characterize legacy issuer/helper and refresh behavior against baseline fixture for each, including exceptions and `expires_in` falsy/override semantics; compare exact outcome, not assumed validity. Existing other token classes/claims unchanged except independently accepted #79 modifications.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. existing AND unknown provenance × absent/3600/86400/59/malformed: no write, fresh issuance or conversion — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. baseline-compare legacy issuer/helper and refresh each variant, exact exception and falsy/override outcome — PARTIAL statis [Q] — irisan saja; sisanya GAP/NOT ASSESSED.
3. other token classes/claims unchanged except accepted #79 modifications — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### C04

> **Teks accepted persis (UAT.md):** Fresh scope parameter tampered with empty, whitespace, signed, decimal, non-ASCII digits, zero, 59, 86401, huge or text: sanitized `UserError` for invalid configuration before signer and cached return; unauthorized actor receives `AccessError`; protocol boundary maps errors to its existing sanitized protocol error without secrets. Authorized settings write rejects invalid. Check 60/86400 controls. Ordinary actor cannot change setting through UI or direct RPC; privileged direct tamper cannot bypass issuance validation. Record effective ACLs.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. fresh tamper empty/whitespace/signed/decimal/non-ASCII/zero/59/86401/huge/text gives sanitized UserError before signer and warm cache — PARTIAL statis [A] — irisan saja; sisanya GAP/NOT ASSESSED.
2. unauthorized actor AccessError; protocol maps to existing sanitized error without secrets — PARTIAL statis [D] — irisan saja; sisanya GAP/NOT ASSESSED.
3. authorized Settings invalid write rejects; 60/86400 controls — PARTIAL statis [C] — irisan saja; sisanya GAP/NOT ASSESSED.
4. ordinary actor UI and direct RPC cannot change; privileged tamper cannot bypass issue validation; effective ACL readback — PARTIAL statis [D] — irisan saja; sisanya GAP/NOT ASSESSED.

### C05

> **Teks accepted persis (UAT.md):** Fresh scope override omitted, int 60, configured TTL pass; None, bool, 0, 59, >configured, 86401, float/string reject before signing. No restrictions imposed on legacy helper args by this delta.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. fresh override omission, integer 60, configured TTL succeed — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
2. explicit None/bool/0/59/>configured/86401/float/string reject before signer — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
3. no new restriction on legacy helper arguments — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### C06

> **Teks accepted persis (UAT.md):** Instrument signer and controlled clock; two scoped calls each revalidate auth/config and mint, no scoped cache return. After a worker observes config B its next issuance uses B; concurrent reads measured without inventing global propagation. Existing tokens retain signed exp and verifier rejects at configured boundary, subject to policy/trust. Required legacy cache cases still apply.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. controlled clock and signer: two fresh calls revalidate authorization/config and each mint; no scoped cache return — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
2. after each worker observes B next issuance uses B; measure concurrency without invented propagation — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. old signed exp retained; verifier rejects at boundary subject to policy/trust — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. required legacy cache cases apply — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### T01

> **Teks accepted persis (UAT.md):** Fixture fresh terverifikasi, key TTL tidak ada; jalankan issuance fresh yang terautentikasi melalui setiap entry point fresh yang diizinkan. Assert TTL 900, signed exp−iat dan metadata respons sama; Settings memakai satu key dan menampilkan detik tanpa menulis. Simpan 60 dan 86400 sebagai actor berwenang dan pastikan masing-masing dipakai. Jangan menerapkan TTL fresh pada jalur legacy glue; karakterisasi jalur itu secara terpisah.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. verified fresh missing TTL: each allowed authenticated fresh entry point TTL 900, signed exp−iat and response metadata agree — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
2. Settings single key, seconds displayed, no write — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. authorized save 60 and 86400, each used — PARTIAL statis [A] — irisan saja; sisanya GAP/NOT ASSESSED.
4. legacy glue not assigned fresh TTL; characterize separately — PARTIAL statis [Q] hanya fake missing-key signer 86400, bukan bukti fresh TTL tidak diterapkan atau perbandingan baseline; sisanya GAP/NOT ASSESSED.

### T02

> **Teks accepted persis (UAT.md):** Known existing DB fixture with stored 3600 then 86400: before any separately approved migration prove no overwrite/reinterpretation, including refreshing Settings. With approved rollout verify exact value preserved. Existing missing or unknown deployment provenance must not default to 900 or silently write it; new contract issuance blocks pending explicit migration choice.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. existing DB stored 3600 then 86400: before approved migration no overwrite/reinterpretation including Settings refresh — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. approved rollout preserves exact value — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. existing missing or unknown provenance: no 900 default or silent write, block fresh issuance until migration choice — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### T03

> **Teks accepted persis (UAT.md):** Fresh profile: Settings writes and direct parameter tampering with empty, spaces, ` 60`, `60 `, `+60`, `-1`, `0`, `59`, `86401`, `60.0`, non-ASCII digits, text, huge integer: UI rejects save; config-read/issuance returns sanitized configuration error before signer and before any warm cache return; no fallback/clamp. Integer endpoints 60/86400 remain positive controls.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. fresh Settings and direct tamper: empty/spaces/leading or trailing spaces/+60/−1/0/59/86401/60.0/non-ASCII/text/huge all reject UI save — PARTIAL statis [C] — irisan saja; sisanya GAP/NOT ASSESSED.
2. config read/issuance sanitized error before signer and warm cache; no fallback/clamp — PARTIAL statis [A] — irisan saja; sisanya GAP/NOT ASSESSED.
3. integer endpoints 60 and 86400 positive controls — PARTIAL statis [A] — irisan saja; sisanya GAP/NOT ASSESSED.

### T04

> **Teks accepted persis (UAT.md):** Fixture fresh dengan TTL valid dan signer/cache spy: uji omission, integer 60 dan TTL efektif sebagai kontrol positif; uji None eksplisit, bool, nol, negatif, pecahan, string, kurang dari 60, melebihi 86400 atau TTL efektif. Setiap input invalid ditolak sebelum signer/cache pada semua entry point fresh berwenang termasuk RPC bypass. Jangan menerapkan pembatasan baru pada API/helper legacy; perubahan kontrak legacy memerlukan persetujuan kompatibilitas terpisah.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. fresh valid TTL: omission, integer 60 and effective TTL positive — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
2. explicit None/bool/zero/negative/fraction/string/<60/>86400/>effective denied before signer/cache on every authorized entry including RPC bypass — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
3. legacy API/helper not newly restricted; compatibility approval needed for change — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### T05

> **Teks accepted persis (UAT.md):** Controlled clock, prior valid token and cache: sign with configured A, change to B, reissue after each worker observes change; signed exp and returned metadata reflect effective B and no token from A is returned. Previously signed token keeps exp but may fail policy/trust; at/after exp verifier rejects with source baseline leeway=0. Warm cache cannot return expired token or bypass auth/config checks; test DB, audience, actor, key and policy isolation and concurrent changes. Record real propagation; no promised instantaneous cross-worker effect.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. controlled clock A→B after each worker observes: signed exp and metadata B, no A token returned — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. prior token exp retained; policy/trust may deny; at/after exp rejected with baseline leeway zero — PARTIAL statis [S] — irisan saja; sisanya GAP/NOT ASSESSED.
3. warm cache cannot return expired or bypass auth/config — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. DB/audience/actor/key/policy isolation, concurrent changes and measured propagation without instantaneous promise — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### T06

> **Teks accepted persis (UAT.md):** Inventory shared-key readers/extensions, preserve refresh helper behavior and 14-day source issuance implementation; in separately approved migration fixture verify old values, fresh/missing and rollback and record observed effects on refresh reader, without changing refresh feature. If a key change would affect a refresh consumer and no compatible plan is approved, rollout is BLOCKED, not PASS.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. inventory shared-key readers/extensions, preserve refresh helper and 14-day source issuance — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. separately approved migration: old values, fresh/missing, rollback and observed refresh effects — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. consumer impact without compatible approved plan blocks rollout — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### M01

> **Teks accepted persis (UAT.md):** Approved fresh mapping, same issuer and user two issuances and after login/email rename: same exact 64 lowercase-hex opaque subject, no uid/login/db claims; different user differs. No caller-selected subject accepted; inspect actual payload only in secured synthetic fixture.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. approved issuer/user two issuances then login/email rename: identical lowercase 64-hex opaque sub — PARTIAL statis [I] — irisan saja; sisanya GAP/NOT ASSESSED.
2. distinct user yields different subject — PARTIAL statis [I] — irisan saja; sisanya GAP/NOT ASSESSED.
3. signed payload excludes uid/login/db claims — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
4. caller-selected subject rejected; synthetic payload secured — PARTIAL statis [R] — irisan saja; sisanya GAP/NOT ASSESSED.

### M02

> **Teks accepted persis (UAT.md):** Verify generation uses Python standard-library `secrets` for 32 bytes, Odoo SQL uniqueness constraints and no raw SQL. Concurrent first issuance for same pair yields exactly one persisted row/same subject; observe savepoint handling and exact `(namespace, principal)` reread after integrity conflict. Independently force deterministic subject collision in isolated test seam: retry then success; repeated collision beyond three attempts denies, no partial issuance. DB rejects duplicate namespace/principal and namespace/sub including archived rows.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. Python secrets 32-byte generation, Odoo SQL uniqueness declarations, no raw SQL — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. concurrent first same pair: one persistent row and same subject; observe savepoint and exact namespace/principal reread following conflict — PARTIAL statis [F] — irisan saja; sisanya GAP/NOT ASSESSED.
3. deterministic subject collision retry succeeds — PARTIAL statis [E] — irisan saja; sisanya GAP/NOT ASSESSED.
4. repeated collision > three attempts denied, no partial issuance — PARTIAL statis [G] — irisan saja; sisanya GAP/NOT ASSESSED.
5. DB rejects duplicate namespace/principal and namespace/sub incl archived — PARTIAL statis [H] — irisan saja; sisanya GAP/NOT ASSESSED.

### M03

> **Teks accepted persis (UAT.md):** Attempt write/reassignment, reparent, namespace/subject edit, unlink and deletion of referenced user, including privileged model RPC; reject, retain reservation. Archived mapping cannot issue and cannot be reused. Missing/ambiguous namespace and inactive/deleted principal fail before signing.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. privileged model RPC write/reassign/reparent/namespace/subject edits/unlink denied; reservation retained — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. deleting referenced user denied — PARTIAL statis [J] — irisan saja; sisanya GAP/NOT ASSESSED.
3. archived mapping cannot issue or be reused — PARTIAL statis [H] — irisan saja; sisanya GAP/NOT ASSESSED.
4. missing/ambiguous namespace and inactive/deleted principal fail before signing — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### M04

> **Teks accepted persis (UAT.md):** Different explicitly configured fresh DB/issuer namespaces isolate mappings; cloned/restored DB, missing/changed namespace or reused namespace absent separate authorized lifecycle plan: scoped issuance blocked; no rewriting identity. Treat cross-instance uniqueness as operational evidence, not inferred from DB constraint.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. separately configured fresh DB/issuer namespaces isolate mappings — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. clone/restore, missing/changed/reused namespace without approved lifecycle block issuance without rewrite — PARTIAL statis [L] — irisan saja; sisanya GAP/NOT ASSESSED.
3. cross-instance uniqueness demonstrated operationally not inferred from DB constraint — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### M05

> **Teks accepted persis (UAT.md):** Public, portal, regular internal, system administrator, trust administrator, legitimate issuance service: attempt mapping read/search/create/write/unlink and exposed RPC, plus forged context/sudo kwargs. Only private service path after actor/client authorization can read/create; no human bypass of immutability. Prove actual ACL/record-rule and sudo boundaries with installed registry, not view inspection.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. public/portal/internal/system/trust admin/service each attempt read/search/create/write/unlink and exposed RPC including forged context/sudo kwargs — PARTIAL statis [K] — irisan saja; sisanya GAP/NOT ASSESSED.
2. only private service path after actor/client authorization reads/creates; no human immutability bypass — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. installed registry proves actual ACL/record rules/sudo boundaries not view-only — PARTIAL statis [K] — irisan saja; sisanya GAP/NOT ASSESSED.

### M06

> **Teks accepted persis (UAT.md):** Valid authenticated active registered client A issues; signed client_id A; correct explicitly bound issuer/user/audience RS trust verifies. Missing/forged auth provenance, request kwargs client B, inactive/unknown/ambiguous client, mismatch issuer/audience, unauthorized user or direct glue without authenticated client all fail before signer; unrelated legacy path unchanged.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. authenticated active registered A issues signed client_id A; explicit issuer/user/audience RS trust verifies — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
2. missing/forged auth provenance, client B kwargs, inactive/unknown/ambiguous client, issuer/audience mismatch, unauthorized user, direct glue without auth all fail before signer — PARTIAL statis [M] — irisan saja; sisanya GAP/NOT ASSESSED.
3. unrelated legacy path unchanged — GAP/NOT ASSESSED — [P] hanya claims synthetic self/system, bukan perbandingan baseline.

### M07

> **Teks accepted persis (UAT.md):** Tamper each signed header, payload, signature; wrong algorithm/type/key/kid, untrusted/expired key, missing/wrong iss/aud/iat/exp/jti/client/azp, expiration, invalid policy and provenance: RS rejects without fallback. Include valid cryptographic positive control and independently configured local PEM vs JWKS key selection; never weaken existing verifier.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. tamper signed header/payload/signature and wrong algorithm/type/key/kid, untrusted/expired key reject without fallback — PARTIAL statis [N] — irisan saja; sisanya GAP/NOT ASSESSED.
2. missing/wrong iss/aud/iat/exp/jti/client/azp, expiration, invalid policy/provenance reject no fallback — PARTIAL statis [S] — irisan saja; sisanya GAP/NOT ASSESSED.
3. valid cryptographic control and independently configured local PEM vs JWKS selection; verifier not weakened — PARTIAL statis [T] — irisan saja; sisanya GAP/NOT ASSESSED.

### M08

> **Teks accepted persis (UAT.md):** Explicit RS binding maps verified issuer/sub to intended eligible user: pass. Missing, wrong-user, inactive, ambiguous or forged/unverified subject: deny, no email/login fallback, automatic binding or rewrite; malicious RPC cannot create binding absent existing trust-admin privilege. Assert no self-provider HTTP on success/classification/key/error paths; remote parity retained.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. explicit RS verified issuer/sub binding resolves intended eligible user — PARTIAL statis [O] — irisan saja; sisanya GAP/NOT ASSESSED.
2. missing/wrong-user/inactive/ambiguous/forged/unverified deny without email/login fallback, autobinding or rewrite — PARTIAL statis [O] — irisan saja; sisanya GAP/NOT ASSESSED.
3. malicious RPC cannot create binding without existing trust-admin privilege — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. zero self-provider HTTP across success/classification/key/error with calibrated full observer; remote parity — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### M09

> **Teks accepted persis (UAT.md):** Legacy login-sub tokens and RS bindings in existing fixture: no conversion, alias or new dual acceptance, legacy profile remains unchanged where not explicitly changed by accepted #79. No claim other feature acceptance; sibling owners review captured contract evidence.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. existing legacy login-sub tokens and RS bindings: no conversion/alias/new dual acceptance — GAP/NOT ASSESSED — [P] tidak membuktikan binding atau tidak adanya konversi.
2. legacy profile unchanged except explicitly accepted #79 changes — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
3. no sibling acceptance inferred; sibling owners review captured contract — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### I01

> **Teks accepted persis (UAT.md):** Approved issuer mapping fixture: issue twice for one principal/issuer/database, then rename login/email and reissue; exact same nonempty opaque sub; two principals under same issuer differ. No subject equals login/email or exposed raw DB id; verify scoped profile omits uid/login/db identifying claims. Keep evidence synthetic.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. approved mapping, same principal/issuer/database twice then login/email rename: exact same nonempty opaque sub — PARTIAL statis [I] — irisan saja; sisanya GAP/NOT ASSESSED.
2. two principals differ — PARTIAL statis [I] — irisan saja; sisanya GAP/NOT ASSESSED.
3. sub differs from login/email/raw DB id; signed profile omits uid/login/db claims — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
4. synthetic-only evidence — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### I02

> **Teks accepted persis (UAT.md):** Simultaneous issuance for same `(issuer_namespace, principal)` yields one persistent mapping and same sub; attempt second mapping for same pair rejected by DB uniqueness. Same issuer + same sub mapped to another principal is rejected by DB uniqueness; different issuer/DB isolation verified with separately established namespaces. Unknown/ambiguous/reassigned/deleted identity rejects; no silent mapping reuse. Test clone/issuer changes only with separately approved lifecycle.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. simultaneous same issuer_namespace/principal issuance one persistent mapping and same sub — PARTIAL statis [F] — irisan saja; sisanya GAP/NOT ASSESSED.
2. DB rejects duplicate pair and duplicate issuer/sub across principals — PARTIAL statis [H] — irisan saja; sisanya GAP/NOT ASSESSED.
3. separately established issuer/DB namespaces isolate — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. unknown/ambiguous/reassigned/deleted identity rejects without reuse — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
5. clone/issuer changes tested only with separately approved lifecycle — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

### I03

> **Teks accepted persis (UAT.md):** With authenticated active registered client A issue scoped token: signed client_id exactly A's record, RS validates under matching profile. Forged claim or kw client_id B, audience substitution, missing auth, inactive/unknown client, auth for B presented as A, and ambiguous mapping all reject before signing; direct glue/helper without authenticated client cannot issue this RS profile. Independent legacy non-RS operation is assessed separately.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. authenticated active registered A issuance signed client_id equals A record and matching RS verifies — PARTIAL statis [B] — irisan saja; sisanya GAP/NOT ASSESSED.
2. forged claim or B kw, audience substitution, missing auth, inactive/unknown client, B auth as A and ambiguous mapping reject before signer — PARTIAL statis [M] — irisan saja; sisanya GAP/NOT ASSESSED.
3. direct glue/helper without authenticated client cannot issue RS profile — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. legacy non-RS separately assessed — PARTIAL statis [P] — irisan saja; sisanya GAP/NOT ASSESSED.

### I04

> **Teks accepted persis (UAT.md):** Existing login-sub token, legacy client and RS subject binding fixtures: inventory affected accepted consumers; no automatic rewrite, alias, replacement or altered claims outside approved profile. If no Owner/sibling-approved compatibility and issuer-model scope, mark positive issuance blocked. Baseline RS-side `(issuer, sub)` binding alone must not be asserted as issuer-side `(issuer, principal)` uniqueness.

Fixture/actor: prasyarat bersama di atas ditambah varian eksplisit berikut; semua actual NOT RUN.

1. inventory affected accepted consumers of existing login-sub token, legacy client and RS binding fixtures — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
2. no automatic rewrite/alias/replacement or outside-profile claim change — GAP/NOT ASSESSED — [P] tidak membuktikan hasil tersebut.
3. without Owner/sibling-approved compatibility and issuer-model scope positive issuance blocked — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.
4. RS (issuer, sub) binding not claimed to prove issuer (issuer, principal) uniqueness — GAP/NOT ASSESSED — belum dipetakan ke assertion memadai.

## Rekonsiliasi dan batas

- IDs diperiksa: 25 = C01–C06 (6), T01–T06 (6), M01–M09 (9), I01–I04 (4); tepat: C01, C02, C03, C04, C05, C06, T01, T02, T03, T04, T05, T06, M01, M02, M03, M04, M05, M06, M07, M08, M09, I01, I02, I03, I04.
- Unit pemeriksaan: 92; 48 hanya punya irisan kandidat, 44 GAP/NOT ASSESSED tanpa rujukan; **seluruh 92 unit masih memiliki gap**, karena rujukan bukan pemetaan penuh. Jumlah ini menghitung unit di dokumen, bukan jumlah varian atau tes.
- Seluruh 25 kasus masih mempunyai atom GAP/NOT ASSESSED: C01, C02, C03, C04, C05, C06, T01, T02, T03, T04, T05, T06, M01, M02, M03, M04, M05, M06, M07, M08, M09, I01, I02, I03, I04. Tidak ada kasus full-case assessed/completed; kategori ini tidak bermakna tidak ada kode tes lainnya.
- Gap utama: issuance sebenarnya end-to-end/RS dan kredensial; seluruh varian fresh vs legacy baseline dan refresh/migrasi/UI; signer/cache/expiry/worker/DB concurrency; ACL nyata, RPC dispatch dan aktor lengkap; constraint/rollback/collision DB; lifecycle clone/issuer; verifier matrix/local PEM/JWKS; binding dan calibrated socket/HTTP network observer; review sibling/owner dan operational cross-instance evidence. Lihat tiap butir untuk rincian, termasuk kontrol dan actor.
- Katalog merupakan pembacaan assertion source dan AST verifikasi identitas metode; native discovery tetap NOT ASSESSED/NOT RUN, unit collection NOT RUN. Unit mock tidak membuktikan registry, ORM, transaksi, ACL, RPC, network atau signed end-to-end. Tidak ada container/build/pull, DB atau test dijalankan.
- Reproduksi count: baca header `### C01`… pada UAT dan butir bernomor di seksi kasus; hitung dengan parser Markdown, bukan nama metode. Pengelompokan satu butir dengan matriks tidak berarti satu varian dapat menggantikan yang lain.


## Lampiran — rekonsiliasi diagnostik Gen5 (bukan rebind UAT)

Basis accepted tetap `docs/ADDONS13-79/UAT.md`, SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e` (hash dihitung ulang pada path itu). Baris kasus historis di atas tetap menjadi inventaris sub-oracle dan variant; lampiran ini hanya mengubah pembacaan bukti untuk irisan yang disebut, bukan menghapus gap. Gen5 ialah diagnostik clean-tree commit `49b5a739ce25b8feeb74b8d7c91641e2c98c5978`, bukan HEAD `5f1f0f9` yang disebut saat delegasi; tidak ada rebind candidate/runtime/authorization. SCOPE-01 tetap OPEN; positive fresh issuance terkait tetap BLOCKED. Semua 25 full case **NOT ESTABLISHED**, UAT penuh bukan PASS.

### Provenance dan batas hasil

`safe-summary.json` scratch sementara SHA-256 `50c8f26e3082b6c3c5a3d6141e7e296cb856e801248a4f9b84a22a4223b0791d`. Hash runner dihitung ulang dari masing-masing path yang tercatat di summary dan cocok; controller juga diperiksa. Urutan berikut resource / oidc_resource / oidc: selector exit 0, start unik dan total ringkasan modul 28 / 18 / 44; semua nama dalam summary ditemukan pada log runner, tanpa failure test yang teridentifikasi. Ini rekonsiliasi selector dan daftar failure, bukan individual per-test result eksplisit; status irisan disebut **executed diagnostic** berdasarkan start, hitungan, ringkasan dan exit, bukan PASS acceptance. SQL ERROR pada log mentah masing-masing 3 / 0 / 6, sehingga exit 0 bukan bukti raw-log bersih. Proxy-mode mensimulasikan header proxy saja, bukan TLS riil; tidak ada bukti calibrated zero-egress. Scratch dapat terhapus, hash bukan substitusi arsip bukti yang tahan lama.

| Selector | SHA-256 runner log terbatas | SHA-256 controller log |
|---|---|---|
| amr_resource | `5b836a4210aa71165d9323e52eb60ac6298f5d4fa1ea65c41ff46ff64fb73185` | `e02206022df4b3513e32c2b82dd2ceb085376cbae6d667383ca5ba17cc597628` |
| amr_oidc_resource | `d3d8a093dd1f4b43ed812e57c6533acdded185be1e43a23a67c6047c7ec4a312` | `661b9ef32031fa86f80054b42a645b0727612eab2275df1e7cedeb6385704430` |
| amr_oidc | `fe5ab1919312979b9df7ce468bb531ef5cfa3aae601ab22cb25a5bdc54c19b5d` | `1553ac8399ac9f1176038093afaec8076681252320f2a29fcf87a884c121f727` |

### Kunci source dan batas assertion

Semua referensi baris berikut berasal dari `git show 49b5a739ce25b8feeb74b8d7c91641e2c98c5978:<path>`, bukan nomor baris worktree berjalan. Katalog A–T di atas memberikan path, class dan nama metode lengkap; source assertion line untuk rujukan statis adalah A:306,310,314; B:396,398–423,429,432,434,436,438; C:283; D:236; E:105–108; F:126–131; G:143,147–150; L:325,327,334,337,339,344,346,348; M:462,464–465; N:305–311; O:590,595; Q:253–254; R:521–527; S:350; T:372. Ini **static unit only**, tidak ada bukti unit tersebut dijalankan pada Gen5; rentang mencakup assertion yang relevan, bukan berarti setiap baris dalam rentang assertion.

Bukti **executed diagnostic** berikut cocok tepat dengan daftar metode Gen5, sumber dan log:

- **H** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_archived_subject_keeps_both_unique_reservations_and_denies_issuance`, assertion 64–75: arsip, penolakan pemanggilan mapper dan dua constraint DB dalam savepoint; bukan end-to-end signer.
- **I** path sama, `TestFreshIssuerSubjectIdentity::test_subject_is_stable_across_user_rename_and_distinct_per_user`, assertion 103–104,111–112,120–122: mapper ORM stable setelah rename dan distinct user; bukan dua issuance signed.
- **J** path sama, `TestFreshIssuerPrincipalSubject::test_user_deletion_is_restricted_by_subject_foreign_key`, assertion 85–86: penghapusan user ditolak.
- **K** path sama, `TestFreshIssuerPrincipalSubject::test_every_human_role_has_no_mapping_acl`, assertion 27–39: tiga role tertentu, read ACL/search/create, bukan seluruh aktor/operasi.
- **U** path sama, `TestFreshIssuerPrincipalSubject::test_sudo_rpc_cannot_create_or_mutate_a_subject`, assertion 41–53: direct sudo model dan forged context create/write/unlink; nama metode bukan bukti dispatch RPC, write/unlink pada recordset kosong bukan bukti retensi mapping spesifik.
- **P** `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims`, assertion 37–52: decoded legacy synthetic self/system target uid/sub; bukan perbandingan baseline atau bukti tanpa konversi.
- **V** path sama/class sama `test_legacy_cache_reuses_within_ttl_bucket_and_rolls_over`, assertion 73–93: legacy fixed-clock reuse dan rollover signer; bukan fresh.
- **W** path sama/class sama `test_signing_configuration_change_uses_new_key_and_ttl`, assertion 112–126: legacy key/TTL berubah, exp dan key baru diperiksa; bukan fresh multiworker.
- **X** `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures`, assertion 430–463,476–503: RS256 local, mandatory claims terpilih dan JWKS melalui fetch mock, termasuk leeway argument nol; bukan seluruh matrix maupun exact-exp clock.
- **Y** path sama/class sama `test_ut07_matching`, assertion 511–536,544–547: verified fixture binding, missing/unverified dan inactive ditolak; bukan real end-to-end provenance maupun full network observer.

### Rekonsiliasi per kasus

Kolom kedua menyatakan hanya irisan yang benar-benar ditemukan; **static** merujuk katalog unit di atas, bukan eksekusi. `NOT ASSESSED` berarti belum dipastikan oleh telaah ini, bukan klaim bahwa tes tidak ada. Setiap baris mempertahankan status **full case NOT ESTABLISHED** dan seluruh persyaratan pada teks accepted di atas.

| Kasus | Gen5 executed diagnostic / static unit | Residual variant atau oracle NOT ASSESSED / NOT RUN |
|---|---|---|
| C01 | Static A, B; tidak ada irisan Gen5 dipastikan | Settings/no write, refresh 86400/14 hari dan signed real TTL. |
| C02 | Static A; tidak ada irisan Gen5 dipastikan | Kedua save berwenang, refresh reader, disclosure UI, no silent write. |
| C03 | Executed P legacy claims; static Q | Seluruh provenance × nilai, baseline exact/falsy, no conversion/write. |
| C04 | Static A,C,D; tidak ada irisan Gen5 dipastikan | Matriks tamper, sanitized protocol, warm cache, actual UI/RPC/ACL. |
| C05 | Static B; tidak ada irisan Gen5 dipastikan | Semua override sebelum signer/cache, legacy compatibility. |
| C06 | Executed V legacy cache dan W legacy key/TTL; static B | Fresh revalidation/mint, worker propagation, signed expiry dan isolasi. |
| T01 | Executed P legacy claims; static A,B,Q | Semua fresh entrypoints signed TTL, Settings save/read/no write, legacy baseline. |
| T02 | Tidak ada irisan Gen5 dipastikan | Stored existing 3600/86400, Settings refresh, approved rollout dan unknown provenance. |
| T03 | Static A,C; tidak ada irisan Gen5 dipastikan | Semua invalid UI/tamper, sanitized error sebelum warm cache dan endpoints riil. |
| T04 | Static B; tidak ada irisan Gen5 dipastikan | Matriks override semua entrypoint/RPC, signer/cache dan legacy compatibility. |
| T05 | Executed V,W legacy saja; X leeway argument nol; static S | Fresh A→B tiap worker, prior token exact expiry, cache/auth/isolation/concurrency. |
| T06 | Tidak ada irisan Gen5 dipastikan | Inventory shared readers, refresh 14-day, migration/rollback dan rollout decision. |
| M01 | Executed I mapper; static B,R | Issuance signed dua kali/rename, payload privacy, caller subject pada HTTP nyata. |
| M02 | Executed H archived dual uniqueness; static E,F,G | Secrets source/no raw SQL, concurrent issuance/reread, real collisions/rollback, active variants. |
| M03 | Executed H,J,U direct model | Privileged RPC dispatch, mutation pada mapping aktual/retensi, semua principal dan signer negatives. |
| M04 | Static L; tidak ada irisan Gen5 dipastikan | Dua DB/issuer, real clone/restore, namespace reuse dan operational uniqueness. |
| M05 | Executed K,U; static M | Public/trust/service lengkap, record rules, forged RPC dispatch dan private authorization boundary. |
| M06 | Executed P legacy claims; static B,M | Authenticated client A ke signed RS, semua forged/inactive/unknown/ambiguous variants, baseline legacy. |
| M07 | Executed X subset RS local/JWKS mock; static N,S,T | Tamper header/payload/signature matrix, key/claim/policy/provenance lengkap, independent real JWKS, no fallback. |
| M08 | Executed Y fixture binding; static O | Wrong-user/ambiguity/rewrite, actual privilege RPC, calibrated zero self-provider egress, remote parity. |
| M09 | Executed P legacy claims | Existing baseline binding, no conversion/alias/dual acceptance dan sibling review. |
| I01 | Executed I mapper; static B | Approved signed issuance, payload identifying claims dan semua identity comparison. |
| I02 | Executed H archived dual uniqueness; static F | Simultaneous issuance, active variants, separate DB/issuer, lifecycle/identity cases. |
| I03 | Executed P legacy claims; static B,M | Signed authenticated A plus RS, seluruh forgery/auth/mapping negatives, direct glue boundary. |
| I04 | Executed P legacy claims | Inventory consumers, baseline no rewrite/alias, approved compatibility/scope dan issuer-side uniqueness terpisah. |

Hitungan: 25 baris rekonsiliasi unik (C 6, T 6, M 9, I 4); tidak satu pun full case established. Klasifikasi ini tidak mengklaim seluruh 90 metode dipetakan atau seluruh atom telah dibuktikan.

### Matriks bukti per atom Gen5 — overlay aditif

ID `<kasus>.<nomor dua digit>` menunjuk tepat butir bernomor historis tanpa mengubahnya. Status: **EXECUTED DIAGNOSTIC PARTIAL** hanya irisan assertion native yang dimulai dan direkonsiliasi dalam Gen5; **STATIC UNIT** assertion fake/unit yang tidak dibuktikan berjalan; **NOT ASSESSED** tidak ditemukan irisan yang layak untuk atom ini. Semua residual dan setiap varian dalam butir tetap perlu pemeriksaan: matriks varian dalam teks UAT **belum diekspansi/diperiksa satu per satu**, dan tidak dapat disimpulkan hijau. Kunci di bawah mencantumkan assertion aktif pada blob commit; lihat deskripsi batas per kunci di lampiran sebelumnya. Bukti diagnostik bukan PASS UAT; no rebind; SCOPE-01 OPEN.

| Atom | Status dan irisan bukti | Residual spesifik yang belum dibuktikan |
|---|---|---|
| C01.01 | STATIC UNIT [A] | Belum terbukti sebagai oracle penuh: fresh explicit provenance + absent key read 900; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C01.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: Settings displays 900 without read/issue creating key; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C01.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: refresh missing-key reader 86400; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C01.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: refresh creation stays 14 days; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C01.05 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: signed exp−iat and response TTL 900; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C02.01 | STATIC UNIT [A] | Belum terbukti sebagai oracle penuh: authorized fresh Settings save 60 and 86400; issuance uses each exact value; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C02.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: shared refresh reader sees each stored value without asserting creation lifetime change; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C02.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: UI discloses coupling before save; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C02.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: no other setting/silent write; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C03.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: existing AND unknown provenance × absent/3600/86400/59/malformed: no write, fresh issuance or conversion; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C03.02 | STATIC UNIT [Q] | Belum terbukti sebagai oracle penuh: baseline-compare legacy issuer/helper and refresh each variant, exact exception and falsy/override outcome; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C03.03 | NOT ASSESSED | Perbandingan baseline other token classes/claims belum dibuktikan; syarat unchanged mengecualikan perubahan #79 yang secara independen diterima, bukan mengasumsikan semua perubahan diterima. |
| C04.01 | STATIC UNIT [A] | Belum terbukti sebagai oracle penuh: fresh tamper empty/whitespace/signed/decimal/non-ASCII/zero/59/86401/huge/text gives sanitized UserError before signer and warm cache; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C04.02 | STATIC UNIT [D] | Belum terbukti sebagai oracle penuh: unauthorized actor AccessError; protocol maps to existing sanitized error without secrets; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C04.03 | STATIC UNIT [C] | Belum terbukti sebagai oracle penuh: authorized Settings invalid write rejects; 60/86400 controls; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C04.04 | STATIC UNIT [D] | Belum terbukti sebagai oracle penuh: ordinary actor UI and direct RPC cannot change; privileged tamper cannot bypass issue validation; effective ACL readback; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C05.01 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: fresh override omission, integer 60, configured TTL succeed; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C05.02 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: explicit None/bool/0/59/>configured/86401/float/string reject before signer; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C05.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: no new restriction on legacy helper arguments; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C06.01 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: controlled clock and signer: two fresh calls revalidate authorization/config and each mint; no scoped cache return; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C06.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: after each worker observes B next issuance uses B; measure concurrency without invented propagation; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C06.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: old signed exp retained; verifier rejects at boundary subject to policy/trust; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| C06.04 | EXECUTED DIAGNOSTIC PARTIAL [V,W] | V/W hanya contoh reuse/rollover dan perubahan key/TTL legacy; pemetaan seluruh required legacy cache cases belum lengkap, tanpa mengasumsikan hasil kasus lain. |
| T01.01 | STATIC UNIT [B] | Fake helper bukan inventaris lengkap entry point fresh yang diizinkan atau bukti masing-masing melalui signing nyata; TTL dan metadata tiap entry point belum dibuktikan. |
| T01.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: Settings single key, seconds displayed, no write; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T01.03 | STATIC UNIT [A] | Belum terbukti sebagai oracle penuh: authorized save 60 and 86400, each used; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T01.04 | STATIC UNIT [Q]; diagnostic [P] hanya konteks claims | Q hanya fake missing-key signer 86400; P hanya decoded synthetic legacy self/system claims. Keduanya tidak membuktikan fresh TTL tidak diterapkan atau kesetaraan baseline; karakterisasi legacy tetap belum lengkap. |
| T02.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: existing DB stored 3600 then 86400: before approved migration no overwrite/reinterpretation including Settings refresh; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T02.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: approved rollout preserves exact value; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T02.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: existing missing or unknown provenance: no 900 default or silent write, block fresh issuance until migration choice; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T03.01 | STATIC UNIT [C] | Belum terbukti sebagai oracle penuh: fresh Settings and direct tamper: empty/spaces/leading or trailing spaces/+60/−1/0/59/86401/60.0/non-ASCII/text/huge all reject UI save; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T03.02 | STATIC UNIT [A] | Belum terbukti sebagai oracle penuh: config read/issuance sanitized error before signer and warm cache; no fallback/clamp; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T03.03 | STATIC UNIT [A] | Belum terbukti sebagai oracle penuh: integer endpoints 60 and 86400 positive controls; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T04.01 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: fresh valid TTL: omission, integer 60 and effective TTL positive; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T04.02 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: explicit None/bool/zero/negative/fraction/string/<60/>86400/>effective denied before signer/cache on every authorized entry including RPC bypass; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T04.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: legacy API/helper not newly restricted; compatibility approval needed for change; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T05.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: controlled clock A→B after each worker observes: signed exp and metadata B, no A token returned; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T05.02 | EXECUTED DIAGNOSTIC PARTIAL [X]; STATIC UNIT [S] | Belum terbukti sebagai oracle penuh: prior token exp retained; policy/trust may deny; at/after exp rejected with baseline leeway zero; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T05.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: warm cache cannot return expired or bypass auth/config; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T05.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: DB/audience/actor/key/policy isolation, concurrent changes and measured propagation without instantaneous promise; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T06.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: inventory shared-key readers/extensions, preserve refresh helper and 14-day source issuance; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T06.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: separately approved migration: old values, fresh/missing, rollback and observed refresh effects; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| T06.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: consumer impact without compatible approved plan blocks rollout; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M01.01 | EXECUTED DIAGNOSTIC PARTIAL [I] | Belum terbukti sebagai oracle penuh: approved issuer/user two issuances then login/email rename: identical lowercase 64-hex opaque sub; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M01.02 | EXECUTED DIAGNOSTIC PARTIAL [I] | Belum terbukti sebagai oracle penuh: distinct user yields different subject; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M01.03 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: signed payload excludes uid/login/db claims; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M01.04 | STATIC UNIT [R] | Belum terbukti sebagai oracle penuh: caller-selected subject rejected; synthetic payload secured; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M02.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: Python secrets 32-byte generation, Odoo SQL uniqueness declarations, no raw SQL; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M02.02 | STATIC UNIT [F] | Belum terbukti sebagai oracle penuh: concurrent first same pair: one persistent row and same subject; observe savepoint and exact namespace/principal reread following conflict; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M02.03 | STATIC UNIT [E] | Belum terbukti sebagai oracle penuh: deterministic subject collision retry succeeds; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M02.04 | STATIC UNIT [G] | Belum terbukti sebagai oracle penuh: repeated collision > three attempts denied, no partial issuance; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M02.05 | EXECUTED DIAGNOSTIC PARTIAL [H] | Belum terbukti sebagai oracle penuh: DB rejects duplicate namespace/principal and namespace/sub incl archived; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M03.01 | EXECUTED DIAGNOSTIC PARTIAL [U] | Belum terbukti sebagai oracle penuh: privileged model RPC write/reassign/reparent/namespace/subject edits/unlink denied; reservation retained; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M03.02 | EXECUTED DIAGNOSTIC PARTIAL [J] | Belum terbukti sebagai oracle penuh: deleting referenced user denied; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M03.03 | EXECUTED DIAGNOSTIC PARTIAL [H] | Belum terbukti sebagai oracle penuh: archived mapping cannot issue or be reused; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M03.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: missing/ambiguous namespace and inactive/deleted principal fail before signing; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M04.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: separately configured fresh DB/issuer namespaces isolate mappings; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M04.02 | STATIC UNIT [L] | Belum terbukti sebagai oracle penuh: clone/restore, missing/changed/reused namespace without approved lifecycle block issuance without rewrite; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M04.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: cross-instance uniqueness demonstrated operationally not inferred from DB constraint; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M05.01 | EXECUTED DIAGNOSTIC PARTIAL [K,U] | K hanya tiga role untuk read ACL/search/create; U direct sudo/context dengan recordset kosong untuk write/unlink. Hasil setiap kombinasi actor × operation, RPC dan forged kwargs lainnya belum dipetakan; jangan menebak hasilnya. |
| M05.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: only private service path after actor/client authorization reads/creates; no human immutability bypass; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M05.03 | EXECUTED DIAGNOSTIC PARTIAL [K] | Belum terbukti sebagai oracle penuh: installed registry proves actual ACL/record rules/sudo boundaries not view-only; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M06.01 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: authenticated active registered A issues signed client_id A; explicit issuer/user/audience RS trust verifies; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M06.02 | STATIC UNIT [M] | Belum terbukti sebagai oracle penuh: missing/forged auth provenance, client B kwargs, inactive/unknown/ambiguous client, issuer/audience mismatch, unauthorized user, direct glue without auth all fail before signer; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M06.03 | NOT ASSESSED | [P] hanya decoded synthetic legacy self/system claims, bukan perbandingan baseline; unchanged untuk jalur unrelated selain perubahan #79 yang diterima belum dibuktikan. |
| M07.01 | EXECUTED DIAGNOSTIC PARTIAL [X]; STATIC UNIT [N] | Belum terbukti sebagai oracle penuh: tamper signed header/payload/signature and wrong algorithm/type/key/kid, untrusted/expired key reject without fallback; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M07.02 | EXECUTED DIAGNOSTIC PARTIAL [X]; STATIC UNIT [S] | Belum terbukti sebagai oracle penuh: missing/wrong iss/aud/iat/exp/jti/client/azp, expiration, invalid policy/provenance reject no fallback; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M07.03 | EXECUTED DIAGNOSTIC PARTIAL [X]; STATIC UNIT [T] | Belum terbukti sebagai oracle penuh: valid cryptographic control and independently configured local PEM vs JWKS selection; verifier not weakened; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M08.01 | EXECUTED DIAGNOSTIC PARTIAL [Y]; STATIC UNIT [O] | Belum terbukti sebagai oracle penuh: explicit RS verified issuer/sub binding resolves intended eligible user; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M08.02 | EXECUTED DIAGNOSTIC PARTIAL [Y]; STATIC UNIT [O] | Belum terbukti sebagai oracle penuh: missing/wrong-user/inactive/ambiguous/forged/unverified deny without email/login fallback, autobinding or rewrite; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M08.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: malicious RPC cannot create binding without existing trust-admin privilege; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M08.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: zero self-provider HTTP across success/classification/key/error with calibrated full observer; remote parity; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M09.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: existing legacy login-sub tokens and RS bindings: no conversion/alias/new dual acceptance; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| M09.02 | NOT ASSESSED | Perbandingan baseline legacy profile belum dibuktikan; pengecualian hanya untuk perubahan #79 yang secara eksplisit diterima, tanpa mengasumsikan hasil atau penerimaan perubahan lainnya. |
| M09.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: no sibling acceptance inferred; sibling owners review captured contract; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I01.01 | EXECUTED DIAGNOSTIC PARTIAL [I] | Belum terbukti sebagai oracle penuh: approved mapping, same principal/issuer/database twice then login/email rename: exact same nonempty opaque sub; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I01.02 | EXECUTED DIAGNOSTIC PARTIAL [I] | Belum terbukti sebagai oracle penuh: two principals differ; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I01.03 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: sub differs from login/email/raw DB id; signed profile omits uid/login/db claims; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I01.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: synthetic-only evidence; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I02.01 | STATIC UNIT [F] | Belum terbukti sebagai oracle penuh: simultaneous same issuer_namespace/principal issuance one persistent mapping and same sub; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I02.02 | EXECUTED DIAGNOSTIC PARTIAL [H] | Belum terbukti sebagai oracle penuh: DB rejects duplicate pair and duplicate issuer/sub across principals; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I02.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: separately established issuer/DB namespaces isolate; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I02.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: unknown/ambiguous/reassigned/deleted identity rejects without reuse; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I02.05 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: clone/issuer changes tested only with separately approved lifecycle; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I03.01 | STATIC UNIT [B] | Belum terbukti sebagai oracle penuh: authenticated active registered A issuance signed client_id equals A record and matching RS verifies; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I03.02 | STATIC UNIT [M] | Belum terbukti sebagai oracle penuh: forged claim or B kw, audience substitution, missing auth, inactive/unknown client, B auth as A and ambiguous mapping reject before signer; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I03.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: direct glue/helper without authenticated client cannot issue RS profile; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I03.04 | EXECUTED DIAGNOSTIC PARTIAL [P] | Belum terbukti sebagai oracle penuh: legacy non-RS separately assessed; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I04.01 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: inventory affected accepted consumers of existing login-sub token, legacy client and RS binding fixtures; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I04.02 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: no automatic rewrite/alias/replacement or outside-profile claim change; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I04.03 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: without Owner/sibling-approved compatibility and issuer-model scope positive issuance blocked; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |
| I04.04 | NOT ASSESSED | Belum terbukti sebagai oracle penuh: RS (issuer, sub) binding not claimed to prove issuer (issuer, principal) uniqueness; seluruh subvarian yang disebut belum diekspansi/diperiksa satu per satu. |

Kunci bukti: nomor adalah baris AST assertion aktif (termasuk `assertRaises`), bukan klaim bahwa semua baris rentang dieksekusi secara individual. Metode diagnostic hanya memiliki bukti rekonsiliasi start/selector, bukan hasil assertion per-test terpisah.
- **A** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_ttl_defaults_in_memory_and_enforces_canonical_ascii_bounds` — assertion aktif: 306, 310, 314.
- **B** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_authenticated_client_issues_only_opaque_profile_claims_and_scoped_ttl` — assertion aktif: 396, 398, 399, 405, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 419, 420, 421, 422, 423, 429, 432, 434, 436, 438.
- **C** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileModelBoundaryTests::test_settings_reject_noncanonical_and_out_of_range_fresh_ttl_before_persistence` — assertion aktif: 283.
- **D** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileModelBoundaryTests::test_settings_direct_rpc_requires_system_group_for_profile_and_ttl` — assertion aktif: 236.
- **E** `amr_oidc/tests/unit/test_subject_mapping_retry.py::SubjectMapperRetryTests::test_unique_collision_with_archived_subject_retries_new_random_value` — assertion aktif: 105, 106, 107, 108.
- **F** `amr_oidc/tests/unit/test_subject_mapping_retry.py::SubjectMapperRetryTests::test_unique_error_after_same_principal_winner_returns_existing_subject` — assertion aktif: 126, 127, 128, 129, 130, 131.
- **G** `amr_oidc/tests/unit/test_subject_mapping_retry.py::SubjectMapperRetryTests::test_repeated_unique_collisions_exhaust_three_attempts_without_reserving` — assertion aktif: 143, 147, 148, 149, 150.
- **H** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_archived_subject_keeps_both_unique_reservations_and_denies_issuance` — assertion aktif: 64, 65, 68, 72.
- **I** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerSubjectIdentity::test_subject_is_stable_across_user_rename_and_distinct_per_user` — assertion aktif: 104, 112, 121, 122.
- **J** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_user_deletion_is_restricted_by_subject_foreign_key` — assertion aktif: 85.
- **K** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_every_human_role_has_no_mapping_acl` — assertion aktif: 35, 36, 38.
- **L** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_fresh_profile_instance_binding_requires_external_marker_and_matches_digest` — assertion aktif: 325, 327, 334, 337, 339, 344, 346, 348.
- **M** `amr_oidc/tests/unit/test_fresh_profile_issuance.py::FreshProfileTokenHelperTests::test_bad_client_credential_stops_before_mapping_or_signer` — assertion aktif: 462, 464, 465.
- **N** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_actual_rs256_signature_and_helpers` — assertion aktif: 305, 306, 307, 308, 309, 310, 311.
- **O** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat19_binding_exact_no_email_login_or_autobind` — assertion aktif: 590, 595.
- **P** `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_self_issuance_and_system_cross_user_signed_target_claims` — assertion aktif: 37, 42, 43, 50, 51, 52.
- **Q** `amr_oidc/tests/unit/test_token_issuer_security.py::TokenIssuerSecurityTests::test_glue_preserves_legacy_missing_ttl_default_end_to_end` — assertion aktif: 253, 254.
- **R** `amr_oidc/tests/unit/test_token_issuer_security.py::TokenIssuerSecurityTests::test_fresh_client_route_rejects_caller_subject_before_issuance` — assertion aktif: 521, 522, 523, 524, 525, 526, 527.
- **S** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_required_claims_and_zero_leeway` — assertion aktif: 350.
- **T** `amr_resource/tests/unit/test_security_unit.py::SecurityUnitTests::test_uat06_jwks_rsa_selection_and_no_cache` — assertion aktif: 372.
- **U** `amr_oidc/tests/integration/test_fresh_issuer_subject.py::TestFreshIssuerPrincipalSubject::test_sudo_rpc_cannot_create_or_mutate_a_subject` — assertion aktif: 43, 48, 50, 52.
- **V** `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_legacy_cache_reuses_within_ttl_bucket_and_rolls_over` — assertion aktif: 84, 85, 92, 93.
- **W** `amr_oidc_resource/tests/integration/test_user_token_glue.py::TestUserTokenGlueActorAndIssuer::test_signing_configuration_change_uses_new_key_and_ttl` — assertion aktif: 123, 124, 125.
- **X** `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut06_verified_jwt_and_failures` — assertion aktif: 450, 451, 455, 457, 459, 460, 462, 463, 465, 471, 475, 485, 486, 487, 488, 489, 496, 501, 503, 508, 509.
- **Y** `amr_resource/tests/integration/test_helper.py::TestResourceHelper::test_ut07_matching` — assertion aktif: 524, 525, 526, 527, 530, 535, 539, 540, 541, 543, 546.

```json
{"appended_atom_ids": 92, "extra_atom_ids": [], "full_case_established": 0, "missing_atom_ids": [], "original_rows": 92, "primary_status_counts": {"EXECUTED_DIAGNOSTIC_PARTIAL": 19, "NOT_ASSESSED": 42, "STATIC_UNIT": 31}, "schema": "ct-mi-atom-coverage-v1", "unique_atom_ids": 92, "variant_expansion": "not performed"}
```

## Lampiran tambahan — dekomposisi varian eksplisit (parsial)


Overlay aditif pada 92 parent historis; tidak mengganti teks accepted maupun bukti Gen5. Ini inventaris **parsial**, bukan bukti lengkap pemecahan setiap varian: parent yang tidak tercantum dan sub-oracle yang belum didekomposisi tetap unresolved. Setiap anak NOT ASSESSED karena bukti spesifik anak belum diverifikasi independen pada blob kandidat; referensi parsial parent tidak otomatis diwariskan. NOT ASSESSED bukan klaim tes tidak ada. Actual assertion untuk seluruh kasus UAT accepted secara penuh tetap NOT RUN; ini tidak menyangkal eksekusi diagnostik Gen5 sebelumnya yang terbatas dan bukan eksekusi acceptance. SCOPE-01 OPEN, positive fresh terkait BLOCKED; tidak ada rebind atau PASS.

| Child ID | Varian/condition/output | Status dan metode/bukti |
|---|---|---|
| C02.01.v001 | save 60; issuance 60 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C02.01.v002 | save 86400; issuance 86400 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C02.02.v001 | refresh reader stored 60 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C02.02.v002 | refresh reader stored 86400 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v001 | existing provenance; absent; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v002 | existing provenance; absent; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v003 | existing provenance; absent; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v004 | existing provenance; 3600; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v005 | existing provenance; 3600; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v006 | existing provenance; 3600; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v007 | existing provenance; 86400; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v008 | existing provenance; 86400; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v009 | existing provenance; 86400; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v010 | existing provenance; 59; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v011 | existing provenance; 59; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v012 | existing provenance; 59; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v013 | existing provenance; malformed; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v014 | existing provenance; malformed; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v015 | existing provenance; malformed; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v016 | unknown provenance; absent; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v017 | unknown provenance; absent; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v018 | unknown provenance; absent; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v019 | unknown provenance; 3600; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v020 | unknown provenance; 3600; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v021 | unknown provenance; 3600; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v022 | unknown provenance; 86400; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v023 | unknown provenance; 86400; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v024 | unknown provenance; 86400; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v025 | unknown provenance; 59; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v026 | unknown provenance; 59; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v027 | unknown provenance; 59; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v028 | unknown provenance; malformed; no key write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v029 | unknown provenance; malformed; no fresh issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.01.v030 | unknown provenance; malformed; no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v001 | existing provenance; absent; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v002 | existing provenance; absent; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v003 | existing provenance; absent; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v004 | existing provenance; absent; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v005 | existing provenance; absent; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v006 | existing provenance; absent; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v007 | existing provenance; 3600; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v008 | existing provenance; 3600; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v009 | existing provenance; 3600; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v010 | existing provenance; 3600; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v011 | existing provenance; 3600; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v012 | existing provenance; 3600; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v013 | existing provenance; 86400; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v014 | existing provenance; 86400; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v015 | existing provenance; 86400; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v016 | existing provenance; 86400; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v017 | existing provenance; 86400; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v018 | existing provenance; 86400; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v019 | existing provenance; 59; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v020 | existing provenance; 59; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v021 | existing provenance; 59; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v022 | existing provenance; 59; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v023 | existing provenance; 59; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v024 | existing provenance; 59; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v025 | existing provenance; malformed; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v026 | existing provenance; malformed; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v027 | existing provenance; malformed; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v028 | existing provenance; malformed; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v029 | existing provenance; malformed; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v030 | existing provenance; malformed; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v031 | unknown provenance; absent; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v032 | unknown provenance; absent; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v033 | unknown provenance; absent; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v034 | unknown provenance; absent; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v035 | unknown provenance; absent; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v036 | unknown provenance; absent; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v037 | unknown provenance; 3600; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v038 | unknown provenance; 3600; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v039 | unknown provenance; 3600; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v040 | unknown provenance; 3600; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v041 | unknown provenance; 3600; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v042 | unknown provenance; 3600; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v043 | unknown provenance; 86400; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v044 | unknown provenance; 86400; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v045 | unknown provenance; 86400; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v046 | unknown provenance; 86400; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v047 | unknown provenance; 86400; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v048 | unknown provenance; 86400; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v049 | unknown provenance; 59; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v050 | unknown provenance; 59; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v051 | unknown provenance; 59; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v052 | unknown provenance; 59; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v053 | unknown provenance; 59; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v054 | unknown provenance; 59; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v055 | unknown provenance; malformed; baseline legacy issuer exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v056 | unknown provenance; malformed; baseline legacy helper exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v057 | unknown provenance; malformed; baseline refresh exact outcome | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v058 | unknown provenance; malformed; baseline exceptions | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v059 | unknown provenance; malformed; baseline expires_in falsy semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C03.02.v060 | unknown provenance; malformed; baseline expires_in override semantics | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v001 | tamper empty: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v002 | tamper whitespace: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v003 | tamper signed: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v004 | tamper decimal: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v005 | tamper non-ASCII digits: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v006 | tamper zero: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v007 | tamper 59: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v008 | tamper 86401: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v009 | tamper huge: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.01.v010 | tamper text: sanitized UserError before signer and cached return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.03.v001 | authorized settings invalid write rejects | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.03.v002 | positive control 60 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.03.v003 | positive control 86400 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.04.v001 | ordinary actor UI cannot change setting | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.04.v002 | ordinary actor direct RPC cannot change setting | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.04.v003 | privileged tamper cannot bypass issuance validation | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C04.04.v004 | effective ACL readback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.01.v001 | override omitted succeeds | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.01.v002 | override integer 60 succeeds | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.01.v003 | override configured TTL succeeds | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v001 | override None rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v002 | override bool rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v003 | override 0 rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v004 | override 59 rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v005 | override >configured rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v006 | override 86401 rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v007 | override float rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| C05.02.v008 | override string rejects before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T01.03.v001 | authorized save 60 and use 60 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T01.03.v002 | authorized save 86400 and use 86400 | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.01.v001 | existing stored 3600: before approved migration no overwrite, including Settings refresh | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.01.v002 | existing stored 3600: before approved migration no reinterpretation, including Settings refresh | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.01.v003 | existing stored 86400: before approved migration no overwrite, including Settings refresh | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.01.v004 | existing stored 86400: before approved migration no reinterpretation, including Settings refresh | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.03.v001 | existing missing: no 900 default | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.03.v002 | existing missing: no silent write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.03.v003 | existing missing: fresh issuance blocked pending migration choice | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.03.v004 | unknown provenance: no 900 default | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.03.v005 | unknown provenance: no silent write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T02.03.v006 | unknown provenance: fresh issuance blocked pending migration choice | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v001 | empty: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v002 | empty: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v003 | spaces: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v004 | spaces: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v005 | ` 60`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v006 | ` 60`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v007 | `60 `: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v008 | `60 `: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v009 | `+60`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v010 | `+60`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v011 | `-1`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v012 | `-1`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v013 | `0`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v014 | `0`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v015 | `59`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v016 | `59`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v017 | `86401`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v018 | `86401`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v019 | `60.0`: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v020 | `60.0`: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v021 | non-ASCII digits: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v022 | non-ASCII digits: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v023 | text: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v024 | text: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v025 | huge integer: Settings UI rejects save | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.01.v026 | huge integer: direct parameter tamper evaluated at config read/issuance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v001 | config read/issuance after invalid empty: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v002 | config read/issuance after invalid empty: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v003 | config read/issuance after invalid empty: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v004 | config read/issuance after invalid empty: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v005 | config read/issuance after invalid empty: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v006 | config read/issuance after invalid spaces: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v007 | config read/issuance after invalid spaces: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v008 | config read/issuance after invalid spaces: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v009 | config read/issuance after invalid spaces: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v010 | config read/issuance after invalid spaces: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v011 | config read/issuance after invalid ` 60`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v012 | config read/issuance after invalid ` 60`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v013 | config read/issuance after invalid ` 60`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v014 | config read/issuance after invalid ` 60`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v015 | config read/issuance after invalid ` 60`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v016 | config read/issuance after invalid `60 `: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v017 | config read/issuance after invalid `60 `: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v018 | config read/issuance after invalid `60 `: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v019 | config read/issuance after invalid `60 `: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v020 | config read/issuance after invalid `60 `: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v021 | config read/issuance after invalid `+60`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v022 | config read/issuance after invalid `+60`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v023 | config read/issuance after invalid `+60`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v024 | config read/issuance after invalid `+60`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v025 | config read/issuance after invalid `+60`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v026 | config read/issuance after invalid `-1`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v027 | config read/issuance after invalid `-1`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v028 | config read/issuance after invalid `-1`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v029 | config read/issuance after invalid `-1`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v030 | config read/issuance after invalid `-1`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v031 | config read/issuance after invalid `0`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v032 | config read/issuance after invalid `0`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v033 | config read/issuance after invalid `0`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v034 | config read/issuance after invalid `0`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v035 | config read/issuance after invalid `0`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v036 | config read/issuance after invalid `59`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v037 | config read/issuance after invalid `59`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v038 | config read/issuance after invalid `59`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v039 | config read/issuance after invalid `59`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v040 | config read/issuance after invalid `59`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v041 | config read/issuance after invalid `86401`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v042 | config read/issuance after invalid `86401`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v043 | config read/issuance after invalid `86401`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v044 | config read/issuance after invalid `86401`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v045 | config read/issuance after invalid `86401`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v046 | config read/issuance after invalid `60.0`: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v047 | config read/issuance after invalid `60.0`: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v048 | config read/issuance after invalid `60.0`: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v049 | config read/issuance after invalid `60.0`: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v050 | config read/issuance after invalid `60.0`: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v051 | config read/issuance after invalid non-ASCII digits: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v052 | config read/issuance after invalid non-ASCII digits: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v053 | config read/issuance after invalid non-ASCII digits: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v054 | config read/issuance after invalid non-ASCII digits: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v055 | config read/issuance after invalid non-ASCII digits: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v056 | config read/issuance after invalid text: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v057 | config read/issuance after invalid text: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v058 | config read/issuance after invalid text: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v059 | config read/issuance after invalid text: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v060 | config read/issuance after invalid text: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v061 | config read/issuance after invalid huge integer: sanitized configuration error | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v062 | config read/issuance after invalid huge integer: before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v063 | config read/issuance after invalid huge integer: before warm cache return | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v064 | config read/issuance after invalid huge integer: no fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.02.v065 | config read/issuance after invalid huge integer: no clamp | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.03.v001 | integer endpoint 60 positive | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T03.03.v002 | integer endpoint 86400 positive | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.01.v001 | omission positive | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.01.v002 | integer 60 positive | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.01.v003 | effective TTL positive | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v001 | explicit None: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v002 | explicit None: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v003 | bool: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v004 | bool: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v005 | zero: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v006 | zero: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v007 | negative: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v008 | negative: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v009 | fraction: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v010 | fraction: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v011 | string: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v012 | string: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v013 | less than 60: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v014 | less than 60: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v015 | over 86400: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v016 | over 86400: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v017 | over effective TTL: denied before signer, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T04.02.v018 | over effective TTL: denied before cache, all authorized fresh entry points including RPC bypass | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v001 | DB isolation | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v002 | audience isolation | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v003 | actor isolation | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v004 | key isolation | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v005 | policy isolation | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v006 | concurrent changes | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| T05.04.v007 | measured propagation, no instantaneous promise | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.01.v001 | same issuer/user two issuances same opaque subject | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.01.v002 | login rename reissuance same subject | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.01.v003 | email rename reissuance same subject | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.01.v004 | subject exactly 64 lowercase hex | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.03.v001 | signed payload excludes uid | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.03.v002 | signed payload excludes login | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M01.03.v003 | signed payload excludes db | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.01.v001 | standard-library secrets generates 32 bytes | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.01.v002 | Odoo SQL uniqueness constraints | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.01.v003 | no raw SQL | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.05.v001 | DB rejects duplicate namespace/principal with active row | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.05.v002 | DB rejects duplicate namespace/principal with archived row | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.05.v003 | DB rejects duplicate namespace/sub with active row | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M02.05.v004 | DB rejects duplicate namespace/sub with archived row | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.01.v001 | privileged model RPC write rejected, reservation retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.01.v002 | privileged model RPC reassignment rejected, reservation retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.01.v003 | privileged model RPC reparent rejected, reservation retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.01.v004 | privileged model RPC namespace edit rejected, reservation retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.01.v005 | privileged model RPC subject edit rejected, reservation retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.01.v006 | privileged model RPC unlink rejected, reservation retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.03.v001 | archived mapping cannot issue | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.03.v002 | archived mapping cannot be reused | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.04.v001 | missing namespace fails before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.04.v002 | ambiguous namespace fails before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.04.v003 | inactive principal fails before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M03.04.v004 | deleted principal fails before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M04.02.v001 | cloned DB without authorized lifecycle blocks scoped issuance and identity rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M04.02.v002 | restored DB without authorized lifecycle blocks scoped issuance and identity rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M04.02.v003 | missing namespace without authorized lifecycle blocks scoped issuance and identity rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M04.02.v004 | changed namespace without authorized lifecycle blocks scoped issuance and identity rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M04.02.v005 | reused namespace without authorized lifecycle blocks scoped issuance and identity rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
**Oracle bersama M05.01.v001–v048 (UAT:123):** read/create hanya melalui private service path setelah otorisasi actor/client; tidak ada manusia yang dapat bypass immutability. Ini batasan, bukan izin otomatis bagi service atau blanket denial/allow untuk setiap kombinasi. Outcome spesifik actor/operasi yang tidak ditentukan oleh batasan tersebut tetap **NOT ASSESSED**, termasuk search, RPC dan mekanisme context/sudo; buktikan ACL/record-rule dan batas sudo pada installed registry.

| M05.01.v001 | public: read | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v002 | public: search | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v003 | public: create | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v004 | public: write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v005 | public: unlink | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v006 | public: exposed RPC | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v007 | public: forged context | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v008 | public: forged sudo kwargs | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v009 | portal: read | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v010 | portal: search | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v011 | portal: create | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v012 | portal: write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v013 | portal: unlink | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v014 | portal: exposed RPC | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v015 | portal: forged context | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v016 | portal: forged sudo kwargs | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v017 | regular internal: read | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v018 | regular internal: search | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v019 | regular internal: create | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v020 | regular internal: write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v021 | regular internal: unlink | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v022 | regular internal: exposed RPC | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v023 | regular internal: forged context | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v024 | regular internal: forged sudo kwargs | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v025 | system administrator: read | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v026 | system administrator: search | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v027 | system administrator: create | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v028 | system administrator: write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v029 | system administrator: unlink | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v030 | system administrator: exposed RPC | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v031 | system administrator: forged context | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v032 | system administrator: forged sudo kwargs | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v033 | trust administrator: read | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v034 | trust administrator: search | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v035 | trust administrator: create | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v036 | trust administrator: write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v037 | trust administrator: unlink | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v038 | trust administrator: exposed RPC | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v039 | trust administrator: forged context | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v040 | trust administrator: forged sudo kwargs | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v041 | legitimate issuance service: read | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v042 | legitimate issuance service: search | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v043 | legitimate issuance service: create | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v044 | legitimate issuance service: write | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v045 | legitimate issuance service: unlink | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v046 | legitimate issuance service: exposed RPC | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v047 | legitimate issuance service: forged context | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.01.v048 | legitimate issuance service: forged sudo kwargs | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.02.v001 | private service read only after actor/client authorization | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.02.v002 | private service create only after actor/client authorization | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M05.02.v003 | no human bypass of immutability | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v001 | missing auth provenance: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v002 | forged auth provenance: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v003 | client B kwargs: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v004 | inactive client: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v005 | unknown client: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v006 | ambiguous client: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v007 | issuer mismatch: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v008 | audience mismatch: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v009 | unauthorized user: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M06.02.v010 | direct glue without authenticated client: fail before signer | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v001 | tampered signed header: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v002 | tampered signed payload: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v003 | tampered signature: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v004 | wrong algorithm: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v005 | wrong type: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v006 | wrong key: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v007 | wrong kid: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v008 | untrusted key: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.01.v009 | expired key: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v001 | missing iss: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v002 | missing aud: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v003 | missing iat: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v004 | missing exp: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v005 | missing jti: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v006 | missing client: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v007 | missing azp: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v008 | wrong iss: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v009 | wrong aud: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v010 | wrong iat: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v011 | wrong exp: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v012 | wrong jti: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v013 | wrong client: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v014 | wrong azp: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v015 | expiration: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v016 | invalid policy: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.02.v017 | invalid provenance: RS rejects without fallback | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.03.v001 | valid cryptographic positive control | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.03.v002 | independently configured local PEM key selection | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.03.v003 | independently configured JWKS key selection | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M07.03.v004 | existing verifier not weakened | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.02.v001 | missing subject: deny; no email/login fallback, automatic binding or rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.02.v002 | binding to wrong user: deny; no email/login fallback, automatic binding or rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.02.v003 | binding to inactive user: deny; no email/login fallback, automatic binding or rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.02.v004 | ambiguous binding: deny; no email/login fallback, automatic binding or rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.02.v005 | forged subject: deny; no email/login fallback, automatic binding or rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.02.v006 | unverified subject: deny; no email/login fallback, automatic binding or rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.04.v001 | no self-provider HTTP on success path | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.04.v002 | no self-provider HTTP on classification path | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.04.v003 | no self-provider HTTP on key path | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.04.v004 | no self-provider HTTP on error path | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M08.04.v005 | remote parity retained | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M09.01.v001 | legacy login-sub tokens: no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M09.01.v002 | legacy login-sub tokens: no alias | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M09.01.v003 | legacy login-sub tokens: no new dual acceptance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M09.01.v004 | RS bindings: no conversion | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M09.01.v005 | RS bindings: no alias | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| M09.01.v006 | RS bindings: no new dual acceptance | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.01.v001 | two issuances same principal/issuer/database yield same nonempty opaque sub | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.01.v002 | login rename reissue retains sub | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.01.v003 | email rename reissue retains sub | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.03.v001 | sub differs from login | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.03.v002 | sub differs from email | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.03.v003 | sub differs from raw DB id | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.03.v004 | scoped profile omits uid identifying claim | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.03.v005 | scoped profile omits login identifying claim | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I01.03.v006 | scoped profile omits db identifying claim | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I02.02.v001 | DB rejects duplicate issuer_namespace/principal | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I02.02.v002 | DB rejects duplicate issuer/sub for another principal | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I02.04.v001 | unknown identity rejects without silent reuse | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I02.04.v002 | ambiguous identity rejects without silent reuse | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I02.04.v003 | reassigned identity rejects without silent reuse | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I02.04.v004 | deleted identity rejects without silent reuse | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v001 | forged claim client_id B rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v002 | kw client_id B rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v003 | audience substitution rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v004 | missing auth rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v005 | inactive client rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v006 | unknown client rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v007 | auth for B presented as A rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.02.v008 | ambiguous mapping rejects before signing | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.03.v001 | direct glue without authenticated client cannot issue RS profile | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I03.03.v002 | direct helper without authenticated client cannot issue RS profile | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.01.v001 | inventory affected accepted consumers: existing login-sub token | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.01.v002 | inventory affected accepted consumers: legacy client | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.01.v003 | inventory affected accepted consumers: RS subject binding | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.02.v001 | no automatic rewrite | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.02.v002 | no automatic alias | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.02.v003 | no automatic replacement | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |
| I04.02.v004 | no altered claims outside approved profile | NOT ASSESSED — metode/ekspresi spesifik belum diverifikasi pada `49b5a739`; bukan bukti gagal. |

Pemeriksaan mekanis inventaris yang ditranskripsi: 43 parent dari 92 memiliki anak; 426 ID anak unik; 49 parent belum dipecah dalam overlay ini. Perbandingan hanya terhadap daftar eksplisit manual di script pembuat, **bukan** parser semantik lengkap UAT; kombinasi actor × operasi/hasil dan seluruh parent lain masih perlu telaah independen. Tidak ada klaim semua named variant sudah tertangkap. Katalog A–Y dan metode/ekspresi pada lampiran sebelumnya merupakan bukti parent historis, bukan pemetaan otomatis untuk anak di sini.

Parent belum dipecah: C01.01, C01.02, C01.03, C01.04, C01.05, C02.03, C02.04, C03.03, C04.02, C05.03, C06.01, C06.02, C06.03, C06.04, I01.02, I01.04, I02.01, I02.03, I02.05, I03.01, I03.04, I04.03, I04.04, M01.02, M01.04, M02.02, M02.03, M02.04, M03.02, M04.01, M04.03, M05.03, M06.01, M06.03, M08.01, M08.03, M09.02, M09.03, T01.01, T01.02, T01.04, T02.02, T04.03, T05.01, T05.02, T05.03, T06.01, T06.02, T06.03.

## Lampiran — disposisi 49 parent tersisa (aditif, NOT ASSESSED)

UAT terikat SHA-256 `fade6f5d10f19b29584e23506a00e28ef6fb1fabb28cb026ad139eedf07e6d7e`; rujukan baris menunjuk fixture/tindakan/expected kasus accepted, bukan bukti hasil. Setiap baris mewarisi fixture, actor, prasyarat dan observer eksplisit pada kasus UAT yang dirujuk dan UAT:7–13,17; actor yang tidak dinamai tidak ditebak. Aksi dan outcome spesifik diberikan pada kolom oracle. Semua anak baru **NOT ASSESSED**, actual **NOT RUN**; residual adalah seluruh verifikasi oracle tersebut pada fixture/actor/entry point yang berlaku, termasuk readback dan evidence tersanitasi. Tidak ada pemetaan otomatis dari bukti parent ke anak. Gen5 tetap diagnostik historis, bukan rebind; SCOPE-01 tetap OPEN.

`Satu atom` berarti tidak ada varian bernama yang dapat dipisahkan tanpa mengarang; `Ekspansi` memisahkan varian/operasi/outcome eksplisit saja, bukan cross-product. Nilai, entry point, actor atau kasus yang hanya dirujuk secara kolektif tetap perlu inventaris independen.

| Parent | Disposisi | Anak baru | Sumber |
|---|---|---:|---|
| C01.01 | Satu atom | 1 | UAT:63 |
| C01.02 | Ekspansi | 3 | UAT:63 |
| C01.03 | Satu atom | 1 | UAT:63 |
| C01.04 | Satu atom | 1 | UAT:63 |
| C01.05 | Ekspansi | 2 | UAT:63 |
| C02.03 | Satu atom | 1 | UAT:69 |
| C02.04 | Ekspansi | 2 | UAT:69 |
| C03.03 | Ekspansi | 2 | UAT:75 |
| C04.02 | Ekspansi | 2 | UAT:81 |
| C05.03 | Satu atom | 1 | UAT:87 |
| C06.01 | Ekspansi | 4 | UAT:93 |
| C06.02 | Ekspansi | 2 | UAT:93 |
| C06.03 | Ekspansi | 2 | UAT:93 |
| C06.04 | Satu atom | 1 | UAT:93 |
| T01.01 | Ekspansi | 3 | UAT:171 |
| T01.02 | Ekspansi | 3 | UAT:171 |
| T01.04 | Ekspansi | 2 | UAT:171 |
| T02.02 | Ekspansi | 2 | UAT:177 |
| T04.03 | Ekspansi | 3 | UAT:189 |
| T05.01 | Ekspansi | 3 | UAT:195 |
| T05.02 | Ekspansi | 4 | UAT:195 |
| T05.03 | Ekspansi | 3 | UAT:195 |
| T06.01 | Ekspansi | 4 | UAT:201 |
| T06.02 | Ekspansi | 4 | UAT:201 |
| T06.03 | Satu atom | 1 | UAT:201 |
| M01.02 | Satu atom | 1 | UAT:99 |
| M01.04 | Ekspansi | 2 | UAT:99 |
| M02.02 | Ekspansi | 4 | UAT:105 |
| M02.03 | Satu atom | 1 | UAT:105 |
| M02.04 | Ekspansi | 2 | UAT:105 |
| M03.02 | Satu atom | 1 | UAT:111 |
| M04.01 | Satu atom | 1 | UAT:117 |
| M04.03 | Satu atom | 1 | UAT:117 |
| M05.03 | Ekspansi | 3 | UAT:123 |
| M06.01 | Ekspansi | 3 | UAT:129 |
| M06.03 | Satu atom | 1 | UAT:129 |
| M08.01 | Satu atom | 1 | UAT:141 |
| M08.03 | Satu atom | 1 | UAT:141 |
| M09.02 | Satu atom | 1 | UAT:147 |
| M09.03 | Ekspansi | 2 | UAT:147 |
| I01.02 | Satu atom | 1 | UAT:207 |
| I01.04 | Satu atom | 1 | UAT:207 |
| I02.01 | Ekspansi | 2 | UAT:213 |
| I02.03 | Satu atom | 1 | UAT:213 |
| I02.05 | Ekspansi | 2 | UAT:213 |
| I03.01 | Ekspansi | 3 | UAT:219 |
| I03.04 | Satu atom | 1 | UAT:219 |
| I04.03 | Satu atom | 1 | UAT:225 |
| I04.04 | Satu atom | 1 | UAT:225 |

| Anak | Fixture/actor, aksi dan outcome expected | Sumber | Status / residual |
|---|---|---|---|
| C01.01.v001 | Fixture/actor kasus C01: fresh provenance, absent key: scoped issuance reads 900 seconds. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.02.v001 | Fixture/actor kasus C01: absent key: Settings may display 900. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.02.v002 | Fixture/actor kasus C01: absent key: Settings read does not create key. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.02.v003 | Fixture/actor kasus C01: absent key: scoped issue does not create key. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.03.v001 | Fixture/actor kasus C01: absent key: refresh helper retains baseline 86400. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.04.v001 | Fixture/actor kasus C01: absent key: refresh creation remains source 14 days. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.05.v001 | Fixture/actor kasus C01: fresh absent key: signed exp minus iat equals 900. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C01.05.v002 | Fixture/actor kasus C01: fresh absent key: response TTL equals 900. | UAT:63 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C02.03.v001 | Fixture/actor kasus C02: fresh Settings: disclose coupling before authorized save. | UAT:69 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C02.04.v001 | Fixture/actor kasus C02: fresh authorized Settings save: no other setting changed. | UAT:69 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C02.04.v002 | Fixture/actor kasus C02: fresh authorized Settings save: no silent write. | UAT:69 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C03.03.v001 | Fixture/actor kasus C03: existing other token classes unchanged except independently accepted #79 modifications. | UAT:75 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C03.03.v002 | Fixture/actor kasus C03: existing other token claims unchanged except independently accepted #79 modifications. | UAT:75 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C04.02.v001 | Fixture/actor kasus C04: fresh tampered configuration: unauthorized actor receives AccessError. | UAT:81 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C04.02.v002 | Fixture/actor kasus C04: fresh tampered configuration: protocol boundary maps errors to existing sanitized protocol error without secrets. | UAT:81 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C05.03.v001 | Fixture/actor kasus C05: legacy helper arguments: delta imposes no new restrictions. | UAT:87 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.01.v001 | Fixture/actor kasus C06: two scoped calls: each revalidates auth. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.01.v002 | Fixture/actor kasus C06: two scoped calls: each revalidates config. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.01.v003 | Fixture/actor kasus C06: two scoped calls: each mints. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.01.v004 | Fixture/actor kasus C06: two scoped calls: no scoped cache return. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.02.v001 | Fixture/actor kasus C06: after worker observes config B, its next issuance uses B. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.02.v002 | Fixture/actor kasus C06: concurrent reads: measure propagation without invented global propagation. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.03.v001 | Fixture/actor kasus C06: existing token retains signed exp. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.03.v002 | Fixture/actor kasus C06: verifier rejects at configured boundary subject to policy and trust. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| C06.04.v001 | Fixture/actor kasus C06: required legacy cache cases still apply; exact cases require separate identification. | UAT:93 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.01.v001 | Fixture/actor kasus T01: verified fresh absent TTL: each allowed authenticated fresh entry point yields TTL 900. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.01.v002 | Fixture/actor kasus T01: same issuance: signed exp minus iat equals 900. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.01.v003 | Fixture/actor kasus T01: same issuance: response metadata agrees with TTL 900. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.02.v001 | Fixture/actor kasus T01: verified fresh absent TTL: Settings uses one key. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.02.v002 | Fixture/actor kasus T01: verified fresh absent TTL: Settings displays seconds. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.02.v003 | Fixture/actor kasus T01: verified fresh absent TTL: Settings does not write. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.04.v001 | Fixture/actor kasus T01: legacy glue: do not apply fresh TTL. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T01.04.v002 | Fixture/actor kasus T01: legacy glue: characterize separately. | UAT:171 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T02.02.v001 | Fixture/actor kasus T02: approved rollout with existing stored 3600 preserves exact value. | UAT:177 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T02.02.v002 | Fixture/actor kasus T02: approved rollout with existing stored 86400 preserves exact value. | UAT:177 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T04.03.v001 | Fixture/actor kasus T04: legacy API: no new restrictions from delta. | UAT:189 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T04.03.v002 | Fixture/actor kasus T04: legacy helper: no new restrictions from delta. | UAT:189 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T04.03.v003 | Fixture/actor kasus T04: legacy contract change requires separate compatibility approval. | UAT:189 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.01.v001 | Fixture/actor kasus T05: controlled clock and prior valid token/cache; sign with configured A, change to B, then reissue after each worker observes B: signed exp reflects B. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.01.v002 | Fixture/actor kasus T05: controlled clock and prior valid token/cache; sign with configured A, change to B, then reissue after each worker observes B: returned metadata reflects B. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.01.v003 | Fixture/actor kasus T05: controlled clock and prior valid token/cache; sign with configured A, change to B, then reissue after each worker observes B: no A token returned. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.02.v001 | Fixture/actor kasus T05: previously signed token retains exp. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.02.v002 | Fixture/actor kasus T05: previously signed token may fail policy or trust. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.02.v003 | Fixture/actor kasus T05: at exp verifier rejects with source baseline leeway zero. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.02.v004 | Fixture/actor kasus T05: after exp verifier rejects with source baseline leeway zero. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.03.v001 | Fixture/actor kasus T05: warm cache cannot return expired token. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.03.v002 | Fixture/actor kasus T05: warm cache cannot bypass auth checks. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T05.03.v003 | Fixture/actor kasus T05: warm cache cannot bypass config checks. | UAT:195 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.01.v001 | Fixture/actor kasus T06: inventory shared-key readers. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.01.v002 | Fixture/actor kasus T06: inventory shared-key extensions. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.01.v003 | Fixture/actor kasus T06: preserve refresh helper behavior. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.01.v004 | Fixture/actor kasus T06: preserve 14-day source issuance implementation. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.02.v001 | Fixture/actor kasus T06: separately approved migration: verify old values. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.02.v002 | Fixture/actor kasus T06: separately approved migration: verify fresh/missing. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.02.v003 | Fixture/actor kasus T06: separately approved migration: verify rollback. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.02.v004 | Fixture/actor kasus T06: separately approved migration: record observed refresh reader effects without changing refresh feature. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| T06.03.v001 | Fixture/actor kasus T06: key change affects refresh consumer and no compatible plan approved: rollout BLOCKED. | UAT:201 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M01.02.v001 | Fixture/actor kasus M01: approved fresh mapping: different user yields different subject. | UAT:99 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M01.04.v001 | Fixture/actor kasus M01: approved fresh mapping: caller-selected subject not accepted. | UAT:99 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M01.04.v002 | Fixture/actor kasus M01: inspect actual payload only in secured synthetic fixture. | UAT:99 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.02.v001 | Fixture/actor kasus M02: concurrent first issuance same pair: exactly one persisted row. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.02.v002 | Fixture/actor kasus M02: concurrent first issuance same pair: same subject. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.02.v003 | Fixture/actor kasus M02: integrity conflict: observe savepoint handling. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.02.v004 | Fixture/actor kasus M02: integrity conflict: observe exact namespace/principal reread. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.03.v001 | Fixture/actor kasus M02: isolated deterministic subject collision: retry then success. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.04.v001 | Fixture/actor kasus M02: repeated collision beyond three attempts denies. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M02.04.v002 | Fixture/actor kasus M02: repeated collision beyond three attempts: no partial issuance. | UAT:105 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M03.02.v001 | Fixture/actor kasus M03: referenced user deletion rejected and reservation retained. | UAT:111 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M04.01.v001 | Fixture/actor kasus M04: different explicitly configured fresh DB/issuer namespaces isolate mappings. | UAT:117 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M04.03.v001 | Fixture/actor kasus M04: cross-instance uniqueness requires operational evidence, not inference from DB constraint. | UAT:117 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M05.03.v001 | Fixture/actor kasus M05: installed registry: prove actual ACL boundary. | UAT:123 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M05.03.v002 | Fixture/actor kasus M05: installed registry: prove actual record-rule boundary. | UAT:123 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M05.03.v003 | Fixture/actor kasus M05: installed registry: prove actual sudo boundary rather than view inspection. | UAT:123 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M06.01.v001 | Fixture/actor kasus M06: authenticated active registered client A issues. | UAT:129 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M06.01.v002 | Fixture/actor kasus M06: signed token client_id is A. | UAT:129 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M06.01.v003 | Fixture/actor kasus M06: RS verifies with explicitly bound issuer/user/audience trust. | UAT:129 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M06.03.v001 | Fixture/actor kasus M06: unrelated legacy path unchanged. | UAT:129 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M08.01.v001 | Fixture/actor kasus M08: explicit RS binding maps verified issuer/sub to intended eligible user. | UAT:141 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M08.03.v001 | Fixture/actor kasus M08: malicious RPC cannot create binding absent existing trust-admin privilege. | UAT:141 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M09.02.v001 | Fixture/actor kasus M09: legacy profile unchanged where not explicitly changed by accepted #79. | UAT:147 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M09.03.v001 | Fixture/actor kasus M09: no claim other feature acceptance. | UAT:147 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| M09.03.v002 | Fixture/actor kasus M09: sibling owners review captured contract evidence. | UAT:147 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I01.02.v001 | Fixture/actor kasus I01: two principals under same issuer have different subjects. | UAT:207 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I01.04.v001 | Fixture/actor kasus I01: approved issuer mapping fixture: keep evidence synthetic. | UAT:207 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I02.01.v001 | Fixture/actor kasus I02: simultaneous same issuer_namespace/principal issuance: one persistent mapping. | UAT:213 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I02.01.v002 | Fixture/actor kasus I02: simultaneous same issuer_namespace/principal issuance: same sub. | UAT:213 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I02.03.v001 | Fixture/actor kasus I02: different issuer/DB isolation verified with separately established namespaces. | UAT:213 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I02.05.v001 | Fixture/actor kasus I02: clone changes tested only with separately approved lifecycle. | UAT:213 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I02.05.v002 | Fixture/actor kasus I02: issuer changes tested only with separately approved lifecycle. | UAT:213 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I03.01.v001 | Fixture/actor kasus I03: authenticated active registered A issues scoped token. | UAT:219 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I03.01.v002 | Fixture/actor kasus I03: signed client_id exactly equals A record. | UAT:219 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I03.01.v003 | Fixture/actor kasus I03: RS validates under matching profile. | UAT:219 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I03.04.v001 | Fixture/actor kasus I03: independent legacy non-RS operation assessed separately. | UAT:219 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I04.03.v001 | Fixture/actor kasus I04: without Owner/sibling-approved compatibility and issuer-model scope, positive issuance is blocked. | UAT:225 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |
| I04.04.v001 | Fixture/actor kasus I04: baseline RS issuer/sub binding alone does not prove issuer issuer/principal uniqueness. | UAT:225 | NOT ASSESSED — belum diverifikasi; seluruh oracle dan prasyarat/observer terkait masih residual. |

### Rekonsiliasi dan gap semantik yang masih terbuka

- Disposisi mencakup 92/92 parent: 43 overlay awal dipertahankan tanpa perubahan; 49 ditelaah pada lampiran ini. Ini bukan sertifikasi kelengkapan semantik 43 overlay awal.
- Overlay awal mengakui sendiri kombinasi/varian yang belum ditelaah independen; termasuk C03.01/C03.02, actor/operasi M05.01, dan varian yang merujuk kasus kolektif. Tidak menganggapnya lengkap hanya karena memiliki ID anak.
- C06.04 merujuk kasus legacy cache tanpa enumerasi di baris C06; daftar pastinya harus ditelusuri ke UAT yang relevan. T01.01 merujuk setiap entry point fresh yang diizinkan tanpa menamainya; inventaris/disposisi entry point tetap diperlukan.
- C03.03/M06.03/M09.02 dan T01.04/T04.03 mengandalkan batas baseline/pengecualian accepted atau karakterisasi legacy yang belum diidentifikasi secara lengkap. T06.01–02 dan T02.02 memerlukan inventaris, batas migrasi dan keputusan terpisah; tidak menyiratkan persetujuan.
- M04.01/I02.03 tidak membuktikan keunikan lintas instance hanya dari constraint; I04.04 membedakan binding RS dari uniqueness issuer. M05.03 tetap memerlukan registry dan batas ACL/record-rule/sudo aktual.
- Tidak ada bukti runtime baru; semua anak baru NOT ASSESSED. Fresh mapping/profile scope tetap PENDING, positive issuance terkait BLOCKED dan SCOPE-01 OPEN; tidak ada klaim PASS UAT penuh.
