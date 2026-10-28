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
    return sentry, {"enabled": enabled, "mode": mode}
