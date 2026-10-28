# ADDONS13-63 — UAT-DRAFT (UPDATED TO LATEST AGREED STEP 0 REQUIREMENTS)

**Provenance:** Owner approved the earlier UAT plan on 2026-10-27 CST against draft SHA-256 `363263a998dc47f9db97525711a2ee1748a9b09b7a93f7c7666fd107b3dbd572`. The later Owner clarifications were recorded after that approval, and this document was then revised to reflect the latest agreed requirements. No approval of the exact SHA of this revised document is asserted. Every case remains **NOT RUN**, and no test or runtime pass is claimed. **Candidate baseline:** `c08b050cfd85ccc5c705eb92852e57626eb82806`; Odoo 13 / Python 3.7. Cases map 1:1 to the PRD acceptance criteria. This is not implementation authorization or risk acceptance.

## Environment/setup (proposed)

- Isolated disposable Odoo 13 + PostgreSQL test database, Python 3.7; install modules through normal test harness only after implementation is approved. UAT must use synthetic clients and synthetic secrets, never production credentials.
- Configure one active confidential test client per approved auth method; create secret via approved hash path and ensure access is role-restricted. Include inactive/unknown client fixtures and a second client for conflicting-identity tests.
- Keep test data and execution isolated and synthetic. Authentication-boundary cases should assert the auth decision before grant dispatch using instrumentation or a narrowly scoped test seam; they need not add/change grant behavior. AC-7 regression requires an already supported grant fixture in the isolated environment; treat fixture availability as a setup check. If unavailable, mark that case BLOCKED/NOT RUN and escalate setup rather than adding grant scope or permission. Never infer auth success from a downstream grant error unless instrumentation proves the boundary decision.
- Capture route registry/controller metadata and sanitized request/response/log evidence. Redact Authorization header and all body credentials at collection time.

## Owner decisions recorded for execution

- Legacy `authentication_method='client_secret'` accepts either Basic or form-body credentials, exactly one method per request; explicit `client_secret_basic` and `client_secret_post` selections accept only their named channel.
- Authentication failures use `invalid_client` with HTTP 401; Basic failures include `WWW-Authenticate: Basic`.
- Implement in the helper/model path behind the current effective token route. Leave controller and route ownership unchanged; future movement belongs to ADDONS13-38 and must preserve behavior.
- Credentials never come from query parameters; duplicate or mixed credential sources fail closed. All cases below remain NOT RUN.

## Cases

