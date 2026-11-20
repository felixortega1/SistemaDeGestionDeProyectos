# Deploy de gestion_proyectos en el VPS (patron de la guia del servidor)

Valores: `PROYECTO=gestion_proyectos` · `DOMINIO=proyectos.walkcode.pe` (sin www) · `PUERTO=8003` · `MODULO=config`
· `REPO=git@github.com:felixortega1/SistemaDeGestionDeProyectos.git` · rama `feature/story-task-split` (luego `main`).
Esta app lee variables `MYSQL_*` (no `DB_*`); `STATIC_ROOT` es `/opt/gestion_proyectos/staticfiles` por defecto; no usa media de usuarios.

Validado en local: `makemigrations --check` sin cambios, `ruff` limpio, `pytest` 170 passed (91 %).

## 0. Revisar el servidor (solo lectura)
```bash
free -h; df -h /; python3.12 --version; mysql --version; nginx -v
ss -tlnp | grep -E ':(80|443|3306|3307|800[0-9])\b'
ls /etc/nginx/sites-enabled
```
## 1. Paquetes
```bash
sudo apt update
sudo apt install -y git build-essential pkg-config libmysqlclient-dev python3.12-venv python3.12-dev
```
## 2. Usuario y carpetas
```bash
sudo adduser --system --group --home /home/gestion_proyectos --shell /usr/sbin/nologin gestion_proyectos
sudo mkdir -p /opt/gestion_proyectos /var/lib/gestion_proyectos /etc/gestion_proyectos
sudo chown gestion_proyectos:gestion_proyectos /opt/gestion_proyectos
sudo chown -R gestion_proyectos:gestion_proyectos /var/lib/gestion_proyectos && sudo chmod 750 /var/lib/gestion_proyectos
sudo chown root:gestion_proyectos /etc/gestion_proyectos && sudo chmod 750 /etc/gestion_proyectos
```
## 3. Codigo (deploy key de solo lectura)
```bash
sudo -u gestion_proyectos mkdir -p -m 700 /home/gestion_proyectos/.ssh
sudo -u gestion_proyectos ssh-keygen -t ed25519 -N "" -C "gestion_proyectos-vps" -f /home/gestion_proyectos/.ssh/id_ed25519
sudo -u gestion_proyectos sh -c 'ssh-keyscan github.com >> /home/gestion_proyectos/.ssh/known_hosts'
sudo cat /home/gestion_proyectos/.ssh/id_ed25519.pub
```
GitHub → repo → Settings → Deploy keys → Add (sin "Allow write access"). Luego:
```bash
sudo -u gestion_proyectos git clone -b feature/story-task-split git@github.com:felixortega1/SistemaDeGestionDeProyectos.git /opt/gestion_proyectos
```
## 4. Entorno de Python
```bash
cd /opt/gestion_proyectos
sudo -u gestion_proyectos python3.12 -m venv .venv
sudo -u gestion_proyectos .venv/bin/pip install --upgrade pip
sudo -u gestion_proyectos .venv/bin/pip install -r requirements.txt   # ya incluye gunicorn y mysqlclient
```
## 5. Base de datos
```bash
openssl rand -base64 24            # guardar la clave
nano deploy/create_db.sql          # reemplazar CLAVE_LARGA (dos veces, la misma)
sudo mysql < deploy/create_db.sql
```
Produccion empieza limpia (sin datos de prueba).
## 6. Variables de entorno
```bash
sudo cp deploy/gestion_proyectos.env.example /etc/gestion_proyectos/gestion_proyectos.env
sudo nano /etc/gestion_proyectos/gestion_proyectos.env      # SECRET_KEY y MYSQL_PASSWORD
sudo chown root:gestion_proyectos /etc/gestion_proyectos/gestion_proyectos.env
sudo chmod 640 /etc/gestion_proyectos/gestion_proyectos.env
```
## 7. Migraciones, estaticos y primer usuario
```bash
cd /opt/gestion_proyectos
sudo -u gestion_proyectos bash -c 'set -a; . /etc/gestion_proyectos/gestion_proyectos.env; set +a; .venv/bin/python manage.py migrate'
sudo -u gestion_proyectos bash -c 'set -a; . /etc/gestion_proyectos/gestion_proyectos.env; set +a; .venv/bin/python manage.py collectstatic --noinput'
sudo -u gestion_proyectos bash -c 'set -a; . /etc/gestion_proyectos/gestion_proyectos.env; set +a; .venv/bin/python manage.py check --deploy'
sudo -u gestion_proyectos bash -c 'set -a; . /etc/gestion_proyectos/gestion_proyectos.env; set +a; .venv/bin/python manage.py createsuperuser'
```
## 8. Servicio
```bash
sudo cp deploy/gestion_proyectos.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gestion_proyectos
sudo systemctl status gestion_proyectos --no-pager
curl -sI http://127.0.0.1:8003/accounts/login/ | head -1
```
Si falla: `journalctl -u gestion_proyectos -n 80 --no-pager`.
## 9. Nginx
```bash
sudo cp deploy/nginx-gestion_proyectos.conf /etc/nginx/sites-available/gestion_proyectos.conf
sudo ln -s /etc/nginx/sites-available/gestion_proyectos.conf /etc/nginx/sites-enabled/gestion_proyectos.conf
sudo nginx -t        # recargar solo si dice "syntax is ok"
sudo systemctl reload nginx
sudo -u www-data ls /opt/gestion_proyectos/staticfiles   # si "Permission denied": sudo chmod o+x /opt/gestion_proyectos
curl -sI -H "Host: proyectos.walkcode.pe" http://127.0.0.1/accounts/login/ | head -1
```
## 10. HTTPS
```bash
dig +short proyectos.walkcode.pe        # debe dar 161.132.41.144
sudo certbot --nginx -d proyectos.walkcode.pe
sudo certbot renew --dry-run
```
## 11. Respaldos
```bash
sudo cp /opt/ruteame/deploy/respaldo.sh /usr/local/bin/gestion_proyectos-respaldo
sudo nano /usr/local/bin/gestion_proyectos-respaldo   # BD=gestion_proyectos_db, DESTINO=/var/backups/gestion_proyectos; sin carpeta media
sudo chmod 750 /usr/local/bin/gestion_proyectos-respaldo
sudo /usr/local/bin/gestion_proyectos-respaldo && ls -lh /var/backups/gestion_proyectos
echo '45 3 * * * root /usr/local/bin/gestion_proyectos-respaldo >> /var/log/gestion_proyectos-respaldo.log 2>&1' | sudo tee /etc/cron.d/gestion_proyectos-respaldo
```
Hora 03:45 (03:15 y 03:30 ya estan ocupadas). `actualizar.sh` llama a este respaldo, asi que hay que crearlo antes de la primera actualizacion.
## 12. Actualizar
`sudo chmod +x /opt/gestion_proyectos/deploy/actualizar.sh` y luego `sudo /opt/gestion_proyectos/deploy/actualizar.sh`
(rama por defecto `feature/story-task-split`; cuando se fusione: `sudo RAMA=main ... ` o cambiar el valor en el script).

## Dia a dia
| Que | Comando |
|---|---|
| Ver errores | `journalctl -u gestion_proyectos -f` |
| Reiniciar | `sudo systemctl restart gestion_proyectos` |
| Volver atras | `cd /opt/gestion_proyectos && sudo -u gestion_proyectos git log --oneline -5`, `git checkout COMMIT`, reiniciar (si hubo migracion, restaurar antes el respaldo) |
