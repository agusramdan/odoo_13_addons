ADDONS13-46 — UAT DRAFT — revisi Analis Step 0 setelah v4

Issue UUID: 0932b9ca-60ee-44b7-8c88-3e98a173b15b
Scope: hanya amr_resource. Referensi [PRD](PRD-DRAFT.md), [addendum keputusan desain D-01–D-11 berdasarkan delegasi Owner](DECISION-ADDENDUM-OWNER-DELEGATED-ANALYST-01.md), [inventaris](SOURCE-INVENTORY.md), [laporan](ANALYST-REPORT.md), [manifest](RESULT.json).
Expected results untuk keputusan D-01–D-11 harus dibaca bersama addendum keputusan; nilai di sana adalah baseline desain, bukan hasil test atau approval gate. Actual test tetap NOT RUN.
acceptance=false
step0_gate=PENDING_ANALYST_DELIVERED_LEAD_REVIEW_REQUIRED
development_authorization=NOT_GRANTED; test_authorization=NOT_GRANTED

1. Makna dan prasyarat

Ini rancangan kasus acceptance dan unit coverage, bukan hasil UAT/test. Kasus lama in-scope dipertahankan ID-nya; ID lintas-addon lama tidak digunakan kembali. Tambahan hanya memperbaiki gap migration/profile/standalone-JWKS/runtime evidence. Tidak ada file test produk dibuat atau kasus dieksekusi.

Semua D-01..D-11 merujuk keputusan baseline yang dirinci pada PRD addendum, bukan keputusan Owner yang sudah dibuat atau Lead acceptance. Implementasi harus mengikuti baseline addendum; setiap perubahan memerlukan revisi PRD/UAT sebelum coding. Sebelum menjalankan Step 3: Step 1 selesai, kandidat final dibekukan, Step 2 unified Code Review diterima, target QA/runtime/DB/cleanup dan authorization runtime/UAT tersedia. Stored Python tidak boleh di-enable dari rancangan ini; candidate-bound manual Security adalah komponen Step 2, bukan gate Security tersendiri.

Rencana target: Odoo 13 / Python 3.7.9 sesuai baseline D-10 addendum. Runtime/executable/DB belum diperiksa. Default QA adalah target terisolasi yang ditetapkan Lead/Owner sesuai canonical workflow; tidak ada private endpoint/credential dicantumkan dan tidak ada target diakses.

Unit plan:
  Developer/user di Step 1 memanggil metode kandidat asli (bukan salinan/reimplementasi algoritma). Spy boleh merekam urutan; mock hanya external HTTP/JWKS/key-provider/ORM/clock/cache/request boundary atau dependency yang secara eksplisit di luar metode yang sedang diuji. Jangan mengganti trust lookup/validation/resolution yang merupakan subject of assertion dengan stub sukses.
  Gunakan issuer/token/claims/user sintetis; endpoint reserved .invalid; jika unit kriptografis dibutuhkan, key hanya sintetis ephemeral in-memory, tidak membuka private-key file. Mock network tetap closed. Boundary-mocked sequence case tidak membuktikan signature library bekerja; crypto-backed positive/negative vector terpisah dalam UAT-06 wajib direncanakan pada versi library yang dipin.
  Guard DNS (termasuk resolver), socket, requests, redirects dan PyJWKClient transport serta file/env access tak disetujui. Tidak ada real HTTP/DNS. Patch logger agar tidak menyimpan payload/token; unexpected egress atau raw-token evidence adalah blocker. Zero network wajib diukur, bukan hanya diasumsikan karena requests dimock.
  Suite aktual target memakai SavepointCase dan registry/DB. Jangan menjalankannya melalui perintah unittest standalone rekaan. Jika Developer merancang pure unit harness baru, verifikasi ia benar memanggil candidate method dan mencatat batas mock; itu tidak mengganti integration suite Odoo.

