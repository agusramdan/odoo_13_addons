# ADDONS13-39 — Batas metadata dan grant pada candidate

**Status bukti:** uraian kontrak source pada candidate ADDONS13-39 berbasis T1 `agusramdan/odoo_13_addons@a2684e704304e947464b3eec7d8d2ef734ec0aef`. Tes unit terisolasi adalah bukti helper/controller fixture saja; bukan bukti registry Odoo, route efektif, HTTP runtime, interoperabilitas, atau kesiapan produksi. Pin commit candidate final dan hasil UAT dicatat pada evidence task terpisah.

## Kebijakan metadata per kombinasi modul

| Kombinasi | Source contract candidate | Batas bukti |
|---|---|---|
| A: `amr_token` saja | `ControllerToken` tidak mendeklarasikan `/.well-known/openid-configuration`. Tidak ada route RFC 8414 karena tidak ada response type OAuth lengkap yang terbukti. | Route efektif A dan respons router belum diuji pada registry Odoo. |
| B: `amr_token` + `amr_oidc` | `ControllerOIDC` mendeklarasikan `GET /.well-known/openid-configuration` dan mengembalikan HTTP 404. `amr_token` tetap tidak memiliki route Discovery. Tidak ada route RFC 8414. | Unit test memanggil handler lokal; tidak membuktikan pemilikan route efektif, tidak adanya route duplikat/fallback, atau respons HTTP di runtime. |

Metadata sukses tidak dipublikasikan: candidate tidak mengeluarkan response type OIDC, endpoint OIDC, klaim, atau grant list melalui well-known document. RFC 8414 memerlukan capability OAuth lengkap yang dibuktikan lebih dahulu; tidak ada positive flow atau builder/route pada Feature ini.

## Konsumen internal dan kompatibilitas

Di repositori yang sama, `amr_resource.get_oidc_config()` mengambil `/.well-known/openid-configuration` dari issuer dan dipakai oleh `generate_token()`, `introspect_token()`, serta `validate()` (`../../amr_resource/models/helper.py:40-44,60-73,82-103,130-136`). Jika konfigurasi issuer menunjuk ke instance ini, kontrak 404 akan membuat pemanggil tersebut gagal. Source consumer tidak diubah; issuer/configuration, caller di luar repo, cache, pemberitahuan, serta rencana migrasi belum diinventarisasi. Ini blocker release, bukan alasan untuk mengarang compatibility.

Helper publik `openid_configuration` dihapus. Helper private `_service_account_endpoint_defaults` hanya dipakai oleh `oidc.client.export_service_account` untuk menjaga field `issuer`, `authorization_endpoint`, dan `token_endpoint` pada ekspor lama; tiga nilai tersebut bukan Discovery document dan bukan bukti flow dapat digunakan. Ekspor service-account dan konsumennya belum menjadi release-approved.

## Dispatcher dan alur otorisasi

- `amr.token.helper.oidc_token()` menolak semua grant dengan `status=400`, `error=unsupported_grant_type`; tidak ada access token yang dihasilkan melalui dispatcher.
- Cabang lama password/custom (`challenge_approval`, `digital_signature`), client credentials, JWT bearer, dan refresh tidak didispatch. Method implementasi yang dipertahankan untuk meminimalkan perubahan diberi nama private `_do_*`; tidak ada klaim bahwa seluruh internal caller di luar repositori telah diinventarisasi.
- Source handler bodies untuk `/oidc/authorize`, `/oidc/auth`, `/oidc/authorize_continue`, dan `/oidc/login/submit` mengembalikan `400 unsupported_response_type` saat dipanggil; mereka tidak membuat authorization code atau token. Middleware/auth dan registry dapat mengubah HTTP outcome (misalnya `authorize_continue` dideklarasikan `auth='user'`); route efektif belum diuji. Authorization-code redemption dan ID-token issuance tetap tidak tersedia.
- RFC 8414 `grant_types_supported` maupun client-auth method tidak diiklankan. Konfigurasi UI/field seperti `private_key_jwt` bukan bukti metode tersebut bekerja.

## Scope dan gerbang tersisa

Implementasi ini tidak menambah flow, route OAuth metadata, atau capability baru. Offline unit tests tidak menguji Odoo registry/MRO, effective route owner, HTTP/cache header, consumer compatibility, atau data runtime. Integration/runtime UAT tetap **DEFERRED / NOT RUN**. Inventory consumer/cache eksternal, pemberitahuan, rollback dan disposition risiko OD-06/UAT-20 tetap diperlukan sebelum release; tidak ada residual-risk acceptance atau otorisasi produksi yang dinyatakan.

Referensi implementasi: [`amr_token` helper](../../amr_token/models/helper.py), [`amr_token` controller](../../amr_token/controllers/main.py), [`amr_oidc` helper](../models/helper.py), [`amr_oidc` controller](../controllers/main.py), dan unit tests pada kedua addon.
