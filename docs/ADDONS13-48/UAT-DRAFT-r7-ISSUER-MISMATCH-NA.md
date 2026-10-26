# ADDONS13-48 — UAT Draft r7 (verified issuer mismatch structurally N/A)

**Status: Owner-approved acceptance plan and UAT-04 amendment.** Companion to Owner-approved PRD r8. This revision supersedes UAT r6 only for UAT-04 wording; Lead execution results are recorded in `UAT-EXECUTION-r3.md`.

## Scope matrix

| Addon | Candidate UAT boundary | Excluded from this UAT |
|---|---|---|
| `amr_oidc` | `oidc.client.validate_token` plus directly necessary consumer adaptations; issuer/profile, signature, issuer, audience, fail-closed, and legacy lookup assertions below. | All grant implementation/behavior changes, including dispatch, handlers, issuance, refresh, password/challenge/digital-signature grants, policy/catalog/configuration, PKCE, rotation, replay, and endpoint/session lifecycle. Do not infer password grant is denied/disabled. |
| `amr_token` | No standalone feature UAT. Only an expressly approved, directly necessary consumer-facing adaptation, without grant behavior changes. | All grant implementation/behavior changes and unrelated token-provider work. Do not infer password grant is denied/disabled. |

If testing requires a grant behavior change in either addon, stop and raise a separate scope decision; do not execute that work under this UAT.

| Case | AC | Proposed assertion / evidence | Status |
|---|---|---|---|
| UAT-01 | AC01 | On an authorized candidate, record selector `iss` and selected profile. Assert exact issuer match, active profile, `token_profile='jwt'`, exactly one match, and no other unverified claim trusted for selection. | PASS |
| UAT-02 | AC02 | Assert signature and verified issuer validation use the same uniquely selected profile, and token acceptance occurs only after both pass. | PASS |
| UAT-03 | AC03 | Exercise profile-allowlisted and non-allowlisted audiences. Assert only the selected profile's allowlist controls audience acceptance. | PASS |
| UAT-04 | AC04 | Exercise exact issuer/profile selection and signature validation on that same selected profile; malformed, missing, and unknown issuer; inactive, non-JWT, and ambiguous-profile prevention (verify duplicate issuer creation is rejected by registry uniqueness rather than corrupting DB state); invalid signature; and disallowed audience. Assert each feasible rejection fails closed. The separate “verified issuer mismatch” token case is structurally N/A: selector and verifier consume the same signed `iss` claim, so a valid token cannot present different issuer values at those stages. | PASS; mismatch subcase N/A |
| UAT-05 | AC05 | Observe lookup/verifier behavior on failures; assert no global/default fallback, no alternate-profile retry, and no acceptance. | PASS |
| UAT-06 | AC06 | Review actual relevant call sites and established legacy contract, including falsy/empty-self client lookup; assert supported behavior is preserved or capture a concrete blocker. | PASS |
| UAT-07 | AC07 | Review candidate diff and test plan against both-addon matrix. Assert changes are limited to `amr_oidc.validate_token` and directly necessary approved consumer adaptation; assert no grant implementation/behavior change in either addon. | PASS |
| UAT-08 | AC08 | Use an audience on the selected profile allowlist that differs from `client_id`; assert it is not rejected merely for inequality. Verify client_id is lookup input only on legacy falsy/empty-self path, not an additional cryptographic audience constraint. | PASS |
| UAT-09 | AC09 | Review PRD/UAT and any candidate notes; assert all grant implementation in both addons is explicitly out of scope and no statement claims password grant is denied/disabled or tested. | PASS |

## Coverage and open items

- AC count: **9** (AC01–AC09); UAT count: **9** (UAT-01–UAT-09); each AC maps to exactly one unique UAT case and vice versa.
- Lead executed all nine cases on 2026-10-26; evidence and limitations are in `UAT-EXECUTION-r3.md`.
- Owner-approved disposition: the standalone verified-issuer-mismatch token case in UAT-04 is structurally N/A for the same signed `iss` selector/verifier claim; the exact-match and same-profile signature assertions remain in scope.
- Grant implementation in both addons remains out of scope; this revision makes no claim that password grant is denied, disabled, or tested.
