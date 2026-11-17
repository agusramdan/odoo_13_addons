# Developer guide

## Module and dependencies

This is an Odoo 13 addon, version `13.0.3.0.3`, licensed AGPL-3 in its manifest. Declared dependencies are `base`, `mail`, `amr_resource`, and `amr_service_client`; declared data includes ACL, views, cron, and server-action XML (`../__manifest__.py:3-29`). The external client implementation belongs to dependencies; do not infer its protocol or guarantees from this addon alone.

Key code boundaries:

- `models/data_sync_strategy.py`: strategy configuration, mapping/input preparation, pull setup, extension callbacks.
- `models/data_sync.py`: external/internal record association, state, relation handling, record processing.
- `models/data_sync_cron.py`: scheduled pull and delete-check orchestration.
- `controllers/main.py` + `controllers/mixin.py`: HTTP push route, JSON parsing, response/error formatting.
- `services/data_update.py`: payload validation, authorized-party/strategy selection, persistence and dispatch.
- `security/ir.model.access.csv`: declared model-level ACLs.

These paths are source locations, not a stable public API promise.

## Push contract visible in source

The controller declares `POST /api/v1/data/update`, `type="http"`, `auth="machine"`, and `csrf=False`; it parses the request JSON and invokes `data.update.service` through `sudo()` (`../controllers/main.py:13-23`; payload parsing in `../controllers/mixin.py:18-23`). The service requires truthy `issuer`, `res_model`, `res_id`, `operation`, and `event_datetime` values (`../services/data_update.py:17-23,32-39`). In modes other than `not_secure`, it reads JWT `azp` and overwrites payload `issuer` when present; `secure` rejects missing issuer, while other cases may continue to store an error result (`../services/data_update.py:92-123`). It resolves `authorized_party`, external company and strategy and creates an `external.data.update` (`../services/data_update.py:32-90`); accepted records are dispatched (`:112-123`).

The source default is `secure_log` under parameter key `amr_data_sync.date_update_security_option` (`../services/data_update.py:25-29`). Do not treat this default or mode naming as a reviewed security policy. Validate status codes, authentication integration, payload schema, transaction boundaries, and effective response behavior in the target Odoo runtime before documenting them as guarantees.

## Pull and transformation path

`sync_from_application_server` selects method-call or list sync (`../models/data_sync_strategy.py:527-532`). List sync builds remote fields/context/domain, opens `server_sync_id.create_remote_model`, then calls the sync-record callback (`../models/data_sync_strategy.py:540-583,610-620`). Input preparation filters fields by write access and configured include/exclude/mapping settings, converts types, handles company and relation fields, applies mappings and optional `safe_eval`, then may invoke `prepare_input_dict` (`../models/data_sync_strategy.py:425-525`). `external.data.sync` records state and external/internal identifiers and tracks payload/error/timing and relation/history links (`../models/data_sync.py:18-84`).

The cron invokes due strategies, schedules the next run one hour later, and for delete-capable strategies checks a batch capped at 1000 records (`../models/data_sync_cron.py:43-96`). These are code paths; neither cron scheduling nor remote behavior is proven here.

## Extension and review cautions

The source has optional model callbacks such as `prepare_input_dict`, `internal_process_method`, and sync-done/archive hooks (`../models/data_sync_strategy.py:522-524,743-775`). Confirm the exact callable conventions and execution context from implementation and tests before relying on them. Script evaluation exposes Odoo environment/model/data context (`../models/data_sync_strategy.py:501-510,663-686`); treat strategy-edit permissions and script security as high risk requiring independent review.

ACL CSV grants `base.group_user` read/write/create on sync, company, relation, and update records but not unlink; several configuration models are read-only for that group, with broader manager permissions declared (`../security/ir.model.access.csv:1-30`). These declarations do not prove record-rule, controller, `sudo`, or multi-company safety.

## Development and verification

No test command, runner setup, environment bootstrap, or successful test result is established by the accepted PRD/UAT or this source inspection. The UAT defines Odoo 13 and Python 3.7.9 as proposed target context and marks scenarios NOT RUN. Before making runtime claims, use an authorized isolated Odoo 13 environment with disposable database and controlled external endpoint; record exact candidate revision, Python/Odoo/dependency versions, command, selector, test counts, exit code, and sanitized evidence. Keep mock-unit results distinct from HTTP/ORM/remote integration results. Do not run tests against production or infer installation success from static source.

Security review should explicitly cover machine-auth issuer/`azp`, `sudo()` boundaries, company/tenant isolation, input validation and bounds, logs/error payloads, stored `data_json`/`payload_json`/`error_info`, script evaluation, and credential handling. No claim that these controls are adequate has been verified.
