# ADDONS13-63 — PRD-DRAFT r3

**Status and provenance:** Full candidate revision of the r2 draft, adding the Owner-authorized local server-wide bootstrap requirement for safe malformed form handling. It preserves the previously approved PRD/UAT documents and the r2 drafts unchanged. This r3 document remains a draft. The described local implementation and isolated tests are separately user-authorized; this does not authorize external Odoo configuration, commit/push, deployment, or Plane changes. No bootstrap validation is claimed. Repository HEAD at preparation: `7ecf5147811ba4a90616f74c6161739fc799394a` (branch `ADDONS13-63`). Existing worktree changes are preserved; no code/config/tests/runtime/DB/Plane changes, commit, push, or deployment are part of this documentation task.

## Problem and intent

Implement token-endpoint client authentication for `client_secret_basic` and `client_secret_post` while transferring ownership of exactly POST `/oidc/token` from `amr_token` to `amr_oidc`. Preserve existing returned payload and HTTP semantics for grant dispatch, including unsupported grant as a returned status/error dictionary (`{'status':400,'error':'unsupported_grant_type',...}`), not an exception. Authentication failures follow the approved auth contract below.

## Scope and boundaries

- Only the effective POST `/oidc/token` route transfers from `amr_token` to `amr_oidc`; exactly one effective matching route is permitted.
- Preserve path, type, method, auth, and CSRF settings exactly: `/oidc/token`, `http`, POST, `auth='none'`, `csrf=False`.
- The OIDC-owned handler dispatches to the intended OIDC helper/handler; prove with sentinel HTTP integration, not source inspection alone.
- All other OIDC routes (including JWKS, introspection, profile, authorization, discovery, and any existing endpoint) remain unchanged in path, owner, method, type, auth, CSRF, and behavior. Their transfer is assigned to ADDONS13-38 and is outside scope.
- Authentication and malformed-form handling must not change grant dispatch or existing returned payload/HTTP behavior.
- No grant additions, refresh changes, token issuance redesign, metadata/discovery changes, authorization-code lifecycle work, private_key_jwt/TLS authentication, or secret-storage/UI redesign.

## Owner-approved authentication requirements

1. Existing `authentication_method='client_secret'` remains backward-compatible and accepts either HTTP Basic or form-body credentials, exactly one method per request. Explicit `client_secret_basic` and `client_secret_post` accept only their corresponding channel. Do not migrate or reinterpret existing records.
2. Authentication failures return OAuth `invalid_client`, HTTP 401. Basic authentication failures include `WWW-Authenticate: Basic`. Never echo credentials or verifier.
3. Authentication methods are not grant types. Reject multiple credential channels or conflicting client identities before grant dispatch. Do not alter grant dispatch.
4. Use existing active-client lookup and protected hash verifier; never store plaintext secrets.
5. Basic credentials follow RFC 6749 §2.3.1 form-encoding rules before HTTP Basic encoding and split the decoded pair at the first colon. `client_secret_post` reads only form-urlencoded body fields. Never accept credentials from query parameters. Reject malformed encoding, malformed Basic payloads, duplicate credential fields, and dual methods without fallback.
6. Only clients capable of secret authentication with an existing valid verifier authenticate by these methods. Other authentication methods and OAuth grants remain unchanged/out of scope.
7. Apply OAuth error mapping consistently; Basic challenge only for Basic requests.
8. Preserve unsupported-grant behavior as a returned dictionary and resulting HTTP semantics; do not refactor it into an exception.

## Raw-form bootstrap requirement (Owner-authorized local design)

Odoo 13's `HttpRequest` accesses parsed form data during request construction. To classify malformed percent escapes consistently before that parse can produce a generic HTTP 400, a minimal separate bootstrap addon (proposed name `amr_oidc_token_raw_form`) must wrap the version-pinned `Root.get_request` pre-dispatch boundary. It caches/inspects the raw request body only when the request is POST `/oidc/token` with form-urlencoded content type, before Odoo parses it. The wrapper must be guarded and idempotent, verify the original method signature, and leave non-target requests untouched. It must distinguish a malformed raw `%` escape (e.g. `%ZZ`) from a valid literal-percent value encoded as `%25ZZ`; the former maps to JSON `invalid_client`/401, while the latter remains a valid decoded credential value and proceeds through normal auth/grant handling. No request body, secret, Authorization header, or verifier may be logged.

The bootstrap addon must be activated operationally through Odoo `server_wide_modules` / `--load` (including `amr_oidc_token_raw_form`) so it is loaded before the first HTTP request. Disposable tests may load the addon with CLI `--load=...,amr_oidc_token_raw_form`; this does not modify external Odoo configuration. Production/server `server_wide_modules` activation remains a prerequisite and is not changed or deployed now. Ordinary import of `amr_oidc` alone is not a substitute for guaranteed first-request timing. The server-wide activation prerequisite must be explicitly met and verified before production use; no external configuration or deployment is authorized here.

