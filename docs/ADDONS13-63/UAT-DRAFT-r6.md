# ADDONS13-63 — UAT-DRAFT r6

Status DRAFT / NON-ACCEPTED. Semua kasus dan seluruh variannya NOT RUN. Tidak ada test PASS, runtime evidence, waiver, atau izin pelaksanaan. Target Odoo 13 / Python 3.7; runtime/DB authorization terpisah wajib diperoleh sebelum prosedur ini dijalankan.

## 1. Pasangan kontrak dan provenance

Pasangan: docs/ADDONS13-63/PRD-DRAFT-r6.md. Mapping satu-ke-satu: predecessor AC-1 sampai AC-9 -> AC-63-R6-01 sampai AC-63-R6-09 -> UAT-63-R6-01 sampai UAT-63-R6-09. Tidak menggunakan AC Basic-only r5 sebagai baseline acceptance. Setiap case di bawah adalah satu UAT ID unik dengan varian bernama; semua varian NOT RUN.

Accepted snapshots dibaca langsung read-only:
/home/ubuntu/.hermes/cache/scratch/addons13-63-accepted-step0/accepted-prd.md
/home/ubuntu/.hermes/cache/scratch/addons13-63-accepted-step0/accepted-uat.md

Konteks dispatch: HEAD 82cba4ef0975ceec31cc6e2c536e3c58e5983ef8, base origin/main 5de9a5776aecf8383ce580ed0446ee470f1c5425, remote task ref 7ecf5147811ba4a90616f74c6161739fc799394a belum push. Tidak diverifikasi git/hash oleh r6. Detail hash predecessor versus committed copies dan konflik tanggal approval/footer snapshot ada di PRD §1. Laporan current Plane marker LEAD-FLOW-UPDATE-2026-10-28-ADDONS13-63 dari dispatch user digunakan sebagai provided evidence, bukan fetch Plane. Plane tidak diedit/diakses jaringan.

Accepted desired contract tetap Basic DAN post; keputusan Owner Basic-only UNVERIFIED, O-1. Session history lokal menemukan dua dispatch lama mengklaim arahan Owner, bukan instruksi Owner asli yang teratribusi independen; lihat PRD P5. Tidak ada acceptance r5/r6 dari klaim tersebut. Dokumen r5 dibaca untuk pembanding, bukan oracle final.

S1–S10 dan T1–T6 merujuk inventory path:line PRD r6 yang dibaca langsung pada tugas ini. Expected current-code di bawah adalah PREDIKSI SOURCE, bukan actual result. Desired baseline tidak boleh diturunkan agar sama dengan source. Characterization yang sesuai source bukan PASS acceptance bila kontrak masih mismatch/OPEN. Mapping exact HTTP errors, legacy/default, encoding dan transport yang sejak predecessor OPEN tidak tiba-tiba dianggap accepted di sini.

## 2. Gate eksekusi kelak — jangan dijalankan sekarang

