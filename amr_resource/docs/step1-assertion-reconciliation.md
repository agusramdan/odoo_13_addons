# Step 1 assertion preservation reconciliation

Scope: implementation reconciliation against checkpoint `eafaff21e1761970517c2fdab83d1f3166315870`, not an independent review or acceptance gate. Only the two native test files and this candidate checklist were changed in this reconciliation. Accepted Step 0 documents and production implementation were not edited.

Each baseline assertion was compared within its original method, including surrounding fixtures, mock expectations, exception branches, and loops. Compatible behavior is retained; contract-rejected behavior has explicit replacement assertions rather than silent removal. Assertion-call counts below are static inventories, not runtime coverage or acceptance evidence. Loop-backed cases make a one-to-one call-count target inappropriate.

## Per-method semantic checklist

### `tests/test_helper.py`

| Method | Preserved/restored checks | Rejected baseline and replacement checks |
| --- | --- | --- |
| `test_ut01_resolution_and_compute` | Issuer/audience resolution, audience collection shape, explicit selector handling, local classification, configuration removal behavior. | D-02 rejects parameter-key and base-URL inference. Both legacy selector configurations and deletion of their referenced parameters leave registry resolution unchanged; legacy URL/UUID classifications and ignored explicit issuer fail. D-02 settings selectors and computed previews are absent. Inactive registry selection raises Unauthorized for all three getters instead of returning false placeholders. |
| `test_ut03_extraction_precedence` | All six parameter aliases in precedence order, empty parameter result, custom-header precedence, environment-over-header bearer precedence, valid bearer extraction, empty bearer result. | D-11 malformed presented bearer now raises Unauthorized rather than becoming absent; each formerly malformed fixture remains checked. |
| `test_ut04_discovery_and_errors` | Complete configuration return shape, JWKS return value and exact outbound destination, HTTP and JSON/transport failure branches. | D-02 static configuration replaces Discovery: configuration lookup performs no fetch. Unknown and slash-normalized issuer candidates fail without fetch. D-03/D-11 failures become Unauthorized; malformed JWKS schemas also fail. There is no obsolete requests-response status mock after moving transport behind the shared boundary. |
| `test_ut04_issuance_and_wrappers` | All three issuer alias precedence cases, exactly-one-profile default selection, response dictionary, scalar encode result, grant payload, accepted client-ID handling, decode delegation including ignored extra keyword arguments. | Caller secrets, combined caller credentials, wrong client IDs and unknown issuers reject before fetch; exact trusted endpoint, request data and headers are checked. HTTP/JSON failures, malformed responses and missing token endpoint reject generically. Old absent-selector error becomes explicit success only for the unique registered profile. |
| `test_ut05_introspection_and_hs` | Explicit issuer selection, return claims, validation-through-introspection, credential cases, absent endpoint, HTTP/JSON and inactive/error branches. | D-01 rejects HS; D-03 rejects caller URLs, caller secrets and GET-body behavior. Invalid paths do not fetch or decode token claims. Opaque success checks provenance, anchored issuer, complete claims and the exact trusted form request. Wrong client ID/issuer reject before fetch. All former inactive cases remain, with additional strict-boolean, missing-activity and audience negatives. Audience checking replaces the obsolete assertion that it was never consulted. |
| `test_ut06_verified_jwt_and_failures` | Complete verified payload; existing payload key/algorithm metadata is not overwritten; local validation avoids JWKS; remote destination and exact verified-decode algorithm/issuer/audience/required-claim options; signature/audience/issuer verification failures; malformed input and header failures. | D-01/D-11 replace incidental AttributeError/library exceptions with Unauthorized. Local and remote RSA success use synthetic in-memory keys. Required-claim and token-type negatives remain. Verification-stage failure assertions confirm both decode phases were reached. A cumulative no-logging assertion replaces the rejected raw-token logging expectation. Direct bounded JWKS replaces obsolete PyJWKClient-constructor/Discovery assertions. |
| `test_ut07_matching` | Successful user result, UID, user predicate, empty-record predicate, payload-returning get_validate_user, empty validated result returning None, and token-login wrapper. | D-05 exact issuer-subject binding wins over a real competing email account; login/email/unbound/missing-sub fallback is rejected. Both normal and machine claims reject an inactive bound user. D-11 plain dictionaries cannot enter either matching or UID resolution; only internal verified claims enter successful resolution. |

