FROM odoo:13.0

COPY requirements.txt /tmp/addons-requirements.txt

# RUN git clone --depth 1 --branch 13.0 https://github.com/odoo/odoo.git /opt/odoo

COPY ./amr_* /mnt/extra-addons/

WORKDIR /opt/odoo
