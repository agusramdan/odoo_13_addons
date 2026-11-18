# ADDONS13-79 test process preparation

`prepare_run.py` is a standalone preparation adapter, not a UAT controller. It
never starts Docker, Odoo, PostgreSQL, or changes an attempt ledger. It is not
integrated into `tests/run-uat.sh` or the historical scratch controller.
An authorized lifecycle controller must consume both returned read-only mounts
and all `odoo_args`, eliminate competing addon-path mounts/config overrides,
and verify the actual effective container mounts and process argv before use.
It must also enforce candidate/commit and document binding, snapshot hashes,
resource ownership, freshness, attempt fencing, evidence and cleanup. This
adapter does not enforce those UAT prerequisites and is not approval to run.

Example offline preparation using already verified local snapshot and core
addon roots (no process launch):

```
python3 tests/addons13_79/prepare_run.py --source /absolute/snapshot \
  --core /absolute/core-addons --output /absolute/new-output --selector amr_resource
```

For resource-only, dependencies are traversed transitively through both source
and core, with missing, cyclic and forbidden dependencies rejected. Source
addons take precedence and only their closure is copied. Core must not contain
provider, token or glue addons. Both roots are scanned for symlinks, but this
is not a secure traversal: host changes between checking, reading, copying and
mounting can introduce symlinks or replace files (TOCTOU). Use independently
verified, immutable, trusted snapshots and protect the output and core throughout
use. The adapter does not verify snapshot hashes or authenticity; read-only
container mounts do not prevent host edits. Other selectors fail closed: a
curated, hash-verified full-snapshot contract has not been implemented. No
proxy-enabled plan is currently produced. No production configuration or HTTP
fixture is edited.

Offline regression (supplemental unittest with repository isolation guard):

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.agents/skills/odoo-unit-test/scripts python3 -c 'from isolation import install,self_check; install(); self_check(); import unittest; s=unittest.defaultTestLoader.discover("tests/addons13_79/unit",pattern="test_*.py"); r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(not r.wasSuccessful())'
```

The prescribed pytest skill runner is the required gate when available; this
unittest command is supplemental and does not establish Odoo integration,
HTTP proxy semantics, TLS, registry state, or UAT acceptance.
