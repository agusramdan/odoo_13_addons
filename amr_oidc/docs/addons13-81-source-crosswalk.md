# ADDONS13-81 source crosswalk (Step 1)

**Decision binding:** original source inventory `SOURCE-INVENTORY.md`, SHA-256 `b78cd5f5d0a2f35a255e686fe8d6c977cefbe9a1718127d3cb5c57f42eac684c`; current accepted PRD v4.7 SHA-256 `17a27cfaee80df92b6ad2481bd037ebf7f72c60065199e280e75be6d4daf360d` and UAT v4.7 SHA-256 `09508006e9a8e3ea2308d94a391e1fccbe035970bb17054a2e0ff7e05844cd4c`. Earlier supplement hashes `a12f87a986b2205ab104f9ba6d2666a6a00853a2f782f93e6c994b2bcd1e9979` (PRD) and `f627cfe132e065f7aba2bbbf79edaa892e8e892026bbaa79ed2ea08345df11e5` (UAT) are historical pre-sync bytes, not current accepted artifacts. Earlier v4.0/v4.1 decisions remain historical context; v4.5/v4.6 drafts are not represented as accepted.

This static source-to-decision crosswalk is not a UAT result. **UAT-19 remains NOT RUN.** It does not establish installed registry/MRO, HTTP dispatch, ACL enforcement, database state, live cryptographic validation, installation, or production safety. The accepted inventory's snapshot is not replaced by nearby inventories. `amr_resource` is unchanged and outside candidate scope. The Step 1 unit coverage for internal signing boundaries and caller authorization is listed below; it does not prove Odoo RPC dispatch guards or runtime authorization.

## Accepted decisions mapped to candidate

| Decision | Accepted disposition | Candidate evidence / exact location |
|---|---|---|
| OD-01 | Reject persistent `amr.token`; persistent `res.users.create_access_token` fails with controlled `UserError`. | No `amr.token` model in `amr_token/models/` or `amr_oidc/models/`; `amr_token/models/helper.py` is only an alias to `amr.oidc.helper`. `amr_oidc/models/res_users.py::ResUsers.create_access_token` raises `UserError`. |
| OD-02 | Preserve endpoint/authentication/response rules; grants unsupported. | Routes in `amr_oidc/controllers/main.py`; token helper `amr_oidc/models/token_helper.py::TokenHelper.oidc_token` fails closed. Adapter adds no grant implementation. |
| OD-03 | Database UUID defaults only when resource and audience are absent. During ENCODE, a supplied resource must be one nonempty string, overrides audience, maps only to outgoing `aud`, and is not emitted as a separate `resource` claim. Without resource, audience retains its supported nonempty string/list forms; explicit invalid values reject. | `amr_oidc/models/token_helper.py::TokenHelper._generate_token`, `_generate_user_token`, `_encode`; `amr_oidc/models/oidc_client.py::OidcClient._create_access_token`, `_client_credentials`; `amr_oidc/models/res_users.py::ResUsers.get_access_token`. Resource is normalized to effective audience before the user-token cache key. |
| OD-04 | Keep legacy `token_views.xml` unregistered or discard it. | `amr_token/views/token_views.xml` is not in `amr_token/__manifest__.py::data`; adapter manifest data is empty. |
| OD-05 | No glue addon is selected; provider and Resource Server remain independent without implicit integration. | No glue addon or provider-to-resource dependency is declared. HTTP response projection is local to `amr_oidc/controllers/main.py`; provider helper methods are mapped below and are not evidence of cross-addon integration. Runtime dispatch/MRO remains unverified. |
| OD-06 | Local fail-closed validation; asymmetric verification selects `alg` from the JWT header within the asymmetric allowlist and uses header `kid` only to select a configured trusted public key. Reject missing/unknown kid, disallowed/non-asymmetric alg, and alg/key mismatch. Configured signing algorithm selects signing only, not asymmetric verification. Live cryptographic verification remains NOT RUN. | `amr_oidc/models/token_helper.py::TokenHelper.decode`, `_token_strategy`, `TokenAsymmetric.decode`; key lookup is constrained by header-derived algorithm and kid. Offline tests verify dispatch/query behavior only, not real cryptography. |
| OD-07 | Optional one-way adapter only; no grants, persistence, or response glue. | `amr_token/models/helper.py::TokenHelper` inherits `amr.oidc.helper`; provider implementation is in `amr_oidc`. `amr_token` depends on provider, not vice versa. Runtime MRO is unverified. |
| OD-08 | Keep the independent Resource Server unchanged. | No `amr_resource` path changed; provider and adapter manifests do not depend on it. Static fact only, not installed dependency evidence. |
| Security issuance boundary | Secret/key accessors and token signing helpers are internal; access-token issuance is self-only except `base.group_system`, with checks before cache/signing/storage. | `amr_oidc/models/token_helper.py::_get_secret`, `TokenHelper._generate_*`, `_check_token_issuance_access`; `models/public_key.py::PublicKey._get_private_key/_generate_token`; `models/res_users.py::ResUsers.get_access_token`; `models/oidc_refresh_token.py::OidcRefreshToken._get_secret/_create_refresh_token`. Offline assertions are in `tests/unit/test_token_issuer_security.py`; actual Odoo RPC dispatch remains unverified. |

