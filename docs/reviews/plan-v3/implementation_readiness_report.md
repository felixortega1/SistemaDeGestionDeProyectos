# Informe de revisión Goldfish

**Objetivo:** `docs/designs/plan-implementacion.md` (líneas 297-451)

## Estado de los revisores

| Revisor | Estado |
| --- | --- |
| `egm-implementation-readiness` | completado |
| `egm-codebase-details` | completado |
| `egm-style` | completado |

Veredicto: el plan no está listo para implementarse sin decisiones del implementador. Hay 3 Blockers, 10 Majors y varios Nits.

## Blockers

### B1. La invariante `is_done` choca con `create_column` - Severity: Blocker
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`, `style`
* **Affected Scope:** líneas 100 y 373
* **Discrepancia:** `update_column` exige una sola columna `is_done` y que sea la última. `create_column` añade la columna nueva "al final", así que "Hecho" deja de ser la última. No se define qué pasa con las transiciones sembradas, con la "primera columna" ni con `close_sprint`. Tampoco se fija el valor inicial de `position`.
* **Recomendación:** fijar una regla explícita. Por ejemplo, `create_column` inserta antes de la columna `is_done` y siembra transiciones con la columna anterior y con la `is_done`. Definir `position` (valor inicial, unicidad por proyecto, reordenación) y añadir una prueba.

### B2. `create_project` rompe la regla de capas y `test_imports` no lo detecta - Severity: Blocker
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** líneas 65, 367, 372 y 400
* **Discrepancia:** un `services.py` solo importa capas inferiores y `projects` va antes que `board`. Sin embargo, `projects.services.create_project` llama a `board.services.create_default_board`. `tests/test_imports.py` solo detecta ciclos, no el orden de capas, y un import perezoso tampoco se detecta.
* **Recomendación:** elegir una vía. Mover `board` por debajo de `projects` (viable, porque `board.models` usa cadenas), o mover la orquestación a la vista de `projects`. Hacer que `test_imports.py` verifique el orden de capas con análisis AST.

### B3. Un paso E2E de F1 depende de una página de F3 - Severity: Blocker
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`, `style`
* **Affected Scope:** líneas 311, 386 y 425
* **Discrepancia:** el paso 2, marcado F1, espera "4 columnas en la página de columnas". `columns.html` y sus vistas son de F3. El criterio de aceptación de L320 sí es verificable en F1.
* **Recomendación:** mover el paso a F3 o verificarlo en F1 por el admin o la shell.

## Major

### M1. `assign_sprint` necesita el WIP en F2, pero este se especifica en F3 - Severity: Major
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** líneas 136, 310-311 y 375
* **Discrepancia:** la regla 10 aplica el WIP en `assign_sprint`. El bloqueo, el conteo y el reintento solo se describen en `move_task` (F3). No hay pruebas de F2 para ello.
* **Recomendación:** extraer `_enforce_wip(column, sprint, exclude_task)` y asignarlo a F2 con pruebas. O retirar ese comportamiento del criterio de F2.

### M2. Faltan firmas y retornos de la mayoría de los servicios - Severity: Major
* **Reviewer Lens:** `implementation-readiness`
* **Affected Scope:** líneas 370-377
* **Discrepancia:** solo seis servicios tienen firma. Faltan los de sprint, `assign_sprint`, dependencias, CRUD de tareas, épicas e hitos, `create_project`, miembros, `update_column` y `set_transitions`. `get_board` no define su retorno, del que dependen `_board.html` y `_card.html`. No está claro quién comprueba los permisos.
* **Recomendación:** añadir una tabla con firma, retorno, excepciones y responsable del permiso por servicio.

### M3. Faltan el resolvedor de columnas y el mecanismo de conversión de excepciones - Severity: Major
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** líneas 146-148, 163 y 370
* **Discrepancia:** `POST /columns/<id>/edit/` necesita `from_column_id`, que no existe. No se comprueba que `dep_id` pertenezca a la tarea. El plan dice que "las vistas convierten" `Conflict`, `Unprocessable`, `Forbidden` y `NotFound`, pero no nombra middleware ni decorador. Tampoco se dice quién devuelve el 401 con `HX-Redirect`, porque `login_required` redirige con 302.
* **Recomendación:** añadir `from_column_id` (F3) y cubrirlo en `test_isolation.py` y `test_roles.py`. Especificar un middleware o decorador común y añadirlo a `MIDDLEWARE`.

