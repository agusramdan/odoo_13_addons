# ADDONS13-46 — PRD DRAFT

**Status:** `DRAFT` · `acceptance=false` · Step 0 not accepted  
**Plane issue:** `ADDONS13-46` — Feature: Resolve amr_resource OIDC issuer and Discovery dependency  
**Issue UUID:** `0932b9ca-60ee-44b7-8c88-3e98a173b15b`  
**Captured:** 2026-10-23 · **Revision:** v4, Owner addon-boundary decision · **Artifact set:** this PRD, [`UAT-DRAFT.md`](UAT-DRAFT.md), [`LEAD-ANALYSIS.md`](LEAD-ANALYSIS.md), [`SOURCE-INVENTORY.md`](SOURCE-INVENTORY.md)

## 1. Problem and purpose

The pinned target contains `amr_resource` code that obtains OIDC Provider Configuration from `issuer + /.well-known/openid-configuration` for token generation, introspection, and asymmetric validation. The same target statically registers `/.well-known/openid-configuration` in `amr_oidc/controllers/main.py` with status 404; `amr_token/controllers/main.py` no longer registers that route. In the separate source snapshot, `amr_token/controllers/main.py` still registers it and delegates the response to `amr.token.helper.openid_configuration()`. This is a source-level cross-addon contract mismatch; it is **not** proof of a deployed/runtime failure.

The goal is an explicit issuer/trust contract **within addon `amr_resource` only**, including an issuer registration required before token acceptance, multiple registered audiences, optional `azp` checking, and issuer-specific user resolution. It should define the resource helper's behavior without changing other addons. This analysis does not implement or enable a route.

## 2. Goals and boundaries

### In scope for the proposed Development contract

- Define trusted issuer selection, cardinality, configuration semantics, and fallback behavior.
- Distinguish explicit Discovery mode from explicitly configured endpoint mode; reject unknown issuers before network activity.
- Trace token generation, introspection, JWT validation, local-token bypass, and authentication/user-mapping consumers.
- Specify the new `oidc.issuer.register` trust model, audience child records, optional `azp` policy, and per-issuer user-resolution modes.
- Specify profile/endpoint validation, bounded network behavior, compatibility, cache invalidation, and rollback considerations.
- Plan synthetic unit cases that call actual methods with network/JWK/ORM boundaries mocked.

This Feature owns only `amr_resource` source/target changes and tests. Compatibility work in another addon is tracked separately; a cross-link or related Feature does not block this Feature's gates unless an explicit dependency is accepted.

### Out of scope

- Changing `amr_oidc` Discovery route publication, grants, response types, authentication methods, or metadata. Keep those claims aligned with `ADDONS13-39`; no capability/metadata work is duplicated here.
- Implementing OAuth/OIDC flows, changing identity mapping outside the accepted issuer-registration contract, rotating secrets/keys, changing gateway/service configuration, or touching production.
- Executing tests, Odoo registry/HTTP/integration/UAT, external consumers, rollout, or rollback. Those require later explicit authorization and evidence.
- Treating source-only modules as installed/deployed. Their presence must be revalidated against the actual candidate and authorized QA module inventory.
- Changing `amr_token` overrides or its local generation/validation/introspection path; this scope is transferred to ADDONS13-38 ([Lead scope-transfer addendum](../../ADDONS13-38/analysis-20261023T141448Z-lead-scope-transfer-amr-token/SCOPE-TRANSFER-ADDENDUM.md)). The `amr_resource` base helper facts remain evidence, not authorization to edit `amr_token`.
- Changing `amr_oidc` route publication or Discovery/capability metadata; these remain with ADDONS13-38/ADDONS13-39. `amr_oidc` client token-validation compatibility is tracked in ADDONS13-48. No route, grant, metadata, or client-validation change is authorized here.
- Changing `amr_service_client` provider/cache behavior; this is tracked by ADDONS13-49.
- Changing source-only helper consumers (`amr_auto_login`, `amr_mobile`, `amr_oauth`, `amr_oidc_client`, `amr_resource_jwt`, `amr_signature`); these are tracked separately by ADDONS13-50 through ADDONS13-55, respectively. Static mentions are not evidence those addons are installed in the target.