1. Owner/Lead menyelesaikan O-1 scope dan O-2 konfigurasi/default; tuliskan policy O-3/O-4/O-5 dan ownership/baseline O-6. Jika memilih scope amendment, revisi dan accept kontrak baru secara eksplisit, jangan mencatat post exclusion sebagai lulus AC-2 predecessor.
2. Dapatkan otorisasi terpisah untuk disposable Odoo 13/Python 3.7/PostgreSQL sandbox, module composition, native test execution, local HTTP dan log inspection. Tidak memakai produksi/shared DB, real credentials atau external services. Tidak ada izin ini dalam tugas dokumentasi r6.
3. Lead merekam candidate revision, baseline pembanding, module/dependency versions dan route ownership agreement. Tidak memakai hasil run r4/r5 sebagai evidence kandidat sekarang.
4. Fixtures sintetis: A active explicit client_secret_basic; B default client_secret; C inactive; D absent verifier; E/F private_key_jwt/tls_client_auth; G unknown ID; H post hanya setelah selection/policy implementation legal disetujui. Hash melalui approved fixture path, bukan menaruh plaintext sebagai verifier untuk positive cases. Negative verifier fixtures diberi label. Dua identitas untuk konflik, is_confidential=False untuk policy characterization, special-character ID/secret terpisah.
5. Request normal POST /oidc/token, body urlencoded grant_type=client_credentials saja, satu Basic header. Encode masing-masing komponen sebelum separator/base64. Simpan fixture labels, bukan credentials/Authorization mentah.
6. Instrumentation test-only native yang disetujui mencatat auth-return client label, super-entry order/count dan private handler/issuer counters, bukan secrets. Jangan mengganti seluruh oidc_token untuk membuktikan autentikasi. HTTP 400 unsupported_grant_type sendiri bukan bukti auth berhasil. Route sentinel membuktikan wiring saja. Ikuti framework; tidak mengotorisasi global hook/production monkey patch.
7. Actual result saat ini untuk semua case: belum diperoleh. Kelak capture HTTP status, JSON, headers, effective owner/registry, sanitized counters dan log scan sesuai boundary. Bila gate/oracle/fixture belum ada, tetap NOT RUN; jangan beri PASS lewat unit double atau skip.

## 3. Kasus dan traceability

### UAT-63-R6-01 -> AC-63-R6-01 -> predecessor AC-1: valid Basic
Status: NOT RUN; acceptance mapping legacy menunggu O-2, ownership O-6.
Anchor: amr_oidc/controllers/main.py:54-61; amr_oidc/models/token_client_auth.py:46-62,78-95; amr_oidc/models/oidc_client.py:49-86; existing HTTP tests :87-99 (T1).

Langkah kelak:
a. Pada agreed single token route kirim A dengan satu valid Basic dan tanpa credential query/form. Instrumentasi harus membuktikan client A terverifikasi sebelum super sekali.
b. Ulang B default legacy; catat selection/default dan auth result terpisah, tanpa migrasi.
c. Ulang public/nonconfidential fixture dengan verifier benar untuk karakterisasi kebijakan yang belum diputuskan, bukan public-client support acceptance.

Desired accepted: valid Basic untuk active configured client via restricted existing hash berhasil pada auth boundary agreed owner. Tidak menuntut token diterbitkan. Legacy/public behavior hanya menurut policy eksplisit O-2.
Prediksi source: A dan B dapat melewati auth lalu super return 400 unsupported_grant_type; helper tidak memeriksa is_confidential/allowed_grants; client hasil auth tidak diteruskan ke super. Keberhasilan B/public saat characterization tidak mengesahkan mapping/default/public policy.
Boundary/evidence: native ORM auth + real HTTP + auth/super order spy; record label/counters/status/body redacted. Satu effective route dibuktikan R6-08, bukan sekadar decorator. Downstream 400 tanpa spy dan helper sentinel tidak memenuhi bukti case ini. Risiko future client binding dicatat, bukan mengaktifkan grant.

### UAT-63-R6-02 -> AC-63-R6-02 -> predecessor AC-2: valid post accepted baseline
Status: NOT RUN; MISMATCH SOURCE, acceptance BLOCKED O-1/O-2.
Anchor: accepted-prd.md:7,21,76; amr_oidc/models/token_client_auth.py:18-20,64-89; amr_oidc/models/oidc_client.py:50-54; amr_oidc/tests/test_token_client_auth_http.py:77-85,101-106,121-130.

Langkah kelak:
a. Inspeksi native selection dan approved post configuration/default policy. Jika post tidak tersedia secara legal, laporkan gap, jangan membuat ORM record dengan nilai selection ilegal seolah dukungan native.
b. Setelah approved implementation/fixture tersedia: H active selected post, satu client_id+client_secret dalam application/x-www-form-urlencoded body, tanpa Authorization/query. Spy auth-return H dan super-entry.
c. Ulang wrong/absent/partial credentials dan configured method mismatch (detail error R6-03). Ulang B hanya sesuai approved mapping. Pastikan bukan fallback dari gagal Basic.

