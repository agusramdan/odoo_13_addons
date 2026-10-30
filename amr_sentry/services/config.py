import json
import os

import yaml


DEFAULT_CONFIG_PATH = "/etc/odoo/amr_sentry.yaml"


class SentryConfigError(Exception):
    """Safe error indicating that Sentry configuration could not be loaded."""


def load_config():
    path = os.environ.get("AMR_SENTRY_CONFIG") or DEFAULT_CONFIG_PATH
    extension = os.path.splitext(path)[1].lower()
    try:
        with open(path, "r") as stream:
            if extension in (".yaml", ".yml"):
                data = yaml.safe_load(stream)
            elif extension == ".json":
                data = json.load(stream)
            else:
                raise SentryConfigError("unsupported configuration extension")
    except SentryConfigError:
        raise
    except Exception:
        raise SentryConfigError("configuration could not be loaded")
    if not isinstance(data, dict):
        raise SentryConfigError("configuration must be a mapping")
    sentry = data.get("sentry")
    policy = data.get("service_client")
    if not isinstance(sentry, dict) or not isinstance(policy, dict):
        raise SentryConfigError("required configuration mappings are invalid")
    allowed = {"enabled", "mode"}
    if set(policy) - allowed:
        raise SentryConfigError("service_client policy contains unknown keys")
    enabled = policy.get("enabled", False)
    mode = policy.get("mode", "none")
    if not isinstance(enabled, bool) or mode not in ("all", "error", "selected", "none"):
        raise SentryConfigError("service_client policy is invalid")
    required = {
        "default_integrations", "auto_enabling_integrations", "integrations",
        "include_local_variables", "include_source_context", "send_default_pii",
        "max_request_body_size", "max_breadcrumbs", "auto_session_tracking",
        "send_client_reports", "enable_metrics", "debug",
    }
    if set(sentry) - (required | {"dsn", "environment", "release", "server_name", "project_root"}):
        raise SentryConfigError("sentry contains unknown keys")
    dsn = sentry.get("dsn")
    if dsn is not None and not isinstance(dsn, str):
        raise SentryConfigError("sentry dsn is invalid")
    for key in ("environment", "release", "server_name", "project_root"):
        if key in sentry and not isinstance(sentry[key], str):
            raise SentryConfigError("sentry metadata is invalid")
    expected = dict.fromkeys(required, False)
    expected.update(integrations=[], max_request_body_size="never", max_breadcrumbs=0)
    for key, value in sentry.items():
        if key in expected and (type(value) is not type(expected[key]) or value != expected[key]):
            raise SentryConfigError("sentry safety profile is invalid")
    if enabled and mode != "none" and sentry.get("dsn") and required - set(sentry):
        raise SentryConfigError("sentry safety profile is incomplete")
    return sentry, {"enabled": enabled, "mode": mode}
