# `amr_token` — Panduan User

> Provenance upstream: source addon Odoo 13 [`addons_oidc` commit `6725f802acde636be0b25e2c140d15dccd37b0db`](https://github.com/agusramdan/addons_oidc/tree/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token). Uraian dan rujukan kandidat lokal dicocokkan secara statis dengan pin. Menu, hak akses efektif, konfigurasi server, dan perilaku runtime belum diverifikasi; dokumen ini bukan persetujuan memakai kunci nyata atau memasang addon di produksi.

## Ringkasnya

`amr_token` menyimpan public-key record untuk JWKS dan mendeklarasikan `GET /.well-known/jwks.json`. Pada candidate ADDONS13-39, addon dasar tidak mendeklarasikan OIDC Discovery; dispatcher token menolak grant dengan `400 unsupported_grant_type`. Jika `amr_oidc` dipasang, path OIDC Discovery dideklarasikan oleh addon itu dan mengembalikan 404. Ini kontrak source/unit fixture, bukan bukti route efektif di Odoo. Lihat [batas protokol ADDONS13-39](../../amr_oidc/docs/addons13-39-protocol.md), [serialisasi key](../models/public_key.py#L114-L128), dan [route JWKS](../controllers/main.py#L51-L54).

## Batas sebelum penggunaan operasional

Panduan ini bersifat source-only; belum ada bukti addon terpasang, UI/menu terlihat, ACL efektif, atau endpoint berjalan pada Odoo. Jangan gunakan private key/secret nyata, jangan aktifkan demo key, dan jangan mengubah grup/ACL untuk mengatasi menu yang tidak terlihat. Penggunaan operasional memerlukan environment Odoo 13 non-produksi yang disetujui serta verifikasi role, form/settings, dan respons endpoint secara terpisah.

## Menu, halaman, dan akses

Source XML mendeklarasikan menu `JWKS Keys` di bawah menu Users, tetapi menetapkan grup `base.group_no_one`. Karena itu operator biasa—termasuk ERP Manager—tidak boleh mengasumsikan menu tersebut terlihat. Settings view XML mendeklarasikan blok `JWT Token` untuk `base.group_erp_manager` dan memakai kondisi `attrs` pada `module_amr_token`; model `res.config.settings` kandidat tidak mendeklarasikan field bernama itu (ia memiliki field terpisah `module_amr_token_oauth`). Jangan mengasumsikan kondisi/visibilitas efektif sebelum diverifikasi pada Odoo candidate. Rujukan kandidat: [menu](../views/menuitem.xml#L3-L11), [settings view](../views/res_config_settings_views.xml#L7-L40), [settings model](../models/res_config_settings.py#L61-L76), [ACL](../security/ir.model.access.csv#L1-L2). ([menu upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/views/menuitem.xml#L3-L11), [settings view upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/views/res_config_settings_views.xml#L2-L43), [settings model upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/models/res_config_settings.py#L61-L76), [ACL upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/security/ir.model.access.csv#L1-L2))

Form kandidat memiliki bagian Identity, Status, Public Key, Private Key (Dev Only), dan Lifecycle. ACL source memberi grup ERP Manager hak read/write/create/unlink pada model; field `private_key` tetap field teks dan tidak ditunjukkan terenkripsi oleh addon. Ini bukan hasil pemeriksaan akses pada server. Rujukan kandidat: [form](../views/public_key_views.xml#L9-L78), [ACL](../security/ir.model.access.csv#L1-L2). ([public-key view upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/views/public_key_views.xml#L4-L104), [ACL upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/security/ir.model.access.csv#L1-L2))

## Arti field utama

| Field         | Arti pada source                                                                                                                                      | Catatan aman                                                                                                                                         |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | Nama tampilan record                                                                                                                                  | Tidak dinyatakan required pada model.                                                                                                                |
| `kid`         | Identifier key yang disertakan pada JWK                                                                                                               | Required dan indexed; tidak ada unique constraint yang terlihat.                                                                                     |
| `source`      | Label sumber key: `database`, `hsm`, `file_path`, `env_pem`, `env_path`, `config_path`, `config_pem`, `system_parameter_pem`, `system_parameter_path` | Label `hsm` tersedia, tetapi implementasi retrieval melempar `ValueError` untuk HSM. Mode retrieval non-database tidak membuktikan dukungan signing. |
| `hsm_key_id`  | Field identifier HSM                                                                                                                                  | Tidak membuktikan ada koneksi atau implementasi HSM.                                                                                                 |
| `algorithm`   | Algoritma yang dicatat pada record; default `RS256`                                                                                                   | Pastikan jenis key cocok; source tidak menunjukkan validasi pasangan jenis key/algoritma pada model.                                                 |
| `public_key`  | PEM public key; validasi mencoba mem-parsing PEM                                                                                                      | Jangan masukkan private key pada field ini.                                                                                                          |
| `private_key` | Field teks opsional yang digunakan jalur database                                                                                                     | Jangan simpan private key nyata; source tidak menunjukkan enkripsi field/at-rest.                                                                    |
| `active`      | Status aktif; default `True`                                                                                                                          | Menurut source, record aktif ikut pada respons JWKS.                                                                                                 |
| `is_signing`  | Flag signing; default `False`                                                                                                                         | Pada JWKS, flag ini menambah `use: "sig"`; bukan filter keikutsertaan.                                                                               |
| `expires_at`  | Tanggal kedaluwarsa opsional                                                                                                                          | Source `get_jwks()` tidak memfilter tanggal ini. Jangan menganggap tanggal tersebut mencabut key.                                                    |

Rincian tipe/default dan perilaku: [Panduan Developer](developer.md#2-model-dan-field-amrpublickey), [field kandidat](../models/public_key.py#L23-L74), [retrieval kandidat](../models/public_key.py#L81-L112), serta [`public_key.py` pada upstream pin](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/models/public_key.py#L19-L129).

## Pengaturan dan pembuatan key

Settings kandidat mendeklarasikan `Signature Type` (`secret`/`public_key`), algoritma secret/public-key, dan masa berlaku token. Tombol `Create Key` pada settings dideklarasikan saat tipe `public_key` dipilih; ia membuat record baru. Method model `action_generate_key()` menulis key ke record yang ada, tetapi form public-key kandidat tidak memiliki tombol aktif untuk method itu—header action contoh dikomentari. Kedua jalur menyimpan private key tanpa enkripsi pada field teks. **Jangan gunakan salah satu jalur untuk key nyata atau di produksi**; menu/form dan akses efektif belum diverifikasi. ([settings kandidat](../models/res_config_settings.py#L6-L76), [settings button kandidat](../views/res_config_settings_views.xml#L33-L36), [create action kandidat](../models/res_config_settings.py#L75-L76), [helper key generation upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/models/helper.py#L99-L151), [model action kandidat](../models/public_key.py#L141-L144), [form header kandidat](../views/public_key_views.xml#L11-L29))

## JWKS dan siklus hidup

Route kandidat `GET /.well-known/jwks.json` dideklarasikan publik dan menghasilkan objek berisi `keys`. Record `active=True` masuk ke serialisasi kandidat; `is_signing=False` tidak mencegah key muncul, dan `expires_at` tidak difilter. Mengubah `active` menjadi false tampak mengecualikan record dari pencarian JWKS di source, tetapi proses pencabutan/rotasi belum diverifikasi. Candidate cross-check: [controller](../controllers/main.py#L51-L54), [helper JWKS](../models/helper.py#L179-L181), [serialisasi model](../models/public_key.py#L114-L128). ([controller upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/controllers/main.py#L57-L60), [helper upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/models/helper.py#L263-L267), [serialisasi upstream](https://github.com/agusramdan/addons_oidc/blob/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token/models/public_key.py#L115-L129))

Record demo kandidat [`../demo/public_key_demo.xml`](../demo/public_key_demo.xml) menggunakan public PEM sintetis, `active=False`, `is_signing=False`, dan tidak memasok `private_key`; manifest mendaftarkannya sebagai data demo, sehingga pemuatan bergantung pada instalasi dengan demo data aktif. Jangan mengaktifkan record tersebut atau memakainya sebagai key nyata/produksi.

### Token helper di luar pengelolaan JWKS

Source kandidat juga memperluas helper access-token pada `res.users`; salah satu jalurnya menambahkan bearer token ke query string URL. Ini bukan langkah pengelolaan JWKS dan bukan pola yang direkomendasikan untuk dibagikan. Lihat [panduan developer](developer.md#identitas-model-inheritance-dan-integrasi-kandidat); jangan membagikan URL yang mengandung token.

## FAQ

**Apakah HSM didukung?**

Tidak berdasarkan source snapshot. Pilihan `hsm` dan field `hsm_key_id` ada, tetapi `get_private_key()` tidak memiliki implementasi HSM dan mengembalikan error unsupported.

**Apakah `expires_at` otomatis menghentikan key muncul di JWKS?**

Tidak berdasarkan `get_jwks()` yang diperiksa. Ia mencari record aktif tanpa filter expiry.

**Apakah environment variable/file/config path pasti dipakai untuk signing?**

Tidak. `get_private_key()` menyediakan jalur retrieval, tetapi `PublicKey.generate_token()` membaca `self.private_key` langsung. Jangan menganggap mode non-database sebagai signing yang telah didukung.

**Apakah `is_signing=True` memilih satu key tertentu untuk ditandatangani?**

Tidak terbukti. Helper signing mencari berdasarkan `algorithm` saja, tanpa filter `kid`, `active`, atau `is_signing`; beberapa record dengan algoritma yang sama dapat membuat pemilihan ambigu. Jangan mengandalkan hasil yang deterministik.

**Apakah `views/token_views.xml` menjadi bagian UI yang terpasang?**

Tidak. Manifest kandidat mendaftarkan public-key views, menu, dan settings view, tetapi tidak mencantumkan `views/token_views.xml` pada `data`. Pencarian statis kandidat `amr_token` dan dependency `amr_resource` juga tidak menemukan deklarasi `_name = "amr.token"`; jangan menganggap model atau daftar token tersedia/terpasang. ([manifest kandidat](../__manifest__.py#L15-L23), [`token_views.xml` kandidat](../views/token_views.xml#L1-L40))

**Apakah addon sudah terbukti berjalan di Odoo atau siap produksi?**

Panduan ini tidak membuktikan instalasi, dependency runtime, UI, endpoint, ACL efektif, atau keamanan. Gunakan hanya dalam lingkungan non-produksi yang telah disetujui dan setelah gate test/review terpisah.

## Catatan versi

Source yang dirujuk adalah addon Odoo 13, versi manifest `13.0.0.0.8`. Kompatibilitas Odoo 20 dan penggunaan produksi tidak diklaim.
