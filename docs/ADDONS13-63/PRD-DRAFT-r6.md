# ADDONS13-63 — PRD-DRAFT r6

Status: DRAFT / NON-ACCEPTED. Reanalisis evidence, bukan kelanjutan keputusan r5. Target Odoo 13 / Python 3.7. Semua kasus UAT NOT RUN. Tidak mengotorisasi implementasi, runtime, DB, QA, waiver, maupun perubahan scope.

## 1. Identitas, sumber dan provenance keputusan

Worktree /home/ubuntu/worktrees/ADDONS13-63-analysis; branch lokal ADDONS13-63. Konteks dispatch: HEAD 82cba4ef0975ceec31cc6e2c536e3c58e5983ef8, origin/main 5de9a5776aecf8383ce580ed0446ee470f1c5425, remote task ref 7ecf5147811ba4a90616f74c6161739fc799394a (belum push). Ini nilai dari dispatch, bukan verifikasi git/hash sesi ini. Source dibaca dari worktree; kesetaraan bytes dengan HEAD dan verifikasi akhir milik Lead.

Evidence langsung yang dibaca:
- P1: /home/ubuntu/.hermes/cache/scratch/addons13-63-accepted-step0/accepted-prd.md, khususnya :5-7,19-59,73-85.
- P2: /home/ubuntu/.hermes/cache/scratch/addons13-63-accepted-step0/accepted-uat.md, khususnya :5-38.
- P3: docs/ADDONS13-63/PRD-DRAFT-r5.md:11,47-81 dan UAT-DRAFT-r5.md:46-65,116-130; keduanya dibaca lengkap sebagai draft pembanding, bukan sumber acceptance.
- P4: pesan dispatch tugas r6 dari user: laporan current Plane description/comment dengan marker LEAD-FLOW-UPDATE-2026-10-28-ADDONS13-63; issue UUID 0d2cf310-259f-4e5c-b5b0-ff0edf13d537, In Progress. Tidak mengakses Plane/jaringan; hanya informasi yang diberikan, bukan salinan lengkap activity/description hasil fetch.
- P5: pencarian session_search read-only profil analis, role user, query ADDONS13-63 lalu client_secret_post dengan exclusion dua hasil sebelumnya. Hasil: dua pesan dispatch historis, tidak ada hasil tambahan pada query kedua. Session local-3ca1f878cdaa94635a09f95935b255bfa0f6bb12c341c46d6cacd254e7b0b7df message 2279 menyebut “arahan scope Owner: Basic-only”; session local-1b9cb65d8813fa6f25fbeb317f6d188a93389edfbda03fdf47bef965de9b2bea message 2296 menyebut “Owner mengarahkan Basic-only”. Ini bukti bahwa dispatch lama memuat klaim itu, bukan bukti terpisah identitas penulis Owner atau instruksi Owner asli pembatalan post. Tidak ada percakapan Owner asli yang terautentikasi/teratribusi independen ditemukan dalam riwayat yang tersedia. Keterbatasan pencarian profil ini bukan bukti bahwa keputusan tersebut tidak pernah ada.

Baseline acceptance yang dipakai: P4 melaporkan activity Step 0 tanggal 2026-10-26 menerima predecessor PRD SHA-256 2bd6ebd045e25cdb2f61dfad5e65afc31794c8e57d413248b8c87d33b678315c dan UAT 363263a998dc47f9db97525711a2ee1748a9b09b7a93f7c7666fd107b3dbd572. P4 juga menyebut status/provenance copies commit 7ecf514 dengan hash PRD 84867c587906958ad9192786b8e9c8b073fc46cce274dd47967862ba6ded0aed dan UAT 21f99b1eb760090afc78162e142b66c689c6a45bfc5b94b812620f8b365aab17. Tidak menyamakan hash predecessor dengan hash copies.

Konflik metadata: snapshot P1/P2:3 menulis approval 2026-10-27 CST, sementara P1:85/P2:44 masih mengandung disclaimer lama “proposed/no AC accepted/draft only”. P4 menyatakan activity acceptance pada 26 Oktober dan snapshot cocok hash melalui Lead. r6 memperlakukan isi kontrak predecessor sebagai accepted baseline sesuai dispatch terkini; tanggal/bytes provenance tetap perlu rekonsiliasi Lead, tidak diperbaiki diam-diam dan tidak dihitung ulang di sini. Snapshot bukan bukti acceptance r6 atau hasil UAT.

