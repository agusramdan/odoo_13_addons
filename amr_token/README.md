# Modul `amr_token` — OIDC JWKS Key

> Addon Odoo 13 untuk menyimpan material kunci dan membentuk respons JWKS. Candidate ADDONS13-39 tidak mendeklarasikan OIDC Discovery pada `amr_token`; token dispatcher menolak semua grant. Ini bukan bukti route efektif, instalasi, keamanan, atau kesiapan produksi. Lihat [batas protokol ADDONS13-39](../amr_oidc/docs/addons13-39-protocol.md).

| Metadata                               | Nilai                                                                                                                                                                |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Versi manifest kandidat                | [`13.0.0.0.8`](__manifest__.py#L10)                                                                                                                                  |
| Dependensi Odoo                        | `base`, `base_setup`, `web`, `amr_resource` ([manifest](__manifest__.py#L11))                                                                                        |
| Python external dependency di manifest | `pyjwt` (distribusi PyPI; diimpor sebagai modul `jwt`) — deklarasi saja, bukan bukti paket tersedia ([manifest](__manifest__.py#L12-L14))                            |
| Dependency Python repository           | File root `requirement.txt`: PyJWT 2.8.0, cryptography 39.0.2, requests 2.21.0, Werkzeug 0.14.1 (target Odoo 13/Python 3.7.9/Linux); bukan bukti paket terpasang     |
| Source pin (provenance)                | [`addons_oidc` commit `6725f802acde636be0b25e2c140d15dccd37b0db`](https://github.com/agusramdan/addons_oidc/tree/6725f802acde636be0b25e2c140d15dccd37b0db/amr_token) |

## Untuk Developer

Panduan teknis dan batasan source: [Panduan Developer](docs/developer.md). Mencakup model, settings, route yang dideklarasikan, dependency, key-selection, dan batas runtime yang belum diverifikasi. Route OIDC Discovery pada kombinasi dengan `amr_oidc` mengembalikan 404; tidak ada RFC 8414 route.

## Untuk User

Panduan pengguna berbasis source: [Panduan User](docs/user.md). UI/hak akses efektif belum dikonfirmasi pada Odoo runtime; jangan gunakan petunjuk ini sebagai persetujuan penggunaan kunci nyata.

## Catatan Versi

- Source ditujukan untuk Odoo 13; kompatibilitas Odoo 20 tidak diklaim.
- Suite unit offline candidate dijalankan pada Python 3.7.9; detail UI, ACL efektif, dependency pada Odoo, dan perilaku server memerlukan verifikasi tersendiri.
- Dokumentasi ini tidak menyatakan security clearance, dukungan HSM, atau kesiapan produksi.