## Source helper surface: 35 symbols (34 class methods plus module function)

The bound inventory lists 34 class helper methods **and** module-level `get_algorith_config`; total 35 symbols. Candidate functions are in `amr_oidc/models/token_helper.py` unless stated. `amr_token/models/helper.py` supplies only the optional alias and no second implementation. Its registry-time resolution is not verified.

| Inventoried symbol(s) | Candidate mapping / disposition |
|---|---|
| `get_algorith_config` (module-level) | `amr_oidc/models/token_helper.py::get_algorith_config`; class constant `TokenHelper.ALGORITHM_CONFIG` derives from it. |
| `generate_key`, `private_key_to_pem`, `public_key_to_pem`, `create_public_key` | Internal signing/key material methods are `_generate_key`, `_private_key_to_pem`, `_public_key_to_pem`; `create_public_key` remains the model action entry point. `models/oidc_client.py::OidcClient.export_service_account` calls `TokenHelper._generate_key`. |
| `get_header_token` | `TokenHelper.get_header_token` in `amr_oidc/models/token_helper.py`. |
| `get_bearer_token` | `TokenHelper.get_bearer_token` in `amr_oidc/models/token_helper.py`; no separate provider extension class is imported by `models/__init__.py`. |
| `get_basic_auth` | `TokenHelper.get_basic_auth` in `amr_oidc/models/token_helper.py`; no separate provider extension class is imported by `models/__init__.py`. |
| `get_signature_type`, `get_signature_algorithm`, `get_expires_in`, `get_retention_in`, `get_secret`, `get_issuer`, `get_audience`, `get_token_endpoint`, `_service_account_endpoint_defaults` | Corresponding provider config methods in `amr_oidc/models/token_helper.py`; secret retrieval is private (`_get_secret`); audience behavior is OD-03. |
| `oidc_jwks` | `TokenHelper.oidc_jwks` in `amr_oidc/models/token_helper.py`; route handler `ControllerOIDC.well_known_jwks`. |
| `oidc_token` | `TokenHelper.oidc_token` in `amr_oidc/models/token_helper.py`; unsupported under OD-02. |
| `_do_password_grant`, `_do_challenge_grant`, `_do_digital_signature_grant` | Explicit OD-02 disposition: no callable grant implementation retained in provider or adapter. |
| `generate_user_token`, `encode`, `generate_token`, `generate_token_asymmetric`, `generate_token_secret` | Corresponding methods are internal (`_generate_user_token`, `_encode`, `_generate_token`, `_generate_token_asymmetric`, `_generate_token_secret`) in `amr_oidc/models/token_helper.py`. OD-03 resource-to-audience handling is encode-only; `_generate_token` removes the input `resource` before emitting claims. Configured algorithm controls signing; asymmetric verification dispatches from header alg/kid under OD-06. User issuance rejects a non-self target unless the actor has `base.group_system`, before signing. `_generate_user_token` does not call `amr_resource` user-category methods; the resource-specific `type` claim is omitted because provider category policy is not defined (OD-05). |
| `decode`, `validate`, `validate_secret`, `validate_asymmetric` | Historical inventory names retained as provenance; current `TokenHelper` exposes `decode()` only, not same-named `validate`, `validate_secret`, or `validate_asymmetric`. Both HTTP controller paths call `TokenHelper.decode`: introspection passes the authenticated `client_id` as audience and profile passes the database UUID. `TokenSecret.decode` handles the secret strategy; `TokenAsymmetric.decode` performs its own trusted-key lookup and JWT verification. `PublicKey.validate_token` exists as a separate record method in `models/public_key.py` and is not called by `TokenHelper.decode`. Legacy `validate` is not retained as a method name. |
| `oidc_introspect` | `TokenHelper.oidc_introspect` in `amr_oidc/models/token_helper.py`. The HTTP handler is separately implemented in `amr_oidc/controllers/main.py` and projects an allowlist; this source mapping does not claim Odoo RPC behavior was verified. |
| `oidc_profile` | `TokenHelper.oidc_profile` in `amr_oidc/models/token_helper.py`. The HTTP handler is separately implemented in `amr_oidc/controllers/main.py` and returns `sub`; this source mapping does not claim Odoo RPC behavior was verified. |
| `oidc_introspect_payload_response_enhance`, `oidc_profile_payload_response_enhance` | Both methods are present in `amr_oidc/models/token_helper.py` and currently return the input data unchanged; no adapter override is registered in this candidate. Their effective runtime dispatch remains unverified. |