## 3. Pinned evidence and current source behavior

Source snapshot: detached `6725f802acde636be0b25e2c140d15dccd37b0db`, clean. Target snapshot: local `main` `dae519f29e9c4709dc04796b38148b00d333c58b`, clean. These are local analysis pins; remote freshness and deployed code are not established. See `SOURCE-INVENTORY.md` for file hashes. The target's `amr_resource/models/helper.py` is byte-identical to the source snapshot.

### Owner scope inputs in this revision (not artifact acceptance)

- Owner selected multiple audiences as child records (`One2many`) under one issuer registration and accepted the proposed optional-`azp` handling: absence is allowed only when the token profile permits it; a present `azp` must match the configured authorized-party value. Exact profile-specific rules remain provisional.
- Owner requested three user-resolution capabilities: a fixed Odoo user, invoking a method on a selected model, and Python code stored on `oidc.issuer.register`. Through the follow-up choice, Owner selected stored Python as a **privileged code-execution feature requiring Security review**. This does not accept residual risk or claim `safe_eval` is a security boundary.
- Owner requests the existing `get_user_match` as an available resolver-method choice, displayed with the exact label `Default` (internal resolver key `get_user_match`). This records the method option and label; whether it is preselected for new/existing issuer records remains undecided. Its current matching and account-eligibility semantics are documented below and are not silently changed by the label.
- These are scope/design inputs, not acceptance of this PRD/UAT revision and not authority to modify source or tests.

The exact model name `oidc.issuer.register` was not found in either pinned snapshot's visible files; this design therefore adds a new model rather than extending an existing one.

### Configuration

- `amr_resource.get_issuer()` (`amr_resource/models/helper.py:24-27`) reads the **name of an `ir.config_parameter` key** from `amr_resource.issuer` (default `web.base.url`), then returns that parameter's value or silently falls back to `web.base.url`. It is not a typed multi-issuer registry.
- `get_audience()` (`:30-33`) uses analogous key indirection through `amr_resource.audience`; `get_audiences(issuer)` (`:36-37`) returns only that configured audience and ignores its `issuer` argument.
- `is_local_issuer(issuer)` (`:20-21`) compares only against `web.base.url`. `is_local_token()` (`:76-80`) decodes the JWT without signature verification to read `iss`, then uses that comparison to select a branch. Local cryptographic verification happens later in `amr_token`.

### Discovery-dependent paths

- `get_oidc_config(issuer)` (`:40-44`) performs `requests.get(issuer.rstrip('/') + '/.well-known/openid-configuration')`, raises on HTTP error, and returns JSON. There is no app-level metadata cache or timeout in this method.
- `generate_token()` (`:61-73`) chooses `iss or issuer or issuer_url`, fetches Discovery, takes `token_endpoint`, then sends optional client credentials. It does not first resolve the argument against `get_issuer()` or an issuer allowlist.
- `introspect_token()` (`:83-102`) accepts a direct `url` that bypasses Discovery; otherwise it accepts `iss`, or reads `iss` from an unverified token, then fetches Discovery and calls the resulting endpoint.
- `validate_hs()` (`:105-110`) uses introspection. The asymmetric branch in `validate()` (`:114-149`) reads `iss` from an unverified payload, fetches that issuer's metadata and JWKS, then verifies using the **same token-derived issuer**. The metadata response's `issuer` value is not checked against an independently selected trusted issuer in this method.

OIDC Discovery 1.0 defines the Provider Configuration document at the issuer-specific `/.well-known/openid-configuration` path and requires its issuer metadata to match the issuer used for retrieval.[1] This applies to OIDC Provider metadata; it does not make every generic resource access token an OIDC ID Token. The accepted contract must name the token profile for each caller before applying ID-Token-specific claims rules.

### Local issuer/token paths and consumers

