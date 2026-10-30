# ADDONS13-64 — PRD v3.1, remediasi hook-only / privacy file-only

**DRAFT v3.1 — NOT ACCEPTED.** Full superseding review draft; belum mengganti acceptance historis sampai Owner menerima exact hashes. Candidate analisis aktual `4c39fd76cb3818f0fd29cd8c7738fb647e85fde5`, branch `ADDONS13-64`, source committed blobs di `/home/ubuntu/worktrees/ADDONS13-64`. Target produk **Odoo 13 / CPython 3.7.3**, berdasarkan direct Owner. Lead memverifikasi worktree bersih dan diff `6a51c81493b339c67fb97c6615a3e7d758c60251..4c39fd76cb3818f0fd29cd8c7738fb647e85fde5` hanya `AGENTS.md` (commit `agent Python 3.7.3`); source produk identik. Attribution/otorisasi commit tersebut tidak ditebak dan approval dokumen tidak otomatis mengotorisasi push commit itu. Live remote feature masih `6a51c81493b339c67fb97c6615a3e7d758c60251`; target integrasi `origin/main=ac1bcbd66261b92c10078f2a8744a657a3b6490c` cocok live remote. Local main `c08b050cfd85ccc5c705eb92852e57626eb82806` tidak digunakan. Hasil eksperimen tetap historical pada source6a51c81, bukan UATv3.1. Rebinding ini hanya metadata kandidat, tidak mengubah kontrak normatif draftv3. Dokumen analisis/traceability/source-evidence v3 dipertahankan sebagai provenance pra-binding; rujukan terbaru adalah dua dokumen v3.1 dan REBIND-v3.1.json.

## 1. Outcome, audience, authority

Core `amr_service_client` tidak wajib membawa Sentry; optional `amr_sentry` melaporkan hanya outcome hook service-client tanpa automatic integrations, menjaga outcome bisnis. Dokumen ini lengkap dan menggantikan isi normatif draft revision/proposal terdahulu **bila disetujui**, bukan addendum bertumpuk. Developer mengerjakan delta kecil, QA memverifikasi oracle nyata, operator mengelola file/restart, Owner memutus residual product/privacy/security.

**Keputusan Owner yang sudah berlaku:** hook-only, automatic integrations off, privacy options FROM FILE (bukan injected kwargs); selected wajib record client opt-in, tidak kwargs fallback dan tidak restore tags/extra lama; target Python 3.7.3; pilih legacy A isolated test-only, Requests adjustment di sandbox diperbolehkan. Ini menggantikan retain Requests 2.21 **untuk sandbox saja**, bukan pin produksi atau waiver advisory. Major Odoo19/Python3.12 dan SDK1.9 bukan jalur task ini.

**Yang belum approved:** safe-profile/schema validation delta bagian 4, seluruh PRD/UAT v3, kontrak residual exception D-EX dan proses SDK D-GLOBAL; implementasi dan runtime berikutnya perlu izin terpisah. Accepted artifacts lama tidak disentuh: `docs/ADDONS13-64/step0-20261030/OWNER-ACCEPTANCE.json` mengikat candidate3774c6f dan exact PRD `15f8e36979fd56dc70542a72b2a28156886da01777aeb31d95b4c09803fd422f`, UAT `d68fbc2f07e72a243404897d75c47aeaca50ef6cd7ad79af278e1148aa8cba8f`; approval lama bukan acceptance dokumen/hasil baru.

## 2. Evidence aktual, bukan hasil UAT v3

Rujukan absolut dan hashes ada di SOURCE-EVIDENCE.json. Eksperimen `legacy-py373-experiment-20261030/{RESULT.md,QA-EXPERIMENT.md}` menguji current source dengan minimal active config dsn+policy, bukan safe flags proposal ini.