Desired accepted: satu valid post pair diterima hanya sesuai configured/selected policy O-2 pada boundary yang sama; auth sukses sebelum super dan tidak membuka grant baru. Source yang belum menyediakan post tetap mismatch, bukan desired rejection.
Prediksi source sekarang: selection hanya menambah Basic; body-only post ditolak 401 invalid_client, description 'Client authentication failed.', tanpa WWW-Authenticate karena body guard lebih awal; tidak mencapai super. Tidak ada positive post fixture native yang sah dari selection source ini. Existing test yang mengharapkan post absent/reject mengkarakterisasi source, BUKAN memenuhi accepted AC-2.
Boundary/evidence: legal native selection/configuration + ORM auth spy + HTTP. Double dengan stale method string hanya characterization unit, bukan dukungan post native. Kelak bedakan actual vs desired/mismatch; semua langkah sekarang NOT RUN. Bila Owner memilih Basic-only, AC ini perlu disposition/amendment accepted tertulis, tidak otomatis PASS/waived.

### UAT-63-R6-03 -> AC-63-R6-03 -> predecessor AC-3: failures/error mapping
Status: NOT RUN; exact accepted error oracle BLOCKED O-3; post variants juga O-1/O-2.
Anchor: amr_oidc/models/token_client_auth.py:26-89; amr_oidc/models/oidc_client.py:72-86; amr_oidc/controllers/main.py:56-60; amr_token/controllers/main.py:15-25. Tests T1 :25-43,57-61,139-160; T5 :51-67 hanya source assertions.

Langkah kelak: table-driven variants missing header tanpa query/body credentials; Basic invalid base64, UTF-8, missing colon, malformed percent; A wrong/empty secret; G unknown, C inactive, D absent verifier, malformed/plaintext/non-pbkdf2 verifier; E/F unsupported method; non-Basic Authorization. Untuk post valid configuration, ulang invalid/missing/unknown/inactive/unverified/method mismatch. Instrumentasikan super/private handlers tidak dipanggil pada auth failure. Terpisah seam controller HTTPException dan non-HTTP exception dengan synthetic message; pulihkan seam.

Desired accepted: seluruh credential failure ditolak sebelum grant dispatch, exact status/body/challenge menurut approved matrix, tanpa credential disclosure. Tidak menyamakan unsupported method dengan supported private_key_jwt/TLS. HTTP/parser exceptions bukan credential-failure oracle otomatis.
Prediksi source: missing header tanpa credentials, Basic malformed/verifier/client/method failures -> 401 invalid_client + Basic challenge; non-Basic -> 401 invalid_client tanpa Basic challenge. Body-only credentials -> 401 tanpa challenge, bukan post verifier-specific failure. HTTPException dilempar ulang dengan response/header; non-HTTP caught controller -> 401 {success:false,error:invalid_request,error_description:'Request could not be processed.'}, tidak dijanjikan Basic challenge. Traceback/ex logging tetap risiko R6-06. Unknown exception dari parser sebelum controller tidak dicakup janji mapping ini.
Boundary/evidence: native ORM/helper dan HTTP, sanitized matrix per varian beserta auth/super counters; exception seam hanya mapping controller-parent, tidak membuktikan auth. Jangan menganggap mapping source sebagai policy accepted tanpa O-3. Simpan generic error/check headers tanpa secrets.

### UAT-63-R6-04 -> AC-63-R6-04 -> predecessor AC-4: exclusivity/conflicts
Status: NOT RUN; transport/duplicates policy BLOCKED O-4, positive post O-1/O-2.
Anchor: amr_oidc/models/token_client_auth.py:40-77; tests/test_token_client_auth_http.py:108-130.

