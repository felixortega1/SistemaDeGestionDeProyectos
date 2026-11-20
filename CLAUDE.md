# CLAUDE.md — Sistema de Gestión de Proyectos

Guía para trabajar en este repositorio. Describe **lo que existe hoy** en el código (extraído del repo en el commit `3c7117a`). Si el código y este archivo discrepan, manda el código: actualiza este archivo.

## Qué es

Monolito Django para gestionar proyectos con Scrum: empresas → proyectos → épicas → historias (con criterios de aceptación) → tareas → sprints (con métricas) → tablero Kanban con límites WIP, Gantt de solo lectura, presupuesto por departamento y "tickets diarios" por persona. Interfaz en español.

## Stack actual (versiones fijadas)

- Python + **Django 5.2.19**, plantillas Django + **HTMX 2.0.4** (sin SPA, sin API REST).
- Base de datos: **MySQL 8.0.46** (misma versión que producción; el código exige >= 8.0.16 por los CHECK) (`mysqlclient 2.3.1`). SQLite solo para desarrollo rápido (`DB_ENGINE=sqlite`).
- Contraseñas: **argon2-cffi** (Argon2 primero, PBKDF2 de respaldo).
- Estáticos: **whitenoise 6.12.0** (`CompressedStaticFilesStorage`). Servidor: **gunicorn 27.0.1**.
- Config por entorno: **django-environ** (`.env`).
- JS vendorizado en `static/vendor/` (sin npm ni build): HTMX 2.0.4, SortableJS 1.15.6, frappe-gantt 1.0.3. JS propio en `static/js/` (`board.js`, `gantt.js`, `tickets.js`, `ui.js`).
- Pruebas: pytest 9.2, pytest-django, pytest-cov, pytest-env. Lint: ruff 0.17.5.

## Servidor de producción (objetivo de deploy)

- VPS Ubuntu 24.04, 4 GB RAM (+2 GB swap), nginx como único punto de entrada con HTTPS (certbot) y un bloque por dominio.
- **Python 3.12** del sistema (venv propio en `/opt/gestion/.venv`), **MySQL 8.0.46 compartido con RAINAU** (solo escucha en 127.0.0.1) → este proyecto usa su **propia base y usuario** (`gestion_app_db` / `gestion_app`). Sin Docker: servicios con systemd.
- Patrón copiado de Ruteame (FastAPI): usuario de sistema propio, `/opt/<app>`, env en `/etc/<app>/<app>.env`, servicio systemd en puerto propio. Aquí: servicio `gestion`, gunicorn en `127.0.0.1:8003` (8001/8002 ocupados por Ruteame; verificar con `ss -tlnp`).
- Archivos de deploy en `deploy/` (ver `deploy/README-deploy.md`). Nunca tocar la base, usuarios ni servicios de RAINAU/Ruteame.
- **Línea base de versiones = producción** (Python 3.12, MySQL 8.0.46). El repo nació con MySQL 8.4 pero el código no usa nada exclusivo de 8.4 (mínimo 8.0.16 por los CHECK). Desarrollar y probar siempre contra 8.0.x. Riesgo a vigilar: índice único sobre `GeneratedField` virtual (`Sprint.active_project_id`). Cuando se actualice MySQL en el servidor, se actualiza en todos los proyectos a la vez.
- Datos: deploy nuevo, no hay datos de producción que migrar.

