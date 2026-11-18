# Review: REQUEST CHANGES

Basis: working tree terhadap `a4b49e2153ef69d71f116834618a7efd1300677d` (`RESOURCE2`), spec dan test plan yang disetujui menurut instruksi owner. Dokumen masih berlabel draft. Snapshot review: model SHA-256 `f5621dae06bede8c1085c255f5bf3cd825404716f82c3ac48337b672ea25bb13`, view `8bda9ba942d597d8992dbca92bcbc107e6cb60a7437d18ec4fc02ae93b62f48a`, browser test `c59f77f110bccbb577efa37f3f3c87fff0fc61a06dad9b1ff3b23b13f0073238`, integrasi `712ff079ce601e3df893842e8a943f962a6d457423c89e2c5525dc0042268b47`. QA mengubah tes browser paralel; hasil dan temuan browser hanya berlaku pada snapshot tersebut dan perlu dicocokkan ulang dengan file final. Tidak mengubah kode atau test.

## Temuan

1. **High - guard otorisasi unarchive dapat dilewati untuk draft arsip** - `amr_resource/models/trust_registry.py:265-274`; ACL `amr_resource/security/ir.model.access.csv:6`. User code admin memiliki write issuer. Record draft dapat dibuat inactive atau diarsipkan dengan `write({'active': False})` karena guard draft mengizinkannya; kemudian `write({'active': True, 'client_id': 'changed'})` tidak masuk cabang `unarchiving` karena dictionary bukan tepat `{'active': True}`. Record tetap draft sehingga masuk `others` dan super write mengaktifkannya tanpa trust admin. Pemeriksaan baru menutup kasus unarchive standar pada arsip disable, tetapi tidak semua unarchive. Periksa setiap perubahan inactive ke active tanpa bergantung pada key lain, dan batasi nilai tambahan sesuai aturan draft; tambah tes ORM negatif code admin dan positif trust admin untuk batch dan gabungan nilai. **Security: access control; judgement.**
2. **Medium - test browser unarchive gagal** - `amr_resource/tests/browser/test_browser.py:116-119`. QA melaporkan `test_archive_reactivation` gagal `Timeout: action menu` setelah arsip dan buka kembali (`.runtime/browser_archive.log`); belum terbukti apakah selector atau UI yang salah. Investigasi DOM/UI, perbaiki penyebab dan jalankan ulang sampai unarchive standar, draft aktif, lalu production terverifikasi. **Tests; judgement.**
3. **Medium - tambah/hapus empat One2many via UI belum diuji** - `amr_resource/tests/browser/test_browser.py:129-196`. Test mengedit anak yang disiapkan ORM dan memeriksa readonly, tetapi tidak tambah/hapus melalui UI draft. AC-3 dan rencana test memerlukannya pada setiap relasi, dengan constraint existing. Tambah dan jalankan skenario browser valid. **Tests; judgement.**

## Tindak lanjut review sebelumnya

- Unarchive standar `write({'active': True})` kini memeriksa trust admin sebelum mengubah state. Test integrasi code admin negatif dan admin positif tersedia; pengecualian gabungan nilai pada temuan 1 masih terbuka.
- Batch arsip plus production divalidasi sebelum kedua write; kedua urutan dicakup unit dan integrasi. Ini membuktikan penolakan validasi tersebut, bukan atomicity seluruh kemungkinan kegagalan pada dua super write.
- Tombol production dan archive disembunyikan untuk arsip; `action_to_draft` masih dapat memulihkan arsip disable menjadi draft, sesuai hasil state yang diwajibkan. Jalur unarchive standar browser belum lulus.

## Verifikasi dan batas

- `git diff --check`: lulus pada snapshot review ini.
- Laporan QA `.runtime/test_report.md`: unit Docker 45 passed, coverage line 63% (1.142 statement, 417 missed; tests/fixtures dikecualikan); denominator dan pengecualian belum dikonfirmasi owner sehingga gate coverage belum diputuskan. Unit memakai mock.
- Laporan QA: integrasi Odoo 13 kelas `TestIssuerLifecycle` 9 lulus; browser lifecycle, children, draft form dan nonadmin masing-masing lulus; archive reactivation gagal seperti di atas. Hasil QA dilaporkan dari snapshot eksekusinya, bukan dijalankan ulang dalam review ini; cocokkan hash sebelum menganggap hasil berlaku untuk final.
- Audit keamanan dibatasi diff dan ACL/guard terkait, bukan audit menyeluruh semua jalur RPC/controller/sudo. RPC di luar cakupan spesifikasi. Repository sibling dan addon eksternal tidak diperiksa. Tidak ada klaim UAT atau acceptance; tidak ada commit.

Guidelines read: Imports; Naming and model layout; Translate only static literals; Recordsets, domains and context; Computes, onchange and constraints; Methods and extension points; Transactions and exceptions; Batch ORM calls; Performance conventions; Tests; Plain ASCII punctuation; Changes in a stable version; Views, actions and data records; Anchor view inheritance; odoo-security. Tidak ada file `static/` berubah.
