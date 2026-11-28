# Per-addon test layout

```text
my_addon/
  __init__.py
  models/
  tests/
    __init__.py             # from . import integration
    integration/
      __init__.py           # imports native Odoo test modules
      test_model.py         # TransactionCase/SavepointCase/HttpCase
    unit/
      test_model.py         # pure Python or mocked, offline
      test_wizard.py
```

Before moving a legacy test tree, classify each module: real Odoo cases belong in `integration/` and must be imported through both package initializers; standalone `unittest` or mocked tests belong in `unit/` and stay outside those imports. After moving files, update relative-import depth and every path derived from `__file__` or `os.path`; run the suite because stale roots can pass syntax checks while reading the wrong directory. For structural registration tests, parse the initializer chain, assert its registered module set is nonempty, and verify every registered module exists instead of hard-coding a test name in the root initializer.

Create `tests/unit/` in each addon being tested. Keep unit test files independent of Odoo's `tests/__init__.py` and do not add imports there. Do not create `tests/unit/__init__.py`: this avoids pytest treating the unit directory as an addon package, which may trigger the addon's Odoo-dependent initializers. If an existing unit directory is already a Python package, inspect its import chain and choose an appropriate isolated collection strategy rather than changing existing package files blindly.

Run `python <skill>/scripts/run_tests.py --addon <path-to-addon>` for each addon; it requires an existing `tests/unit` folder and fails if missing. The runner installs its isolation guard before collection, adds `scripts/` to `sys.path`, uses pytest importlib mode, sets the pytest root to the unit directory, and limits conftest discovery to the unit directory. It does not automatically add shared fixture directories, addon-level compatibility adapters, sibling addon test folders, or repository roots to `PYTHONPATH`. Before choosing the environment, inspect imports in the selected test files and adapters, then set `PYTHONPATH` to the minimum required mounted paths; use the adapter's actual directory when an AC selector imports it by module name rather than adding only its canonical `unit/` directory. Project pytest settings or plugins may still affect collection; disable or adapt them if necessary. For multiple addons, run the command separately so their fixtures and imports remain isolated. If unit modules import sibling unit modules by bare module name, add `<addon>/tests/unit` to `PYTHONPATH`; the runner does not add that directory automatically. The runner's `-- <pytest arguments>` form remains available for advanced selection; its caller is responsible for equivalent collection isolation.

Example pattern for a repository with one shared helper and a sibling selector adapter:

```sh
PYTHONPATH="$REPO/tests/shared:$REPO/addon/tests:$REPO/sibling/tests:$REPO" \
  python "$SKILL/scripts/run_tests.py" --addon "$REPO/addon"

PYTHONPATH="$REPO/tests/shared:$REPO/addon/tests:$REPO/sibling/tests:$REPO" \
  python "$REPO/addon/ac_tests/test_acNN.py"
```

Use only the roots actually required by imports. In containers, translate them to the mount path (for example `/workspace/...`) and keep the source mount read-only. A missing-module collection failure is not a product-test failure; correct the invocation and rerun. Strict selector output such as `COMPONENT PASS` proves only that selector's expected component tests ran, not full AC or UAT acceptance; preserve unavailable cases as `NOT RUN`.

For Odoo-dependent source files, use `odoo_modules()` before importing the target. If the addon's initializers import real Odoo or unrelated dependencies, load the target file with `importlib.util.spec_from_file_location` as in `examples/test_mocked.py`, and supply any required relative import context explicitly. Do not load a real Odoo registry. Each test should build fresh doubles. The sample `examples/sample_addon/tests/unit` demonstrates discovery even when addon initializers require Odoo.

## Provider-only and optional-adapter boundaries

When a provider must work without an optional adapter, verify the executable model boundary rather than inferring independence from the manifest or imports alone:

1. Search active provider code—including controllers, error paths, and inherited methods—for registry lookups such as `self.env[...]`, `request.env[...]`, and `env.ref(...)`. Separate executable lookups from comments, tests, and historical configuration keys.
2. Resolve each referenced model/XML ID to its active declaration and owning addon; compare that owner with the provider manifest and the accepted dependency contract.
3. Treat a provider lookup to a model declared only by an optional adapter as a hard runtime dependency, even when the provider manifest and Python imports omit that adapter: installation may succeed while the request fails at registry lookup.
4. Add a focused offline regression test with a strict provider-only registry/request double that raises on unknown model access. Test the adapter alias separately and assert the dependency direction. Avoid permissive `MagicMock` or default-dictionary behavior that silently manufactures missing models.
5. Bind the finding to the exact base-to-candidate diff. A green unit suite does not override a confirmed dependency-contract violation; an absent registry/runtime test remains a separate evidence gap, not proof of independence.
