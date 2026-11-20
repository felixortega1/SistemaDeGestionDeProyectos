#!/usr/bin/env bash
# Entorno local identico al servidor: Ubuntu 24.04 (WSL2), Python 3.12, MySQL 8.0. Sin Docker.
# Ejecutar desde la raiz del repo:  bash deploy/local-setup-wsl.sh
set -euo pipefail
cd "$(dirname "$0")/.."

sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev build-essential pkg-config libmysqlclient-dev mysql-server
sudo service mysql start
mysql --version

# Base y usuario locales (+ permisos sobre test_% para que pytest cree su base de pruebas)
sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS gestion_app_db CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'gestion_app'@'127.0.0.1' IDENTIFIED BY 'local-dev-pass';
CREATE USER IF NOT EXISTS 'gestion_app'@'localhost' IDENTIFIED BY 'local-dev-pass';
GRANT ALL ON gestion_app_db.* TO 'gestion_app'@'127.0.0.1';
GRANT ALL ON gestion_app_db.* TO 'gestion_app'@'localhost';
GRANT ALL ON `test\_%`.* TO 'gestion_app'@'127.0.0.1';
GRANT ALL ON `test\_%`.* TO 'gestion_app'@'localhost';
FLUSH PRIVILEGES;
SQL

# .env local (solo si no existe)
if [ ! -f .env ]; then
  cat > .env <<ENV
SECRET_KEY=$(python3.12 -c "import secrets;print(secrets.token_urlsafe(50))")
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
APP_TIMEZONE=America/Lima
MYSQL_DATABASE=gestion_app_db
MYSQL_USER=gestion_app
MYSQL_PASSWORD=local-dev-pass
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
ENV
fi

# venv fuera de /mnt/c por velocidad
VENV="$HOME/.venvs/gestion"
python3.12 -m venv "$VENV"
"$VENV/bin/pip" install -r requirements-dev.txt

"$VENV/bin/python" manage.py migrate
"$VENV/bin/pytest" -q
echo "OK. Para trabajar: source $VENV/bin/activate && python manage.py seed_demo && python manage.py runserver"
