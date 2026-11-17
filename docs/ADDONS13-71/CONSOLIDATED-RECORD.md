# ADDONS13-71 — consolidated record

**Diperbarui:** 2026-11-17
**Fungsi:** satu ringkasan kerja bersama dua dokumen requirement, `PRD.md` dan `UAT.md`. Keduanya salinan byte-identik dari PRD/UAT v6 yang diterima; hash acceptance tetap berlaku. Dokumen dan laporan eksternal di `docs/reports/ADDONS13-71/` tidak dihapus.

## Status akhir

- **Step 4:** `ACCEPTED_WITH_WAIVER`, bukan PASS agregat. Owner me-waive hanya perbandingan baseline AU13 dan AU14; risiko kompatibilitas provider yang mendasari tidak diterima.
- **UAT attempt 1:** FAIL/incomplete — 54 test method mulai, 1 gagal, 2 error.
- **UAT attempt 2:** runner exit 0 — 54 method, tanpa failure/error pada suite kandidat. Ini bukan bukti perbandingan baseline AU13/AU14.
- Perbandingan baseline AU13/AU14: **NOT RUN**. Dua dari tiga percobaan terpakai; tidak ada percobaan ketiga.
- **Plane:** ADDONS13-71 berstatus Done. Tindak lanjut terpisah ADDONS13-99 (AU13) dan ADDONS13-100 (AU14), keduanya Backlog.
- **PR #47:** terbuka ke `main`; belum merge. Checks terakhir terpantau pending. PR review/acceptance, merge, release, dan deployment tetap terpisah.

## Kontrak yang berlaku

- `active_log` adalah snapshot saat client dibuat dan diteruskan ke sender normal. Explicit sender `True`/`False` menang; omitted berarti `False`; explicit `None` mengikuti endpoint bila ada. Flag off meniadakan log sukses, bukan percobaan log error. `active_log` di payload tetap data JSON.
- `params` hanya dikirim jika truthy. URL truthy override menang atas `path`; fallback endpoint memakai `get_url(path or self.path)`; tanpa endpoint tidak ada fallback `path`. URL falsy dan hasil header normalisasi falsy dihilangkan sebelum provider. Input headers asli, termasuk `None`, tetap diteruskan ke normalizer. Provider dapat mengubah context sesudahnya.
- Risiko URL/header yang diterima terbatas pada potensi inkompatibilitas provider strict yang membutuhkan key yang dihilangkan, dan risiko tujuan URL override/SSRF. Ini bukan penerimaan risiko keamanan atau kompatibilitas secara umum.
- Keputusan refaktor D1–D5: (D1) tolak bentuk positional ambigu sebelum provider/network; jangan ubah POST menjadi GET diam-diam; (D2) pertahankan input headers asli termasuk `None`; (D3) method per-call dan stored yang sama-sama falsy gagal sebelum provider/transport; (D4) report method efektif setelah provider, fallback ke input bila context belum tersedia; (D5) whitelist keyword per entry point dan tolak unknown sebelum provider/network. D5 mengikuti matriks Lead per entry point, bukan filter terhadap payload/kwargs domain data.
- Target runtime: Odoo 13 / CPython 3.7.3.

## Hash-bound dokumen dan arsip

Nama `DRAFT` pada file asal tidak membatalkan acceptance yang tercatat terpisah. Penerimaan berikut terikat pada hash persis:

- PRD/UAT awal logging: `a8f39e9bac135b0228e599e552423ee498eb525211713e086869f0ff26365ead` / `85a55bbb2ce23f7484e54c6c1f7b4bca4695ae8515db34db1484dbbbf18a4d80`; record acceptance `c43ff4b8aef9f0876202ab32f3b823e74bbcdc845297e18efebfa24782904a30`.
- Amendemen URL/headers: PRD/UAT `0b7bb752aed021ad3edc4d021032c96a2d110145f75067e8d1c68a36ada20c72` / `7eadd09c9f044e41a9091070075dfaa977acff1b17a983b4be1af96bdc99fc88`; Owner acceptance `7cfc24449a32f845478d7f2c28f3109a6ac39b219a2df745f4029036e0f5ebfe`.
- Refaktor v6: PRD [`PRD.md`](PRD.md) SHA-256 `3d724eb1fffd74cf6532f7aa67c456c2fb74e231f6afecaab92a5f534c86225d`; UAT [`UAT.md`](UAT.md) SHA-256 `3501f674678c83b35a0439285dcc99fe160921003379c3d3eaa54074e3684725`; TRACE SHA-256 `735fbbac6ca03cfa64bb8e014545e6b6b743d4f09056e9461bb1582adc136169`; Owner acceptance `0cf5eecfe50ae900fb21c3ae508731666ed7fe4352828bda12b62c513ec6595f`; manifest `36736c123ad94731d3080c0f8f2370375d1b29b3529fead344817618d36a69cc`.
- Step 4 disposition file SHA-256: `d2a8f7da97f294a1331c02b005aa380ae4ad16f96f3dc9f5d109fdc5ecbf3673`.

PRD/UAT salinan di root diverifikasi byte-identik dengan acceptance hashes. Sumber historisnya tetap dapat dipulihkan dari commit `08a044c1267ddc66a4c6b7d5292d6059ee2d0183`; Step 4 disposition asal dari `11991229793eb6f0339ab745c548904383457ab4`. Owner acceptance dan Lead D5 oracle tetap di `/home/ubuntu/docs/reports/ADDONS13-71/`. Attempt-1 report tetap di `/home/ubuntu/docs/reports/ADDONS13-71/step4-testprep-f28d605/ATTEMPT-1-RESULTS-2026-11-17.md`; private raw logs tidak disalin ke sini.

## Pelaksanaan dan handoff

- Step 2: `08a044c1267ddc66a4c6b7d5292d6059ee2d0183`; 206 offline unit tests passed pada Python 3.7.3.
- Step 3: Lead PASS untuk source snapshot `f28d6053f87cf71c9e87584e4d39909c697f1331`; cakupan review tetap terbatas pada snapshot itu.
- Step 4 candidate test snapshot: `f28d605-step4-prep-v5`, manifest `c092c83f6052475570dea2ec62b0579b007b954e864908df3b25e475e655ae54`. Hasil attempt 1 tetap FAIL; attempt 2 tidak mengubah actual perbandingan baseline yang NOT RUN. F15 berstatus `ACCEPTED_WITH_WAIVER`, bukan PASS.

## Penghapusan dokumen tersebar

Dokumen versi/amendment di subdirektori `docs/ADDONS13-71/` dihapus dari working tree. Kini root berisi hanya `PRD.md`, `UAT.md`, dan `CONSOLIDATED-RECORD.md`. PRD/UAT dipulihkan byte-identik dari snapshot v6; acceptance hashes tetap sama. Draft antara v1/v2/v3/v5 bukan kontrak tambahan. File tracked sebelumnya tetap dapat ditelusuri melalui Git history; draft lokal yang tidak pernah di-commit dihapus sesuai instruksi Owner. Konsolidasi ini tidak mengubah acceptance, actual UAT, atau gate.
