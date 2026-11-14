# Reusable UAT Environment Design & Authorization Template

> **Purpose:** reusable reference for planning a task-specific UAT environment in this repository. Copy/fill the profile for each task and bind it to that task's accepted requirements and test cases. This document is design guidance only: it provisions nothing, runs nothing, and grants no access or permission by itself.
>
> **No blanket permission:** repository presence, an accepted PRD/UAT, prior UAT, completion of this worksheet, or general permission to “test” does not authorize an environment, database, network request, external integration, or data mutation. Only an explicit, current, owner-approved authorization envelope that names the exact candidate, acceptance cases, target/resources, allowed actions, run/retry budget, expiry, and cleanup permits execution within those bounds. A task matching all those fields may proceed without asking the owner to reconfirm each already-authorized action. Missing, ambiguous, expired, revoked, changed, or out-of-envelope scope means STOP and obtain explicit fresh approval before that action. No approval here can override policy, security controls, or an independent workflow gate.

## 1. How to use this reference

1. Read the repository's canonical workflow, task's accepted PRD and UAT, repository instructions, and applicable runtime/build/dependency configuration. Record their exact identities and reconcile conflicts explicitly; do not silently select a version or treat a draft/example as authoritative.
2. Bind this profile to the specific candidate revision and acceptance-case IDs. Plan only tests required by accepted criteria. Keep review/quality gates distinct from runtime authorization.
3. Classify each case by environment needs (offline, native Odoo/database, internal HTTP/proxy, external/network). Prefer the least capable environment that proves the criterion; do not introduce network/database actions merely because infrastructure exists.
4. Obtain and record owner approval for the completed envelope before any authorized runtime action. A profile marked `PENDING`, `UNKNOWN`, or blank is not authorization. If a needed field cannot be bounded, do not execute that part.
5. Record actual per-case outcomes and evidence after authorized execution. Approval, eligibility, and workflow acceptance are separate from observed test results.

This is a fillable design profile, not an executable manifest. YAML-like fields below are a human worksheet only: no script, CI job, container, or operator should interpret it as permission without a separately implemented, reviewed, and explicitly authorized mechanism.

## 2. Per-task environment and authorization profile

Copy this section into the task's UAT/execution record. Use `NOT APPLICABLE` with a reason where appropriate; never leave a blank that could be mistaken for approval.

```yaml
profile_version: "1"
task:
  id: "<task/issue identifier>"
  owner: "<named accountable owner>"
  operator: "<named runner/operator>"
  reviewer: "<named independent reviewer or NOT APPLICABLE + reason>"
  accepted_prd: "<path, revision/hash, acceptance status>"
  accepted_uat: "<path, revision/hash, acceptance status>"
  workflow_gate: "<required prior review/gate and actual status>"
candidate:
  repository: "<repository identity>"
  revision: "<full immutable commit SHA>"
  worktree_state: "<clean or exact approved dirty-diff identity; otherwise STOP>"
  included_changes: "<exact paths/diff identity>"
  excluded_changes: "<explicit scope exclusions>"
runtime:
  authoritative_sources_checked:
    - "<AGENTS/config/image/lock/source + revision/hash>"
  reconciled_runtime: "<exact OS/image/runtime and version, or unresolved>"
  image: "<immutable image reference incl. digest; or NOT APPLICABLE>"
  dependency_lock: "<exact lock/manifest revision/hash>"
  architecture: "<platform/architecture>"
  unresolved_conflicts: "<none, or list; unresolved means STOP>"
cases:
  - id: "<accepted UAT case ID>"
    acceptance_criterion: "<exact AC ID and concise criterion>"
    class: "OFFLINE | NATIVE_ODOO_DB | INTERNAL_HTTP_PROXY | EXTERNAL_NETWORK"
    environment: "<exact isolated target/resource names or none>"
    data_fixture: "<synthetic fixture IDs/source; no real user data>"
    actions: "<bounded action and expected state changes>"
    evidence: "<specific sanitized evidence to retain>"
authorization:
  status: "PENDING | APPROVED | DENIED | EXPIRED | REVOKED"
  approver: "<owner name/identity>"
  approval_record: "<durable approval reference and timestamp/timezone>"
  approved_at: "<timestamp>"
  expires_at: "<timestamp/timezone>"
  exact_target: "<isolated host/project/namespace/resource identity; no production>"
  resources: "<named services, database alias, ports, volumes, proxy routes, APIs>"
  allowed_actions: "<explicitly enumerated operations, commands/workflow, boundaries>"
  database_scope:
    create: "<exact disposable DB naming pattern/owner; or NONE>"
    read: "<exact synthetic-only source; or NONE>"
    update: "<exact disposable target and permitted writes; or NONE>"
    delete: "<exact disposable target and cleanup authority; or NONE>"
  network_scope:
    outbound: "<NONE by default; exact host/protocol/port/purpose if approved>"
    inbound: "<exact listener/source/port if approved; otherwise NONE>"
    external_services: "<exact service/account/sandbox and permitted operations, or NONE>"
  data_scope: "<synthetic-only fixture classes and constraints>"
  side_effects: "<expected side effects and prohibited effects>"
  max_runs: "<integer maximum total executions>"
  max_retries: "<integer maximum retries, including trigger for stopping>"
  cleanup:
    owner: "<named responsible party>"
    deadline: "<timestamp/timezone>"
    actions: "<exact disposable objects to remove/restore; never implied>"
    verification: "<read-back evidence proving cleanup and residual check>"
  stop_conditions: "<unexpected target/data, failure, drift, ambiguity, limit, etc.>"
results:
  cases: "<record actual status separately per accepted case>"
  evidence_location: "<access-controlled path/reference; sanitized>"
  cleanup_status: "NOT STARTED | COMPLETE | FAILED | NOT APPLICABLE + reason"
```

