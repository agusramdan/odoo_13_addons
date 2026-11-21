#!/usr/bin/env bash
set -e

echo "=== 1. Setup SSH Known Hosts (GitHub) ==="
mkdir -p ~/.ssh
if ! grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null; then
  ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null || true
fi

echo "=== 2. Menunggu PostgreSQL Siap ==="
until pg_isready -h db -U odoo; do
  sleep 2
done

echo "=== 3. Inisialisasi Database Template (Jika Belum Ada) ==="
DB_EXISTS=$(PGPASSWORD=odoo psql -h db -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='odoo_dev'")
if [ "$DB_EXISTS" != "1" ]; then
  echo "Membuat database odoo_dev..."
  PGPASSWORD=odoo createdb -h db -U odoo odoo_dev
fi
echo "=== 4. Aktivasi Hermes Skills-as-Code ==="
if [ -d "/workspace/skills" ]; then
  hermes skills trust /workspace/skills || true
fi

echo "=== Workspace Siap! ==="
echo "URL Live Demo: https://${DEVPOD_WORKSPACE_ID:-odoo-dev}.dev.agusramdan.web.id"
