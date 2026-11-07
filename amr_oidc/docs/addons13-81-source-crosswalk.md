# ADDONS13-81 source crosswalk (Step 1)

**Decision binding:** accepted PRD/UAT v4.0 and addendum v4.1; bound source inventory `SOURCE-INVENTORY.md`, SHA-256 `b78cd5f5d0a2f35a255e686fe8d6c977cefbe9a1718127d3cb5c57f42eac684c`.

This static source-to-decision crosswalk is not a UAT result. **UAT-19 remains NOT RUN.** It does not establish installed registry/MRO, HTTP dispatch, ACL enforcement, database state, live cryptographic validation, installation, or production safety. The accepted inventory's snapshot is not replaced by nearby inventories. `amr_resource` is unchanged and outside candidate scope. The Step 1 unit coverage for internal signing boundaries and caller authorization is listed below; it does not prove Odoo RPC dispatch guards or runtime authorization.

## Accepted decisions mapped to candidate

| Decision | Accepted disposition | Candidate evidence / exact location |
|---|---|---|
| OD-01 | Reject persistent `amr.token`; persistent `res.users.create_access_token` fails with controlled `UserError`. | No `amr.token` model in `amr_token/models/` or `amr_oidc/models/`; `amr_token/models/helper.py` is only an alias to `amr.oidc.helper`. `amr_oidc/models/res_users.py::ResUsers.create_access_token` raises `UserError`. |
| OD-02 | Preserve endpoint/authentication/response rules; grants unsupported. | Routes in `amr_oidc/controllers/main.py`; token helper `amr_oidc/models/token_helper.py::TokenHelper.oidc_token` fails closed. Adapter adds no grant implementation. |
| OD-03 | Database UUID only defaults when audience is absent (`None`); explicit audience must be a non-empty string or a non-empty string array; invalid explicit/default values are rejected. | `amr_oidc/models/token_helper.py::TokenHelper.get_audience`, `_validate_audience`, `generate_token`, `generate_user_token`; `amr_oidc/models/res_users.py::ResUsers.get_access_token` defaults `audience=None`. URL helpers derive only for `None`. |
| OD-04 | Keep legacy `token_views.xml` unregistered or discard it. | `amr_token/views/token_views.xml` is not in `amr_token/__manifest__.py::data`; adapter manifest data is empty. |
| OD-05 | No response-enrichment hook/cross-addon response glue. | Adapter `amr_token/models/helper.py::TokenHelper` is an inheritance alias; legacy response hook names are absent. Controller response projection is local to `amr_oidc/controllers/main.py`. |
| OD-06 | Local fail-closed validation; asymmetric JWT `kid` resolves to active OIDC key. Do not claim live crypto verification. | `amr_oidc/models/token_helper.py::TokenHelper.validate`, `validate_secret`, `validate_asymmetric`; `amr_oidc/models/public_key.py::PublicKey.validate_token` rejects inactive/missing active key and JWT header `kid` mismatch. |
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
| `get_bearer_token` | Base `TokenHelper.get_bearer_token` in `amr_oidc/models/token_helper.py`; effective provider extension override is `amr_oidc/models/helper.py::TokenHelper.get_bearer_token`. |
| `get_basic_auth` | Base `TokenHelper.get_basic_auth` in `amr_oidc/models/token_helper.py`; effective provider extension override is `amr_oidc/models/helper.py::TokenHelper.get_basic_auth`. |
| `get_signature_type`, `get_signature_algorithm`, `get_expires_in`, `get_retention_in`, `get_secret`, `get_issuer`, `get_audience`, `get_token_endpoint`, `_service_account_endpoint_defaults` | Corresponding provider config methods in `amr_oidc/models/token_helper.py`; secret retrieval is private (`_get_secret`); audience behavior is OD-03. |
| `oidc_jwks` | `TokenHelper.oidc_jwks` in `amr_oidc/models/token_helper.py`; route handler `ControllerOIDC.well_known_jwks`. |
| `oidc_token` | `TokenHelper.oidc_token` in `amr_oidc/models/token_helper.py`; unsupported under OD-02. |
| `_do_password_grant`, `_do_challenge_grant`, `_do_digital_signature_grant` | Explicit OD-02 disposition: no callable grant implementation retained in provider or adapter. |
| `generate_user_token`, `encode`, `generate_token`, `generate_token_asymmetric`, `generate_token_secret` | Corresponding methods are internal (`_generate_user_token`, `_encode`, `_generate_token`, `_generate_token_asymmetric`, `_generate_token_secret`) in `amr_oidc/models/token_helper.py`; configured algorithms and OD-03 apply. User issuance rejects a non-self target unless the actor has `base.group_system`, before signing. `_generate_user_token` does not call `amr_resource` user-category methods; the resource-specific `type` claim is omitted because provider category policy is not defined (OD-05). |
| `decode`, `validate`, `validate_secret`, `validate_asymmetric` | Corresponding `TokenHelper` methods in `amr_oidc/models/token_helper.py`; asymmetric lookup/validation is local and fail-closed (OD-06). |
| `oidc_introspect` | Base `TokenHelper.oidc_introspect` in `amr_oidc/models/token_helper.py`; effective provider extension override `amr_oidc/models/helper.py::TokenHelper.oidc_introspect` returns inactive. Route logic is in controller. |
| `oidc_profile` | Base `TokenHelper.oidc_profile` in `amr_oidc/models/token_helper.py`; effective provider extension override `amr_oidc/models/helper.py::TokenHelper.oidc_profile` returns inactive. Route logic is in controller. |
| `oidc_introspect_payload_response_enhance`, `oidc_profile_payload_response_enhance` | Explicit OD-05 disposition: absent, unsupported extension APIs; no adapter hook replacement. |

