# Panduan Pengembang — `amr_oidc`

[README addon](../README.md) · [Panduan Pengguna](user.md)

## Cakupan dan identitas kode sumber

Penelaahan source mencakup addon `amr_oidc` dan parent `amr_token`. Asal addon: `agusramdan/addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db`. Manifest mendeklarasikan Odoo 13, versi `13.0.1.0.0`, lisensi `LGPL-3`. Panduan ini bersumber dari kode, bukan hasil instalasi, uji runtime Odoo, audit keamanan formal, atau deployment.

Rujukan memakai path relatif repositori dan `path:baris` aktual. SHA-256 pada tabel integritas adalah digest per berkas untuk keterlacakan, bukan identitas commit/branch/PR. Semua path kode aplikasi dan tes yang dikutip tercantum di tabel; `../../AGENTS.md` hanya dirujuk sebagai panduan target proyek, bukan berkas kode addon.

`AGENTS.md` menetapkan target proyek Python 3.7.9 (`../../AGENTS.md:14-16`); ini bukan bukti versi runtime atau toolchain yang terpasang. Test sources memakai stub inert (`amr_oidc/tests/support.py`) dan tidak menjalankan Odoo registry, ORM, HTTP, PostgreSQL, atau autentikasi nyata. Versi runtime dan hasil eksekusi pada lingkungan target perlu dibuktikan terpisah.

## Arsitektur

Paket utama mengimpor pengendali, model, dan wizard (`amr_oidc/__init__.py:3-5`; `amr_oidc/models/__init__.py:3-8`). Controller mewarisi `ControllerToken`; `TokenHelper` mewarisi model abstract `amr.token.helper` dari addon induk (`amr_oidc/controllers/main.py:10-18`; `amr_oidc/models/helper.py:18-20`; `amr_token/models/helper.py:1-20`). Pewarisan membuktikan deklarasi perluasan, bukan bahwa pemanggil tertentu benar-benar menggunakan metode.

Manifest menyebut `base`, `web`, `amr_token`, dependensi Python `pyjwt`, `cryptography`, serta daftar data XML/ACL (`amr_oidc/__manifest__.py:4-23`). Ketersediaan paket, registry, dan kompatibilitas lingkungan tidak dibuktikan.

## Konsumen terverifikasi

**BELUM TERVERIFIKASI.** Dalam graf kode sumber yang diperiksa tidak ditemukan bukti pemanggil addon lain yang dapat ditetapkan sebagai konsumen aktual untuk API `amr_oidc`. Relasi pewarisan controller dan helper induk serta delegasi yang terlihat bukan bukti adanya pemanggil eksternal. Tidak disajikan contoh pemanggilan yang seolah-olah telah berjalan.

## Model, field, dan relasi

