# Modul `amr_resource` — Panduan Developer

> Task: ADDONS13-24 — dokumentasi kandidat addon `amr_resource` (Odoo 13).
>
> Source module: commit `7a6f09bef97f38d53566b1351c3178c536fdb4e4`; target baseline worktree `377537b4d428a5105eee4d72547ec077b0f03569`.
>
> Status: DRAFT. Review independen atas isi dokumentasi serta layout folder `docs/` dan link relatif kandidat ini: **PASS terbatas**; final acceptance Lead tetap terpisah. Ini bukan test/security acceptance.
>
> Bukti runtime: test belum PASS terverifikasi; risiko keamanan tetap PENDING/BLOCKED.

## Untuk Developer

### 1. Arsitektur

`amr_resource` adalah addon Odoo 13 yang berperan sebagai *Resource Server*: ia menyediakan helper validasi token, pemetaan token ke pengguna Odoo, metode autentikasi untuk request, serta controller terkait URL akses dan JSON-RPC. Addon ini bukan OIDC Provider/IdP dan tidak menandatangani/menerbitkan token sendiri; `generate_token()` dapat meminta token ke token endpoint yang ditemukan melalui discovery. Wording `Resource Server` juga digunakan pada manifest. (`__manifest__.py:4-16`; `models/helper.py:15-218`; `models/ir_http.py:10-139`; `controllers/main.py:14-106`.)

Komponen yang tampak pada source:

```text
Controller routes ──> auth methods di ir.http ──> ResourceHelper
       │                                      └──> res.users matching
       ├──> URL hooks pada res.users
       └──> call_kw Odoo (hak efektif ditentukan juga oleh core/rules)
Settings view ──> res.config.settings ──> ir.config_parameter
Wizard form ──> transient create-user wizard ──> res.users
```

Diagram ini menunjukkan koneksi statis pada addon; ia bukan bukti route dispatch, permission efektif, instalasi, atau alur runtime. Manifest mendeklarasikan dependensi Odoo `base`, `web`, dan `base_setup`, serta memuat XML group, settings view, dan wizard. (`__manifest__.py:4-16`; `__init__.py:3-6`; `models/__init__.py:3-6`; `controllers/__init__.py:3`; `wizard/__init__.py:3`.)

### 2. Model, Field, dan Relasi

Model/helper yang dideklarasikan atau diwarisi oleh addon:

| Model / class | Kontrak source | Field/relasi lokal | Bukti |
|---|---|---|---|
| `amr.resource.helper` / `ResourceHelper` | `models.AbstractModel`; helper konfigurasi, discovery, introspection, validasi token, dan pencocokan user | Tidak ada field lokal yang dideklarasikan | `models/helper.py:15-218` |
| `ir.http` / `IrHttp` | `models.AbstractModel` extension; mengimplementasikan metode autentikasi machine/params/user-or-param dan helper context/session | Tidak ada field lokal yang dideklarasikan | `models/ir_http.py:10-139` |
| `base` / `Base` | extension dengan helper `user_machine_sudo()` untuk memilih environment machine-user | Tidak ada field lokal yang dideklarasikan | `models/res_users.py:11-26` |
| `res.users` / `ResUsers` | extension untuk predicate group, pemetaan user/token, dan URL hooks | Tidak ada field lokal yang dideklarasikan | `models/res_users.py:29-95` |
| `res.config.settings` / `ResConfigSettings` | `models.TransientModel`; selector issuer/audience, preview hasil compute, freeze, serta checkbox install modul | Rinciannya di bawah | `models/res_config_settings.py:6-78` |
| `create.user.wizard` / `CreateUserWizard` | transient wizard untuk membuat user dari template | `name` Char required; `login` Char required; `email` Char opsional; `template_id` Many2one ke `res.users`, required | `wizard/create_user_wizard.py:7-37` |

Field settings dan perilakunya pada source:

| Field | Kontrak source | Bukti |
|---|---|---|
| `amr_select_issuer` | Selection; parameter `amr_resource.issuer`; default selector `web.base.url` | `models/res_config_settings.py:9-15` |
| `amr_resource_issuer` | Char computed dari parameter yang dipilih; field ini tidak muncul pada XML view yang diperiksa | `models/res_config_settings.py:12-15,50-56`; `views/res_config_settings_views.xml:2-47` |
| `amr_select_audience` | Selection; parameter `amr_resource.audience`; default selector `web.base.url` | `models/res_config_settings.py:17-24` |
| `amr_resource_audience` | Char computed; membaca nilai parameter yang ditunjuk selector, tanpa deklarasi `config_parameter`, `store`, atau `inverse` | `models/res_config_settings.py:21-24,59-66` |
| `amr_web_base_url_freeze` | Boolean; parameter `web.base.url.freeze`; tidak memiliki default eksplisit | `models/res_config_settings.py:25-29` |
| `module_amr_approval_aggregator`, `module_amr_oidc`, `module_amr_oidc_client`, `module_amr_token`, `module_amr_oauth`, `module_amr_auto_login`, `module_amr_signature`, `module_amr_esign_pdf`, `module_amr_service_client`, `module_amr_data_push`, `module_amr_data_sync`, `module_amr_approval_task_client`, `module_amr_notification_client` | Checkbox `module_*` di settings. Keberadaan field bukan bukti addon pasangan terpasang/tersedia; tidak semua field ditampilkan pada view. | `models/res_config_settings.py:31-48`; `views/res_config_settings_views.xml:31-175` |

XML seed mendeklarasikan group machine dan technical serta template user machine. Tidak ada `ir.model.access.csv` atau record rule lokal pada snapshot. Group pada view membatasi tampilan XML, tetapi hak efektif baca/tulis melalui ORM, RPC, form parameter, dan core Odoo belum dibuktikan. Jangan menyimpulkan tidak adanya ACL lokal sebagai akses terbuka atau sebagai jaminan least privilege. (`security/res_groups.xml:3-26`; `views/res_config_settings_views.xml:2-30`; `models/res_config_settings.py:50-78`.)

### 3. Cara Modul Lain Memakainya

**BELUM TERVERIFIKASI untuk konsumen lintas-addon.** Kandidat ini hanya memuat `amr_resource`; tidak ada pemanggilan konsumen dari addon lain di dalamnya. Karena itu Panduan ini tidak mengarang contoh integrasi yang seolah-olah telah digunakan atau diuji. Method helper yang tersedia tercantum pada bagian API; test package lokal memanggil helper sebagai karakterisasi source, tetapi test tersebut belum dieksekusi. (`models/helper.py:19-218`; `tests/test_helper.py`; `tests/test_contracts.py`.)

### 4. API / Method Publik

Method berikut adalah kontrak source, bukan janji keberhasilan runtime. Penggunaan memerlukan lingkungan Odoo dan dependensi yang sesuai.