## Comandos

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env                                 # completar SECRET_KEY y MYSQL_*
docker compose up -d                                 # MySQL 8.0.46 local (o sin Docker: bash deploy/local-setup-wsl.sh)
python manage.py migrate
python manage.py createsuperuser                     # solo para /admin/
python manage.py seed_demo                           # datos de ejemplo (contraseña Demo12345!)
python manage.py runserver
pytest                                               # pruebas
pytest --cov=apps --cov-fail-under=80                # cobertura mínima 80 %
ruff check .                                         # lint (reglas E, F, I; línea 130; excluye migrations y static)
```

## Variables de entorno (`.env`)

`SECRET_KEY` (obligatoria; falla al arrancar sin ella), `DEBUG` (default `false`), `ALLOWED_HOSTS` (default `localhost,127.0.0.1`), `APP_TIMEZONE` (default `UTC`), `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` (default `projects`), `MYSQL_HOST` (default `127.0.0.1`), `MYSQL_PORT` (default `3306`), `DB_ENGINE` (`sqlite` para desarrollo), `CSRF_TRUSTED_ORIGINS`, `BEHIND_HTTPS_PROXY`.
Nunca commitear `.env`.

## Estructura

```
config/            settings, urls raíz, wsgi
apps/core/         permisos por rol, excepciones de servicio, middleware, bloqueos, helpers HTMX, comando seed_demo
apps/accounts/     User propio (login por email), registro/login/logout
apps/projects/     Company, Project, ProjectMember (roles), transferencia de PO
apps/backlog/      Epic, Story (epic, priority, stakeholder), AcceptanceCriterion (de Story), Task (FK opcional `story`), TaskDependency, Milestone, SprintTask (historial), Comment (de Story **o** Task)
apps/sprints/      Sprint (planned/active/closed)
apps/board/        BoardColumn (WIP, política, is_done), ColumnTransition, tablero
apps/gantt/        cálculo de fechas efectivas y estructura del Gantt (solo lectura)
apps/budget/       Department (presupuesto manual por área)
apps/tickets/      Ticket (pendientes diarios por persona y empresa)
templates/         una carpeta por app; fragmentos HTMX con prefijo `_`
tests/             una prueba por área, conftest con fixtures
docs/              plan-implementacion, guia-de-uso, reviews, diseño
docker/initdb/     01-grants.sh (permisos sobre bases `test_%` para pytest)
```

## Arquitectura (reglas vigentes)

1. **Capas:** `views.py` (HTTP, formularios, permisos) → `services.py` (reglas de negocio) → `models.py`. La lógica de negocio va en `services.py`, no en vistas ni plantillas.
2. **Errores de negocio:** los servicios lanzan `ServiceError` (`Conflict` 409, `Unprocessable` 422, `Forbidden` 403, `NotFound` 404) de `apps/core/exceptions.py`. `ServiceExceptionMiddleware` los convierte en `templates/error.html` con ese estado. No devolver códigos manualmente desde servicios.
3. **La tarea es la fuente de verdad.** Tablero y Gantt son vistas derivadas y de lectura (el Gantt es `readonly`).
4. **`sprint` y `column` de una tarea solo se escriben desde `backlog.services.apply_placement`**, y siempre van juntos (ambos nulos o ambos con valor). `update_task` nunca toca `column`, `sprint` ni estado.
5. **Concurrencia:** toda operación que cambie sprint/columna/WIP o borre tareas toma `lock_project(project_id)` (`SELECT … FOR UPDATE` sobre el proyecto) dentro de `transaction.atomic()`. Re-leer la fila tras el bloqueo.
6. **HTMX:** `fragment_or_redirect` devuelve el fragmento si la petición es HTMX y redirige si no. Sesión caducada en HTMX → 401 con `HX-Redirect` a login. Redirecciones `next` validadas con `url_has_allowed_host_and_scheme`.
7. **Base de datos:** `read committed`, `sql_mode=STRICT_TRANS_TABLES`, `utf8mb4`. Las invariantes críticas están **también como constraints** en BD (CheckConstraint / UniqueConstraint), no solo en Python. Hay `tests/test_migrations.py`.
8. **Borrados:** FKs con `PROTECT` por defecto; `CASCADE` solo en miembros, columnas, transiciones, hitos, departamentos y comentarios de la tarea.
9. **Idioma:** textos de interfaz, mensajes de error y docs en **español**; identificadores de código en **inglés**. `LANGUAGE_CODE="es"`, `USE_TZ=True`, `TIME_ZONE=APP_TIMEZONE`.
10. **Migraciones:** una por cambio, nunca editar migraciones ya aplicadas; ruff las excluye.

## Roles y permisos (`apps/core/permissions.py`)

Roles por proyecto (`ProjectMember.role`): `product_owner` (PO), `project_manager` (PM), `scrum_master` (SM), `developer` (DEV). Un usuario es miembro por proyecto, único por (proyecto, usuario).

- `ANY_ROLE` = los 4. `SM_UP` = PO+PM+SM. `STORY_CREATORS` = SM_UP. `PO_ONLY` = PO.
- Decorador `@project_role_required(roles, resolver)`: no autenticado → login (o 401 HTMX); **no miembro → 404** (no revela existencia); rol insuficiente → 403. Resolvers: `from_project_id`, `from_task_id`, `from_sprint_id`, `from_column_id`, `from_comment_id`, `from_department_id`. Deja `request.project`, `request.member`, `request.obj`.
- Todo acceso a datos se filtra por membresía en el proyecto (hay `tests/test_isolation.py`).

| Acción | Quién |
| --- | --- |
| Ver proyecto, historias, backlog, tablero, Gantt, presupuesto, sprints, miembros | Cualquier miembro |
| Editar proyecto; añadir/quitar/cambiar rol de miembros; transferir PO | PO |
| Crear tarea suelta y hitos (`task_new`, `milestone_new`); borrar tarea | PO |
| Crear historias y tareas de una historia | PO, PM, SM |
| Crear/editar épicas; añadir/quitar criterios de aceptación | PO, PM, SM |
| Borrar épica | PO |
| Marcar/desmarcar un criterio de aceptación | Cualquier miembro |
| Devolver una tarea de un sprint planificado al backlog | PO, PM, SM |
| Crear/editar/iniciar/cerrar sprint; asignar tarea o historia (todas sus tareas pendientes) a sprint | PO, PM, SM |
| Crear/editar columnas y transiciones del tablero | PO, PM, SM |
| Crear/editar/borrar departamentos (presupuesto) | PO, PM, SM |
| Editar tarea (`can_edit_task`) | PO siempre; DEV solo si es su responsable |
| Mover tarea en el tablero (`can_move_task`) | PO/PM/SM siempre; DEV solo si es suya o sin responsable |
| Comentar, añadir/quitar dependencias | Cualquier miembro |
| Borrar comentario | Su autor o el PO |

## Reglas de negocio vigentes

**Cuentas**
- Login por email (único, siempre en minúsculas), sin username. Contraseña mínimo 8 caracteres (`MinimumLengthValidator`). Sesión de 8 h (`28800`), cookies `HttpOnly`; `Secure` cuando `DEBUG=false`.
- `/admin/` es solo para el operador (superusuario).

**Proyectos**
- Pertenecen a una `Company`; si no se indica empresa se usa/crea "General". Solo se puede elegir una empresa donde ya se participa.
- Quien crea el proyecto queda como PO y se le crea el tablero por defecto.
- `end_date >= start_date`. Máximo **3 objetivos** (uno por línea, ≤200 caracteres c/u).
- Miembros: no se puede asignar PO con `add_member`/`change_role` (solo por **transferencia**; el PO saliente pasa a PM, SM o DEV). No se puede quitar al PO ni cambiar su rol directo. No se puede quitar a un miembro con tareas asignadas sin terminar. Hay que registrar antes al usuario (se busca por email).

**Backlog / tareas**
- `Story` y `Task` son **tablas separadas** (no existe `kind` ni `parent`). `Story`: título, descripción, stakeholder, prioridad, puntos, épica; sin sprint ni columna. `Task`: `story` (FK `PROTECT`, opcional, mismo proyecto), sprint, columna, asignado, puntos, fechas. Prioridad y épica de una tarea son las de su historia.
- Servicios: `create_story/update_story/delete_story`, `create_task/update_task/delete_task`. Rutas: `/projects/<id>/stories/`, `/stories/<id>/` (`story_detail`: criterios, tareas, comentarios, asignar a sprint), `/stories/<id>/tasks/new/`, `/stories/<id>/assign-sprint/`.
- El responsable debe ser miembro del proyecto (se tolera mantener uno antiguo).
- Dependencias solo entre tareas del mismo proyecto; sin autodependencia, sin duplicados, **sin ciclos**.
- Borrar historia: solo PO y sin tareas (409). Borrar tarea: solo si no tiene dependencias, sprint ni historial (si no → 409).
- Comentarios: solo miembros; no vacíos; pertenecen a una historia **o** a una tarea (CHECK `comment_story_xor_task`). Rutas: `/stories/<id>/comments/add/`, `/tasks/<id>/comments/add/`.

**Épicas** (`Epic`: proyecto, título, descripción, color `#RRGGBB`)
- Solo `Story` tiene épica (mismo proyecto). Una tarea **hereda** la épica de su historia; `Task` no tiene campo `epic`.
- Color validado como hexadecimal `#RRGGBB` (se guarda en mayúsculas). Servicios: `create_epic`, `update_epic`, `delete_epic`. No se borra una épica con historias (`Conflict` 409; además `Story.epic` es `PROTECT`).
- `/projects/<id>/stories/` agrupa las historias por épica con barra de avance (tareas hechas / totales), sección «Sin épica» al final y filtro `?epic=<id>|none`.