Runner: semua per-case adalah planned test identifiers, bukan nama test yang sudah ada. Tidak dituliskan command executable fiktif. Developer/Tester wajib memilih actual approved runner setelah runtime/module/candidate authorized, lalu merekam executable, version, cwd yang disanitasi, command, exit, counts dan test-file digest. Invocation hanya dibuat saat prasyarat itu terpenuhi; status saat ini tetap NOT RUN.

2. Cases

CASE UAT-01 — unknown issuer pada non-HS validation
AC: AC-01, AC-09
Target/method: actual ResourceHelper.validate non-HS dan actual trust lookup kandidat; unit otomatis Step 1, replay Step 3 oleh Tester.
Decision dependencies: D-01, D-02.
Data/prasyarat: missing/malformed/unknown/inactive/ambiguous issuer, synthetic parseable JWT header/payload; mocked ORM registry dan transport closed.
Langkah: panggil validate untuk tiap fixture, spy DNS/socket/Discovery/JWKS/introspection/token endpoint; cek tidak ada resolver dipanggil.
Expected: reject deterministik sebelum outbound; nol semua egress dan resolver. Algorithm/type sesuai profil final, tidak disamakan dengan semua access token.
Actual: NOT RUN

CASE UAT-02 — HS/introspection issuer trust dan activity
AC: AC-01, AC-09, AC-11, AC-12
Target/method: actual validate_hs → introspect_token; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-01, D-02, D-04.
Data/prasyarat: HS synthetic input, absent/unknown/inactive registration; trusted response active True/False/missing/string serta issuer/aud/azp/time variants final profile.
Langkah: invoke actual methods; assert unknown zero requests; trusted metadata/endpoint boundaries return fixtures; mutate each required claim/activity field.
Expected: no credential/token leaves for unknown profile; active response bukan pengganti accepted claim policy. Semua invalid type/required claim gagal sesuai keputusan; resolver tidak dipanggil sebelum validasi lengkap. Tidak menganggap generic truthiness active sudah disetujui.
Actual: NOT RUN

CASE UAT-03 — Discovery mode dan metadata equality
AC: AC-02, AC-05
Target/method: actual get_oidc_config dan profile endpoint selection; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-02, D-03.
Data/prasyarat: registered .invalid issuer; exact/mismatched/missing metadata issuer, malformed JSON/object, absent endpoint.
Langkah: invoke actual method; mock HTTP responses, endpoint fetch spy; repeat variants.
Expected: hanya valid schema dan exact issuer diteruskan; mismatch/schema error berhenti sebelum mengikuti endpoint atau resolver, tanpa silent fallback; bounded transport policy berlaku.
Actual: NOT RUN

CASE UAT-04 — static generation dan wrappers
AC: AC-01, AC-02, AC-04, AC-05
Target/method: actual generate_token/encode; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-01, D-02, D-03, D-11.
Data/prasyarat: trusted static profile/token endpoint, aliases iss/issuer/issuer_url, credential references sintetis lengkap/parsial, unknown/absent/conflicting selector.
Langkah: invoke generate_token dan encode; Discovery guard gagal bila dipanggil; mock token response serta HTTP/JSON failure; inspect safe structural call attributes tanpa credential dump.
Expected: static zero Discovery, untrusted zero outbound, aliases/credential method mengikuti accepted contract (baseline precedence tidak diam-diam diubah). Generate JSON dan encode access_token shape/error mapping sesuai D-11. Tidak melakukan user resolution atas token yang baru diminta.
Actual: NOT RUN

CASE UAT-05 — introspection static, direct url dan opaque token
AC: AC-01, AC-02, AC-04, AC-05
Target/method: actual introspect_token; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-01, D-02, D-03, D-11.
Data/prasyarat: static endpoint, untrusted override URL, caller iss conflict, synthetic opaque value dan explicit trusted profile selector; GET-body legacy dan proposed transport hanya setelah diputuskan.
Langkah: invoke actual method per branch; Discovery mock harus nol untuk static; track destinations/auth and error mapping.
Expected: arbitrary url tidak bypass trust/policy; opaque token hanya diproses bila supported profile+trusted selector tersedia, selain itu reject sebelum parse/network; no automatic fallback. Transport method/body/credential behavior eksplisit D-03, bukan anggapan POST sudah diimplementasikan.
Actual: NOT RUN