- Baseline actual Python3.7.3/Odoo13.0-20221005, Requests2.21.0/urllib3 1.24.1; candidate same interpreter/Odoo dengan Requests2.31.0, urllib3 1.26.20, SDK2.73.0, PyYAML6.0.1, certifi2026.10.23, charset-normalizer3.5.2, idna3.10. Full pip check keduanya exit0; L1 masing-masing41 pass; candidate install/registry smoke pass, baseline optional install BLOCKED missing sentry_sdk.
- Real SDK outside-hook logging menghasilkan event pada mode aktif; hook-only FAIL. Exception-message dan synthetic sensitive locals masuk envelope; privacy FAIL. QA tidak membuktikan bridge meneruskan raw HTTP header/body: SDK-only tanpa forwarding juga bocor dari locals/message. Summary tidak menentukan provenance tiap field. Safe config belum diuji, jadi tidak disimpulkan pasti gagal.
- ORM memakai `model.new()`, request synthetic; bukan persisted fixtures/full dispatch/log/UI. Unhandled outside exception dan separate capture-method failure NOTRUN. Transport failure terbatas mempertahankan response/exception identity. Historical passes tidak dipromosi menjadi UAT v3.
- Containment HOLD historis: AGENTS dirty unattributed, dipertahankan tanpa tuduhan/revert. Cleanup identified resources terverifikasi historis, tetapi anonymous Odoo volume IDs tidak tercatat, jadi bukan all-volume audit.

## 3. Source contract yang dipertahankan

Addon manifest13.0.1.0.0 depends amr_service_client; external Python sentry_sdk/yaml, pins SDK2.73.0/PyYAML6.0.1 di addon. Core manifest depends base/web/base_setup/amr_resource; tidak SDK. Root `requirement.txt` Requests2.31.0 dan komentar Python3.7.9 adalah source state, **bukan authority target3.7.3 atau approval produksi**. Empty core requirements bukan seluruh graph dependency; manifest/import/prerequisite lain tetap diperhitungkan.

`AMR_SENTRY_CONFIG` hanya pemilih path; unset/kosong => `/etc/odoo/amr_sentry.yaml`; .yaml/.yml safe YAML, .json JSON; explicit invalid override tidak fallback. Root harus mapping dengan sentry dan service_client mapping. Policy hanya enabled bool (default false), mode case-sensitive all/error/selected/none (default none); unknown policy invalid. Top-level extra saat ini diabaikan: tidak menambah strict top-level rule tanpa kebutuhan. Hanya sentry menjadi SDK kwargs; policy tidak ikut.

Load/init sekali import per proses, bukan per DB atau hot reload. SDK/config/init failure non-fatal; reporter disabled, diagnostic generik tanpa DSN/config/error text. `yaml` diimport sebelum runtime guard: missing declared PyYAML dapat memblokir optional addon import, bukan dijanjikan non-fatal. Core-only tidak memerlukan optional package.

Semua aktif memerlukan enabled true, mode reportable, DSN string nonempty dari file, valid safety profile, SDK siap. Disabled/none/missing DSN => zero init/capture aplikasi; tidak mengambil SENTRY_DSN/old Settings untuk enable. Old settings UI/imports dihapus, stale ir.config_parameter tidak dimigrasi/tidak efektif, opt-in field/UI tetap.

| Mode | Sukses | Gagal | Eligibility |
|---|---|---|---|
| all | satu fixed message `Service client request completed`, level info | satu original exception capture, subject D-EX | tidak perlu opt-in |
| error | nol | satu original exception capture, subject D-EX | tidak perlu opt-in |
| selected | satu fixed message | satu original exception capture, subject D-EX | record client opt-in wajib |
| none | nol | nol | no init |

Explicit service_client mengambil precedence; bila None dan self singleton, gunakan bound self; absent/empty/non-singleton tidak eligible selected. Tidak fallback kw.sentry_opt_in, tidak mengembalikan client names/tags/extra lama.

## 4. Proposal delta paling kecil yang koheren — M1 (BELUM APPROVED)

