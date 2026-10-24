# Panduan User — Resource Server

## Untuk siapa

Pengguna biasa tidak mengelola issuer/token atau stored source. Konfigurasi dilakukan administrator internal yang ditunjuk dengan `base.group_system` dan **Trust Admin**; **Code Admin** terpisah hanya untuk penyimpanan source yang tidak dieksekusi. Group tidak otomatis diberikan. `security/res_groups.xml:1-37`; `models/trust_registry.py:94-162`

## Menu dan konfigurasi

Source menyediakan **Settings → Resource Trust → Trusted Issuers** dan action Trusted Issuers pada blok Server Resource. Render/menu/hak efektif di instance harus diverifikasi administrator; keberadaan view bukan bukti runtime. Code Admin mempunyai menu **Stored Source (Disabled)**; ini bukan tombol aktivasi Python. `views/trust_registry_views.xml:1-91`; `views/res_config_settings_views.xml:1-172`

Pada company request yang benar, administrator:

1. Membuat issuer HTTPS exact unik dan aktif; case/trailing slash tidak dinormalisasi. Memilih profil JWT atau opaque secara eksplisit.
2. Menetapkan client ID dan minimal satu audience exact unik. Token cukup memiliki satu audience yang cocok (ANY).
3. Menetapkan azp exact, atau secara eksplisit mengizinkan azp tidak hadir. Nilai azp yang hadir namun salah selalu ditolak.
4. JWT: memilih satu JWKS endpoint public HTTPS **atau** protected `local_key_ref` berisi nama parameter RSA public PEM. Opaque: menetapkan introspection endpoint public HTTPS. Endpoint lokal/private/redirect tidak didukung.
5. Bila endpoint memerlukan client secret, memasukkan **nama reference parameter protected** pada `credential_ref`, bukan secret di form profil. Tidak pernah memasukkan private key/token ke form source atau dokumen.
6. Memilih resolver. **Default** berarti exact issuer-subject binding; tidak dipilih otomatis. Membuat binding subject ke satu internal user aktif sesuai company. Fixed user hanya dari konfigurasi administrator; resolver method hanya allowlist. Tidak ada email/login fallback atau auto-binding.

Sumber: `models/trust_registry.py:165-384`; `models/trust_registry.py:420-442`; `models/helper.py:268-283`.

## Konfigurasi lama

Selector parameter `amr_resource.issuer` / `amr_resource.audience` adalah referensi key legacy, bukan URL literal atau konfigurasi trust aktif. Settings tidak lagi menampilkan selector itu sebagai cara mengaktifkan autentikasi. Freeze `web.base.url` tidak memilih issuer/audience. Jangan mengaktifkan checkbox sibling secara massal. `models/res_config_settings.py:1-55`; `views/res_config_settings_views.xml:1-172`

Administrator meminta migrasi eksplisit v1 sesuai [Developer guide](developer.md#6-settings-dan-migrasi-legacy-v1): inventory nonsecret, exact subject bindings, dry-run, backup dan restore rehearsal yang diotorisasi sebelum apply. Migrasi tidak otomatis, tidak menghapus konfigurasi lama, menolak konflik, dan mencatat revision digest. Email-only mapping tidak dikonversi otomatis.

## Alur dan penolakan

Session sah tetap didahulukan. Bila session tidak sah, bearer diperiksa sebelum params; bearer invalid tidak boleh diganti dengan params. Access token harus memenuhi profil terdaftar dan user eligible. ID Token, HS JWT, unknown/inactive issuer, audience/azp salah, expired token, unbound subject, user nonaktif/public/portal/superuser atau company tidak sesuai ditolak. Stored Python tidak dijalankan. `models/ir_http.py:66-76`; `models/helper.py:207-248`; `models/helper.py:254-260`

## Troubleshooting aman

- Unauthorized: minta administrator memeriksa status issuer/company, token class, audience/azp, expiry dan binding subject. Jangan mengirim token/raw claims/password/key/URL credential ke tiket/log.
- Unknown issuer: jangan menambahkan URL dari token secara otomatis. Pastikan registry exact sudah disetujui.
- Endpoint gagal: tidak ada retry/redirect otomatis; administrator memeriksa static endpoint/TLS dan kebijakan public network. Jangan mengaktifkan insecure HTTP/local bypass.
- Migrasi konflik: hentikan apply; bandingkan konfigurasi/mapping terkontrol dan backup. Jangan overwrite marker agar pemeriksaan idempotence terlewati.
- Minta bantuan dengan versi addon, kategori error dan langkah nonsecret. Runtime/ACL/route/rollback memerlukan verifikasi terpisah di lingkungan disposable yang diotorisasi.

## Batas versi

Source `13.0.1.0.0` menargetkan Odoo 13 / Python 3.7.9. Panduan ini tidak membuktikan instalasi, UAT, compatibility addon issuer/sibling, Odoo 20, rollout ataupun rollback di instance tertentu. `__manifest__.py:1-21`