CASE UAT-06 — signature, key dan required claim validation
AC: AC-01, AC-02, AC-10, AC-11, AC-12
Target/method: actual validate dan key/profile selection; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-01, D-03, D-04.
Data/prasyarat: allowed/disallowed algorithms/key types/kid, valid/invalid signature synthetic vectors, selected profile JWKS; expired/missing exp, future nbf/iat, clock leeway edges, wrong issuer/aud/azp dan malformed header/alg.
Langkah: a) boundary-mocked sequence assertions dan actual method error handling; b) actual JWT library verification pada pinned version dengan ephemeral synthetic keys dan mocked transport/key distribution, jangan mock signature success untuk b); c) invalid claim vectors harus menahan resolver.
Expected: hanya RS256 dengan RSA key dari JWKS profile yang lolos; wajib `typ=at+jwt`, `iss`, `aud`, `exp`, `iat`, `jti`, `sub`, `client_id`; `exp` belum lewat, `iat` tidak di masa depan, `nbf` bila ada sudah berlaku, leeway 0. Algoritma/key type lain ditolak. Resolver tidak dipanggil untuk signature/claim invalid. Library verification dan mocked sequencing dilaporkan terpisah.
Actual: NOT RUN

CASE UAT-08 — local classification base helper saja
AC: AC-03
Target/method: actual is_local_issuer/is_local_token dan profile lookup amr_resource; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-02.
Data/prasyarat: configured local issuer sama/berbeda web.base.url, trailing slash variant, unknown/missing iss dan forged signature synthetic input.
Langkah: invoke classification, bandingkan exact selected rule; count outbound dan pastikan classification tidak memanggil resolver atau menghasilkan principal.
Expected: classification konsisten registered rule; unknown sesuai D-02; zero network. Classification True bukan signature acceptance. Tidak invoke amr_token atau mengklaim local round-trip kompatibel.
Actual: NOT RUN

CASE UAT-09 — in-addon consumer contract dan auth precedence
AC: AC-04, AC-12
Target/method: actual _auth_method_machine/_params/_user_or_param, ResUsers.decode dan with_access_token_context; unit contract otomatis Step 1/replay Step 3.
Decision dependencies: D-01, D-05, D-06, D-11.
Data/prasyarat: synthetic valid/invalid profiles/users; mocked request/session/core auth/ORM/transport; same-UID dan changed-UID, session success/failure, params failure/bearer fallback.
Langkah: invoke actual consumer bodies dengan real helper validation/resolver chain untuk assertions terkait chain; jangan mengganti helper lengkap dengan selalu-sukses mock. Exercise invalid token/no user/errors, decode same/different user, validate=False request payload dan marked-context branch.
Expected: precedence session → bearer → explicit params. Valid session remains accepted; invalid presented bearer rejects without parameter fallback; params are considered only when bearer is absent and their own validation succeeds. Return/error contract dan same-UID metadata mengikuti D-11; session success bukan bukti token accepted. Runtime registry/MRO tetap UAT-29.
Actual: NOT RUN

CASE UAT-12 — endpoint, redirects, DNS, timeout dan credential policy
AC: AC-05
Target/method: actual endpoint validator, HTTP dispatch dan PyJWKClient boundary kandidat; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-03.
Data/prasyarat: invalid scheme/port/origin, allowed endpoint, redirect allowed→disallowed, DNS/public→private classification fixtures, loopback/private policy exceptions, timeout/oversized response/HTTP/JSON failure; no actual DNS.
Langkah: invoke setiap outbound path (metadata, token, introspection, direct JWKS, PyJWKClient); transport records structural destination and flags, not secret values; simulate redirect and DNS change; instrument limits.
Expected: denied sebelum token/credential dikirim; permitted call memakai HTTPS/TLS verify, connect 3s/read 5s/total 8s, no retries, max 1 MiB, no redirects, DNS/address revalidation dan no credential forwarding lintas-origin sesuai D-03 addendum; error sanitized. Tetap NOT RUN sampai kandidat dan runtime QA diotorisasi.
Actual: NOT RUN

