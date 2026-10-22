# Modul `amr_oidc`

> Tugas: ADDONS13-37; repositori/lokasi: `agusramdan/odoo_13_addons/amr_oidc`; pin sumber upstream: `agusramdan/addons_oidc@6725f802acde636be0b25e2c140d15dccd37b0db`; snapshot kode yang didokumentasikan: `agusramdan/odoo_13_addons@6bd356e7386420e23b23d6f2874cb9c20944d003`; versi manifest: `13.0.1.0.0`.
> Tanggal inspeksi: 2026-10-22; status: telah ditinjau Lead setelah tinjauan independen; dokumentasi tetap DRAFT, belum dirilis/dipublikasikan.
> Lingkup: dokumentasi berbasis kode sumber saja, bukan bukti instalasi, runtime, keamanan efektif, atau deployment. Target proyek Python 3.7.9 dinyatakan oleh `AGENTS.md`; runtime belum diverifikasi. Odoo 13; tidak mengklaim migrasi atau kompatibilitas Odoo 20.

## Ringkasan

Addon ini memperluas helper token `amr_token`, mendeklarasikan lima model persisten dan satu wizard, beberapa rute HTTP, tampilan/menu serta ACL statis. Deklarasi tersebut tidak membuktikan alur OIDC end-to-end atau akses efektif. Rincian kode sumber dan batas bukti ada pada [panduan pengembang](docs/developer.md); orientasi pengguna dan batas operasional ada pada [panduan pengguna](docs/user.md).

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
- **Konsumen:** tidak ada pemanggil addon lain yang terverifikasi dalam graf yang diperiksa; pewarisan bukan bukti adanya pemanggil.
- **Metode/rute:** permukaan lokal dan jalur delegasi dirinci di panduan pengembang; bukan kontrak runtime/API teruji.
- **Dependensi:** addon `base`, `web`, `amr_token`; Python `pyjwt`, `cryptography` menurut manifest. Target Python proyek 3.7.9; runtime belum diverifikasi.
- **Konfigurasi:** parameter yang tampak pada kode sumber: `amr_token.expires_in`, `amr_token.secret`, `web.base.url`; jangan menyalin atau mengubah nilai produksi berdasar dokumen ini.
- **Galat:** hanya cabang kode sumber yang terlihat dijelaskan; perilaku runtime, percobaan ulang, dan idempotensi tidak ditetapkan.
- **OIDC/protokol:** penukaran authorization-code/token dan penerbitan ID-token tidak disediakan oleh addon/graf kode sumber dan dependensi yang ditinjau. Metadata Discovery bukan bukti implementasi. Kapabilitas lain berstatus `UNASSESSED / UNVERIFIED`.
- **Keamanan/batas:** ACL adalah deklarasi statis; penegakan, visibilitas menu, peran efektif dan isolasi data belum diverifikasi. Lihat kebijakan eksplisit di kedua panduan.
- **Pengguna/menu/peran, tanya jawab:** disediakan pada [panduan pengguna](docs/user.md).

## Catatan versi dan riwayat perubahan

- Versi Odoo sumber: 13; manifest `13.0.1.0.0`, lisensi `LGPL-3`; snapshot kode yang didokumentasikan `6bd356e7386420e23b23d6f2874cb9c20944d003`; pin asal sumber upstream `6725f802acde636be0b25e2c140d15dccd37b0db`.
- Status migrasi 20.0: belum; tidak ada migrasi atau kompatibilitas Odoo 20 yang diklaim.
- Status runtime/penerapan: belum diverifikasi dalam dokumentasi source ini.
- Changelog 2026-10-22 (ADDONS13-37): indeks/panduan ditinjau terhadap snapshot kode sumber, PRD-DRAFT dan UAT-DRAFT yang diterima; bukti dan batasan dicatat di panduan. Tinjauan independen: PASS (Editor dan Reviewer); tidak ada PR, rilis, atau publikasi yang diklaim.