Current provider registration: `amr_oidc/models/__init__.py` imports the helper definitions directly from `token_helper.py`; there is no provider `models/helper.py` extension in the registered source graph. `amr_token/models/helper.py::TokenHelper` is a separate optional alias inheriting `amr.oidc.helper`, not a provider override. Effective registry MRO itself is not asserted.

## Inventoried `res.users` methods

| Source method | Candidate path/function or disposition |
|---|---|
| `get_user_by_username` | `amr_oidc/models/res_users.py::ResUsers.get_user_by_username`. |
| `is_user_allow_create_token` | `amr_oidc/models/res_users.py::ResUsers.is_user_allow_create_token`. |
| `get_mobile_access_token` | `amr_oidc/models/res_users.py::ResUsers.get_mobile_access_token`; delegates to ephemeral token API. |
| `_get_access_token` | `amr_oidc/models/res_users.py::ResUsers._get_access_token`; cache key `(uid, effective audience, five-minute bucket)` distinguishes different resource values after resource-over-audience normalization. |
| `get_access_token` | `amr_oidc/models/res_users.py::ResUsers.get_access_token`; singleton and self/admin authorization checks precede token issuance; explicit resource must be a nonempty string and becomes the cache audience; no-argument audience remains `None`, allowing database UUID default. |
| `create_access_token` | `amr_oidc/models/res_users.py::ResUsers.create_access_token`; OD-01 controlled `UserError`, no persistent storage call. |
| `add_url_access_token` | `amr_oidc/models/res_users.py::ResUsers.add_url_access_token`; derives host only for `None`, preserves/rejects explicit empty. |
| `get_auto_login_url` | `amr_oidc/models/res_users.py::ResUsers.get_auto_login_url`; same `None`-only URL audience derivation; an explicit resource forwarded through kwargs overrides that audience under OD-03. |

## Routes and accepted disposition

Every route decorator declared by the current provider controller is enumerated below. The named 036fec4 native Odoo selector executed signed-token profile and introspection HTTP routes; its proxy-mode forwarded headers exercise Odoo's proxy-header secure-flag/route path, not a TLS socket or production proxy trust. Dispatcher inheritance beyond those exercised paths remains unverified.

