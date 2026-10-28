# ADDONS13-63 — PRD-DRAFT (UPDATED TO LATEST AGREED STEP 0 REQUIREMENTS)

**Provenance:** Owner approved Step 0 requirements on 2026-10-27 CST against the earlier PRD draft SHA-256 `2bd6ebd045e25cdb2f61dfad5e65afc31794c8e57d413248b8c87d33b678315c`. The additional Owner clarifications recorded below were received after that approval, and these documents were then revised to reflect the latest agreed requirements. No approval of the exact SHA of these revised documents is asserted. Approval is scoped to Step 0 requirements only; it is not a waiver, risk acceptance, or authorization beyond the Owner's separate instruction to continue Steps 1–4. **Baseline:** repository `/home/ubuntu/worktrees/ADDONS13-63-analysis`; detached HEAD and `origin/main` = `c08b050cfd85ccc5c705eb92852e57626eb82806`; clean before draft. All source evidence below is line-bound to that SHA (use `git show c08b050cfd85ccc5c705eb92852e57626:<path>`). Odoo 13 / Python 3.7; follow `AGENTS.md`.

## Problem and intent

Support OAuth client authentication methods `client_secret_basic` and `client_secret_post` at the token endpoint, distinct from OAuth grant types. RFC 6749 §2.3.1 explicitly specifies HTTP Basic client authentication and permits client credentials in the request body when Basic is unavailable/unsupported, while requiring the server to support the Basic method. It also says a client MUST NOT use more than one authentication method in a request. This feature should authenticate the client without broadening grant dispatch, grant policy, issuance or refresh semantics.

## Verified source/call-flow

- `amr_token/controllers/main.py:56-63`: sole baseline `/oidc/token` route; POST/http, auth none, csrf false; calls `amr.token.helper.sudo().oidc_token(**kwargs)` and serializes result.
- `amr_oidc/controllers/main.py:4-8`: OIDC controller subclasses the `amr_token` `ControllerToken`. It does not override `/oidc/token` in baseline. This Feature does not change controller/route ownership: it targets the helper/model authentication path behind the current effective route. Coordinate with ADDONS13-38, which owns endpoint migration, so the route move preserves this behavior; no second route/duplicate registration.
- `amr_oidc/models/token_helper.py:28-30` defines `amr.oidc.helper`; `:147-152` default `oidc_token` rejects grants; `:14-16` extension class inherits that model; `:74-115` client-credentials handler currently accepts Basic or form client credentials, then invokes credential checking and token creation. It is a grant handler, not a generic authentication boundary; do not extend grant dispatch as a side effect.
- `amr_oidc/models/token_helper.py:31-45` parses Basic header with base64 decode/split-first-colon; malformed data returns `(None,None)`. `:47-72` password grant has separate client credential handling. This is not yet a shared, RFC-conformant token-endpoint authenticator.
- `amr_oidc/models/oidc_client.py:49-54` stores restricted `client_secret_hash`, and default `authentication_method` is `client_secret`; `:72-86` verifies PBKDF2-SHA512 hash; `:127-142` `client_auth` decodes Basic credential and looks up active client. `amr_oidc/tests/test_client_secret_verifier.py:28-65` tests verifier/access restrictions and existing Basic helper, not token-route method semantics.
- `amr_oidc/models/helper.py:28-30` declares base helper; `:81-94` has another Basic parser. `amr_oidc/models/token_helper.py:14-16` extends helper. Existing parser duplication raises method/ownership ambiguity; proposal is one well-defined client-auth operation at the token request boundary, not copying parser logic.
- `amr_oidc/__manifest__.py:12-15` depends on `amr_token` and declares pyjwt/cryptography.

## Owner decisions — accepted 2026-10-27

The Owner approved the following decisions in direct response to Lead's three explicit clarification questions:

1. **Legacy method compatibility:** Existing `authentication_method='client_secret'` remains backward-compatible and accepts either HTTP Basic or form-body client credentials, but exactly one authentication method per request. Add explicit `client_secret_basic` and `client_secret_post` method selections; explicit values accept only their corresponding channel. Do not migrate/reinterpret existing records.
2. **Failure response:** Client-authentication failures return OAuth `invalid_client` with HTTP 401. For Basic authentication, return a `WWW-Authenticate: Basic` challenge. Never echo credentials or verifier.
3. **Endpoint sequencing:** Implement only in the helper/model authentication path used by the current effective token route. Do not edit controller routes or change route ownership. ADDONS13-38 remains responsible for endpoint migration and must preserve this behavior when it moves the route.
4. These are client-authentication methods, not grant types. Reject multiple credential channels or conflicting client identities. Keep Discovery/RFC 8414 metadata outside this Feature; no metadata change.

## Implementation constraints (resolved at Step 0)

- Use existing active-client lookup and protected hash verifier; do not store plaintext secrets.
- `client_secret_basic` follows RFC 6749 §2.3.1 form-encoding rules before HTTP Basic encoding and splits the decoded pair at the first colon. `client_secret_post` reads only form-urlencoded body fields. Never accept credentials from query parameters. Reject malformed encoding, malformed Basic payloads, duplicate credential fields, and dual methods without fallback.
- Keep the generic legacy `client_secret` alias compatible as described above; explicit selections must not silently fall back to the other channel.
- Only clients capable of secret authentication with an existing valid verifier can authenticate by these methods. Other authentication methods and OAuth grants remain unchanged/out of scope.
- Apply RFC error mapping above consistently and ensure the Basic challenge is emitted only for Basic requests.


