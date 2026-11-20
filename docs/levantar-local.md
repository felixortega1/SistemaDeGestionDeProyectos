# Levantar el sistema en local (Windows)

Mismo patrón que Ruteame. Línea base = servidor: **Python 3.12 + MySQL 8.0.46**.

| | Ruteame | Este proyecto |
| --- | --- | --- |
| MySQL | `MySQL80` (Windows), `127.0.0.1:3307` | **el mismo servicio**, base y usuario propios |
| Servidor web | uvicorn `:8000` | `manage.py runserver` **`:8010`** |
| Carpeta | `C:\xampp\htdocs\ruteame_pe` | `C:\xampp\htdocs\gestion_proyectos` |

No toques la base de Ruteame: aquí se crea `gestion_app_db` con el usuario `gestion_app`.

--------------------------------------------------------------------------------

## A. Una sola vez (preparación)

### 1. Comprobar MySQL
- Servicio `MySQL80` en marcha. Si no responde, PowerShell **como administrador**: `net start MySQL80`.
- En Workbench conecta a `127.0.0.1:3307` y ejecuta `SELECT VERSION();` → debe decir `8.0.46`.

### 2. Crear base y usuario
En Workbench (conectado como root) abre y ejecuta **`deploy/local_db.sql`**. Crea `gestion_app_db`, el usuario `gestion_app` y el permiso sobre `test_%` (necesario para que `pytest` cree su base de pruebas).

### 3. Entorno Python (PowerShell)
```powershell
cd C:\xampp\htdocs\gestion_proyectos
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```
Debe aparecer `(.venv)` al inicio de la línea. Si falla `mysqlclient`, avisa del error.

### 4. Configuración
```powershell
copy .env.example .env
```
Edita `.env`:
```
SECRET_KEY=un-texto-largo-aleatorio
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
APP_TIMEZONE=America/Lima
MYSQL_DATABASE=gestion_app_db
MYSQL_USER=gestion_app
MYSQL_PASSWORD=local-dev-pass
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
```
`.env` no se sube a git. **El puerto es 3307**, no 3306 (ese es el de MariaDB/XAMPP).

### 5. Crear tablas y datos de ejemplo
```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser     # opcional, solo para /admin/
```

--------------------------------------------------------------------------------

## B. Cada vez que trabajes

### 1. Base de datos
Corre sola como servicio. Si no responde: `net start MySQL80` (PowerShell administrador).

### 2. Servidor (ventana 1)
```powershell
cd C:\xampp\htdocs\gestion_proyectos
.venv\Scripts\activate
python manage.py runserver 8010
```
- Debe decir `Starting development server at http://127.0.0.1:8010/`.
- Déjala abierta. Se recarga sola al cambiar código.

### 3. Comprobaciones de arranque
- `http://localhost:8010/accounts/login/` → muestra el login.
- Entra con `ana@demo.com` / `Demo12345!` (Product Owner del proyecto de ejemplo).
- Empresas → proyecto → **Diagramas › Kanban** muestra el tablero con tarjetas.
- `http://localhost:8010/admin/` → entra con el superusuario.
- Si la página sale sin estilos: confirma `DEBUG=true` en `.env`.

### 3b. Pruebas (ventana 2, o antes de arrancar)
```powershell
.venv\Scripts\activate
pytest -q                                   # todo debe salir passed
pytest --cov=apps --cov-fail-under=80       # cobertura mínima
ruff check .                                # lint
```
Con MySQL **no** debe omitirse la prueba de concurrencia del WIP (en SQLite sí).

### 4. Probar desde el celular (opcional)
1. PC y celular en la misma Wi-Fi. `ipconfig` → anota tu IPv4 (ej. `192.168.1.15`).
2. En `.env`: `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.15`.
3. Arranca con `python manage.py runserver 0.0.0.0:8010`.
4. Acepta el permiso del firewall de Windows para el puerto 8010.
5. En el celular abre `http://192.168.1.15:8010`.

--------------------------------------------------------------------------------

## C. Si algo falla

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `Can't connect to MySQL server on '127.0.0.1:3306'` | `.env` sin `MYSQL_PORT=3307` | Corregir el puerto |
| `Can't connect ... 3307` | Servicio apagado | `net start MySQL80` (admin) |
| `Access denied for user 'gestion_app'` | No se ejecutó `local_db.sql` o contraseña distinta | Repetir paso A.2 y revisar `.env` |
| `SECRET_KEY` / `ImproperlyConfigured` | Falta `.env` o `SECRET_KEY` | Paso A.4 |
| `Access denied ... test_gestion_app_db` en `pytest` | Falta el permiso `test_%` | Repetir paso A.2 |
| `Error: That port is already in use` | Otro proceso en 8010 | `runserver 8011` |
| `DisallowedHost` | IP/host no está en `ALLOWED_HOSTS` | Añadirlo en `.env` y reiniciar |
| `CSRF verification failed` por IP o dominio | Falta origen | `CSRF_TRUSTED_ORIGINS=http://192.168.1.15:8010` |
| `migrate` falla creando el índice de `uniq_active_sprint_per_project` | Posible incompatibilidad con 8.0 | **Detenerse** y mandar el error completo |