| Registered path | Handler | Accepted disposition / source behavior |
|---|---|---|
| `/.well-known/jwks.json` | `ControllerOIDC.well_known_jwks` | Public GET; return helper JWKS JSON. Retain JWKS endpoint. |
| `/oidc/token` | `ControllerOIDC.api_oidc_token` | POST; 400 `unsupported_grant_type`; grants remain unsupported (OD-02). |
| `/.well-known/openid-configuration` | `ControllerOIDC.well_known_openid_configuration` | Public GET; 404; discovery explicitly unavailable. |
| `/oidc/authorize` | `ControllerOIDC.authorize` | Public; 400 `unsupported_response_type`; authorization unsupported. |
| `/oidc/auth` | `ControllerOIDC.authorize` | Alias of `/oidc/authorize`; same unsupported response. |
| `/oidc/continue` | `ControllerOIDC.continue_page` | Public website GET; renders `amr_oidc.custom_oidc_continue_template`; UI path only, no authorization grant. |
| `/oidc/login_form` | `ControllerOIDC.login_page` | Public website GET; renders `amr_oidc.custom_login_template`; UI path only. |
| `/oidc/authorize_continue` | `ControllerOIDC.authorize_continue` | User-authenticated route; 400 `unsupported_response_type`. |
| `/oidc/login/submit` | `ControllerOIDC.login_submit` | Public POST; 400 `unsupported_response_type`; no authorization issuance. |
| `/oidc/introspect` | `ControllerOIDC.api_oidc_introspect` | GET/POST declaration, auth none; handler accepts only secure POST/form token, authenticates registered introspection client, returns inactive or an allowlisted claim projection. Signed-token HTTP route exercised via Odoo proxy mode and synthetic forwarded headers; no TLS socket or production proxy-trust proof. |
| `/oidc/profile` | `ControllerOIDC.api_oidc_profile` | GET/POST declaration, auth none; handler requires bearer header and empty query/body, validates token and returns `sub`; signed-token HTTP route exercised; no TLS socket proof. |
| `/oidc/userinfo` | `ControllerOIDC.api_oidc_profile` | Alias of profile handler; same source behavior. |

## Settings and registered candidate resources

| Bound source setting/item | Candidate field/method, parameter, disposition |
|---|---|
| Algorithm | `amr_oidc.models.res_config_settings.ResConfigSettings.amr_token_algorithm`; `amr_token.algorithm`; choices HS256/RS256/ES256, default RS256. |
| Signature type | `amr_token_signature_type`; `amr_token.signature_type`; choices `secret` / `public_key`, required. |
| Secret | `amr_token_secret`; `amr_token.secret`; password widget in settings view. No secret value is reproduced here. |
| Secret algorithm | `amr_token_secret_algorithm`; `amr_token.secret_algorithm`; HS256/HS384/HS512, default HS256. |
| Public-key algorithm | `amr_token_public_key_algorithm`; `amr_token.public_key_algorithm`; ES256/ES256K/ES384/ES512, RS256/RS384/RS512, PS256/PS384/PS512; default RS256. |
| Retention | `amr_token_retention_in`; `amr_token.retention_in`; integer seconds. |
| Expiry | `amr_token_expires_in`; `amr_token.expires_in`; integer seconds. |
| Audience/config parameter | `amr_token_audience`; `database.uuid`; database UUID is the absent-audience default only (OD-03). |
| Computed `using_secret` | `amr_token_using_secret`, computed by `_compute_amr_token_using_secret`; true iff `amr_token_algorithm == "HS256"`. It has no config parameter. |
| Create public key action | `ResConfigSettings.action_create_public_key`; calls `amr.oidc.helper.create_public_key(amr_token_public_key_algorithm)` via sudo. |
| Legacy module toggles | Source fields `module_amr_token_oauth` / other toggles are not retained as active candidate settings; no accepted contract restores them. |

Candidate source paths: model `amr_oidc/models/res_config_settings.py`; view `amr_oidc/views/res_config_settings_views.xml`; registration `amr_oidc/__manifest__.py`. The settings view inherits `base_setup.res_config_settings_view_form`, uses `amr_token_config`, and exposes signature type, secret, secret/public-key algorithm, expiry, and create-key action; retention, audience, computed field, and algorithm are not displayed there. This is declaration evidence only.

