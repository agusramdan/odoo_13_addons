#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR" || exit

echo "================================================="
echo "      Instalasi Odoo Cron Watchdog               "
echo "================================================="

# --- FUNGSI HELPER ---
ask_variable() {
    local var_name=$1
    local default_value=$2
    local prompt_message=$3
    local user_input
    read -p "$prompt_message [$default_value]: " user_input
    echo "${user_input:-$default_value}"
}

# 1. SETUP ENVIRONMENT VARIABLE (.env)
if [ ! -f ".env" ]; then
    echo "File .env tidak ditemukan. Memulai setup konfigurasi interaktif..."
    echo "Tekan ENTER jika ingin menggunakan nilai [default]."
    echo ""

    PGHOST=$(ask_variable "PGHOST" "postgres" "Host PostgreSQL")
    PGPORT=$(ask_variable "PGPORT" "5432" "Port PostgreSQL")
    PGDATABASE=$(ask_variable "PGDATABASE" "odoo13" "Nama Database")
    PGUSER=$(ask_variable "PGUSER" "cron_monitor_ro" "Username Database (Watchdog)")
    PGPASSWORD=$(ask_variable "PGPASSWORD" "secret_password" "Password Database (Watchdog)")
    KUMA_CRON_PUSH_URL=$(ask_variable "KUMA_CRON_PUSH_URL" "http://uptime-kuma:3001/api/push/REPLACE_CRON_TOKEN" "URL Uptime Kuma (Cron)")
    KUMA_WATCHDOG_PUSH_URL=$(ask_variable "KUMA_WATCHDOG_PUSH_URL" "http://uptime-kuma:3001/api/push/REPLACE_WATCHDOG_TOKEN" "URL Uptime Kuma (Watchdog)")
    CHECK_INTERVAL_SECONDS=$(ask_variable "CHECK_INTERVAL_SECONDS" "60" "Interval Pengecekan (detik)")
    AUDIT_STALE_MINUTES=$(ask_variable "AUDIT_STALE_MINUTES" "120" "Batas Waktu Stale (menit)")
    MONITORING_NETWORK=$(ask_variable "MONITORING_NETWORK" "monitoring" "Nama Docker Network")
    LOG_LEVEL=$(ask_variable "LOG_LEVEL" "INFO" "Log Level (INFO/DEBUG/WARNING)")

    cat <<EOF > .env
PGHOST=$PGHOST
PGPORT=$PGPORT
PGDATABASE=$PGDATABASE
PGUSER=$PGUSER
PGPASSWORD=$PGPASSWORD
KUMA_CRON_PUSH_URL=$KUMA_CRON_PUSH_URL
KUMA_WATCHDOG_PUSH_URL=$KUMA_WATCHDOG_PUSH_URL
CHECK_INTERVAL_SECONDS=$CHECK_INTERVAL_SECONDS
AUDIT_STALE_MINUTES=$AUDIT_STALE_MINUTES
MONITORING_NETWORK=$MONITORING_NETWORK
LOG_LEVEL=$LOG_LEVEL
EOF
    echo "File .env berhasil dibuat."
else
    echo "File .env ditemukan, menggunakan konfigurasi yang ada."
fi

# Load variabel dari .env
export $(grep -v '^#' .env | xargs)

# 2. SETUP DOCKER NETWORK
NETWORK_NAME=${MONITORING_NETWORK:-monitoring}
if ! docker network ls | grep -qw "$NETWORK_NAME"; then
    echo "Membuat Docker network: $NETWORK_NAME..."
    docker network create "$NETWORK_NAME"
fi

# 3. SETUP DATABASE USER DI POSTGRESQL
echo ""
echo "================================================="
echo "      Setup User PostgreSQL ($PGUSER)            "
echo "================================================="
read -p "Apakah Anda ingin mengeksekusi SQL untuk membuat user database '$PGUSER' sekarang? (y/n): " SETUP_DB

if [[ "$SETUP_DB" == "y" || "$SETUP_DB" == "Y" ]]; then

    # Generate SQL file on-the-fly
    cat <<EOF > apply_monitor_user.sql
-- Run as PostgreSQL administrator.
CREATE ROLE $PGUSER LOGIN PASSWORD '$PGPASSWORD';
GRANT CONNECT ON DATABASE $PGDATABASE TO $PGUSER;
GRANT USAGE ON SCHEMA public TO $PGUSER;
GRANT SELECT ON TABLE ir_cron, amr_cron_execution TO $PGUSER;
EOF

    read -p "Masukkan Username Admin PostgreSQL (Superuser) [postgres]: " ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-postgres}

    read -s -p "Masukkan Password untuk user $ADMIN_USER: " ADMIN_PASSWORD
    echo ""

    echo "Mengeksekusi SQL ke $PGHOST:$PGPORT database $PGDATABASE..."

    # Menjalankan container psql sementara
    docker run --rm -i \
        --network "$NETWORK_NAME" \
        -e PGPASSWORD="$ADMIN_PASSWORD" \
        postgres:12-alpine \
        psql -h "$PGHOST" -p "$PGPORT" -U "$ADMIN_USER" -d "$PGDATABASE" < apply_monitor_user.sql

    if [ $? -eq 0 ]; then
        echo "SUKSES: User $PGUSER berhasil dikonfigurasi di database!"
    else
        echo "GAGAL: Terjadi kesalahan saat mengeksekusi SQL."
        echo "Pastikan kredensial admin benar atau database sudah ada."
    fi

    # Selalu hapus file SQL untuk keamanan, baik sukses maupun gagal
    rm -f apply_monitor_user.sql
else
    echo "Melewati setup database."
fi

# 4. PULL & RUN DOCKER CONTAINER
echo ""
echo "================================================="
echo "      Menjalankan Docker Container               "
echo "================================================="
IMAGE_NAME="agusramdan/cron-watchdog:latest"

echo "Menarik image $IMAGE_NAME dari Docker Hub..."
docker pull "$IMAGE_NAME"

CONTAINER_NAME="cron_watchdog_service"
if docker ps -a | grep -qw "$CONTAINER_NAME"; then
    echo "Menghentikan dan menghapus container lama..."
    docker stop "$CONTAINER_NAME" > /dev/null
    docker rm "$CONTAINER_NAME" > /dev/null
fi

echo "Menjalankan container $CONTAINER_NAME..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    --env-file .env \
    --restart unless-stopped \
    "$IMAGE_NAME"

echo ""
echo "Instalasi Selesai!"
echo "Container '$CONTAINER_NAME' berjalan di background."
echo "Pantau log service dengan perintah: docker logs -f $CONTAINER_NAME"
