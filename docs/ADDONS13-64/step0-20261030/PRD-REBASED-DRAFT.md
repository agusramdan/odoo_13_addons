# ADDONS13-64 — PRD analisis ulang Step 0

**Status: DRAFT — NOT ACCEPTED.** Versi 20261030, inspeksi statis pra-rebase; bukan persetujuan implementasi/rilis. Candidate SHA pasca-rebase: **3774c6fda99aab9b5f3d03241a4a876d1cb493b1**. Dokumen harus diikat ke SHA kandidat baru, ditinjau ulang, dihitung ulang hash-nya dan diterima exact-hash sebelum gate berikutnya.

## 1. Tujuan dan evidence binding

Pisahkan SDK Sentry dari `amr_service_client` ke addon opsional `amr_sentry`, tanpa mengubah hasil layanan dan tanpa dependency SDK wajib pada inti. Implementasi sudah ada; ini evaluasi ulang existing implementation, bukan spesifikasi greenfield.

- Feature diperiksa melalui committed blobs: `ADDONS13-64` pada `eaf2c7f016ad9c0ae7945528529e0b73727bed4c`.
- Target remote-tracking lokal: `origin/main` pada `ac1bcbd66261b92c10078f2a8744a657a3b6490c` (bukan local main `c08b050cfd85ccc5c705eb92852e57626eb82806`). Tidak fetch/ubah refs dalam analisis ini.
- Merge-base `5de9a5776aecf8383ce580ed0446ee470f1c5425`; feature delapan commit dan target satu commit sesudah base. Incoming empat path `amr_resource`; feature 32 path; irisan path kosong, bukan jaminan tidak ada konflik semantik.
- Source inventory/blob/hash: `EVIDENCE-SNAPSHOT.json`. Temuan dan rebase terbatas Git: `STEP0-REPORT.md`.
- Issue cached: `/home/ubuntu/.hermes/profiles/lead/cache/scratch/addons13-64-discovery.json`, UUID `2753318a-cadc-4177-9493-db554b63d7c6`. Plane tidak diakses/diubah sesuai batas tugas; komentar terbaru tidak diverifikasi langsung. Keputusan historis di bawah bersumber cached issue dan artefak lokal, bukan klaim pembacaan komentar live.

## 2. Scope dan keputusan yang dipertahankan

### In scope

1. Addon `amr_sentry` memiliki SDK init, config loader, reporter dan extension ORM `_inherit = 'service.client'`; core hanya menyediakan hook no-op dan bridge ORM best-effort.
2. File konfigurasi YAML/JSON tunggal; `AMR_SENTRY_CONFIG` hanya memilih lokasi, unset/kosong memakai `/etc/odoo/amr_sentry.yaml`. Ekstensi `.yaml`/`.yml` memakai safe YAML, `.json` memakai JSON. Override eksplisit invalid tidak fallback.
3. Top-level `sentry` dan `service_client` wajib mapping. Hanya `sentry` diteruskan sebagai kwargs SDK. Policy menerima `enabled` boolean default false dan `mode` enum case-sensitive `all/error/selected/none` default none; policy key lain invalid. Existing loader tidak menolak key top-level tambahan; jangan mengklaim strict top-level allowlist.
4. Load dan initialize sekali pada import modul per proses; restart seluruh proses/worker untuk reload. Tidak hot reload/polling. Fork/preload dan multi-registry perlu validasi runtime, tidak disamakan dengan init per database.
5. Gate aplikasi: enabled true, mode reportable, DSN truthy dari file. Config hilang/tak terbaca/malformed/schema invalid, import SDK gagal, init gagal: reporter disabled non-fatal, warning generik tanpa config/DSN/exception text. Capture gagal tidak mengubah hasil bisnis.
6. Global Settings Sentry dihapus dari model imports/manifest/view; nilai lama `ir.config_parameter` tidak dimigrasi dan bukan sumber efektif. Field/UI `sentry_opt_in` per client tetap ada.
7. Pin existing `sentry-sdk==2.73.0`, `PyYAML==6.0.1` berada pada requirements addon opsional, manifest external Python `sentry_sdk`, `yaml`. Ini kondisi source, **bukan approval kompatibilitas dependency**. Resolusi deployment menunggu gate dependency.
8. Privacy mengikuti mekanisme SDK standar; tanpa custom scrubber dan tanpa lampiran eksplisit request/response body, header, credential, customer data. Reporter mengirim pesan sukses tetap atau exception asli. Tidak ada jaminan semua informasi exception otomatis aman; periksa event dengan SDK nyata di transport lokal.