CASE UAT-14 — cache/config restore simulation
AC: AC-06
Target/method: actual profile selection/config invalidation/cache adapter kandidat; unit otomatis Step 1/replay Step 3, bukan runtime rollback.
Decision dependencies: D-02, D-09.
Data/prasyarat: synthetic old/new issuer+policy/endpoint/credential-ref/key revisions dan fake clock/cache; jika addon tidak memiliki cache, dokumentasikan no-cache dan isolate actual library caching boundary.
Langkah: populate entry/profile A, switch revision/profile B, rotate kid/credential reference, expire/negative-cache cases, restore accepted old config tuple; invoke real helper routes each step.
Expected: tidak ada cache addon/library untuk token, introspection, metadata atau JWKS; cache PyJWKClient/helper dinonaktifkan. Tidak ada reuse lintas profile/revision. Mock restore tidak membuktikan recovery DB/deployment.
Actual: NOT RUN

CASE UAT-15 — candidate scope dan evidence/harness safety
AC: AC-07, AC-08
Target/method: candidate delta allowlist dan actual unit harness; static/manual + automated evidence checks Step 1, reviewer repeats Step 2, Tester verifies Step 3.
Decision dependencies: E-01, D-10.
Data/prasyarat: authorized future candidate/base/test digest; explicit amr_resource-only changed-path allowlist; harness sentinels untuk DNS/socket/HTTP/file/env/logger.
Langkah: scope diff review tanpa mutation; guard violation harus fail; inspect tests memanggil actual candidate methods bukan duplikat; match result count, SHA dan mock boundaries; lihat Step 2 required review evidence, jangan jalankan Semgrep di Step 0 ini.
Expected: tidak ada edit addon lain, route Discovery/metadata atau service cache; no network/secret file/token log; actual evidence bound candidate+test hashes. Structural harness check bukan product/security PASS.
Actual: NOT RUN

CASE UAT-16 — registry lookup exact dan active
AC: AC-01, AC-09
Target/method: actual candidate registration lookup; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-02, D-08.
Data/prasyarat: fixtures exact/missing/inactive/duplicate/archived rows, malformed issuer, case/trailing slash variants.
Langkah: call actual lookup via validators, verify deterministic rejection and zero egress on invalid fixture; ensure no create-from-token operation.
Expected: hanya satu exact active registration yang diterima sesuai chosen cardinality; ambiguous fixture tidak dipangkas limit=1. DB uniqueness enforcement bukan mock proof, ditunda UAT-24.
Actual: NOT RUN

CASE UAT-17 — multiple audience child rows dan token-type semantics
AC: AC-10
Target/method: actual audience/profile validation; unit otomatis Step 1/replay Step 3.
Decision dependencies: E-02, D-01, D-04.
Data/prasyarat: two child audience values; aud string/list, one/all/none match, missing/empty/duplicate/non-string/nested types; separate accepted token-type fixtures.
Langkah: invoke actual validators untuk setiap profil dan vector; mutate issuer with same audience; check no web.base.url inference.
Expected: child rows mendukung multiple values; `aud` berupa string/list string valid dan sekurangnya satu exact match (ANY). Missing/empty/non-string/nested reject; audience tidak menggantikan issuer trust.
Actual: NOT RUN