Langkah kelak: A valid Basic + urlencoded client credentials identitas sama lalu berbeda; partial client_id/client_secret, empty keys, duplicate credential keys, conflicting query identities; ulang malformed Basic dan valid body; lakukan non-urlencoded mixed-channel dan repeated Authorization dengan approved layer strategy dari R6-05. Tambah post-only valid control setelah implementasi approved agar multi-method rejection tidak disalahartikan dari semua body reject.
Desired accepted: multi-method/conflicting identities/approved ambiguous duplicate cases ditolak tanpa memilih credential lain atau fallback; tidak ada super dispatch. Valid single approved post harus dibedakan dari mixed requests.
Prediksi source: Basic+parseable urlencoded credentials ditolak 401 invalid_client dengan challenge jika Basic berhasil diparse; malformed Basic keluar lebih awal + challenge. Body-only juga ditolak; itu tidak membuktikan dua supported methods eksklusif. Query key ditolak sebelum parsing; challenge hanya jika prefix Basic. Non-urlencoded mixed/repeated headers belum dijamin reject.
Boundary/evidence: HTTP parser -> helper -> super counters; query/form duplicate bukan repeated-header coverage. Bukti perlu request variant labels, status/body/challenge, zero dispatch; tidak merekam raw credential bodies. Unknown transport oracle tidak diberi PASS; O-4 tetap OPEN.

### UAT-63-R6-05 -> AC-63-R6-05 -> predecessor AC-5: channel/encoding/parser
Status: NOT RUN; final policy O-3/O-4 OPEN.
Anchor: amr_oidc/models/token_client_auth.py:40-77; amr_oidc/models/token_helper.py:81-94 dan amr_oidc/models/helper.py:31-44 adalah parser lama, BUKAN boundary oracle. Existing HTTP tests :45-61,108-119,162-175.

Langkah kelak:
a. Query client_id saja/client_secret saja/keduanya, empty/duplicate, masing-masing tanpa header, valid/malformed Basic, non-Basic; pastikan tidak fallback.
b. Basic komponen UTF-8, percent-encoded colon dalam ID/secret, literal colon setelah separator dalam secret, encoded plus versus '+' space, malformed percent/invalid UTF-8/base64/prefix whitespace. Cocokkan fixture tepat tanpa mencetak decoded pair.
c. Post urlencode decoding/colon/plus/duplicates setelah approved policy/implementation tersedia; jangan menyamakan Basic decoder dengan form decoder.
d. Content type lowercase dan normalized case/charset untuk mixed urlencoded. Basic valid + JSON/multipart/unknown content type dengan credentials, serta tanpa Basic; raw malformed form/UTF-8 dan repeated Authorization di approved ingress. Catat layer terakhir tercapai: ingress/WSGI, Odoo parser, controller, auth helper, super.

Desired accepted: credential hanya approved header/form, query ditolak, encoding/colon/duplicate sesuai approved oracle; ambiguous channels tidak diambil diam-diam. Dukungan post tetap desired accepted, bukan pemberian izin auth lewat JSON/query. Final malformed/parser/header outcome harus tertulis sebelum verdict.
Prediksi source: query key -> 401 invalid_client; Basic challenge hanya prefix lower().startswith('basic '). Basic strict b64/UTF-8; split colon pertama lalu reject malformed percent, replace '+' space, unquote bytes+UTF-8. Valid pair bisa mencapai auth dan downstream 400; malformed Basic -> 401 + challenge. Guard urlencoded memakai http.form/fallback parse_qsl; normalization bergantung http.mimetype. Non-urlencoded mixed body tidak diperiksa eksplisit; tanpa Basic tidak ada jalur auth sukses di helper, tetapi outcome parser/ingress tidak dijamin 401. Tidak ada source policy repeated headers yang lengkap. Invalid raw UTF-8 body dapat menjadi non-HTTP exception mapping bila mencapai controller, bukan pasti invalid_client.
Boundary/evidence: pisahkan pure decoding, parser-native, ORM auth, ingress/HTTP. Capture layer counters dan outcomes tersanitasi; doubles tidak menutup WSGI/parser. Basic/form encoding oracle tidak boleh disimpulkan sebagai RFC compliance tanpa review terpisah. Catat mismatch terhadap desired, jangan menetapkan kebijakan baru dari characterization.

