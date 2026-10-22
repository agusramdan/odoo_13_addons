# Panduan Pengguna — `amr_oidc`

[README addon](../README.md) · [Panduan Pengembang](developer.md)

## Tujuan, sasaran pembaca, dan prasyarat

Panduan berbasis kode sumber ini ditujukan kepada administrator Odoo, pengembang integrasi, dan pihak yang meninjau menu/akses. Ia menjelaskan deklarasi addon `amr_oidc` untuk Odoo 13, bukan prosedur instalasi, konfigurasi produksi, atau bukti bahwa layar maupun protokol bekerja. Sebelum tindakan operasional, diperlukan lingkungan dan prosedur yang disetujui, peran yang ditetapkan administrator, serta verifikasi akses/runtime tersendiri. Jangan gunakan secret, token, authorization code, private key, data pengguna, atau log mentah sebagai bahan uji/dukungan.

Manifest menyatakan versi `13.0.1.0.0`, lisensi `LGPL-3`, dan target Odoo 13 (`amr_oidc/__manifest__.py:4-12`). Asal upstream addon: `agusramdan/addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db`. Migrasi atau kompatibilitas Odoo 20 tidak diklaim. Rujukan kode sumber memakai path relatif repositori dan nomor baris aktual.

## Menu dan tindakan yang dideklarasikan

XML mendeklarasikan action `action_oidc_client` dengan label `OIDC Clients` dan `action_oidc_authorization_code` dengan label `OIDC Auth Code` (`amr_oidc/views/oidc_client_views.xml:64-75`; `amr_oidc/views/oidc_authorization_code_views.xml:20-24`). Menu kedua action memakai parent `amr_token.menu_token_parent` dan group `base.group_no_one` (`amr_oidc/views/menuitem.xml:8-13`). Elemen menu tersebut tidak menetapkan atribut `name`; label action bukan bukti label atau jalur menu yang tampil. Root menu lokal OIDC berupa komentar (`amr_oidc/views/menuitem.xml:4-7`). Ini deklarasi statis, bukan bukti menu tampil, jalur navigasi, akses, atau hasil tindakan. Visibilitas/runtime UI: **[PERLU KONFIRMASI]**.

| Area deklaratif | Yang ditunjukkan kode sumber | Batas |
|---|---|---|
| Client | Action `action_oidc_client` (`OIDC Clients`), form/list dan tombol terkait wizard. | Menu tidak menetapkan `name`; tidak menginstruksikan pengelolaan client; role dan akses efektif belum terverifikasi. |
| Authorization code | Action `action_oidc_authorization_code` (`OIDC Auth Code`) dan tree view. | Menu tidak menetapkan `name`; jangan buka atau akses record. Otorisasi/keamanan akses tidak ditetapkan di sini. |
| Login/continue | Rute authorize memvalidasi client/callback sebelum jalur penerbitan; form login/continue menyertakan CSRF token; dua rute submit dideklarasikan POST+CSRF (`amr_oidc/controllers/main.py:37-41,68-74,92-108`; `amr_oidc/views/login_template.xml:185-207,419-430`). | Ini hanya deklarasi/source contract. Sesi, login, callback, pemeriksaan CSRF dan UI efektif [PERLU KONFIRMASI]. |
| Wizard service account | Form menyebut Generate/Save/Close; ekspor dalam kode sumber menghasilkan materi kunci privat. | Bukan langkah aman operasional; jangan jalankan atau ekspor key berdasarkan panduan ini (`amr_oidc/models/oidc_client.py:145-168`). |

Refresh view juga tidak tercantum pada manifest data, dan menu root lokal yang diperiksa berupa komentar (`amr_oidc/__manifest__.py:16-23`; `amr_oidc/views/menuitem.xml:8-13`). Ini tetap bukan bukti keadaan runtime.

## Akses dan kebijakan

ACL CSV secara statis membatasi `oidc.client` dan authorization code ke `base.group_erp_manager`, serta refresh token ke `base.group_system` (read/write/create; unlink tidak diberikan). `oidc.client.key` tetap memiliki read untuk `base.group_user`; field `client_secret` menyebut `base.group_erp_manager` (`amr_oidc/security/ir.model.access.csv:1-9`; `amr_oidc/models/oidc_client.py:39`). Baris ACL dan tes kontrak lokal tidak membuktikan izin efektif, record rules, field enforcement, atau batas RPC. Tidak ada baris ACL untuk replay/wizard; ketiadaan baris bukan bukti izin atau penolakan.

