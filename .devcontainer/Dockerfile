FROM odoo:13.0@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6

COPY requirements.txt /tmp/addons-requirements.txt

USER root

# 1. Install dependensi Python Odoo & debugpy
RUN python3 -m pip install --no-cache-dir --upgrade pip==23.3.2 \
    && python3 -m pip install --no-cache-dir -r /tmp/addons-requirements.txt debugpy \
    && rm -f /tmp/addons-requirements.txt

# 2. Install utilitas dasar (alihkan repo Debian Buster EOL ke archive)
RUN sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list \
    && sed -i 's|security.debian.org|archive.debian.org|g' /etc/apt/sources.list \
    && sed -i '/buster-updates/d' /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    openssh-client \
    postgresql-client \
    sudo \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 3. Buat user 'dev' (UID 1000, cocok dengan user 'ubuntu' di VPS) + akses sudo
RUN useradd -m -u 1000 -s /bin/bash dev \
    && echo "dev ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && mkdir -p /workspace /home/dev/.hermes/memories \
    && chown -R dev:dev /workspace /home/dev/.hermes

# 4. Install uv secara global
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# 5. Install Hermes Agent sebagai user 'dev' agar binary & memori bisa diakses tanpa root
USER dev
RUN uv tool install --python 3.11 hermes-agent
ENV PATH="/home/dev/.local/bin:${PATH}"

WORKDIR /workspace
