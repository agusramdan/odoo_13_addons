ADDONS13-46 — PRD DRAFT — revisi Analis Step 0 setelah v4

Issue UUID: 0932b9ca-60ee-44b7-8c88-3e98a173b15b
Scope: hanya addon amr_resource.
acceptance=false
step0_gate=PENDING_ANALYST_DELIVERED_LEAD_REVIEW_REQUIRED
development_authorization=NOT_GRANTED; test_authorization=NOT_GRANTED

Indeks: [UAT](UAT-DRAFT.md), [addendum keputusan desain D-01–D-11 berdasarkan delegasi Owner](DECISION-ADDENDUM-OWNER-DELEGATED-ANALYST-01.md), [inventaris](SOURCE-INVENTORY.md), [laporan Analis](ANALYST-REPORT.md), [manifest](RESULT.json).
Status keputusan: D-01–D-11 dijabarkan dalam addendum sebagai baseline desain konservatif yang dipilih Analis atas delegasi Owner. Itu bukan risk acceptance, Lead acceptance, atau authorization coding/testing. Addendum berlaku sebagai revisi keputusan untuk pembacaan draft ini; acceptance harus terikat pada hash revisi.
Pembanding historis: [PRD v4](../analysis-20261023T141448Z-owner-addon-scope-v4/PRD-DRAFT.md) dan [check Lead](../analysis-20261023T141448Z-owner-addon-scope-v4/LEAD-STEP0-CHECK-20261023T154515Z.md). Tidak ditimpa.

1. Masalah, tujuan, pengguna

Fakta snapshot: helper amr_resource mengambil metadata dari issuer untuk permintaan token, introspection tanpa URL eksplisit, dan validasi JWT non-HS. Issuer pemilih metadata dapat berasal dari caller atau payload yang belum diverifikasi; belum ada model trust registry dalam addon. Lihat F-01–F-07 pada inventaris untuk lokasi dan call-path. v4 melaporkan ketidaksesuaian publikasi Discovery lintas-addon; revisi ini tidak memverifikasi ulang route addon lain atau mengklaim endpoint aktual mengembalikan 404.

Tujuan usulan: membuat pemilihan issuer/profile dan resolver user eksplisit dalam amr_resource, tanpa menerima issuer sebagai otoritas hanya karena token menyebutnya. Mendukung konfigurasi endpoint statis sebagai alternatif Discovery yang tidak memerlukan perubahan route provider.

Pengguna/alur usulan:
  Administrator trust yang disetujui mengelola issuer, audience child rows, policy profil dan resolver. Pengelola stored Python adalah peran privileged terpisah atau subset yang diputuskan Owner.
  Pemanggil helper memilih issuer terdaftar; token input hanya dipakai sebagai kandidat lookup, tidak menjadi izin URL. Setelah validasi token, resolver issuer menghasilkan satu user yang eligible.
  Auth machine/params memakai user teresolusi; user_or_param tetap memiliki cabang session yang harus dibedakan dari autentikasi token. QA/reviewer menilai kandidat, bukan menerima snapshot ini sebagai implementasi.

2. Scope dan batas lifecycle

In-scope rencana: amr_resource helper/config, issuer registry baru, audience dan azp, signature/introspection claim policy pada base helper, local classification base helper, user resolution, in-addon consumers, ACL/views/config/migration, in-addon cache/rollback, test dan dokumentasi kandidat addon. Ini kebutuhan usulan, bukan perubahan source sekarang.

Out-of-scope:
  amr_token generation/validation/introspection/overrides → ADDONS13-38.
  Route dan metadata Discovery → ADDONS13-38/39.
  amr_oidc client token-validation → ADDONS13-48.
  amr_service_client provider/cache → ADDONS13-49.
  amr_auto_login, amr_mobile, amr_oauth, amr_oidc_client, amr_resource_jwt, amr_signature → ADDONS13-50..55 secara berurutan.
Tidak mengubah addon tersebut, menambah klaim compatibility, atau menjadikan keberadaan manifest sebagai installed-module evidence. Ketergantungan gate lintas-issue hanya jika Lead/Owner mencatat kontrak dependency secara eksplisit; tidak otomatis.