| Area | Method/route | Perilaku yang tampak pada source | Bukti |
|---|---|---|---|
| Konfigurasi | `get_issuer()`, `is_local_issuer(issuer)` | `get_issuer` menyelesaikan parameter issuer lalu fallback ke `web.base.url`; `is_local_issuer` membandingkan issuer dengan nilai `web.base.url` secara langsung. | `models/helper.py:19-27` |
| Audience | `get_audience()`, `get_audiences(issuer=None)` | Menyelesaikan nilai audience dari selector; `get_audiences` mengembalikan list satu elemen dan tidak memakai argumen `issuer`. | `models/helper.py:29-37` |
| Discovery | `get_oidc_config(issuer)`, `get_jwks_data(issuer)` | Membuat GET ke URL well-known yang disusun dari issuer, lalu `raise_for_status()` dan membaca JSON. Kedua request tidak menetapkan timeout eksplisit. | `models/helper.py:39-51` |
| Token | `generate_token(...)`, `encode(...)`, `decode(token)` | `generate_token` mengambil token endpoint dari discovery lalu POST dengan `data`; Basic auth hanya dipasang bila kedua credential truthy. `encode` mengambil `access_token` dari respons; `decode` meneruskan token ke `validate`. | `models/helper.py:53-73` |
| Introspection/validasi | `introspect_token(...)`, `validate_hs(token)`, `validate(token)` | Introspection menggunakan GET dengan body `data` yang berisi token. Jalur HS memakai hasil introspection aktif; jalur non-HS melakukan lookup discovery/JWKS dan memanggil decode terverifikasi dengan parameter dari source. | `models/helper.py:82-149` |
| Pemetaan user | `get_validate_user(token)`, `get_user_match(validation)`, `get_user_token_login(token)`, `get_uid(payload)`, `is_user_match(user,payload)` | Helper memvalidasi payload lalu mencari user menurut urutan source; pencarian dilakukan dengan `sudo()` dan dapat memasukkan machine user inactive. Tidak ada pemetaan terpisah issuer+subject yang dibuktikan. | `models/helper.py:151-193` |
| Ekstraksi token | `get_param_token()`, `get_header_token()`, `get_bearer_token()` | Membaca alias query/form/header/Bearer sesuai urutan dan pola yang ditentukan source; malformed/missing Bearer dapat menghasilkan `None`. | `models/helper.py:195-218` |
| User helpers | `user_machine_sudo(user)`, `is_user_machine()`, `is_user_technical()`, `is_user_business()`, `is_user_allow_create_token()` | Predicate dan pemilihan environment mengikuti source; method `user_machine_sudo` memiliki konsekuensi privilege yang harus ditinjau. | `models/res_users.py:14-46` |
| Auth Odoo | `_auth_method_machine`, `_auth_method_params`, `_auth_method_user_or_param` | Memetakan token/parameter ke user. `user_or_param` mencoba beberapa cabang berurutan; sebagian exception ditangkap luas. UID yang berbeda memperbarui request metadata, sedangkan UID sama tidak selalu mengisi ulang metadata. | `models/ir_http.py:41-108` |
| Session/context helpers | `set_session(user,session_token)`, `get_jwt_payload()`, `check_scope(required_scope)` | `set_session` terpisah dari auth methods; `get_jwt_payload` default kosong dan `check_scope` no-op. | `models/ir_http.py:14-39,126-139` |
| URL & controller | `GET /redirect`, `GET /api/v1/access_token/url`, `/api/test/connection/machine` | Dua route GET pertama menggunakan `auth='user_or_param'` dan `csrf=False`; connection route menggunakan `auth='machine'`, sementara decorator tidak menyatakan `methods`/`type` secara eksplisit. URL helper memakai input atau hook model/user. | `controllers/main.py:51-95` |
| JSON-RPC | JSON route `/api/dataset/call_kw` (`auth='machine'`) | Memanggil pemeriksaan nama method lalu Odoo `call_kw`; tidak tampak pemeriksaan scope tambahan lokal. Hak akses efektif tetap bergantung pada Odoo/core/rules yang belum diuji. | `controllers/main.py:98-106`; `models/ir_http.py:126-139` |
| Wizard | `action_create()` | Menolak login duplikat, membuat `res.users` dari input dan group/share milik template, lalu mengembalikan action form. `active` template tidak disalin eksplisit. | `wizard/create_user_wizard.py:17-37` |

Batas penting API:

- `get_access_token()` dan `create_access_token()` pada `res.users` adalah stub, bukan penerbitan token yang berfungsi; source memakai `raise NotImplemented`. `add_url_access_token()` dan `get_auto_login_url()` default tidak menambahkan token. (`models/res_users.py:48-77`.)
- `check_scope()` adalah no-op dan `get_jwt_payload()` default mengembalikan payload kosong. Jangan memperlakukan keduanya sebagai enforcement. (`models/ir_http.py:126-139`.)
- Route controller memanggil helper masing-masing; helper `handle_exception` di `exceptions.py` tidak membuktikan bahwa semua route memakai format/status error yang seragam. (`controllers/main.py:16-49,51-106`; `exceptions.py:8-36`.)
- Pada route URL publik, pemeriksaan hook dan hook yang dipanggil tidak konsisten pada source; ini dicatat sebagai gap, bukan diubah menjadi kontrak sukses. (`controllers/main.py:57-91`.)