Kesimpulan scope: accepted contract mencakup client_secret_basic DAN client_secret_post (P1:7,21,38-41,75-76). Basic-only sebagai keputusan Owner berstatus UNVERIFIED (OPEN O-1); klaim r5 dan dispatch historis tidak dipromosikan menjadi acceptance. Pesan Owner terbaru yang dilaporkan P4 tidak menetapkan scope auth ulang. Tidak ada keputusan baru bahwa post harus dihapus. Semua usulan r6 tetap terbuka, bukan perubahan baseline.

## 2. Inventory source langsung — bukan hasil test/runtime

Path berikut relatif worktree. Angka baris berasal dari read_file pada sesi ini; pencarian definisi dalam amr_oidc dan amr_token melengkapi pembacaan, bukan introspeksi live registry.

S1. amr_oidc/controllers/main.py:6,13,54-61: ControllerOIDC mewarisi ControllerToken; deklarasi POST /oidc/token, type=http, auth=none, csrf=False; memanggil amr.oidc.helper.sudo().oidc_token(**kwargs), kemudian make_response. Exception dicatat traceback sebelum handle_exception(ex,401,'invalid_request').
S2. amr_token/controllers/main.py:13-80 tidak mendeklarasikan token route; :15-25 melempar ulang HTTPException, mencatat exception lain beserta ex dan memetakan generic payload; :39-49 mengonsumsi status sebagai HTTP status dan JSON payload lainnya. Source menyarankan owner token amr_oidc, bukan bukti satu effective route/MRO runtime.
S3. amr_oidc/models/token_client_auth.py:15-20 hanya menambah selection client_secret_basic; :23-24 extend amr.oidc.helper; :93-95 autentikasi sebelum super. Returned client dari autentikasi tidak diteruskan ke super. amr_oidc/models/__init__.py:3-8 mengimpor base token_helper, helper, oidc_client, token_client_auth; urutan komposisi ORM efektif perlu runtime terotorisasi.
S4. amr_oidc/models/token_client_auth.py:40-90: query guard lebih awal; Basic parser; urlencoded body credential guard; lookup aktif sudo limit=1; set metode diterima literal {client_secret,client_secret_basic}; check_credentials; return client. Tidak memeriksa is_confidential atau allowed_grants di boundary ini.
S5. amr_oidc/models/token_client_auth.py:26-37: Unauthorized dengan Response JSON HTTP 401, error invalid_client, error_description 'Client authentication failed.', content type application/json; charset=utf-8. WWW-Authenticate=Basic hanya jika basic=True.
S6. amr_oidc/models/oidc_client.py:23-28,31-54,64-86: ID unik/nonblank; default authentication_method=client_secret, selection dasar private_key_jwt/tls_client_auth; hash restricted provider admin, copy=False; check_credentials mensyaratkan secret/verifier ada, identify pbkdf2_sha512 dan verify benar. Tidak membuktikan otomatis hashing semua write paths. :127-142 client_auth memakai parser Basic lain, bukan boundary endpoint yang dipanggil S3.
S7. amr_oidc/models/token_helper.py:28-31 standalone model amr.oidc.helper (bukan inherit amr.token.helper); :147-152 oidc_token SELALU return status=400,error=unsupported_grant_type,error_description terjemahan "Grant Type '%s' is not supported" % grant_type. amr_token/models/helper.py:154-159 identik dalam penolakan dispatch. :209-272 di helper OIDC memiliki fungsi generasi token umum, tetapi keberadaan fungsi bukan bukti token issuer reachable dari endpoint.
S8. amr_oidc/models/helper.py:14-15 extends helper OIDC; :31-44 parser Basic permissive; :48-115 private password/client_credentials handlers; :117-235 assertion/refresh handlers. Tidak ada override oidc_token dalam file yang dibaca. _do_client_credentials dapat membentuk access_token jika dipanggil langsung, tetapi S7 tidak dispatch ke sana. Logging assertion mentah pada :190-192 adalah risiko helper lain/laten, bukan bukti kebocoran melalui token route saat ini. amr_oidc/models/token_helper.py:81-94 juga punya parser Basic lama; jangan memakai parser ini sebagai oracle strict endpoint S4.
S9. amr_oidc/controllers/main.py:15-52,63-74: JWKS GET public; discovery GET public return 404; authorize/auth, authorize_continue, login/submit return 400 unsupported_response_type; continue/login_form GET template; introspect GET dan query token/access_token return 400, POST lain ke parent; profile/userinfo GET ke helper OIDC. Parent S2 masih punya JWKS/introspect/profile. Tidak mengklaim seluruh migrasi ADDONS13-38 selesai atau semua route tetangga token-owned.
S10. amr_oidc/__manifest__.py:5,12-15 depends base/web/amr_token, external pyjwt/cryptography, version 13.0.1.0.0. AGENTS.md:7-19,29-30 menetapkan Odoo 13/Python 3.7, framework/ORM, sudo terbatas. Tidak ada verifikasi dependency versions/runtime.