### Out of scope / larangan sesi ini

Tidak implementasi, edit source, menjalankan runtime/tests/install/resolver, modifikasi refs, rebase aktual, Plane, commit/push/PR/merge/deploy. Tidak menyentuh branch/worktree lain. Tidak migrasi settings lama, menambah custom scrubber, mengubah dependency pins/requests Odoo secara diam-diam, atau memperluas perbaikan `amr_resource` di feature.

## 3. Perilaku mode yang harus dipertahankan

Seluruh baris membutuhkan konfigurasi valid, enabled true, DSN tersedia dan SDK siap. Tanpa gate itu tidak init atau capture aplikasi.

| Mode | Sukses | Gagal | Opt-in |
|---|---|---|---|
| all | satu capture_message tetap, level info | satu capture_exception | tidak diperlukan |
| error | tidak capture | satu capture_exception | tidak diperlukan |
| selected | capture_message hanya eligible | capture_exception hanya eligible | record client `sentry_opt_in` truthy wajib; tanpa client tidak eligible |
| none | tidak capture | tidak capture | diabaikan; tidak init |

Baseline helper mempunyai fallback `kw.sentry_opt_in` jika client tidak ada. Reporter baru hanya menerima record client. Normal wrapper memasok record existing, tetapi compatibility helper/direct caller harus diperiksa; fallback hilang bukan otomatis disetujui. Tags/extra baseline (nama client, component, outcome, method/status, integration) juga hilang dari reporter baru. Perubahan metadata perlu keputusan eksplisit bila ada konsumen dashboard; jangan mengembalikan nama/data pelanggan tanpa privacy review.

## 4. Kontrak call flow existing

- `ServiceClient.call()` → prepare/authenticate request → `requests.request` → `raise_for_status` → wrapper `_report_sentry` → `report_outcome(env, service_client=...)` → `env['service.client']._report_sentry` → optional override → REPORTER. Sukses return response; error dengan `raise_exception=True` re-raise asli. Failure bridge ditelan, tidak mengganti outcome.
- `ServiceClientSend.dispatch_send()` membuat request langsung (bukan memanggil call); satu hook untuk hasil request. Error ditangkap lalu membuat business error log; sukses membuat log hanya jika active_log. Tidak menjanjikan queue/ack/retry yang tidak ada di source.
- `run_action_service_client()` tidak melaporkan ulang exception dari call; meneruskan ke error_handle atau re-raise. Exception response handler/next action mempunyai hook sendiri. Sukses request lalu gagal handler adalah dua outcome berbeda, bukan otomatis duplikat.
- `service.client.log.send()` request langsung → tulis state/response tersanitasi → hook jika client tersedia → return self. Error sebelum client terbentuk tidak dapat dilaporkan; write failure dapat menghentikan alur sebelum hook. `dispatch_send()` model log hanya memanggil send dan return self.
- Kontrak baseline yang perlu ditandai, bukan diperbaiki diam-diam: pada `call(raise_exception=False)` jika prepare/request gagal sebelum assignment response, return response dapat menghasilkan UnboundLocalError. Kegagalan business log/handler bukan otomatis kegagalan telemetry. Catat sebagai defect baseline bila direproduksi pada gate terpisah.