### 5. Dependensi

**Odoo manifest:** `base`, `web`, `base_setup`. Modul mengimpor Odoo serta library Python `requests`, `jwt`/`PyJWKClient`, dan `werkzeug`. Tidak ada versi paket eksternal yang dipin dalam manifest. Ketersediaan versi yang kompatibel dengan instalasi target Odoo 13 belum diverifikasi; file source saja tidak membuktikan instalasi berhasil. (`__manifest__.py:4-16`; `models/helper.py:5,76-78,114-116`; `models/ir_http.py:3`; `controllers/main.py:5-7`.)

### 6. Konfigurasi

Parameter berikut adalah *key names*, bukan nilai konfigurasi runtime:

| Parameter | Makna pada source | Catatan |
|---|---|---|
| `amr_resource.issuer` | Menyimpan pilihan key issuer; nilai bawaan selector `web.base.url` | Field issuer computed tidak ditempatkan di view yang diperiksa; konfigurasi UI/runtime belum diverifikasi. |
| `amr_resource.audience` | Menyimpan pilihan key audience; nilai bawaan selector `web.base.url` | Helper membaca nilai key yang dirujuk; bila kosong, helper fallback ke `web.base.url`. Field computed pada UI membaca key yang dipilih dengan default kosong, sehingga hasil UI dan helper dapat berbeda. |
| `web.base.url.freeze` | Parameter Boolean untuk freeze | Field tidak menetapkan default; implementasi perilaku freeze di core Odoo berada di luar snapshot. |

`action_edit_web_base_url()` melakukan pencarian parameter dengan `sudo()` lalu mengembalikan action form untuk record yang ditemukan; method itu sendiri tidak menulis parameter. Keberadaan record dan akses efektif form perlu uji runtime. (`models/res_config_settings.py:9-29,50-78`; `models/helper.py:19-37`.)

Jangan mengaktifkan checkbox `module_*` secara massal. Ketersediaan sibling addon, dependency closure, serta konsekuensi instalasinya tidak dibuktikan oleh snapshot ini. Jangan masukkan nilai issuer, audience, token, client secret, atau signing material produksi ke README, test, log, atau tiket.

### 7. Error Handling

- Request HTTP memanggil `raise_for_status()` dan kemudian membaca JSON; tidak ada timeout eksplisit pada GET/POST yang ditinjau. Kegagalan jaringan/HTTP/JSON dapat muncul dari library dan tidak selalu dikonversi ke satu respons aplikasi. (`models/helper.py:39-51,61-73,83-102`.)
- Source melempar `ValueError` untuk beberapa prasyarat issuer/endpoint dan `InvalidTokenError` saat hasil introspection tidak aktif. Cabang lain mempertahankan exception library atau menangani exception berbeda-beda. (`models/helper.py:61-73,83-110,114-149`.)
- Kegagalan parsing header JWT mencatat token mentah melalui logger sebelum exception dilempar. Jangan menyalin token atau raw log ke support ticket; gunakan placeholder sintetis dan lakukan redaksi sebelum eskalasi. (`models/helper.py:114-121`.)
- Controller memiliki beberapa pembentuk respons/error tersendiri. Tidak ada bukti bahwa helper exception menjadi handler global untuk semua route. Untuk diagnosis, catat kelas error dan jalur/versi, bukan token, credential, payload pribadi, atau raw error yang mungkin memuat input. (`controllers/main.py:16-49`; `exceptions.py:8-36`.)

### 8. Catatan Pola Odoo 13 vs 20

