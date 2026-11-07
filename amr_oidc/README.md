# Modul `amr_oidc`

> Ikhtisar source addon Odoo 13. Deklarasi source bukan bukti instalasi, registry, HTTP, ACL efektif, atau operasi runtime.

## Untuk Developer

### Arsitektur source

- `amr_oidc` memiliki implementasi provider di `models/token_helper.py`; registrasi model dapat ditelusuri dari `models/__init__.py`.
- Manifest provider mendeklarasikan dependensi addon `base`, `base_setup`, dan `web`; `amr_oidc` tidak bergantung pada `amr_token` atau `amr_resource`.
- `amr_token` dipertahankan sebagai adapter opsional satu arah ke provider. Adapter tidak memiliki implementasi token, route, atau ekstensi `res.users` duplikat.
- Endpoint token menolak grant dengan `unsupported_grant_type`; OIDC Discovery tetap tidak tersedia. Addon ini bukan implementasi OIDC penuh.
- Target kompatibilitas proyek: Odoo 13 / Python 3.8.20. Runtime Odoo tidak dibuktikan oleh dokumentasi source ini.

### Rujukan teknis

- [Manifest provider](__manifest__.py)
- Implementasi source berada di `models/`, `controllers/`, dan `views/`. Dokumen lama di `docs/` mungkin merujuk snapshot sebelumnya; gunakan source saat ini untuk detail implementasi.

## Untuk User

Tidak ada prosedur operasional instance yang dibuktikan oleh source ini. `docs/user.md` adalah panduan source historis, bukan instruksi untuk instalasi atau pengaturan instance aktif. Gunakan runbook administrator yang disetujui sebelum mengubah konfigurasi, ACL, key, atau data produksi.

## Batas

Dokumen ini tidak menyatakan hasil Odoo registry/MRO, akses efektif, route dispatcher, database, kriptografi runtime, atau deployment. `amr_token` tetap tersedia sebagai adapter opsional; tidak ada prosedur migrasi database yang ditetapkan di sini.
