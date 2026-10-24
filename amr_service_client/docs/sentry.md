# Sentry reporting

Global mode is configured in **Settings → Service Client Sentry**:

- **All**: report success and failure outcomes for `service.client` calls and `service.client.log` sends.
- **Error**: report failures only (request exceptions and HTTP error statuses).
- **Selected**: report failures only for `service.client` records with **Report errors to Sentry** enabled.
- **None**: disable reporting (default).

Reporting is best-effort and never changes request results or exception propagation. Events include only record type/state and Odoo record identifiers plus exception class; request URLs, headers/tokens, params, payloads, response bodies, contexts, and traceback text are not sent. Reporting errors are suppressed.

Deployment must install `sentry-sdk` in the Odoo Python environment and initialize/configure the SDK and DSN externally (for example in the deployment's Odoo startup hook). This addon deliberately does not initialize Sentry or store a DSN. If the SDK is unavailable, reporting is silently disabled. An operation through `service.client` and its separately persisted `service.client.log` are separate events, because All covers both model types.
