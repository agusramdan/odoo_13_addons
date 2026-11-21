#!/usr/bin/env bash
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Harap jalankan skrip ini dengan sudo: sudo bash setup-vps.sh"
  exit 1
fi

echo "=========================================================="
echo "  Setup VPS: DevPod + Caddy + LiteLLM + Hermes (Odoo CDE) "
echo "=========================================================="

# --- 1. Input Interaktif Dasar ---
DEFAULT_USER="${SUDO_USER:-$(whoami)}"
read -rp "Masukkan username SSH developer utama [${DEFAULT_USER}]: " DEV_USER
DEV_USER="${DEV_USER:-$DEFAULT_USER}"

read -rp "Masukkan LiteLLM Master Key (kosongkan untuk generate otomatis): " LITELLM_MASTER_KEY
if [ -z "$LITELLM_MASTER_KEY" ]; then
  LITELLM_MASTER_KEY="sk-master-$(openssl rand -hex 16)"
  echo "-> Generated Master Key: $LITELLM_MASTER_KEY"
fi

read -rp "Masukkan OpenAI/Gemini/Anthropic API Key (opsional): " PROVIDER_API_KEY

# --- 2. Install Docker Engine ---
echo -e "\n[1/7] Memeriksa & menginstal Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
else
  echo "-> Docker sudah terinstal."
fi

# --- 3. Konfigurasi User & SSH Agent Forwarding ---
echo -e "\n[2/7] Mengonfigurasi user '$DEV_USER' dan SSH Agent Forwarding..."
if id "$DEV_USER" &>/dev/null; then
  usermod -aG docker "$DEV_USER"
fi

if grep -qE "^#?AllowAgentForwarding" /etc/ssh/sshd_config; then
  sed -i 's/^#\?AllowAgentForwarding.*/AllowAgentForwarding yes/' /etc/ssh/sshd_config
else
  echo "AllowAgentForwarding yes" >> /etc/ssh/sshd_config
fi
systemctl reload ssh || systemctl reload sshd || true

# --- 4. Konfigurasi Firewall (UFW) ---
echo -e "\n[3/7] Mengonfigurasi UFW Firewall (Port 22, 80, 443)..."
if command -v ufw &> /dev/null; then
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
fi

# --- 5. Buat Docker Networks & Volume Hermes ---
echo -e "\n[4/7] Membuat Docker Networks & Volume Memori Hermes..."
docker network inspect caddy_net >/dev/null 2>&1 || docker network create caddy_net
docker network inspect ai_net >/dev/null 2>&1 || docker network create ai_net
docker volume create "hermes_mem_${DEV_USER}" >/dev/null

# --- 6. Deteksi & Pilihan Penanganan Caddy ---
echo -e "\n[5/7] Memeriksa instalasi Caddy yang sudah ada..."
CADDY_MODE="fresh"
HOST_CADDYFILE="/etc/caddy/Caddyfile"
EXISTING_CADDY_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i caddy | head -n 1 || true)

if systemctl is-active --quiet caddy 2>/dev/null || [ -n "$EXISTING_CADDY_CONTAINER" ]; then
  echo "⚠️  TERDETEKSI Caddy sudah terpasang di VPS ini:"
  systemctl is-active --quiet caddy 2>/dev/null && echo "   - Systemd service 'caddy' sedang AKTIF"
  [ -n "$EXISTING_CADDY_CONTAINER" ] && echo "   - Docker container '${EXISTING_CADDY_CONTAINER}' sedang BERJALAN"
  echo ""
  echo "Pilih cara penanganan Caddy:"
  echo "  1) Migrasi ke caddy-docker-proxy (hentikan Caddy host & mount Caddyfile lama)"
  echo "  2) Pertahankan Caddy host (jalankan caddy-docker-proxy di port internal 127.0.0.1:8080)"
  echo "  3) Lewati instalasi Caddy (hanya deploy LiteLLM, sambungkan Caddy lama ke caddy_net)"
  read -rp "Masukkan pilihan [1/2/3]: " CADDY_CHOICE

  case "$CADDY_CHOICE" in
    1)
      CADDY_MODE="migrate"
      if systemctl is-active --quiet caddy 2>/dev/null; then
        systemctl stop caddy
        systemctl disable caddy
        echo "-> Service Caddy host dihentikan."
      fi
      if [ -n "$EXISTING_CADDY_CONTAINER" ]; then
        docker stop "$EXISTING_CADDY_CONTAINER"
        echo "-> Container '$EXISTING_CADDY_CONTAINER' dihentikan."
      fi
      ;;
    2)
      CADDY_MODE="behind_host"
      echo "-> Caddy host dipertahankan. caddy-docker-proxy akan berjalan di 127.0.0.1:8080."
      ;;
    3)
      CADDY_MODE="skip"
      if [ -n "$EXISTING_CADDY_CONTAINER" ]; then
        docker network connect caddy_net "$EXISTING_CADDY_CONTAINER" 2>/dev/null || true
        echo "-> Container '$EXISTING_CADDY_CONTAINER' disambungkan ke network 'caddy_net'."
      fi
      echo "-> Melewati instalasi container Caddy baru."
      ;;
    *)
      echo "Pilihan tidak valid. Membatalkan."
      exit 1
      ;;
  esac
