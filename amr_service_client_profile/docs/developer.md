# Developer Guide — Service Client Issuer Profile

## Addon boundary

- Core addon: `amr_service_client`; depends on `base`, `web`, and `base_setup`, and contains the manual OAuth `token_uri` path.
- Optional extension: `amr_service_client_profile`; depends on `amr_service_client` and `amr_resource`.
- Resource owns `oidc.issuer.register` and `amr_resource.group_oidc_trust_admin`. The extension adds `issuer_profile_id` to the existing transient `service.credential.wizard` using Odoo `_inherit` without a new `_name`, and inherits the core wizard view.
- Keep issuer model/group/XML-ID references out of core. Do not change persistent credential JSON or Resource profile records as part of this extension.

## Profile enforcement

The field is group-restricted in ORM metadata and in the inherited view. The extension also guards `create` and `write` when an untrusted user submits `issuer_profile_id`, because Odoo can silently discard restricted-field values before they reach the wizard method. `_oauth_token_uri()` additionally checks the user, rejects simultaneous manual/profile input, and validates profile activity, token endpoint, and exact client-ID match for the two OAuth credential types. No profile delegates to the core manual URI path.

## Verification

Offline focused contract tests:

```sh
python3 -B -m unittest discover -s tests/addons13_27 -p 'test_U15_issuer_wizard.py' -v
```

The offline harness uses doubles; it does not prove Odoo registry or access behavior. The candidate was also installed and exercised on Odoo 13.0-20221005 / Python 3.7.3 in a disposable PostgreSQL database with no public ports or external network. The observed checks included core-only installation with Resource absent from the addons path, optional dependency resolution, combined-view/field metadata, authorized and unauthorized ORM paths, manual and profile generation, fail-closed saves, and upgrade/uninstall/source-rollback data readback. These checks are not browser UI acceptance, production validation, or proof that every test in the repository-wide offline suite passes.

The repository-wide offline suite has existing failures/errors on both the approved baseline and the feature candidate; compare exact test names before attributing them to this addon. Never use a live database, provider, or real credential to run these checks.
