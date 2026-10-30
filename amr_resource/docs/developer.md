# Panduan Developer — `amr_resource`

## 1. Target dan arsitektur

Versi source `13.0.1.0.0`, Odoo 13 / Python 3.7.9. Manifest bergantung hanya pada `base`, `web`, `base_setup`; dependency eksternal `jwt` dan `cryptography` dinyatakan eksplisit. Tidak mengasumsikan `amr_token` atau sibling terpasang. Instalasi, effective MRO, dan dependency closure Odoo harus diverifikasi terpisah pada lingkungan disposable yang diotorisasi. `__manifest__.py:1-21`

Inbound: consumer → `amr.resource.helper` → lookup exact registry sesuai company efektif → signature/introspection dan claims → provenance internal → satu resolver → tepat satu user eligible. Issuer token adalah hint lookup, bukan URL yang boleh diikuti. Session sah didahulukan; tanpa session, bearer mendahului params; bearer invalid tidak fallback. Metadata request hanya diperbarui bila UID berubah. `models/helper.py:44-317`; `models/ir_http.py:66-76`; `models/ir_http.py:41-56`

## 2. Model dan akses

- `oidc.issuer.register`: issuer exact unik global termasuk archived; company, active, profil JWT/opaque, endpoint statis, client ID, azp, credential/key reference, resolver, audience/binding children dan audit source.
- `oidc.issuer.register.audience`: `issuer_id`, `value`; unik `(issuer_id, value)`; minimal satu audience tidak dapat dihapus/reparent tanpa menolak transaksi.
- `oidc.issuer.subject`: `issuer_id`, `sub`, `user_id`; unik `(issuer_id, sub)`; tidak ada mapping email/login atau binding otomatis.
- `amr.resource.registry.access`: mixin kontrol akses; tidak menyediakan tabel trust alternatif.

Nama model mengikuti kontrak registry, bukan addon issuer eksternal. Source dan constraints: `models/trust_registry.py:165-384`; `models/trust_registry.py:387-417`; `models/trust_registry.py:420-442`.

Group `group_oidc_trust_admin` dan `group_oidc_code_admin` diberikan manual kepada administrator internal `base.group_system`. Trust admin mengelola profil/binding; code admin hanya storage source beserta audit, bukan izin mengeksekusi/activate. User biasa/public/portal tidak diberi akses registry. ACL, company record rules, field groups dan guard backend melengkapi view; jangan menganggap visibilitas XML sebagai kontrol tunggal. Lookup runtime melakukan elevated read terbatas, tetapi hasil user dibrowse dan resolver berjalan pada environment pemanggil, bukan implicit sudo. `security/ir.model.access.csv:1-5`; `security/registry_rules.xml:1-19`; `models/trust_registry.py:94-162`; `models/trust_registry.py:370-384`

## 3. Profil token dan resolver

JWT hanya RS256/RSA public key ≥2048 bit, `typ=at+jwt`; key berasal dari JWKS statis atau protected local-key reference, bukan claim URL. Wajib `iss`, `aud`, `exp`, `iat`, `jti`, `sub`, `client_id`; `nbf` dicek bila ada; leeway 0. Header key override/critical extension tidak didukung. Signature diverifikasi oleh library asli sebelum claim/resolver. `models/helper.py:207-248`

Opaque diterima hanya melalui profil introspection registry terpilih; tidak ada fallback JWT→opaque. POST form ke endpoint tepercaya, `active` harus boolean tepat `True`. Issuer response bila absen ditambatkan ke profil; bila ada harus exact-match. `sub`, `aud`, `client_id`, expiry dan claim waktu yang hadir divalidasi. `aud` berupa string/list string nonkosong dan ANY exact-match audience; `azp` bila hadir harus satu string exact-match konfigurasi, dan hanya boleh absen bila diizinkan. `models/helper.py:190-201`; `models/helper.py:151-188`

Pilihan `get_user_match` berlabel **Default**, tanpa default/preselection otomatis; memakai exact issuer-subject binding. `fixed_user` memakai user konfigurasi, bukan UID claim. `resolver` hanya key allowlist kode `get_user_match`; tidak menerima nama model/method bebas. Semua mode menghasilkan satu `res.users` aktif, internal non-superuser/non-public/non-portal dan company request termasuk company user. Tidak fallback antarresolver. Stored Python tidak dieksekusi; edit source menghasilkan revision/digest/actor/time melalui ORM. `models/helper.py:268-283`; `models/helper.py:254-260`; `models/trust_registry.py:282-287`

