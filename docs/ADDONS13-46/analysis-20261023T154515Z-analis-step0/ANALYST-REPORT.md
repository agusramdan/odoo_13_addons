ADDONS13-46 — Laporan Analis Step 0

Issue: ADDONS13-46
UUID: 0932b9ca-60ee-44b7-8c88-3e98a173b15b
Output: /home/ubuntu/docs/reports/ADDONS13-46/analysis-20261023T154515Z-analis-step0/
Role: Analis, bukan Lead acceptance, Owner policy authority, Developer, Tester atau Security gate.
acceptance=false
step0_gate=PENDING_ANALYST_DELIVERED_LEAD_REVIEW_REQUIRED
development_authorization=NOT_GRANTED
test_authorization=NOT_GRANTED
Scope: amr_resource saja. Plane tidak dibaca/diubah; current state UNKNOWN dalam pekerjaan ini.

1. Deliverables dan integritas

[PRD-DRAFT.md](PRD-DRAFT.md)
SHA-256: 74bf2788c0ccecdf79d6e368004ec86bc6c69682cac374b7438d019f8fd3a42b
Masalah/tujuan/pengguna, facts, keputusan E vs D, matriks profil per entry point, model/API usulan, AC, risiko dan evidence lifecycle.

[UAT-DRAFT.md](UAT-DRAFT.md)
SHA-256: 6d1f14f5c59fe77c22b56840f63d58d4d8d9979b59709b740cfb811d4ba4b688
Kasus dengan setup/langkah/expected/actual, unit-vs-runtime boundaries, trace dua arah dan peran/gate. 25 unique cases; 23 NOT RUN dan 2 DEFERRED / NOT RUN. Actual executions nol.

[SOURCE-INVENTORY.md](SOURCE-INVENTORY.md)
SHA-256: 3b9f0cef9a13c8e13ff4f8e250e2d670672dcfcdf06daa8d2984fcde9d094809
Pinned roots, 21 row hash file addon, verified call-path F-01..F-14, tests actual definitions, module matrix dan limitations.

[ANALYST-REPORT.md](ANALYST-REPORT.md) adalah dokumen ini. Hash aktualnya dicatat di [RESULT.json](RESULT.json) setelah bytes report final, bukan self-hash rekursif dalam report.
RESULT.json adalah manifest baru yang mengikat empat dokumen final, pemeriksaan aktual dan preservasi historis. Manifest tidak menyimpan hash dirinya sendiri; SHA-256 RESULT.json dihitung terpisah dalam verifikasi akhir/final response agar tidak ada circular hash claim. Tidak menyimpan source/log dump.

2. Identitas source/target dan guard Git

Awal DAN akhir pemeriksaan snapshot:
  Source: /home/ubuntu/worktrees/ADDONS13-39-SOURCE
  HEAD: 6725f802acde636be0b25e2c140d15dccd37b0db
  Status: clean; porcelain stdout kosong; cocok expected.
  Target: /tmp/ADDONS13-46-target-main
  HEAD: dae519f29e9c4709dc04796b38148b00d333c58b
  Status: clean; porcelain stdout kosong; cocok expected.

Setiap Git subprocess sejak probe pertama dipasok GIT_NO_LAZY_FETCH=1 GIT_TERMINAL_PROMPT=0 GIT_OPTIONAL_LOCKS=0. rev-parse HEAD/status pada kedua root exit 0; ls-tree lokal dan cat-file batch-check memastikan scoped addon text blobs source 15/target 21 tersedia lokal. Tidak ada indikasi missing object/fetch atau retry unguarded. Tidak fetch/ls-remote, tidak menyentuh Git/source/tests. Seluruh 15 source addon files identik target; 6 additions target adalah 3 docs dan 3 test-package files. Akhir pemeriksaan juga rehash setiap file addon terhadap baseline, tidak hanya HEAD/status.

3. Temuan sumber bermakna (bukan verdict Security)