- Target `amr_token/models/helper.py:39-61` overrides `amr.resource.helper` methods. Its local generation, validation, and override behavior are out of scope here and transferred to ADDONS13-38. For this Feature, inspect/alter only code owned by `amr_resource`; verify its base-helper contract without claiming the effective cross-addon override is fixed.
- `amr_token` local `amr.token.helper.validate()` does not require audience by default; the target has a test named `test_default_validation_does_not_require_audience`. This is context transferred to ADDONS13-38, not an ADDONS13-46 acceptance criterion or an authorization to change `amr_token` policy.
- In-scope auth/model consumers are `amr_resource/models/ir_http.py` (`_auth_method_machine`, `_auth_method_params`, `_auth_method_user_or_param`) and `amr_resource/models/res_users.py` (`decode`, `with_access_token_context`). `amr_token` local helpers and `amr_oidc` consumers are excluded and separately tracked.
- `amr_resource.get_user_match()` (`:157-176`) currently resolves email first against `res.users.login`/`email`, then `sub` against login; for `type == 'machine'` it may return an inactive account. Calls use `sudo()`. The target tests characterize this behavior. A per-issuer resolver changes a public auth contract and needs explicit fallback, user-eligibility, and compatibility criteria.
- `amr_service_client` is present in the target and has a separate outbound token cache, but no direct call to `amr.resource.helper` was found in its provider implementation. Cache/profile isolation is assigned to ADDONS13-49 and is not an `amr_resource` acceptance criterion.
- Six source-only helper consumers are individually tracked in ADDONS13-50 through ADDONS13-55; they are absent from the pinned target. Three other source manifest dependents (`amr_auth_qr`, `amr_jsonrpc_jwt`, `amr_user_public_key`) had no direct helper call identified in the static scan and are not assigned a change by this Feature. Actual installed modules and external consumers remain unknown.

### Security/compatibility findings (static, severity not assessed)

- Base issuer discovery is selected from unverified JWT `iss` in validation/introspection, and generation accepts a caller-provided issuer URL. This can cause outbound requests to untrusted hosts; in generation/introspection, configured client credentials may be sent to endpoints obtained from that metadata. Conditional impact depends on callers, network policy, and credentials; exploitability was not tested.
- Local detection and selected issuer can disagree; a locally generated token with a custom issuer may be routed to remote Discovery.
- Direct `url` override, metadata endpoint origins, redirects, schemes, DNS/private-address restrictions, and request timeouts have no explicit trusted-profile contract in the inspected helper.
- `get_user_match()` (`:157-176`) maps by email and then `sub`/login, not by an explicit `(issuer, subject)` binding. Whether multiple trusted issuers may map to the same user is unresolved.
- `validate()` logs the raw token on malformed-header error (`:117-121`). This is an adjacent baseline logging risk, not silently expanded into this Feature; no real token was used or emitted.
- Source/target module graph differs, no runtime installed-module inventory was obtained, and no test/runtime evidence exists.
- Fixed-user mapping can collapse multiple token subjects onto a privileged account; unrestricted model/method dispatch can call unintended ORM methods; database-stored Python is executable code, not ordinary configuration. Severity and exploitability are unassessed. Odoo's security guidance warns that `safe_eval` still has powerful capabilities and that dynamic attribute access can reach record properties/methods.[3]

## 4. Proposed contract — recommendation only

**Recommended minimum:** bind every operation to an explicit trusted issuer profile. The profile selects either (a) `discovery` mode for an issuer already trusted out-of-band, or (b) `static` mode with administrator-configured token/introspection/JWKS endpoints. The token's unverified `iss` may be used only to look up an already configured profile; it must never directly become a URL. Unknown, missing, or ambiguous issuers fail before DNS/HTTP/JWKS/introspection. Do not silently fall back from failed Discovery to another issuer or to `web.base.url`.

### Proposed issuer registry and user-resolution model

Place `_name = 'oidc.issuer.register'` in `amr_resource`; it is the base resource/auth layer and the target manifest has no `amr_oidc` dependency. Use one registration per exact issuer, an active flag, and a database uniqueness constraint on `issuer`. Add `audience_ids = fields.One2many('oidc.issuer.register.audience', 'issuer_id', ...)`; the child has required `issuer_id = fields.Many2one(..., ondelete='cascade')` and required `audience`. Enforce uniqueness on `(issuer_id, audience)`. Treat child values as audiences accepted by this resource—not as an issuer's complete ecosystem of audiences. Proposed access policy: parent/child CRUD only through an approved administrator group; do not expose registry enumeration or mutation through public/RPC methods, and keep runtime lookup internal and field-limited. Group semantics and exact API boundary require Owner/Security acceptance. Recommended access-token policy: `aud` must contain at least one explicitly registered audience; a missing/empty or nonmatching `aud` fails. The exact semantics still require Owner acceptance.