### Owner approval semantics

Approval must be attributable to the owner and apply to the completed, exact profile—not inferred from silence, task assignment, prior approval, or a generic statement. It is valid only for the named candidate, accepted case IDs, target, resource boundaries, actions, data, attempt limits, and time window. Preserve the approval reference with the task record. The approval envelope may authorize a bounded set of runs/retries; individual runs inside that live envelope do not need redundant confirmation. Count every execution against the limit. Stop at the first unexpected side effect or scope mismatch; do not spend unused retries on a changed setup.

A new candidate SHA/diff, UAT or acceptance change, target/resource/port/DB change, new case, changed data classification, new outbound destination, expanded action, higher run/retry count, expiry, failed cleanup, or any other material deviation is outside the envelope. Obtain fresh explicit approval before continuing. Do not “repair” scope by changing the worksheet after approval; record the old disposition and seek re-approval. Approval of disposable UAT never authorizes production, customer data, destructive cleanup beyond named objects, release, deployment, or merge.

## 3. Environment selection and safety baseline

### Case classes

- **OFFLINE:** pure/unit/static checks with no Odoo service, database, socket, or external call. Use when sufficient for the criterion. Offline execution still requires the applicable candidate/test authorization and must not be represented as native runtime UAT.
- **NATIVE_ODOO_DB:** real Odoo registry/ORM/module behavior against an isolated, disposable database and separately isolated filestore. Requires explicit named DB create/write/delete bounds, compatible Odoo/runtime tuple, synthetic data, and cleanup read-back. Never point a disposable test at a production or shared database.
- **INTERNAL_HTTP_PROXY:** inbound requests through a local/internal HTTP endpoint or proxy. Bind listener and source address/port, route, target, and test operations exactly; loopback/private network is not an implicit authorization to expose or probe it. Outbound self-HTTP should be `NONE` unless the accepted criterion and owner-approved envelope explicitly require it.
- **EXTERNAL_NETWORK:** any internet, third-party API, SaaS, email, payment, identity provider, webhook, DNS change, or external callback. Default is no external network. Prefer a local fake/sandbox; when truly required, name exact endpoint, sandbox account, operation, volume/rate bound, and side effects. Production endpoints and real customer accounts are excluded unless separately authorized under a distinct process.

A case may need multiple classes; record each and its exact targets rather than selecting only the least restrictive label.

### Baseline controls

