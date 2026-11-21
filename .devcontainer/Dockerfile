FROM odoo:13.0@sha256:487514270bff6f4a37cfb7532a2f513cfca7ea4ce996f628c6d9edd4502be2a6

COPY requirements.txt /tmp/addons-requirements.txt

USER root

RUN python3 -m pip install --no-cache-dir --upgrade pip==23.3.2 \
    && python3 -m pip install --no-cache-dir -r /tmp/addons-requirements.txt

# 1. Install utilitas dasar untuk DevPod, SSH Forwarding, & PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    openssh-client \
    postgresql-client \
    sudo \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 2. Install debugpy ke dalam Python milik Odoo 13
RUN pip3 install --no-cache-dir debugpy

# 3. Install uv (untuk mengisolasi Python Hermes dari Python 3.7/3.8 milik Odoo 13)
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# 4. Install Hermes Agent (terisolasi dengan Python 3.11+ via uv)
# Sesuaikan package/repo jika Anda memakai fork atau versi internal Hermes
# Odoo 13 berjalan di Python 3.7/3.8, sedangkan Hermes Agent membutuhkan Python modern (3.11+).  \
# Menggunakan uv tool install --python 3.11 memastikan hermes berjalan mulus di terminal tanpa merusak dependensi Python odoo-bin.
RUN uv tool install --python 3.11 hermes-agent \
    && ln -sf /root/.local/bin/hermes /usr/local/bin/hermes

# 5. Siapkan direktori workspace & memori Hermes
RUN mkdir -p /workspace /root/.hermes/memories

WORKDIR /workspace
