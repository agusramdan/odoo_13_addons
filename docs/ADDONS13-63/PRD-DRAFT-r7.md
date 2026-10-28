# ADDONS13-63 — PRD Amendment DRAFT r7

**Status:** DRAFT / NOT YET ACCEPTED. Lead decision addendum under Owner direction; it does not replace the hash-bound r6 predecessor until this exact amendment package is accepted. No implementation, test, runtime, QA, or release gate is passed by this document.

## 1. Base revision and authority

This amendment supplements the Owner-accepted r6 documents only:

- PRD base `docs/ADDONS13-63/PRD-DRAFT-r6.md`, SHA-256 `ccde0a6dfc0bf4fca780457395c7113b27d251d56579311f01c8d96cbdf862a4`.
- UAT base `docs/ADDONS13-63/UAT-DRAFT-r6.md`, SHA-256 `d4e0230bfea5a1a5237ec8002fe2843ea1aea12a7a0a0f3a4cc1898032b6174f`.

On 28 October 2026, Owner instructed the Lead: “Sebagai lead, Setuju Rekomendasi.” The Lead records the following bounded dispositions as adoption of the recommendations previously presented, not as a verbatim Owner-authored policy statement. Acceptance of r6 remains historical and does not automatically accept this new r7 amendment. Source references are observations from the r6 inventory/current worktree, not runtime evidence.

## 2. Disposition of O-1–O-6

### O-1 — Authentication scope: RESOLVED BY LEAD DISPOSITION

Preserve the accepted Basic **and** Post scope. Do not remove `client_secret_post` by equating current source behavior with desired behavior. RFC 6749 §2.3.1 requires Basic support for clients issued a client password. Body credentials may be supported, are not recommended, and should be limited to clients unable to use Basic. RFC 7591 §2 defines `client_secret_basic` and `client_secret_post` as token-endpoint authentication metadata values and defaults an omitted value to Basic; this application’s field mapping remains a local compatibility decision. Protocol context does not prove runtime conformance.

### O-2 — Legacy/default, method selection, and public clients: RESOLVED BY LEAD DISPOSITION

- Preserve existing database values and the current default `client_secret`; interpret that legacy method as Basic for backward compatibility. Preserve the existing application contract requiring a nonempty secret checked against the restricted PBKDF2 verifier; this amendment does not authorize plaintext-secret storage. RFC 6749 §2.3.1 allows a client to omit `client_secret` when its secret is empty; this Feature deliberately does not claim support for empty-secret clients. Any change to that accepted application rule requires a separate amendment.
- Keep `client_secret_basic` as an explicit Basic selection.
- Add `client_secret_post` as a distinct explicit selection. Do not silently migrate existing records to Post or change their default. Approve Post only for a registered client documented as unable to use Basic; selection is opt-in and is not, by itself, evidence that this limitation was reviewed.
- Secret-based Basic/Post authentication is rejected for records with `is_confidential=False`; such records must not be issued a password credential, and secret verification must not be relied on to identify a public client. This is a deliberately conservative application policy, not a claim that RFC 6749 requires this exact Boolean rule. Existing non-confidential rows with stored hashes may lose secret-auth compatibility; no database inventory or migration is authorized here, so this is an explicit rollout risk.
- No data migration is included. Future configuration UI or bulk migration is out of scope.

Source anchors: `amr_oidc/models/oidc_client.py:27-29,49-54`; `amr_oidc/models/token_client_auth.py:18-20,79-90`. The current auth helper does not check `is_confidential` and does not offer Post; implementing this disposition requires a source change.

### O-3 — Error/challenge mapping: RESOLVED BY LEAD DISPOSITION

- Duplicate request parameters/credentials, conflicting credential channels, multiple client-authentication methods, malformed token-form syntax, or unsupported request media type: HTTP 400 `invalid_request`; descriptions are static and do not reveal credentials or parser internals.
- Failed/missing/unknown/inactive/non-confidential or unsupported-method client authentication, including malformed Basic syntax: `invalid_client`. A failed Basic attempt through an `Authorization: Basic` header returns HTTP 401 with `WWW-Authenticate: Basic`. Missing authentication or failed form-body Post authentication returns HTTP 400 `invalid_client` with no Basic challenge. A non-Basic Authorization scheme is outside the accepted credential channels and is rejected as HTTP 400 `invalid_request`, without fallback or claim that the scheme authenticated the client.
- After successful client authentication, every grant remains fail-closed and returns HTTP 400 `unsupported_grant_type` with a constant, non-reflective description. No access/refresh/ID token issuance is added.

