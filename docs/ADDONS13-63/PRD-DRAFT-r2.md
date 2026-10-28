# ADDONS13-63 — PRD-DRAFT r2

**Status and provenance:** Candidate revised full draft reflecting the Owner-approved narrow POST `/oidc/token` route transfer from `amr_token` to `amr_oidc`, plus previously approved authentication requirements. The previously approved PRD/UAT files are preserved unchanged by this task. The exact r2 file hashes have **not** yet been approved. This document is not new implementation authorization. Candidate repository HEAD at preparation: `7ecf5147811ba4a90616f74c6161739fc799394a` (branch `ADDONS13-63`). Worktree already contained task files modified/untracked before this revision; no commit or push is made. Candidate auth suite provenance: it previously ran 11 tests with 1 known failure (malformed form returned HTTP 400, expected 401). No test of this proposed route transfer has run.

## Problem and intent

Implement token-endpoint client authentication for `client_secret_basic` and `client_secret_post` while transferring ownership of exactly the POST `/oidc/token` route from `amr_token` to `amr_oidc`. Preserve the existing returned payload and HTTP semantics for grant dispatch, including the unsupported grant response represented as a returned dictionary (`{status:400,error:'unsupported_grant_type'}`); do not refactor that return into an exception. Authentication failures follow the separately approved auth contract below.

## Scope and boundaries

- Only the effective POST `/oidc/token` route transfers from `amr_token` to `amr_oidc` in ADDONS13-63.
- The effective route must be owned by `amr_oidc`; `amr_token` must no longer register that route. Exactly one effective matching route is permitted.
- Preserve route path, type, HTTP method, auth, and CSRF settings exactly: `/oidc/token`, `http`, POST, `auth='none'`, `csrf=False`.
- The OIDC-owned handler must dispatch to the intended OIDC helper/handler. Prove dispatch with a sentinel HTTP integration test, not merely source inspection or controller inheritance.
- All other OIDC routes, including JWKS, introspection, profile, authorization, discovery, and any other existing endpoint, remain unchanged in path, owner, method, type, auth, CSRF, and behavior. Their transfer is assigned to ADDONS13-38 and is outside this feature.
- Authentication payload/error requirements below are independent of route ownership. Transferring route ownership must not alter grant dispatch or existing returned payload/HTTP behavior.
- No grant additions, refresh changes, token issuance redesign, metadata/discovery changes, authorization-code lifecycle work, private_key_jwt/TLS authentication, or secret-storage/UI redesign.

## Owner-approved authentication requirements

1. Existing `authentication_method='client_secret'` remains backward-compatible and accepts either HTTP Basic or form-body credentials, but exactly one method per request. Explicit `client_secret_basic` and `client_secret_post` values accept only their corresponding channel. Do not migrate or reinterpret existing records.
2. Authentication failures return OAuth `invalid_client` with HTTP 401. Basic authentication failures include a `WWW-Authenticate: Basic` challenge. Never echo credentials or verifier.
3. Authentication methods are not grant types. Reject requests using multiple credential channels or conflicting client identities before grant dispatch. Do not alter grant dispatch.
4. Use existing active-client lookup and protected hash verifier; do not store plaintext secrets.
5. Basic credentials follow RFC 6749 §2.3.1 form-encoding rules before HTTP Basic encoding and split decoded pair at the first colon. `client_secret_post` reads only form-urlencoded body fields. Never accept credentials from query parameters. Reject malformed encoding, malformed Basic payloads, duplicate credential fields, and dual methods without fallback.
6. Only clients capable of secret authentication with an existing valid verifier can authenticate by these methods. Other authentication methods and OAuth grants remain unchanged/out of scope.
7. Apply the OAuth error mapping consistently; Basic challenge only for Basic requests.
8. Preserve the existing returned-dictionary unsupported-grant behavior and resulting HTTP semantics; it is not an exception and must not be refactored to one.

## Compatibility consequence

Installations that have only `amr_token` will no longer expose `/oidc/token` after this route transfer. To receive `/oidc/token`, they must install `amr_oidc`, which depends on `amr_token`. No dual-route or compatibility route is proposed or implied. A different safe compatibility path may be specified only if an actual code finding establishes it; none is asserted here.

## Acceptance criteria

- **AC-1 — Basic authentication:** The effective POST `/oidc/token` route accepts valid Basic credentials for an active configured client using existing protected hash verification when the client's method is `client_secret_basic` or legacy `client_secret`.
- **AC-2 — Form authentication:** The same route accepts valid form-urlencoded body credentials when the method is `client_secret_post` or legacy `client_secret`; explicit method values accept only their named channel.
- **AC-3 — Authentication rejection:** Missing, malformed, unknown, inactive, unsupported-method, or invalid credentials fail before grant dispatch with OAuth `invalid_client`, HTTP 401, and no credential/verifier disclosure. Basic failures include `WWW-Authenticate: Basic`.
- **AC-4 — Exclusive credential method:** Requests using both Basic and body credentials, duplicate credential keys, or conflicting client identities are rejected without fallback.
- **AC-5 — Credential locations/parsing:** Credentials are read only from Authorization header or form-urlencoded body, never URL query parameters; encoding and malformed input follow the rules above.
- **AC-6 — Secret safety:** Plaintext secret, Authorization header, decoded Basic value, and verifier do not appear in response or application logs; stored verifier remains restricted and hashed.
- **AC-7 — Auth payload and grant compatibility:** Authenticated requests preserve existing grant dispatch, token issuance, returned payload, and HTTP semantics. In particular, unsupported grant continues to return the existing status/error dictionary and is not converted to an exception. No grant, refresh, metadata, discovery, or authorization-code behavior is added.
- **AC-8 — Route registry and unchanged neighbors:** Exactly one effective POST `/oidc/token` route exists, owned by `amr_oidc`, with no registration in `amr_token`; path/type/method/auth/CSRF are unchanged. All other OIDC/JWKS/introspection/profile/authorization routes remain unchanged and assigned to ADDONS13-38 where applicable.
- **AC-9 — Runtime compatibility:** Tests and supported code remain compatible with Odoo 13 and Python 3.7.
- **AC-10 — Route dispatch and installation compatibility:** A sentinel HTTP integration test proves the OIDC helper/handler is called. An `amr_token`-only installation no longer exposes `/oidc/token`; installing `amr_oidc` (which depends on `amr_token`) exposes the single OIDC-owned route. Do not provide or imply dual-route support.

## Test and evidence requirements

Use isolated synthetic clients and secrets only. Route evidence must include effective Odoo route registration and HTTP sentinel dispatch. Compare the non-token route inventory before/after and verify unchanged owner and route metadata. Test returned payload/HTTP semantics for unsupported grants as a returned dictionary, not an exception. Static route search alone is insufficient to establish effective ownership or dispatch. No runtime or test execution is claimed in this draft.

## Provenance and authorization boundary

The earlier approved drafts remain at `docs/ADDONS13-63/PRD-DRAFT.md` and `docs/ADDONS13-63/UAT-DRAFT.md`; this revision creates separate r2 files. The prior candidate auth suite result is provenance only: 11 tests ran, with one known failure (malformed form HTTP 400 versus expected 401). No proposed route-transfer test has run. All UAT cases remain NOT RUN. Exact r2 file hashes are not yet approved, and this document does not grant new implementation authorization.
