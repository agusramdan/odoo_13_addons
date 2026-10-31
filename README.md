# Odoo 13 Addons

Project `addons_odoo_13` is for development of Odoo 13 Addons. It does not have a production server.

## Deployment boundary

- The only deployment target for this project is the Odoo 13 demo server: <https://odoo13.agusramdan.web.id>.
- This project must not be treated as a production deployment or release. A Git commit/push is not deployment approval or evidence of a successful deployment.

## Addon documentation

- [amr_service_client](amr_service_client/README.md) — Client HTTP/JSON-RPC; lihat indeks dan panduan developer/user di dalam addon.
- [amr_sentry](amr_sentry/README.md) — optional Sentry reporting for service-client outcomes.
- [amr_resource](amr_resource/README.md) — Resource Server addon; see its linked Developer and User guides.

## Indeks addon

Target dokumentasi ini adalah Odoo 13 untuk development/demo; migrasi ke Odoo 20 berada di luar cakupan dan kompatibilitas Odoo 20 tidak diklaim.

| Addon / peran                                                             | Versi manifest | Depends | Python eksternal (manifest) | Status penggunaan |
|---------------------------------------------------------------------------|---|---|---|---|
| [amr_service_client](amr_service_client/README.md) — Client HTTP/JSON-RPC | 13.0.0.1.0 | base, web, base_setup, amr_resource | pyjwt | Development/demo-only; bukan produksi |
| [amr_resource](amr_resource/README.md) — Resource Server                  | 13.0.0.0.8 | base, web, base_setup | Tidak dideklarasikan | Development/demo-only; bukan produksi |
| [amr_sentry](amr_sentry/README.md)                                        | 13.0.1.0.0 | amr_service_client | sentry_sdk, yaml | Development/demo-only; not production |