Add optional `allowed_azp` (or a child allowlist if multiple authorized parties are required) and `require_azp` policy. If the token has `azp`, require exact match to an explicitly configured party; do not accept arbitrary claim values. If absent, proceed only if the token profile permits absence. For OIDC ID Tokens, follow the OIDC-specific audience/authorized-party checks; do not apply ID-Token assumptions to generic OAuth access tokens.[2]

Add a required `user_mapping_mode`, with proposed values `issuer_subject`, `fixed_user`, `resolver_method`, and `python_code`. `fixed_user` uses a `Many2one('res.users')`, not an arbitrary login or numeric value. `issuer_subject` should use a binding keyed by `(issuer registration, sub)`; OIDC defines `sub` as locally unique within its issuer, so the pair avoids cross-issuer collisions.[2] Keep current email-first behavior only as an explicitly accepted legacy mode; do not silently use email as a cross-issuer identity key.

For `resolver_method`, do not dispatch arbitrary model/method names from database fields. Use an allowlisted resolver key or an approved `(model, method)` pair with a stable input/output contract. Resolver execution occurs only after token validation and receives verified, profile-approved claims—not raw token or unverified payload. It must return exactly one permitted `res.users` or fail closed; no silent fallback to another mode.

Include code-owned resolver key `get_user_match` in the available method choices and show it with the exact UI label `Default`. The target implementation currently checks `email` against `res.users.login`/`email` first, then checks `sub` against `login`; for `type == 'machine'`, it can also return an inactive user. It uses `sudo()` and `limit=1`, so the first match is not proof that the result is unique or eligible. This option is not equivalent to issuer-bound `(iss, sub)` mapping. Invoke it only after all accepted token checks; require the accepted single-user/eligibility contract, and do not treat its label as permission for cross-issuer email matching. Whether to preselect this option and whether to preserve or tighten its legacy matching behavior require explicit Owner decisions.

Owner chose to retain `python_code` on the registration record as a privileged code-execution feature. Treat every code edit as executable-code change, restrict read/write to a specifically approved privileged group, maintain traceable revisions/audit, and require independent manual Security review as part of unified Code Review Step 2 before enabling it. Do not treat `safe_eval` alone as a safety boundary for arbitrary/untrusted stored code; Odoo documents that it remains powerful and must be reserved for trusted privileged users. Define and review the exact execution context/capabilities, ensuring code runs only after token/issuer/audience/`azp` checks. Do not pass raw JWT or unverified claims. Whether `env`, recordsets, helper calls, or only restricted functions are available is an unresolved security design decision.[3]

For the same-instance issuer whose Discovery publication is intentionally disabled, use the trusted static/local profile; do **not** restore or modify the `amr_oidc` Discovery route as a workaround. Keep the existing local token helper path, but make local recognition and `get_issuer()` resolve through the same selected profile. Preserve current config-key indirection or introduce a versioned migration; do not silently reinterpret `amr_resource.issuer` from a system-parameter key into a literal URL.

This recommendation does not decide whether the product supports one issuer per database or multiple profiles, which token types each consumer accepts, whether audience verification is mandatory, or whether subject mapping becomes issuer-bound. Those require explicit Owner/Lead decisions below. For any configured endpoint, the accepted policy must define scheme/TLS, redirect behavior, allowed origins/ports, DNS/private-address handling, timeouts, and whether credentials may be sent. No raw endpoint or secret is included in this draft.

### Options for Owner decision

1. **One trusted profile per database:** smallest compatibility surface; blocks valid multi-issuer use unless callers are separated.
2. **Named allowlisted profiles:** supports multiple issuers; requires a data/config migration and deterministic token-issuer-to-profile lookup.
3. **Discovery-only trusted profile:** preserve metadata fetch, but it cannot serve the same-instance case while Discovery returns 404; not sufficient by itself for the reported scenario.