CASE UAT-18 — optional azp per profile
AC: AC-11
Target/method: actual authorized-party claim checks pada accepted token validators; unit otomatis Step 1/replay Step 3.
Decision dependencies: E-03, D-01, D-04.
Data/prasyarat: absent/exact/wrong/empty/non-string azp, configured value absent/single/multiple sesuai D-04; access/ID/introspection classes hanya bila accepted.
Langkah: combine aud cardinality dan token type; invoke validation; inspect resolver ordering.
Expected: `azp` boleh absen bila profile mengizinkan; bila hadir harus satu string nonempty exact-match nilai konfigurasi tunggal. Konfigurasi/claim invalid ditolak. ID Token tidak diterima untuk resource authentication.
Actual: NOT RUN

CASE UAT-19 — identity collision dan issuer binding
AC: AC-12, AC-16
Target/method: actual selected identity resolver; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-05.
Data/prasyarat: same sub across two issuers, colliding email/login users, differing email trust evidence dan unmapped subject.
Langkah: validated synthetic contexts masuk resolver; bila issuer_subject mode dipilih assert pair isolation; bila legacy dipilih assert exact explicit ambiguity/email policy; do not create binding from untrusted input.
Expected: hanya exact unique `(issuer, sub)` binding yang resolve; email/login fallback, auto-binding, dan `limit=1` ambiguity masking dilarang. Unbound subject, collision, duplicate binding, or inactive user reject; no resolver mode fallback.
Actual: NOT RUN

CASE UAT-20 — fixed user eligibility dan ordering
AC: AC-12, AC-13
Target/method: actual fixed-user resolver dan entry chain; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-06.
Data/prasyarat: allowed fixed reference, archived/deleted/disallowed/high-privilege/company-mismatch fixtures sesuai final policy; arbitrary claim uid; invalid issuer/signature/time/aud/azp.
Langkah: invoke actual auth chain; resolver spy hanya observe, tidak mengganti result validation; repeat invalid token and invalid configured user.
Expected: valid approved profile memilih hanya configured eligible user; invalid token zero resolver invocation; claim uid tidak memilih user; disallowed result reject no mode fallback. Eligibility final harus ditulis sebelum run.
Actual: NOT RUN

CASE UAT-21 — method/model allowlist dan result type
AC: AC-12, AC-14
Target/method: actual resolver dispatcher/result validator dan allowlisted test method; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-06.
Data/prasyarat: approved/unapproved pair, arbitrary private/public method name, exception, no user, many users, wrong model/int/dict/cross-DB-like invalid result.
Langkah: invoke dispatcher after valid/invalid verified-context fixtures; assert dispatch target, uid/context sesuai accepted API; unlisted pair never called.
Expected: actual allowlist enforced; one eligible res.users result only; malformed/ambiguous/error reject, no arbitrary ORM dispatch atau fallback Python/fixed/Default. Product dispatcher tidak dimock untuk membuktikan allowlistnya sendiri.
Actual: NOT RUN

CASE UAT-22 — stored Python context/order/error/audit reference
AC: AC-12, AC-15
Target/method: actual execution adapter dan result validator; controlled unit otomatis Step 1 setelah explicit authorization, replay Step 3 setelah unified Code Review.
Decision dependencies: E-05, D-07, D-08.
Data/prasyarat: benign synthetic code revision+digest, reviewed context specification, denied capability probes yang tidak melakukan I/O, exceptions/wrong returns; invalid token fixtures. Tidak menjalankan arbitrary/untrusted code atau enable fitur dari draft.
Langkah: spy order dan exposed names/context types; use approved benign code only; invalid claim profile must not execute; error/return validator actual; assert referenced revision/digest/actor metadata structurally without storing code/token.
Expected: v1 stored Python execution is disabled; adapter must not execute stored code in either valid or invalid-token path. Fixed-user/allowlisted resolver only. Re-enabling requires separate Owner authorization and candidate-bound unified Code Review; unit result does not assert sandbox safety.
Actual: NOT RUN

