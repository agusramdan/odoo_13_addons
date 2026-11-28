# odoo-unit-test-mock

Portable skill and starter kit for Odoo 13 Community unit tests without PostgreSQL, a registry, or an Odoo server. Python 3.8+ and pytest are required; no Odoo package is needed. The examples use both `unittest` / `unittest.mock` and pytest.

## Install and run

Extract the ZIP. From the extracted `odoo13-unit-test-mock` directory:

```sh
python -m pip install -r requirements.txt
python scripts/run_tests.py
python scripts/run_tests.py -- examples/test_pure.py
```

The runner defaults to all examples, invokes pytest, and installs the database/network guard before pytest imports tests. A missing pytest or failed test produces a nonzero exit code. See [isolation](references/isolation.md) for scope and limitations. Run only trusted code: this guard is a testing aid, not a security sandbox.

### Codex CLI

Copy the extracted `odoo-unit-test` folder to `~/.codex/skills/odoo-unit-test` (or `$CODEX_HOME/skills/odoo-unit-test` if configured). Restart Codex and invoke `$odoo-unit-test` or select it with `/skills`. See [OpenAI skills documentation](https://developers.openai.com/codex/skills/).

### Hermes Agent

Copy the folder to `~/.hermes/skills/odoo-unit-test-mock`, or into the skills directory configured for your Hermes profile. Start a new session or refresh skills and ask Hermes to use `odoo-unit-test-mock`. Consult [Hermes skills documentation](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md) for profile-specific settings.

## Contents and limitations

`scripts/mock_odoo.py` supplies MockOdooEnv, MockModel, MockRecordset, MockFactory and a scoped Odoo import shim. Examples cover model, wizard, controller, cron, approval and API. `templates/` contains a starting point. These are intentionally small, fail-fast doubles, not Odoo: no database, computed fields, record rules, transactions, field descriptors, onchange, route dispatch or real ORM behavior. Validate those separately with Odoo integration tests. Adapt code imports and mock contracts to the addon being tested.

## License

GNU Lesser General Public License version 3.0 only (LGPL-3.0-only). See [LICENSE](LICENSE). Third-party dependencies retain their own licenses.

## Unit tests for each addon

Keep unit tests with their addon in `<addon>/tests/unit/`, with files named `test_*.py`. Run from any directory using the skill's runner:

```sh
python /path/to/odoo13-unit-test-mock/scripts/run_tests.py --addon /path/to/my_addon
```

The runner adds its own `scripts/` directory to the Python path, so tests can import `mock_odoo`. It sets the pytest root to the unit directory, restricts conftest discovery above it, and selects importlib mode. See [addon layout](references/addon-layout.md) for an example and collection limitations. The default command without `--addon` still runs the packaged examples.
