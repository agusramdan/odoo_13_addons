#!/usr/bin/env bash
set -e

echo "=== 1. Setup Docker Socket & SSH Known Hosts ==="
sudo chmod 666 /var/run/docker.sock 2>/dev/null || true

mkdir -p ~/.ssh
if ! grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null; then
  ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null || true
fi

# Deteksi otomatis DEVPOD_WORKSPACE_ID dari mount path DevPod jika belum terset
if [ -z "$DEVPOD_WORKSPACE_ID" ] || [ "$DEVPOD_WORKSPACE_ID" = "odoo-dev" ]; then
  DETECTED_ID=$(docker inspect "$(hostname)" --format '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}' | sed -E 's|.*/workspaces/([^/]+)/content.*|\1|')
  if [ -n "$DETECTED_ID" ]; then
    export DEVPOD_WORKSPACE_ID="$DETECTED_ID"
    sed -i '/^export DEVPOD_WORKSPACE_ID=/d' ~/.bashrc 2>/dev/null || true
    echo "export DEVPOD_WORKSPACE_ID=\"$DETECTED_ID\"" >> ~/.bashrc
  fi
fi

echo "=== 2. Menunggu PostgreSQL Siap ==="
until pg_isready -h db -U odoo; do
  sleep 2
done

echo "=== 3. Inisialisasi Database odoo_dev (Jika Belum Ada) ==="
DB_EXISTS=$(PGPASSWORD=odoo psql -h db -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='odoo_dev'")
if [ "$DB_EXISTS" != "1" ]; then
  echo "Membuat database odoo_dev..."
  PGPASSWORD=odoo createdb -h db -U odoo odoo_dev
fi

# Cek apakah tabel inti Odoo sudah terinisialisasi
TABLE_EXISTS=$(PGPASSWORD=odoo psql -h db -U odoo -d odoo_dev -tAc "SELECT to_regclass('public.ir_module_module')")
if [ "$TABLE_EXISTS" != "ir_module_module" ]; then
  echo "Menginisialisasi modul base pada odoo_dev..."
  PROJECT=$(docker inspect "$(hostname)" --format '{{index .Config.Labels "com.docker.compose.project"}}')
  docker exec "${PROJECT}-odoo-1" odoo -c /etc/odoo/odoo.conf -d odoo_dev -i base --without-demo=all --stop-after-init
fi

echo "=== 4. Aktivasi Hermes Skills-as-Code ==="
if [ -d "/workspace/skills" ]; then
  hermes skills trust /workspace/skills || true
fi

MODEL_CODER

if [ ! -f ~/.hermes/.env ]; then
  cat <<'EOF' > ~/.hermes/.env
MODEL_CODER=${MODEL_CODER}
MODEL_REASONING=${MODEL_REASONING}
EOF
  echo "-> .hermes/.env berhasil dibuat."
fi

# Generate .vscode/launch.json otomatis jika belum ada
if [ ! -f /workspace/.vscode/launch.json ]; then
  mkdir -p /workspace/.vscode
  cat <<'EOF' > /workspace/.vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach Odoo 13 (Docker)",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "odoo",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/workspace"
        }
      ],
      "justMyCode": false
    }
  ]
}
EOF
  echo "-> .vscode/launch.json berhasil dibuat."
fi

chmod +x /workspace/.devcontainer/odoo-ctl.sh 2>/dev/null || true

echo "=== Workspace Siap! ==="
echo "URL Live Demo: https://${DEVPOD_WORKSPACE_ID}.dev.agusramdan.web.id"
