# Modul `amr_resource` — Panduan User

> Task: ADDONS13-24 — dokumentasi kandidat addon `amr_resource` (Odoo 13).
>
> Source module: commit `7a6f09bef97f38d53566b1351c3178c536fdb4e4`; target baseline worktree `377537b4d428a5105eee4d72547ec077b0f03569`.
>
> Status: DRAFT. Review independen atas isi dokumentasi serta layout folder `docs/` dan link relatif kandidat ini: **PASS terbatas**; final acceptance Lead tetap terpisah. Ini bukan test/security acceptance.
>
> Bukti runtime: test belum PASS terverifikasi; risiko keamanan tetap PENDING/BLOCKED.

## Untuk User

### Menu & Form

Addon mewarisi form `res.config.settings` dan mendeklarasikan blok dengan string `Server Resource`, dibatasi pada view untuk `base.group_erp_manager`. Field audience, freeze, preview, tombol Edit dan beberapa checkbox ditata di XML. **Jalur menu/halaman aktual dan label yang terlihat setelah render Odoo belum diuji**; `string` dan `data-string` pada blok berbeda. Perlakukan “Server Resource” sebagai label source, bukan kepastian teks navigasi di instance Anda. Issuer setting tidak tampil pada view addon yang diperiksa. (`views/res_config_settings_views.xml:2-47,31-175`.)

Wizard membuat form transient berisi nama, login, email opsional dan template user; XML yang ada tidak menunjukkan menu/action entry. Tidak dapat diasumsikan wizard bisa dibuka melalui menu tertentu. (`wizard/create_user_wizard.xml:3-25`; `wizard/create_user_wizard.py:7-37`.)

### Role dan Hak Akses

- XML membatasi visibilitas blok settings ke group ERP Manager; ini bukan bukti bahwa operasi ORM/RPC atau form `ir.config_parameter` memiliki pembatasan yang sama.
- Addon mendeklarasikan group machine dan technical. Keanggotaan group memengaruhi predicate source; group machine berkaitan dengan jalur yang dapat membuat environment `su=True`, sehingga aksesnya berisiko tinggi dan harus dibatasi sesuai kebijakan yang ditinjau.
- Tidak ada matriks hak efektif untuk ERP Manager, internal non-manager, portal, dan public yang telah diuji. Jangan menyimpulkan izin efektif dari label/group di view saja.

Rujukan: `views/res_config_settings_views.xml:2-30`; `security/res_groups.xml:3-26`; `models/res_users.py:14-46`; Developer Report, bagian NOT RUN.

### Alur Kerja Harian

**Konfigurasi awal (panduan source; belum diuji runtime):**

1. Gunakan hanya sandbox Odoo 13 disposable yang versinya/dependensinya telah disetujui; jangan menguji pada produksi.
2. Pastikan operator yang menjalankan setup berwenang. XML view menyatakan group ERP Manager untuk blok settings, tetapi akses efektif harus diverifikasi oleh administrator Odoo.
3. Pada settings, pilih selector `amr_select_audience` (`web.base.url` atau `database.uuid`). `amr_resource_audience` adalah preview computed dari nilai parameter yang dipilih, bukan tempat mengisi audience literal.
4. Jangan anggap opsi Freeze sudah melindungi perubahan `web.base.url`: addon menyimpan flag, sedangkan perilaku core yang menegakkannya belum dibuktikan pada snapshot.
5. Sebelum menghubungkan resource server, selesaikan review keamanan issuer/discovery/JWKS/outbound host, audience, role machine, logging, timeout, dan scope. README ini tidak memberikan langkah konfigurasi produksi karena gate tersebut masih terbuka.

**Penggunaan request:** route dan helper menyediakan jalur Bearer/parameter sesuai auth yang tertulis pada source. Pemetaan user, token, audience dan hasil respons belum diverifikasi pada server runtime; jangan menganggap setiap exception akan menjadi 401 atau setiap request akan memperoleh session login.

### Konfigurasi Awal

Nama parameter yang disebut source: `amr_resource.issuer`, `amr_resource.audience`, dan `web.base.url.freeze`. Jangan memasukkan nilai credential/token/signing key ke channel bersama atau URL. Nilai parameter aktual, hak pengubah dan efek Freeze belum diverifikasi. Pemasangan/upgrade hanya boleh diuji di lingkungan disposable dengan dependency matrix Odoo 13 yang benar-benar tersedia; README tidak menetapkan versi package yang belum dipin.

### FAQ

**Apakah addon ini menerbitkan access token?**

Tidak berdasarkan source yang diperiksa. Method `get_access_token` dan `create_access_token` adalah stub; URL hooks default tidak menambahkan token. Untuk penerbitan token dibutuhkan implementasi lain yang scope/otorisasinya terpisah. (`models/res_users.py:48-77`.)

**Apakah audience pilihan merupakan allowlist issuer?**

Tidak. Audience dan issuer adalah konsep/parameter terpisah; source tidak membuktikan allowlist issuer atau host outbound. Risiko tersebut masih PENDING/BLOCKED. (`models/helper.py:19-37,114-149`.)

**Mengapa login/API dapat gagal?**

Kemungkinan umum dari source meliputi parameter issuer/audience kosong, discovery atau endpoint tidak tersedia, respons HTTP/JSON gagal, header Bearer tidak cocok pola parser, user tidak termapping, atau library dependency tidak kompatibel. Catat kelas error, versi dan jalur; jangan kirim token/payload/raw log. Untuk perilaku aktual, perlu uji runtime terotorisasi.

**Apakah test sudah lulus?**

Belum ada hasil PASS terverifikasi. Test unit belum dieksekusi dalam Odoo; satu percobaan QA gagal sebelum memberikan summary runner. Review statis test/security berstatus inconclusive. Jangan memakai dokumen ini sebagai bukti instalasi, security approval, atau deployment.

**Bisakah saya mengaktifkan checkbox addon terkait?**

Jangan mengaktifkannya berdasarkan keberadaan checkbox saja. Addon pasangan/sibling dan dependency-nya belum diverifikasi pada target; konsultasikan administrator/Lead sebelum perubahan.

## Catatan Versi

- Odoo sumber: 13.
- Versi manifest: `13.0.0.0.8`; license manifest: LGPL-3.
- Source module commit: `7a6f09bef97f38d53566b1351c3178c536fdb4e4` (sesuai provenance Developer Report); target baseline: `377537b4d428a5105eee4d72547ec077b0f03569`.
- Kandidat lokal: branch `ADDONS13-24`, belum di-commit; SHA final kandidat belum tersedia.
- Status migrasi Odoo 20: belum diverifikasi / belum dimigrasikan pada bukti yang tersedia.
- Status runtime/deployment: **BELUM TERVERIFIKASI**.
- Changelog: 2026-10-18 — panduan Developer + User dan link/layout `docs/` mendapat review independen **PASS terbatas** untuk akurasi dokumentasi. Ini bukan commit, PR, security clearance, QA PASS, atau release.