Pertahankan bridge/model/reporter API dan SDK2.73; jangan Hub redesign, custom scrubber, nested data_collection atau broad privacy framework. Tambahkan validasi file di optional config loader sebelum init, dan ganti contoh/docs dengan safety profile eksplisit. Nilai tidak disuntikkan/direpair/diganti kode. Key bertipe exact: bool bukan string/int; integer0 bukan false. File aktif minimal dsn+policy yang dulu lolos sekarang **ditolak sebelum init**. Ini schema breaking delta yang memerlukan approval, bukan klaim accepted behavior lama.

Profil di bawah terdiri dari 12 safety assertions: 3 menutup integration defaults/auto/explicit; 5 menutup locals/source/PII/body/breadcrumb channels; 3 menutup session/client-report/metrics otomatis; debug false mencegah config-sensitive SDK diagnostics. Bukan 20-option universal SDK schema. enable_logs tidak perlu field baru: SDK2.73 default false, tidak boleh dioverride dalam narrow allowlist. Tracing/profiling tidak dikonfigurasi, tidak ada integrations/call API terkait; jika real envelope membuktikan output otomatis lain, gate FAIL dan revisi minimum baru, bukan menambah opsi diam-diam.

```yaml
sentry:
  dsn: "https://public@example.invalid/1"  # fixture; real DSN dikelola operator
  default_integrations: false
  auto_enabling_integrations: false
  integrations: []
  include_local_variables: false
  include_source_context: false
  send_default_pii: false
  max_request_body_size: "never"
  max_breadcrumbs: 0
  auto_session_tracking: false
  send_client_reports: false
  enable_metrics: false
  debug: false
service_client:
  enabled: false
  mode: none
```

Untuk aktif, operator mengganti enabled/mode dan DSN, bukan safety values. Proposal sentry allowlist = `dsn` + 12 safety keys di atas + optional strings `environment`, `release`, `server_name`, `project_root`. String metadata harus synthetic/non-customer; gunakan nilai file eksplisit dalam acceptance fixtures untuk menguji env contamination. Arbitrary SDK options di luar allowlist (termasuk unknown, data_collection, custom callback/filter/transport, enable_logs, with_locals/request_bodies SDK1.9) ditolak. Tidak membuat nested schema. Optional metadata absent dapat memakai SDK auto/environment defaults: **bukan file-only metadata/privacy PASS**, harus dibaca oracle D-GLOBAL; operator exclusive-process acceptance harus memilih metadata file yang eksplisit dan disetujui.

Pada enabled true/mode reportable/DSN tersedia, setiap safety key wajib exact nilai di contoh; omission/unsafe => disabled dengan generic diagnostic, zero init, no retry. Pada disabled/none tidak init; loader tetap menolak malformed/unknown/type unsafe bila diberikan, tetapi omission safety keys tidak boleh mengaktifkan apa pun. Missing DSN menonaktifkan; dsn null/absent/empty tidak fallback; non-string nonempty invalid. Hanya nilai sentry dari file diteruskan ke sdk.init; tidak kwargs privacy tersembunyi. SDK native standard scrubber tetap mekanisme SDK, bukan custom sanitizer addon. `send_default_pii` deprecated tetapi tersedia pada exact2.73; jangan tambahkan data_collection bersamaan. Fakta API diverifikasi statis consts/client2.73, **bukan test flag efektif**.

## 5. Batas bisnis dan privacy

Wrapper ServiceClient.call -> core report_outcome -> env['service.client'] hook -> optional reporter; optional hook hanya success/client/exception, tidak melampirkan response/method/private kwargs. Business bridge menerima kwargs, bukan bukti ia meneruskan ke capture SDK. Call sukses return response, raise_exception true re-raise asli. Pre-assignment response + raise_exception false punya potensi UnboundLocalError baseline; catat/gate terpisah, jangan perluas remediation.

