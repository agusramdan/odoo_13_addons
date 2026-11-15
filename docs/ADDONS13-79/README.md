# ADDONS13-79 — navigasi dokumentasi

## Mulai di sini

- [PRD](PRD.md) — kebutuhan dan batasan.
- [UAT](UAT.md) — skenario dan kriteria pengujian.
- [Metadata persetujuan](ACCEPTANCE-METADATA.md) — persetujuan Owner atas byte PRD dan UAT berdasarkan hash. Persetujuan spesifikasi **bukan** hasil atau kelulusan UAT.

## Status dan bukti

- **SCOPE-01: OPEN.** Pengecualian cakupan masih memerlukan keputusan; jangan menganggapnya sebagai waiver.
- **Ledger generation 3: 3/3.** Catatan ini bukan izin untuk mereset ledger atau menjalankan ulang pengujian.
- Hasil teramati generation 3 yang dilaporkan secara historis: **28 tes, 2 kegagalan; 18 tes, tanpa kegagalan; 44 tes, 1 kegagalan**. Hasil ini terikat pada snapshot kerja yang tidak bersih: commit `ec27a8b2a14447867575f4024baafc3c9e541ced` ditambah dua overlay pengujian `amr_resource`. Ini bukan hasil untuk perubahan baru atau kandidat saat ini, dan bukan bukti lulus UAT native secara penuh.

## Dokumen kerja Step 4

Dokumen berikut adalah persiapan dan pemetaan historis, bukan persetujuan atau hasil UAT terkini; status dan kandidat di dalamnya berlaku pada saat dokumen dibuat.

- [Persiapan tanpa runtime](STEP4-PREPARATION-NO-RUNTIME.md)
- [Pemetaan assertion statis](STEP4-ASSERTION-CROSSWALK-STATIC.md)
- [Draft D01 dan desain harness](STEP4-ATOMIC-D01-AND-HARNESS-DRAFT.md)