### UAT-63-R6-06 -> AC-63-R6-06 -> predecessor AC-6: secret/storage/logging
Status: NOT RUN; log-scope/sanitasi O-5 OPEN.
Anchor: amr_oidc/models/oidc_client.py:49-86,127-142; amr_oidc/controllers/main.py:58-60; amr_token/controllers/main.py:15-25; amr_oidc/models/token_helper.py:147-152; amr_oidc/models/helper.py:190-192. Verifier tests :28-65 bukan run evidence.

Langkah kelak: gunakan canary sintetis untuk accepted-auth-to-400 dan tiap failure, termasuk exception branches R6-03. Periksa field metadata, hash verification (valid/wrong/empty/plaintext/malformed/non-pbkdf2), copy dengan client_id baru, ordinary-user read ID vs verifier. Audit approved write paths terpisah dari check_credentials, jangan mengasumsikan otomatis hashing. Scan response dan approved application log sinks untuk secret/raw header/decoded pair/verifier; jangan retain raw captures. Pisahkan exploratory canary di grant_type dan exception text. Triage raw assertion log laten tanpa mengaktifkan assertion grant.
Desired accepted: auth credentials/verifier tidak terungkap di responses/application logs; verifier hashed/restricted dan tidak disalin. Perlu bukti native ACL dan audit write path sesuai batas audit; absensi dalam sample bukan jaminan seluruh sistem.
Prediksi source: check_credentials hanya menerima verifier pbkdf2_sha512 valid, field provider-admin/copy=False. Tidak ada bukti otomatis hash seluruh writes. Generic auth response tidak echo credential, tetapi controller traceback dan parent exception text tidak membuktikan no-leak; grant_type masuk error description. Raw assertion logger ada pada private helper yang tidak didispatch S7; bukan temuan kebocoran endpoint actual.
Boundary/evidence: native ORM ACL/storage + application response/logging; proxy/infrastruktur sink yang tidak diperiksa dinyatakan di luar evidence. Catat sink/cakupan/assertion/result boolean/lokasi redacted, jangan nilai canary/verifier. Jika canary ditemukan laporkan risiko/finding sesuai layer, bukan ditoleransi diam-diam demi compatibility. Tidak ada audit/run sekarang.

### UAT-63-R6-07 -> AC-63-R6-07 -> predecessor AC-7: grant preservation/no new capability
Status: NOT RUN; baseline attribution O-6 OPEN.
Anchor: amr_oidc/models/token_client_auth.py:93-95; amr_oidc/models/token_helper.py:147-178,209-272; amr_oidc/models/helper.py:48-235; amr_token/models/helper.py:154-159; grant/capability tests T4.

Langkah kelak: dengan A valid Basic, kemudian H post hanya setelah scope/policy approved, instrumentasikan auth -> base super dan private _do_* handlers/generic issuers tanpa mengganti dispatch. Kirim missing grant_type, client_credentials, password, refresh_token, authorization_code, urn:ietf:params:oauth:grant-type:jwt-bearer, challenge_approval, digital_signature, unknown. Bandingkan baseline Lead terverifikasi setelah rebase, source diff auth change terisolasi dan output endpoint. Review metadata/discovery/code paths untuk tidak ada tambahan fitur karena auth.
Desired accepted: auth sukses tidak menambah/mengubah existing grant dispatch/issuance/refresh/metadata/discovery/code lifecycle. Tidak perlu supported-grant issuer jika baseline tidak memilikinya. Jika baseline revisi lain berbeda, selesaikan attribution/dependency review dahulu, bukan menambahkan issuer untuk memenuhi fixture lama.
Prediksi source: setiap grant mencapai base yang return dictionary status=400,error=unsupported_grant_type,description terjemahan "Grant Type '%s' is not supported" dengan grant_type (missing None); controller memakai HTTP 400 dan tidak mengembalikan field status sebagai JSON. Tidak ada access/refresh/id token atau dispatch ke private handlers lewat oidc_token yang dibaca. Fungsi generasi token tetap ada tetapi tidak membuktikan reachable issuer endpoint.
Boundary/evidence: native OIDC ORM/MRO+HTTP auth-order/private-handler/issuer counters, helper dictionary dan HTTP payload per varian, stable locale untuk exact description; source/baseline diff terpisah. amr_token doubles dan HTTP downstream 400 saja tidak membuktikan OIDC auth extension atau seluruh private handlers tidak terpanggil. Input grant_type reflection security milik R6-06, bukan izin mengubah payload diam-diam. Jangan mengaktifkan real issuance credentials/grants.

