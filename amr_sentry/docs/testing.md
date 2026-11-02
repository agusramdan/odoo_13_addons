# Sentry test layout

The offline U11 contracts are in `amr_sentry/tests`; the two contracts for the
core bridge and settings are in `amr_service_client/tests`. They use the shared
`tests/addons13_27/support.py` doubles and are not Odoo ORM tests. Run from the
repository root with Python 3.7 and the test dependencies (including PyYAML):

```sh
PYTHONPATH=tests/addons13_27:amr_sentry/tests:. python3 -B -m unittest discover -s amr_sentry/tests -p 'test_U11_sentry_*.py' -v
PYTHONPATH=tests/addons13_27:. python3 -B -m unittest discover -s amr_service_client/tests -p 'test_U11_sentry_*.py' -v
python3 -B -m unittest discover -s tests/addons13_27 -p test_sentry_test_layout.py -v
```

The historical selector remains supported via a test-only discovery shim; it
runs the same 51 addon-owned contracts once, without importing them in Odoo:

```sh
python3 -B -m unittest discover -s tests/addons13_27 -p 'test_U11_sentry_*.py' -v
```

Odoo discovers the ORM hook test from `integration_tests` through
`tests/__init__.py`; the offline contracts are intentionally not imported by
Odoo's test loader. Run Odoo 13 with `--test-enable --test-tags=/amr_sentry`
in a disposable database to exercise that test. Neither these offline tests nor
the ORM hook check establish Sentry runtime, privacy, or full UAT acceptance.
