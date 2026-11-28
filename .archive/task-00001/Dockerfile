FROM unittest:odoo13-python373
USER root
RUN printf 'deb http://archive.debian.org/debian buster main\ndeb http://archive.debian.org/debian-security buster/updates main\n' > /etc/apt/sources.list && apt-get -o Acquire::Check-Valid-Until=false update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends chromium python3-websocket && rm -rf /var/lib/apt/lists/*
USER odoo
ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
