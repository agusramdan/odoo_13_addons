# Architecture — `amr_data_sync`

This is a static source map, not runtime evidence. The addon manifest declares Odoo/addon dependencies `base`, `mail`, `amr_resource`, and `amr_service_client`, plus ACL/view/cron/server-action data (`../__manifest__.py:11-29`). The remote-model transport is reached through dependency-provided `server_sync_id.create_remote_model`; its implementation and guarantees are outside the evidence cited here.

## Component map

```text
Remote Odoo/client (dependency boundary)
      │ pull list/read
      ▼
external.data.sync.strategy ──► external.data.sync ──► configured internal Odoo model
      ▲                              │                       ▲
      │ cron/manual                  └── relations/mapping ──┘
external.data.sync.cron

External caller ── POST /api/v1/data/update ──► controller ──► data.update.service
      machine auth (declared)                    sudo()          │
                                                               ├─ resolve authorized party/company/strategy
                                                               ├─ create external.data.update history
                                                               └─ dispatch accepted update
```

The diagram summarizes source paths; arrows do not imply verified successful transactions or effective runtime registration.

## Pull path

The strategy chooses its sync mode and either calls a configured method or lists remote records (`../models/data_sync_strategy.py:527-532`). For list sync it builds remote context/domain/field configuration, including optional company and last-update filtering (`../models/data_sync_strategy.py:540-583`), opens a remote model and passes each item to `external.data.sync.data_from_external` (`../models/data_sync_strategy.py:610-620`). Strategy input preparation filters non-writable/unknown/excluded fields, converts values, applies mappings, handles relations and may evaluate a configured script (`../models/data_sync_strategy.py:425-525`). The sync model persists external/internal identifiers, state, timestamp/payload/error fields, relations, and update history links (`../models/data_sync.py:18-84`).

Cron invokes due strategies, records last and next sync timestamps, and, when strategy permits external deletion, checks completed sync records in a batch of at most 1000 (`../models/data_sync_cron.py:43-96`). This does not prove a scheduler is active or that deletion semantics are safe.

## Push path and trust boundary

The controller declares `POST /api/v1/data/update`, HTTP type, machine auth, POST-only, and CSRF disabled; it parses JSON and calls the abstract service with `sudo()` (`../controllers/main.py:13-23`; parsing in `../controllers/mixin.py:18-23`). The service requires core fields, selects a server using `issuer`, and resolves the supplied company before selecting a model strategy. In this code path, if no external company mapping is resolved, no strategy is selected and the update is stored in the error state; a resolved company may fall back to a strategy without company restrictions (`../services/data_update.py:32-90`). It reads `azp` from JWT except when configured `not_secure`; `secure` rejects a missing issuer. Default source parameter is `amr_data_sync.date_update_security_option=secure_log` (`../services/data_update.py:25-29,92-123`). Accepted records are dispatched (`../services/data_update.py:112-123`).

**Security boundary:** authentication, issuer identity, payload fields, company mapping, and strategy selection feed privileged service work. The unconditional source-level `sudo()` makes validation/authorization review essential. Declared model ACLs are in `../security/ir.model.access.csv:1-30`; they do not establish effective access, record rules, tenant isolation, or safety of privileged controller operations. `safe_eval` receives environment/model and external data context (`../models/data_sync_strategy.py:501-510,663-686`). Stored payload/data/error fields exist (`../models/data_sync.py:63-75`); retention and redaction behavior is not established here.

## Persistence, failure, observability

The sync model has `draft`, `process`, `need_resolve`, `error`, and `done` states and fields for identifiers, timestamps, payload/data, errors, related records and update history (`../models/data_sync.py:18-84,30-34`). The controller logs exceptions and its generic error handler returns `str(ex)` as `error_description` (`../controllers/main.py:21-23`; `../controllers/mixin.py:65-81`). This is a potential information-disclosure surface; deployment-specific logging/response behavior must be reviewed and tested. No transaction, rollback, idempotency, retry, performance, or effective HTTP behavior is certified by this diagram.

## Validation boundary

The accepted analysis artifact `PRD-v3.md` and `UAT-v3.md` are proposals; UAT cases are NOT RUN. No install, Odoo registry, HTTP call, database, cron, security test, or external connection was performed for these docs. Therefore installation, route registry, runtime ACLs, user experience, data correctness, security, and external compatibility remain unverified. See [developer guide](developer.md) and [user guide](user.md) for practical limits.
