# AC-focused component entrypoints

All addon-owned case bodies, including behavior, live in `amr_sentry/tests/unit`.
The old `amr_sentry/tests/test_U11_sentry_*` paths and the `ac*_cases.py` files
are compatibility adapters; canonical unit cases do not depend on those legacy
adapters. These offline cases do not replace native Odoo ORM integration tests.
The historical `tests/addons13_27` shim remains. AC-01
selects the external `amr_service_client` bridge test; that dependency is not
copied. AC-07 also includes the synthetic N3 component regression here.

From the repository root, inside the supported Python 3.7.3 runtime, run one
entrypoint at a time (replace `NN` with `01` through `12`):

```sh
PYTHONPATH=tests/addons13_27:amr_sentry/tests:amr_service_client/tests:amr_sentry/ac_tests:. \
  python3 -B amr_sentry/ac_tests/test_acNN.py
```

A `COMPONENT PASS` means the expected number of distinct tests was selected and
executed with no failures, errors, skips, expected failures, or unexpected
successes. It is not an AC acceptance verdict. A mismatch or missing import
exits 1. AC-05 and AC-12 exit 2 with `NOT RUN`, since their required oracles
are unavailable. Do not treat either outcome as a pass. No aggregate runner is
provided; any aggregate must propagate failures and incomplete statuses.

These modules intentionally fail unittest discovery closed: ordinary unittest
can return success for skipped-only tests. Keep this directory outside Odoo's
`tests` package and outside normal addon test discovery. Run the gate controls
with the same PYTHONPATH: `python3 -B amr_sentry/ac_tests/check_strict_runner.py`.
Existing canonical and native test commands remain necessary.

| AC | Component selector(s) | Expected |
|---|---|---:|
| 01 | core bridge | 2 |
| 02 | config | 4 |
| 03 | safe file | 5 |
| 04 | policy, model | 15 |
| 05 | real SDK isolation/outside telemetry | NOT RUN |
| 06 | bootstrap warning, reporter failure diagnostic | 2 |
| 07 | service-client behavior, N1–N3, L2 and L3 component regressions | 12 |
| 08 | action exception reporting, A1 next-action component regression | 3 |
| 09 | bootstrap initialization | 1 |
| 10 | packaging | 2 |
| 11 | documentation | 7 |
| 12 | monitoring controls and restore/disable/restart | NOT RUN |

The L2 case checks the extracted `dispatch_send` method with a synthetic HTTP
response and fake log and reporting hooks: one request, one success hook, and
no log creation with `active_log=False`. It does not exercise a configured
policy, real SDK, persisted records, fresh-cursor counts, or Odoo ORM; it does
not assert that error logging is disabled. Full L2 remains a separate ORM gate.

The L3 matrix invokes extracted `dispatch_send` for preparation, transport and
HTTP failures with both `active_log` settings. It checks exact fake request,
failure-hook and error-log calls, exception identity, response availability,
and fake log arguments. The hook and log sink are fakes: no configured policy,
SDK capture, persistence, fresh cursor, rollback, or error-log-write failure is
tested. Full L3 remains an ORM gate; C1 and L5 remain blocked.

The A1 next-action case joins extracted request and action methods with a fake
HTTP response and reporter, including a failing action-error reporter. It checks
one request, two ordered hook outcomes, response and exception identities, and
the error handler. It is not evidence of real SDK delivery, configured policy,
persisted actions, or ORM behavior; the full A1 persisted-action oracle remains.
