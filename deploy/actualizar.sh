#!/usr/bin/env bash
# Uso: sudo /opt/gestion_proyectos/deploy/actualizar.sh
set -euo pipefail
RAIZ=/opt/gestion_proyectos; USUARIO=gestion_proyectos; ENV=/etc/gestion_proyectos/gestion_proyectos.env
SERVICIO=gestion_proyectos; PUERTO=8003
RAMA=${RAMA:-feature/story-task-split}   # cambiar a main cuando se fusione el Pull Request
URL_OK="http://127.0.0.1:$PUERTO/accounts/login/"

echo "1/6 Respaldo";       /usr/local/bin/gestion_proyectos-respaldo
echo "2/6 Codigo";         sudo -u "$USUARIO" git -C "$RAIZ" fetch origin
                           sudo -u "$USUARIO" git -C "$RAIZ" checkout "$RAMA"
                           sudo -u "$USUARIO" git -C "$RAIZ" pull --ff-only
cd "$RAIZ"
echo "3/6 Dependencias";   sudo -u "$USUARIO" .venv/bin/pip install -q -r requirements.txt
echo "4/6 Migraciones";    sudo -u "$USUARIO" ENV="$ENV" bash -c 'set -a; . "$ENV"; set +a; .venv/bin/python manage.py migrate --noinput'
echo "5/6 Estaticos";      sudo -u "$USUARIO" ENV="$ENV" bash -c 'set -a; . "$ENV"; set +a; .venv/bin/python manage.py collectstatic --noinput'
echo "6/6 Reinicio";       systemctl restart "$SERVICIO"
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS -o /dev/null "$URL_OK"; then echo "OK: responde."; exit 0; fi
  sleep 2
done
echo "ERROR: no responde. journalctl -u $SERVICIO -n 80 --no-pager" >&2; exit 1
