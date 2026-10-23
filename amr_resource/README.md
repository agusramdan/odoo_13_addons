# Resource Server (`amr_resource`)

Addon Odoo 13 untuk validasi OAuth access token dan pemilihan user melalui registry issuer terkontrol. Versi source `13.0.1.0.0`; target Python 3.7.9. Dependensi Odoo: `base`, `web`, `base_setup`. `__manifest__.py:1-21`

## Untuk Developer

[Developer guide](docs/developer.md): kontrak helper/consumer, profil JWT/opaque, transport tertutup, dependency pins, konfigurasi dan migrasi legacy eksplisit, test offline vs Odoo-native, serta batas keamanan.

## Untuk User

[User guide](docs/user.md): peran administrator, menu Resource Trust, audience dan subject binding, referensi key/credential, penolakan autentikasi dan troubleshooting aman.

## Batas produk

Hanya access token dari issuer terdaftar; tidak ada Discovery, email fallback, auto-binding, atau eksekusi stored Python. Registry/ACL/view dalam source bukan bukti instalasi atau runtime berhasil. Tidak mengklaim kompatibilitas Odoo 20, addon issuer/sibling, maupun deployment.