**Batas bukti:** mapping di atas adalah source policy, bukan bukti enforcement bagi public, portal, internal user, atau RPC. Field group, method boundary, record rules, menu/UI, dan effective roles perlu verifikasi runtime oleh pihak berwenang. Area seperti secret/private-key handling, lifecycle, dan tenant isolation memerlukan review terpisah; panduan ini bukan risk acceptance. Jangan menganggap menu tersembunyi atau widget password sebagai pengamanan; jangan menjalankan helper, mengekspor key, atau menguji endpoint berdasarkan panduan ini.

## Batas protokol dan konfigurasi

Graf kode sumber/dependensi yang ditinjau tidak menyediakan authorization-code redemption/token exchange maupun ID-token issuance; addon bukan alur OIDC Authorization Code lengkap. Metadata response type/discovery bukan bukti kapabilitas. Source memvalidasi callback tetap/allowlist secara exact dan memeriksa expiry refresh dengan predicate `expires_at > now`, tetapi tes kontrak lokal tidak membuktikan alur Odoo/HTTP berjalan. Kapabilitas grant/response lain, endpoint, metode autentikasi client dan Discovery lain tetap `UNASSESSED / UNVERIFIED`. Refresh mismatch lain tetap ketidakselarasan source, bukan bukti flow berhasil. Rujukan rinci: [batas protokol](developer.md#batas-protokol).

Parameter source yang tampak `amr_token.expires_in`, `amr_token.secret`, dan `web.base.url` bukan panduan nilai produksi. Jangan membaca atau mengubah parameter produksi berdasar dokumen ini; nilai rahasia tidak dicantumkan (`amr_oidc/models/oidc_refresh_token.py:20-37,56-97`).

## Batas alur, konfigurasi, dan pemulihan

Tidak ada alur kerja penggunaan maupun prosedur konfigurasi yang terverifikasi untuk dijalankan berdasarkan panduan ini. Dokumen ini tidak memberikan langkah membuat client, mengubah ACL, login, men-generate/mengekspor key, mengakses authorization-code, atau menguji endpoint. Sebelum operasi, minta panduan operasional dan persetujuan terpisah dari administrator atau pemilik berwenang serta verifikasi role/runtime pada lingkungan yang disetujui. Jangan gunakan nilai produksi atau bypass ACL/record rules.

Tidak tersedia prosedur pemulihan versi atau pemusnahan yang disetujui. Revert kode saja tidak menghapus record database, token, atau key yang telah diekspor. Pemulihan/pembersihan memerlukan runbook terpisah yang disetujui dan disesuaikan dengan lingkungan; panduan ini tidak menetapkan langkah destruktif.

## Tanya jawab dan eskalasi

**Apa yang dapat dipastikan panduan ini?** Hanya deklarasi source statis yang dirujuk; bukan kondisi instance, visibilitas UI, izin efektif, atau keberhasilan request.

**Apakah code flow lengkap atau ID token tersedia?** Authorization-code redemption/token exchange dan ID-token issuance tidak disediakan oleh addon/graf kode sumber/dependensi yang ditinjau. Jangan menganggap OIDC Authorization Code Flow lengkap.

**Apakah metadata membuktikan dukungan?** Tidak. Metadata Discovery/response types tidak membuktikan kapabilitas. Capability lainnya `UNASSESSED / UNVERIFIED`.

**Bagaimana meminta bantuan?** Hubungi administrator/Lead melalui kanal yang disetujui. Sertakan versi/snapshot, nama menu/metode umum, waktu kejadian, dan kondisi yang sudah disanitasi. Jangan kirim token, secret, authorization code, cookie, private/public key, payload sensitif, URL callback berisi data, screenshot berisi credential, atau raw log. Jika bukti sensitif terlanjur dibagikan, hentikan distribusi dan ikuti prosedur incident/credential rotation organisasi; panduan ini tidak menetapkan prosedur tersebut.

**UI atau role tidak tampak seperti deskripsi?** [PERLU KONFIRMASI] Runtime, konfigurasi, group efektif, dan integrasi menu perlu diperiksa oleh administrator yang berwenang. Jangan mencoba memperbaikinya dengan sudo atau mengubah ACL sendiri.

**Apakah mengembalikan kode menghapus data/token/key?** Tidak. Revert kode bukan pemusnahan; tidak ada prosedur pemulihan versi/pemusnahan terverifikasi di sini. Minta runbook terpisah yang disetujui, tanpa melakukan penghapusan sendiri.

## Rujukan lanjutan

- Detail arsitektur, model, metode, parameter/galat, ACL dan integritas kode sumber: [Panduan Pengembang](developer.md).
- Status runtime/deployment tidak dibuktikan dokumen source ini; tidak ada klaim migrasi Odoo 20.
