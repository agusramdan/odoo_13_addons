# AMR Sentry operator guide

This optional addon reports service-client outcomes to Sentry when explicitly enabled. It depends on `amr_service_client`. Install the pinned Python dependencies `sentry-sdk==2.73.0` and `PyYAML==6.0.1` as part of your separately managed deployment process.

## Configuration

`AMR_SENTRY_CONFIG` selects the configuration file. If unset or empty, the path is `/etc/odoo/amr_sentry.yaml`. The file extension selects the parser: `.yaml` and `.yml` use YAML; `.json` uses JSON. The top-level `sentry` and `service_client` values must both be mappings. The `sentry` mapping is passed as keyword arguments to `sentry_sdk.init()` when reporting is enabled and configured. `service_client` accepts `enabled` and `mode`.

Use a secret-safe deployment mechanism for a real DSN. Restrict file ownership and permissions according to your environment; this is an operator recommendation, not a permission check enforced by the addon.

```yaml
sentry:
  dsn: "https://example.invalid/project"
  environment: development
  default_integrations: false
  auto_enabling_integrations: false
  integrations: []
  include_local_variables: false
  include_source_context: false
  send_default_pii: false
  max_request_body_size: "never"
  max_breadcrumbs: 0
  auto_session_tracking: false
  send_client_reports: false
  enable_metrics: false
  debug: false
service_client:
  enabled: false
  mode: none
```

The equivalent JSON shape is `{"sentry":{"dsn":"https://example.invalid/project","environment":"development","default_integrations":false,"auto_enabling_integrations":false,"integrations":[],"include_local_variables":false,"include_source_context":false,"send_default_pii":false,"max_request_body_size":"never","max_breadcrumbs":0,"auto_session_tracking":false,"send_client_reports":false,"enable_metrics":false,"debug":false},"service_client":{"enabled":false,"mode":"none"}}`.

For activation, replace the placeholder DSN and set `enabled: true` and a reportable mode; retain all 12 safety keys exactly as shown, including their types. Missing or unsafe safety values cause active configuration to be rejected before SDK initialization. Only `dsn`, these safety keys, and the optional string metadata `environment`, `release`, `server_name`, and `project_root` are allowed in `sentry`; other SDK options are rejected. Use synthetic, non-customer metadata. Omitted metadata may use SDK environment or automatic defaults; choose explicit, approved metadata for exclusive-process acceptance.

## Exclusive process eligibility

Enable this addon only in dedicated Odoo processes/workers where operators can exclude all other Sentry SDK initialization, integrations and event processors, and any ambient customer data in SDK global, isolation or current scopes. Inventory the loaded addons, startup hooks and instrumentation for every worker and database served by those processes; restrict the deployment so other tenants or databases cannot be reported without authority. Verify these conditions before activation and after deployment changes, and restart all affected workers for configuration changes. If exclusivity cannot be established or maintained, do not enable reporting in that process; a separately reviewed isolation design is needed.

The SDK is process-global: this addon does not enforce exclusivity, prevent another component from reinitializing the SDK or mutating its scopes, or isolate databases. Disabling this addon does not disable an SDK initialized by another component. Use explicit approved metadata and check for environment or automatic defaults as part of deployment eligibility; the example alone does not prove isolation.

## Reporting modes

- `all`: report successful outcomes and failures.
- `error`: report failures only.
- `selected`: report success or failure only for service clients with `sentry_opt_in` enabled.
- `none`: no reporting. This is the default mode; `enabled` also defaults to false.

A real DSN, `enabled: true`, a reportable mode, the complete valid safety profile, and a ready SDK are required for initialization. Configuration is loaded at import/process startup; restart all Odoo processes after changes. There is no hot reload or global Settings UI. Per-client opt-in remains relevant only for `selected` mode.

## Failure behavior and data handling

Configuration load, SDK import, SDK initialization, and reporting failures are fail-closed/best-effort: reporting is disabled or the service-client outcome is retained, with generic warnings. Do not rely on reporting for service operation or diagnostics.

The addon does not explicitly attach request/response bodies, headers, credentials, or customer data. Sentry SDK standard capture behavior still applies; no custom scrubber or broad privacy guarantee is provided. Review your Sentry project and SDK configuration for your own requirements.

For reportable failures, the original exception is sent to Sentry. Its message, chained cause, or path/URL may contain sensitive data, including tokens or customer data. The safety profile is not a guarantee that arbitrary exception text is clean. The Owner accepted the bounded D-EX residual exposure (Plane comment `ecaba4b8-afcb-47b4-924b-94d97e4a1b9b`); this is not a general waiver or a guarantee of strict zero-data handling. Exception-text UAT remains unverified, and this acceptance is not privacy, runtime, or security PASS. Do not treat this guide or the safety profile as such approval.

This guide documents source behavior only. It does not verify Odoo installation, registry startup, production use, migration or deletion of stale configuration values, or a deployment's secret handling.