## Scope

- Parse/validate the two named client-auth methods at one token endpoint boundary.
- Resolve active client and verify secret using existing hash verifier.
- Prevent authentication ambiguity, credential-channel confusion and secret disclosure.
- Add isolated unit/integration coverage for accepted and rejected authentication cases and route registration.

## Exclusions

No grant dispatch/policy/catalog changes; no refresh changes; no token issuance semantics; no Discovery edits or RFC 8414 metadata; no authorization-code lifecycle; no private_key_jwt/TLS authentication; no secret-management UI/storage redesign; no endpoint migration itself. This Feature must not change route ownership; coordinate the independent ADDONS13-38 migration to preserve this behavior.

## Dependencies and sequencing

- ADDONS13-38 endpoint ownership migration (In Progress): this Feature will not change controller/route ownership. Implement in the helper/model path behind the current effective route and coordinate with ADDONS13-38 so the route move preserves the same behavior; later integration must reverify the single effective route at its new owner.
- Existing `oidc.client` hash field and verifier, Odoo request form/header parsing, and test infrastructure. No DB migration is proposed.
- Owner decisions above resolve legacy compatibility, explicit method selection, error mapping, and sequencing.

## Security, compatibility, risks, rollback

- RFC 6749 §2.3.1: client password in Basic or request body; body method only when Basic unavailable/unsupported; do not use multiple methods in one request. The feature must not mistake `grant_type` for `client_authentication_method`.
- Use hash verification, active-client lookup, constant-time/framework verifier; never persist or log plaintext credentials. Keep request body/query/header out of logs and error descriptions. Avoid permissive base64 / split behavior creating credential confusion; correctly split credentials at first colon after decoding.
- Risk: existing generic `client_secret` records must remain backward-compatible while explicit Basic/Post values enforce their respective channels. Ensure the two credential channels are mutually exclusive per request.
- Risk: the current route is inherited from `amr_token`; this Feature must not register a duplicate or move route ownership. Verify effective route registration and model dispatch while leaving controllers unchanged.
- Rollback: revert only the isolated auth-boundary change and its tests, restoring baseline `/oidc/token` behavior. Do not revert ADDONS13-38 endpoint migration; coordinate rollback ordering. No DB migration is currently proposed; if implementation later needs one, stop for separate approval/rollback plan.

## Test matrix (proposed; not executed)

| Area | Cases |
|---|---|
| Basic | valid active client/hash; wrong secret; malformed base64; missing scheme/credentials; colon in secret; inactive/unknown client |
| Post | valid form credentials; wrong/missing client/secret; query-string credentials rejected; malformed/duplicate form parameters |
| Exclusivity | Basic + body credentials rejected; Basic + conflicting client ID rejected; unrelated grant parameters unaffected |
| Configuration | Legacy `client_secret` accepts either one channel; explicit `client_secret_basic` and `client_secret_post` accept only their named channel; unsupported methods fail `invalid_client` |
| Boundary | POST token route only; controller ownership/registration unchanged; exactly one inherited `/oidc/token` route; GET and neighboring OIDC routes unchanged |
| Security | no plaintext/hash/header/body secret in response, application logs, or normal persisted fields; Basic failure includes `WWW-Authenticate`; all auth failures return `invalid_client` / HTTP 401 |
| Compatibility | existing grant behavior unchanged for authenticated valid requests; no grant support added; Python 3.7/Odoo 13 |

## Accepted acceptance criteria (Owner decisions recorded above)

- **AC-1** The current effective POST `/oidc/token` route accepts valid Basic credentials for an active configured client using existing protected hash verification when the client's method is `client_secret_basic` or legacy `client_secret`.
- **AC-2** The same route accepts valid form-urlencoded body credentials when the method is `client_secret_post` or legacy `client_secret`; explicit method values accept only their named channel.
- **AC-3** Missing, malformed, unknown, inactive, unsupported-method, or invalid credentials fail before grant dispatch with OAuth `invalid_client`, HTTP 401, and no credential/verifier disclosure; Basic failures include `WWW-Authenticate: Basic`.
- **AC-4** Requests using both Basic and body credentials, duplicate credential keys, or conflicting client identities are rejected without fallback.
- **AC-5** Credentials are read only from the approved Authorization header or form-urlencoded body, never URL query parameters; form/Basic encoding and malformed input follow the accepted rules above.
- **AC-6** Plaintext secret, Authorization header, decoded Basic value and verifier do not appear in response or application logs; stored verifier remains restricted and hashed.
- **AC-7** Authenticated requests preserve existing grant dispatch/token issuance semantics; this change adds no grant, refresh, metadata, discovery, or authorization-code behavior.
- **AC-8** Route registry evidence demonstrates exactly one POST `/oidc/token` registration at the current effective owner; this Feature leaves controller/route ownership unchanged and coordinates future ownership movement with ADDONS13-38.
- **AC-9** Tests and supported code remain compatible with Odoo 13 and Python 3.7.

**Status:** Owner-approved Step 0 requirements and UAT plan. All tests/UAT remain NOT RUN. Owner has separately authorized Development Steps 1–4; no deployment is authorized.