Canonical: /home/ubuntu/docs/standards/DEVELOPMENT-WORKFLOW.md:29-43,54-76,124-139,147-153. Analis menyampaikan Step 0; acceptance Step 0 milik Lead. Keputusan scope Owner bukan penerimaan PRD, risk acceptance atau izin implementasi. Development serial: Step 1 Coding termasuk unit aktual dan dokumen kandidat; Step 2 satu Code Review mencakup review umum, manual Security, Semgrep offline; Step 3 automatic UAT; Step 4 Owner review/PR_ACCEPT dan merge readback. Deployment Owner melalui CI/CD di luar gate. Tidak ada gate Security/dokumentasi/deployment tambahan. Tidak ada override atau authorization yang diberikan di sini.

3. Fakta baseline yang memengaruhi kontrak

Lokasi dengan prefiks T: mengacu pada target pin; S: pada source pin (root lengkap pada inventaris). Semua file produksi addon yang ditemukan di source identik byte dengan target.

  Config: T:amr_resource/models/helper.py:20-37 memakai key-indirection dan fallback web.base.url; get_audiences mengabaikan argumen issuer. T:amr_resource/models/res_config_settings.py:9-29,50-66 mendefinisikan selector/preview; view menampilkan audience tetapi bukan selector issuer. View group bukan bukti ACL backend.
  Metadata dan JWKS: T:amr_resource/models/helper.py:40-51 memiliki dua helper GET well-known terpisah. validate justru memakai metadata.jwks_uri → PyJWKClient langsung pada :134-142; tidak memanggil get_jwks_data. Policy transport harus mencakup kedua jalur, bukan hanya requests wrapper.
  Generation: T:amr_resource/models/helper.py:53-73 encode → generate_token → get_oidc_config → requests.post; precedence iss, issuer, issuer_url. Auth tuple hanya jika client_id DAN client_secret truthy. Response JSON dikembalikan, encode mengambil access_token.
  Introspection/HS: T:amr_resource/models/helper.py:83-110 direct url melewati Discovery; tanpa iss membaca payload unverified. GET memakai data access_token, bukan POST atau query params. validate_hs hanya memeriksa truthiness active, tanpa audience/azp/time checks lokal eksplisit pada cabang itu. Perubahan metode transport harus didisposisikan, tidak diam-diam dianggap kompatibel.
  Signature/claims: T:amr_resource/models/helper.py:114-149 membaca alg header, cabang HS via introspection; non-HS mengirim algorithms=[alg], issuer dari payload yang sama, audience konfigurasi global ke jwt.decode. Tidak terlihat allowlist algoritma berbasis profil atau daftar required claims eksplisit. Default/versi library dan time-claim behavior efektif UNKNOWN; bukan bukti signature dilewati atau token kedaluwarsa diterima.
  Local: T:amr_resource/models/helper.py:20-27,76-80 membandingkan iss unverified dengan web.base.url. Classification bukan validasi kriptografis; base validate tidak memiliki local bypass. Efek override addon lain tidak diuji.
  Identity: T:amr_resource/models/helper.py:157-193 email login/email → sub login → cabang machine mencari active True/False; sudo, limit=1. Ini tidak membuktikan uniqueness atau issuer binding. get_uid menerima payload tanpa melakukan validasi sendiri.
  Consumers: T:amr_resource/models/ir_http.py:42-108 get_validate_user → get_user_match; user_or_param mencoba session lalu params lalu bearer dengan broad except. Resolver failure-no-fallback bukan berarti session/params/bearer fallback dilarang; keputusan perubahan auth precedence harus terpisah. T:amr_resource/models/res_users.py:48-55,79-95 decode/context → get_uid; validate=False memakai request payload, context marker dapat short-circuit. Semua entry point perlu provenance contract.

4. Tabel keputusan terbatas

E = keputusan eksplisit Owner dari instruksi/v4, bukan acceptance artefak.
D = keputusan baseline Analis atas delegasi Owner; detail normatif dan batasnya ada pada DECISION-ADDENDUM-OWNER-DELEGATED-ANALYST-01.md. Baris D di bawah mempertahankan pertanyaan/temuan asal sebagai jejak historis dan tidak boleh dibaca sebagai status pending yang mengalahkan addendum.