| AC / unique case | Setup and request | Route boundary | Assertions / evidence required | Evidence level | Status | Limits / teardown |
|---|---|---|---|---|---|---|
| AC-1 / UAT-63-01 | Active client with valid hash and either `client_secret_basic` or legacy `client_secret`; POST with one Basic Authorization pair. | Current effective inherited token route; POST only; no controller edits. | Authentication accepts expected client before grant dispatch; error challenge absent on success; no second route. | Runtime integration + route-registry evidence; source-level test alone is insufficient for PASS. | NOT RUN | Use synthetic credentials only; redact headers, delete client/hash/records. |
| AC-2 / UAT-63-02 | Active client with explicit `client_secret_post` or legacy `client_secret`; one form-urlencoded `client_id` + `client_secret`. | Same current token route, POST. | Accept body credentials only under selected/legacy policy; no query fallback. | Runtime integration with request instrumentation and sanitized trace. | NOT RUN | Explicit method restricts channel; legacy accepts body or Basic, not both. Tear down fixtures. |
| AC-3 / UAT-63-03 | Wrong secret, missing fields, malformed Basic, unknown/inactive client, absent/invalid hash. | Same token boundary. | Each fails before grant dispatch with OAuth `invalid_client`, HTTP 401; Basic failure has `WWW-Authenticate: Basic`; no secret/hash in response/logs. | Runtime integration + sanitized response/log evidence. | NOT RUN | Ensure error body/headers are verified on real route. Delete fixtures and sanitize logs. |
| AC-4 / UAT-63-04 | Submit Basic plus form credentials; repeat with mismatched client IDs; include duplicate credential keys. | Same token boundary. | All multi-method/conflicting/duplicate cases rejected, never select fallback credential; response is `invalid_client`/401, no dispatch. | Runtime integration + dispatch spy/trace proving early rejection. | NOT RUN | Clear traces and fixtures. |
| AC-5 / UAT-63-05 | Send credentials in query only; Basic payload with colon in secret; URL-encoded values including plus/space; malformed encoding/base64; duplicate keys. | Same token boundary. | Query credentials rejected; approved encoding semantics respected; no unintended request source accepted; ambiguity rejected without fallback. | Runtime integration with sanitized request parser trace. | NOT RUN | RFC encoding and strict rejection rules apply; teardown all test artifacts. |
| AC-6 / UAT-63-06 | Use synthetic unique canary secret; exercise success and each credential failure; inspect allowed application log sink and responses. | Token boundary and verifier storage/access rules. | Canary absent from response/logs; Authorization raw and decoded value absent; plaintext not stored; verifier remains hashed and restricted to provider admin; `invalid_client` does not echo input. | Runtime security test + role-based ORM access checks + sanitized log scan. | NOT RUN | Logging sinks/environment may be incomplete; absence in sampled logs is not universal proof. Destroy canary and captured artifacts. |
| AC-7 / UAT-63-07 | Baseline-approved supported grant with valid authenticated client, compared against pre-change expected behavior; no grant or refresh modifications. | Same token route and helper dispatch. | For authenticated request, grant dispatch and token response semantics unchanged; no new grant/refresh/metadata/authorization-code behavior. | Runtime regression on isolated DB plus source diff review (future stage only). | NOT RUN | No changes exist to test; downstream grant fixture may entail scope and requires separate approval. Drop disposable DB. |
| AC-8 / UAT-63-08 | Load the current accepted module set and inspect Odoo route registry. | Current inherited `/oidc/token` route. | Exactly one registered POST `/oidc/token`; no controller edits or duplicate route; GET rejected/not mapped; neighboring routes unchanged. | Runtime route-registry introspection plus source-level route search; source-only is not runtime PASS. | NOT RUN | Route currently declared in `amr_token/controllers/main.py:56-63` and inherited by `amr_oidc`; ownership migration stays in ADDONS13-38. Tear down server/DB. |
| AC-9 / UAT-63-09 | Review implementation/test syntax and APIs against Python 3.7 and Odoo 13; execute compatibility checks only in the separately authorized development/UAT stage. | Static compatibility review plus relevant isolated Odoo tests; token boundary. | No syntax/API incompatibility; approved tests pass on supported versions. | Static review plus actual Odoo 13/Python 3.7 test runtime required for PASS. | NOT RUN | No tests/runtime have been run in this documentation revision. Remove disposable environment after authorized run. |

## Cross-case route/method/secrets assurance

- **No route duplication:** UAT-63-08 must show one route registration at agreed owner; route source search alone is preliminary, not proof of runtime registration.
- **No method confusion:** UAT-63-04/05 distinguish auth method from grant type; one approved channel only, credential source constrained to header or form as accepted, no query fallback. Authentication failure must be shown before grant dispatch.
- **No secrets leakage:** UAT-63-06 uses canary credentials and checks sanitized outputs/logs/storage/access controls. Never collect raw authorization headers; no real credentials. Log sampling is limited evidence, not a universal guarantee.
- **HTTP method boundary:** UAT-63-01/02/08 verify POST-only route behavior; tests must not treat controller inheritance or handler reachability as proof of correct owner.

## Limitations and coordination

1. Baseline has not implemented the feature; all cases remain NOT RUN. They may now be executed only as part of the separately authorized Development/UAT stages, using the isolated disposable environment.
2. ADDONS13-38 remains In Progress and owns endpoint migration and Discovery/deprecation decisions. This Feature leaves controller/route ownership unchanged; verify no duplicate route now, then preserve auth behavior when that Feature later moves it. No metadata change here.
3. Owner resolved legacy `client_secret`, explicit method selection, error mapping, and route sequencing. Standards-driven encoding and malformed/duplicate handling are specified above. Public-key/TLS auth and unsupported clients remain outside scope.
4. Static source evidence cannot prove live Odoo route registry, actual logs, credential parsing, or runtime compatibility; those require the specified UAT evidence.

## Teardown

After an authorized future UAT run: remove disposable database and synthetic clients, hashes, users and configuration; stop isolated Odoo instance; securely discard request traces/log captures containing any credential material; retain only redacted evidence, candidate SHA, runtime version and case verdict. Do not modify shared or production systems.

**UAT disposition:** Owner-approved Step 0 plan; no case has been executed, passed, waived, or marked NOT APPLICABLE. Cases remain NOT RUN pending their authorized test run. Approval is not a test result or residual-risk acceptance.
