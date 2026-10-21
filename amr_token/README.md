# Modul `amr_token` — OIDC JWKS Key

> Addon Odoo 13 untuk menyimpan material kunci OIDC dan membentuk respons JWKS. Dokumentasi membedakan provenance upstream dari deklarasi kandidat; bukan bukti instalasi, UI, kompatibilitas runtime, keamanan, atau kesiapan produksi.

| Metadata                               | Nilai                                                                                                                                                                |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Versi manifest kandidat                | [`13.0.0.0.8`](__manifest__.py#L10)                                                                                                                                  |
| Dependensi Odoo                        | `base`, `base_setup`, `web`, `amr_resource` ([manifest](__manifest__.py#L11))                                                                                        |
| Python external dependency di manifest | `pyjwt` (distribusi PyPI; diimpor sebagai modul `jwt`) — deklarasi saja, bukan bukti paket tersedia ([manifest](__manifest__.py#L12-L14))                            |
| Dependency Python repository           | File root `requirement.txt`: PyJWT 2.8.0, cryptography 39.0.2, requests 2.21.0, Werkzeug 0.14.1 (target Odoo 13/Python 3.7.9/Linux); bukan bukti paket terpasang     |
| Source pin (provenance)                | [`addons_oidc` commit `6725f802acde636be0b25e2c140d15dccd37b0db`](https://github.com/agusramdan/addons_oidc/tree/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token) |

## Untuk Developer

Panduan teknis dan batasan source: [Panduan Developer](docs/developer.md). Mencakup model, settings, semua route yang dideklarasikan, dependency, key-selection, dan batas runtime yang belum diverifikasi.

## Untuk User

Panduan pengguna berbasis source: [Panduan User](docs/user.md). UI/hak akses efektif belum dikonfirmasi pada Odoo runtime; jangan gunakan petunjuk ini sebagai persetujuan penggunaan kunci nyata.

## Catatan Versi

- Source ditujukan untuk Odoo 13; kompatibilitas Odoo 20 tidak diklaim.
- Detail UI, ACL efektif, dependency terpasang, dan perilaku server memerlukan verifikasi tersendiri.
- Dokumentasi ini tidak menyatakan security clearance, dukungan HSM, atau kesiapan produksi.