CASE UAT-23 — no-fallback dan eligible-single-user untuk semua mode
AC: AC-12, AC-13, AC-14, AC-15, AC-16
Target/method: actual resolver chain dan consumer adapters; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-05, D-06, D-07, D-11.
Data/prasyarat: tiap selected mode menghasilkan zero/multiple/archived/disallowed users atau error; machine inactive explicit policy; same UID and context payload provenance fixtures.
Langkah: inject only external ORM/code-call boundary responses, invoke actual dispatcher/result validator/auth consumer; observe no second resolver mode; test bad token zero all modes.
Expected: exactly one permitted user atau explicit failure; limit=1 tidak dijadikan uniqueness proof. Policy inactive machine final, bukan otomatis baseline dipertahankan atau tightened. Auth-source precedence dipisah dari no resolver-mode fallback.
Actual: NOT RUN

CASE UAT-24 — Odoo registry, constraints, ACL/RPC dan UI/code audit
AC: AC-09, AC-10, AC-15, AC-17
Target/method: real candidate ORM/registry/views/RPC dalam disposable isolated Odoo 13 QA; integration otomatis + manual reviewed evidence, Step 3 oleh Tester.
Decision dependencies: D-02, D-07, D-08, D-10; Step 2 sudah diterima.
Data/prasyarat: authorized DB/runtime/module matrix, role fixtures approved trust admin/code editor/internal/portal/public, synthetic issuer/audience/code revisions; runner+cleanup accepted.
Langkah: install/upgrade; enforce issuer and issuer-audience constraints, child cascade; exercise parent/child CRUD/read, code read/write/activate per role via ORM DAN RPC, row/company restrictions; inspect rendered Default label and actual selection key; edit code revision/audit capture then enforce approved activation/review policy. No production access.
Expected: `group_oidc_trust_admin` and `group_oidc_code_admin` are separate; no public/portal/general-user CRUD/read; company-scoped records and field/RPC guards are enforced beyond view visibility. Stored Python remains non-executable in v1. Exact resolver key/label; actual audit/revision evidence.
Actual: DEFERRED / NOT RUN

CASE UAT-25 — get_user_match pilihan Default tanpa asumsi preselection
AC: AC-12, AC-14, AC-16, AC-17
Target/method: actual choice declaration/adapter dan get_user_match; unit contract otomatis Step 1/replay Step 3, rendering UAT-24.
Decision dependencies: E-04, D-05, D-06.
Data/prasyarat: selection key get_user_match; exact label Default; email-first/sub/login fixtures, multiple matches, machine inactive, no result/invalid token; new/existing record selection defaults sesuai keputusan.
Langkah: inspect selection contract then invoke actual method after verified context; assert ordering, ambiguity/eligibility handling outside limit=1 if needed. Preserve characterization baseline separately from new expected assertions.
Expected: option available dengan key/label tepat; preselection tidak ditebak. Email/subject precedence dan ambiguity/inactive behavior persis policy accepted; single permitted result/no implicit fallback. Invalid token tidak reaches method.
Actual: NOT RUN

CASE UAT-26 — config migration dan legacy fallback disposition
AC: AC-06, AC-09, AC-16, AC-17
Target/method: actual candidate migration/config selection adapter dan user-binding migration jika dipilih; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-02, D-05, D-08, D-09.
Data/prasyarat: legacy amr_resource.issuer/audience berisi KEY references (bukan literal URLs), missing referenced key, fallback web.base.url, empty values, existing records/conflicts dan duplicate child/bindings.
Langkah: invoke migration plan/apply adapter atas mocked persistence; ulang untuk idempotence; simulate conflict/failure/restore; inspect preselection/mapping disposition, no real DB.
Expected: tidak silently reinterpret parameter key sebagai URL; exact versioned migration report/action, idempotence/no duplicate trust rows; invalid/conflicting config rejected/resolved hanya via recorded policy. User identities/code privileges tidak diperluas diam-diam. Real DB migration/restore UAT-29, bukan unit proof.
Actual: NOT RUN