### UAT-63-R6-08 -> AC-63-R6-08 -> predecessor AC-8: route ownership/dependencies
Status: NOT RUN; agreed owner/sequence O-6 OPEN.
Anchor: amr_oidc/controllers/main.py:13-74; amr_token/controllers/main.py:13-80; amr_oidc/__manifest__.py:12-15; amr_oidc/models/token_helper.py:28-31; HTTP tests :177-207; stale token controller tests :80-99,120-133.

Langkah kelak:
a. Setelah agreement ADDONS13-38, enumerasi native registry komposisi amr_oidc+dependencies; periksa path/method/effective callable owner dan decorator metadata. Probe POST/GET; bedakan framework-injected methods dari explicit methods, jangan mengubah oracle tanpa review.
b. Sentinel terkontrol berbeda untuk helper OIDC vs token hanya untuk wiring, lalu restore. Ini bukan auth test.
c. Dalam disposable composition terpisah yang disetujui, inspeksi amr_token-only token route; jangan install/uninstall shared DB.
d. Inventory tetangga terhadap baseline Lead: JWKS, discovery, authorize/auth, continue/login_form, authorize_continue/login_submit, introspect, profile/userinfo, termasuk methods/type/auth/CSRF/website. Source unspecified dan framework effective metadata dicatat terpisah.

Desired accepted: tepat satu POST /oidc/token pada agreed owner, GET tidak dipetakan, tanpa duplicate route/compatibility shim atau perubahan tetangga akibat auth feature. Route migration bukan otomatis scope fitur; endpoint ownership dan token-only compatibility harus punya keputusan.
Prediksi source: deklarasi token ControllerOIDC, type=http/auth=none/POST/csrf=False, helper OIDC.sudo; ControllerToken tidak mempunyai token method. OIDC helper standalone, bukan grant delegate token helper, walau addon/controller depends amr_token. amr_token-only source tidak mendeklarasikan token route; registry/HTTP composition perlu dibuktikan, bukan janji 404 semua deployment.
Baseline tetangga source: JWKS child ke helper OIDC; discovery GET public 404; authorize/auth dan authorize_continue/login_submit 400 unsupported_response_type; continue/login_form GET templates; introspect GET/query token atau access_token 400, POST lain ke parent; profile/userinfo GET helper OIDC. Parent masih punya JWKS/introspect/profile. Jangan menyatakan semua route tetangga sudah migrated/owned base atau discovery/authorization aktif.
Boundary/evidence: native registry/HTTP/composition, effective owner snapshot, helper sentinel result/restoration, agreed sequence/baseline diff. Existing registry test source menghitung satu rule dan nama method serta class metadata, bukan runtime proof owner. Stale base-controller tests perlu disposition Developer/Lead lewat izin baru, bukan disembunyikan, diedit, atau dinyatakan gagal dari baca source saja.

### UAT-63-R6-09 -> AC-63-R6-09 -> predecessor AC-9: compatibility/evidence integrity
Status: NOT RUN.
Anchor: AGENTS.md:7-19; amr_oidc/__manifest__.py:5,12-15; amr_oidc/models/__init__.py:3-8; amr_oidc/tests/__init__.py:2-12; verifier test :6-11.

