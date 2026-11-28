# Modes

## Pure Python
Extract business decisions into functions or classes and inject dependencies; test with unittest.TestCase or pytest and unittest.mock. The pure example covers an approval transition and a failed external API call without importing Odoo.

## Odoo mocked
Use `odoo_modules()` before importing the module under test, then instantiate its class using ordinary Python and inject `env` and fields. The shim supplies minimal `odoo.api` decorators, field constructors, model base classes, exceptions and HTTP names. It restores the prior modules afterward. Load individual files with importlib when addon `__init__.py` eagerly imports unrelated code. Patch the target module's imported symbols, not their original source. Add explicit mock methods for the actual addon contract; avoid permissive MagicMock chains that hide errors. These fakes do not emulate the Odoo metaclass or descriptor behavior.

`MockModel` keeps in-memory records. `search` supports conjunctions of `=`, `!=`, `in`, and `not in`; unsupported domains raise. `create`, `browse`, `write`, `mapped`, `filtered`, `ensure_one`, context and sudo are deliberately limited. `env.cr` always raises; it cannot emulate SQL. Each test should construct fresh mocks.