**Recommendation:** option 2 only if multi-issuer behavior is an actual requirement; otherwise option 1 plus explicit `static`/`discovery` mode. In either case, no implicit trust from a token claim and no silent fallback. This is not accepted policy.

## 5. Provisional functional requirements and acceptance criteria

All criteria below remain provisional until the Owner accepts the exact PRD/UAT hashes.

- **AC-01 — Trusted selection:** Resolve `iss` only to an administrator-configured trusted profile using the accepted exact comparison rule. Missing, unknown, duplicate, or malformed issuer fails closed before any DNS, Discovery, JWKS, introspection, or token-endpoint call. No prefix match or implicit normalization.
- **AC-02 — Explicit modes:** `discovery` mode fetches metadata only for the selected trusted issuer, verifies returned `issuer` equality and endpoint policy, and has no silent fallback. `static` mode uses configured endpoint URIs and makes zero Discovery requests.
- **AC-03 — `amr_resource` issuer classification:** The in-scope `amr_resource` issuer/profile lookup uses the accepted exact configured profile rules. Changes to `amr_token` local generation/validation/override behavior are excluded and tracked by ADDONS13-38.
- **AC-04 — In-addon consumer compatibility:** Preserve public helper signatures, return shapes, exception mapping, and user/auth callback behavior for `amr_resource` consumers unless an explicit accepted AC changes them. Cross-addon consumer compatibility is owned by its separately tracked Feature and is not claimed here.
- **AC-05 — Endpoint safety:** Validate configured endpoints against the accepted scheme/origin/redirect/DNS policy and apply bounded request timeouts. No client secret or token may be sent to an endpoint that has not passed that policy.
- **AC-06 — `amr_resource` cache isolation:** Define metadata/JWKS/token cache ownership, keying, TTL, and invalidation within `amr_resource`. An issuer/endpoint/config change must not reuse credentials or cached tokens from a different profile. `amr_service_client` cache behavior is excluded and owned by its separate Feature.
- **AC-07 — Scope boundary:** Do not change `amr_oidc` Discovery publication or ADDONS13-39 grant/metadata behavior. Do not modify the target's current 404 route under this Feature; verify the accepted ADDONS13-39 disposition before any route change.
- **AC-08 — Test evidence:** Unit tests call real candidate methods with synthetic claims/keys and mocked HTTP/JWK/ORM/clock/cache boundaries; unknown issuers assert zero outbound calls. Actual Odoo runtime/integration and external-consumer tests remain separately gated and are not implied by unit results.
- **AC-09 — Registration required:** A token is eligible only when its exact `iss` resolves to one active `oidc.issuer.register`; unknown, inactive, missing, or ambiguous registration rejects before any outbound request. Registration is never created from token input. Proposed ACL contract: only the approved administrator group can manage parent/child records; public/RPC callers cannot enumerate or mutate trust configuration, and runtime lookup exposes only required fields.
- **AC-10 — Multiple audiences:** Each registration owns distinct audience child rows; token `aud` must satisfy the accepted resource-profile matching rule. Missing, empty, or nonmatching audiences reject. Audience values are not inferred from email, issuer URL, or `web.base.url`.
- **AC-11 — Optional `azp`:** Absence is permitted only when the selected token profile permits it. If present, `azp` must exactly match the configured authorized-party value(s); it never substitutes for `iss`, `aud`, signature, or token activity checks. ID Token-specific multiple-audience behavior is kept separate.[2]
- **AC-12 — Resolver sequencing/result:** User resolution runs only after issuer, signature/introspection, time, audience, and applicable `azp` checks succeed. It returns exactly one allowed `res.users` or fails closed; no implicit email/login fallback follows a selected-mode failure.
- **AC-13 — Fixed user:** `fixed_user` references a real `res.users` record and applies only to the issuer profile that passed token validation. Account eligibility/privilege restrictions are explicit; no arbitrary user ID from claims is accepted.
- **AC-14 — Model-method resolver:** Only explicitly allowlisted model-method resolvers can run; unknown model/method pairs, invalid return types, and resolver exceptions fail closed without invoking a different mode.
- **AC-15 — Stored Python mode:** `python_code` is privileged executable configuration, not ordinary data. Its access, revision/audit trail, restricted execution context, ordering after all token checks, and failure handling are reviewed on the exact candidate in unified Code Review Step 2. Do not claim `safe_eval` alone is a safe boundary for arbitrary/untrusted stored code or execute unverified claims/raw tokens.[3]
- **AC-16 — Identity binding:** The accepted default and legacy compatibility rule for mapping `(iss, sub)`, email, and machine users are explicit per token profile. If issuer-subject binding is selected, identities from different issuers cannot collide; email fallback requires an explicit verified-email policy.[2]
- **AC-17 — `Default` resolver option:** The code-owned resolver choice with internal key `get_user_match` is available and displayed exactly as `Default`. It runs only after token validation and must satisfy AC-12's single permitted-user/fail-closed contract. The display label does not imply issuer-subject binding, authorize cross-issuer email matching, settle account eligibility, or decide whether the choice is preselected.

