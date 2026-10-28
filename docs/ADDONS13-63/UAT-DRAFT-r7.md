# ADDONS13-63 — UAT Amendment DRAFT r7

**Status:** DRAFT / NOT YET ACCEPTED. All UAT IDs and variants remain **NOT RUN**. This amendment pairs with `docs/ADDONS13-63/PRD-DRAFT-r7.md` and supplements the Owner-accepted r6 UAT; it does not rewrite r6 actuals.

## 1. Baseline and boundaries

Accepted predecessor UAT: `docs/ADDONS13-63/UAT-DRAFT-r6.md`, SHA-256 `d4e0230bfea5a1a5237ec8002fe2843ea1aea12a7a0a0f3a4cc1898032b6174f`. Its paired PRD hash is `ccde0a6dfc0bf4fca780457395c7113b27d251d56579311f01c8d96cbdf862a4`.

This amendment maps AC-63-R7-01..09 one-to-one to UAT-63-R7-01..09. Each r7 AC amends the corresponding r6 AC; unaffected r6 test design is inherited only as a design, not as execution evidence. The current source is statically described in PRD r6 and remains different from the r7 desired contract. No current r7 test has been executed.

O-6 sequencing is pending a response on ADDONS13-38. Until effective route ownership and sequencing are confirmed and the exact r7 artifact hashes are accepted, do not change source or execute addon/runtime/QA tests. Odoo 13/Python 3.7 target compatibility remains NOT RUN. A target QA run requires separate authorization naming disposable target, PostgreSQL access/database creation, run/retry limit, and cleanup scope.

## 2. Cases (all NOT RUN)

### UAT-63-R7-01 — AC-63-R7-01 — single route and valid Basic
**Status: NOT RUN.**
Use active confidential synthetic clients with `authentication_method=client_secret` (legacy default) and explicit `client_secret_basic`. Send one correctly form-encoded Basic header plus a form-urlencoded grant request. Instrument native ORM boundary to prove authentication precedes one dispatch. Expected: both configurations authenticate; downstream remains HTTP 400 `unsupported_grant_type`, with no token fields. Non-confidential variant must fail authentication. Do not treat HTTP 400 alone as proof auth succeeded. Current source prediction: legacy/explicit Basic can pass verification without the confidentiality check, then the grant dispatcher rejects. No execution evidence.

### UAT-63-R7-02 — AC-63-R7-02 — opt-in client_secret_post
**Status: NOT RUN; current source mismatch.**
Only after explicit method selection exists on a legal native selection, send one form-urlencoded body containing one `client_id`, one nonempty `client_secret`, and grant parameters, with no Authorization header or query credentials. Test valid secret, wrong/missing secret, inactive/unknown client, non-confidential client, and no silent method fallback. Expected: selected confidential Post client authenticates before dispatch; invalid/non-confidential cases return `invalid_client`; no token issuance. Existing/default `client_secret` records continue to use Basic and must not acquire Post through migration/default. Current source prediction: Post selection and positive path do not exist; body credentials are rejected. Do not fake a selection value as a native positive fixture.

### UAT-63-R7-03 — AC-63-R7-03 — credential error/challenge matrix
**Status: NOT RUN.**
Cases: failed/malformed/unknown/inactive/unsupported-method Basic with an Authorization header; a non-Basic Authorization scheme; failed/missing form-body Post; no authentication included; missing/empty verifier. Expected: failed Basic attempt -> HTTP 401, `invalid_client`, `WWW-Authenticate: Basic`; non-Basic scheme -> HTTP 400 `invalid_request`, no fallback; missing authentication or form-body Post failure -> HTTP 400 `invalid_client`, no Basic challenge. No credential, verifier, decoded pair, or raw parser/exception content appears in response. Exercise actual HTTP mapping, not helper-only doubles. These expected statuses are r7 application decisions and require native validation.

### UAT-63-R7-04 — AC-63-R7-04 — duplicate/conflicting mechanisms
**Status: NOT RUN.**
Cases: Basic plus body credentials (same and different clients), Basic plus query credentials, repeated body `client_id`/`client_secret`, repeated Authorization fields, missing/empty duplicate values, and multiple selected auth methods. Expected: HTTP 400 `invalid_request`, no fallback, no auth-success/super/grant dispatch. Repeat a valid Basic-only and valid selected Post-only control to show the endpoint is not rejecting all credential mechanisms. For repeated headers, prove the actual ingress/WSGI/Odoo layer can detect and reject duplicates; if it collapses them before application code, report BLOCKED rather than PASS.