ID | Status | Isi dan rekomendasi Analis | Kebutuhan keputusan/evidence
E-01 | EXPLICIT_SCOPE_ONLY | Scope hanya amr_resource; transfer sesuai bagian 2. | Bukan compatibility lintas-addon.
E-02 | EXPLICIT_DESIGN_INPUT | Satu issuer dapat memiliki beberapa audience child rows. | Tidak menetapkan ANY/ALL atau issuer cardinality per DB.
E-03 | EXPLICIT_DESIGN_INPUT | azp optional sesuai profil token; jika hadir wajib match nilai yang dikonfigurasi. | Tidak menetapkan cardinality konfigurasi atau aturan per token type.
E-04 | EXPLICIT_DESIGN_INPUT | Resolver key get_user_match tersedia; label UI persis Default. | Bukan persetujuan preselection, email trust, duplicate atau inactive behavior.
E-05 | EXPLICIT_DESIGN_INPUT | fixed user, resolver method/model dan stored python_code masuk desain; Python adalah privileged executable-code. | Candidate-bound manual Security wajib di satu Code Review Step 2; tidak ada risk acceptance.
D-01 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Profil token PER consumer/operation. Rekomendasi deny unsupported token classes, bukan terima ID Token otomatis sebagai resource credential. | Putuskan accepted JWT access/opaque/introspection/local classes, alg allowlist/key type, required claims, exp/nbf/iat/leeway, active boolean semantics, subject/type/scope rules dan credential source. Lihat matriks bagian 5.
D-02 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Trust/cardinality/mode/migration. Rekomendasi exact issuer lookup satu active row, tanpa prefix/normalisasi implisit, no fallback. | Single DB issuer atau multi-issuer; default profile untuk generation/opaque token; alias precedence, konflik argumen, malformed/absent issuer; local classification; migrasi key-indirection dan legacy invalid config. Pilih static/discovery/local capability tanpa mengimplementasikan amr_token.
D-03 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Endpoint/redirect/DNS/timeout/credential policy. Rekomendasi HTTPS+TLS verify, no redirects default, origin allowlist, bounded timeout, no auto credential forwarding. | Skema/port/origin, dev exceptions, private/loopback/DNS rebinding/address validation, redirect revalidation, metadata size, connect/read/total deadline dan retry bounds; PyJWKClient transport; direct url policy; GET-body legacy vs metode introspection baru. Tetapkan nilai limit konkret sebelum coding; tidak diciptakan di Step 0.
D-04 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Audience/azp per token type. Rekomendasi resource ANY-match terhadap child rows untuk access token, strict value types. | ANY/ALL/exact-resource; missing/empty/string/list/malformed aud; nilai azp tunggal vs allowlist, absent/multiple-aud rules per profile, opaque/introspection equivalent. Jangan transplant aturan ID Token ke access token.
D-05 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Identity/default/migration. Rekomendasi binding (issuer,sub), no automatic email collision resolution. | Apakah issuer_subject ditambahkan sebagai mode atau belum; Default dipilih otomatis atau tidak; email verified/trust prerequisites, email-first vs subject-first, ambiguity saat banyak match, machine inactive eligibility dan migration existing bindings. limit=1 tidak cukup untuk kontrak exactly-one.
D-06 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Fixed user dan resolver method. Rekomendasi code-owned allowlist, typed single res.users result; no implicit mode fallback. | Eligible user/group/company, privilege ceiling, deletion/archive behavior, approved model/method pairs, input signature, execution uid/sudo/context, exception normalization. Fixed user tidak boleh dipilih token user-id.
D-07 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Stored Python context/permission/audit. Rekomendasi minimum reviewed context, jangan klaim safe_eval sebagai sandbox. | Engine; env/recordsets/imports/helper functions/writes/network/budget/side effects; edit/read/activate roles; revision digest+actor+time dan audit retention, re-review setiap perubahan code/context. Tentukan prosedur review code DB yang dimuat setelah SHA; candidate harus mengikat exact code revision/config digest juga. Security reviewer memberi evidence, tidak verdict terpisah.
D-08 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Registry ACL dan RPC boundary. Rekomendasi deny non-approved CRUD/read Python, internal field-limited runtime lookup. | Grup parent/child/code, row/company isolation/global issuer uniqueness, RPC enumeration/public method guard dan secret references. base.group_erp_manager pada view tidak otomatis menjadi admin trust/code.
D-09 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Cache dan rollback. Rekomendasi tidak menambah token cache baru tanpa kebutuhan; semua cache aktual harus diinventarisasi termasuk library JWKS. | Metadata/JWKS ownership, TTL/negative-cache/refresh/kid rollover, cache keys(profile+policy revision+endpoint+key/credential reference), revocation/config edit invalidation antar worker; known-good code+config+schema+audit/cache rollback unit. Tidak menyentuh service-client cache.
D-10 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Effective target matrix dan in-addon compatibility. Rekomendasi QA isolated Odoo 13 dengan module list eksplisit. | Pin runtime/dependency versions, module install/upgrade set dan MRO; pastikan hanya base contract diklaim tanpa bypass override addon lain. Python 3.7 dari target AGENTS; 3.7.9 hanya provenance v4, bukan verifikasi runtime/keputusan baru.
D-11 | ANALYST_SELECTED_UNDER_OWNER_DELEGATION | Error/provenance/auth semantics. Rekomendasi preserve signatures/return shapes dan auth precedence kecuali delta disetujui. | Rejection exception per helper, mapping 401 vs error, session-vs-token fallback, same-UID metadata, validate=False/context trust, direct get_user_match/get_uid callers; logging raw-token baseline dipisahkan, bukan dianggap sudah diperbaiki.

