# Draft rencana test — amr_resource

**Status: DRAFT, menunggu persetujuan owner sebelum development.** Skenario berikut rencana, bukan hasil. Eksekusi **NOT RUN**; coverage **belum diukur**.

## Persiapan
- Odoo 13 dan database uji terisolasi; install addon serta dependensi manifest (`base`, `web`, `mail`, `base_setup`, Python `jwt`, `cryptography`; `amr_resource/__manifest__.py:9,21`). Verifikasi registry/view addon `amr_resource` pada runtime; `resolver_key` tidak ada dalam view addon tersebut saat ini. Gunakan data sintetis; browser diperlukan untuk bukti UI.
- Investigasi `test_trust_state.py:72,199,219-220` yang merujuk `AmrResourceIssuer` alih-alih `OidcResourceIssuer` (`models/trust_registry.py:142`); `test_trust_child_guards.py:47,56` sudah memakai nama aktual. Catat blocker aktual; jangan mengasumsikan hasil.

## Unit
1. Default/create/copy draft; untuk record aktif, uji keenam transisi antar state berbeda, termasuk disable ke draft dan production. Uji penolakan target invalid dan transisi ke state sama sesuai perilaku existing; uji batch dengan transisi tidak valid tanpa perubahan parsial.
2. Uji unlink disable menjadi inactive tanpa penghapusan fisik; draft/production ditolak. Uji unarchive record disable arsip menjadi aktif draft; pastikan arsip tidak dapat langsung menjadi production, lalu uji transisi draft aktif ke production.
3. Uji guard parent `oidc.issuer.register` dan regresi guard anak yang sudah ada tanpa menambah guard anak. Pastikan constraint existing tidak dilemahkan.
4. Target owner: unit line coverage minimal 50% seluruh addon `amr_resource`. Asumsi sementara runner skill mengecualikan tests/fixtures dari denominator Python; pengecualian belum dikonfirmasi owner. Minta konfirmasi sebelum gate; catat perintah, interpreter, persentase, denominator, file dikecualikan, serta keputusan owner. Gunakan runner dan runtime sesuai workflow unit proyek; jika tidak tersedia laporkan setup-blocked, bukan lulus.

## Integrasi dan browser Odoo 13
- Dengan trust admin, buat issuer draft; verifikasi semua field yang sebelumnya editable tetap editable sesuai hak, modifier dan constraint existing. Pada production/disable verifikasi parent readonly. Jangan mengasumsikan field yang sudah readonly menjadi editable.
- Pada draft uji tambah/edit/hapus pada empat relasi One2many dengan data valid; pada production dan disable pastikan masing-masing readonly di UI. Periksa modifier di browser, bukan sekadar inspeksi XML.
- Untuk record aktif uji visibilitas tombol dan keenam transisi berbeda. Arsipkan disable melalui UI; verifikasi inactive dan record masih ada. Temukan arsip, unarchive menjadi aktif draft, lalu transisi ke production; pastikan tidak ada jalur langsung dari arsip ke production.
- Verifikasi akses UI trust admin dan user biasa sesuai ACL dan grup existing, tanpa perubahan ACL. RPC tidak diperiksa. Pertahankan regresi constraint dan guard anak existing; catat bukti dan hasil aktual.
- `amr_resource/tests/integration/test_lifecycle.py` dan `amr_resource/tests/browser/test_browser.py` adalah referensi existing, bukan bukti kelulusan; keduanya diimpor `amr_resource/tests/__init__.py:1-2`. Ekspektasi produksi langsung dari arsip pada `test_lifecycle.py:33-37,64-73` bertentangan dengan keputusan owner; revisi setelah persetujuan, jangan dianggap acceptance baru. Unit `test_trust_state.py:143-156,226-236` juga mengharapkan aktivasi melalui transisi dari record inactive; bedakan target disable yang tidak mengaktifkan. Otomatisasi dan eksekusi setelah persetujuan.

## Kriteria penerimaan dan gate
- AC-1: keenam pasangan state berbeda pada record aktif berhasil; target invalid dan state sama ditolak tanpa perubahan. Tombol sesuai state terverifikasi di browser.
- AC-2: unlink draft/production ditolak; disable menjadi inactive dan tetap exists. Arsip tidak langsung ke production; unarchive menghasilkan active draft, kemudian transisi production berhasil.
- AC-3: untuk masing-masing empat One2many, tambah/edit/hapus dapat dilakukan di draft dengan data valid dan constraint existing; semua readonly di production dan disable pada UI. Field parent sebelumnya editable tetap editable di draft; parent readonly di kedua state lain. Guard ORM issuer dan guard anak existing tetap berlaku; RPC tidak diuji.
- AC-4: akses trust admin dan user biasa sesuai ACL existing; tidak ada perubahan ACL. Coverage unit line minimal 50% untuk seluruh addon, denominator dan pengecualian menunggu konfirmasi owner.
- Buat dan jalankan otomatisasi integrasi Python untuk AC yang relevan di Odoo 13, serta bukti browser untuk perilaku UI; catat setiap AC, hasil, perintah dan bukti aktual. Tes mocked bukan bukti ORM atau browser.
- Owner menyetujui draft sebelum development. UAT `ACCEPT` hanya jika semua integrasi wajib lulus; `ACCEPTED_WITH_WAIVER` hanya dengan keputusan eksplisit owner, mencatat setiap item FAIL/NOT RUN, alasan, cakupan dan task tindak lanjut terpisah. Waiver tidak mengubah hasil menjadi PASS. Laporan test/review/waiver dibuat pada tahap yang sesuai.
