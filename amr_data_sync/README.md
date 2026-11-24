# External Data Sync (`amr_data_sync`)

Odoo 13 addon for syncing records between this Odoo instance and configured external systems. This guide describes the checked source, not proof of installation or runtime behavior.

## Documentation

- [User guide](docs/user.md) — operator concepts, workflow, monitoring, and security cautions.
- [Developer guide](docs/developer.md) — module boundaries, extension points, and development/testing cautions.
- [Architecture](docs/architecture.md) — source-traced pull and push flows.

## Source-backed overview

The manifest declares addon version `13.0.3.0.3`, depends on `base`, `mail`, `amr_resource`, and `amr_service_client`, and loads access rules, views, cron data, and server-action data (`__manifest__.py:3-29`). The addon includes pull synchronization and an HTTP push endpoint. The endpoint is declared `POST /api/v1/data/update`, `type="http"`, `auth="machine"`, with CSRF disabled; its service call uses `sudo()` (`controllers/main.py:13-23`). Treat the elevated call and authentication/configuration behavior as security-sensitive and validate them in the deployed Odoo environment.

## Important limitations

No tests, installation, HTTP calls, database operations, cron execution, or external connections are evidenced by these documents. Static source inspection does not prove effective route registration, ACL/record-rule behavior, successful sync, installability, security, or performance. Do not put credentials or production data in configuration examples or reports. See the [architecture](docs/architecture.md) for explicit trust boundaries and open risks.
