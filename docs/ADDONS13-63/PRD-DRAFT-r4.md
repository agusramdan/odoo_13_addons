# ADDONS13-63 — PRD-DRAFT r4

**Status and provenance:** Current candidate draft superseding r3 for review. The earlier approved PRD/UAT files and r2/r3 drafts remain unchanged; r2/r3 are historical drafts and do not describe the current candidate scope. The direct Owner scope update cancels `client_secret_post` and requires Basic-only client authentication. The existing `authentication_method='client_secret'` is retained as a Basic-only backwards-compatibility alias; this is an implementation assumption based on the existing field default (`amr_oidc/models/oidc_client.py:50-54`), not a separate Owner decision. No auth migrations. This documentation task makes no source, test, runtime, database, configuration, Plane, commit, push, or deployment changes. Local code/tests were authorized separately; no external configuration, commit/push, deployment, or Plane updates are authorized. Repository HEAD at preparation: `7ecf5147811ba4a90616f74c6161739fc799394a` on `ADDONS13-63`; pre-existing dirty candidate changes are preserved.

## Problem and intent

Transfer only POST `/oidc/token` from `amr_token` to `amr_oidc` and enforce Basic-only token endpoint client authentication. Do not support or offer `client_secret_post`. Preserve existing grant dispatch, returned payloads, and HTTP semantics, especially unsupported grant as the existing returned status/error dictionary rather than an exception.

## Scope and boundaries

- Transfer exactly POST `/oidc/token` to `amr_oidc`, preserving `/oidc/token`, `type='http'`, POST, `auth='none'`, and `csrf=False`.
- The OIDC-owned handler dispatches to the intended OIDC helper/handler; verify by sentinel HTTP integration.
- Other OIDC routes (JWKS, introspection, profile, authorization, discovery, and any existing endpoint) remain unchanged in path, owner, method, type, auth, CSRF, and behavior. Their transfer is assigned to ADDONS13-38 and out of scope here.
- Only HTTP Basic credentials are accepted, for explicit `client_secret_basic` and legacy `client_secret`. The latter remains a Basic-only alias as the assumption stated above. Body credentials are rejected for both values. `client_secret_post` is not offered or accepted.
- No auth migrations. Do not add a server-wide `Root.get_request` hook, bootstrap addon, or external configuration. Since body credentials are rejected, the prior malformed-body authentication scenario no longer requires a preparse interceptor. Ordinary Odoo form parsing/HTTP behavior for malformed non-credential bodies with valid Basic is out of scope; do not promise to remap parser errors to `invalid_client`.
- No grant additions, refresh changes, token issuance redesign, metadata/discovery changes, authorization-code lifecycle work, private_key_jwt/TLS authentication, or secret-storage/UI redesign.

## Authentication requirements

1. Accept valid HTTP Basic credentials for active clients configured with `client_secret_basic` or legacy `client_secret` (Basic-only alias assumption). Use existing active-client lookup and protected hash verifier. Never store plaintext secrets.
2. Reject Basic attempts with OAuth `invalid_client`, HTTP 401, and `WWW-Authenticate: Basic`; do not disclose credentials or verifier.
3. Reject body credentials for both `client_secret_basic` and legacy `client_secret`. Do not offer or accept `client_secret_post` in method selection.
4. Authentication methods are not grant types. Reject missing, malformed, unknown, inactive, unsupported-method, invalid, duplicate, partial, mixed, or conflicting credentials before grant dispatch, without fallback.
5. Never accept credentials from query parameters. Basic credentials follow RFC 6749 §2.3.1 form-encoding rules before HTTP Basic encoding and split the decoded pair at the first colon. Use request `httprequest.mimetype` (derived from headers) when content-type evaluation is needed; do not compare raw header text in a way that breaks casing/charset parameters.
6. Preserve unsupported-grant behavior as a returned status/error dictionary and resulting HTTP mapping; do not convert it into an exception.

## Compatibility consequence

Installations with only `amr_token` will no longer expose `/oidc/token` after transfer. To receive it they must install `amr_oidc`, which depends on `amr_token`. No dual-route or compatibility route is proposed or implied.

## Acceptance criteria

- **AC-1 — Basic success and compatibility alias:** Valid Basic credentials authenticate active clients configured as `client_secret_basic` and legacy `client_secret`, using the existing protected hash verifier. Legacy mode accepts Basic only; no migration occurs.
- **AC-2 — Basic failure and challenge:** Invalid/missing/malformed Basic, unknown or inactive client, unsupported method, and invalid verifier fail before grant dispatch as `invalid_client`/401 with `WWW-Authenticate: Basic`; no secret/verifier disclosure.
- **AC-3 — Body rejection and Post exclusion:** Body credentials are rejected for `client_secret_basic` and legacy `client_secret`; `client_secret_post` is not offered in selection and is not accepted.
- **AC-4 — Credential ambiguity and locations:** Reject query-only credentials, mixed Basic/body, duplicate or partial credentials, and conflicting client identities without fallback or grant dispatch.
- **AC-5 — Basic decoding and content type:** Basic form-encoding/decoding follows the stated rules, including splitting at the first colon. Content-type inspection uses normalized `httprequest.mimetype` as appropriate. No malformed raw form-to-401 contract is imposed; ordinary Odoo parser behavior remains out of scope.
- **AC-6 — Secret safety:** Plaintext secret, Authorization header, decoded Basic value, and verifier do not appear in responses or application logs; stored verifier remains hashed and restricted.
- **AC-7 — Grant compatibility:** Authenticated requests preserve existing grant dispatch, token issuance, returned payload, and HTTP semantics. Unsupported grant remains the returned status/error dictionary and is not converted to an exception. No grant/refresh/metadata/discovery/authorization-code behavior is added.
- **AC-8 — Route registry and unchanged neighbors:** Exactly one effective POST `/oidc/token` route exists, owned by `amr_oidc`, none in `amr_token`; path/type/method/auth/CSRF are unchanged. Other OIDC routes remain unchanged.
- **AC-9 — Runtime compatibility:** Supported code/tests remain compatible with Odoo 13 and Python 3.7; no global hook/bootstrap is required.
- **AC-10 — Route dispatch and installation compatibility:** Sentinel HTTP integration proves OIDC helper dispatch. `amr_token`-only installation does not expose the route; `amr_oidc` plus dependency does. No dual-route support.

## Test and evidence requirements

Use isolated synthetic clients/secrets only. Verify effective Odoo route registration and sentinel dispatch; compare non-token route inventory/metadata. Exercise Basic success for both configured methods, all specified rejection and body-channel cases, safe logging/storage, and unsupported-grant returned-value/HTTP behavior. Do not add a malformed `%ZZ`-to-401 parser requirement or a preparse hook. Historical focused HTTP test provenance under superseded Post-support behavior: 12 tests, 11 passed and 1 failed (`test_rejects_malformed_form_percent_escape_even_with_valid_client`, actual HTTP 400 vs expected 401); this does not establish failure of the revised body-rejection contract. No r4 UAT has been executed.

## Risks, rollback, and authorization boundary

The legacy `client_secret` alias interpretation is a documented implementation assumption and should be confirmed in review. The previously approved PRD/UAT and r2/r3 files remain preserved; r2/r3 remain historical drafts. All r4 cases are unexecuted. Local code/tests were authorized separately, but this document does not authorize external configuration, commit/push, deployment, or Plane updates. No server-wide monkey patch or bootstrap activation/deployment requirement remains in r4.