CASE UAT-27 — token profile per consumer dan payload provenance
AC: AC-04, AC-08, AC-12
Target/method: actual public helpers + in-addon consumers pada PRD bagian 5; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-01, D-10, D-11.
Data/prasyarat: explicit accepted/rejected token classes tiap consumer, opaque/local/ID/access/introspection fixtures; signed-profile mismatch, already-marked context, untrusted dict dan stale request payload.
Langkah: iterate matrix tiap operation, invoke real method/adapter; verify no reimplementation shortcuts; exercise get_uid/is_user_match direct payload-only entry, validate=False and context marker branch according to accepted provenance rule.
Expected: all matrix entries have explicit accept/reject/provenance behavior, unsupported class rejected; tidak menganggap every helper call revalidates token atau setiap session needs token. Payload tidak menjadi verified principal hanya karena caller memasukkan dict/marker. Signature/return changes harus accepted; otherwise block, not improvise.
Actual: NOT RUN

CASE UAT-28 — standalone JWKS helper tidak bypass trust
AC: AC-01, AC-02, AC-05
Target/method: actual get_jwks_data dan its transport/profile adapter; unit otomatis Step 1/replay Step 3.
Decision dependencies: D-02, D-03.
Data/prasyarat: known/unknown issuer, static/discovery selections sesuai final API, malformed URI, timeout, wrong endpoint origin, JSON failure.
Langkah: invoke get_jwks_data secara langsung, bukan menganggap validate memanggilnya; spy lookup/destination/timeout/zero egress for invalid inputs.
Expected: public helper sendiri terikat policy; no untrusted well-known URL construction/secret forwarding; failure handling consistent. Base validator PyJWKClient path dinilai terpisah di UAT-06/UAT-12.
Actual: NOT RUN

CASE UAT-29 — effective target HTTP/MRO dan rollback rehearsal
AC: AC-04, AC-06, AC-08
Target/method: candidate amr_resource pada isolated Odoo 13 QA; actual authorized HTTP/registry/cache/migration/restore, Step 3 oleh Tester bersama operator QA berwenang.
Decision dependencies: D-02, D-09, D-10, D-11; Step 2 diterima dan runtime+rollback rehearsal scope separately authorized.
Data/prasyarat: exact candidate/runtime/dependency/module install matrix, disposable DB/storage, synthetic config/code revisions and approved endpoints, known-good rollback tuple+cleanup. No route Discovery provider changes, no production.
Langkah: verify actual module list dan effective helper MRO tanpa mengklaim addon lain kompatibel; exercise in-scope HTTP auth/session/params/bearer success/failure/role cases and same-UID metadata; run install/upgrade/versioned migration, change profile/cache across QA workers, restore known-good code/config/schema/reference tuple, replay in-scope probes; read back cleanup/restoration.
Expected: actual target/effective path matches bounded amr_resource contract; jika override mengambil alih behavior, evidence limitation/dependency dicatat dan tidak diklaim base-unit fix menyelesaikan cross-addon flow. Runtime/ACL/HTTP/restore assertions dan exact evidence tersedia; code-only rollback yang kembali gagal Discovery bukan success. Rehearsal QA bukan deployment/production rollback proof.
Actual: DEFERRED / NOT RUN

3. Trace AC → UAT (reverse trace ada pada setiap case)

AC-01 -> UAT-01, UAT-02, UAT-04, UAT-05, UAT-06, UAT-16, UAT-28
AC-02 -> UAT-03, UAT-04, UAT-05, UAT-06, UAT-28
AC-03 -> UAT-08
AC-04 -> UAT-04, UAT-05, UAT-09, UAT-27, UAT-29
AC-05 -> UAT-03, UAT-04, UAT-05, UAT-12, UAT-28
AC-06 -> UAT-14, UAT-26, UAT-29
AC-07 -> UAT-15
AC-08 -> UAT-15, UAT-27, UAT-29
AC-09 -> UAT-01, UAT-02, UAT-16, UAT-24, UAT-26
AC-10 -> UAT-06, UAT-17, UAT-24
AC-11 -> UAT-02, UAT-06, UAT-18
AC-12 -> UAT-02, UAT-06, UAT-09, UAT-19, UAT-20, UAT-21, UAT-22, UAT-23, UAT-25, UAT-27
AC-13 -> UAT-20, UAT-23
AC-14 -> UAT-21, UAT-23, UAT-25
AC-15 -> UAT-22, UAT-23, UAT-24
AC-16 -> UAT-19, UAT-23, UAT-25, UAT-26
AC-17 -> UAT-24, UAT-25, UAT-26

