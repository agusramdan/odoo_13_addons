# Layout and discovery

```text
my_addon/
  __manifest__.py
  tests/
    __init__.py             # from .integration import test_model, test_wizard
    integration/
      __init__.py           # from . import test_model, test_wizard
      test_model.py
    unit/                   # independent pure/mocked tests
```

For Odoo 13, import each integration test module directly into the top-level `tests` package (for example, `from .integration import test_model, test_wizard`) and import each module in `tests/integration/__init__.py`. Odoo 13's loader inspects only top-level `tests` package members whose names begin with `test_`; `from . import integration` alone can leave nested integration tests undiscovered even when the nested package imports them. Verify real collection from Odoo logs (`Ran N tests` and expected methods); exit 0 with zero collected tests is not a pass. Preserve existing imports and test files. Do not import isolated unit tests into Odoo's integration test package automatically. Preserve existing addon initialization and test files. Use unique addon/module names and avoid naming collision. Test registration and module update/install are performed by Odoo, not by plain pytest discovery.