Effective override qualification: `amr_oidc/models/helper.py::TokenHelper` overrides `get_bearer_token`, `get_basic_auth`, `oidc_introspect`, and `oidc_profile`; the base definitions remain mapped above as the directly corresponding base methods. Effective registry MRO itself is not asserted.

## Inventoried `res.users` methods

| Source method | Candidate path/function or disposition |
|---|---|
| `get_user_by_username` | `amr_oidc/models/res_users.py::ResUsers.get_user_by_username`. |
| `is_user_allow_create_token` | `amr_oidc/models/res_users.py::ResUsers.is_user_allow_create_token`. |
| `get_mobile_access_token` | `amr_oidc/models/res_users.py::ResUsers.get_mobile_access_token`; delegates to ephemeral token API. |
| `_get_access_token` | `amr_oidc/models/res_users.py::ResUsers._get_access_token`; cache key `(uid, audience, five-minute bucket)` distinguishes `None` from client/URL audiences. |
| `get_access_token` | `amr_oidc/models/res_users.py::ResUsers.get_access_token`; singleton and self/admin authorization checks precede cache access; no-argument audience remains `None`, allowing database UUID default. |
| `create_access_token` | `amr_oidc/models/res_users.py::ResUsers.create_access_token`; OD-01 controlled `UserError`, no persistent storage call. |
| `add_url_access_token` | `amr_oidc/models/res_users.py::ResUsers.add_url_access_token`; derives host only for `None`, preserves/rejects explicit empty. |
| `get_auto_login_url` | `amr_oidc/models/res_users.py::ResUsers.get_auto_login_url`; same `None`-only derivation and empty-audience behavior. |

## Routes and accepted disposition (declaration map, not HTTP execution)

Every route decorator declared by the current provider controller is enumerated below. These are source declarations and static handler behavior; **no HTTP route execution or dispatcher inheritance was verified**.

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
| `/oidc/introspect` | `ControllerOIDC.api_oidc_introspect` | GET/POST declaration, auth none; handler accepts only secure POST/form token, authenticates registered introspection client, returns inactive or an allowlisted claim projection. Declaration is not runtime route proof. |
| `/oidc/profile` | `ControllerOIDC.api_oidc_profile` | GET/POST declaration, auth none; handler requires bearer header and empty query/body, validates token and returns `sub`; no profile enrichment. |
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

`amr_oidc/tests/test_introspect_query_rejection.py` is registered as an Odoo `HttpCase` and asserts cleartext rejection only; it does not prove HTTPS success or query rejection. Secure handler behavior and query rejection are covered by isolated controller tests in `tests/unit/test_standalone_package.py`, using Odoo 13's query/form-to-route-kwargs mapping. Actual HTTPS transport/dispatch remains NOT RUN.

`amr_oidc/tests/__init__.py` imports exactly these eight Odoo integration modules (registered for Odoo discovery, not run as integration tests here): `amr_oidc/tests/test_public_key_ownership.py`, `amr_oidc/tests/test_public_key_orm.py`, `amr_oidc/tests/test_jwks_route.py`, `amr_oidc/tests/test_introspect_query_rejection.py`, `amr_oidc/tests/test_replay_acl.py`, `amr_oidc/tests/test_oidc_client_identity.py`, `amr_oidc/tests/test_client_secret_verifier.py`, and `amr_oidc/tests/test_client_registration.py`.

