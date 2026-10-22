# Panduan Pengembang — `amr_oidc`

[README addon](../README.md) · [Panduan Pengguna](user.md)

## Cakupan dan identitas kode sumber

Penelaahan historis kode sumber pada snapshot `agusramdan/odoo_13_addons@6bd356e7386420e23b23d6f2874cb9c20944d003`, termasuk parent `amr_token` pada snapshot tersebut. Asal addon: `agusramdan/addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db`. Manifest mendeklarasikan Odoo 13, versi `13.0.1.0.0`, lisensi `LGPL-3`. Kandidat kini adalah branch `ADDONS13-37-rev4` dengan titik awal `2d053aaa0f561b309fcd543d062c8e0f25fb46c3`; perubahan Step 1 Rev4 dijelaskan di bawah. Ini bukan hasil instalasi, uji runtime Odoo, audit keamanan, atau deployment.

Rujukan berikut menggunakan path relatif repositori dan `path:baris` kandidat; simbol metode adalah acuan utama. SHA-256 pada tabel integritas adalah hash berkas kandidat worktree, bukan hash upstream. Semua path source yang dikutip dalam panduan ini terdaftar satu kali pada tabel tersebut; simbol/rentang memberi lokasi klaim yang tepat.

`AGENTS.md` menetapkan Python 3.7 (`AGENTS.md:14-16`); kontrak Rev4 meminta target verifikasi Python 3.7.9. Suite offline dijalankan dengan Python 3.11.15; Python 3.7.9 NOT RUN. Tidak dilakukan install atau eksekusi ORM/RPC/HTTP/UAT.

## Arsitektur

Paket utama mengimpor pengendali, model, dan wizard (`amr_oidc/__init__.py:3-5`; `amr_oidc/models/__init__.py:3-8`). Controller mewarisi `ControllerToken`; `TokenHelper` mewarisi model abstract `amr.token.helper` dari addon induk (`amr_oidc/controllers/main.py:10-18`; `amr_oidc/models/helper.py:18-20`; `amr_token/models/helper.py:1-20`). Pewarisan membuktikan deklarasi perluasan, bukan bahwa pemanggil tertentu benar-benar menggunakan metode.

Manifest menyebut `base`, `web`, `amr_token`, dependensi Python `pyjwt`, `cryptography`, serta daftar data XML/ACL (`amr_oidc/__manifest__.py:4-23`). Ketersediaan paket, registry, dan kompatibilitas lingkungan tidak dibuktikan.

## Konsumen terverifikasi

**BELUM TERVERIFIKASI.** Dalam graf kode sumber yang diperiksa tidak ditemukan bukti pemanggil addon lain yang dapat ditetapkan sebagai konsumen aktual untuk API `amr_oidc`. Relasi pewarisan controller dan helper induk serta delegasi yang terlihat bukan bukti adanya pemanggil eksternal. Tidak disajikan contoh pemanggilan yang seolah-olah telah berjalan.

## Model, field, dan relasi

