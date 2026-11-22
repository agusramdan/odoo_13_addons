#!/usr/bin/env bash
set -e

echo "=== 1. Setup Docker Socket & SSH Known Hosts ==="
sudo chmod 666 /var/run/docker.sock 2>/dev/null || true

mkdir -p ~/.ssh
if ! grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null; then
  ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null || true
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

chmod +x /workspace/.devcontainer/odoo-ctl.sh 2>/dev/null || true

echo "=== Workspace Siap! ==="
echo "URL Live Demo: https://${DEVPOD_WORKSPACE_ID:-odoo-dev}.dev.agusramdan.web.id"