Exact `amr_oidc/__manifest__.py` data registrations, in declared order: `security/res_groups.xml`; `views/res_config_settings_views.xml`; `security/ir.model.access.csv`; `data/oidc_client_grants.xml`; `views/public_key_views.xml`; `views/oidc_client_views.xml`; `views/oidc_authorization_code_views.xml`; `views/menuitem.xml`; `views/login_template.xml`; `wizard/service_account.xml`. Demo registration: `demo/public_key_demo.xml`. These are candidate registrations, not install proof. `amr_token/__manifest__.py` has `depends: ['amr_oidc']` and `data: []`; legacy `amr_token/views/token_views.xml` is unregistered. Source `amr_token/security/ir.model.access.csv` was header-only; it is not registered by the adapter. Provider ACL declarations are in `amr_oidc/security/ir.model.access.csv` and group declarations in `amr_oidc/security/res_groups.xml`.

## UAT-19 source-item disposition: tests and artifacts

### Provider (`amr_oidc`) current candidate tests

`amr_oidc/tests/integration/test_introspect_query_rejection.py` is registered as an Odoo `HttpCase`. It includes cleartext rejection and signed-token introspection/profile HTTP cases. On 036fec4, the native Odoo selector executed the signed-token cases; introspection used `--proxy-mode` with synthetic `X-Forwarded-Proto/Host`, proving Odoo's proxy-header secure-flag/route path only—not TLS socket or production proxy trust. Query rejection also has isolated controller coverage in `tests/unit/test_standalone_package.py`, using Odoo 13's query/form-to-route-kwargs mapping. Formal UAT-19 remains NOT RUN.

Both `amr_oidc/tests/__init__.py` and `amr_oidc/tests/integration/__init__.py` import exactly these eight Odoo integration modules under `amr_oidc/tests/integration/`: `test_public_key_ownership.py`, `test_public_key_orm.py`, `test_jwks_route.py`, `test_introspect_query_rejection.py`, `test_replay_acl.py`, `test_oidc_client_identity.py`, `test_client_secret_verifier.py`, and `test_client_registration.py`. `test_helper_decode.py` is also under `tests/integration/` but is not in those imports.

| Exact path | Disposition / runner |
|---|---|
| `amr_oidc/tests/unit/test_capability_fail_closed.py` | Offline `unittest.TestCase`; now in `tests/unit`, not imported by addon initializer; collected by isolated Python 3.7.9 / pytest 7.4.4 unit runner. Moved from `amr_oidc/tests/test_capability_fail_closed.py`; imports support by explicit file path. |
| `amr_oidc/tests/unit/test_package_contract.py` | Offline unit test; isolated unit runner; not addon-registered. Reconciles the former candidate filename `amr_oidc/tests/test_package_contract.py` named in source/addendum evidence. |
| `amr_oidc/tests/unit/test_provider_ownership.py` | Offline unit test; isolated unit runner; not addon-registered. |
| `amr_oidc/tests/unit/test_token_issuer_security.py` | Offline security unit test for internal signing/access boundaries; isolated unit runner; not addon-registered. Odoo RPC dispatch remains unverified. |
| `amr_oidc/tests/unit/test_standalone_package.py` | Offline unit tests for resource precedence/propagation, audience-only claims, cache audience selection and defaults; isolated unit runner; not addon-registered. |
| `amr_oidc/tests/unit/test_asymmetric_header_verification.py` | Offline component tests for header alg/kid dispatch, allowlist rejection and exact trusted-key lookup; mocks do not establish real signature cryptography; isolated unit runner; not addon-registered. |
| `amr_oidc/tests/integration/test_helper_decode.py` | `TransactionCase` referencing `amr.resource.helper`; excluded from the provider's eight imports and not part of the offline unit run. It is not the Resource Server's `test_helper.py`. |
| `amr_oidc/tests/support.py` | Shared isolated import doubles used by offline tests; not a test module/runner target and not imported through Odoo test initializer. |
| `amr_oidc/tests/test_capability_fail_closed.py` | Former path; moved (not retained) to `tests/unit/test_capability_fail_closed.py`; source inventory/addendum cite this historical path. |
| `amr_oidc/tests/test_package_contract.py` | Former path; candidate contract is now `tests/unit/test_package_contract.py`; source inventory/addendum cite the historical path. |
| `amr_resource/tests/test_helper.py` | Resource-owned, unchanged Odoo test; resource test registration/ownership remains with `amr_resource`; not provider test evidence and not run here. |

