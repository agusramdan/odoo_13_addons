# User Guide — Service Client Issuer Profile

## Purpose and prerequisites

`amr_service_client_profile` is an optional extension to `amr_service_client`. It adds issuer-profile selection to the Service Credential wizard. Install `amr_service_client` and `amr_resource` first; the profile addon depends on both and does not replace either one. Without this addon, core OAuth credentials use the manually entered `token_uri`.

Only users assigned to the Resource Trust Administrator group (`amr_resource.group_oidc_trust_admin`) can see or select issuer profiles. The Resource addon remains the owner of issuer records and their access policy.

## Configure a credential with an issuer profile

1. Open the intended Service Client credential record and use its `Config Credential` action.
2. Choose `Client Secret` or `Service Account`.
3. Enter the exact `client_id` configured on the issuer profile.
4. Select an active issuer profile with a configured token endpoint. Leave the manual `token_uri` empty.
5. Generate or save the credential using the existing wizard flow.

The wizard rejects an inactive profile, an empty token endpoint, a client-ID mismatch, or simultaneous profile and manual URI values. The profile endpoint is used as the generated credential's `token_uri`. Invalid profile saves fail before writing credential JSON.

## Manual URI and other credential types

If no profile is selected, enter `token_uri` manually for `Client Secret` or `Service Account`, including when the optional addon is installed. `API Key`, `Bearer`, and `Basic` credentials do not use issuer profiles.

## Security and operational notes

The picker visibility is not the only protection: the server enforces the trust-admin group on profile access and attempts to set the profile field. Do not grant the trust-admin group to ordinary credential operators. This guide documents source behavior; it does not authorize configuration against an unapproved issuer or use of real secrets in testing.

The candidate was installed and exercised on Odoo 13.0-20221005 / Python 3.7.3 with disposable databases. Registry, view-inheritance metadata and ORM behavior were checked; browser-based UI acceptance and production readiness are not claimed. No live database or external identity provider was used.