4. Status summary dan kriteria verdict nanti

SUMMARY_CASES=25
SUMMARY_NOT_RUN=23
SUMMARY_DEFERRED_NOT_RUN=2
SUMMARY_EXECUTED=0
Deferred cases: UAT-24, UAT-29. Semua case lain NOT RUN. Tidak ada PASS/FAIL/SKIP/waiver/actual run diciptakan. Pemeriksaan dokumen dalam laporan/RESULT bukan case execution.

Pass nanti hanya bila seluruh expected yang sudah dibekukan dalam policy accepted terbukti pada actual candidate+target tepat. Fail bila assertion produk melanggar expected; blocked bila policy/runner/runtime/authorization/evidence wajib belum ada; NOT RUN tetap bukan PASS. Pertahankan actual raw disposition secara tersanitasi, jangan ubah hasil gagal menjadi lulus. Waiver hanya per canonical policy oleh role berwenang, tidak diciptakan Analis.

5. Evidence template dan batas keamanan

Per run wajib: issue/case+AC IDs, accepted PRD/UAT hashes, candidate branch/SHA/content digest, test-file digest, stored-code/config revision digest (tanpa kode/raw secret), runtime/library/module matrix, actor/role, gate, safe target identifier, mock boundaries, exact authorized command (sanitized jika mengandung input sensitif), expected/actual, exit/counts, evidence path dan cleanup/readback. Product logs/token/credentials/private endpoints tidak disalin. Simpan metadata error class/reason, bukan raw token/error dump.

Unit Step 1 milik Developer/user; UAT Step 3 milik Tester yang ditunjuk Lead, bukan acceptance Lead oleh Analis. UAT-24/29 perlu Odoo registry/ACL/HTTP/DB/runtime dan rollback rehearsal authorization terpisah. External issuer/production rollout/rollback tidak diotorisasi. Module override/sibling compatibility ada di issue scope masing-masing, bukan deferred compatibility acceptance task ini.

Stored Python wajib manual Security review pada exact candidate dan exact stored-code/context/config revision di dalam SATU gate Code Review Step 2 dengan independent Code Reviewer dan evidence Security contributor. Semgrep offline dan review umum ikut gate yang sama. Tidak ada verdict Security terpisah; unit/UAT PASS tidak membuktikan arbitrary stored code aman atau menerima residual risk. Perubahan code/revision/context memerlukan disposition kandidat dan review ulang sesuai canonical workflow.

6. Perbaikan terhadap UAT v4

v4 sudah memiliki 21 case in-scope, seluruhnya belum dijalankan. Revisi ini menambah UAT-26 migration, UAT-27 token-profile/provenance, UAT-28 standalone JWKS, UAT-29 effective runtime/HTTP/restore plan. v4 planned unittest commands tidak diteruskan sebagai command yang seolah siap: suite aktual adalah SavepointCase dan runner baru belum ada. Perbandingan ini menggambarkan revisi saat UAT-DRAFT dibuat: saat itu ANY audience masih diperlakukan sebagai belum diputuskan. Pada revisi berjalan, pilihan ANY dan keputusan D-01–D-11 ditetapkan oleh addendum keputusan; UAT tetap belum dieksekusi. Referensi D-03/D-04 v4 yang tidak menunjuk decision table konkret diganti dependency IDs PRD yang eksplisit. Jalur HS, opaque tokens, required claims/time/alg policy dan boundary crypto mocks diperjelas. Source-only consumers dan amr_token/amr_oidc/service-client tetap dikeluarkan, tanpa case execution/compatibility claim lintas-addon.
