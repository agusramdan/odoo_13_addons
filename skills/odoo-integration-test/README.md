# odoo-integration-test

Skill for Odoo 13 Community integration tests. Unlike the companion `odoo13-unit-test-mock`, these tests use real Odoo and PostgreSQL; no mock registry is used. Tests belong in `<addon>/tests/integration/` and are discovered through Odoo's test imports. Scripts use Python 3.8+; actual Odoo dependencies and PostgreSQL must be set up separately.

## Install skill

Copy this folder to `~/.codex/skills/odoo-integration-test` (or `$CODEX_HOME/skills/odoo-integration-test`) for Codex CLI, or to `~/.hermes/skills/odoo-integration-test` for Hermes Agent. Use the skills directory configured for your profile if different. Start or refresh the agent session and invoke the skill by name.

## Run a project's integration tests

Prepare a **dedicated disposable test database** and test-only configuration and services. Confirm the database identity independently. The runner updates or installs the addon and its dependencies; it does not create, reset, or drop the database. Run in the environment containing Odoo 13 and its Python dependencies:

```sh
python /path/to/odoo-integration-test/scripts/run_integration.py \
  --odoo-bin /path/to/odoo-bin --database my_disposable_test_db \
  --addon my_addon --mode update --ack-test-db \
  -- --config /path/to/test-odoo.conf --addons-path /path/to/odoo/addons,/path/to/custom/addons
```

Use `--mode install` for a fresh database where the addon has never been installed. The runner uses `--test-tags /my_addon`, which selects all tests for that addon, not only tests in `tests/integration`. Review the log for discovery, counts and failures; exit code alone cannot prove tests ran. `--dry-run` prints the command without executing it. See [running](references/running.md) and [layout](references/layout.md).

## Examples and validation

`examples/demo_integration` is a real installable sample addon with ORM and wizard tests. It needs an Odoo 13 environment and disposable PostgreSQL database to execute. Runner unit tests under `tests/` use no Odoo or database: `python -m unittest discover -s tests -v`. They validate command construction and safety checks, not Odoo integration behavior. `templates/` provides starting files.

[Odoo 13 test documentation](https://www.odoo.com/documentation/13.0/developer/reference/addons/testing.html). License: LGPL-3.0-only; see LICENSE.