## 4. Helper dan consumer

| API | Kontrak |
|---|---|
| `get_issuer`, `get_audience`, `get_audiences` | Registry aktif pada company efektif; tanpa selector harus tepat satu profil yang sesuai. Tidak fallback ke `web.base.url`. |
| `get_oidc_config(issuer)` | Mapping endpoint dari registry; namanya dipertahankan tetapi tidak melakukan Discovery. |
| `get_jwks_data(issuer)` | JWKS endpoint registry dengan transport terbatas; tidak memakai PyJWKClient/cachenya. |
| `validate`, `decode`, `get_validate_user` | Claims terverifikasi dengan provenance internal; signature public dipertahankan. HS/ID token ditolak, bukan introspection fallback. |
| `get_user_match`, `get_uid`, `is_user_match` | Memerlukan provenance internal yang terikat company/UID dan payload utuh; dict biasa/context marker tidak cukup. |
| `get_param_token`, `get_header_token`, `get_bearer_token` | Ekstraksi saja, bukan validasi; header bearer hadir namun malformed ditolak. |
| `res.users.decode` / `with_access_token_context` | UID harus sesuai principal; request-payload/context tidak boleh memalsukan provenance. |

Sumber: `models/helper.py:44-317`; `models/res_users.py:45-52`; `models/res_users.py:76-90`.

## 5. Transport, key dan credential

HTTPS port 443, TLS verification dan hostname check aktif; tanpa userinfo, redirect, proxy environment atau retry. Semua hasil DNS harus public; address dipin pada socket saat connect agar tidak resolve ulang ke alamat lain. Connect 3 s, read 5 s, deadline total 8 s; response maksimum 1 MiB. Berlaku pada token, introspection dan JWKS. Tidak ada Discovery, HTTP loopback lokal, addon token/metadata/JWKS cache, maupun PyJWKClient. `transport.py:212-257`; `transport.py:85-125`; `transport.py:163-185`

`credential_ref` adalah **nama key** `ir.config_parameter` yang menunjuk client secret; bukan secret literal. Basic credential hanya dibentuk setelah trusted lookup. `local_key_ref` menunjuk parameter protected berisi RSA public PEM; bukan URL, path private-key atau PEM inline. Nilai computed `local_public_key` read-only untuk kompatibilitas internal/validasi konfigurasi; tidak boleh ditulis melalui ORM/RPC/default context. Token validation membaca parameter key secara langsung pada tiap panggilan, sehingga rotasi key tidak memakai nilai computed/cached lama. Batasi akses konfigurasi core ke administrator yang ditunjuk; addon tidak menambahkan secret field biasa. Jangan menaruh private key, token atau secret di source/log. `models/helper.py:118-126`; `models/helper.py:109-116`; `models/trust_registry.py:262-268`; `models/trust_registry.py:270-280`

## 6. Settings dan migrasi legacy v1

Settings membuka action **Trusted Issuers** dengan guard trust-admin; selector issuer/audience lama tidak lagi dipresentasikan sebagai konfigurasi autentikasi aktif. Freeze `web.base.url` tetap setting global, tidak memilih trust. Checkbox sibling tetap opsional, bukan dependensi addon ini. `models/res_config_settings.py:49-55`; `views/res_config_settings_views.xml:1-172`

Migrasi **eksplisit**, additive, versioned dan idempotent melalui private ORM method administrator:

```python
registry._migrate_legacy_v1(values, audiences, bindings, dry_run=True)
# Apply hanya setelah dry-run, backup, otorisasi dan restore rehearsal QA:
registry._migrate_legacy_v1(values, audiences, bindings, dry_run=False)
```

Ini API pada sesi ORM tepercaya yang diotorisasi, bukan route/RPC publik, bukan instruksi untuk menjalankan produksi, dan tidak dipanggil otomatis saat install/upgrade/token validation.