## 3. Perilaku source auth/error/parser saat ini

Ini prediksi statis untuk request yang mencapai helper, bukan actual HTTP execution.

- Urutan: query credential guard -> Authorization parsing -> urlencoded body guard -> missing Basic check -> active client/method/verifier -> super. Query dengan salah satu key client_id/client_secret, termasuk kosong/duplikat, ditolak; challenge hanya jika header lower().startswith('basic ').
- Basic: prefix literal case-insensitive 'basic ' (bukan semua bentuk whitespace), split(None,1), base64 validate=True, decoded UTF-8, split colon pertama SEBELUM form decoding. Malformed percent escape ditolak; '+' menjadi spasi lalu unquote_to_bytes dan UTF-8 decode. Encoded colon/plus/spasi dan secret colon harus dibedakan dalam fixtures.
- Valid Basic dengan method client_secret_basic atau legacy client_secret dan hash benar mencapai super. Tidak berarti HTTP 200 atau token tersedia: S7 mengembalikan unsupported_grant_type/400 untuk semua grant, termasuk missing.
- Invalid Basic, unknown/inactive client, wrong/empty secret, absent/invalid/non-pbkdf2 verifier, unsupported configured method: invalid_client/401 + Basic challenge. Missing header tanpa credential query/body juga challenge Basic. Non-Basic Authorization: invalid_client/401 tanpa challenge Basic.
- Body guard hanya mimetype application/x-www-form-urlencoded; http.form lalu fallback parse_qsl(raw UTF-8 body, keep_blank_values=True). Salah satu credential key cukup untuk reject, termasuk partial/empty/duplicate; bukan validasi duplikasi semua grant fields. Body-only tanpa Authorization ditolak tanpa challenge, karena guard keluar sebelum missing-header check. Basic valid + body credentials ditolak dengan challenge; malformed Basic lebih dahulu ditolak dengan challenge. Body-only valid post tidak pernah berhasil.
- client_secret_post tidak ditambahkan ke selection dan tidak termasuk set diterima. Inilah mismatch eksplisit terhadap accepted AC-2, bukan expected desired post exclusion.
- Non-urlencoded JSON/multipart credential-bearing body dengan Basic valid tidak mendapat pemeriksaan body eksplisit S4. Tidak ada success auth tanpa Basic di helper, tetapi itu tidak membuktikan penolakan semua mixed-channel requests. Raw invalid UTF-8/form parsing dan repeated Authorization bergantung parser/WSGI/ingress; failure sebelum helper tidak dijamin OAuth 401.
- HTTPException diteruskan parent; non-HTTP exception pada controller menjadi HTTP 401 JSON success=false,error=invalid_request,error_description='Request could not be processed.'. Jangan menyamakan semua failure dengan invalid_client atau semua 401 dengan Basic challenge. Parent logs ex dan controller logs traceback: generic response tidak membuktikan logging aman.
- grant_type direfleksikan ke description S7. Input canary dalam grant_type/exception message dapat muncul pada response/log tanpa credential auth secara sengaja dicetak. Harus dibedakan dari bukti kebocoran auth aktual; no-leak universal belum terbukti.

## 4. Accepted requirement -> current source -> AC r6 -> UAT

Pertahankan sembilan AC predecessor sebagai sembilan AC r6, satu-ke-satu dengan UAT unik. Teks berikut adalah restatement draft untuk evaluasi baseline, bukan acceptance ulang. Detail yang dulu OPEN tetap OPEN; source bukan pembuat kebijakan.

