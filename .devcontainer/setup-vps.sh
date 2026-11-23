#!/usr/bin/env bash
# ============================================================================
#  setup-vps.sh  —  DevPod + Caddy + LiteLLM + Hermes (Odoo CDE)
#  Versi perbaikan: 2026-11-22
#
#  Perbaikan vs versi awal:
#   [F1] Caddy container pakai network_mode: host (mode bridge menyebabkan
#        reverse_proxy 127.0.0.1:* refused -> 502 untuk semua site di Caddyfile)
#   [F2] Mode migrate: container Caddy lama di-REMOVE (bukan cuma stop) agar
#        nama 'caddy' tidak konflik saat compose up
#   [F3] Backup config lama (.env / litellm_config.yaml / docker-compose.yml)
#        sebelum ditimpa; re-run tidak lagi menghancurkan konfigasi existing
#   [F4] Input key pakai read -s (tidak tampil di layar / tidak masuk history)
#   [F5] Master key tidak di-echo ke stdout (cukup disimpan di .env)
#   [F6] litellm publish 127.0.0.1:4000 agar bisa di-reverse_proxy dari Caddy
#   [F7] Cek prasyarat: openssl ada, port 80/443 bebas sebelum mode fresh
#   [F8] Re-run: pilihan skip generate jika config existing terdeteksi
# ============================================================================
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Harap jalankan skrip ini dengan sudo: sudo bash setup-vps.sh"
  exit 1
fi

echo "=========================================================="
echo "  Setup VPS: DevPod + Caddy + LiteLLM + Hermes (Odoo CDE) "
echo "=========================================================="

# --- 0. Cek prasyarat [F7] ---
echo -e "\n[0/7] Cek prasyarat..."
if ! command -v openssl &>/dev/null; then
  echo "ERROR: openssl tidak ditemukan. Install dulu: apt-get install -y openssl"
  exit 1
fi
if ! command -v curl &>/dev/null; then
  echo "ERROR: curl tidak ditemukan. Install dulu: apt-get install -y curl"
  exit 1
fi

INFRA_DIR="/opt/devpod-infra"

# --- 1. Input Interaktif Dasar ---
DEFAULT_USER="${SUDO_USER:-$(whoami)}"
read -rp "Masukkan username SSH developer utama [${DEFAULT_USER}]: " DEV_USER
DEV_USER="${DEV_USER:-$DEFAULT_USER}"

# [F4] key tidak echo ke layar
read -rsp "Masukkan LiteLLM Master Key (kosongkan untuk generate otomatis): " LITELLM_MASTER_KEY
echo ""
if [ -z "$LITELLM_MASTER_KEY" ]; then
  LITELLM_MASTER_KEY="sk-master-$(openssl rand -hex 16)"
  echo "-> Master Key baru di-generate (disimpan di $INFRA_DIR/.env)"
fi

read -rsp "Masukkan OpenAI/Gemini/Anthropic API Key (opsional): " PROVIDER_API_KEY
echo ""

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
  if ! ufw status | grep -q "Status: active"; then
    # UFW belum aktif -> aman di-set default lalu enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    echo "-> UFW diaktifkan dengan rule 22/80/443."
  else
    # UFW sudah aktif -> hanya tambah rule, JANGAN enable ulang
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "-> UFW sudah aktif; rule 22/80/443 dipastikan ada."
  fi
fi

# --- 5. Buat Docker Networks & Volume Hermes ---
echo -e "\n[4/7] Membuat Docker Networks & Volume Memori Hermes..."
docker network inspect caddy_net >/dev/null 2>&1 || docker network create caddy_net
docker network inspect ai_net >/dev/null 2>&1 || docker network create ai_net
# Volume memori Hermes (dipakai agent Hermes saat deploy DevPod)
docker volume inspect "hermes_mem_${DEV_USER}" >/dev/null 2>&1 || docker volume create "hermes_mem_${DEV_USER}" >/dev/null

