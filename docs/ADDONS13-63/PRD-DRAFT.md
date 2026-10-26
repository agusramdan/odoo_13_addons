# ADDONS13-63 — PRD-DRAFT (OWNER-APPROVED STEP 0)

**Owner approval:** Accepted by direct Owner instruction on 2026-10-27 CST for the exact pre-provenance draft SHA-256 `2bd6ebd045e25cdb2f61dfad5e65afc31794c8e57d413248b8c87d33b678315c`. Approval is scoped to Step 0 requirements only; it is not a waiver, risk acceptance, or authorization beyond the Owner's separate instruction to continue Steps 1–4. **Baseline:** repository `/home/ubuntu/worktrees/ADDONS13-63-analysis`; detached HEAD and `origin/main` = `c08b050cfd85ccc5c705eb92852e57626eb82806`; clean before draft. All source evidence below is line-bound to that SHA (use `git show c08b050cfd85ccc5c705eb92852e57626eb82806:<path>`). Odoo 13 / Python 3.7; follow `AGENTS.md`.

## Problem and intent

Support OAuth client authentication methods `client_secret_basic` and `client_secret_post` at the token endpoint, distinct from OAuth grant types. RFC 6749 §2.3.1 explicitly specifies HTTP Basic client authentication and permits client credentials in the request body when Basic is unavailable/unsupported, while requiring the server to support the Basic method. It also says a client MUST NOT use more than one authentication method in a request. This feature should authenticate the client without broadening grant dispatch, grant policy, issuance or refresh semantics.

## Verified source/call-flow

- `amr_token/controllers/main.py:56-63`: sole baseline `/oidc/token` route; POST/http, auth none, csrf false; calls `amr.token.helper.sudo().oidc_token(**kwargs)` and serializes result.
- `amr_oidc/controllers/main.py:4-8`: OIDC controller subclasses the `amr_token` `ControllerToken`. It does not override `/oidc/token` in baseline. **Ownership sequencing is a hard dependency:** ADDONS13-38 (In Progress) owns migration of every OIDC endpoint from `amr_token` to `amr_oidc`, including Discovery/deprecation decisions. Coordinate whether this feature waits for that migration or is explicitly sequenced against the resulting token route; no second route/duplicate registration.
- `amr_oidc/models/token_helper.py:28-30` defines `amr.oidc.helper`; `:147-152` default `oidc_token` rejects grants; `:14-16` extension class inherits that model; `:74-115` client-credentials handler currently accepts Basic or form client credentials, then invokes credential checking and token creation. It is a grant handler, not a generic authentication boundary; do not extend grant dispatch as a side effect.
- `amr_oidc/models/token_helper.py:31-45` parses Basic header with base64 decode/split-first-colon; malformed data returns `(None,None)`. `:47-72` password grant has separate client credential handling. This is not yet a shared, RFC-conformant token-endpoint authenticator.
- `amr_oidc/models/oidc_client.py:49-54` stores restricted `client_secret_hash`, and default `authentication_method` is `client_secret`; `:72-86` verifies PBKDF2-SHA512 hash; `:127-142` `client_auth` decodes Basic credential and looks up active client. `amr_oidc/tests/test_client_secret_verifier.py:28-65` tests verifier/access restrictions and existing Basic helper, not token-route method semantics.
- `amr_oidc/models/helper.py:28-30` declares base helper; `:81-94` has another Basic parser. `amr_oidc/models/token_helper.py:14-16` extends helper. Existing parser duplication raises method/ownership ambiguity; proposal is one well-defined client-auth operation at the token request boundary, not copying parser logic.
- `amr_oidc/__manifest__.py:12-15` depends on `amr_token` and declares pyjwt/cryptography.

## Proposed decision (requires Lead/Owner acceptance)

1. Implement support limited to `client_secret_basic` and `client_secret_post` for client authentication at `/oidc/token`, using existing stored client verifier and configured authentication method where its meaning is confirmed.
2. Treat these as authentication methods, never grant types. Authenticate/reject before grant dispatch; preserve existing grant dispatch and response/issuance behavior for authenticated requests.
3. Reject ambiguous requests that supply credentials by multiple methods (RFC 6749 §2.3.1); normalize credential failures to a non-secret OAuth error response. Never expose/log secret, Basic header, decoded credentials or verifier.
4. Scope does not include RFC 8414 metadata: no discovery/metadata change is proposed. Discovery decisions belong to ADDONS13-38. This exclusion does not decide future metadata advertisement.
5. Route ownership/sequencing must be explicitly agreed with ADDONS13-38 before implementation; do not create/modify issues in this analysis.

## Assumptions / open decisions

- Confirm `authentication_method` is intended to select client authentication method and whether existing value `client_secret` maps to Basic, backward-compatible behavior, or neither. Do not silently reinterpret persisted configuration.
- Confirm whether `client_secret_post` should be accepted only when explicitly selected, and whether `client_secret_basic` is required/default under RFC expectations; migration/backward-compatibility policy needs Owner decision.
- Define OAuth error/status mapping for missing, malformed, unknown/inactive client, invalid secret, mismatched method, duplicate credential channels, and unsupported auth method. RFC error semantics and existing application conventions must be reconciled.
- Clarify whether URL-encoded form parsing is already guaranteed for `type='http'`; reject query-string credentials and avoid consuming credentials from unintended request locations.
- Confirm UTF-8 and percent-decoding behavior, colon-containing secrets, plus/space handling, duplicate form parameters, and Basic base64 strictness.
- Confirm behavior when client has no stored secret hash, `is_confidential=False`, or method is `private_key_jwt` / `tls_client_auth` (out of implementation scope unless separately approved).