AC-63-R6-01 -> UAT-63-R6-01; predecessor AC-1 (P1:75).
Desired: satu POST token boundary pada owner yang disepakati menerima valid Basic untuk active configured client melalui verifier terlindungi. Observed S1-S6 sesuai parsial pada source; live route/MRO/auth-order belum terbukti. Legacy client_secret Basic alias adalah current implementation, bukan approved mapping; O-2. Tidak mensyaratkan issuance.

AC-63-R6-02 -> UAT-63-R6-02; predecessor AC-2 (P1:76).
Desired: boundary sama menerima valid client_secret_post ketika dikonfigurasi/dipilih menurut policy legacy/default yang disetujui. Observed S3/S4 menolak seluruh urlencoded credential body, tidak menyediakan selection post. MISMATCH kontrak accepted vs source. Acceptance terblokir O-1/O-2; test yang mengharapkan post exclusion tidak memenuhi AC ini. Jangan membuat fixture ORM selection ilegal lalu menyebutnya dukungan native.

AC-63-R6-03 -> UAT-63-R6-03; predecessor AC-3 (P1:77).
Desired: invalid/missing/malformed/unknown/inactive/unverified credentials berhenti sebelum grant, status/error sesuai mapping disetujui tanpa secret. Observed S4-S6 mendukung penolakan Basic statis; exact mapping sebelumnya OPEN. Rincian bagian 3 hanya characterization, bukan mapping approved. Error post-invalid belum terpisah dari penolakan semua post. O-3.

AC-63-R6-04 -> UAT-63-R6-04; predecessor AC-4 (P1:78).
Desired: multi-method/conflicting identities ditolak tanpa fallback. Observed Basic+urlencoded/query ditolak; post tunggal juga ditolak (bukan bukti exclusivity dua metode supported). Non-urlencoded/repeated header belum dijamin, O-4. Duplicate form ambiguity tetap perlu policy.

AC-63-R6-05 -> UAT-63-R6-05; predecessor AC-5 (P1:79).
Desired: credentials hanya approved header/form, query ditolak; encoding/colon/duplicate sesuai aturan disetujui. Observed query reject dan Basic strict decode; form hanya guard bukan post authentication. Basic percent/plus rules teramati, policy final belum diputuskan. Invalid raw form/proxy parser tidak boleh diasumsikan 401. O-3/O-4.

AC-63-R6-06 -> UAT-63-R6-06; predecessor AC-6 (P1:80).
Desired: plaintext secret/Authorization/decoded Basic/verifier tidak ada pada response/application logs; verifier hashed/restricted. Observed S6 hash verify/group/copy; S1/S2 exception logging dan S7 reflection masih risiko. Tidak ada bukti seluruh write/storage/log sink aman. O-5; ordinary user ACL memerlukan native ORM.

AC-63-R6-07 -> UAT-63-R6-07; predecessor AC-7 (P1:81).
Desired: auth sukses mempertahankan grant dispatch/issuance yang sudah ada; tidak menambah grant/refresh/metadata/discovery/code lifecycle. Observed S7 semua grant ditolak; S8 private handlers tidak reachable lewat dispatch yang dibaca. Source tidak mendukung asumsi supported-grant issuer. Oracle baseline saat ini adalah fail-closed setelah auth, bukan membuat grant baru agar UAT lama punya success fixture. Perubahan rebase lintas-ticket bukan otomatis acceptance atau regresi disebabkan ADDONS13-63; perlu baseline diff Lead. O-6.

AC-63-R6-08 -> UAT-63-R6-08; predecessor AC-8 (P1:82).
Desired: registry tepat satu POST token route pada agreed owner, GET tidak dipetakan, tetangga tidak berubah oleh fitur ini. Observed deklarasi token pada ControllerOIDC dan tidak pada ControllerToken; ini berubah dari inventory predecessor amr_token. Belum bukti registry/ownership agreement ADDONS13-38 selesai. Komposisi amr_token-only berisiko kehilangan token endpoint; O-6.

AC-63-R6-09 -> UAT-63-R6-09; predecessor AC-9 (P1:83).
Desired: source/tests dan eksekusi kompatibel Odoo 13/Python 3.7. Source target AGENTS/manifest ada; belum ada import/registry/dependency/runtime evidence. Doubles/skip bukan native PASS. Runtime/DB harus diotorisasi terpisah.

