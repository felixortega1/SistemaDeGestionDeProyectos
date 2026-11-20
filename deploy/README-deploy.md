# Deploy en el VPS (Ubuntu 24.04, Python 3.12, MySQL 8.0.46 compartido, nginx + certbot, systemd)

Sigue el patron de aislamiento de Ruteame: usuario, carpeta, venv, servicio, env, base y puerto propios.
Valores a confirmar antes: dominio, puerto libre (`ss -tlnp`; 8001/8002 ya ocupados, aqui 8003) y contrasenas.

## 0. Validar ANTES en local con MySQL 8.0 (obligatorio)
Opcion recomendada en esta maquina: MySQL80 ya instalado (puerto 3307) -> seguir `docs/levantar-local.md`.
Opcion A, sin Docker (recomendada, identica al servidor): WSL2 con Ubuntu 24.04.
```bash
# en PowerShell (una vez): wsl --install -d Ubuntu-24.04
# dentro de Ubuntu, en la carpeta del proyecto (ej. /mnt/c/xampp/htdocs/gestion_proyectos):
bash deploy/local-setup-wsl.sh      # instala python3.12 + mysql-server 8.0, crea base/usuario y venv, corre migrate y pytest
```
Opcion B, con Docker: `docker compose up -d` (el compose ya usa mysql:8.0.46; si hubo volumen 8.4, `docker compose down -v` antes).
Opcion C, Windows nativo: instalar MySQL Community 8.0.x (NO usar el MariaDB de XAMPP).

Criterio de OK: `migrate` sin errores y `pytest` en verde (la prueba de concurrencia WIP no debe omitirse).

## 1. Paquetes de compilacion (no cambian servicios existentes)
```bash
sudo apt install -y python3.12-venv python3.12-dev build-essential pkg-config libmysqlclient-dev git
```

## 2. Usuario y codigo
```bash
sudo useradd --system --create-home --home-dir /opt/gestion --shell /usr/sbin/nologin gestion
sudo -u gestion git clone https://github.com/felixortega1/SistemaDeGestionDeProyectos.git /opt/gestion
cd /opt/gestion && sudo -u gestion python3.12 -m venv .venv
sudo -u gestion .venv/bin/pip install -r requirements.txt
```
(Si el directorio ya existe por `--create-home`, clonar en carpeta temporal o usar `--no-create-home` y `mkdir`.)

## 3. Base de datos propia
Editar contrasena en `deploy/create_db.sql` y: `sudo mysql < deploy/create_db.sql`

## 4. Variables
```bash
sudo mkdir -p /etc/gestion
sudo cp deploy/gestion.env.example /etc/gestion/gestion.env   # editar valores reales
sudo chown root:gestion /etc/gestion/gestion.env && sudo chmod 640 /etc/gestion/gestion.env
```

## 5. Inicializar
```bash
set -a; source /etc/gestion/gestion.env; set +a
sudo -E -u gestion .venv/bin/python manage.py migrate
sudo -E -u gestion .venv/bin/python manage.py collectstatic --noinput
sudo -E -u gestion .venv/bin/python manage.py createsuperuser
```

## 6. Servicio y nginx
```bash
sudo cp deploy/gestion.service /etc/systemd/system/ && sudo systemctl daemon-reload
sudo systemctl enable --now gestion && systemctl status gestion
sudo cp deploy/nginx-gestion.conf /etc/nginx/sites-available/gestion   # editar server_name
sudo ln -s /etc/nginx/sites-available/gestion /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d gestion.TU-DOMINIO.com
```
Verificar: `curl -I https://gestion.TU-DOMINIO.com/accounts/login/` y `journalctl -u gestion -f`.

## 7. Respaldos y seguridad
- Agregar `gestion_app_db` al cron de respaldos existente (03:15/03:30).
- ufw/fail2ban ya cubren 22/80/443; gunicorn escucha solo en 127.0.0.1.
- Memoria: VPS de 4 GB compartido; usar `--workers 2`.

## Actualizaciones
`sudo bash /opt/gestion/deploy/deploy.sh`

## Rollback
`git -C /opt/gestion checkout <commit-anterior>` + `systemctl restart gestion` (migraciones hacia atras solo si es necesario: `manage.py migrate <app> <numero>`).