5. Matriks profil per operation/consumer — kontrak keputusan ada pada addendum D-01–D-11

Entry point | Fakta saat ini | Usulan boundary dan pilihan pending
validate/decode/get_validate_user | HS introspection; non-HS JWKS dari unverified iss; decode mengabaikan kw saat meneruskan validate | Token type tidak didefinisikan oleh prefix HS; pilih accepted profiles, issuer lookup dan policy. Opaque token perlu trusted selector out-of-band atau ditolak, bukan parsing JWT paksa.
generate_token/encode | caller issuer aliases + Discovery + POST; encode scalar access_token | Trusted profile dari caller/default eksplisit; generation bukan inbound user resolution. Response bukan otomatis verified claims; jenis grant/credential forwarding diputuskan.
introspect_token/validate_hs | direct URL atau iss dari caller/unverified JWT; active truthy | Profile dan endpoint trusted sebelum token/secret keluar; klaim introspection harus punya schema/trust/policy setara token type yang diterima.
is_local_token/is_local_issuer | unverified classification saja | Menghasilkan classification untuk profile terdaftar; tidak pernah menghasilkan accepted principal sendiri.
_auth_method_machine / _auth_method_params | token → validate → match → update uid hanya bila berubah | Token-profile allowlist masing-masing dan user eligibility eksplisit. Parameter-token exposure baseline bukan authorization baru.
_auth_method_user_or_param | session → params → bearer | Session-only success bukan bukti token diterima; putuskan profil hanya untuk cabang token dan disposition broad fallback.
res.users.decode | helper.decode → get_uid → equality user.id | Verified payload provenance harus dibawa ke resolver issuer tanpa mengubah return payload/None tanpa persetujuan.
with_access_token_context | marker short-circuit; validate default True, False memakai request payload | Putuskan trusted marker/request-payload contract; callers tidak boleh menyamakan mapping payload dengan validasi token.
get_user_token_login / get_uid / is_user_match | yang pertama validate; yang lain menerima payload | Pertahankan public signature hanya bila ada internal verified-context boundary yang jelas. Jangan anggap semua pemanggil telah memvalidasi.

6. Model/data dan urutan kontrak — baseline desain pada addendum

Model baru dalam amr_resource: oidc.issuer.register (belum ada dalam deklarasi addon kedua pin). Minimal rancangan: name, issuer exact, active, mode, policy/profile revision, static endpoint fields atau reference, user_mapping_mode, fixed_user_id Many2one res.users, code-owned resolver key/model-method allowlist, python_code beserta revision/audit reference. Untuk D-05 v1, tambahkan binding model `oidc.issuer.subject` dengan `issuer_id`, `subject` exact, `user_id` dan unique constraint global `(issuer_id, subject)`; mapping dibuat administrator lewat alur terkontrol, tidak dari token. Tidak menyimpan secret di artefak/dokumen; credential reference dan aksesnya diputuskan D-03/D-08.

Audience child: oidc.issuer.register.audience; issuer_id Many2one cascade, audience required; audience_ids One2many parent. Unique `(issuer_id, audience)` berlaku termasuk archived records. Issuer registry unik secara global; tidak ada row otomatis dari iss/aud token.

Setiap consumer/operation memakai tepat satu class profil yang dipilih dari konfigurasi issuer; tidak ada token-class auto-detection atau fallback. Baseline JWT/opaque claims dan `azp` mengikuti addendum D-01/D-04. Identity v1 wajib binding exact `(issuer, sub)`.

