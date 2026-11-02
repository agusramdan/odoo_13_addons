# Revision note — ADDONS13-57 separated HMAC draft

Status: DRAFT / NOT ACCEPTED. Supersedes prior drafts only for proposed HMAC ownership/integration. No code, tests, runtime, database, Plane, commit or push authorization.

- Source baseline: `98c608f395add60a2e57182726e077167a01d5a5` (rebound per Owner internal comment `26d21ab4`).
- Candidate identity: HEAD plus combined diff SHA256 `70b9db25139901b69ced3d90cf3d99306355ac972fa99c19b19f4979a99c14f1` (not a passing candidate).
- Accepted source PRD: SHA256 `920d946873858c349d08427c93434bf0ce2e877bef4fcfca58b44b2ad2ba2bac`.
- Accepted source UAT: SHA256 `7a57d11180f94896dd2361c7d5cbf52f841a574c819bbe6133f1eb58a0c9906f`.
- Accepted D2–D5 proposal: SHA256 `48c2f70aea50fa0f84e52b05c892ba2329d970f9dbbe15138b8bd15d9a33757a`. Originals were not modified.

Owner directed HMAC/key-provider ownership to a separate addon; `amr_resource_hmac` is a provisional name. ADDONS13-58 is the proposed receiving/dependency task; its exact scope is not approved until its own PRD/UAT acceptance. `amr_resource` ordinary install/runtime does not require that addon. Read-only inventory/dry-run without it cannot confer apply eligibility. Apply/destructive cleanup fails closed before mutation without compatible provider and verifiable approval; no unsigned SHA fallback. Interface questions remain open.

Coverage: retained AC-01–09/U01–U16; added U17–U25 for addon absent, provider unavailable/unauthorized, wrong purpose/environment/schema/candidate, wrong key version/tag, stale independent inventory, rotation, leakage, and a valid-provider positive control. 25 unique test IDs total, all NOT RUN. Existing non-HMAC privacy, atomicity/concurrency, cleanup, recovery and regression criteria are retained.

Next gate: exact Owner/Lead acceptance of this draft pair, separate exact acceptance of ADDONS13-58 PRD/UAT and interface, then separate implementation-stage authorization. Draft acceptance alone does not authorize implementation.
