# Optional Service Client issuer-profile integration

This Odoo 13 addon adds issuer-profile selection to the `service.credential.wizard`. It depends on `amr_service_client` and `amr_resource`; Resource owns the issuer registry and trust-admin group. See the [User Guide](docs/user.md) and [Developer Guide](docs/developer.md).

Without this addon, OAuth credentials use the manually entered `token_uri` in core. With it installed, authorized users can select an active profile for client-secret and service-account credentials. Server-side checks reject unauthorized field writes, inactive or endpoint-less profiles, client-ID mismatches, and simultaneous profile/manual URI. API-key, bearer and basic credentials are not affected.

Version `13.0.1.0.0`; license LGPL-3. The candidate was installed and exercised on Odoo 13.0-20221005/Python 3.7.3 with disposable databases, including registry/view metadata, ORM authorization and data-preservation checks. Browser UI acceptance and production readiness are not claimed; offline tests also use doubles.