Prefiks T: mengikuti root/pin pada inventaris; hash produksi sama dengan S:.

  a. Issuer/config: T:amr_resource/models/helper.py:20-37 memakai parameter-key indirection; local comparison hanya web.base.url; get_audiences tidak memakai issuer. Mengganti config menjadi URL literal tanpa migrasi akan mengubah semantics. Registry baru belum ada dalam deklarasi addon.
  b. Metadata/JWKS path berbeda: T:amr_resource/models/helper.py:40-51 well-known GET helpers; validasi pada :134-142 justru PyJWKClient(metadata.jwks_uri), bukan get_jwks_data. Endpoint/DNS/timeout policy harus mencakup direct helper DAN transport JWK library. Implicit library behavior UNKNOWN.
  c. Generation/introspection: T:amr_resource/models/helper.py:61-73,83-110 bisa memilih metadata dari caller/token iss; direct introspection url bypass Discovery. Introspection nyata di kode adalah GET body data. validate_hs hanya mengecek active truthiness pada cabang lokal. Ini fakta kode, bukan bukti introspection server menerima invalid token.
  d. Signature/claim: T:amr_resource/models/helper.py:114-149 memakai header alg sebagai algorithms=[alg], issuer dari payload yang juga memilih metadata, audience global. Policy token class, alg allowlist dan required time/claims belum eksplisit. Library signature enforcement dipanggil; tidak mengklaim kriptografi dilewati atau exploit terbukti.
  e. Resolution: T:amr_resource/models/helper.py:157-193 email-first lalu sub login, machine include inactive, sudo/limit=1. get_uid/is_user_match tidak validate token sendiri. Default label yang dipilih Owner tidak memutus ambiguity/eligibility atau menyulapnya menjadi issuer-sub binding.
  f. Consumers: T:amr_resource/models/ir_http.py:42-108 memvalidasi lalu mapping; session→params→bearer fallback broad except, request metadata hanya jika UID berubah. T:amr_resource/models/res_users.py:48-55,79-95 payload-only get_uid, validate=False dan context short-circuit perlu provenance rule. No-resolver-mode-fallback berbeda dari existing auth-source fallback.
  g. ACL/access: T:amr_resource/__manifest__.py:9-15 memuat groups/settings/wizard tanpa ACL CSV lokal; T:amr_resource/views/res_config_settings_views.xml:8-30 group visibility bukan backend ACL; registry/ACL efektif UNKNOWN. Baseline T:amr_resource/models/res_users.py:14-26 machine su=True dan T:amr_resource/controllers/main.py:98-106 generic call_kw dicatat tanpa scope rewrite.
  h. Tests actual: T:amr_resource/tests/test_helper.py:11-28 memakai Odoo SavepointCase; :187-224 memock jwt.decode/JWKS, bukan bukti signature verification. T:amr_resource/tests/test_contracts.py:63-140,227-290 direct body/controller calls bukan route/ACL tests. Planned unittest commands v4 bukan runner yang terbukti tersedia.
  i. Baseline raw-token logging: T:amr_resource/models/helper.py:117-121. Risiko baseline dicatat, tidak diam-diam diklaim sudah diperbaiki atau diterima; tidak memakai real token/log.

Inferensi bersyarat: input-derived issuer/endpoint dapat menyebabkan egress dan mungkin token/credential disclosure tergantung caller, config, network dan credentials yang tidak diperiksa. User mapping/fixed user/ORM dispatch/Python dapat memengaruhi principal/privilege. Severity UNASSESSED, exploitability/runtime/installed modules/deployment UNKNOWN. Tidak ada verdict aman.

4. Review substantif v4 dan canonical Step 0

v4 mengandung scope/risiko/AC dan 21 planned cases yang berguna; bukan diteruskan tanpa perbaikan. Perubahan revisi ini:

  1) Manifest historis stale dibuktikan dari actual bytes: hash PRD/UAT/inventory/Lead-analysis berbeda dari entri RESULT.json yang masih berlabel v3. Manifest dan check Lead tidak diedit; keenam file historis di-hash sebelum/sesudah.
  2) Seluruh E yang eksplisit Owner dipertahankan: multiple audience child rows; optional azp per profile dan present match; get_user_match label Default; fixed/method/Python design dan mandatory manual Security di satu Code Review. Scope decisions tidak disetarakan artifact/risk acceptance.
  3) D-01..D-11 konkret menggantikan referensi keputusan D-03/D-04 v4 yang tidak punya tabel ID yang dapat dirujuk. ANY audience, issuer-subject default, method allowlist dan timeout values tetap rekomendasi, bukan policy approved.
  4) Tambah matriks token profile/provenance per operation/consumer, termasuk generation bukan inbound auth, opaque token selector, HS claim/activity gap, signature/time/alg rule, payload-only get_uid dan context bypass semantics.
  5) Pisahkan standalone get_jwks_data dari PyJWKClient path; tambah migration/key-indirection, ambiguity/inactive user, actual ACL/RPC, stored-code revision binding serta cache/library uncertainty.
  6) UAT menambah migration, profile/provenance, standalone JWKS dan effective QA runtime/HTTP/restore cases. Trace AC↔UAT dua arah lengkap; setiap case punya data/langkah/expected/actual/decision/prasyarat/automation/role-gate.
  7) Hapus kesan command test rekaan sudah siap. Existing tests butuh registry/DB SavepointCase; unit baru wajib actual candidate method dengan external boundaries mocked dan no-network guards. Crypto mock sequence bukan crypto verification.
  8) Canonical lifecycle tidak mensyaratkan manual gate Security/dokumentasi/deployment terpisah. Step 0 acceptance milik Lead; Owner memutus kebijakan dan authorization terpisah; stored Python review adalah candidate-bound komponen Step 2, bukan prasyarat fiktif Analis untuk memberi Security PASS sekarang.
  9) Current Plane status tidak diklaim dari historical v4/Lead notes. Transfer amr_token/Discovery/OIDC/service-client/source-only scopes dipertahankan tanpa compatibility/UAT result di issue ini.

