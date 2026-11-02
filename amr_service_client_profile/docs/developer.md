# Developer Guide — Service Client Issuer Profile

## Addon boundary

- Core addon: `amr_service_client`; depends on `base`, `web`, and `base_setup`, and contains the manual OAuth `token_uri` path.
- Optional extension: `amr_service_client_profile`; depends on `amr_service_client` and `amr_resource`.
- Resource owns `oidc.issuer.register` and `amr_resource.group_oidc_trust_admin`. The extension adds `issuer_profile_id` to the existing transient `service.credential.wizard` using Odoo `_inherit` without a new `_name`, and inherits the core wizard view.
- Keep issuer model/group/XML-ID references out of core. Do not change persistent credential JSON or Resource profile records as part of this extension.

## Profile enforcement

The field is group-restricted in ORM metadata and in the inherited view. The extension also guards `create` and `write` when an untrusted user submits `issuer_profile_id`, because Odoo can silently discard restricted-field values before they reach the wizard method. `_oauth_token_uri()` additionally checks the user, rejects simultaneous manual/profile input, and validates profile activity, token endpoint, and exact client-ID match for the two OAuth credential types. No profile delegates to the core manual URI path.

## Verification

Offline focused contract tests (using repository doubles; not Odoo ORM integration):

```sh
PYTHONPATH=tests/addons13_27 python3 -B -m unittest discover -s amr_service_client_profile/tests -p 'test_*_unit.py' -v
```

This is an offline unit/contract oracle, not an Odoo addon test. It imports shared doubles via `PYTHONPATH`; keep it out of Odoo's loader. The Odoo-native `SavepointCase` tests live in `integration_tests/` and are registered through `tests/__init__.py` only. They exercise profile-backed wizard generation and ORM authorization/validation with the real registry.

Integration runner (Odoo 13 only; use a fresh disposable PostgreSQL database on an isolated internal-only network, with no published ports and candidate source mounted read-only):

```sh
# Run inside the pinned Odoo 13.0 / Python 3.7.3 test runtime.
/usr/bin/odoo -d "$DB_NAME" \\
  --db_host="$DB_HOST" --db_port=5432 \\
  --db_user="$DB_USER" --db_password="$DB_PASSWORD" \\
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,"$ADDONS_ROOT" \\
  --init=amr_service_client_profile --test-enable --stop-after-init \\
  --log-level=test --test-tags=/amr_service_client_profile --no-http
```

Require logs showing the intended test methods and a nonzero test count; installation or zero-test success is not test evidence. Verify the database is absent before the run; destroy the database, test container(s), and isolated network afterward and verify they are absent.

The new integration suite was exercised on Odoo 13.0-20221005 / Python 3.7.3 with a fresh PostgreSQL 13 database on a dedicated internal-only Docker network; all five test methods passed. This scoped result is not a substitute for full UAT, browser UI acceptance, or production validation.

The repository-wide offline suite has existing failures/errors on both the approved baseline and the feature candidate; compare exact test names before attributing them to this addon. Never use a live database, provider, or real credential to run these checks.