## Compatibility consequence

Installations with only `amr_token` will no longer expose `/oidc/token` after route transfer. To receive it they must install `amr_oidc`, which depends on `amr_token`. No dual-route or compatibility route is proposed or implied.

## Acceptance criteria

- **AC-1 — Basic authentication:** Effective POST `/oidc/token` accepts valid Basic credentials for an active configured client using existing protected hash verification for `client_secret_basic` or legacy `client_secret`.
- **AC-2 — Form authentication:** The endpoint accepts valid form-urlencoded body credentials for `client_secret_post` or legacy `client_secret`; explicit values accept only their named channel.
- **AC-3 — Authentication rejection:** Missing, malformed, unknown, inactive, unsupported-method, or invalid credentials fail before grant dispatch with OAuth `invalid_client`, HTTP 401, and no credential/verifier disclosure. Basic failures include `WWW-Authenticate: Basic`.
- **AC-4 — Exclusive credential method:** Requests using both Basic and body credentials, duplicate credential keys, or conflicting client identities are rejected without fallback.
- **AC-5 — Credential locations and parsing:** Credentials come only from Authorization header or form-urlencoded body, never query parameters. Correctly encoded literal percent data (including `%25ZZ`) is not mistaken for a malformed escape. Malformed raw form escapes (including `%ZZ`) are handled as `invalid_client`/401 JSON before generic Odoo form parsing; valid form data and Basic decoding follow the specified rules.
- **AC-6 — Secret safety:** Plaintext secret, Authorization header, decoded Basic value, raw request body, and verifier do not appear in response or application logs; stored verifier remains restricted and hashed.
- **AC-7 — Auth payload and grant compatibility:** Authenticated requests preserve existing grant dispatch, token issuance, returned payload, and HTTP semantics. Unsupported grant remains the returned status/error dictionary and is not converted to an exception. No grant, refresh, metadata, discovery, or authorization-code behavior is added.
- **AC-8 — Route registry and unchanged neighbors:** Exactly one effective POST `/oidc/token` route exists, owned by `amr_oidc`, none in `amr_token`; path/type/method/auth/CSRF are unchanged. Other OIDC routes remain unchanged and assigned as specified.
- **AC-9 — Runtime compatibility:** Supported code/tests remain compatible with Odoo 13 and Python 3.7. The bootstrap is version-pinned, signature-checked, guarded, and idempotent.
- **AC-10 — Route dispatch and installation compatibility:** Sentinel HTTP integration proves OIDC helper dispatch. `amr_token`-only installation does not expose the route; `amr_oidc` plus dependency does. No dual-route support.
- **AC-11 — Bootstrap startup, signature, and idempotence:** In an isolated test process loaded with CLI `--load=...,amr_oidc_token_raw_form`, the bootstrap loads before HTTP handling, verifies the pinned original signature, installs a guarded/idempotent wrapper, and leaves non-target requests untouched. Production/server-wide activation remains an external prerequisite and is not changed or deployed here.
- **AC-12 — Target-only malformed form behavior:** Only target POST `/oidc/token` form-urlencoded malformed raw `%ZZ` returns JSON `invalid_client`/401 before generic parsing; `%25ZZ` is valid encoded literal data and proceeds through normal handling. Non-target requests remain unchanged.

## Test and evidence requirements

Use isolated synthetic clients/secrets only. Verify effective Odoo route registration and sentinel dispatch; compare non-token route inventory and metadata. Exercise malformed `%ZZ` versus valid literal-percent `%25ZZ`, valid form/Basic, non-target paths and non-form content types. Assert unsupported grant as a returned dictionary and resulting HTTP behavior, not exception. Validate bootstrap activation order and signature against the pinned Odoo 13 runtime before any PASS. No bootstrap validation has run for this draft. Disposable isolated tests may explicitly load the addon with CLI `--load=...,amr_oidc_token_raw_form`; production/server-wide activation is a separate prerequisite. The prior focused HTTP suite ran 12 tests: 11 passed and one failed (`test_rejects_malformed_form_percent_escape_even_with_valid_client`, actual HTTP 400 versus expected 401). This known failure is not resolved or retested here.

## Risks, rollback, and authorization boundary

The narrow `Root.get_request` monkey patch is intentionally version-pinned and carries Odoo upgrade/interaction risk; validate original signature and ordering on the exact supported runtime, assert idempotence, and monitor only sanitized outcomes. If unsafe or incompatible, remove the bootstrap addon from external `server_wide_modules` / `--load` and restart Odoo; this disables the preparse behavior. Do not claim malformed-form acceptance until runtime evidence passes. The previously approved PRD/UAT and r2 files remain preserved. These r3 documents remain drafts. The described local implementation and isolated tests are separately user-authorized; no external Odoo configuration, database/runtime activity beyond disposable tests, Plane updates, commit/push, or deployment is authorized.