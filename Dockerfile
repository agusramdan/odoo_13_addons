FROM odoo:13.0@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6

COPY requirements.txt /tmp/addons-requirements.txt
COPY odoo.conf /etc/odoo/odoo.conf

USER root
RUN python3 -m pip install --no-cache-dir --upgrade pip==23.3.2 \
    && python3 -m pip install --no-cache-dir --target /opt/pytest-packages -r /tmp/addons-requirements.txt
USER odoo

COPY . /etc/odoo/addons/