## 5. Inventory test source dan gap evidence

T1. amr_oidc/tests/test_token_client_auth_http.py:25-61 missing/bad Basic/encoding; :63-75 valid-to-unsupported-grant; :77-130 post absent, legacy alias, explicit Basic, mixed/duplicate/query/partial; :139-175 wrong secret, absent hash, inactive/method, normalized content type. Assertions ini dibaca, tidak dieksekusi. :77-79 justru mengunci post exclusion yang bertentangan accepted AC-2. Success :45-55,:63-75,:87-99 hanya observasi downstream 400 yang diharapkan test, tidak spy auth-order.
T2. File sama :177-189 registry count/method-name + class decorator metadata; tidak membuktikan owner callable efektif seluruh registry dari pembacaan. :191-207 sentinel mengganti seluruh oidc_token, melewati auth dan grant. Ini wiring test saja.
T3. amr_oidc/tests/test_client_secret_verifier.py:28-65 hash restriction/copy/ordinary-user access/client_auth; :6-11 dapat skip tanpa Odoo. Bukan endpoint method/encoding policy dan bukan audit semua storage writes.
T4. amr_oidc/tests/test_capability_fail_closed.py:17-53,83-139 isolated doubles, mengecek helper tanpa dispatch/public handlers dan fail-closed discovery/authorization. amr_token/tests/test_oidc_grants.py:24-61 doubles pada token base, bukan native OIDC extension/MRO/auth. Handler spies memakai nama do_* bukan semuanya private _do_*; jangan menyimpulkan seluruh private issuer path telah dibuktikan tidak dipanggil oleh run.
T5. amr_token/tests/test_controller_contract.py:80-99,120-133 masih mengharapkan ControllerToken.api_oidc_token dan amr.token.helper; bertentangan S1/S2. Ini stale-contract observation, bukan test FAIL hasil eksekusi. :51-67 memuat generic error/HTTPException assertions dengan doubles, bukan full HTTP/log safety.
T6. amr_oidc/tests/__init__.py:2-12 mengimpor HTTP/verifier tests; capability file tidak tercantum. Collection aktual belum diketahui; tidak boleh menghitung file sebagai tests collected.

Gap: positive post native, strict order spies sebelum super, issuer/private handler counters, token-only composition, full effective route owner, non-urlencoded/repeated-header/parser layer cases, uniform approved error matrix, logging/ACL/storage audit dan native target compatibility. Tidak ada test/run historis r4/r5 yang diteruskan sebagai verdict r6. SOURCE OBSERVATION != TEST SOURCE != RUNTIME EVIDENCE; kategori terakhir kosong pada tugas ini.

## 6. Keputusan OPEN dan rekomendasi analisis Lead

O-1 Scope auth / Owner dengan Lead: pilih setelah evidence asli diminta.
A. Pertahankan accepted Basic+post: perlu gap-fix source/selection dan positive/negative post tests dengan otorisasi baru; biaya implementasi/compatibility dan keamanan body/log harus dianalisis.
B. Ajukan Basic-only sebagai scope amendment: perlu instruksi Owner langsung dan acceptance kontrak revisi; post AC tidak boleh sekadar dihapus karena source sekarang menolak. Risiko memutus caller post dan perlu rencana transisi.
C. Tunda penentuan scope/implementasi sambil mencari evidence Owner asli: mempertahankan baseline accepted dan mismatch terbuka; risiko keterlambatan, bukan waiver mismatch.
Semua pilihan OPEN, tidak dipilih r6. Rekomendasi proses: Lead menautkan instruksi Owner asli atau meminta keputusan baru secara eksplisit sebelum penyesuaian implementasi/acceptance. Dua dispatch P5 tidak cukup untuk mengatasi konflik provenance P4.

O-2 Legacy/default/config / Owner: tetapkan client_secret alias Basic atau mapping lain, default dan transisi existing records; post hanya explicit selection atau policy lain yang disetujui; perilaku public/is_confidential=False/absent hash. Pilihan mempertahankan alias meminimalkan perubahan data tetapi ambiguity tetap; mengganti default/migrasi memerlukan approval dan rollback data tersendiri. Tidak menafsirkan selection private_key_jwt/tls_client_auth sebagai dukungan endpoint.

