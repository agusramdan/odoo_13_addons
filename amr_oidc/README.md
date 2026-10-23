# Modul `amr_oidc`

> Riwayat dokumentasi: ADDONS13-37 pada snapshot `agusramdan/odoo_13_addons@6bd356e7386420e23b23d6f2874cb9c20944d003`; target candidate ADDONS13-39 berbasis T1 `a2684e704304e947464b3eec7d8d2ef734ec0aef`. Perubahan saat ini dijelaskan pada [catatan protokol ADDONS13-39](docs/addons13-39-protocol.md). Manifest versi `13.0.1.0.0`; dokumentasi belum dirilis/dipublikasikan.
> Riwayat inspeksi ADDONS13-37: 2026-10-22; dokumentasi tetap DRAFT, belum dirilis/dipublikasikan.
> Candidate ADDONS13-39 telah menjalani unit tests offline pada Python 3.7.9; ini bukan bukti instalasi/runtime Odoo, keamanan efektif, atau deployment. Odoo 13; tidak mengklaim migrasi atau kompatibilitas Odoo 20.

## Ringkasan

Addon ini memperluas helper token `amr_token`, mendeklarasikan lima model persisten dan satu wizard, beberapa rute HTTP, tampilan/menu serta ACL statis. Deklarasi tersebut tidak membuktikan alur OIDC end-to-end atau akses efektif. Candidate ADDONS13-39 menolak semua grant dan mengembalikan 404 pada handler OIDC Discovery; RFC 8414 tidak dipublikasikan. Lihat [catatan protokol ADDONS13-39](docs/addons13-39-protocol.md), [panduan pengembang](docs/developer.md), dan [panduan pengguna](docs/user.md).

## Untuk Pengembang

README ini adalah indeks; panduan lengkap ada di [panduan pengembang](docs/developer.md).

- [Arsitektur dan dependensi](docs/developer.md#arsitektur)
- [Model, field, relasi dan ACL](docs/developer.md#model-field-dan-relasi)
- [Konsumen terverifikasi](docs/developer.md#konsumen-terverifikasi) dan [metode yang tampak pada kode](docs/developer.md#metode-yang-tampak-pada-kode-sumber)
- [Konfigurasi dan galat](docs/developer.md#konfigurasi)
- [Keamanan, batas protokol, Odoo 13 vs 20, dan peta kode sumber/hash](docs/developer.md#keamanan-dan-batas)

## Untuk Pengguna

README ini adalah indeks; panduan lengkap ada di [panduan pengguna](docs/user.md).

- [Tujuan, prasyarat, menu dan role](docs/user.md#tujuan-sasaran-pembaca-dan-prasyarat)
- [Akses dan kebijakan](docs/user.md#akses-dan-kebijakan); [tanya jawab dan eskalasi](docs/user.md#tanya-jawab-dan-eskalasi)

### Ringkasan kontrak

- **Arsitektur:** graf impor addon memuat pengendali, model, dan wizard; helper mewarisi `amr.token.helper` dari `amr_token`.
- **Model:** `oidc.client`, `oidc.authorization.code`, `oidc.client.key`, `oidc.jwt.replay`, `oidc.refresh.token`; detail atribut di panduan pengembang.
- **Konsumen:** `amr_resource.get_oidc_config()` mengambil Discovery dari issuer dan digunakan oleh `generate_token()`, `introspect_token()`, dan `validate()`; issuer lokal dapat terdampak oleh route 404. Consumer/cache eksternal belum diinventarisasi.
- **Metode/rute:** permukaan lokal dan jalur delegasi dirinci di panduan pengembang; bukan kontrak runtime/API teruji.
- **Dependensi:** addon `base`, `web`, `amr_token`; Python `pyjwt`, `cryptography` menurut manifest. Target Python proyek 3.7.9; unit test dijalankan pada interpreter 3.7.9 dalam container, tetapi Odoo runtime belum diuji.
- **Konfigurasi:** parameter yang tampak pada kode sumber: `amr_token.expires_in`, `amr_token.secret`, `web.base.url`; jangan menyalin atau mengubah nilai produksi berdasar dokumen ini.
- **Galat:** hanya cabang kode sumber yang terlihat dijelaskan; perilaku runtime, percobaan ulang, dan idempotensi tidak ditetapkan.
- **OIDC/protokol:** candidate fail-closed (`400 unsupported_response_type`/`unsupported_grant_type`, Discovery 404, tanpa RFC 8414 route); token exchange dan ID-token issuance tetap tidak tersedia. UAT runtime/consumer compatibility deferred.
- **Keamanan/batas:** ACL adalah deklarasi statis; penegakan, visibilitas menu, peran efektif dan isolasi data belum diverifikasi. Lihat kebijakan eksplisit di kedua panduan.
- **Pengguna/menu/peran, tanya jawab:** disediakan pada [panduan pengguna](docs/user.md).

## Catatan versi dan riwayat perubahan

- Versi Odoo sumber: 13; manifest `13.0.1.0.0`, lisensi `LGPL-3`; snapshot ADDONS13-37 `6bd356e7386420e23b23d6f2874cb9c20944d003` adalah riwayat dokumentasi; candidate ADDONS13-39 berbasis T1 `a2684e704304e947464b3eec7d8d2ef734ec0aef`.
- Status migrasi 20.0: belum; tidak ada migrasi atau kompatibilitas Odoo 20 yang diklaim.
- Status bukti: suite unit offline pada Python 3.7.9 dijalankan; runtime Odoo, deployment, dan kesiapan produksi belum diverifikasi.
- Changelog 2026-10-22 (ADDONS13-37): indeks/panduan ditinjau terhadap snapshot kode sumber, PRD-DRAFT dan UAT-DRAFT yang diterima; bukti dan batasan dicatat di panduan. Tinjauan independen: PASS (Editor dan Reviewer); tidak ada PR, rilis, atau publikasi yang diklaim.