## 6. Decision and risk register

No residual risk has been accepted; no Security reviewer is assigned; severity is `UNASSESSED`; future candidate SHA is `PENDING` for every item.

| ID | Evidence / conditional risk | Required disposition/action | Gate / UAT |
|---|---|---|---|
| R-01 | `amr_resource/models/helper.py:61-73,83-102,114-149`: caller/token-derived issuer can select Discovery/token/introspection/JWKS endpoints. Conditional SSRF/credential disclosure/authentication risk; not runtime-proven. | Owner chooses trust cardinality/profile source; reject unknown issuers before network; Security review required. | Step 0 readiness, Step 2; UAT-01–06, UAT-16 |
| R-02 | `amr_resource/models/helper.py:20-27,76-80` + `amr_token/models/helper.py:39-51,281-350`: local detector compares `web.base.url`, while local generator/validator use selected issuer. The cross-addon mismatch is transferred to ADDONS13-38; only the base `amr_resource` helper is in scope here. | Define and test the `amr_resource` profile classification contract; do not change the `amr_token` generator/validator or claim end-to-end local behavior is fixed. | Step 0; UAT-08; end-to-end `amr_token` work in ADDONS13-38 |
| R-03 | `amr_resource/models/helper.py:40-44,134-142`: metadata issuer equality and endpoint-origin policy are not enforced in the base flow; no explicit timeout. | Accept metadata/transport rules and bounded timeout; no secrets to untrusted endpoint. | Step 0 and Step 2; UAT-03,06,12 |
| R-04 | `amr_resource/models/helper.py:157-176`: email-first/sub-login resolution is not issuer-bound; `amr_token` audience/default-validation behavior is out of scope. | Decide `amr_resource` user identity binding, audience policy, and legacy migration explicitly; do not change identity mapping implicitly. | Step 0/Step 2; UAT-19–25; `amr_token` validation in ADDONS13-38 |
| R-05 | `amr_resource/models/helper.py:117-121` logs raw malformed token. | Keep out of this Feature unless Owner expands scope; separately triage and do not claim logs are safe. | Separate security disposition; not an ADDONS13-46 fix |
| R-06 | `amr_service_client/services/providers.py:100-115,185-201,309-320`: separate outbound-token caches have provider-specific keys/expiry; service-account key omits token URI. | Keep provider/cache changes out of this Feature; track and test in the separately created `amr_service_client` Feature. | Separate Feature; not an ADDONS13-46 gate or UAT |
| R-07 | Source has 10 direct manifest dependents; target has 2. Runtime installed modules/external consumers unknown. | Keep the target/module inventory as a limitation; individual non-`amr_resource` addon compatibility is tracked by separate Features and must not be claimed by this Feature. | Step 0 target revalidation; no deferred UAT in this scope |
| R-08 | Target snapshot statically routes `/.well-known/openid-configuration` to 404 and has an existing test asserting it; no runtime request was made. | Keep ADDONS13-39 route/metadata scope separate; verify accepted upstream disposition before any route change. | Dependency on ADDONS13-39; not an implementation target here |
| R-09 | `python_code` stored in issuer records is later executed in the Odoo worker; exact context and controls are undecided. `safe_eval`/dynamic attribute access are not a blanket safety boundary for untrusted stored code. | Security review exact execution mechanism, privilege boundary, code editing/audit, allowed context, failure behavior, and post-validation ordering; do not enable before Step 2 review. No residual risk accepted. | Unified Code Review Step 2; UAT-21, UAT-24 |
| R-10 | Configurable arbitrary model/method dispatch could invoke unintended ORM methods; fixed-user mode could map unrelated subjects to a privileged account. | Use code-owned resolver allowlist, typed user result, least-privilege fixed account, and explicit no-fallback rules. | Step 0/Step 2; UAT-19–23 |
| R-11 | Current `get_user_match()` is email-first and not bound to `(issuer, sub)`; collisions across issuers may select the wrong local user. Static mapping only; no exploitability claim. | Decide identity key and legacy email/machine behavior; bind external subject to issuer; test same-sub/different-issuer and email collision cases. | Step 0 and Step 2; UAT-19, UAT-23 |
| R-12 | The requested `Default` label may obscure that `get_user_match()` is email-first, uses `sudo()`/`limit=1`, and can return an inactive machine user; duplicate matches may be silently reduced to one result. | Keep the internal key explicit; decide preselection, collision/ambiguity handling, email trust, and inactive-user eligibility. Enforce AC-12 rather than assuming `limit=1` proves uniqueness. | Step 0/Step 2; UAT-21, UAT-23, UAT-25 |

