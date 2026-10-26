# ADDONS13-48 — PRD Draft r8 (grant work excluded)

**Status: Owner-approved Step 0 scope (2026-10-26).** Based on repository branch `ADDONS13-48`, HEAD `b1399abf3bcc0031983a39761d5b7d34850f59f5`. Scope and acceptance criteria are approved; verification outcomes are recorded separately in `UAT-EXECUTION-r3.md`. This status records approval and does not imply commit, push, or deployment.

## 1. Scope matrix (per addon)

| Addon | In scope | Explicitly out of scope |
|---|---|---|
| `amr_oidc` | `oidc.client.validate_token` consumer-side validation contract; directly necessary consumer adaptations; exact issuer-profile selection and token verification described below. | **All grant implementation and grant behavior changes**: grant dispatch/handlers, authorization/code or token issuance flows, refresh-token flows, password/challenge/digital-signature grants, policy/catalog/configuration or enablement changes, endpoint/session lifecycle, PKCE, rotation, replay, and provider redesign. No grant implementation is authorized. Existing repository behavior is not to be characterized as accepted, rejected, enabled, or disabled by this specification. In particular, do not infer that password grant is denied or disabled. |
| `amr_token` | No independent feature work. Only a narrowly necessary consumer-facing adaptation may be considered if required by `amr_oidc.validate_token`, and only after the exact dependency is documented and Lead approves it; such adaptation must not implement or alter grants. | **All grant implementation and grant behavior changes**: grant dispatch/handlers, issuance/token creation, password or other grant handlers, refresh, policy/configuration, endpoint/session lifecycle, PKCE, rotation, replay, and provider redesign. Also excluded: unrelated token-provider changes. Do not infer password grant is denied or disabled. |

Grant exclusion is a boundary on this work, not a claim about current runtime behavior, a waiver, or a risk acceptance. If the in-scope consumer contract cannot be met without changing grant behavior in either addon, stop and raise a separate scope decision.

## 2. Validation requirements

1. Treat JWT `iss` only as an **unverified selector hint**. Use its exact value to select exactly one active issuer profile with exact issuer match and `token_profile='jwt'`.
2. Verify signature and verified issuer against that same selected profile. Do not trust unverified claims as authentication/authorization evidence.
3. Validate audience only against that selected profile's configured audience allowlist. Do not add a `client_id` audience equality requirement.
4. `client_id` remains lookup-only on the legacy falsy/empty-`self` client lookup path; it is not an extra cryptographic audience constraint.
5. Fail closed on malformed/missing/unusable issuer, zero or multiple matching profiles, inactive/non-JWT profile, signature/verified-issuer/audience failure. No global/default issuer fallback and no retry against another profile.
6. Preserve supported legacy `validate_token` call/return/error behavior where established and relevant. Consumer adaptations must be directly necessary and stay within the matrix.

## 3. Repository evidence and boundary notes

At the recorded snapshot, `amr_oidc/models/oidc_client.py` defines `validate_token` at line 168; its falsy-self branch decodes without signature verification to inspect `aud`, looks up a client using that value, then delegates validation using the client's `client_id` as audience. This is the consumer-side area under review, not a statement that current behavior meets requirements. The `amr_oidc` manifest depends on `amr_token`. `amr_token/models/helper.py` contains token/grant-related helpers and issuance paths. `amr_oidc` also contains grant-related helper/dispatch code and grant catalog data. Those observations reinforce the explicit exclusion; they do not decide current deployed/runtime grant behavior. Do not modify unrelated existing worktree changes.

## 4. Acceptance criteria (draft; one-to-one UAT mapping)

- **AC01** `iss` is only an unverified selector hint; selection requires exactly one active exact-issuer profile with `token_profile='jwt'`. (UAT-01)
- **AC02** Signature and verified issuer are checked against the same selected profile before token acceptance. (UAT-02)
- **AC03** Audience is checked only against the selected profile's configured allowlist; disallowed audience fails closed. (UAT-03)
- **AC04** Malformed/missing issuer, unknown/inactive/non-JWT/ambiguous profile, invalid signature, verified issuer mismatch, or disallowed audience cannot yield an accepted token. (UAT-04)
- **AC05** No default/global issuer fallback or retry against another profile occurs on selection or verification failure. (UAT-05)
- **AC06** Relevant legacy call forms and falsy/empty-self `client_id` lookup are assessed; preserve supported behavior or document a concrete blocker. (UAT-06)
- **AC07** Candidate changes are confined to `amr_oidc.validate_token` and directly necessary consumer adaptations; the per-addon matrix is respected. No grant implementation/behavior change occurs in either addon. (UAT-07)
- **AC08** A profile-allowlisted audience differing from `client_id` is not rejected merely for inequality; client_id remains lookup-only on the legacy lookup path. (UAT-08)
- **AC09** Documents and implementation notes explicitly exclude all grant implementation in both addons and make no claim that password grant is denied/disabled. (UAT-09)

All criteria are approved requirements. The unique one-to-one crosswalk, including the Owner-approved UAT-04 amendment, is in UAT r7; Lead execution results are recorded in `UAT-EXECUTION-r3.md`.

## 5. Scope decisions and resolved questions

- **Owner-approved scope interpretation:** “grant implementation” excludes all changes that create, dispatch, enable, disable, configure, or alter grant behavior, including password grant; it does not assert the existing status of any grant.
- **Resolved:** No `amr_token` consumer adaptation was necessary; no `amr_token` file was changed.
- **Resolved:** `oidc.issuer.register` provides active/exact-issuer profile selection, `token_profile='jwt'`, and audience allowlists; `amr_resource` verifies using the selected profile's key and issuer.
- **Resolved:** The falsy/empty-self `oidc.client.validate_token` call site performs the legacy `client_id == unverified aud` lookup; the candidate preserves it and no longer adds client ID as a cryptographic audience constraint.
- **Resolved:** Owner approved this scope and UAT; Step 0 was closed before the user directed continuation through Steps 1–4. Execution evidence is in `UAT-EXECUTION-r3.md`.