### M4. Los archivos de `frappe-gantt`, HTMX y SortableJS no están fijados - Severity: Major
* **Reviewer Lens:** `implementation-readiness`
* **Affected Scope:** líneas 33-34, 303, 387 y 392
* **Discrepancia:** los nombres de archivo y las opciones cambian entre 0.6.x y 1.x, y la versión se difiere. Sin ella no se pueden escribir `gantt.html`, `gantt.js` ni `base.html`. El plan B (tabla HTML/CSS) necesita desplazamiento y ancho, que el contrato de L157 no incluye.
* **Recomendación:** fijar versiones y nombres de archivo ahora. Documentar el campo extra del plan B o eliminarlo.

### M5. La columna generada del sprint activo está mal especificada - Severity: Major
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** líneas 99, 374 y 403
* **Discrepancia:** no se da la expresión literal. Un `GeneratedField` no puede ser una FK, así que el nombre real de la columna sería `active_project`, no `active_project_id`, que es el que usa el SQL de respaldo. Si el respaldo `RunSQL` se aplica sin estado, `makemigrations --check` en `test_migrations.py` falla. Django 5.2 exige `db_persist` explícito.
* **Recomendación:** escribir el campo literal (`Case/When` o `If`, `output_field=BigIntegerField(null=True)`, `db_persist=False`). Alinear el nombre del SQL de respaldo y usar `SeparateDatabaseAndState`, con el mismo nombre de índice en el `UniqueConstraint`.

### M6. La comprobación de tareas asignadas en F1 no tiene mecanismo - Severity: Major
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** línea 372
* **Discrepancia:** `apps.get_model("backlog", "Task")` lanza `LookupError` en F1, cuando `backlog` no está instalada. No se dice cómo se "activa".
* **Recomendación:** fijar un `try/except LookupError` que devuelva falso, o `apps.is_installed`.

### M7. Faltan decisiones de los modelos - Severity: Major
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** líneas 92-105 y 375
* **Discrepancia:** faltan los `related_name` de `TaskDependency` (dos FK a `Task`) y de `Task.parent` y `Task.epic`. Faltan `max_length`, nulidad y `on_delete` (incluido `SprintTask`). No se distingue qué invariantes son `CheckConstraint` y cuáles validación del servicio. El índice `Task(assignee)` es redundante.
* **Recomendación:** añadir una tabla de campos y listar los `CheckConstraint` literales.

### M8. Las pruebas de cableado y la configuración tienen huecos - Severity: Major
* **Reviewer Lens:** `implementation-readiness`, `codebase-details`
* **Affected Scope:** líneas 355, 361 y 399-400
* **Discrepancia:** `test_imports` necesita `django.setup()` y no dice cómo descubre los módulos `services`. `pytest-env` no fija `DATABASE_URL` ni `APP_TIMEZONE`, y no hay valores por defecto de `APP_TIMEZONE` ni de `ALLOWED_HOSTS`. Sin `.env`, las pruebas fallan.
* **Recomendación:** documentar el valor por defecto de cada variable y añadir `DATABASE_URL` al bloque `env` de pytest, o documentar el requisito.

### M9. Permisos de creación de tareas para Developer sin definir - Severity: Major
* **Reviewer Lens:** `implementation-readiness`
* **Affected Scope:** líneas 125 y 133
* **Discrepancia:** "Developer solo sus tareas", pero una tarea nueva no tiene `assignee`. No se dice quién asigna o reasigna al crear.
* **Recomendación:** fijar la regla en `can_edit_task` y en la vista `tasks/new`.

### M10. El criterio de aceptación de F4 no es verificable con pytest - Severity: Major
* **Reviewer Lens:** `codebase-details`, `style`
* **Affected Scope:** líneas 33, 181, 337, 391 y 418
* **Discrepancia:** "lleva la clase `is_late` en el HTML". La clase la crea `gantt.js` en el navegador, y el JS propio no tiene pruebas. En el HTML solo existe `is_late` dentro del `json_script`.
* **Recomendación:** redactarlo como "`build_gantt` devuelve `is_late: true`" o "el JSON contiene `is_late: true`". Pasar la clase CSS al recorrido manual.

