# Sentry test layout

Offline unit tests are owned by their addons: Sentry behavior, policy,
configuration, bootstrap, documentation, model, safe-file, layout, bridge, and
settings tests live under `amr_sentry/tests/unit` and
`amr_service_client/tests/unit`. The old `test_U11_sentry_*` files under
`amr_service_client/tests` are compatibility adapters for AC selectors; their
canonical test bodies are collected from the addon unit directories. The shared
`tests/addons13_27/support.py` remains a fixture dependency. The ORM probe is at
`amr_sentry/tests/orm_68_probe.py`; no Sentry test, selector, or probe remains
in `tests/addons13_27`.

## Dockerized pytest (Python 3.7.3)

The test-only Docker template is under the repository's root `tests/`
directory: `tests/Dockerfile.pytest`, `tests/requirements-pytest.txt`, and
`tests/Dockerfile.pytest.dockerignore`. The Dockerfile-specific ignore file
limits the build context to the Dockerfile and requirements only; source and
credentials are not sent to the build daemon. The Hermes skill remains external
and is mounted read-only when running.

Build from the repository root:

```sh
docker build --tag amr-sentry-pytest:py373 --file tests/Dockerfile.pytest tests
```

Run the `amr_sentry` unit suite with networking disabled and source/skill mounted
read-only:

```sh
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD:/workspace:ro" \
  -v "$HOME/.hermes/skills/odoo13-unit-test-mock:/skill:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/tests/addons13_27:/workspace/amr_sentry/tests:/workspace/amr_service_client/tests:/workspace \
  amr-sentry-pytest:py373 --addon /workspace/amr_sentry
```

The bridge/settings tests owned by `amr_service_client` are also in its
`tests/unit` directory. Run only those Sentry cases through the same guarded
runner (the unrelated service-client tests require additional dependencies):

```sh
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  -v "$PWD:/workspace:ro" \
  -v "$HOME/.hermes/skills/odoo13-unit-test-mock:/skill:ro" \
  -w /workspace \
  -e PYTHONPATH=/workspace/tests/addons13_27:/workspace/amr_sentry/tests:/workspace/amr_service_client/tests:/workspace \
  amr-sentry-pytest:py373 -- \
  --import-mode=importlib \
  --rootdir=/workspace/amr_service_client/tests/unit \
  --confcutdir=/workspace/amr_service_client/tests/unit \
  /workspace/amr_service_client/tests/unit/test_unit_sentry_bridge.py \
  /workspace/amr_service_client/tests/unit/test_unit_sentry_settings.py
```

The skill runner installs its test isolation guards before pytest collection.
This is a test aid, not a security sandbox; run only trusted source. The
network-disabled test containers do not need PostgreSQL or a running Odoo
server. Offline mocked tests do not prove ORM, database, runtime, privacy, or
full UAT behavior. Use the separate Odoo integration suite for those gates.

Odoo discovers ORM tests via each addon's `tests/__init__.py`. Run Odoo 13 with
`--test-enable --test-tags=/amr_sentry` in a disposable database to exercise
the Sentry hook integration test.