Langkah kelak: review supported syntax/APIs; rekam actual Odoo/Python/dependency versions dan addon composition, import/registry/MRO/auth extension. Setelah izin terpisah, jalankan approved suites/UAT di Odoo 13/Python 3.7; laporkan collected/executed/skipped/failure per test, tidak menghitung file sebagai collected. Reconcile stale-contract tests dan capability standalone doubles vs native harness; jangan memasang global bootstrap/interceptor untuk menutupi gap.
Desired accepted: supported code/tests benar-benar kompatibel target native. Static syntax review, isolated doubles, lingkungan lain atau skip karena Odoo unavailable tidak cukup untuk PASS. Manifest menyatakan dependencies, bukan membuktikan library version compatibility.
Prediksi source: target/manifest ada, imports extension ada; capability test tidak tercantum tests/__init__, collection native belum diketahui. Tidak ada actual compatibility result pada tugas ini.
Boundary/evidence: static review terpisah actual supported-runtime transcript/import/registry/test result. Rekam batas sandbox, missing deps/skip/blocker jujur. Tidak menggunakan fabricated output/riwayat run sebagai evidence kandidat r6.

## 4. Rekap OPEN, gap dan verdict

O-1 scope Basic+post accepted vs Basic-only UNVERIFIED: terutama R6-02; semua auth controls bergantung pilihan scope. Lead meminta instruksi Owner asli atau keputusan baru; opsi mempertahankan baseline/gap-fix, amend Basic-only, atau tunda keputusan semuanya OPEN dengan dampak di PRD §6.
O-2 legacy/default/public/config: R6-01/02/03. Alias source tidak menjadi keputusan Owner; fixture post ilegal bukan native success.
O-3 error/encoding mapping: R6-03/05. Source characterization tidak mengisi acceptance policy yang belum disetujui.
O-4 non-urlencoded/repeated-header/parser/duplicate semantics: R6-04/05. Pisahkan ingress, Odoo parser, controller dan helper, jangan klaim universal 401.
O-5 sanitasi logging/reflection/storage audit: R6-06 dan exception/grant subvariants R6-03/07. Tidak mengklaim no-leak dari generic response atau sample logs.
O-6 ownership/dependency/rebase baseline/token-only compatibility: R6-07/08. ADDONS13-38 coordination tidak terbukti complete lewat source.

Gap test source yang nyata: post positive tidak tersedia, bahkan test mengecualikannya; boundary-order spies tidak tersedia dalam valid-to-400 cases; sentinel bypass auth; native route owner/MRO/ACL/logging/parser/compatibility belum terbukti; token controller contract masih mengharapkan route base; doubles private-handler coverage terbatas. Pembacaan test bukan test result, tidak ada execution FAIL/PASS yang diklaim.

## 5. Pelaporan dan teardown kelak

Per case/varian wajib simpan: verified candidate revision dan baseline, keputusan/policy version, fixture label, boundary aktual, desired accepted oracle, prediksi source, actual result, sanitized evidence reference, status dan blocker. Seluruh UAT-63-R6-01 sampai UAT-63-R6-09 beserta subvariannya saat ini NOT RUN; tidak ada bukti runtime. BLOCKED adalah acceptance disposition, bukan klaim test telah dijalankan. Case dengan source mismatch tidak ditandai PASS karena characterization sesuai source.

Sesudah run berizin kelak: pulihkan spies/sentinel/seams, hapus disposable DB/clients/users/verifiers/canaries/config, stop sandbox, musnahkan raw credential traces dan retain redacted evidence saja. Jangan menyentuh shared/production resources. Tidak ada deployment atau rollback source sekarang; rencana rollback auth terisolasi dan larangan membatalkan migrasi ADDONS13-38 ada di PRD §7. Bila pilihan default butuh data migration, perlu approval dan backup/restore plan terpisah.

Batas tindakan r6: baca evidence lokal/session dan tulis dua draft baru saja. Tidak menjalankan prosedur di atas, tests, addon, Odoo/DB/runtime, QA, service/network; tidak edit Plane, source/tests, accepted snapshots, PRD-DRAFT.md/UAT-DRAFT.md, r2-r5 atau manifest historis; tidak stage/commit/push. Tidak mengklaim hash/source unchanged; verifikasi akhir oleh Lead. R6 bukan acceptance, waiver, atau izin implementasi.