### M11. El docker de F1 falla en Windows por CRLF - Severity: Major
* **Reviewer Lens:** `codebase-details`, `implementation-readiness`
* **Affected Scope:** línea 352
* **Discrepancia:** con `autocrlf`, `01-grants.sh` llega con CRLF y el entrypoint de `mysql:8.4` falla. Los grants no se aplican y Django no puede crear `test_<base>`.
* **Recomendación:** añadir `.gitattributes` con `*.sh text eol=lf` a la lista de F1.

### M12. El E2E tiene pasos incoherentes - Severity: Major
* **Reviewer Lens:** `style`, `codebase-details`
* **Affected Scope:** línea 434
* **Discrepancia:** el paso 11 habla de tareas "terminadas" que conservan sprint, pero ningún paso previo lleva una tarea a "Hecho". Es un paso de F2 listado después de los de F4.
* **Recomendación:** añadir el paso que mueve una tarea hasta "Hecho" y ordenar la tabla por fase.

## Nit

* **N1. `move_task` con tarea obsoleta (L115, L408).** El servicio debe releer la tarea tras bloquear la columna. La prueba de L408 no dice qué comportamiento verifica. `update_column` tampoco indica `select_for_update` (regla 3).
* **N2. Fecha de MySQL 8.0 (L303).** Hoy es 2026-11-17 y el fin de soporte ya ocurrió (abril de 2026). Quitar "lo que hay que confirmar".
* **N3. Licencia de HTMX (L392).** HTMX 2 es 0BSD, no MIT.
* **N4. `DATABASE_URL` (L350).** Usar `127.0.0.1` en vez de `localhost` (en Linux/macOS usa socket Unix) y aplicar percent-encoding a las contraseñas.
* **N5. Cobertura (L313, L341, L419).** `--cov=apps` incluye `migrations/`. Añadir `omit` en `[tool.coverage.run]`. En la tabla, "cobertura mínima" debería decir "80 %".
* **N6. `docker-compose.yml` (L351).** Falta un healthcheck, porque `migrate` tras `up -d` falla mientras MySQL arranca. Tampoco se fija el puerto 3306.
* **N7. Archivos no listados (L163, L367, L377).** Faltan `apps.py` (nombre `apps.<app>`) y `admin.py` con un `UserAdmin`. `settings.py` no define `BASE_DIR`, `SECURE_PROXY_SSL_HEADER` ni `CSRF_TRUSTED_ORIGINS`.
* **N8. Dependencias de migración (L367).** Omiten `AUTH_USER_MODEL` (`updated_by`, `created_by`, `assignee`). `makemigrations` lo añade solo.
* **N9. Rutas (L146-147).** Varias rutas solo `POST` no indican qué página se redibuja con 422. No hay `GET` del formulario de sprint. Faltan los valores válidos de `role` (`product_owner` solo por `transfer-po`).
* **N10. Consecuencia no mencionada (L109).** Una tarea devuelta al backlog conserva filas de `SprintTask`, así que no se puede borrar nunca (409).
* **N11. Estilo (L299, L355, L367, L391, L396, L404, L13).** Correcciones menores:
  * "ejecutable y probable" debería decir "verificable con `pytest`".
  * "reglas" de Ruff sin especificar.
  * "se revisan" sin criterio.
  * L391: dar el criterio del plan B (si falla cualquiera de las cuatro condiciones).
  * L396: explicar la diferencia de SQLite (`select_for_update` sin efecto y sin columnas generadas con índice único).
  * L404: "403 o 404 según corresponda" remite a la regla 7 (L119).
  * "pequeñas" es subjetivo.
  * "Marca el paquete" y "(fase 2)" se repiten.
* **N12. `isolation_level` (L115, L361).** `READ COMMITTED` ya es el valor por defecto de Django en MySQL. Mantener la declaración explícita y una prueba, pero la justificación es innecesaria.

## Verificado como correcto

* `CheckConstraint(condition=...)` en Django 5.1+.
* CHECK en MySQL desde 8.0.16.
* `UniqueConstraint` sobre columna virtual con varios NULL en InnoDB.
* `Client(enforce_csrf_checks=True)`.
* `htmx:beforeSwap` con 409/422.
* `htmx.ajax` en HTMX 2.
* `HX-Redirect` con 401.
* `hx-headers` en `<body>`.
* `LogoutView` exige POST en Django 5.
* SortableJS 1.15.x y `frappe-gantt` (MIT).
* Ruedas de `mysqlclient` para Windows.
* Grafo de migraciones acíclico y orden `accounts`, `projects`, `board`/`sprints`, `backlog`, `budget` coherente.
* No hay ciclos de import reales.