Fakta source yang diperiksa adalah addon versi Odoo 13 (`13.0.0.0.8`). Tidak ada bukti port atau eksekusi pada Odoo 20. Status Odoo 20: **belum diverifikasi; jangan digunakan sebagai kompatibel atau sudah dimigrasikan**. Sebelum migrasi, verifikasi dependency/runtime, API ORM/auth, views/settings, ACL dan kontrak controller pada target; pertahankan temuan source sebagai baseline sampai ada persetujuan perubahan behavior. (`__manifest__.py:4-16`; Developer Report, bagian identitas/provenance dan NOT RUN.)

### 9. Keamanan dan Batasan

Bagian ini merangkum risiko/kesenjangan source yang belum ditutup; bukan pernyataan bahwa eksploitasi telah dibuktikan, dan bukan clearance keamanan:

- `issuer`, discovery, `jwks_uri`, endpoint introspection/token berpotensi diturunkan dari input/payload tanpa allowlist host/issuer lokal yang terbukti. Requests tidak menetapkan timeout. Risiko trust boundary/outbound request tetap **PENDING/BLOCKED**. (`models/helper.py:39-51,61-102,114-149`.)
- Audience bukan allowlist issuer. Tidak terlihat enforcement scope lokal; `check_scope()` no-op. (`models/helper.py:29-37,114-149`; `models/ir_http.py:126-139`.)
- Jalur machine menggunakan user mapping yang privileged; helper machine dapat membuat environment dengan `su=True`. Generic JSON-RPC meneruskan method ke `call_kw`; kebijakan akses efektif belum diuji. Jangan gunakan endpoint ini untuk operasi sensitif tanpa security/access review dan validasi konfigurasi terpisah. (`models/res_users.py:14-26`; `controllers/main.py:98-106`.)
- Matching user memakai klaim seperti email/login/sub dan pencarian `sudo`; machine user inactive dapat termasuk. Ikatan issuer-subject dan matriks role belum dibuktikan. (`models/helper.py:151-176`.)
- Token mentah dapat masuk log saat parsing gagal; route redirect/URL tidak membuktikan allowlist tujuan. Jangan menaruh bearer token pada URL atau menyebarkannya di log. (`models/helper.py:114-121,195-218`; `controllers/main.py:51-91`.)
- Test yang ada hanya desain/karakterisasi source dan sebagian boundary dimock. Reviewer independen menemukan assertion mock logger yang mengharapkan token sintetis, mock JWT/JWKS, direct call controller tanpa route/ACL coverage, serta UT-08 yang bergantung pada efek `TypeError` dari `raise NotImplemented`. Test tidak lulus otomatis karena belum dijalankan dan bukan security acceptance. (`tests/test_helper.py`; `tests/test_contracts.py`; Developer Report, bagian Review.)

### 10. Bukti dan status verifikasi

- Developer Report mencatat 15 file produksi byte-identik dengan sumber, 3 file test ditambahkan, serta pemeriksaan statis Python/XML. README.md pada root addon menjadi indeks dokumentasi; panduan Developer/User ini berada di docs/. Kandidat worktree belum menghasilkan commit/SHA final.
- Eksekusi unit test: **NOT RUN / tidak ada PASS terverifikasi**. Percobaan lokal berhenti sebelum collection karena runtime Odoo tidak tersedia. Satu percobaan QA yang diizinkan berakhir exit 1 tanpa summary runner; penyebab runtime persis tidak terkonfirmasi. Tidak ada retry tanpa otorisasi baru.
- Review statis independen sebelumnya: **INCONCLUSIVE** untuk test coverage/security. Risiko tetap **PENDING/BLOCKED**; Lead memilih melanjutkan ke jalur PR-ready/dokumentasi, tetapi pilihan tersebut tidak mengubah bukti tes atau menyatakan risiko security PASS.
- Instalasi, upgrade, rendering UI, ACL/role matrix, integrasi provider, browser, rollback, dan deployment: **BELUM TERVERIFIKASI / NOT RUN**.

Rujukan detail evidence task ADDONS13-24 disimpan terpisah dari paket addon; dokumen ini merangkum status test dan risiko yang relevan, dan tidak menganggap laporan lokal sebagai file release.
