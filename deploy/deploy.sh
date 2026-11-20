#!/usr/bin/env bash
# Actualizar el sistema ya instalado. Ejecutar como root o con sudo desde el servidor.
set -euo pipefail
APP=/opt/gestion
cd "$APP"
sudo -u gestion git pull --ff-only
sudo -u gestion "$APP/.venv/bin/pip" install -r requirements.txt
set -a; source /etc/gestion/gestion.env; set +a
sudo -E -u gestion "$APP/.venv/bin/python" manage.py migrate --noinput
sudo -E -u gestion "$APP/.venv/bin/python" manage.py collectstatic --noinput
sudo -E -u gestion "$APP/.venv/bin/python" manage.py check --deploy || true
systemctl restart gestion
systemctl --no-pager status gestion | head -5
