# odoo_13_addons

Project `addons_odoo_13` is for development of Odoo 13 addons. It does not have a production server.

## Deployment boundary

- The only deployment target for this project is the Odoo 13 demo server: <https://odoo13.agusramdan.web.id>.
- This project must not be treated as a production deployment or release. A Git commit/push is not deployment approval or evidence of a successful deployment.

## Addon documentation

- [amr_resource](amr_resource/README.md) — Resource Server addon; see its linked Developer and User guides.

## Indeks addon

Target dokumentasi ini adalah Odoo 13 untuk development/demo; migrasi ke Odoo 20 berada di luar cakupan dan kompatibilitas Odoo 20 tidak diklaim.

| Addon / peran | Versi manifest | Depends | Python eksternal (manifest) | Status penggunaan |
|---|---|---|---|---|
| amr_service_client — client HTTP/JSON-RPC | 13.0.0.1.0 | base, web, base_setup, amr_resource | pyjwt | Development/demo-only; bukan produksi |
| [amr_resource](amr_resource/README.md) — Resource Server | 13.0.0.0.8 | base, web, base_setup | Tidak dideklarasikan | Development/demo-only; bukan produksi |

Sumber deklarasi: `amr_service_client/__manifest__.py:6`, `amr_service_client/__manifest__.py:7`, `amr_service_client/__manifest__.py:9`, `amr_resource/__manifest__.py:9`, `amr_resource/__manifest__.py:10`. Versi dan dependency manifest bukan bukti instalasi, keamanan atau kompatibilitas runtime.

## Untuk Developer

- [Panduan teknis Service Client](docs/developer.md) — client HTTP/JSON-RPC Odoo 13; dokumentasi berbasis sumber, bukan bukti runtime.

## Untuk User

- [Panduan pengguna Service Client](docs/user.md) — menu, konfigurasi, wizard dan log berdasarkan sumber; belum diverifikasi pada runtime Odoo 13.

Dokumentasi ini berbasis sumber saja, bukan klaim keamanan atau kompatibilitas runtime. Panduan tidak mengotorisasi instalasi, request layanan, replay, deployment atau publikasi.