**Criterios de aceptación** (`AcceptanceCriterion`: tarea, texto ≤500, `is_done`, `position`)
- Pertenecen a **historias** (no a tareas). Texto no vacío. Servicios: `add_criterion`, `toggle_criterion(criterion, user)` (exige ser miembro), `delete_criterion`, `criteria_counts`.
- La UI es un checklist HTMX (`templates/backlog/_criteria.html`, se reemplaza completo con `hx-target="#criteria"`). Las respuestas HTMX de este fragmento siempre son 200 (los errores se muestran dentro) para que HTMX las intercambie. Sin HTMX redirigen a `/tasks/<id>/#criterios`.
- Insignia `X/Y` en la lista de historias y en las tarjetas del tablero (criterios de su historia).

**Prioridad**
- `Task.priority`: `high` (Alta), `medium` (Media, por defecto), `low` (Baja), con CHECK `task_priority_valid`. Si el formulario no envía prioridad se usa Media.
- Historias y backlog se ordenan con `order_by_priority` (alta → media → baja, luego id). Filtros por GET en el Backlog: `?priority=` y `?epic=` (valores inválidos se ignoran; en una tarea cuenta la prioridad/épica de su historia).
- Los puntos de estimación se sugieren con la escala 1-2 (S), 3-5 (M), 8 (L).