ServiceClientSend.dispatch_send menggunakan request langsung dan log bisnis, bukan call; log.send write state/response sebelum hook, gagal sebelum client/write bisa tidak punya capture. run_action tidak report ulang call exception; handler/next-action exception outcome tersendiri. Sukses request+handler gagal boleh dua event; dedup tidak menyamakan dua outcome. Existing logs bisa menyimpan request/response lewat logic bisnis: ini bukan janji sanitasi menyeluruh database/log lama. Telemetry diagnostic generic dan Sentry-envelope privacy diuji terpisah dari baseline business log exposure; temuan bisnis baru dilaporkan, bukan ditutupi atau diam-diam diubah.

### D-EX — OPEN OWNER PRODUCT GATE (bukan waiver otomatis)

Original exception dapat memuat token/customer data dalam message, chained cause, path/URL. Flags locals/body/PII tidak menjamin arbitrary exception text bersih. Pilih eksplisit: **EX-A** mempertahankan original exception dengan residual text/path yang didefinisikan/diterima secara spesifik (bukan janji zero arbitrary data dan bukan legacy security waiver); atau **EX-B** strict zero-data tetap wajib, sehingga kontrak telemetry exception perlu desain ulang/approval baru. Sampai Owner memilih: UAT exception-text tidak bisa PASS, overall privacy/acceptance HOLD. Draft ini tidak mengganti exception, menambah scrubber, maupun menyatakan EX-A disetujui.

### D-GLOBAL — OPEN SDK PROCESS / ISOLATION GATE

Current reporter menyimpan module sentry_sdk lalu memakai global capture APIs; build_reporter memanggil sdk.init process-wide. Source SDK2.73 scope._merge_scopes:437–455 menyalin global, isolation dan current scope; get_client:463–495 memilih client ambient. new_scope/isolation_scope bukan fresh empty guarantee. Safe file mengurangi defaults, **tidak mengisolasi scope atau another-SDK initialization**.

Rekomendasi minimal: evaluasi **proses khusus/exclusive** tanpa SDK init/integrations/event processors lain dan tanpa customer ambient scope; simpan sebagai deployment/test eligibility constraint yang harus dipilih Owner dan dibuktikan QA. Bukan persetujuan constraint otomatis dan bukan jaminan fail-closed terhadap aktor lain yang memanggil global SDK. Jika concurrent SDK/global scopes/multi-DB tidak bisa dilarang atau UAT14/18 gagal: HOLD, minta desain adapter terpisah. Tidak mengimpor solusi Hub1.9 atau menganggap fresh Scope menyelesaikan merger. Disabled addon hanya berarti reporter tak capture/init; tidak mengklaim mematikan SDK yang diinisialisasi pihak lain.

## 6. Scope perubahan berikutnya (proposal, bukan izin edit)

- Utama: amr_sentry/services/config.py validation M1; tests config/reporter dan real-SDK acceptance fixtures; README root/addon/operator dengan complete safe example, 3.7.3 authority, restart/exclusive process/exception residual caveat.
- runtime.py/reporter/model/core bridge tidak direwrite kecuali delta perlu dan di-review; existing generic diagnostics harus tetap secret-safe. Core tests/documentation dapat disesuaikan untuk approved contract, bukan scope bisnis baru.
- Root requirement.txt: komentar3.7.9 vs target3.7.3 harus dikoreksi/documented setelah approval; pin Requests2.31 current source jangan diubah/disebut production-approved. Optional addon requirements tetap SDK2.73/PyYAML6.0.1, core tidak ditambah optional SDK/yaml. Test-only full lock/image terpisah di luar repo, bukan bulk production requirements refresh. README lain menyebut Requests2.21 = stale docs yang dijelaskan, bukan otoritas sandbox.
- Tidak production dependency pin/upgrade, migrasi settings/data, Odoo major, SDK downgrade, integration otomatis, tags/fallback, custom scrubber, UI baru, ref/Plane write/commit/push/merge/deploy dalam Step0 ini.

## 7. Acceptance criteria