### Adapter (`amr_token`) current candidate tests

`amr_token/tests/__init__.py` imports `amr_token/integration_tests/test_public_key_orm.py`; that is the adapter's registered Odoo integration test path and was not run as an Odoo integration test here. `amr_token/tests/unit/test_adapter_boundary.py` is the current offline isolated adapter suite; it is not imported by `tests/__init__.py`.

The following exact top-level files remain **legacy/unregistered** offline files under `amr_token/tests/`; they are not current test evidence and were not included in the unit runner:

`amr_token/tests/test_controller_contract.py`, `amr_token/tests/test_data_contract.py`, `amr_token/tests/test_demo_contract.py`, `amr_token/tests/test_generate_key_action.py`, `amr_token/tests/test_helper_configuration.py`, `amr_token/tests/test_helper_key_generation.py`, `amr_token/tests/test_jwks_contract.py`, `amr_token/tests/test_manifest_contract.py`, `amr_token/tests/test_module_registration.py`, `amr_token/tests/test_oidc_grants.py`, `amr_token/tests/test_oidc_user_responses.py`, `amr_token/tests/test_private_key_source_lookup.py`, `amr_token/tests/test_private_key_sources.py`, `amr_token/tests/test_public_key_contract.py`, `amr_token/tests/test_public_key_validation.py`, `amr_token/tests/test_res_users_contract.py`, `amr_token/tests/test_resource_helper_extension.py`, `amr_token/tests/test_settings_contract.py`, `amr_token/tests/test_token_helper_lifecycle.py`, and `amr_token/tests/test_token_methods.py`. None are imported in `amr_token/tests/__init__.py`; they are not asserted as executed.

The accepted addendum's source-test anchors `amr_oidc/tests/test_capability_fail_closed.py`, `amr_oidc/tests/test_package_contract.py`, and `amr_oidc/tests/test_introspect_query_rejection.py` are accounted for above: the first two candidate offline tests are under `tests/unit`; current `integration/test_introspect_query_rejection.py` is in the eight Odoo imports. The bound inventory's `amr_oidc/tests/test_helper_decode.py` is now at `amr_oidc/tests/integration/test_helper_decode.py` and separately excluded as described. Source test references are contracts to reconcile, not test verdicts.

### Other UAT-19 mappings

| UAT-19 item | Candidate mapping / disposition |
|---|---|
| OIDC models | Provider declarations under `amr_oidc/models/`, imported by `amr_oidc/models/__init__.py`; the main asymmetric helper path is `TokenHelper.decode` → `TokenAsymmetric.decode` with trusted-key lookup on `amr.public.key`. `PublicKey.validate_token` is a separate record method, not called by `TokenHelper.decode`. |
| Missing persistent token model | No candidate `_name = 'amr.token'`; OD-01 controlled `UserError`. Static source fact only. |
| Legacy `token_views.xml` | `amr_token/views/token_views.xml` deliberately unregistered (`amr_token/__manifest__.py::data == []`), OD-04. |
| ACL, data, manifest | Exact provider data/demo registrations are itemized above; adapter data empty; source adapter ACL CSV was header-only. Declarations do not establish effective ACL/install state. |
| No glue / no Resource Server dependency | OD-05 adapter lacks hooks; OD-08 resource addon unchanged and omitted from provider/adapter dependency lists. |

Step 1 native Odoo selector and offline unit results are recorded in a separate candidate-bound execution report. This crosswalk maps source-owned items to candidate paths and active test identities; it is not execution evidence and does not establish the aggregate UAT-19 oracle.

**UAT-19 status: NOT RUN.** The separate Step 1 execution report records only the named Odoo HTTP/ORM test methods and offline unit suites that actually ran; those results do not cover or satisfy the full UAT-19 source inventory. Do not infer unexecuted registry, ACL, route, cryptographic, database, installation, or production behavior.