Atribut “tidak dinyatakan” berarti argumen itu tidak tertulis pada deklarasi field lokal; tidak menyimpulkan default ORM. Ringkasan berikut merangkum field lokal; simbol dan rentang deklarasi mengidentifikasi kontrak lengkap. Lihat pula hash file pada [peta integritas kode sumber](#peta-kode-sumber-dan-integritas).

| Model | Field lokal (tipe; atribut eksplisit penting) | Relasi, constraint, deklarasi |
|---|---|---|
| `oidc.client` | `active` Boolean default `True`; `name` Char; `user_id` Many2one default `1`; `client_id`, `client_email`, `web_base_url` Char; `client_secret` Char dengan `groups="base.group_erp_manager"`; `client_type` Selection default `machine`; `authentication_method` Selection default `client_secret`; `redirect_uri` Text; `redirect_path` Selection `list(REDIRECT_MODE.items())` default `auth_oauth_oidc`; `authorization_ids`, `key_ids` One2many. | Pengguna → `res.users`; authorization → `oidc.authorization.code` via `client_id`; keys → `oidc.client.key` via `client_id`. Model baru, tanpa SQL constraint lokal. `amr_oidc/models/oidc_client.py:14-52`. |
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
| `oidc.client.check_credentials` | `(self, client_secret)`: membandingkan nilai; `ValueError` bila mismatch, selain itu `True` (`amr_oidc/models/oidc_client.py:54-59`). |
| `oidc.client.validate_redirect_uri` | `(self, redirect_uri)`: bool; external wajib URI nonkosong dengan scheme/host dan kecocokan persis terhadap satu baris konfigurasi, termasuk query/fragment. Mode tetap wajib path yang dikenal dan base URL; URI absen atau persis callback diterima (`amr_oidc/models/oidc_client.py:61-72`). |
| `oidc.client.client_auth` | `(self, token)`: decode Basic credentials, lookup dengan `sudo`; mismatch/exception ditangani dengan `None` (`amr_oidc/models/oidc_client.py:74-86`). |
| `oidc.client.create_authorization_code` | `(self, redirect_uri=None, scope='')`: membuat code record dengan expiry lima menit memakai `sudo`; source memasukkan nilai string `self.client_id` ke `client_id`, sementara field tujuan adalah Many2one required (`amr_oidc/models/oidc_client.py:88-100`; `amr_oidc/models/oidc_authorization_code.py:13-18`). Ini mismatch tipe pada source; verifikasi ORM diperlukan. Bukan bukti kegagalan runtime. |
| `oidc.client.create_access_token` | `(self, redirect_uri=None, scope='', **kw)`: mendelegasikan pembuatan token ke `env.user.create_access_token` (`amr_oidc/models/oidc_client.py:102-110`). |
| `oidc.client.validate_token` | `(self, token)`: pada cabang falsy `self`, decode payload tanpa signature verify untuk mencari audience, lalu delegasi validasi ke helper parent (`amr_oidc/models/oidc_client.py:112-127`). |
| `oidc.client.validate_refresh_token` | `(self, token)`: delegasi ke model refresh token (`amr_oidc/models/oidc_client.py:129-130`). |
| `oidc.client.export_service_account` | `(self, algorithm)`: membentuk hasil yang mencakup private/public key material; tidak disalin atau diotorisasi oleh panduan (`amr_oidc/models/oidc_client.py:132-155`). |
| `oidc.client.action_export_service_account` | `(self)`: action window untuk wizard (`amr_oidc/models/oidc_client.py:157-168`). |
| `oidc.client.openid_configuration` | `(self)`: memperbarui hasil metadata parent; metadata bukan capability (`amr_oidc/models/helper.py:46-85`; `amr_token/models/helper.py:170-185`). |
| `oidc.client.oidc_token` | `(self, grant_type=None, **kwargs)`: dispatch lokal untuk cabang tertentu dan delegasi lainnya (`amr_oidc/models/helper.py:87-101`). |
| `do_client_credentials` | `(self, data)`: cabang mengambil credential Basic/body, lookup client, lalu delegasi token generation; lihat source (`amr_oidc/models/helper.py:130-171`). |
| `do_client_assertion` | `(self, assertion, data)`: validasi assertion/key/claims, membuat replay record dan delegasi token generation (`amr_oidc/models/helper.py:173-278`). |
| `do_refresh_grant` | `(self, refresh_token=None)`: memanggil validator tanpa audience, lalu mencari user dari `sub` dan delegasi (`amr_oidc/models/helper.py:280-291`). |
| Wizard `action_generate`, `action_save` | Metode wizard menghasilkan/menyimpan data account/key sesuai cabang source; jangan gunakan panduan ini sebagai prosedur ekspor atau menyimpan key (`amr_oidc/wizard/service_account.py:58-105`). |

Tidak ada endpoint API publik yang disimpulkan dari daftar metode ini.

## Rute dan deklarasi antarmuka

Dekorator rute menyatakan atribut statis berikut saja; atribut yang tidak ditulis tidak disimpulkan. Ini bukan jaminan rute terdaftar atau respons runtime (`amr_oidc/controllers/main.py`).

| Path | type | auth | methods | website | csrf | Deklarasi |
|---|---|---|---|---|---|---|
| `/oidc/authorize`, `/oidc/auth` | `http` | `public` | tidak eksplisit | tidak eksplisit | `False` | `:19` |
| `/oidc/continue` | `http` | `public` | `GET` | `True` | tidak eksplisit | `:40` |
| `/oidc/login_form` | `http` | `public` | `GET` | `True` | tidak eksplisit | `:44` |
| `/oidc/authorize_continue` | `http` | `user` | `POST` | tidak eksplisit | `True` | `:48` |
| `/oidc/login/submit` | `http` | `public` | `POST` | tidak eksplisit | `True` | `:53` |
| `/oidc/profile`, `/oidc/userinfo` | `http` | `none` | `GET` | tidak eksplisit | `False` | `:134` |

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

- **Tidak tersedia dalam addon/graf kode sumber/dependensi yang ditinjau:** authorization-code redemption/token exchange dan ID-token issuance. Addon ini tidak boleh disebut implementasi OIDC Authorization Code Flow lengkap (`amr_oidc/controllers/main.py:19-38,72-130`; dispatcher parent `amr_token/models/helper.py:191-204`).
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

Sumber baris/header: `amr_oidc/security/ir.model.access.csv:1-8`. Tidak ada baris untuk `oidc.jwt.replay` atau wizard. Ini deskripsi file saja: tidak membuktikan ACL efektif/izin, record rules, field access, atau keselamatan. Panduan tidak mengotorisasi atau menilai akses baca/ekspor secret/private key maupun akses record authorization-code.

### Persyaratan kebijakan — bukan bukti penegakan runtime

- Admin OIDC dipetakan ke `base.group_erp_manager` untuk client/code dan field secret; refresh-token memakai `base.group_system`. Public, portal, dan user biasa tidak diberi izin oleh ACL model tersebut. Lingkup ekspor/wizard tetap tidak dinilai.
- Akses langsung ORM/RPC `oidc.client` untuk operasi non-secret wajib tunduk pada kebijakan ACL/record-rule yang sama seperti UI/wizard, tanpa bypass.
- Record key dimaksudkan tercakup per user/client pemilik; tidak ada jaminan isolasi perusahaan.
- `sudo()` hanya untuk operasi sistem sempit yang dibenarkan.

Deklarasi kandidat sesuai batas group di atas; ini bukan bukti effective policy, record-rule enforcement, atau pemenuhan seluruh batas `sudo()`. Source memiliki pemanggilan `sudo()` pada client/helper (`amr_oidc/models/oidc_client.py:74-100`; `amr_oidc/models/helper.py:109-110,145-146,201-202,289-304`). Jangan menyimpulkan keamanan dari menu tersembunyi atau ACL statis.

### Perubahan terbatas Step 1 Rev4

- Predicate refresh mensyaratkan `expires_at > now` dan `revoked=False`; bukan bukti operasi refresh end-to-end.
- `get_secret` publik dihapus, diganti `_get_secret` privat; `create_refresh_token` dan `validate_token` tetap mengonsumsi secret secara internal. Tes offline tidak menguji reachability/penolakan dispatcher Odoo 13; UAT-026 NOT RUN.
- Validator redirect tidak lagi mengabaikan query/fragment atau menerima konfigurasi eksternal kosong. Fallback target eksternal kosong di pemeriksaan controller dihapus, sehingga input tidak valid berhenti sebelum penerbitan code/token pada metode yang diuji.
- `/oidc/login/submit` dan `/oidc/authorize_continue`: POST dengan `csrf=True`; form lanjut menyertakan token Odoo dan params. Penolakan GET/CSRF runtime NOT RUN.
- Override `do_password_grant`: kegagalan `user.with_user(user)._check_credentials` hanya mencatat pesan warning konstan; `do_client_credentials` menggunakan verifier aktual `client.check_credentials` (bukan nama `_check_credentials` dalam uraian lama). Keduanya mempertahankan return persis `{'status': 401, 'error': 'invalid_grant'}`, tanpa exception/stack di log. Tidak mengklaim status transport HTTP.
- `helper.py:247`, baseline `amr_token`, service-account/export/key lifecycle, SEC-06–14, UAT-012, rotasi dan deployment tetap di luar scope; tidak dinyatakan aman atau diterima. Step 2–4 belum dijalankan.

## Odoo 13 vs Odoo 20

Source/manifest yang diperiksa menargetkan Odoo 13 (`amr_oidc/__manifest__.py:4-12`). Tidak dilakukan perbandingan source Odoo 20; migrasi/kompatibilitas Odoo 20 tidak diklaim. Perubahan API, ORM, view, ACL atau JS pada versi 20 tidak dinilai.

## Bukti berkas pengujian

Suite `amr_oidc/tests` dijalankan offline dengan stub framework dan dependensi inert. Tes package historis dipertahankan, dengan hash ACL disesuaikan ke snapshot Rev4. Tes `test_security_boundaries.py` memeriksa ACL/field/route/template statis serta metode predicate/redirect aktual; getter publik harus tidak ada dan pemanggil internal memakai helper privat. Tes `test_failure_logging.py` menjalankan override aktual pada verifier yang melempar exception sintetis: return persis 401/invalid_grant, satu verifier, tanpa super/password atau generator token. Log ditangkap hanya dalam memori: pesan terender, args, exc_info, stack_info, hitungan str/repr diperiksa; logger dipulihkan. Bukan bukti dispatcher, ORM/HTTP, registry, pipeline log, atau UAT.

## Peta kode sumber dan integritas

Hash SHA-256 di bawah dihitung ulang dari berkas kandidat Step 1 Rev4. Seluruh path kode sumber yang dirujuk panduan ini dipetakan di bawah; hash bukan bukti runtime atau verdict Step 2.

| Repo-relative path | SHA-256 |
|---|---|
| `amr_oidc/__init__.py` | `51d0f9735a295f9969115778f66156098eb5de49ce6fd0abce6f4e57908b676b` |
| `amr_oidc/__manifest__.py` | `16fae221d45569fc5fea4e68748c00a3d732bdc2ef21fff2819782e029339ba0` |
| `amr_oidc/controllers/main.py` | `d523b270734331c80d814c6412a1b4b2b79e4ae851b9f68db5e44e39925893df` |
| `amr_oidc/models/__init__.py` | `942326411908a566afd11ec65a60f6698dc3a1b438b0020d1c43a4992792ecc2` |
| `amr_oidc/models/helper.py` | `9ab1d08505e93007b999cf12759b471bf8d1c01afa7c967210bd064020a1a93c` |
| `amr_oidc/models/oidc_authorization_code.py` | `23f64d0da605ba6abf9847bee42d81e87aa7d65a67d93dfd783c06fba34c6597` |
| `amr_oidc/models/oidc_client.py` | `a49d07c85e3970c6776a5ba7502f2c4a8d457941d6ae6e26c3c8e917f3f79a4a` |
| `amr_oidc/models/oidc_client_key.py` | `1f5238eea4f73bbe21a274ecac34d184954d05d2cb442f011efbfde41b2c3ef0` |
| `amr_oidc/models/oidc_jwt_replay.py` | `b7c49e3a71eb86c47881c318fbf7f4a9445b8b3f1aecc3af954d04a6b045c5b9` |
| `amr_oidc/models/oidc_refresh_token.py` | `e90fd66e9d22c41a0a14725cb4f73e3557adf6740389fd5a20ecaf7866e3e627` |
| `amr_oidc/security/ir.model.access.csv` | `19b84b88e264d08b3a631d90f83489699df94da3441bf9ed61b81f430a1a9b31` |
| `amr_oidc/tests/test_package_contract.py` | `d93fa998e6573731ac61d22248f2836d018ca8cf32eb99bab90dc8e19e7170ba` |
| `amr_oidc/views/login_template.xml` | `3362ae4245c8cc251769531733d2bfba26b75b5b80f97a3053f31e6fe48b301c` |
| `amr_oidc/views/menuitem.xml` | `c21871d804c848ed687ee3c4f8c5a2744a4eac44ab80e22a178c5a0a4d9eb6ba` |
| `amr_oidc/views/oidc_authorization_code_views.xml` | `178b386eb5d5d575dcee03463ae5f777722debed9157261d30f1ed642c8335a3` |
| `amr_oidc/views/oidc_client_views.xml` | `0ccc1b31fb79f70e56b757ef259990e24ff39783915822a402622e343ac51ec8` |
| `amr_oidc/wizard/service_account.py` | `cc3dbb56ca8f98dffea0ecda38e8bc6632da10a7741a6107cd867db087624550` |
| `amr_oidc/wizard/service_account.xml` | `a5a25cc05fd88ab531ad612ce6f495ef9fabe59e6690b607fc0d5dc1a5d1aab7` |
| `amr_token/models/helper.py` | `e286ae9022c66807c8fb6d6a1dc8af90a1a5c4e1243d42949e3de92a18d3a1dc` |

| `amr_oidc/tests/support.py` | `7b1996c66a6a0a942fd6ae9c3f17da1d6347ec5fc398109ba4a6a9e649140802` |

| `amr_oidc/tests/test_security_boundaries.py` | `1b4f79fd373c1995cd01c1d4f566df6e0afaa3a9a160a683f5c4fa5f18443749` |

| `amr_oidc/tests/test_failure_logging.py` | `5b71709c364b41226eca44030c244deaa57744f9c95c4cf1fc87c7fef142146a` |

[PERLU KONFIRMASI] Registry/runtime, role dan akses efektif, route/UI visibility, dependency aktual, konfigurasi deployed, flow OIDC dan interoperabilitas memerlukan bukti terpisah. Penegakan runtime kebijakan di atas belum dibuktikan. Batas deklaratif client-secret/code termasuk scope; ekspor private-key/wizard tetap tidak dinilai.
