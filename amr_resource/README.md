# Modul `amr_resource`

> Addon Odoo 13 yang berperan sebagai *Resource Server*: membantu validasi token, pemetaan identitas ke user Odoo, dan autentikasi request. Rincian perilaku, batasan, dan bukti ada di panduan terpisah di folder `docs/`.

| | |
|---|---|
| Versi manifest | `13.0.0.0.8` |
| Dependencies | `base`, `web`, `base_setup` |
| Status migrasi Odoo 20 | Belum diverifikasi / belum dimigrasikan |
| Status kandidat | DRAFT lokal; branch `ADDONS13-24`, belum di-commit |

## Untuk Developer

Dokumentasi teknis lengkap: [Panduan Developer](docs/developer.md). Termasuk arsitektur, model/field, API dan routes, konfigurasi, dependensi, error handling, batasan keamanan, serta status verifikasi.

## Untuk User

Panduan pengguna lengkap: [Panduan User](docs/user.md). Termasuk navigasi dan form yang dapat disimpulkan dari source, hak akses yang belum diverifikasi runtime, konfigurasi awal, alur request, dan FAQ.

## Catatan Versi

- Odoo sumber: 13.
- Status migrasi Odoo 20: belum diverifikasi / belum dimigrasikan.
- Unit test: **NOT RUN / tidak ada PASS terverifikasi**; satu percobaan QA berakhir tanpa summary runner. Tidak ada retry.
- Risiko keamanan: **PENDING/BLOCKED**; review dokumen bukan security clearance.
- Review independen atas isi dokumentasi serta layout folder `docs/` dan link relatif kandidat ini: **PASS terbatas**. Final acceptance Lead tetap terpisah; ini bukan test acceptance atau security clearance.
