FROM odoo:13.0@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6

COPY requirements.txt /tmp/addons-requirements.txt

COPY amr_resource/ /opt/odoo/addons/amr_resource/
COPY amr_sentry/ /opt/odoo/addons/amr_sentry/
COPY amr_service_client/ /opt/odoo/addons/amr_service_client/
COPY amr_service_client_profile/ /opt/odoo/addons/amr_service_client_profile/
COPY amr_oidc_resource/ /opt/odoo/addons/amr_oidc_resource/
COPY amr_cron_monitor/ /opt/odoo/addons/amr_cron_monitor/
COPY amr_data_sync/ /opt/odoo/addons/amr_data_sync/
COPY amr_data_sync_event/ /opt/odoo/addons/amr_data_sync_event/
COPY amr_data_sync_queue/ /opt/odoo/addons/amr_data_sync_queue/
COPY amr_data_event/ /opt/odoo/addons/amr_data_event/
COPY amr_data_push/ /opt/odoo/addons/amr_data_push/

WORKDIR /opt/odoo