- Isolate by default: dedicated disposable project/namespace/container/network, unique task-scoped resource names, non-routable or loopback-only listeners where feasible, no shared production volumes, credentials, database, filestore, queues, or proxy routes. Deny outbound network unless explicitly required and approved.
- Use synthetic fixtures and reserved/test identities only. Do not copy production/customer data, even “anonymized,” absent a separate explicit data authorization and validated sanitization plan. Do not use real signing keys, API credentials, email recipients, or payment instruments.
- Keep credentials out of this profile, source control, command output, shell history, logs, screenshots, and evidence. Refer only to approved secret-store references/identifiers; never paste secret values. Verify logs and test artifacts are redacted before sharing.
- Pin the actual image by digest and all relevant runtime/dependency inputs. Record source commit and lockfile identities. Reconcile repository instructions, task acceptance documents, Dockerfiles/images, package/requirements locks, and runner configuration. If they disagree (including Python/OS/framework/dependency versions), surface the conflict to the owner/maintainer and stop runtime UAT until a source of truth is approved. A reference example is not a version selection.
- A clone/restore is not automatically isolated or safe: establish origin, data classification, access, network egress, scheduled jobs, mail/webhook integrations, credentials, and cleanup before use. Snapshot/restore operations need explicit source-read, destination-create/write/delete, and retention scope. A clone can retain secrets, personal data, external endpoints, scheduled jobs, and production identifiers.
- Disable or safely redirect scheduled/async jobs, outbound mail, webhooks, payment, telemetry, and integrations only when that does not invalidate the criterion; record the setting and residual side effects. Never claim “no side effects” without checking the relevant paths.
- Separate lifecycle actions: create, start, migrate/initialize, test, stop, reset, and delete are distinct operations. `stop` is not deletion; deleting a database, volume, snapshot, image, or shared service requires that exact resource and action in the approval. No broad cleanup command.
- Identify operator, owner, reviewer, target admin, and cleanup owner. Ensure capacity and isolation preflight before starting; preflight is read-only unless the envelope explicitly says otherwise. Never print interpolated configuration that may reveal secrets.

## 4. Runtime reconciliation checklist

Before selecting an environment, capture the evidence (paths/revisions/hashes) for:

- repository instructions and canonical workflow;
- accepted task PRD/UAT plus acceptance IDs/statuses;
- application/framework version and required system packages;
- base image and digest, OS/architecture, language/runtime version;
- dependency declarations and complete pinned/resolved lock set;
- test runner/harness, entrypoint, mounts and required skills/fixtures;
- database engine/version, extensions, encoding, schema/module initialization needs;
- HTTP/proxy/network requirements, ports, outbound destinations and integrations.

Record the resolved compatible tuple in the task profile. Do not copy a runtime value from this template or an unrelated task. Do not run an unpinned dependency resolution against the network during UAT. A target requiring upgrade/migration, production-like restore, external credentials, non-synthetic data, or an unlisted dependency is a scope change until explicitly approved.

## 5. Preflight and execution record

### Preflight (before any stateful action)

- [ ] Accepted PRD/UAT and case IDs are exact, current, and hash/revision-bound; required upstream workflow/review gate status is recorded.
- [ ] Candidate source revision and worktree/diff identity match the approval exactly.
- [ ] Every planned case has a class, target, action, fixture, expected state, and evidence plan.
- [ ] Runtime/dependency conflicts are resolved in writing; image/runtime/lock are pinned and match the profile.
- [ ] Owner-approved authorization is current, complete, within expiry and remaining run/retry budget; target/resource names are independently verified before use.
- [ ] Environment is isolated; no production/shared DB, volume, service, route, account or real user data is reachable; egress and credentials are constrained as approved.
- [ ] DB ownership and disposable naming are verified. Any DB create/delete/reset is explicitly named and authorized.
- [ ] Expected side effects, async jobs, mail, telemetry and cleanup are understood; logs/evidence handling is safe.
- [ ] Capacity and service health checks are read-only and adequate. Any material drift blocks execution.

If any item is false, unknown, or outside scope, mark the affected case `BLOCKED` or `NOT RUN`; do not proceed by assumption.

### Per-case result ledger

Use stable accepted case IDs and keep a distinct row per case/subcase. Do not overwrite the planned status with an approval or aggregate result.

| Case / AC | Candidate SHA | Actual environment/target alias | Run / retry | Actual result | Evidence reference | Limitation / deviation |
|---|---|---|---:|---|---|---|
| `<ID>` | `<full SHA>` | `<approved alias>` | `<n>` | `PASS / FAIL / BLOCKED / NOT RUN / N/A` | `<sanitized reference>` | `<reason or none>` |

- `PASS` means the specified assertion was actually observed and evidence is available.
- `FAIL` means an executed assertion did not meet its expected result; retain the failure and safe evidence.
- `BLOCKED` means the case could not proceed because a prerequisite/scope/safety condition prevented it.
- `NOT RUN` means no execution occurred; it is not a pass, waiver, or approval.
- `N/A` requires a documented rationale and the disposition required by the accepted UAT/owner; do not silently remove a case.