# --- 6. Deteksi & Pilihan Penanganan Caddy ---
echo -e "\n[5/7] Memeriksa instalasi Caddy yang sudah ada..."
CADDY_MODE="fresh"
HOST_CADDYFILE="/etc/caddy/Caddyfile"
EXISTING_CADDY_CONTAINER=$(docker ps -a --format '{{.Names}}' | grep -i '^caddy$' | head -n 1 || true)

if systemctl is-active --quiet caddy 2>/dev/null || [ -n "$EXISTING_CADDY_CONTAINER" ]; then
  echo "⚠️  TERDETEKSI Caddy sudah terpasang di VPS ini:"
  systemctl is-active --quiet caddy 2>/dev/null && echo "   - Systemd service 'caddy' sedang AKTIF"
  [ -n "$EXISTING_CADDY_CONTAINER" ] && echo "   - Docker container '${EXISTING_CADDY_CONTAINER}' ada (status: $(docker inspect -f '{{.State.Status}}' "$EXISTING_CADDY_CONTAINER" 2>/dev/null || echo 'unknown'))"
  echo ""
  echo "Pilih cara penanganan Caddy:"
  echo "  1) Migrasi ke caddy-docker-proxy (hentikan Caddy lama & mount Caddyfile lama)"
  echo "  2) Pertahankan Caddy host (caddy-docker-proxy di port internal 127.0.0.1:8080)"
  echo "  3) Lewati instalasi Caddy (hanya deploy LiteLLM)"
  read -rp "Masukkan pilihan [1/2/3]: " CADDY_CHOICE

  case "$CADDY_CHOICE" in
    1)
      CADDY_MODE="migrate"
      if systemctl is-active --quiet caddy 2>/dev/null; then
        systemctl stop caddy
        systemctl disable caddy
        echo "-> Service Caddy host dihentikan."
      fi
      # [F2] REMOVE (bukan hanya stop) agar nama container tidak konflik
      if [ -n "$EXISTING_CADDY_CONTAINER" ]; then
        docker rm -f "$EXISTING_CADDY_CONTAINER"
        echo "-> Container '$EXISTING_CADDY_CONTAINER' dihentikan & dihapus."
      fi
      ;;
    2)
      CADDY_MODE="behind_host"
      echo "-> Caddy host dipertahankan. caddy-docker-proxy akan berjalan di 127.0.0.1:8080."
      ;;
    3)
      CADDY_MODE="skip"
      echo "-> Melewati instalasi container Caddy baru."
      ;;
    *)
      echo "Pilihan tidak valid. Membatalkan."
      exit 1
      ;;
  esac
else
  # [F7] cek port 80/443 sebelum fresh install
  if command -v ss &>/dev/null; then
    if ss -ltn | grep -qE ':(80|443)\s'; then
      echo "ERROR: Port 80/443 sudah dipakai proses lain, tapi Caddy tidak terdeteksi."
      echo "       Cek dengan: ss -ltnp | grep -E ':(80|443)'"
      exit 1
    fi
  fi
  echo "-> Tidak ada Caddy yang sedang berjalan. Melanjutkan instalasi baru."
fi

# --- 7. Generate File Konfigurasi & Docker Compose ---
echo -e "\n[6/7] Menyiapkan stack infrastruktur di ${INFRA_DIR}..."
mkdir -p "$INFRA_DIR"

# [F3] Backup config existing sebelum overwrite
TS=$(date +%Y%m%d%H%M%S)
for f in .env litellm_config.yaml docker-compose.yml; do
  if [ -f "$INFRA_DIR/$f" ]; then
    cp "$INFRA_DIR/$f" "$INFRA_DIR/${f}.bak.${TS}"
    echo "-> Backup: $INFRA_DIR/$f -> ${f}.bak.${TS}"
  fi
done

# [F8] .env existing dengan master key valid -> tawarkan pertahankan
WRITE_ENV=1
if [ -f "$INFRA_DIR/.env" ] && grep -q "^LITELLM_MASTER_KEY=" "$INFRA_DIR/.env"; then
  read -rp "File .env existing berisi master key. Pertahankan? [Y/n]: " KEEP_ENV
  KEEP_ENV="${KEEP_ENV:-Y}"
  if [[ "$KEEP_ENV" =~ ^[Yy] ]]; then
    WRITE_ENV=0
    echo "-> .env existing dipertahankan."
  fi