| Exact path | Disposition / runner |
|---|---|
| `amr_oidc/tests/unit/test_capability_fail_closed.py` | Offline `unittest.TestCase`; now in `tests/unit`, not imported by addon initializer; collected by isolated Python 3.7.9 unit runner. Moved from `amr_oidc/tests/test_capability_fail_closed.py`; imports support by explicit file path. |
| `amr_oidc/tests/unit/test_package_contract.py` | Offline unit test; isolated unit runner; not addon-registered. Reconciles the former candidate filename `amr_oidc/tests/test_package_contract.py` named in source/addendum evidence. |
| `amr_oidc/tests/unit/test_provider_ownership.py` | Offline unit test; isolated unit runner; not addon-registered. |
| `amr_oidc/tests/unit/test_standalone_package.py` | Offline unit test; isolated unit runner; not addon-registered. |
| `amr_oidc/tests/test_helper_decode.py` | `TransactionCase` referencing `amr.resource.helper`; excluded from the provider's eight imports and not part of the offline unit run. It is not the Resource Server's `test_helper.py`. |
| `amr_oidc/tests/support.py` | Shared isolated import doubles used by offline tests; not a test module/runner target and not imported through Odoo test initializer. |
| `amr_oidc/tests/test_capability_fail_closed.py` | Former path; moved (not retained) to `tests/unit/test_capability_fail_closed.py`; source inventory/addendum cite this historical path. |
| `amr_oidc/tests/test_package_contract.py` | Former path; candidate contract is now `tests/unit/test_package_contract.py`; source inventory/addendum cite the historical path. |
| `amr_resource/tests/test_helper.py` | Resource-owned, unchanged Odoo test; resource test registration/ownership remains with `amr_resource`; not provider test evidence and not run here. |

### Adapter (`amr_token`) current candidate tests

`amr_token/tests/__init__.py` imports `amr_token/integration_tests/test_public_key_orm.py`; that is the adapter's registered Odoo integration test path and was not run as an Odoo integration test here. `amr_token/tests/unit/test_adapter_boundary.py` is the current offline isolated adapter suite; it is not imported by `tests/__init__.py`.

The following exact top-level files remain **legacy/unregistered** offline files under `amr_token/tests/`; they are not current test evidence and were not included in the unit runner:

`amr_token/tests/test_controller_contract.py`, `amr_token/tests/test_data_contract.py`, `amr_token/tests/test_demo_contract.py`, `amr_token/tests/test_generate_key_action.py`, `amr_token/tests/test_helper_configuration.py`, `amr_token/tests/test_helper_key_generation.py`, `amr_token/tests/test_jwks_contract.py`, `amr_token/tests/test_manifest_contract.py`, `amr_token/tests/test_module_registration.py`, `amr_token/tests/test_oidc_grants.py`, `amr_token/tests/test_oidc_user_responses.py`, `amr_token/tests/test_private_key_source_lookup.py`, `amr_token/tests/test_private_key_sources.py`, `amr_token/tests/test_public_key_contract.py`, `amr_token/tests/test_public_key_validation.py`, `amr_token/tests/test_res_users_contract.py`, `amr_token/tests/test_resource_helper_extension.py`, `amr_token/tests/test_settings_contract.py`, `amr_token/tests/test_token_helper_lifecycle.py`, and `amr_token/tests/test_token_methods.py`. None are imported in `amr_token/tests/__init__.py`; they are not asserted as executed.

The accepted addendum's source-test anchors `amr_oidc/tests/test_capability_fail_closed.py`, `amr_oidc/tests/test_package_contract.py`, and `amr_oidc/tests/test_introspect_query_rejection.py` are accounted for above: the first two candidate offline tests are under `tests/unit`; current `test_introspect_query_rejection.py` is in the eight Odoo imports. The bound inventory's `amr_oidc/tests/test_helper_decode.py` is separately excluded as described. Source test references are contracts to reconcile, not test verdicts.

### Other UAT-19 mappings

| UAT-19 item | Candidate mapping / disposition |
|---|---|
| OIDC models | Provider declarations under `amr_oidc/models/`, imported by `amr_oidc/models/__init__.py`; asymmetric validation in `models/public_key.py::PublicKey.validate_token`. |
| Missing persistent token model | No candidate `_name = 'amr.token'`; OD-01 controlled `UserError`. Static source fact only. |
| Legacy `token_views.xml` | `amr_token/views/token_views.xml` deliberately unregistered (`amr_token/__manifest__.py::data == []`), OD-04. |
| ACL, data, manifest | Exact provider data/demo registrations are itemized above; adapter data empty; source adapter ACL CSV was header-only. Declarations do not establish effective ACL/install state. |
| No glue / no Resource Server dependency | OD-05 adapter lacks hooks; OD-08 resource addon unchanged and omitted from provider/adapter dependency lists. |

Step 1 offline runner verification on the candidate: Python 3.7.9 skill runner `scripts/run_tests.py --addon amr_oidc` completed **59 passed**; `scripts/run_tests.py --addon amr_token` completed **2 passed**. The focused issuance-security module completed **9 passed**. These are isolated unit/contract suite results only; no Odoo server/RPC dispatch, ORM registry, ACL, database, HTTP or UAT was run.

**UAT-19 status: NOT RUN.** This crosswalk maps source items and dispositions and records isolated suite execution separately; it does not convert those test runs into UAT-19, Odoo integration, runtime, cryptographic, registry, HTTP, ACL, or installation evidence.