Atribut “tidak dinyatakan” berarti argumen itu tidak tertulis pada deklarasi field lokal; tidak menyimpulkan default ORM. Ringkasan berikut merangkum field lokal; simbol dan rentang deklarasi mengidentifikasi kontrak lengkap. Lihat pula hash file pada [peta integritas kode sumber](#peta-kode-sumber-dan-integritas).

| Model | Field lokal (tipe; atribut eksplisit penting) | Relasi, constraint, deklarasi |
|---|---|---|
| `oidc.client` | `active` Boolean default `True`; `name` Char; `user_id` Many2one default `1`; `client_id`, `client_email`, `client_secret`, `web_base_url` Char; `client_type` Selection default `machine`; `authentication_method` Selection default `client_secret`; `redirect_uri` Text; `redirect_path` Selection `REDIRECT_MODE.items()` default `auth_oauth_oidc`; `authorization_ids`, `key_ids` One2many. | Pengguna → `res.users`; authorization → `oidc.authorization.code` via `client_id`; keys → `oidc.client.key` via `client_id`. Model baru, tanpa SQL constraint lokal. `amr_oidc/models/oidc_client.py:14-52`. |
| `oidc.authorization.code` | `code` Char required/index, UUID default; `client_id`, `user_id` Many2one required; `redirect_uri` Text required; `scope` Char; `expired_at` Datetime required; `used` Boolean default `False`. | Client → `oidc.client`, user → `res.users`; model baru. `amr_oidc/models/oidc_authorization_code.py:11-31`. |
| `oidc.client.key` | `client_id` Many2one; `kid`, `algorithm` Char (algorithm default `RS256`); `kty` Selection `RSA/EC/OKP`; `use` Selection `sig/enc` default `sig`; `public_key` Text; `active` Boolean default `True`; `expired_at`, `last_used_at` Datetime. | `client_id` → `oidc.client`; model baru. `amr_oidc/models/oidc_client_key.py:6-25`. |
| `oidc.jwt.replay` | `jti`, `iss` Char required/index; `expired_at` Datetime required. | Model baru; SQL unique `(jti, iss)` bernama `jti_issuer_unique`. `amr_oidc/models/oidc_jwt_replay.py:6-18`. |
| `oidc.refresh.token` | `token` Char required/index; `user_id` Many2one required, `ondelete='cascade'`; `expires_at` Datetime required; `revoked` Boolean default `False`. | Pengguna → `res.users`; unique `token` constraint. `amr_oidc/models/oidc_refresh_token.py:16-50`. |
| `oidc.service.account.wizard` | `client_id` Many2one required/readonly; `algorithm` Selection default `RS256`; `client_email` related readonly; `file_name`, `file_data`, `json_content` readonly. | Transient model; client → `oidc.client`. `amr_oidc/wizard/service_account.py:8-32`. |
| `amr.token.helper` | `TokenHelper` tidak menyatakan field lokal. | Abstract model diperluas dengan `_inherit`. `amr_oidc/models/helper.py:18-20`. |

Selection `oidc.client.client_type`: `machine`, `mobile`, `web`, `atm`, `cdm`; `authentication_method`: `client_secret`, `private_key_jwt`, `tls_client_auth`; redirect mode: `auth_oauth_oidc`, `auth_oauth_oea` (`amr_oidc/models/oidc_client.py:24-51`). Wizard algorithm options: `ES256`, `ES256K`, `ES384`, `ES512`, `RS256`, `RS384`, `RS512`, `PS256`, `PS384`, `PS512` (`amr_oidc/wizard/service_account.py:8-32`).

## Metode yang tampak pada kode sumber

“Tampak pada kode” berarti metode lokal yang dideklarasikan, bukan API stabil/eksternal atau izin pemanggil. Efek berikut hanya cabang kode; keberhasilan eksekusi dan akses efektif belum dibuktikan.

| Model/metode | Tanda tangan dan efek yang tampak pada kode sumber |
|---|---|
| `oidc.client._check_credentials` | `(self, client_secret)`: membandingkan nilai; `ValueError` bila mismatch, selain itu `True` (`amr_oidc/models/oidc_client.py:54-59`). |
| `oidc.client._validate_redirect_uri` | `(self, redirect_uri)`: pada mode fixed callback menerima hanya URI hasil `web_base_url + redirect_path` yang sama persis (atau parameter dihilangkan); pada mode allowlist menerima URI nonkosong yang sama persis dengan satu baris allowlist dan memiliki scheme/netloc (`amr_oidc/models/oidc_client.py:61-85`). |
| `oidc.client._client_auth` | `(self, token)`: decode Basic credentials, lookup dengan `sudo`; mismatch/exception ditangani dengan `None` (`amr_oidc/models/oidc_client.py:87-99`). Helper internal; jalur autentikasi/runtime belum diuji. |
| `oidc.client._create_authorization_code` | `(self, redirect_uri=None, scope='')`: membuat code record dengan expiry lima menit memakai environment `self.env`; source memasukkan string `self.client_id` ke field Many2one `client_id` (`amr_oidc/models/oidc_client.py:101-113`; `amr_oidc/models/oidc_authorization_code.py:13-18`). Ini mismatch source yang memerlukan verifikasi ORM; bukan bukti sukses/gagal runtime. |
| `oidc.client._create_access_token` | `(self, redirect_uri=None, scope='', **kw)`: mendelegasikan pembuatan token ke `env.user.create_access_token` (`amr_oidc/models/oidc_client.py:115-123`). |
| `oidc.client._validate_token` | `(self, token)`: pada cabang falsy `self`, decode payload tanpa verifikasi signature untuk mencari audience, lalu delegasi validasi ke helper parent (`amr_oidc/models/oidc_client.py:125-140`). |
| `oidc.client._validate_refresh_token` | `(self, token)`: delegasi ke model refresh token (`amr_oidc/models/oidc_client.py:142-143`). |
| `oidc.client.export_service_account` | `(self, algorithm)`: membentuk hasil yang mencakup private/public key material; tidak disalin atau diotorisasi oleh panduan (`amr_oidc/models/oidc_client.py:145-168`). |
| `oidc.client.action_export_service_account` | `(self)`: action window untuk wizard (`amr_oidc/models/oidc_client.py:170-181`). |
| `amr.token.helper.openid_configuration` | `(self)`: memperbarui hasil metadata parent; metadata bukan capability (`amr_oidc/models/helper.py:46-85`; `amr_token/models/helper.py:170-185`). |
| `amr.token.helper.oidc_token` | `(self, grant_type=None, **kwargs)`: dispatch lokal untuk cabang tertentu dan delegasi lainnya (`amr_oidc/models/helper.py:87-101`). |
| `amr.token.helper.do_client_credentials` | `(self, data)`: cabang mengambil credential Basic/body, lookup client, lalu delegasi token generation (`amr_oidc/models/helper.py:130-171`). |
| `amr.token.helper.do_client_assertion` | `(self, assertion, data)`: validasi assertion/key/claims, membuat replay record dan delegasi token generation (`amr_oidc/models/helper.py:173-278`). |
| `amr.token.helper.do_refresh_grant` | `(self, refresh_token=None)`: memanggil validator tanpa audience, lalu mencari user dari `payload['sub']` dan delegasi (`amr_oidc/models/helper.py:280-291`). |
| `oidc.refresh.token.get_secret` | `(self)`: mengambil parameter `amr_token.secret` melalui `sudo`; nilai tidak dibaca atau dicantumkan (`amr_oidc/models/oidc_refresh_token.py:21-29`). Caller reachability/RPC tidak dibuktikan; perlakukan helper ini sebagai area sensitif yang memerlukan review terpisah. |
| `oidc.refresh.token.get_expires_in`, `get_issuer`, `get_algorithm`, `create_refresh_token` | Helper membaca parameter/default atau membuat record refresh (`amr_oidc/models/oidc_refresh_token.py:21-68`). Akses efektif dan RPC perlu penilaian terpisah. |
| `oidc.refresh.token._validate_token` | `(self, token, audience, options=None)`: validasi JWT lalu mencari record yang belum kedaluwarsa dan tidak revoked (`amr_oidc/models/oidc_refresh_token.py:87-116`). |
| Wizard `action_generate`, `action_save` | Metode wizard menghasilkan/menyimpan data account/key sesuai cabang source; jangan gunakan panduan ini sebagai prosedur ekspor atau menyimpan key (`amr_oidc/wizard/service_account.py:58-105`). |

Daftar metode tidak membuktikan endpoint HTTP atau jangkauan RPC. Metode public/non-private yang tampak pada model dapat memerlukan penilaian RPC tersendiri; pada pekerjaan ini tidak dilakukan runtime/RPC call test.

## Rute dan deklarasi antarmuka

Dekorator rute menyatakan atribut statis berikut saja; atribut yang tidak ditulis tidak disimpulkan. Ini bukan jaminan rute terdaftar atau respons runtime (`amr_oidc/controllers/main.py`).

| Path | type | auth | methods | website | csrf | Deklarasi |
|---|---|---|---|---|---|---|
| `/oidc/authorize`, `/oidc/auth` | `http` | `public` | tidak eksplisit | tidak eksplisit | `False` | `:37` |
| `/oidc/continue` | `http` | `public` | `GET` | `True` | tidak ditulis | `:60` |
| `/oidc/login_form` | `http` | `public` | `GET` | `True` | tidak ditulis | `:64` |
| `/oidc/authorize_continue` | `http` | `user` | `POST` | tidak eksplisit | `True` | `:68` |
| `/oidc/login/submit` | `http` | `public` | `POST` | tidak eksplisit | `True` | `:73` |
| `/oidc/profile`, `/oidc/userinfo` | `http` | `none` | `GET` | tidak eksplisit | `False` | `:150` |

Menu client/code mencantumkan parent XML ID `amr_token.menu_token_parent` dan group `base.group_no_one`; root menu OIDC lokal dikomentari (`amr_oidc/views/menuitem.xml:4-13`). View client/code dan wizard dideklarasikan pada XML yang tercantum manifest (`amr_oidc/views/oidc_client_views.xml:3-76`; `amr_oidc/views/oidc_authorization_code_views.xml:3-24`; `amr_oidc/wizard/service_account.xml:3-26`; `amr_oidc/__manifest__.py:16-23`). Deklarasi menu/action bukan bukti visibilitas UI/runtime.

## Dependensi

Manifest mendeklarasikan dependensi addon `base`, `web`, `amr_token` dan dependensi Python eksternal `pyjwt`, `cryptography` (`amr_oidc/__manifest__.py:12-23`). Kode sumber mengimpor `jwt` (`amr_oidc/models/helper.py:3-10`). Ketersediaan pustaka, kesesuaian nama distribusi dengan nama import, dan versi terpasang tidak diverifikasi. Keberadaan folder dependensi bukan bukti bahwa ia terpasang.

## Konfigurasi

Parameter yang dibaca kode sumber saat membuat/memvalidasi refresh token:

| Nama parameter | Source default/penggunaan yang terlihat | Batas |
|---|---|---|
| `amr_token.expires_in` | Getter `get_expires_in` membaca parameter dengan default 86400 detik (`amr_oidc/models/oidc_refresh_token.py:20-24`). | Creator `create_refresh_token` menetapkan TTL hard-coded 14 hari (`:56-67`); tidak ada bukti setting getter mengendalikan TTL token terbit. Nilai aktual tidak diketahui. |
| `amr_token.secret` | Dipakai sebagai shared secret dalam pembuatan/verifikasi JWT refresh. | Nilai rahasia tidak dicantumkan; jangan membaca, mengubah, atau membagikannya berdasar dokumen ini. |
| `web.base.url` | Dipakai sebagai issuer/base URL dalam refresh-token source. | Nilai aktual dan deployment URL tidak diverifikasi. |

Rujukan parameter/default: `amr_oidc/models/oidc_refresh_token.py:20-37,56-97`. Source tidak menetapkan siapa yang berwenang mengubah parameter atau kebutuhan restart. Jangan mengubah parameter produksi sebagai pemecahan masalah.

Pada graph source, creator membentuk payload tanpa `sub`, sedangkan helper refresh membaca `payload['sub']`; validator mensyaratkan audience, tetapi pemanggil helper tidak memberikan audience (`amr_oidc/models/oidc_refresh_token.py:68-84,87-97`; `amr_oidc/models/helper.py:280-291`). Ini mismatch source, bukan bukti sukses/gagal runtime; refresh tidak diklaim berhasil.

## Galat dan batas pemecahan masalah

Hanya cabang kode sumber yang tampak, tanpa klaim retry, idempotensi, timeout, atau hasil HTTP/runtime.

| Kondisi source | Cabang tampak | Rujukan |
|---|---|---|
| Client secret mismatch | `ValueError` dari credential check. | `amr_oidc/models/oidc_client.py:54-59` |
| Assertion invalid/claims/key tidak cocok | error dict atau exception sesuai cabang pemeriksaan. | `amr_oidc/models/helper.py:173-258` |
| Replay collision | `IntegrityError` ditangani pada pencatatan replay; perilaku transaksi/runtime tidak dinyatakan. | `amr_oidc/models/helper.py:259-278` |
| Invalid token saat refresh | `InvalidTokenError` ditangani validator; tidak menyatakan pemulihan atau hasil endpoint. | `amr_oidc/models/oidc_refresh_token.py:86-116` |
| Refresh flow | Source-level mismatch: creator membentuk JWT tanpa `sub`, validator meminta audience, pemanggil lokal tidak memberinya dan kemudian mencari `payload['sub']`. | `amr_oidc/models/oidc_refresh_token.py:56-97`; `amr_oidc/models/helper.py:280-291` |

Jangan mendiagnosis dengan token/key nyata atau menyalin raw error/log. Eskalasi dengan nama metode/kondisi umum dan referensi sumber; runtime pemecahan masalah perlu prosedur serta otorisasi terpisah.

## Batas protokol

- **Tidak tersedia dalam addon/graf kode sumber/dependensi yang ditinjau:** authorization-code redemption/token exchange dan ID-token issuance. Addon ini tidak boleh disebut implementasi OIDC Authorization Code Flow lengkap (`amr_oidc/controllers/main.py:19-38,72-132`; dispatcher parent `amr_token/models/helper.py:191-204`).
- Dispatcher parent yang ditinjau memiliki cabang source untuk grant `password`, `challenge_approval`, `digital_signature`, dan cabang `unsupported_grant_type` bagi grant lain (`amr_token/models/helper.py:191-204`). Ini observasi atas dispatcher tersebut, bukan keputusan dukungan keseluruhan capability.
- Metadata `openid_configuration` memuat deklarasi response types termasuk `code`, `token`, `id_token`; metadata bukan implementasi (`amr_oidc/models/helper.py:46-85`; `amr_token/models/helper.py:170-185`).
- Capability grant/response lain, endpoint, client-authentication method, serta Discovery lain: **UNASSESSED / UNVERIFIED**. Tidak ada kesimpulan supported/unsupported. Refresh mismatch hanya ketidakselarasan source, bukan flow berhasil.

## Keamanan dan batas

### ACL statis

CSV mendeklarasikan izin berikut (urutan read/write/create/unlink):

| Model | Group field pada baris | R/W/C/U |
|---|---|---|
| `oidc.client` | `base.group_erp_manager` | Ya/Ya/Ya/Ya |
| `oidc.client.key` | `base.group_erp_manager` | Ya/Ya/Ya/Ya |
| `oidc.client.key` | `base.group_user` | Ya/Tidak/Tidak/Tidak |
| `oidc.authorization.code` | `base.group_erp_manager` | Ya/Ya/Ya/Ya |
| `oidc.refresh.token` | `base.group_system` | Ya/Ya/Ya/Tidak |

Sumber baris/header: `amr_oidc/security/ir.model.access.csv:1-9`; field `client_secret` mendeklarasikan group `base.group_erp_manager` (`amr_oidc/models/oidc_client.py:39`). Tidak ada baris untuk `oidc.jwt.replay` atau wizard. Ini deskripsi file saja: tidak membuktikan ACL efektif/izin, record rules, field access, atau keamanan RPC. Helper `get_secret` dan ekspor private key tetap batas terpisah; nilai sensitif tidak dicantumkan dan caller reachability perlu verifikasi terpisah.

### Persyaratan kebijakan — bukan bukti penegakan kode sumber

- Administrator OIDC yang berwenang untuk pengelolaan `oidc.client` melalui UI/wizard.
- Akses langsung ORM/RPC `oidc.client` untuk operasi non-secret wajib tunduk pada kebijakan ACL/record-rule yang sama seperti UI/wizard, tanpa bypass.
- Record key dimaksudkan tercakup per user/client pemilik; tidak ada jaminan isolasi perusahaan.
- `sudo()` hanya untuk operasi sistem sempit yang dibenarkan.

Policy ini adalah persyaratan, bukan perilaku yang dibuktikan source. Source menetapkan ACL statis dan pemanggilan `sudo()` pada controller/client/helper (`amr_oidc/controllers/main.py:50-51,97-98,121-122`; `amr_oidc/models/oidc_client.py:92-94,137-138`; `amr_oidc/models/helper.py:109-110,145-146,201-202,289-304`). Tidak ada bukti registry/runtime atau enforcement efektif. Metode non-private `get_secret` membaca parameter secret melalui `sudo` (`amr_oidc/models/oidc_refresh_token.py:26-29`); caller reachability belum diverifikasi. Dokumentasi ini tidak menetapkan risk acceptance atau menyimpulkan helper aman dipanggil.

### Redirect, expiry, dan perlindungan form — deklarasi source

- Controller memvalidasi client/redirect sebelum menerbitkan code/token (`amr_oidc/controllers/main.py:37-41,92-108,110-148`). Mode fixed callback dan allowlist exact dibahas pada tabel metode; hasil source-level ini belum diuji melalui HTTP/Odoo.
- Validator refresh mensyaratkan `expires_at > fields.Datetime.now()` serta `revoked=False` saat pencarian record (`amr_oidc/models/oidc_refresh_token.py:101-109`). Ini bukan bukti kondisi database/runtime.
- Form login/continue memuat hidden field `csrf_token` dari `request.csrf_token()` (`amr_oidc/views/login_template.xml:185-186,419-420`); route submit dan authorize-continue dideklarasikan `POST, csrf=True` (`amr_oidc/controllers/main.py:68-74`). Deklarasi dan tes AST tidak membuktikan CSRF efektif/runtime.
- Tes kontrak bersifat offline dan tidak membuktikan enforcement ACL/RPC atau flow OIDC; klaim keamanan efektif memerlukan review dan bukti runtime yang sesuai.

## Odoo 13 vs Odoo 20

Source/manifest yang diperiksa menargetkan Odoo 13 (`amr_oidc/__manifest__.py:4-12`). Tidak dilakukan perbandingan source Odoo 20; migrasi/kompatibilitas Odoo 20 tidak diklaim. Perubahan API, ORM, view, ACL atau JS pada versi 20 tidak dinilai.

## Bukti berkas pengujian

`amr_oidc/tests/test_package_contract.py` dan `amr_oidc/tests/test_security_contract.py` mendefinisikan kontrak offline dengan stub inert di `amr_oidc/tests/support.py`; tes memeriksa sebagian struktur/metadata source. Keberadaan atau hasil tes tersebut tidak membuktikan runtime, ORM, HTTP, registry atau akses efektif; bukti eksekusi tertentu dicatat terpisah.

## Peta kode sumber dan integritas

Hash SHA-256 di bawah adalah digest per berkas source yang menjadi dasar rujukan panduan. Digest dapat dipakai untuk membandingkan isi file, bukan mengidentifikasi branch, commit, PR, atau status gate.

| Repo-relative path | SHA-256 |
|---|---|
| `amr_oidc/__init__.py` | `51d0f9735a295f9969115778f66156098eb5de49ce6fd0abce6f4e57908b676b` |
| `amr_oidc/__manifest__.py` | `16fae221d45569fc5fea4e68748c00a3d732bdc2ef21fff2819782e029339ba0` |
| `amr_oidc/controllers/main.py` | `1d477b08deacd6e792d343234e28b2fbe0d0681d6a5cf32092bc6dd5933214a9` |
| `amr_oidc/models/__init__.py` | `942326411908a566afd11ec65a60f6698dc3a1b438b0020d1c43a4992792ecc2` |
| `amr_oidc/models/helper.py` | `e28b68d32cb3897ae834d84204e82a90fc880def8b55aa0ccd7d1b0d7cc4bb68` |
| `amr_oidc/models/oidc_authorization_code.py` | `23f64d0da605ba6abf9847bee42d81e87aa7d65a67d93dfd783c06fba34c6597` |
| `amr_oidc/models/oidc_client.py` | `3923d67f02c186a1c32fb03eee4fb1460180be969e2fa6cdbeb4d2ed10a2faad` |
| `amr_oidc/models/oidc_client_key.py` | `1f5238eea4f73bbe21a274ecac34d184954d05d2cb442f011efbfde41b2c3ef0` |
| `amr_oidc/models/oidc_jwt_replay.py` | `b7c49e3a71eb86c47881c318fbf7f4a9445b8b3f1aecc3af954d04a6b045c5b9` |
| `amr_oidc/models/oidc_refresh_token.py` | `9fef09d8a411a5129be1f6a41bdeca646e810919903ce5fc814a03363d608862` |
| `amr_oidc/security/ir.model.access.csv` | `853bfcc19561f490386ad2d7fc9edcef2a3ef1cefbd3254367aeec2ddd2e2458` |
| `amr_oidc/tests/test_package_contract.py` | `ee8d27c7ef60ba34e609800225fedb53b6668efb7ae19c0455645fd1d2f7d231` |
| `amr_oidc/tests/test_security_contract.py` | `de8bf3f7e47b8c6900c17512be3105eb7c80910675020183c722f449aa7cd87a` |
| `amr_oidc/tests/support.py` | `856353094578905073cab2148731478d33e9931abb2c235c4bb8e8d609da0917` |
| `amr_oidc/views/login_template.xml` | `3eda24c555b385b58c9bfc2b4b05e691da54adb358538b662d3ffe96777acba2` |
| `amr_oidc/views/menuitem.xml` | `c21871d804c848ed687ee3c4f8c5a2744a4eac44ab80e22a178c5a0a4d9eb6ba` |
| `amr_oidc/views/oidc_authorization_code_views.xml` | `178b386eb5d5d575dcee03463ae5f777722debed9157261d30f1ed642c8335a3` |
| `amr_oidc/views/oidc_client_views.xml` | `0ccc1b31fb79f70e56b757ef259990e24ff39783915822a402622e343ac51ec8` |
| `amr_oidc/wizard/service_account.py` | `cc3dbb56ca8f98dffea0ecda38e8bc6632da10a7741a6107cd867db087624550` |
| `amr_oidc/wizard/service_account.xml` | `a5a25cc05fd88ab531ad612ce6f495ef9fabe59e6690b607fc0d5dc1a5d1aab7` |
| `amr_token/models/helper.py` | `e286ae9022c66807c8fb6d6a1dc8af90a1a5c4e1243d42949e3de92a18d3a1dc` |

[PERLU KONFIRMASI] Registry/runtime, role dan akses efektif, route/UI visibility, dependency aktual, konfigurasi deployed, flow OIDC dan interoperabilitas memerlukan bukti terpisah. Persyaratan kebijakan di atas belum dibuktikan enforce oleh dokumentasi source ini.
