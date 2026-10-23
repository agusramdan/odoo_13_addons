# Panduan Pengguna — `amr_oidc`

[README addon](../README.md) · [Panduan Pengembang](developer.md)

## Tujuan, sasaran pembaca, dan prasyarat

Panduan berbasis kode sumber ini ditujukan kepada administrator Odoo, pengembang integrasi, dan pihak yang meninjau menu/akses. Ia menjelaskan deklarasi addon `amr_oidc` untuk Odoo 13, bukan prosedur instalasi, konfigurasi produksi, atau bukti bahwa layar maupun protokol bekerja. Sebelum tindakan operasional, diperlukan lingkungan dan prosedur yang disetujui, peran yang ditetapkan administrator, serta verifikasi akses/runtime tersendiri. Jangan gunakan secret, token, authorization code, private key, data pengguna, atau log mentah sebagai bahan uji/dukungan.

Identitas kode sumber yang dibahas di panduan historis ini: snapshot `agusramdan/odoo_13_addons@6bd356e7386420e23b23d6f2874cb9c20944d003` (ADDONS13-37); asal upstream `agusramdan/addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db`. Candidate ADDONS13-39 berbasis T1 `a2684e704304e947464b3eec7d8d2ef734ec0aef`; batas metadata/grant current ada pada [catatan ADDONS13-39](addons13-39-protocol.md). Manifest menyatakan versi `13.0.1.0.0`, lisensi `LGPL-3`, Odoo 13. Migrasi atau kompatibilitas Odoo 20 tidak diklaim.

## Menu dan tindakan yang dideklarasikan

XML mendeklarasikan action `action_oidc_client` dengan label `OIDC Clients` dan `action_oidc_authorization_code` dengan label `OIDC Auth Code` (`amr_oidc/views/oidc_client_views.xml:64-75`; `amr_oidc/views/oidc_authorization_code_views.xml:20-24`). Menu kedua action memakai parent `amr_token.menu_token_parent` dan group `base.group_no_one` (`amr_oidc/views/menuitem.xml:8-13`). Elemen menu tersebut tidak menetapkan atribut `name`; label action bukan bukti label atau jalur menu yang tampil. Root menu lokal OIDC berupa komentar (`amr_oidc/views/menuitem.xml:4-7`). Ini deklarasi statis, bukan bukti menu tampil, jalur navigasi, akses, atau hasil tindakan. Visibilitas/runtime UI: **[PERLU KONFIRMASI]**.

| Area deklaratif | Yang ditunjukkan kode sumber | Batas |
|---|---|---|
| Client | Action `action_oidc_client` (`OIDC Clients`), form/list dan tombol terkait wizard. | Menu tidak menetapkan `name`; tidak menginstruksikan pengelolaan client; role dan akses efektif belum terverifikasi. |
| Authorization code | Action `action_oidc_authorization_code` (`OIDC Auth Code`) dan tree view. | Menu tidak menetapkan `name`; jangan buka atau akses record. Otorisasi/keamanan akses tidak ditetapkan di sini. |
| Login/continue | Rute/pengendali dan template dideklarasikan. | Sesi, login, callback dan UI efektif [PERLU KONFIRMASI]. |
| Wizard service account | Form menyebut Generate/Save/Close; ekspor dalam kode sumber menghasilkan materi kunci privat. | Bukan langkah aman operasional; jangan jalankan atau ekspor key berdasarkan panduan ini (`amr_oidc/models/oidc_client.py:158-181`). |

Refresh view juga tidak tercantum pada manifest data, dan menu root lokal yang diperiksa berupa komentar (`amr_oidc/__manifest__.py:16-23`; `amr_oidc/views/menuitem.xml:8-13`). Ini tetap bukan bukti keadaan runtime.

## Akses dan kebijakan