**Sprints**
- Estados `planned → active → closed`. Fin ≥ inicio. Un sprint cerrado no se edita.
- **Solo un sprint activo por proyecto** (garantizado por `GeneratedField active_project_id` + índice único). Para iniciar se exigen fechas de inicio y fin.
- Asignar a sprint: solo tareas, sin sprint previo, del mismo proyecto, sprint planned/active; entran en la **primera columna**. Asignar una historia (`assign_story_to_sprint`) asigna todas sus tareas pendientes en bloque (todo o nada).
- `unassign_sprint(task)` (`POST /tasks/<id>/unassign-sprint/`): devuelve la tarea al backlog **solo si su sprint está `planned`** (bajo `lock_project` y vía `apply_placement(task, None, None)`); sin sprint → 422; sprint activo o cerrado → 409. Botón «Devolver al backlog» en los sprints planificados.
- Métricas (`backlog.services.sprint_metrics(project)`, solo lectura; vive en `backlog` porque `sprints` no puede importar capas superiores): sprints `planned`/`active` → puntos y tareas totales/hechas y % (por puntos; si no hay estimaciones, por cantidad de tareas); `closed` → puntos comprometidos y completados desde `SprintTask`. **Velocidad promedio** = promedio de puntos completados de los sprints cerrados (se muestra en la cabecera de Sprints).
- Cerrar sprint: guarda historial (`SprintTask`: columna, si estaba hecha, puntos); las **no terminadas vuelven al backlog** (sprint/columna a nulo); guarda notas de review y retro.

