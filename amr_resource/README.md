# Resource Server (`amr_resource`)

Addon Odoo 13 untuk validasi OAuth access token dan pemilihan user melalui registry issuer terkontrol. Versi source `13.0.1.0.0`; target Python 3.7.9. Dependensi Odoo: `base`, `web`, `base_setup`. `__manifest__.py:1-21`

## Untuk Developer

[Developer guide](docs/developer.md): kontrak helper/consumer, profil JWT/opaque, transport tertutup, dependency pins, konfigurasi dan migrasi legacy eksplisit, test offline vs Odoo-native, serta batas keamanan.

## Untuk User

[User guide](docs/user.md): peran administrator, menu Resource Trust, audience dan subject binding, referensi key/credential, penolakan autentikasi dan troubleshooting aman.

## Standar OIDC/OAuth/JWT

Dokumen berikut menjadi rujukan desain untuk validasi OAuth access token. Rujukan standar bukan klaim bahwa seluruh spesifikasi telah diimplementasikan atau dibuktikan pada runtime.

- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) dan [OpenID Connect Discovery 1.0 — Second Errata](https://openid.net/specs/openid-connect-discovery-1_0-errata2.html), §§3, 4.1, 4.3: konteks OIDC serta metadata issuer dan `jwks_uri`. Discovery tidak menjadikan addon validator ID Token.
- [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414), §§2, 3.1, 3.3, 6: sumber metadata OAuth AS yang terpisah dari OIDC Discovery; tidak digunakan untuk menentukan OIDC metadata.
- [RFC 7662 — OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662), §§2.1–2.2, 4: kontrak introspection, bukan mekanisme discovery endpoint.
- [RFC 9068 — JWT Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068), §§2, 4: profil access token berbentuk JWT.
- [RFC 7519 — JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519#section-4.1.2), §4.1.2: `sub` adalah subject identifier, bukan jaminan alamat email.
- [RFC 7515 — JSON Web Signature](https://www.rfc-editor.org/rfc/rfc7515): format signature; [RFC 7517 — JSON Web Key](https://www.rfc-editor.org/rfc/rfc7517#section-4.7), khususnya §4.7; [RFC 7518 — JSON Web Algorithms](https://www.rfc-editor.org/rfc/rfc7518), §§3.3, 3.5, 6.3: sumber key dan algoritma RSA.
- [RFC 8725 — JSON Web Token Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725), §§2.1, 3.1, 3.8–3.12: panduan validasi JWT.
- [RFC 6749 — The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749#section-2.3.1), §2.3.1 dan Appendix B: client authentication Basic dan encoding form.

### Kebijakan lokal dan status implementasi

Standar tidak menetapkan urutan mapping, aturan fallback, ACL, atau cara memilih `res.users`; itu kebijakan produk. Candidate ini mendeklarasikan mapping terbatas dan algoritma RS256/PS256 policy (`models/trust_registry.py`), memeriksa konfigurasi NO_JWKS serta metadata RFC8414, dan mempertahankan bentuk publik empat-key `get_oidc_config`; helper internal membawa metode auth RFC8414 ke adapter agar `client_secret_basic`/kontrak referensi ditolak sebelum secret lookup (`models/helper.py`). Opaque dan JWT-shaped token hanya dapat memakai endpoint introspection yang terpilih; JWT memerlukan opt-in, prefilter `at+jwt`/claims, dan respons aktif-authoritative. Parent policy revision berubah saat konfigurasi parent/child berubah, terikat ke provenance validation, dan dipakai menolak hasil stale; perubahan active dicatat tanpa menyertakan secret/token. Mapping mengevaluasi urutan, menolak duplikasi kandidat, memverifikasi binding issuer/sub dan eligibility pada company request tanpa fallback. Batas ini baru diuji pada test boundaries sintetis: suite unit tidak memverifikasi ORM/ACL Odoo, transaksi/race multiworker, crypto pinned-vector PS256, metadata/provider atau UAT. Aktivasi operasional, rollback rehearsal dan kelengkapan historis/runtime policy revision tetap perlu bukti; candidate belum merupakan MVP yang dapat dinyatakan diterima. Metadata outage/invalid bukan deklarasi manual; binding mapping harus sudah ada. Akuisisi token provider bukan fungsi ResourceHelper; generasi token pada alur `amr_oidc` terpisah.


## Batas produk

Hanya access token dari issuer terdaftar; tidak ada email fallback, auto-binding, atau eksekusi stored Python. Registry/ACL/view dalam source bukan bukti instalasi atau runtime berhasil. Tidak mengklaim kompatibilitas Odoo 20, addon issuer/sibling, maupun deployment.
