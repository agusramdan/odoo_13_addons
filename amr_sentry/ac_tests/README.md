# Retired AC-focused scripts

All Python selector and runner scripts formerly in this directory have been
retired. The old `test_acNN.py` paths and `check_strict_runner.py` command are
not supported and have no compatibility shim. The directory is retained only
for this notice; canonical addon-owned cases remain in `amr_sentry/tests/unit`.

Run eligible component checks with the immutable, addon-owned entrypoint
`python amr_sentry/tests/unit/ac_test_runner.py AC02`. It collects and runs the
reviewed selectors through pytest and uses live TestReport results, not caller
supplied counts. Its TDD controls are `tests/unit/test_unit_ac_test_runner.py`;
they execute fresh temporary pytest files and cover positive, missing,
duplicate, skip, xfail, xpass, failure, immutable inventory and count-input
rejection. These tests verify runner mechanics, not full product acceptance or
proof of ORM, SDK, monitoring, or outside-telemetry behavior.

The accepted trace manifest records selector-to-case dispositions and the
external AC01 dependency. That bridge remains read-only and must not be counted
as executed without its own run evidence. AC05 and AC12 remain NOT RUN because
their real SDK/telemetry and monitoring/restore oracles are unavailable.
Historical selector results do not describe the current layout or establish
current acceptance.