## 5. Acceptance criteria dan traceability

| ID | Kriteria penerimaan | UAT |
|---|---|---|
| AC-01 | Core install/load/smoke tanpa addon/SDK Sentry; tidak init/capture/transitive import SDK | 01, 18 |
| AC-02 | File path default/override, YAML/JSON, namespace, defaults, invalid schema dan explicit override fail closed non-fatal, secret-safe | 02–05, 09, 20 |
| AC-03 | Keempat mode dan per-client opt-in sesuai tabel; disabled/missing DSN tidak init/capture aplikasi | 06–08, 21, 22 |
| AC-04 | Init sekali per proses/restart, Settings global tidak efektif, opt-in dipertahankan, upgrade tanpa migrasi lama | 17, 19, 23 |
| AC-05 | call/dispatch/log.send mempertahankan return/state/exception/handler bisnis; failure SDK tidak mengganti outcome | 11–15 |
| AC-06 | Tidak double capture untuk outcome yang sama lintas call/action/dispatch/log; outcome request dan handler dibedakan | 16 |
| AC-07 | Addon tidak melampirkan data request/customer/secret, tanpa custom scrubber; log diagnostik tidak memuat DSN/config; verifikasi SDK nyata tidak diklaim dari mock | 10, 20, 24 |
| AC-08 | Topologi optional install/upgrade menggunakan dependency set disetujui dan konsisten; resolver/pip check/runtime nyata terbukti pada Odoo 13/Python target | 18, 24 |
| AC-09 | Seluruh hasil terikat satu candidate SHA, spec hashes, environment/dependency manifest dan evidence; historical result/waiver tidak otomatis berlaku | seluruh kasus |

## 6. Gap dan risiko acceptance

**BLOCKER dependency:** metadata wheel lokal SDK 2.73.0 mensyaratkan urllib3>=1.26.11; requests 2.21.0 mensyaratkan urllib3>=1.21.1,<1.25. Tidak ada irisan. Root repository memilih requests==2.31.0, bukan bukti kompatibel dengan baseline Odoo. Requires-Python >=3.6 SDK hanya membuktikan rentang metadata interpreter, bukan stack Odoo. Tentukan deployment constraints dan lakukan gate resolver/pip check/real runtime setelah otorisasi; jangan sekadar memaksa install `--no-deps` atau menganggap warning non-fatal sebagai pass. Mengganti SDK/requests memerlukan keputusan scope dan penerimaan baru.

**PENDING candidate:** rebase menghasilkan SHA baru. Tidak ada UAT yang dijalankan pada kandidat baru. Step 0 draft ini harus rebind dan diterima; Step 2/3 lama tidak dapat dinyatakan berlaku penuh otomatis.

**PENDING runtime privacy/gating:** file kwargs diteruskan apa adanya; source tidak menyetel hardcoded privacy/default integration options baseline lagi. SDK bisa memiliki default integrations, env fallback untuk opsi yang tidak diberikan, breadcrumbs atau automatic capture di luar reporter. Gate mode membatasi capture eksplisit reporter, bukan bukti SDK global tidak menangkap event lain. Tentukan apakah AC memaksudkan semua event SDK atau service outcomes saja; lakukan UAT-24 sebelum menyatakan fail-closed global. Jangan menambah defaults/custom scrubber tanpa keputusan.

**PENDING inheritance/bootstrap:** `config.py` mengimpor yaml sebelum runtime exception handler. Manifest menyatakan yaml wajib bagi optional addon; tanpa PyYAML optional import dapat gagal, bukan bukti non-fatal missing declared dependencies. Native hook test hanya memeriksa callable, yang juga dipenuhi core no-op; perlu test efektif override/capture. Process-wide import berpotensi menyalakan SDK saat addon discovered/imported meski database lain belum install; validasi multi-registry/preload.

