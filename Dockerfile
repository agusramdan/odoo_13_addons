FROM python:3.8.20-slim-bookworm@sha256:1d52838af602b4b5a831beb13a0e4d073280665ea7be7f69ce2382f29c5a613f

# Install system dependencies yang diperlukan Odoo 13 & psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install Python packages yang kompatibel dengan Odoo 13 di Python 3.8
RUN pip install --no-cache-dir \
    psycopg2-binary==2.8.6 \
    Babel==2.8.0 \
    chardet==3.0.4 \
    decorator==4.4.2 \
    docutils==0.16 \
    ebaysdk==2.1.5 \
    freezegun==0.3.15 \
    gevent==20.9.0 \
    greenlet==0.4.17 \
    idna==2.10 \
    Jinja2==2.11.3 \
    libsass==0.20.1 \
    lxml==4.6.3 \
    MarkupSafe==1.1.1 \
    num2words==0.5.10 \
    ofxparse==0.21 \
    passlib==1.7.4 \
    Pillow==8.3.2 \
    polib==1.1.0 \
    psutil==5.8.0 \
    pydot==1.4.2 \
    pyopenssl==20.0.1 \
    PyPDF2==1.26.0 \
    pyserial==3.5 \
    python-dateutil==2.8.1 \
    python-openid==2.2.5 \
    pytz==2021.1 \
    pyusb==1.2.1 \
    qrcode==6.1 \
    reportlab==3.5.68 \
    requests==2.25.1 \
    vobject==0.9.6.1 \
    Werkzeug==1.0.1 \
    xlrd==2.0.1 \
    xlsxwriter==1.4.3 \
    xlwt==1.3.0 \
    zeep==4.0.0

COPY requirements.txt /tmp/addons-requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip==23.3.2 \
    && python -m pip install --no-cache-dir -r /tmp/addons-requirements.txt

# Upgrade pip dan install debugpy
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir debugpy

# ==========================================
# CLONE ODOO 13 LANGSUNG DI DOCKERFILE
# ==========================================
RUN git clone --depth 1 --branch 13.0 https://github.com/odoo/odoo.git /opt/odoo

COPY ./amr_* /mnt/extra-addons/

WORKDIR /opt/odoo