| ID | Acceptance criterion | UAT cases |
|---|---|---|
| AC-01 | Core tetap opsional: tanpa amr_sentry/SDK/PyYAML, core tidak import/init/capture SDK dan hook no-op tetap usable. | UAT-01, UAT-20 |
| AC-02 | Konfigurasi satu file YAML/YML/JSON: path default/override, mapping/policy/defaults tepat; invalid non-fatal dan tidak fallback ke env/Settings. | UAT-02, UAT-03, UAT-04 |
| AC-03 | Delta validasi safe-profile file-only: setiap safety key wajib bertipe/nilai exact; missing/unsafe/unknown ditolak sebelum SDK init; kwargs efektif identik file, tanpa injected privacy kwargs. | UAT-05, UAT-06, UAT-07 |
| AC-04 | Mode all/error/selected/none dan enabled/DSN sesuai matriks; selected memerlukan record opt-in, precedence client eksplisit dipertahankan; tanpa kwargs fallback/tags lama. | UAT-04, UAT-08, UAT-09 |
| AC-05 | Dengan real SDK, nol event di luar hook dari logging/unhandled exceptions; integrations efektif kosong; nol automatic telemetry yang tak diminta. | UAT-10, UAT-11, UAT-22 |
| AC-06 | Payload telemetry tidak memuat private args/body/header/credential/customer markers, locals/vars, source context atau ambient metadata; diagnostic telemetry generik; exception-text dinilai terpisah D-EX. | UAT-12, UAT-13, UAT-14 |
| AC-07 | Hasil bisnis call/dispatch/log/action dipertahankan; failure SDK init/capture/transport best-effort; bukan masking business failure atau memperbaiki defect baseline diam-diam. | UAT-03, UAT-15, UAT-16, UAT-17 |
| AC-08 | Tidak double report satu outcome; request-success lalu handler-error adalah dua outcome, bukan satu duplikat. | UAT-16, UAT-17 |
| AC-09 | Load/init sekali per proses, restart reload; file/Settings/env dan SDK global/current/isolation scope tidak mencemari policy atau lintas DB/worker; D-GLOBAL wajib diselesaikan. | UAT-07, UAT-14, UAT-18, UAT-21 |
| AC-10 | Target tepat Odoo 13/CPython 3.7.3; core-only, optional fresh install dan upgrade diuji dengan full inventory/constraints test-only disetujui; pin produksi tidak diubah implisit. | UAT-01, UAT-19, UAT-20, UAT-24 |
| AC-11 | README/operator konsisten, contoh aman lengkap, per-client UI opt-in ada, global UI lama tidak efektif; root requirement dan optional packaging dijelaskan tanpa klaim produksi. | UAT-21 |
| AC-12 | Semua evidence terikat candidate/spec/config/environment, oracle per-case, no-egress dan cleanup per-resource termasuk volume IDs; tidak mewarisi PASS/waiver historis. | UAT-22, UAT-23, UAT-24 |

## 8. Gates dan approval

G0: Owner menerima exact hashes v3 dan M1/schema change; menetapkan D-EX dan D-GLOBAL atau menyatakan keduanya remain HOLD. Clean/accepted worktree snapshot baru diperlukan sebelum implementation; unknown AGENTS preserve, ownership tidak ditebak. G1: izin implementasi terbatas terpisah, source candidate SHA baru + rebind dokumen/evidence tanpa mewarisi acceptance otomatis. G2: izin test-only sandbox terpisah untuk approved lock/image/config, real SDK, persisted Odoo dan focused negatives UAT. G3: QA verdict per-case + privacy/process/security decisions; nol critical failing oracle, seluruh subcases selesai tanpa mengubah FAIL menjadi waiver diam-diam. Production security/risk/release/deploy/merge tetap gate terpisah; legacy dependency smoke tidak menutup advisories.

Rollback rencana (belum dijalankan): disable/none file dan restart seluruh worker, cek core; restore paired disposable DB/filestore/config fixture untuk rehearsal. Jangan in-place downgrade production deps; baseline image immutable, buang run-owned candidates saja, exact volume IDs dicatat sebelum create/remove; jangan broad prune. Risiko egress/secret leak => stop/karantina evidence, bukan hapus jejak. Semua UAT v3 **NOT RUN**.
