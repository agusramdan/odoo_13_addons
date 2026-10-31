# Step 1 — Boolean azp absence policy: offline evidence

- Base: branch `ADDONS13-57`, HEAD `f6f3a425294224ff771a6c467a0af654e0395290`.
- Scope: AC-02/U02 invalid plan input. A supplied `allow_missing_azp` must be an actual Boolean, not a string, integer or null. Omission retains the existing default. This does not decide D2–D5 or implement approval, inventory, reconciliation or drift.
- RED: focused command below exited 1: one test, three assertion failures (`ValidationError not raised`) for `'false'`, `1`, and `None`; the valid `True` control succeeded.
- GREEN: same focused command exited 0: one test, OK. Regression command below exited 0: 159 tests, OK.
- Runtime image ID: `sha256:a58cf9483bf342f50808ea39e7d46ca7caa7f6f2bab94e851fc1def6165c4fc3`.
- SHA-256 of `git diff -- amr_resource/models/trust_registry.py amr_resource/tests/test_migration_unit.py`: `a6ed66f2cc4531e0f6d2acbf4a64de7dace688d02b84a2f683eaf1eebd2304f9`. This is the production-and-test diff only, excluding this evidence file.

Focused command (run from `/home/ubuntu/worktrees/ADDONS13-57`):

```sh
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges -e PYTHONDONTWRITEBYTECODE=1 -v /home/ubuntu/worktrees/ADDONS13-57:/src:ro -w /src --entrypoint python addons13-57-unit-scratch:local -B -m unittest discover -s amr_resource/tests -p 'test_migration_unit.py' -k test_plan_rejects_non_boolean_allow_missing_azp -v
```

Regression command (same working directory and isolation):

```sh
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges -e PYTHONDONTWRITEBYTECODE=1 -v /home/ubuntu/worktrees/ADDONS13-57:/src:ro -w /src --entrypoint python addons13-57-unit-scratch:local -B -m unittest discover -s amr_resource/tests -p 'test_*_unit.py'
```

Offline unit evidence only: no live database, migration execution, native Odoo/ORM test or UAT. U02 as a whole remains NOT RUN; this slice does not establish its complete oracle.
