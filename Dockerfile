FROM odoo:13.0@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6

COPY requirements.txt /tmp/addons-requirements.txt

COPY amr_resource/ /mnt/extra-addons/amr_resource/
COPY amr_sentry/ /mnt/extra-addons/amr_sentry/
COPY amr_service_client/ /mnt/extra-addons/amr_service_client/
COPY amr_service_client_profile/ /mnt/extra-addons/amr_service_client_profile/
COPY amr_oidc_resource/ /mnt/extra-addons/amr_oidc_resource/
COPY amr_cron_monitor/ /mnt/extra-addons/amr_cron_monitor/

WORKDIR /opt/odoo