1. Parameter legacy `amr_resource.issuer` dan `amr_resource.audience` harus berisi **key name eksplisit**; resolve masing-masing key satu kali. URL literal di selector, reference hilang/invalid atau implicit `web.base.url` ditolak.
2. Administrator memasok `values` profil lengkap sesuai policy: `issuer`, `client_id`, `token_profile`, endpoint/key reference, kebijakan azp, **resolver_mode eksplisit** dan optional fixed user. `audiences` list exact unik harus memuat legacy audience. Issuer harus sama persis hasil reference legacy. Tidak mengambil endpoint dari Discovery/token.
3. `bindings` list mapping tepat `sub`/`user_id`, ditentukan administrator; duplicate subject, user invalid/ineligible, email-only mapping/collision dan scope berbeda ditolak. Tidak menebak subject dari email/login.
4. Dry-run memvalidasi plan, profile dan user tanpa create/write. Apply membuat profil/audience/binding dan marker digest `amr_resource.migration.v1.company.<id>` dalam satu savepoint; source parameter lama tidak dihapus/ditulis ulang. Audit ORM mencatat actor; log migrasi hanya version/company/actor/count.
5. Repeat plan yang identik memeriksa ulang seluruh policy/audience/binding dan tidak membuat duplikat. Konflik marker/referensi, data yang berubah/hilang, issuer global/archived/company berbeda atau binding ambigu ditolak, bukan overwrite/`limit=1`.

Sumber: `models/trust_registry.py:48-92`; `models/trust_registry.py:206-260`.

Rollback bukan hanya checkout kode. Pertahankan backup code/schema, konfigurasi legacy dan registry, credential/key references, audit/revision, serta keadaan worker/cache; lakukan restore rehearsal pada QA disposable sebelum rollout. Tidak ada destructive cleanup atau automatic reverse migration dalam addon ini. Restore kode lama yang memakai Discovery bukan bukti recovery aman.

## 7. Dependencies dan pengujian

`requirements.txt` mempin PyJWT 2.8.0, cryptography 39.0.2, cffi 1.15.1, pycparser 2.21 untuk Python 3.7.9. Pin mereproduksi library di runner offline, bukan bukti package closure seluruh Odoo berhasil diinstal. Gunakan constraints Odoo yang disetujui; jangan upgrade dependency bersama/sibling tanpa pemeriksaan terpisah. `requirements.txt:1-5`; `tests/test_migration_unit.py:92-95`

- `test_*_unit.py`: unittest offline; import candidate method asli dengan stub Odoo/ORM/request dan transport/DNS/socket boundaries tertutup. Vector JWT memakai key ephemeral dan signature library asli. Model migration dry-run/repeat/conflict diuji dengan ORM boundary stub; bukan transaksi DB nyata.
- `test_helper.py`, `test_contracts.py`, `test_registry.py`: Odoo-native SavepointCase, diimpor oleh `tests/__init__.py`; perlu registry/DB terotorisasi dan runner Odoo asli. Test legacy yang behavior-nya berubah diperbarui ke reject/static/binding/provenance contract; controller/session/wizard/seed assertions yang tak berubah tetap ada.
- Tidak ada klaim ACL/RPC/UI/HTTP dispatch, install/upgrade, multiworker, real network, effective MRO, rollback rehearsal atau UAT lulus dari suite offline. Bukti run per kandidat disimpan terpisah dari panduan produk.

Sumber: `tests/__init__.py:1-3`; `tests/test_registry.py:1-82`; `tests/test_security_unit.py:1-438`; `tests/test_transport_unit.py:1-394`.

## 8. Errors dan batas keamanan

Kegagalan helper token/resolver menjadi Unauthorized generik; payload, secret, endpoint credential atau exception body tidak dikembalikan. Error administrasi konfigurasi memakai ValidationError/AccessError tanpa dump konfigurasi. `models/helper.py:22-30`; `models/trust_registry.py:94-162`

Controller JSON-RPC `call_kw`, scope stub dan kemampuan modul sibling tetap membutuhkan review/runtime sendiri; addon ini tidak mengklaim membatasi seluruh pemanggilan bisnis melalui perubahan trust. Jangan menganggap helper machine sebagai izin menjadi superuser. `user_machine_sudo` mempertahankan nama publik tetapi memakai `with_user` tanpa implicit sudo. `controllers/main.py:98-106`; `models/ir_http.py:84-86`; `models/res_users.py:11-23`

Odoo 20, external issuer issuance, stored-code execution dan deploy tidak termasuk kemampuan yang diverifikasi oleh source ini.