Minimum canonical PRD/UAT pada DEVELOPMENT-WORKFLOW.md:124-139 dipenuhi secara struktur: problem/goals/users/flow/scope/requirements/contracts/AC/risks/rollout dan UAT setup/steps/expected/negative/security/automation limitations. Policy yang belum resolved tetap explicit blocker readiness; kelengkapan dokumen bukan acceptance.

5. Keputusan yang masih pending — tidak didelegasikan ke Analis

D-01 token profile/alg/required claims/time/activity per entry point.
D-02 issuer cardinality/trust/exact matching/modes/default/local classification dan legacy migration.
D-03 endpoint scheme/origin/redirect/DNS/TLS/timeouts/retry/credential/direct-url/introspection transport.
D-04 audience matching dan azp per token type/cardinality/config validity.
D-05 identity binding/legacy email, ambiguity/inactive machine, Default preselection dan migration.
D-06 fixed-user eligibility/privilege serta approved resolver API/model-method execution contract.
D-07 stored Python engine/context/capabilities/permissions/audit/revision/activation review policy.
D-08 parent-child/code ACL/row/company/RPC trust boundary.
D-09 cache ownership/TTL/rotation/invalidation/rollback known-good tuple.
D-10 effective target modules/runtime/versions/QA MRO dan bounded compatibility.
D-11 errors/auth-source precedence, same-UID metadata, payload/context provenance dan signature/return compatibility.

Detail opsi/trade-off dan rekomendasi belum disetujui ada pada tabel PRD. No Owner decision dibuat, no risk accepted. Lead harus menilai artefak exact hashes; Owner menyelesaikan policy relevan; Development/test tetap NOT_GRANTED. Tidak meminta atau mengasumsikan token override workflow.

6. Pemeriksaan aktual yang dijalankan

Command/check dicatat sebagai nama/opsi pemeriksaan aman, bukan raw argv/session log:

  Guarded Git rev-parse HEAD; status --porcelain=v1 --untracked-files=normal: kedua root exit 0, pin cocok/clean awal dan akhir.
  Guarded Git ls-tree -r -z HEAD; cat-file --batch-check: scoped 15/21 blobs tersedia; tidak missing/fetch.
  Python standard-library hashlib SHA-256 + ast.parse/literal_eval + pathlib: hash 15 common files sama; target-only additions teridentifikasi; model declarations dan manifest matrix diperiksa tanpa import/exec addon.
  Python regex/sets/Counter doc checks sebelum report: 17 unique AC; 25 unique UAT; exact bidirectional mappings; semua referenced UAT IDs ada; 23 NOT RUN + 2 DEFERRED / NOT RUN (UAT-24/29), executed=0; exit 0.
  Citation range existence check pada PRD/UAT/inventaris: 43 local prefixed citation occurrences valid dalam rentang file; 21 inventory hash rows cocok actual bytes. Ini validitas locator, bukan automated proof kebenaran semantik; call-path di atas ditinjau manual.
  Hash baseline recheck: semua scoped source/target addon files unchanged; semua enam v4/check Lead files unchanged. Historical stale entries empat dokumen terkonfirmasi.
  Final artifact/link/hash/trace/pending-ID/citation/inventory/status checks dan integrity readback RESULT dicatat dalam manifest baru serta final response. Link ke RESULT dievaluasi hanya sesudah file itu dibuat; tidak menganggap dangling link sementara sebagai evidence produk.

Tidak ada unit/test suite dijalankan. Python di atas hanya analisis AST/hash dan validator dokumen, bukan addon runtime atau acceptance test. Tool syntax/lint checks jika ada juga bukan product test.

7. Downstream evidence dan batas klaim

Lead: Step 0 exact-hash review/disposition. Developer/user: Step 1 authorized candidate, actual unit/evidence branch/SHA/test digests. Independent Code Reviewer dengan Security contributor: Step 2 general+manual Security stored Python+Semgrep offline pada exact SHA dan stored-code/context revision, tepat satu verdict Code Review. Tester: Step 3 UAT setelah Code Review dan runtime authorization, isolated QA Odoo 13+approved module matrix, UAT-24/29 registry/ACL/HTTP/rollback rehearsal deferred. Owner: Step 4 same-candidate review/PR_ACCEPT+merge readback; deployment CI/CD di luar checklist dan separately authorized.

Final state pekerjaan ini: Analis menyampaikan draft dan static evidence, bukan Lead acceptance. Unit/registry/ACL/HTTP/runtime/UAT/rollback NOT RUN; no source/tests/Git mutations, no Plane mutations, no network/DB/Odoo/service access, no gateway/profile/config changes, no remote freshness claim. Sumber eksternal v4 tidak diakses; tidak memakai klaim eksternal tak terverifikasi sebagai keputusan baru. Tidak ada provider/gateway blocker yang menghentikan penyusunan artefak lokal ini.
