# Sentry test entrypoints

## Offline unit suite (required skill runner)

Use the existing `odoo13-unit-test-mock` skill at `$HOME/.hermes/skills/odoo13-unit-test-mock` on this host, or set `SKILL` to the corresponding installed skill directory in another environment. The skill is not distributed in this repository. It identifies itself as LGPL-3.0-only: review its LICENSE before redistributing it. The tested skill scripts have these SHA-256 hashes (verify with `sha256sum`):

```text
d956ab0e7aa15d89875b2e0465650e35757736c5714ddb355d799224dddfc164  scripts/isolation.py
8882fc7b8c61bb75bebfa7afb1b46cf226b28ab88abb750fbdc8bfb200e0e5e2  scripts/mock_odoo.py
c80dc7999ff5b532274e9ca566e2de2a59fbfda63444dcaa0958a531ac86bd86  scripts/run_tests.py
```

From the repository root, with Python 3.7.3, the existing addon test dependencies, and pytest 7.4.4 plus typing_extensions 4.7.1 installed in a **test-only** environment:

```sh
SKILL="$HOME/.hermes/skills/odoo13-unit-test-mock"
PYTHONPATH="$PWD/tests/addons13_27:$PWD/amr_sentry/tests:$PWD${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -B "$SKILL/scripts/run_tests.py" --addon "$PWD/amr_sentry"
```

The runner adds its `scripts` directory to the import path, installs its isolation guards and selects `tests/unit`. The upstream skill README specifies Python 3.8+; Python 3.7.3 with the versions above was exercised for this addon, not a general upstream compatibility claim. Use a network-disabled container for the test run; the guards are not a security sandbox. For a container, mount the repository and persistent skill directory read-only, set the equivalent container `PYTHONPATH`, and invoke the same runner with `--addon` using container paths. Do not install these dependencies into production. A direct unittest discovery without the skill helper now fails rather than silently skipping the skill case. Mocked offline tests do not prove ORM, database, or runtime behavior.

The canonical addon-owned test bodies live in `tests/unit` and load shared case helpers directly from that directory, without depending on legacy adapters; legacy `test_U11_sentry_*` modules and the corresponding `ac_tests/*_cases.py` modules are compatibility adapters to those bodies. Use the offline legacy selector `python3 -B -m unittest discover -s tests/addons13_27 -p 'test_U11_sentry_*.py' -v`; its compatibility shim enumerates top-level addon-owned legacy files without importing the Odoo integration package. Generic recursive discovery rooted at `amr_sentry/tests` is not an offline entrypoint: it imports integration and requires Odoo. AC selectors remain supported. Do not discover the unit directory and its legacy files together: they expose the same cases. `ac_tests` remains outside Odoo native discovery and uses its strict individual entrypoints; see its README. The integration test is under `tests/integration`; the former `integration_tests.test_service_client_hook` import is retained as a compatibility alias.

## Verification (uncommitted ADDONS13-68 worktree, HEAD 60bf75d)

In `odoo13-runtime:local`, network disabled and source read-only, legacy and unit discovery each ran 49 passing tests with identical 49 distinct test IDs. The external legacy selector ran 53 passing tests including the four core cases. AC component selectors 01–04 and 06–11 passed; AC05 and AC12 returned NOT RUN (exit 2). Strict-runner controls passed.

Odoo native discovery found exactly the integration test module; importing the addon with test mode off imported no addon test modules. The compatibility class was identical and the unit package remained unloaded. A disposable PostgreSQL 13 database was verified absent before a fresh Odoo installation on an internal network. With `/amr_sentry` test tags the hook test ran once, Odoo exited 0, and both addon modules read back as installed. The database, both containers and network were confirmed absent during cleanup. Logs: `/home/ubuntu/.hermes/profiles/lead/cache/scratch/ac68_reorg/` (scratch, subject to pruning).

The coordinated layout now imports the integration package and re-exports its actual test module because Odoo 13 scans `test_*` module attributes on `tests`, not nested packages. The unit directory is not a package. With Python 3.7.3 and pytest 7.4.4 in the network-disabled runtime, the skill unit runner passed 50 tests; the legacy selector passed 53 distinct cases, and the layout guard passed four checks including identity equality against explicitly enumerated owned files. Real Odoo discovery returned exactly `odoo.addons.amr_sentry.tests.integration.test_service_client_hook`; mode-off imported no addon tests, and the legacy import resolved to the same class. On a fresh disposable PostgreSQL 13 database, the integration skill runner exited 0 and logged the hook method exactly once. Both modules were installed, and database, containers, and internal network were verified absent after cleanup. Full native log: `/home/ubuntu/.hermes/profiles/lead/cache/scratch/sentry68-native-351709.log` (scratch, subject to pruning). The log also contains docutils markup warnings from addon descriptions. The earlier native invocation before re-exporting the module exited 0 but ran no hook tests; it is not passing test evidence.