O-3 Error/encoding / Owner+Lead+Security: adopsi mapping source atau revisi mapping dengan review kompatibilitas/protokol; Basic strict percent/UTF-8/plus/colon dan post duplicate/malformed semantics perlu oracle tertulis. Jangan otomatis menyetujui seluruh current 401/challenge branches. Referensi RFC dalam predecessor diperlakukan sebagai rationale dokumen, bukan compliance yang telah diverifikasi lewat jaringan r6.

O-4 Transport / Lead+Developer dengan approval Owner bila kontrak berubah: kebijakan JSON/multipart/unknown format, duplicate headers dan malformed parser failures; reject credential-bearing non-form body atau batasi format yang didukung secara eksplisit. Risiko parser-layer credential confusion; tidak mengotorisasi global interceptor/Root.get_request/monkey patch.

O-5 Secret/logging / Owner+Security+Lead: pilih mitigasi traceback/exception text dan grant_type reflection versus kompatibilitas payload; tentukan application log sinks dan batas bukti. Sanitasi responses saja tidak cukup, sampling log bukan jaminan universal. Laten raw assertion log S8 dicatat untuk triage terpisah, bukan alasan mengaktifkan assertion grant.

O-6 Ownership/dependency/baseline / Lead dan owner ADDONS13-38: konfirmasi agreed token owner, urutan landing/rebase, token-only compatibility dan baseline grant fail-closed setelah rebase. P1 mencatat ADDONS13-38 In Progress sebagai blocking coordination; r6 tidak memverifikasi state live atau completion. Pilihan menunggu atau sequencing eksplisit keduanya perlu evidence keputusan. Jangan menambah dual route/issuer sebagai solusi diam-diam.

## 7. Dependency, implementation boundaries, rollback

Dependencies: addon amr_token/controller response utility, resource helper calls yang ada, protected oidc.client verifier/crypt context, form/header parser Odoo/Werkzeug, approved method/default/error policy, agreed route ownership ADDONS13-38, sandbox native untuk UAT. Manifest dependency tidak berarti OIDC grant dispatch mendelegasi ke helper token.

Urutan handoff yang direkomendasikan (bukan otorisasi): Lead rekonsiliasi provenance/scope -> Owner memutus OPEN relevan -> Lead tetapkan baseline/route sequence dan AC oracle -> Developer mendapat izin perubahan gap terisolasi -> Tester mendapat izin runtime/DB terpisah dan menjalankan pasangan UAT r6 yang direvisi bila keputusan berubah. Jangan menyebut r6 accepted sebelum review eksplisit.

Out of scope: grant/catalog/policy/issuance baru, refresh/code lifecycle, Discovery/RFC8414 metadata atau endpoint migration lintas-ticket, secret UI/storage redesign, private_key_jwt/TLS auth, deployment, perubahan Plane/hierarchy/assignee/priority/state. Allowed_grants policy storage bukan enforcement endpoint ini. Future issuer harus mengikat authenticated client secara eksplisit; tidak diimplementasikan sekarang.

Rollback dokumentasi sekarang: hanya r6 yang boleh ditarik/revisi melalui instruksi baru, tidak memulihkan source historis. Rollback implementasi kelak: revert perubahan auth dan tests yang terisolasi di agreed owner, bukan membatalkan rebase/ADDONS13-38 atau memindah token route kembali secara otomatis. Tidak ada DB migration dalam tugas ini; pilihan O-2 yang memerlukan data migration wajib punya backup/restore dan approval/rollback tersendiri. Revert auth bisa memulihkan kelemahan/kompatibilitas lama dan memerlukan review keamanan. Tidak ada rollback/deployment dijalankan.

Batas tindakan: hanya read-only evidence lokal/session dan pembuatan dua dokumen r6. Snapshot accepted, PRD-DRAFT.md/UAT-DRAFT.md, r2-r5, manifest historis, source/tests tidak menjadi target write. Tidak menjalankan tests/addon/Odoo/DB/runtime/QA/service/network; tidak stage/commit/push atau edit Plane. Tidak mengklaim hashes/source unchanged; Lead memverifikasi akhir. Semua UAT tetap NOT RUN, tidak ada PASS/waiver/acceptance.