### `tests/test_contracts.py`

| Method | Preserved/restored checks | Rejected baseline and replacement checks |
| --- | --- | --- |
| `test_ut02_settings_action_and_declarations` | Full legacy base-URL edit action dictionary, unchanged parameter value, missing-parameter/no-creation behavior, settings block label/data label/group, issuer field absence, freeze parameter key, and no synthetic default on freeze declaration. | Removed selector defaults are explicitly absent; audience selector is absent in both model and view. Registry action model/type/view mode and trust-admin-gated object button replace the obsolete selector-dependent edit UI. Freeze remains present without a condition referencing a removed field. |
| `test_ut07_auth_machine_params_and_metadata` | Both actual machine and parameter entry points, extraction and validation/resolver call arguments, successful return, UID/token/payload metadata, same-UID preservation, missing-user rejection, unused custom token-header path and existing scope no-op. | Validation failure is Unauthorized, does not reach the resolver and cannot mutate metadata. Resolver failure also preserves UID and metadata. Empty get_jwt_payload remains empty when provenance is absent. |
| `test_ut07_session_params_bearer_order` | Valid session short circuit and return; successful token authentication changes UID; both validation and resolver rejection; successful explicit params and params failure. | D-11 explicitly checks session then bearer, no params fallback after either bearer failure, and params only after bearer absence. The real shared token-authentication method is used rather than an always-failing replacement. The session-failure fixture uses Unauthorized, matching the actual supported branch. |
| `test_ut08_user_predicates_environment_and_stubs` | All user/group predicates, identity environment, empty-user identity, token eligibility, URL no-op results, and matching/nonmatching decode results remain. | Non-superuser environment replaces rejected implicit elevation; explicit UserError replaces the accidental TypeError from the old token stub. Neither check was removed. |
| `test_ut08_context` | Verified marker returns the identical record without bearer extraction or validation; successful validation attaches identical payload; other-user context returns the original record; verified validate=False request payload attaches without validation. | D-11 rejects forged marker, unverified request dictionary and missing bearer with Unauthorized. Forged-marker rejection checks that bearer extraction and validation actually occur; unverified validate=False rejection still confirms validation was not invoked. Context-managed patches now use patchers directly, rather than entering the mock returned by the existing patch_model helper. |
| `test_ut08_session_helper` | Entire baseline method AST preserved: session rotation, principal/DB flags, context retrieval, token failure cleanup and explicit-token empty-user cases. | No baseline behavior removed or replaced. |
| `test_ut09_direct_controller_contract` | Entire baseline method AST preserved: responses, URL dispatch, missing-method behavior, redirect/RPC contracts, private-method denial and error conversion. | No baseline behavior removed or replaced. |
| `test_ut10_wizard_and_seed` | Every wizard, required-field, duplicate, seed, group, dependency, data-file and import assertion retained. | Only the expected manifest version changes to the candidate's additive migration version. |

## Static inventory

- `test_helper.py`: 7 baseline and 7 reconciled test methods; assertion call sites 70 baseline, 50 before reconciliation, 85 reconciled.
- `test_contracts.py`: 8 baseline and 8 reconciled test methods; assertion call sites 111 baseline, 97 before reconciliation, 140 reconciled.
- No baseline test methods removed. Repeated cumulative logging checks were consolidated; no assertion-count padding was used.
- Native files parse/compile statically; whitespace validation passes. Staged path count remains zero.

## Execution evidence and limits

Authorized offline suite command:

```text
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges -e PYTHONDONTWRITEBYTECODE=1 -v /home/ubuntu/worktrees/ADDONS13-46-dev:/src:ro -w /src --entrypoint python addons13-34-py379-requirements:local -B -m unittest discover -s amr_resource/tests -p 'test_*_unit.py'
```

Final authorized offline rerun: 74 tests in 1.002 seconds, OK, exit status 0. This document does not claim that the native tests executed.

The two reconciled files contain Odoo SavepointCase tests. They were inspected and statically compiled only, as authorized. Offline unit-suite success does not establish native Odoo/ORM/ACL/HTTP behavior or installation/upgrade success. No Odoo, database, external issuer/network, independent gate, staging, commit, push, PR, merge or deployment was performed. Existing local checkpoint/report/manifest artifacts were preserved.
