# Sistema de Gestión de Proyectos

Herramienta de seguimiento de proyectos que combina Scrum, un tablero Kanban con límites WIP, un diagrama de Gantt y un presupuesto ingresado manualmente por área del proyecto.

> **Diferencial frente a Jira y Linear (premisa del autor, no comparada):** tablero con WIP, Gantt derivado del sprint y presupuesto por departamento bajo la misma fuente de verdad, desplegable por la propia organización con un proceso Django y MySQL.

## Estado

MVP implementado según el [plan de implementación](docs/designs/plan-implementacion.md).

## Instalación y arranque

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows (en Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
cp .env.example .env              # y rellena SECRET_KEY y las variables MYSQL_*
docker compose up -d              # MySQL 8.0 local (igual que producción). Sin Docker: ver deploy/local-setup-wsl.sh
python manage.py migrate
python manage.py createsuperuser  # solo para /admin/ (operador)
python manage.py runserver
pytest                            # pruebas
pytest --cov=apps --cov-fail-under=80
```

Notas:

- `docker/initdb/01-grants.sh` concede a `MYSQL_USER` permisos sobre `test_%` para que Django cree la base de pruebas; solo corre con el volumen vacío (si ya existe: `docker compose down -v`).
- Atajo de desarrollo sin MySQL: `DB_ENGINE=sqlite` en `.env` usa `db.sqlite3`. La prueba de concurrencia real del WIP se omite en SQLite; el bloqueo por proyecto solo se ejerce con MySQL.
- En producción: `DEBUG=false`, HTTPS, `gunicorn config.wsgi` y `python manage.py collectstatic`. Detrás de un proxy HTTPS fija también `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `BEHIND_HTTPS_PROXY=true`.

## Alcance

**MVP**
- Proyectos, backlog, sprints.
- Tablero Kanban con límites WIP y política de transición por columna.
- Gantt de solo lectura, derivado de tareas y sprints.
- Presupuesto por área: monto y moneda.

**Fuera de alcance (por ahora)**
- Facturación, control de horas y seguimiento del gasto real.
- App móvil, integraciones, notificaciones.
- Edición avanzada del Gantt, línea base y ruta crítica (fase 2).

## Decisiones tomadas

- La tarea (estado, estimación, dependencias, sprint) es la fuente de verdad. Tablero y Gantt son vistas derivadas.
- Un monolito modular.
- Aplicación web hecha solo en Python: Django, plantillas con HTMX y MySQL. Repositorio único (monorepo).

## Documentación

- [docs/design_draft.md](docs/design_draft.md): borrador de diseño.
- [docs/guia-de-uso.md](docs/guia-de-uso.md): guía de uso.
- [docs/reviews/](docs/reviews/): revisiones del plan.
- [docs/plan-prompt.md](docs/plan-prompt.md): prompt para generar el plan del sistema.
- [docs/designs/plan-implementacion.md](docs/designs/plan-implementacion.md): plan de implementación (fases, archivos y verificación).

## Idioma

Documentación y textos de la interfaz en español. Identificadores del código en inglés.
