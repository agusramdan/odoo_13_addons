#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "  Setup Laptop FDE (Linux): DevPod + SSH Agent + LiteLLM  "
echo "=========================================================="

# --- 1. Input Interaktif ---
read -rp "Masukkan SSH Host VPS (contoh: dev@103.x.x.x): " VPS_HOST
if [ -z "$VPS_HOST" ]; then
  echo "Error: SSH Host VPS wajib diisi."
  exit 1
fi

DEFAULT_DEV_USER=$(whoami)
read -rp "Masukkan nama developer (untuk volume memori Hermes) [${DEFAULT_DEV_USER}]: " DEV_USER
DEV_USER="${DEV_USER:-$DEFAULT_DEV_USER}"

read -rp "Masukkan LiteLLM Virtual Key Anda: " LITELLM_VIRTUAL_KEY

# --- 2. Install DevPod CLI ---
echo -e "\n[1/5] Memeriksa & menginstal DevPod CLI..."
if ! command -v devpod &> /dev/null; then
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64)  DEVPOD_ARCH="amd64" ;;
    aarch64) DEVPOD_ARCH="arm64" ;;
    *) echo "Arsitektur $ARCH tidak didukung."; exit 1 ;;
  esac
  curl -L -o /tmp/devpod "https://github.com/loft-sh/devpod/releases/latest/download/devpod-linux-${DEVPOD_ARCH}"
  sudo install -c -m 0755 /tmp/devpod /usr/local/bin/devpod
  rm -f /tmp/devpod
  echo "-> DevPod CLI berhasil diinstal."
else
  echo "-> DevPod CLI sudah terinstal ($(devpod version))."
fi

# --- 3. Cek & Generate SSH Key ---
echo -e "\n[2/5] Memeriksa SSH Key..."
SSH_KEY="$HOME/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY" ]; then
  echo "-> SSH Key belum ditemukan. Membuat SSH Key baru (ed25519)..."
  mkdir -p "$HOME/.ssh"
  ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "${DEV_USER}@fde-laptop"
  echo "-> Public Key Anda (salin ke GitHub & VPS):"
  cat "${SSH_KEY}.pub"
  echo ""
  read -rp "Ingin otomatis menyalin SSH Key ke VPS sekarang (ssh-copy-id)? [y/N]: " COPY_KEY
  if [[ "$COPY_KEY" =~ ^[Yy]$ ]]; then
    ssh-copy-id -i "${SSH_KEY}.pub" "$VPS_HOST"
  fi
else
  echo "-> SSH Key ditemukan di $SSH_KEY."
fi

# --- 4. Simpan Environment Variable ke Shell Profile ---
echo -e "\n[3/5] Menyimpan konfigurasi environment & SSH Agent..."
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"

# Hapus blok lama jika skrip dijalankan ulang
sed -i '/# >>> DEVPOD FDE CONFIG >>>/,/# <<< DEVPOD FDE CONFIG <<</d' "$SHELL_RC"

cat <<EOF >> "$SHELL_RC"

# >>> DEVPOD FDE CONFIG >>>
export DEV_USER="${DEV_USER}"
export LITELLM_VIRTUAL_KEY="${LITELLM_VIRTUAL_KEY}"
if [ -z "\${SSH_AUTH_SOCK:-}" ]; then
  eval "\$(ssh-agent -s)" >/dev/null
  ssh-add "${SSH_KEY}" 2>/dev/null || true
fi
# <<< DEVPOD FDE CONFIG <<<
EOF

# Aktifkan di sesi saat ini
export DEV_USER="$DEV_USER"
export LITELLM_VIRTUAL_KEY="$LITELLM_VIRTUAL_KEY"
eval "$(ssh-agent -s)" >/dev/null
ssh-add "$SSH_KEY" 2>/dev/null || true
echo "-> Konfigurasi disimpan di $SHELL_RC."

# --- 5. Konfigurasi Provider SSH & IDE di DevPod ---
echo -e "\n[4/5] Mengonfigurasi DevPod SSH Provider ($VPS_HOST)..."
devpod provider delete ssh >/dev/null 2>&1 || true
devpod provider add ssh -o HOST="$VPS_HOST"
devpod provider use ssh

echo -e "\n[5/5] Mengatur VS Code sebagai default IDE..."
devpod ide use vscode

echo "=========================================================="
echo "  SETUP LAPTOP LINUX SELESAI!"
echo "=========================================================="
echo "Jalankan 'source $SHELL_RC' atau buka terminal baru."
echo "Tes jalankan workspace:"
echo "  devpod up git@github.com:org/repo-odoo.git@main --id test-01"