Urutan inbound baseline:
  a. Parse minimal input dengan size/type bounds; pilih satu trusted active profile (claim hanya lookup hint).
  b. Tolak unknown/inactive/ambiguous sebelum DNS/socket/HTTP/credential/key fetch.
  c. Gunakan hanya endpoint statis dari registry dan transport policy D-03; Discovery dan fallback ke web.base.url/issuer lain tidak digunakan.
  d. Verifikasi signature/key/algorithm atau hasil introspection tepercaya sesuai token profile; required time/issuer/aud/azp dan claims lain harus selesai sebelum resolver.
  e. Dispatch satu resolver yang dipilih issuer; verified claims + internal profile identifier saja, bukan raw token/unverified input. Semua mode menegakkan single eligible res.users atau reject; tidak fallback ke mode lain.
  f. Consumer menerapkan hasil/exception sesuai kontrak yang diterima; tidak mengubah session atau hak superuser secara tersirat.

Resolver API internal menerima verified_claims mapping dan immutable profile/policy identifier; hasil tepat satu `res.users` aktif yang eligible, company-nya mencakup company aktif, bukan int/login/dict/recordset model lain. Tidak menggunakan implicit `sudo()`. Existing get_user_match menerima validation dan perlu adapter yang mempertahankan public signature; model-method dispatch hanya dari allowlist. Stored Python tidak dieksekusi pada v1.

7. Acceptance criteria draft untuk Lead review; keputusan D mengikuti addendum

Semua AC tetap DRAFT dan menunggu Lead review pada hash revisi ini. Keputusan D-01–D-11 mengikuti baseline addendum atas delegasi Owner; AC yang mengoperasionalkannya belum merupakan hasil pengujian atau acceptance gate. Trace dua arah terdapat pada UAT.

AC-01 — Selection: setiap input issuer hanya lookup exact trusted active profile; missing/malformed/unknown/ambiguous rejects sebelum outbound. D-01/D-02.
AC-02 — Modes: static endpoints only; zero Discovery. `get_jwks_data` dan PyJWKClient terikat trusted profile yang sama, endpoint statis, exact issuer dan transport policy; tidak fallback. D-02/D-03.
AC-03 — Classification: base amr_resource local classification konsisten dengan profile rule, bukan bukti validasi/local round-trip amr_token. D-02.
AC-04 — Consumers: signatures, response shapes and auth precedence mengikuti batas D-11; bearer invalid tidak fallback ke params. Profile/provenance contract eksplisit untuk tiap entry point bagian 5. D-01/D-10/D-11.
AC-05 — Transport: semua outbound termasuk direct JWKS helper dan PyJWKClient mematuhi policy scheme/TLS/origin/redirect/DNS/timeouts/credential. URL override dan introspection transport tidak bypass. D-03.
AC-06 — Cache/migration/rollback: key-indirection tidak diinterpretasi ulang sebagai URL; migrasi versioned/idempotent dan invalid legacy config gagal deterministik; cache addon/library token/introspection/metadata/JWKS dinonaktifkan pada v1; rollback mencakup code+config+schema+audit/cache state. D-02/D-09.
AC-07 — Scope: seluruh delta kandidat hanya amr_resource; tidak ada perubahan route/metadata/consumer/cache addon lain dan tidak mengklaim kompatibilitasnya. E-01.
AC-08 — Evidence: unit memanggil actual candidate methods, boundaries external mocked dan zero-network guards; rekam command/runtime/SHA/test digest/expected/actual/counts/mock limits; registry/ACL/HTTP/UAT/rollback tidak diwakili mock PASS. Separate authorization wajib.
AC-09 — Registry/access: issuer uniqueness and exact one-active-profile lookup must be enforced; archived issuer rows cannot create duplicate trust entries. Constraints/CRUD/row/field/RPC boundary must be effective per D-02/D-08, with no auto-registration from token input.
AC-10 — Audiences: multiple child rows distinct tersedia (E-02); `aud` string atau list string dan sekurangnya satu nilai exact-match (ANY); missing/empty/malformed ditolak.
AC-11 — azp: absen hanya bila profile mengizinkan; jika hadir wajib satu string exact-match konfigurasi; tidak menggantikan signature/issuer/aud/activity.
AC-12 — Sequencing/result: setiap resolver hanya setelah seluruh token checks; tepat satu user aktif eligible dengan exact issuer-subject binding atau reject; payload-only helper tidak menerima principal tanpa provenance validasi.
AC-13 — Fixed user: typed reference ke user aktif non-superuser/non-public/non-portal yang company_ids mencakup company aktif; invalid token tidak invoke, arbitrary claim uid tidak memilih user.
AC-14 — Method resolver: code-owned allowlist dan API D-06; unknown method/model, zero/multiple/wrong model/value, exception reject tanpa dispatch/fallback tak terdaftar.
AC-15 — Python: stored Python tidak dieksekusi pada v1; stored-code edits tetap dibatasi dan audited. Aktivasi memerlukan keputusan Owner terpisah dan candidate-bound manual Security dalam unified Code Review.
AC-16 — Identity: unique exact issuer-subject binding; tidak ada email/login fallback atau auto-binding; unbound subject dan ambiguity ditolak; migrasi legacy email hanya lewat mapping administrator yang audited.
AC-17 — Default: key `get_user_match` dan UI label persis `Default` tersedia (E-04); tidak ada preselection otomatis; binding dan hasil mengikuti AC-12.