ACL CSV secara statis menyebut `base.group_erp_manager` serta `base.group_user` untuk client, key, authorization code; refresh-token baris memiliki `group_id` kosong. Detail operasi dan izin literal ada di [panduan developer](developer.md#keamanan-dan-batas), sumber `amr_oidc/security/ir.model.access.csv:1-10`. Baris ACL tidak membuktikan izin efektif, record rules, akses field, atau keamanan; tidak adanya baris untuk replay/wizard juga bukan bukti izin/penolakan.

**Persyaratan kebijakan (bukan bukti penegakan dalam kode sumber):** administrator OIDC yang berwenang untuk pengelolaan `oidc.client` melalui UI/wizard; akses ORM/RPC langsung untuk operasi non-secret tunduk pada kebijakan ACL/record-rule sama, tanpa bypass; record key dimaksudkan terscope per user/client; tidak ada jaminan isolasi perusahaan; `sudo()` hanya untuk operasi sistem sempit dan beralasan. Source tidak membuktikan policy ditegakkan atau group OIDC-admin khusus. Panduan ini tidak mengotorisasi/menilai pembacaan atau ekspor secret/private key maupun akses record authorization-code. Jangan menganggap menu tersembunyi atau widget password sebagai pengamanan.

## Batas protokol dan konfigurasi

Candidate ADDONS13-39 fail-closed pada source handler: authorization-code redemption/token exchange dan ID-token issuance tetap tidak tersedia; handler `/oidc/authorize`, `/oidc/auth`, `/oidc/authorize_continue`, dan `/oidc/login/submit` mengembalikan `400 unsupported_response_type` saat dipanggil; token dispatcher menolak semua grant dengan `400 unsupported_grant_type`. Kombinasi `amr_token` + `amr_oidc` mendeklarasikan OIDC Discovery handler yang mengembalikan 404; tidak ada RFC 8414 route karena tidak ada response type OAuth lengkap yang dibuktikan. Middleware/auth dapat mengubah HTTP outcome; ini kontrak source/unit fixture, bukan verifikasi Odoo runtime atau route efektif. Lihat [batas protokol ADDONS13-39](addons13-39-protocol.md).

Parameter source yang tampak `amr_token.expires_in`, `amr_token.secret`, dan `web.base.url` bukan panduan nilai produksi. Jangan membaca atau mengubah parameter produksi berdasar dokumen ini; nilai rahasia tidak dicantumkan (`amr_oidc/models/oidc_refresh_token.py:20-37,56-97`).

## Batas alur, konfigurasi, dan pemulihan

Tidak ada alur kerja penggunaan maupun prosedur konfigurasi yang terverifikasi untuk dijalankan berdasarkan panduan ini. Dokumen ini tidak memberikan langkah membuat client, mengubah ACL, login, men-generate/mengekspor key, mengakses authorization-code, atau menguji endpoint. Sebelum operasi, minta panduan operasional dan persetujuan terpisah dari administrator atau pemilik berwenang serta verifikasi role/runtime pada lingkungan yang disetujui. Jangan gunakan nilai produksi atau bypass ACL/record rules.

Tidak tersedia prosedur pemulihan versi atau pemusnahan yang disetujui. Revert kode saja tidak menghapus record database, token, atau key yang telah diekspor. Pemulihan/pembersihan memerlukan runbook terpisah yang disetujui dan disesuaikan dengan lingkungan; panduan ini tidak menetapkan langkah destruktif.

## Tanya jawab dan eskalasi

**Apa yang dapat dipastikan panduan ini?** Hanya deklarasi source statis yang dirujuk; bukan kondisi instance, visibilitas UI, izin efektif, atau keberhasilan request.

**Apakah code flow lengkap atau ID token tersedia?** Tidak. Redemption/token exchange dan ID-token issuance tetap tidak tersedia. Candidate menolak authorization response dan grant lewat dispatcher; jangan menganggap OIDC Authorization Code Flow lengkap.

**Apakah metadata membuktikan dukungan?** Tidak. Candidate tidak mengirim sukses OIDC Discovery atau RFC 8414 metadata. Route OIDC Discovery pada kombinasi B mengembalikan 404 dalam fixture; route efektif belum diverifikasi. Metode autentikasi client dan dampak consumer/cache masih `UNASSESSED / UNVERIFIED`.

**Bagaimana meminta bantuan?** Hubungi administrator/Lead melalui kanal yang disetujui. Sertakan versi/snapshot, nama menu/metode umum, waktu kejadian, dan kondisi yang sudah disanitasi. Jangan kirim token, secret, authorization code, cookie, private/public key, payload sensitif, URL callback berisi data, screenshot berisi credential, atau raw log. Jika bukti sensitif terlanjur dibagikan, hentikan distribusi dan ikuti prosedur incident/credential rotation organisasi; panduan ini tidak menetapkan prosedur tersebut.

**UI atau role tidak tampak seperti deskripsi?** [PERLU KONFIRMASI] Runtime, konfigurasi, group efektif, dan integrasi menu perlu diperiksa oleh administrator yang berwenang. Jangan mencoba memperbaikinya dengan sudo atau mengubah ACL sendiri.

**Apakah mengembalikan kode menghapus data/token/key?** Tidak. Revert kode bukan pemusnahan; tidak ada prosedur pemulihan versi/pemusnahan terverifikasi di sini. Minta runbook terpisah yang disetujui, tanpa melakukan penghapusan sendiri.

## Rujukan lanjutan

- Detail arsitektur, model, metode, parameter/galat, ACL dan integritas kode sumber: [Panduan Pengembang](developer.md).
- Status runtime/deployment tidak dibuktikan dokumen source ini; tidak ada klaim migrasi Odoo 20.