**Tablero Kanban**
- Columnas por defecto: Por hacer · En desarrollo (**WIP 3**) · En revisión · Hecho (`is_done`), con transiciones **bidireccionales entre adyacentes**; no se puede saltar pasos.
- Nuevas columnas se insertan **antes de la de "Hecho"** y se conectan a la anterior y a "Hecho".
- Transiciones configurables por proyecto (`set_transitions`); no a sí misma ni entre proyectos.
- Tarjetas (`board/_card.html`): chip de prioridad solo si es Alta, título de la historia padre enlazado, punto con el color de la épica y criterios `X/Y`. `get_board` usa `select_related("assignee", "story", "story__epic")` y una sola consulta agregada para los criterios.
- Mover tarea: solo tareas del **sprint activo**, dentro de su proyecto, siguiendo transiciones permitidas. WIP se valida al colocar (en sprint activo); excederlo → 409.

**Gantt** (`apps/gantt/services.py`, función pura `effective_dates`)
- Fechas de la tarea; si faltan, hereda las del sprint. Sin fechas, una sola o fin<inicio → va a la lista "sin fecha".
- Atrasada (rojo) si no está en columna `is_done` y su fin < hoy. Conflicto (naranja) si inicia antes de que termine su predecesora (excepto cuando ambas heredan fechas del mismo sprint).

**Presupuesto**
- Por departamento y proyecto: nombre único por proyecto, monto ≥ 0 (`Decimal(14,2)`), moneda de **3 letras mayúsculas** (ISO, p. ej. USD). Es solo un registro manual: **no** hay gasto real, facturación ni horas.

**Tickets diarios**
- Pendiente del día ligado a una empresa. Solo se crean/ven en empresas donde se participa; cada persona ve **solo los suyos** (hoy + pendientes anteriores; los hechos solo el día).
- Asignar a otra persona: solo PO/PM/SM de esa empresa y a alguien de la misma empresa. DEV solo para sí mismo.
- Cambiar estado: asignado o creador. Borrar: creador o PO/PM/SM de la empresa.

## Seguridad y producción

- `DEBUG=false`, HTTPS, `gunicorn config.wsgi`, `python manage.py collectstatic` (a `staticfiles/`, servido por whitenoise).
- Detrás de proxy HTTPS: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `BEHIND_HTTPS_PROXY=true` (usa `X-Forwarded-Proto`).
- `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` se activan cuando `DEBUG=false`.
- CSRF activo en todos los POST (los tests usan `CsrfClient` con CSRF forzado).

## Pruebas

- `tests/conftest.py` provee fixtures: `make_user`, `client_for`, `po`, `project`, `add_member`, `sm`, `dev`, `make_task`, `active_sprint`, `columns`.
- `tests/test_scrum.py` cubre épicas, historias/tareas separadas, XOR de comentarios, criterios, prioridad, `unassign_sprint`, métricas, tablero y `seed_demo`.
- Una prueba por área (`test_board_wip`, `test_board_transitions`, `test_roles`, `test_isolation`, `test_gantt_dates`, `test_flow`, …). La prueba de concurrencia real de WIP **se omite en SQLite**: validar con MySQL.
- Nueva funcionalidad = pruebas nuevas; mantener cobertura ≥ 80 %.
- Pytest necesita permisos para crear `test_<db>` (lo da `docker/initdb/01-grants.sh`, solo con volumen vacío; si ya existe: `docker compose down -v`).

## Fuera de alcance actual

Facturación, control de horas, gasto real, app móvil, integraciones, notificaciones, edición avanzada del Gantt, línea base y ruta crítica (fase 2). No añadir sin acordarlo.

## Convenciones para cambios

- Reutilizar `project_role_required` y los servicios existentes; no saltarse `apply_placement` ni `lock_project`.
- Regla nueva → servicio + constraint en BD si es una invariante + prueba + actualizar `docs/guia-de-uso.md` y este archivo.
- Solo Python en backend; frontend con plantillas + HTMX + JS vendorizado (no introducir frameworks JS ni pipeline de build sin acuerdo).
- Mantener documentación y textos en español.

## Documentación

`README.md`, `docs/guia-de-uso.md`, `docs/designs/plan-implementacion.md`, `docs/designs/diseno-visual-web.md`, `docs/design_draft.md`, `docs/reviews/`.