Record exact commands/workflow identifiers, timestamps, tool/image/runtime identity, sanitized logs/assertions, and state read-back needed to reproduce the case. Avoid sensitive payloads. Distinguish mock/stub evidence from live Odoo registry/HTTP/database evidence. Do not infer an aggregate pass from a process exit code, a subset of cases, or historical results.

## 6. Cleanup and closure

After execution, perform only cleanup actions named in the authorization. Verify by reading back the exact approved resource identities and states: disposable DBs, filestore, containers/project, volumes, listeners/routes, test records, snapshots, and temporary artifacts as applicable. Preserve required sanitized evidence and record any residual resource, cleanup failure, and owner escalation; failed cleanup blocks closure and may require new authorization. Do not use broad prune/reset/delete operations. Confirm that no production resource or external side effect was touched, based on evidence—not assumption.

Keep these statuses independent:

1. **Authorization status:** whether an owner-approved envelope exists and is currently valid.
2. **Case result:** actual `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, or approved `N/A` for each case.
3. **Workflow/gate disposition:** review, UAT, waiver, acceptance, and handoff statuses per the canonical workflow. A waiver preserves actual failed/not-run results and is not test evidence or runtime permission. UAT permission does not itself accept a feature or authorize PR acceptance, merge, release, or deployment.

## 7. Repository reference notes

This template is generic and deliberately does not prescribe a Python/Odoo version, image, database name, command, Compose file, or runnable environment. At authoring time, repository configuration was observed to include `AGENTS.md`, root `Dockerfile`, `tests/Dockerfile.pytest`, and `tests/requirements-pytest.txt`; these are discovery pointers, not an authoritative resolved runtime tuple. The canonical workflow is maintained outside this repository at `docs/standards/DEVELOPMENT-WORKFLOW.md` in the workspace and must be consulted directly. Check current files and accepted task artifacts for each task; do not rely on this note as a substitute for current source inspection.

## 8. Non-authoritative ADDONS13-79 example/profile

This is an illustrative task-specific selection only; it does not replace this reusable, version-neutral template, bind accepted cases, qualify dependencies, or authorize execution. Values below reproduce the Owner-provided environment selections, not a compatibility verdict.

```yaml
profile_kind: "NON-AUTHORITATIVE EXAMPLE — not an execution manifest"
task:
  id: "ADDONS13-79"
runtime:
  selected_target: "Python 3.7.3 (Owner selection; NOT YET DEPENDENCY-QUALIFIED)"
  odoo_container: "odoo13addonsuat"
  postgres_container: "odoo13dbuat"
  disposable_database: "odoo13uat"
  compatibility_status: "UNRESOLVED — selections alone do not establish runtime/dependency compatibility"
  test_results: "NOT RUN"
execution:
  max_runs: 3 # maximum total started attempts, not 3 retries
  retry_semantics: "At most two retries after the initial attempt; count every started attempt, including failed or interrupted attempts."
  cleanup: "Automatically after each completed attempt and catchable interruption, success or failure, via tests/run-uat.sh only. The wrapper requires the exact `tests/docker-compose-uat.yml` path and refuses to run if Compose reports any pre-existing project containers; inventory errors fail closed. It targets only the exact Compose file, profile, and unique task-scoped project; it removes that project's containers, network, and Compose-managed volumes, never global resources. A forced kill (including SIGKILL) or host failure cannot be trapped or guarantee cleanup; read back the exact project resources afterward, and treat any residual resource or cleanup failure as blocking closure."
  persistent_state: "An explicit attempt ledger and evidence directory must be outside ephemeral volumes; treat raw logs as potentially sensitive, keep them owner-only (wrapper-created evidence directory mode 0700 and files mode 0600), and sanitize retained logs/evidence before sharing. The wrapper does not sanitize logs. Do not share a project name/ledger across unrelated tasks."
  cleanup_failure: "Blocks closure; investigate and escalate without broad prune/reset."
  result: "NOT RUN"
```

`tests/docker-compose-uat.yml` and `tests/run-uat.sh` encode configuration/lifecycle safeguards only. The wrapper's existence is not proof it has been used or that a particular environment is safe. No `.env`, credentials, or secret values belong in this repository. These fields—and template completion, container names, or test eligibility—are **not execution authorization**. Before any runtime, separately satisfy candidate/spec acceptance and all workflow gates, resolve dependency/runtime compatibility, and obtain a current explicit authorization envelope naming the exact candidate, cases, target, actions, attempt budget, expiry, and cleanup. No UAT was run for this example; all test results remain NOT RUN.