## 7. Rollout and rollback considerations (planning only)

- Before any future rollout, record current non-secret profile/config references and module inventory; protect secret values and key material. Do not execute that capture under this Step 0 task.
- Deploy code and matching configuration as one versioned unit. A code-only rollback to the current Discovery-dependent helper may restore the same 404 failure; therefore rollback is not demonstrated safe until a known-good issuer/endpoint configuration and matching cache invalidation are specified.
- On issuer/profile change, isolate or invalidate affected `amr_resource` metadata/JWKS/token caches according to the accepted cache policy. Never reuse a token across issuer profiles. `amr_service_client` cache behavior is excluded. Do not restore public Discovery publication as an implicit rollback.
- Validate rollback only in an explicitly authorized isolated QA environment with synthetic credentials and mocked or approved endpoints. Production rollout/rollback remains out of scope and unexecuted.

## 8. Step 0 readiness and traceability

- Source snapshot and target snapshot are pinned; hashes and consumer inventory are in `SOURCE-INVENTORY.md`.
- Concrete source call paths and conditional mismatch are recorded above.
- PRD↔UAT traceability is in [`UAT-DRAFT.md`](UAT-DRAFT.md).
- Open Owner decisions (within `amr_resource`): issuer cardinality/source and migration; registry CRUD group/RPC boundary; audience ANY/exact-resource semantics; allowed `azp` cardinality and ID Token behavior; whether `get_user_match` is preselected under the `Default` label and whether its email-first behavior is retained or tightened; ambiguity handling and inactive-user eligibility; issuer-subject mapping/migration; fixed-user eligibility; remaining method allowlist/API contract; Python execution engine/context/permissions/audit and Security review; token profile, endpoint/redirect/DNS policy, direct `url` trust, in-addon cache invalidation, and rollback baseline. Non-`amr_resource` consumer behavior belongs to the separate linked Features, not this task.
- Exact artifact SHA-256 values are recorded in `RESULT.json` after finalization.
- **No code/test files were changed; no tests/runtime/UAT were run.** Append-only scope-disposition comments were posted and read back on ADDONS13-38 and ADDONS13-46. No issue state, checklist verdict, assignee, priority, hierarchy, acceptance, or execution gate changed; ADDONS13-46 remains `Backlog` / Step 0 `PENDING` after the Analis dispatch failed before prompt delivery. This PRD is not accepted and does not authorize Development.

## Sources

[1] https://openid.net/specs/openid-connect-discovery-1_0.html
[2] https://openid.net/specs/openid-connect-core-1_0.html — OpenID Connect Core 1.0 incorporating errata set 2
[3] https://www.odoo.com/documentation/13.0/developer/reference/security.html — Odoo 13 Security in Odoo