8. Risiko, nonfunctional, rollout/rollback

Risiko bersyarat, severity UNASSESSED: input-derived metadata/endpoint dapat menyebabkan outbound ke host tak dipercaya dan mungkin membawa token/credentials, tergantung callers/network/config yang UNKNOWN. Fixed-user privilege collapse, arbitrary ORM dispatch, email collision/inactive mapping dan stored Python capability adalah boundary yang harus ditinjau, bukan exploit yang terbukti.

Residual baseline: raw-token logging pada T:amr_resource/models/helper.py:117-121; check_scope no-op pada T:amr_resource/models/ir_http.py:126-139; machine su=True pada T:amr_resource/models/res_users.py:14-26; controller generic call_kw pada T:amr_resource/controllers/main.py:98-106. Bukan fix yang diam-diam ditambahkan. Lead/Owner perlu disposition scope terpisah untuk baseline yang tidak diubah; delta kandidat tetap wajib review. Harness tidak boleh mengeluarkan token ke log.

NFR: bounded latency/retries/response size; config edits tidak memakai profile/cache revision lama; audited trust/code edits tanpa secrets; least privilege; deterministic sanitized errors. Angka transport baseline ditetapkan pada addendum D-03; TTL/cache berpedoman addendum D-09. Implementasinya tetap perlu diverifikasi pada kandidat/runtime.

Rencana rollout saja: inventory actual modules/config nonsecret, accepted profile decisions, versioned migration dry-run/idempotence/conflict rejection di QA terotorisasi, pin code+schema+config revision, audit/credential reference dan invalidate affected worker caches. Rollback wajib known-good tuple tersebut plus cleanup/restoration evidence; kode lama yang kembali bergantung Discovery bukan bukti recovery. D-09 menetapkan data-loss/irreversible migration dan RTO/RPO. Tidak memulihkan route provider sebagai workaround.

9. Evidence downstream dan status

Peran | Target | Gate / prasyarat | Evidence wajib | Aktual sekarang
Lead | exact draft hashes di RESULT.json | Step 0 review/acceptance, keputusan Owner dicatat terpisah | disposition per D dan hash PRD/UAT | PENDING
Developer/user | actual candidate amr_resource + approved isolated unit harness | Step 1 setelah authorization terpisah | real candidate method unit runs, test digests, branch/SHA, diff/secret/ancestry checkpoints | NOT RUN
Independent Code Reviewer + Security contributor | final candidate SHA + code/config revision digest | Step 2, setelah Step 1 selesai | general review, manual Security stored Python/ACL/transport, Semgrep offline evidence, tepat satu verdict Code Review | NOT RUN
Tester ditugaskan Lead | isolated Odoo 13 QA target dan synthetic DB; module/runtime pin D-10 | Step 3 setelah Code Review diterima serta authorization runtime/UAT | UAT kasus unit replay dan registry/ACL/HTTP/rollback simulation; run IDs dan sanitized evidence | NOT RUN
Owner / authorized DevOps | same accepted candidate PR | Step 4 serial dan merge readback | Owner disposition/PR_ACCEPT yang sah; merge terverifikasi | NOT RUN
Owner | deployment CI/CD atau rollback yang disetujui | di luar empat gate; authorization terpisah | evidence rollout/rollback aktual jika diperintahkan | NOT RUN

Tidak ada candidate baru, runtime target verified, tests, UAT, rollback, service access, Plane read/write, code/test edit atau risk acceptance dalam pekerjaan ini. Sumber eksternal v4 tidak diakses ulang karena jaringan dilarang; norma token spesifik harus dipilih dan ditinjau saat D-01/D-04 diselesaikan, bukan dianggap terverifikasi dari ingatan.