This is the selected application error contract. RFC 6749 §5.2 has HTTP 400 as the default and requires HTTP 401 plus a `WWW-Authenticate` challenge matching the method when Basic client authentication was attempted. This Feature applies that requirement to the supported Basic method. Classification of non-Basic Authorization headers as out-of-contract `invalid_request` is a local policy choice, not a general RFC conformance claim. Localized framework behavior still requires tests.

### O-4 — Request transport, duplicates, and encoding: RESOLVED BY LEAD DISPOSITION

- Accept only POST requests with `application/x-www-form-urlencoded` token parameters. Basic credentials are parsed only from one `Authorization: Basic` value; Post credentials are parsed only from form fields and only when the registered method is `client_secret_post`.
- Never accept `client_id` or `client_secret` from the URI query. Any credential-bearing query is `invalid_request`.
- Reject repeated `client_id`, `client_secret`, or `grant_type` parameters, repeated `Authorization` values, credential-bearing query, or mixed Basic plus body credentials as `invalid_request`; do not choose a value or fall back to another method. Ignore unrecognized request parameters. Other RFC 6749-defined token parameters and extension parameters are not implemented by this Feature; any future handler must follow its governing protocol's multiplicity rules.
- Post credentials use form-urlencoded decoding. Basic identifier and secret are each form-encoded before joining with the first literal colon and Base64 encoding. Keep literal and encoded colon/plus/space behavior covered by separate cases.
- Reject unsupported request media types at the token endpoint without trying to mine JSON/multipart credentials. The effective WSGI/Odoo header boundary must prove repeated-header rejection; if it collapses duplicates before the controller can detect them, stop implementation at that boundary and report a blocker rather than claim the rule is enforced.

RFC 6749 §§2.3.1, 3.2, and 3.2.1 require the body method, when used, to put credentials only in the body, prohibit credentials in the request URI, require POST for token requests, and prohibit multiple client-authentication methods per request. The Verified Erratum 5708 record lists §§3.1 and 3.2 and scopes the repeat rule to parameters defined by RFC 6749. Reported (not verified) Erratum 8791 also concerns §3.2 and proposes a default multiplicity rule for extension parameters; its note says §3.2 was not corrected by 5708, which conflicts with 5708's section listing. This Feature enforces single values for the token-request parameters it consumes (`client_id`, `client_secret`, `grant_type`) and ignores unrecognized parameters. Because the published errata records leave broader duplicate/extension interpretation unclear, this amendment does not claim complete §3.2 duplicate conformance or extension support. The media-type/parser policy is also an explicit local contract.

### O-5 — Secret/logging/reflection: RESOLVED BY LEAD DISPOSITION

Never log plaintext secret, Authorization value, decoded credential pair, verifier, raw request body, or raw exception text from this boundary. Return generic client-facing descriptions. Do not reflect untrusted `grant_type` into an error description. Internal failures may be recorded only as sanitized error category plus a non-sensitive correlation identifier; the approved application log sink and coverage must be verified in tests/review. This does not claim all platform/proxy logs are covered.

### O-6 — Route ownership and ADDONS13-38 sequencing: PARTIALLY RESOLVED; IMPLEMENTATION BLOCKED

- Intended token-route owner is `amr_oidc`, with exactly one effective POST `/oidc/token` route, no compatibility duplicate, and no new grant issuer. Keep current fail-closed grant dispatch.
- ADDONS13-38 is a live dependency whose accepted scope covers moving all OIDC routes from `amr_token` to `amr_oidc`. On 28 October 2026 the Lead appended coordination question `LEAD-COORD-ADDONS13-63-ADDONS13-38-20261028-v1` to Plane issue ADDONS13-38. Readback confirmed the comment; that issue's Step 0 remains In Progress and has no accepted migration contract in the evidence reviewed here.
- Therefore sequencing/effective-owner confirmation is still pending. Do not begin source changes or push a code candidate until the ADDONS13-38 coordination answer and the exact implementation base are reconciled. The Lead recommendation is not proof of live route registration or dependency acceptance.

Source anchor: `amr_oidc/controllers/main.py:54-61`; current route/runtime ownership is not proven by source declaration alone. The base grant dispatcher remains fail-closed as described in r6; no issuer capability is inferred.