## Scope

- Parse/validate the two named client-auth methods at one token endpoint boundary.
- Resolve active client and verify secret using existing hash verifier.
- Prevent authentication ambiguity, credential-channel confusion and secret disclosure.
- Add isolated unit/integration coverage for accepted and rejected authentication cases and route registration.

## Exclusions

No grant dispatch/policy/catalog changes; no refresh changes; no token issuance semantics; no Discovery edits or RFC 8414 metadata; no authorization-code lifecycle; no private_key_jwt/TLS authentication; no secret-management UI/storage redesign; no endpoint migration itself. Any minimum implementation touching endpoint ownership requires separate Lead/Owner agreement with ADDONS13-38 first.

## Dependencies and sequencing

- ADDONS13-38 endpoint ownership migration (In Progress): blocking coordination for `/oidc/token`; one owner/one route. Agree which worktree/change lands first, and rebase/evidence SHA after that change before implementation.
- Existing `oidc.client` hash field and verifier, Odoo request form/header parsing, and test infrastructure.
- Lead/Owner decision on mapping legacy `client_secret`, default method, errors, and supported client types.

## Security, compatibility, risks, rollback

- RFC 6749 §2.3.1: client password in Basic or request body; body method only when Basic unavailable/unsupported; do not use multiple methods in one request. The feature must not mistake `grant_type` for `client_authentication_method`.
- Use hash verification, active-client lookup, constant-time/framework verifier; never persist or log plaintext credentials. Keep request body/query/header out of logs and error descriptions. Avoid permissive base64 / split behavior creating credential confusion; correctly split credentials at first colon after decoding.
- Risk: current default `client_secret` lacks clear Basic-vs-post semantics. Existing callers using form fields may break if selected method is enforced. Compatibility strategy must be explicit, tested, and never weaken method exclusivity.
- Risk: extending inherited controller may register duplicate route or leave `amr_token` as owner during ADDONS13-38 transition. Verify route registry once and method dispatch.
- Rollback: revert only the isolated auth-boundary change and its tests, restoring baseline `/oidc/token` behavior at the agreed owner. Do not revert ADDONS13-38 endpoint migration; coordinate rollback ordering. No DB migration is currently proposed; if implementation later needs one, stop for separate approval/rollback plan.

## Test matrix (proposed; not executed)

| Area | Cases |
|---|---|
| Basic | valid active client/hash; wrong secret; malformed base64; missing scheme/credentials; colon in secret; inactive/unknown client |
| Post | valid form credentials; wrong/missing client/secret; query-string credentials rejected; malformed/duplicate form parameters |
| Exclusivity | Basic + body credentials rejected; Basic + conflicting client ID rejected; unrelated grant parameters unaffected |
| Configuration | each explicitly supported configured method; legacy `client_secret`, public client, absent hash, unsupported method per accepted policy |
| Boundary | POST token route only; GET and neighboring OIDC routes unchanged; exactly one `/oidc/token` route and expected controller owner after sequencing |
| Security | no plaintext/hash/header/body secret in response, application logs, or normal persisted fields; uniform failure behavior where approved |
| Compatibility | existing grant behavior unchanged for authenticated valid requests; no grant support added; Python 3.7/Odoo 13 |

## Exact proposed acceptance criteria (all require approval)

- **AC-1** A single POST `/oidc/token` route at the explicitly agreed owner accepts valid `client_secret_basic` credentials for an active configured client whose secret verifies against existing protected hash.
- **AC-2** The same boundary accepts valid `client_secret_post` credentials only when that method is configured/selected according to the approved legacy/default policy.
- **AC-3** Invalid, missing, malformed, unknown, inactive, or unverified credentials are rejected before grant dispatch; response status/error exactly matches the separately approved mapping and discloses no credential/verifier.
- **AC-4** A request presenting more than one client-authentication method, or conflicting identities across channels, is rejected; it cannot fall through to another method.
- **AC-5** Credentials are read only from the approved header/form locations; query credentials are rejected; parser behavior for encoding, colon and duplicate parameters matches approved rules.
- **AC-6** Plaintext secret, Authorization header, decoded Basic value and verifier do not appear in response or application logs; stored verifier remains restricted and hashed.
- **AC-7** Authenticated requests preserve existing grant dispatch/token issuance semantics; this change adds no grant, refresh, metadata, discovery, or authorization-code behavior.
- **AC-8** Route registry evidence demonstrates exactly one POST `/oidc/token` route, at agreed owner, with no method confusion/duplicate registration; other route ownership remains under ADDONS13-38.
- **AC-9** Tests and supported code remain compatible with Odoo 13 and Python 3.7.

**Status:** proposed only. No AC accepted; implementation not authorized. No tests/runtime/database/review/Plane action performed.