**PENDING regression:** fallback helper opt-in, metadata removal, pre-client errors/write failures dan legacy `raise_exception=False` edge belum terbukti pada kandidat baru. Existing source tests/mocks tidak membuktikan registry/transport nyata.

**UPSTREAM mitigation statis:** target menghapus seed PS256 yang ditolak code-owned catalog dan mengganti dua model RegistryAccess direct subclass dengan models.Model plus `_inherit` access mixin. Ini menangani pola blocker historis di source; bukan klaim install/upgrade sekarang sukses.

## 7. Gates, rollback dan keputusan yang diminta

1. Developer hanya operasi rebase Git yang diotorisasi; verifikasi clean/pinned refs dan simpan before/after evidence. Berhenti pada konflik atau target drift, tanpa implementasi.
2. Analis rebind draft ke candidate baru dan tinjau diff; Owner/Lead menerima exact-hash spesifikasi baru atau meminta revisi. Tidak memindahkan acceptance/waiver historis otomatis.
3. Putuskan dependency set dan batas SDK-global versus explicit service policy; konfirmasi kompatibilitas helper/tag jika masih digunakan. Hanya sesudah otorisasi lakukan review/runtime/UAT kandidat baru.
4. Step 3 belum PASS; Step 4/PR/rilis belum dapat direkomendasikan.

Rollback Git hanya untuk operasi rebase gagal: `git rebase --abort` di feature worktree; tidak reset branch lain. Setelah rebase sukses, rollback ke SHA lama memerlukan izin terpisah, tidak hard reset otomatis. Rollback deployment di masa depan: disabled policy atau mode none lalu restart semua worker, atau uninstall optional addon setelah backup/validasi registry; core tetap berfungsi. Tidak mengandalkan old Settings/env DSN untuk mengaktifkan ulang. Tidak ada deployment/rollback dijalankan dalam sesi ini.

## 8. Rekonsiliasi dokumen lama

PRD/UAT Candidate v2 lama tetap utuh; hashes aktual sama dengan acceptance record cached, walaupun header internal masih menyatakan pending. Issue description juga masih memuat keputusan terbuka dan UAT awal pada 397dc6d; evidence lokal lebih lanjut menyatakan komposisi eaf2c7f + dua overlay dependency memiliki 9 PASS, 11 NOT RUN, 1 PARTIAL (21 kasus). Itu hasil historis komposisi, bukan hasil clean rebased tree. UAT-20 final PARTIAL; Owner hanya mengecualikan rendered-browser subcriterion, tidak seluruh kasus dan tidak mengubahnya ke PASS. Waiver tidak diasumsikan berlaku ke candidate baru. Komentar Plane terbaru tetap perlu verifikasi oleh pihak berwenang; analisis ini tidak mengakses Plane.


## Binding kandidat pasca-rebase oleh Lead

Kandidat analisis: `3774c6fda99aab9b5f3d03241a4a876d1cb493b1`, target `ac1bcbd66261b92c10078f2a8744a657a3b6490c`. Rebase Git-only selesai tanpa konflik; Lead mengulang range-diff: 8/8 patch setara, feature clean, target ancestor, diff --check exit 0. Tidak ada runtime/tests yang dijalankan. Dokumen ini tetap DRAFT / NOT ACCEPTED; bukan izin Step 1 atau waiver. Bagian inspeksi pra-rebase di atas dipertahankan sebagai provenance; pernyataan PENDING/rebase belum dijalankan pada versi awal disupersede oleh binding ini.

Lead membaca seluruh 19 komentar live Plane (next_page_results=false), snapshot `PLANE-COMMENTS-SNAPSHOT.json`. Komentar terbaru mengonfirmasi browser-only waiver UAT-20 pada kandidat lama eaf2c7f; UAT-20 tetap PARTIAL. Tidak ditemukan keputusan komentar baru yang menggantikan konfigurasi yang sudah dicatat. Tidak ada perubahan Plane.