else
  echo "-> Tidak ada Caddy yang sedang berjalan. Melanjutkan instalasi baru."
fi

# --- 7. Generate File Konfigurasi & Docker Compose ---
echo -e "\n[6/7] Menyiapkan stack infrastruktur di /opt/devpod-infra..."
INFRA_DIR="/opt/devpod-infra"
mkdir -p "$INFRA_DIR"

cat <<EOF > "$INFRA_DIR/.env"
LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
OPENAI_API_KEY=${PROVIDER_API_KEY}
EOF
chmod 600 "$INFRA_DIR/.env"

cat <<EOF > "$INFRA_DIR/litellm_config.yaml"
model_list:
  - model_name: default-coding
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
EOF

# Bangun blok service Caddy sesuai pilihan
CADDY_SERVICE_BLOCK=""
if [ "$CADDY_MODE" = "fresh" ] || [ "$CADDY_MODE" = "migrate" ]; then
  EXTRA_ENV=""
  EXTRA_VOL=""
  if [ "$CADDY_MODE" = "migrate" ] && [ -f "$HOST_CADDYFILE" ]; then
    EXTRA_ENV="      - CADDY_DOCKER_CADDYFILE_PATH=/etc/caddy/Caddyfile"
    EXTRA_VOL="      - ${HOST_CADDYFILE}:/etc/caddy/Caddyfile:ro"
  fi

  CADDY_SERVICE_BLOCK=$(cat <<EOF
  caddy:
    image: lucaslorentz/caddy-docker-proxy:ci-alpine
    container_name: caddy
    ports:
      - "80:80"
      - "443:443"
    environment:
      - CADDY_INGRESS_NETWORKS=caddy_net
${EXTRA_ENV}
    networks:
      - caddy_net
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - caddy_data:/data
${EXTRA_VOL}
    restart: unless-stopped
EOF
)
elif [ "$CADDY_MODE" = "behind_host" ]; then
  CADDY_SERVICE_BLOCK=$(cat <<EOF
  caddy-devpod:
    image: lucaslorentz/caddy-docker-proxy:ci-alpine
    container_name: caddy-devpod
    ports:
      - "127.0.0.1:8080:80"
    environment:
      - CADDY_INGRESS_NETWORKS=caddy_net
    networks:
      - caddy_net
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - caddy_data:/data
    restart: unless-stopped
EOF
)
fi

cat <<EOF > "$INFRA_DIR/docker-compose.yml"
services:
${CADDY_SERVICE_BLOCK}

  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: litellm
    env_file:
      - .env
    volumes:
      - ./litellm_config.yaml:/app/config.yaml:ro
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    networks:
      - ai_net
    restart: unless-stopped

networks:
  caddy_net:
    external: true
  ai_net:
    external: true

volumes:
  caddy_data:
EOF

echo -e "\n[7/7] Menjalankan stack infrastruktur..."
cd "$INFRA_DIR"
docker compose up -d

echo "=========================================================="
echo "  INSTALASI SELESAI! (Mode Caddy: $CADDY_MODE)"
echo "=========================================================="
echo "Lokasi konfigurasi : $INFRA_DIR"
echo "LiteLLM Master Key : $LITELLM_MASTER_KEY"

if [ "$CADDY_MODE" = "behind_host" ]; then
  echo ""
  echo "PENTING (Mode 2): Tambahkan blok berikut ke /etc/caddy/Caddyfile di host Anda,"
  echo "lalu jalankan 'sudo systemctl reload caddy':"
  echo ""
  echo "  *.dev.domain.com {"
  echo "      reverse_proxy 127.0.0.1:8080"
  echo "  }"
  echo ""
  echo "(Catatan: di label docker-compose.yml Odoo, gunakan 'http://\${DEVPOD_WORKSPACE_ID}.dev.domain.com'"
  echo " agar SSL ditangani oleh Caddy host)."
fi