## 3. Scope and acceptance criteria amendment

The r6 nine-AC structure remains. This amendment changes the desired policy of the linked criteria as follows; every UAT case remains unexecuted:

| r6 AC | r7 disposition | Required behavior |
|---|---|---|
| AC-63-R7-01 (amends AC-63-R6-01) | Clarified | One agreed route authenticates active confidential clients before dispatch; legacy `client_secret` means Basic. |
| AC-63-R7-02 (amends AC-63-R6-02) | Amended | Basic and explicitly selected Post are supported; existing/default records are not silently migrated; non-confidential clients cannot use secret auth. |
| AC-63-R7-03 (amends AC-63-R6-03) | Amended | Apply the error/challenge matrix in O-3; credentials and parser internals are not exposed. |
| AC-63-R7-04 (amends AC-63-R6-04) | Amended | Duplicate, conflicting, or multiple authentication channels fail with `invalid_request`, without fallback or dispatch. |
| AC-63-R7-05 (amends AC-63-R6-05) | Amended | Enforce body-only Post, no credential query, explicit form encoding, and deterministic duplicate/header handling. |
| AC-63-R7-06 (amends AC-63-R6-06) | Amended | No credentials/verifier/raw exception in response or covered application logs; no raw grant-type reflection. |
| AC-63-R7-07 (amends AC-63-R6-07) | Preserved | Auth success still does not add grant dispatch/token issuance; all current grants remain fail-closed. |
| AC-63-R7-08 (amends AC-63-R6-08) | Amended, blocked | One POST route owned by `amr_oidc`, after sequencing/effective-owner agreement with ADDONS13-38. |
| AC-63-R7-09 (amends AC-63-R6-09) | Preserved | Odoo 13 / Python 3.7 compatibility must be evidenced on the authorized target; static source is insufficient. |

UAT amendment IDs are defined one-to-one in `UAT-DRAFT-r7.md`. No r6 actual is rewritten; r6 UAT records remain historical and NOT RUN.

## 4. Dependencies, rollback, and boundaries

Dependencies: ADDONS13-38 route migration/sequence disposition; Odoo 13/Python 3.7 native module composition; `oidc.client` selection and confidential-client policy; Odoo/Werkzeug form and repeated-header behavior; approved sanitized logging boundary. RFC 6749 §3.2 requires token-endpoint TLS, but this task neither configures nor verifies ingress TLS; release/QA must not send real credentials over plaintext or infer TLS from this source change. If repeated headers or effective route ownership cannot be proven at the authorized layer, stop and report BLOCKED.

No database migration is planned. Rollback of a later implementation must revert only isolated auth changes/tests in the agreed route owner; do not revert the ADDONS13-38 migration or reintroduce a duplicate route automatically. No rollback is executed here.

Out of scope: implementing grant/token issuance; refresh/code lifecycle; mTLS/private-key JWT; Discovery/authorization migration owned by ADDONS13-38; public-client secret authentication; TLS provisioning/ingress verification; deployment, production, external services, or data migration.

## 5. Gate status

- Owner-accepted r6: historical acceptance remains bound to the exact hashes in §1.
- Owner-approved O-1–O-6 recommendations are recorded as Lead dispositions in this amendment. That chat approval does not itself accept the exact r7 PRD/UAT bytes; request separate hash-bound acceptance before Step 1.
- Step 1: BLOCKED pending exact r7 artifact acceptance and ADDONS13-38 sequencing/effective-owner confirmation. No code/test/runtime/QA execution occurred in preparing this amendment.
- Steps 2–4: NOT STARTED; they remain serial and require their own evidence/authorization. Step 3 additionally requires a named disposable QA target, database access/create permission, run/retry limit, and cleanup scope.

## References

- RFC 6749, *The OAuth 2.0 Authorization Framework*, §§2.3, 2.3.1, 3.2, 3.2.1, 5.2. These provisions inform the protocol mapping above; they do not prove implementation conformance.
- RFC 7591, *OAuth 2.0 Dynamic Client Registration Protocol*, §2 (authentication-method metadata labels).
- RFC Editor Erratum 5708 (Verified; record lists §§3.1 and 3.2) and Erratum 8791 (Reported, not verified; §3.2). Erratum 8791's note conflicts with Erratum 5708's section listing; this amendment makes no broader duplicate/extension claim.
