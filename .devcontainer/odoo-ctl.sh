#!/usr/bin/env bash
set -e

DB_NAME="${ODOO_DB:-odoo_dev}"
PROJECT=$(docker inspect "$(hostname)" --format '{{index .Config.Labels "com.docker.compose.project"}}')
ODOO_CONTAINER="${PROJECT}-odoo-1"

stop_odoo() {
  echo "Menghentikan Odoo pada ${ODOO_CONTAINER}..."
  docker exec "${ODOO_CONTAINER}" python3 -c "
import os, signal
my_pid = os.getpid()
killed = 0
for pid in os.listdir('/proc'):
    if not pid.isdigit() or int(pid) in (1, my_pid):
        continue
    try:
        cmd = open(f'/proc/{pid}/cmdline', 'rb').read().decode('utf-8', 'ignore')
        if 'odoo' in cmd or 'debugpy' in cmd:
            os.kill(int(pid), signal.SIGTERM)
            killed += 1
    except OSError:
        pass
print(f'Berhasil menghentikan {killed} proses.' if killed else 'Tidak ada proses Odoo yang berjalan.')
"
}

case "${1:-start}" in
  start)
    echo "Menjalankan Odoo pada ${ODOO_CONTAINER} (DB: ${DB_NAME})..."
    docker exec -it "${ODOO_CONTAINER}" odoo -c /etc/odoo/odoo.conf -d "${DB_NAME}"
    ;;
  stop)
    stop_odoo
    ;;
  init)
    echo "Inisialisasi modul base pada ${ODOO_CONTAINER} (DB: ${DB_NAME})..."
    docker exec -it "${ODOO_CONTAINER}" odoo -c /etc/odoo/odoo.conf -d "${DB_NAME}" -i base --without-demo=all --stop-after-init
    ;;
  debug)
    echo "Menjalankan Odoo pada ${ODOO_CONTAINER} (DB: ${DB_NAME}) dengan debugpy di port 5678..."
    docker exec -it "${ODOO_CONTAINER}" python3 -m debugpy --listen 0.0.0.0:5678 /usr/bin/odoo -c /etc/odoo/odoo.conf -d "${DB_NAME} --dev=xml"
    ;;
  update)
    if [ -z "$2" ]; then
      echo "Penggunaan: $0 update <nama_modul>"
      exit 1
    fi
    docker exec -it "${ODOO_CONTAINER}" odoo -c /etc/odoo/odoo.conf -d "${DB_NAME}" -u "$2" --stop-after-init
    ;;
  test)
    if [ -z "$2" ]; then
      echo "Penggunaan: $0 test <nama_modul>"
      exit 1
    fi
    docker exec -it "${ODOO_CONTAINER}" odoo -c /etc/odoo/odoo.conf -d "${DB_NAME}" -u "$2" --test-enable --stop-after-init
    ;;
  shell)
    docker exec -it "${ODOO_CONTAINER}" odoo shell -c /etc/odoo/odoo.conf -d "${DB_NAME}"
    ;;
  *)
    echo "Penggunaan: $0 {start|stop|init|debug|update <modul>|test <modul>|shell}"
    exit 1
    ;;
esac