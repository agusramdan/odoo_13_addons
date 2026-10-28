# amr_sentry — optional Sentry reporting

> Optional Odoo 13 addon for reporting service-client outcomes. Documentation is based on committed source; Odoo installation, registry loading, and production operation are not verified.

| | |
|---|---|
| Depends | `amr_service_client` |
| Python package pins | `sentry-sdk==2.73.0`, `PyYAML==6.0.1` |
| Default | Reporting disabled (`enabled: false`, `mode: none`) |

## Operator setup

See the [operator guide](docs/operator.md) for configuration, policy modes, restart behavior, and deployment precautions. A real Sentry DSN is a secret: deploy it through a secret-safe configuration process and restrict the configuration file's ownership and permissions. The addon does not enforce file permissions.

The addon reads configuration at process startup. Restart Odoo after changing it. It does not add a global Settings UI; selected reporting uses the existing per-client `sentry_opt_in` flag.

This documentation does not claim hot reload, successful installation/registry loading, migration of old configuration values, or production readiness. Sentry SDK capture follows its standard behavior; the addon does not attach request/response bodies, headers, credentials, or customer data explicitly and does not provide a custom scrubber or broader privacy guarantee.
