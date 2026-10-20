# amr_service_client — Service Client

> Addon client HTTP/JSON-RPC Odoo 13 untuk berkomunikasi dengan layanan, termasuk `amr_resource`; bukan IdP atau resource server.

| | |
|---|---|
| Versi manifest | 13.0.0.1.0 |
| Depends | `base`, `web`, `base_setup`, `amr_resource` |
| Python eksternal (manifest) | `pyjwt` — deklarasi dependensi, bukan bukti paket tersedia |
| Status migrasi Odoo 20 | Tidak diklaim (di luar cakupan); kompatibilitas belum diverifikasi |
| Cakupan | Dokumentasi berbasis sumber untuk development/demo; runtime Odoo 13 belum diverifikasi; bukan untuk produksi |

## Untuk Developer

Panduan teknis lengkap berbasis sumber: [Panduan Developer](docs/developer.md). Ini tidak membuktikan instalasi, keamanan, atau perilaku runtime.

## Untuk User

Panduan pengguna berbasis deklarasi sumber: [Panduan User](docs/user.md). UI, ACL, registry, dan alur penggunaan belum diverifikasi pada runtime Odoo 13.

## Catatan Versi

- Sumber Odoo: 13.0; versi addon dari manifest: `13.0.0.1.0`.
- Migrasi/kompatibilitas Odoo 20 di luar cakupan dokumentasi ini dan tidak diklaim.
- Dokumentasi tidak mengotorisasi instalasi, request layanan nyata, replay, deployment, atau penggunaan produksi.
- Changelog fungsional: tidak ada perubahan kode; perubahan dokumentasi tercatat dalam riwayat repository.
