# User guide

## Scope and prerequisites

`amr_data_sync` connects configured external-system records to Odoo models. Its manifest depends on `base`, `mail`, `amr_resource`, and `amr_service_client` and loads its views, ACL, cron, and server-action data (`../__manifest__.py:11-28`). Confirm those dependencies and the organization's Odoo 13 configuration with the administrator before use. This guide cannot establish that a particular deployment is installed or working.

## Configuration concepts

The source provides configuration models/views for server connections, strategies, company mapping, field mapping, related records, lookup/exclusion, update history, and cron scheduling (manifest `../__manifest__.py:12-28`; view files are listed there). Configure these concepts only through the UI available in your deployed instance and your local operational procedure; exact menu paths, field requirements, credentials, and safe values are not established here. A strategy links an external model to an internal model and can define included/excluded fields, mappings, relation handling, company scope, and optional script (`../models/data_sync_strategy.py:425-525`). Have an administrator review the configuration before enabling synchronization.

## Pull synchronization (source flow)

A strategy can build a remote list configuration from context, domain, company mapping, last-update filtering, and selected fields (`../models/data_sync_strategy.py:540-583`). The list client is opened using the configured server and each returned item is handed to `external.data.sync.data_from_external` (`../models/data_sync_strategy.py:610-620`). The sync record stores state, external/internal identifiers, company, timestamps, payload/history-related data, and related-record links (`../models/data_sync.py:18-84`). Mapping and relation processing are handled during input preparation (`../models/data_sync_strategy.py:425-525`). Exact results depend on live configuration and target model behavior.

A cron model invokes due strategies, records last/next schedule timestamps, and for delete-capable strategies inspects up to 1000 completed sync records per cycle (`../models/data_sync_cron.py:43-96`). The code schedules the next run one hour later in this path; this is source behavior, not a guarantee of wall-clock execution or delivery latency. Use manual actions only where your deployment's access policy permits.

## Push synchronization (source flow)

The declared route accepts `POST /api/v1/data/update` with machine authentication (`../controllers/main.py:13-20`). The service requires `issuer`, `res_model`, `res_id`, `operation`, and `event_datetime`, then selects an authorized server and strategy (`../services/data_update.py:32-90`). Unless token mode is `not_secure`, it reads `azp` from the JWT payload; `secure` rejects a missing issuer, while the default parameter value in source is `secure_log` (`../services/data_update.py:25-29,92-123`). The parameter key is spelled `amr_data_sync.date_update_security_option`. These source defaults/modes are not a security recommendation: obtain an approved security configuration and verify actual behavior with the system owner. Do not trust caller-supplied company/model/record values without reviewing authorization boundaries.

## Monitoring and troubleshooting

Inspect sync and update records/history using the interface and access rights configured by your administrator. Sync state definitions include `draft`, `process`, `need_resolve`, `error`, and `done` (`../models/data_sync.py:30-34`). Treat `need_resolve` as requiring authorized review; do not blindly retry or edit records. A failed push may be stored as an update record with an error state (`../services/data_update.py:76-90`). Error responses and logs can contain exception details: the route logs exceptions and the generic handler returns `str(ex)` in its response (`../controllers/main.py:21-23`; `../controllers/mixin.py:65-81`). Redact sensitive data when reporting incidents and restrict access to logs/history.

## Security and operational limits

- The controller calls the service with `sudo()`; elevated access is explicit in source (`../controllers/main.py:18-20`). ACL declarations do not alone establish effective security or multi-company isolation (`../security/ir.model.access.csv:1-30`).
- Strategy script evaluation is present in source (`../models/data_sync_strategy.py:501-510,663-686`). Only trusted administrators should be allowed to configure scripts; security properties have not been validated here.
- Payload size/shape limits, idempotency contract, retry guarantees, retention/redaction policy, and production-ready security behavior are not established by static inspection.
- Never use production credentials or data in troubleshooting evidence. No runtime/UAT execution is claimed by this guide.