### UAT-63-R7-05 — AC-63-R7-05 — transport and encoding
**Status: NOT RUN.**
Cases: Basic components with encoded colon, plus, space, UTF-8 and malformed percent/base64; Post form-urlencoded components with the same distinct values; credential names in query; JSON/multipart/unknown media types; repeated `grant_type`; and one unrecognized request parameter with valid Basic. Expected: POST + form-urlencoded token request only; no credential accepted from URI; duplicates of owned parameters and multiple auth methods -> 400 `invalid_request`; an unrecognized parameter is ignored and does not alter authentication (then the current dispatcher returns `unsupported_grant_type`); unsupported media types are not parsed for credentials. Preserve first-literal-colon split for Basic before component decoding. Test each parser layer separately and record the last layer reached; no source inspection substitutes for HTTP/parser execution.

### UAT-63-R7-06 — AC-63-R7-06 — secret, logging, and reflection
**Status: NOT RUN.**
Use synthetic canaries only. Exercise success-to-unsupported-grant and each error branch; inspect response and approved application log sinks. Expected: no plaintext secret, Authorization, decoded credential pair, verifier, raw body, raw exception message, or untrusted grant_type reflection. Verifier remains restricted and hashed; audit create/write/copy paths separately. Record sink coverage and sanitized assertions only. Absence in one sample is not proof of every platform/proxy log. No log inspection has been performed for r7.

### UAT-63-R7-07 — AC-63-R7-07 — fail-closed grant behavior
**Status: NOT RUN.**
With separately proven valid Basic and selected Post authentication, test missing, client_credentials, password, refresh_token, authorization_code, urn:ietf:params:oauth:grant-type:jwt-bearer, challenge_approval, digital_signature, and unknown grants. Expected current policy: HTTP 400 `unsupported_grant_type`, constant non-reflective description, zero access/refresh/ID token fields, and no dispatch into private issuer handlers. Compare against verified post-rebase baseline. Do not add an issuer to make a success fixture.

### UAT-63-R7-08 — AC-63-R7-08 — effective route and dependency sequence
**Status: NOT RUN; BLOCKED pending ADDONS13-38 coordination.**
After the cross-Feature sequencing answer, inspect native addon composition and effective HTTP registry. Expected: exactly one POST `/oidc/token` owner in `amr_oidc`, no GET/duplicate/compatibility route, and unchanged neighboring behavior outside the accepted migration scope. Verify agreed route ownership, helper dispatch, and token-only composition. A decorator or source declaration count alone is insufficient. ADDONS13-38 Step 0 is currently In Progress and its live issue has broader OIDC route-migration scope; the coordination request has been posted and read back, but no answer is recorded here.

### UAT-63-R7-09 — AC-63-R7-09 — target compatibility/evidence integrity
**Status: NOT RUN.**
After all prior gates and a separate runtime authorization, first verify that the named QA endpoint is HTTPS with a valid approved TLS configuration and that credentials will not traverse plaintext; if not, stop. Then record Odoo 13, Python 3.7, dependency versions, module composition, import/registry and test collection/execution results. Expected: supported native behavior on the specified target; static AST review, other Python versions, isolated doubles, skipped imports, or plan documents do not pass this case. No runtime or test suite has been run for r7.

## 3. Status summary and execution limits

- UAT-63-R7-01..09: **NOT RUN** (9/9).
- No PASS, FAIL, waiver, runtime result, or QA result is claimed.
- r7 changes expected behavior for Post, confidential-client enforcement, error status, duplicate handling, and log policy; r6 actuals remain immutable historical evidence.
- Step 1 is BLOCKED pending r7 exact-hash acceptance and ADDONS13-38 sequencing/effective-owner confirmation. Steps 2–4 have not started.
- No addon/tests/Odoo/DB/runtime/QA/service execution occurred while drafting this amendment. No production/shared resource access is authorized.
