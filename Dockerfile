FROM odoo:13.0@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6

COPY requirements.txt /tmp/addons-requirements.txt

COPY ./amr_* /mnt/extra-addons/

WORKDIR /opt/odoo