fi

if [ "$WRITE_ENV" = "1" ]; then
  cat <<EOF > "$INFRA_DIR/.env"
LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
OPENAI_API_KEY=${PROVIDER_API_KEY}
EOF
  chmod 600 "$INFRA_DIR/.env"
  echo "-> .env ditulis (chmod 600)."
fi

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
# [F1] SEMUA mode container pakai network_mode: host (kecuali behind_host
#      yang sengaja internal). Bridge + reverse_proxy 127.0.0.1:* = 502.
CADDY_SERVICE_BLOCK=""
if [ "$CADDY_MODE" = "fresh" ] || [ "$CADDY_MODE" = "migrate" ]; then
  CADDY_SERVICE_BLOCK=$(cat <<EOF
  caddy:
    image: lucaslorentz/caddy-docker-proxy:ci-alpine
    container_name: caddy
    network_mode: host
    environment:
      - CADDY_INGRESS_NETWORKS=caddy_net
      - CADDY_DOCKER_CADDYFILE_PATH=/etc/caddy/Caddyfile
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - caddy_data:/data
      - ${HOST_CADDYFILE}:/etc/caddy/Caddyfile:ro
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

# [F6] litellm publish ke 127.0.0.1:4000 agar bisa di-reverse_proxy dari Caddy host
cat <<EOF > "$INFRA_DIR/docker-compose.yml"
services:
${CADDY_SERVICE_BLOCK}

  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: litellm
    env_file:
      - .env
    ports:
      - "127.0.0.1:4000:4000"
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

# Caddyfile wajib ada untuk mode fresh/migrate (bind-mount ro akan gagal jika tidak ada)
if [ "$CADDY_MODE" = "fresh" ] || [ "$CADDY_MODE" = "migrate" ]; then
  if [ ! -f "$HOST_CADDYFILE" ]; then
    echo "-> $HOST_CADDYFILE tidak ada. Membuat Caddyfile minimal..."
    cat <<'EOF' > "$HOST_CADDYFILE"
# Tambahkan site Anda di sini, contoh:
# example.com {
#     reverse_proxy 127.0.0.1:8080
# }
EOF
  fi
fi

echo -e "\n[7/7] Menjalankan stack infrastruktur..."
cd "$INFRA_DIR"
docker compose up -d

echo "=========================================================="
echo "  INSTALASI SELESAI! (Mode Caddy: $CADDY_MODE)"
echo "=========================================================="
echo "Lokasi konfigurasi : $INFRA_DIR"
echo "Master Key         : tersimpan di $INFRA_DIR/.env (jangan dibagikan)"
echo "LiteLLM            : http://127.0.0.1:4000 (host-only)"

if [ "$CADDY_MODE" = "behind_host" ]; then
  echo ""
  echo "PENTING (Mode 2): Tambahkan blok berikut ke $HOST_CADDYFILE,"
  echo "lalu jalankan 'sudo systemctl reload caddy':"
  echo ""
  echo "  *.dev.domain.com {"
  echo "      reverse_proxy 127.0.0.1:8080"
  echo "  }"
  echo ""
  echo "(Catatan: di label docker-compose.yml Odoo, gunakan 'http://\${DEVPOD_WORKSPACE_ID}.dev.domain.com'"
  echo " agar SSL ditangani oleh Caddy host)."
fi

if [ "$CADDY_MODE" = "fresh" ] || [ "$CADDY_MODE" = "migrate" ]; then
  echo ""
  echo "PENTING: Caddy container berjalan dengan network_mode: host."
  echo "Semua reverse_proxy 127.0.0.1:<port> di Caddyfile mengarah ke port host —"
  echo "jangan ubah ke mode bridge (ports:/networks:) atau semua site akan 502."
  echo ""
  echo "Verifikasi cepat:"
  echo "  docker inspect caddy --format '{{.HostConfig.NetworkMode}}'   # harus 'host'"
  echo "  curl -s -o /dev/null -w '%{http_code}\n' https://<domain-anda>"
fi
