# Goldfish Review Report

**Target:** `docs/designs/plan-implementacion.md` (`líneas 267-384`; el resto leído como contexto)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-implementation-readiness` | completed |
| `egm-codebase-details` | completed |
| `egm-style` | completed |

Veredicto: el plan no está listo para implementarse sin decisiones del implementador. Hay 3 Blockers, 13 Majors y varios Nits.

## Prioritized Findings (Blockers -> Major -> Nits)

### Ciclo de imports en la capa de servicios (backlog, board, sprints, core) - Severity: Blocker
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L307, 310, 313-316 (reglas L111-112)
* **Discrepancy Description**: A nivel de modelos no hay ciclo (las FK usan referencias en cadena). A nivel de servicios sí lo hay.
  * `backlog.services.assign_sprint` llama a `board.services.apply_placement`.
  * `board.services` importa `backlog.models.Task`.
  * `sprints.services.close` importa `backlog.models` y `board`.
  * `core.permissions` importa modelos de backlog, sprints y budget, pero todas las apps lo importan.
  * La regla "una app solo importa services y models de otra" no rompe el ciclo.
* **Rationale & Recommendation**: Escribir una jerarquía de capas, por ejemplo accounts, projects, board, sprints, backlog, budget. Mover `apply_placement` y `move_task` a `backlog.services`, que es el dueño de `Task`. Hacer que `core.permissions` resuelva modelos con `apps.get_model` o con imports dentro de funciones. Exigir referencias en cadena en los modelos. Añadir una prueba que importe cada módulo de servicios por separado.

### Dependencia de fase F2 hacia F3 (`apply_placement`) - Severity: Blocker
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L278, 279, 313-315, 341-346, 351
* **Discrepancy Description**: `apply_placement` está asignado a F3. Pero `backlog.assign_sprint` y `sprints.close` (ambos F2) lo llaman, y el criterio de F2 ("las tareas sin terminar quedan en la primera columna") lo necesita. Esto contradice "cada fase deja el sistema ejecutable y probable" (L269).
* **Rationale & Recommendation**: Mover `apply_placement` y la parte de WIP que usa `assign_sprint` a F2, y dejar en F3 solo `move_task`, las vistas y `board.js`. La alternativa es mover `assign-sprint` a F3.

### El E2E y la matriz de roles no son ejecutables por un solo usuario - Severity: Blocker
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L117-128, 171, 312, 359-369
* **Discrepancy Description**: El creador del proyecto queda como Product Owner. Según la matriz, el PO no abre, cierra ni asigna sprints (eso es del Scrum Master), y solo se pueden añadir miembros ya registrados. Los pasos 3 y 10 del E2E no los puede ejecutar un solo usuario, y el E2E no dice qué usuario hace cada paso. `ProjectMember` permite un solo rol por (project, user).
* **Rationale & Recommendation**: Decidir una opción y documentarla: el creador es PO y SM a la vez, el PO también gestiona sprints, o se permiten varios roles. Si el diseño no cambia, reescribir el E2E indicando qué usuario ejecuta cada paso.

### Aislamiento de MySQL (REPEATABLE READ) puede romper el bloqueo del WIP - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-implementation-readiness`
* **Affected Scope:** L111, 181, 301, 313, 347
* **Discrepancy Description**: En InnoDB con REPEATABLE READ, una lectura normal previa al `select_for_update` fija el snapshot. El `count` del WIP puede entonces ignorar un commit concurrente y superar el límite. El orden de lecturas y el mecanismo de reintento por deadlock (1213) no están definidos.
* **Rationale & Recommendation**: Fijar `OPTIONS["isolation_level"] = "read committed"`. Especificar el orden dentro de `atomic()`: bloquear la columna, contar, actualizar. Hacer que el reintento envuelva todo el bloque `atomic`, e indicar qué devuelve el segundo fallo. Añadir una prueba que cargue la tarea antes del bloqueo.

### Core, permisos y pruebas de F1/F2 dependen de modelos de fases posteriores - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L278, 301, 302, 310, 340-344
* **Discrepancy Description**: `core/permissions.py` (F1) define resolvedores sobre modelos que no existen hasta F2 y F5. `test_roles.py` y `test_isolation.py` (F2) cubren acciones de F3 y F5. `settings.py` y `urls.py` enumeran todas las apps en F1, y ningún ítem los marca como Modify en F2-F5.
* **Rationale & Recommendation**: Añadir los resolvedores por fase, con Modify de `core/permissions.py`, `config/settings.py`, `config/urls.py`, `base.html` y `styles.css` en cada fase. Repartir las pruebas de roles y aislamiento por fase.

### Orden de validaciones en `move` sin definir - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L111-112, 149
* **Discrepancy Description**: Hay cuatro comprobaciones sin orden: permiso por responsable, sprint no activo (422), misma columna (200) y transición no permitida (422). Con "primero comprueba el par", mover a la misma columna daría 422 en vez de 200. No se dice qué pasa al mover una `story`, que no tiene columna.
* **Rationale & Recommendation**: Documentar la secuencia: permiso, columna destino, kind=task, sprint activo, misma columna (200), transición (422), WIP (409). Añadir el caso de la historia (422).

### Permisos a nivel de objeto sin dueño - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L116, 121-123, 310
* **Discrepancy Description**: "Solo sus tareas" y "mover si es responsable o no tiene responsable" dependen del objeto, pero no se dice dónde se aplican ni cómo recibe la vista el proyecto resuelto. Faltan reglas sobre quién cambia `assignee`, qué pasa con tareas de un miembro que se quita, y el 403/404 en HTMX.
* **Rationale & Recommendation**: Añadir `can_edit_task` y `can_move_task` en `core.permissions`, fijar cómo llega el proyecto a la vista, y definir la política de borrar miembros con tareas asignadas (409).

### Transferencia del Product Owner indefinida - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L93, 128, 312
* **Discrepancy Description**: No se dice qué rol pasa a tener el PO saliente ni si la operación es atómica. Con un solo rol por usuario, el estado intermedio rompe la unicidad.
* **Rationale & Recommendation**: Definir `transfer_product_owner(project, new_po, old_po_new_role)` con su regla y su prueba.

### Columnas y transiciones: faltan reglas de creación y orden - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L49, 97, 313, 326
* **Discrepancy Description**: El texto dice que crear una columna siembra transiciones, pero el ítem 19 habla solo de edición. No se define dónde se inserta la columna, cómo se reordena `position`, si hay unicidad (project, position), si `is_done` es editable, ni si puede haber varias columnas `is_done`. Tampoco se define cuál es la "primera" columna. La ruta mezcla creación y edición sin los campos del formulario.
* **Rationale & Recommendation**: Especificar los campos, la acción de crear (se añade al final y siembra transiciones con la antigua última), la unicidad y el criterio de "primera columna" (menor `position`).

### Docker initdb: `01-grants.sql` no conoce el usuario de la aplicación - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-implementation-readiness`
* **Affected Scope:** L290-291
* **Discrepancy Description**: Los `.sql` de initdb no interpolan variables de entorno, así que el nombre del usuario puede no coincidir con `MYSQL_USER`. Solo corren con el volumen vacío. Sin el permiso, `pytest` no puede crear `test_<base>`. Faltan el host de la cuenta, el charset `utf8mb4` y el puerto.
* **Rationale & Recommendation**: Usar `01-grants.sh`, que lee `$MYSQL_USER`. Documentar que hay que recrear el volumen. Indicar `'user'@'%'`.

### Fallback PyMySQL sin archivo ni dependencia asignados (Windows) - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L157, 271, 300
* **Discrepancy Description**: `pymysql.install_as_MySQLdb()` no tiene archivo asignado (`config/__init__.py` solo "marca el paquete") y PyMySQL no está en `requirements.txt`. Django 5.2 exige además ocultar la versión del cliente. El entorno de desarrollo es Windows, así que la decisión es inmediata. En Linux, `mysqlclient` necesita cabeceras de MySQL.
* **Rationale & Recommendation**: Elegir una opción y fijarla: mysqlclient con rueda binaria, o PyMySQL con el parche en `config/__init__.py`. Documentar los paquetes del sistema.

### MySQL 8.0 está fuera de soporte - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** L271, 290
* **Discrepancy Description**: A fecha 2026-11-17, MySQL 8.0 ya terminó su vida útil (abril de 2026). La imagen `mysql:8.0` no recibe parches.
* **Rationale & Recommendation**: Fijar MySQL 8.4 LTS, que Django 5.2 soporta. Anotar que 8.4 desactiva `mysql_native_password` por defecto y que PyMySQL necesita `cryptography`. Mantener el mínimo 8.0.16 por los `CHECK`.

### Columna generada con SQL a mano en vez de `GeneratedField` - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-implementation-readiness`
* **Affected Scope:** L96, 314
* **Discrepancy Description**: El plan usa `RunSQL` con una columna invisible para el ORM, y falta el DDL exacto (tabla `sprints_sprint`, índice, `reverse_sql`). Django 5.0+ tiene `GeneratedField` con soporte MySQL. Con la columna invisible, un `AlterField` futuro sobre `status` o `project` fallará. `UniqueConstraint(condition=...)` no sirve en MySQL, por lo que el plan acierta al usar una columna generada.
* **Rationale & Recommendation**: Usar `GeneratedField` más `UniqueConstraint`, o justificar por escrito por qué se descarta. Si se mantiene `RunSQL`, incluir el DDL de ida y de vuelta y prohibir migraciones posteriores sobre `status` y `project_id`.

### frappe-gantt: archivos y opciones dependen de la versión - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** L271, 332, 334, 103, 151
* **Discrepancy Description**: `frappe-gantt.min.js/.css` son de la serie 0.6.x. La 1.x publica otros nombres, tiene `readonly` y acepta `dependencies` como arreglo (según el revisor, no verificado contra el paquete actual). Hitos e historias resumen no tienen soporte nativo y `gantt.js` no dice cómo se dibujan. La estructura de L151 no incluye historias.
* **Rationale & Recommendation**: Fijar la versión antes de cerrar la lista de archivos y no asumir `.min.js`. Definir si los hitos son tareas de un día y las historias barras `custom_class="summary"`, o solo HTML. Resolver en la prueba de concepto cómo combinar `is_late` y `conflict` en `custom_class`.

### SortableJS se destruye al reemplazar el tablero con HTMX - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-implementation-readiness`
* **Affected Scope:** L149, 330
* **Discrepancy Description**: `move` devuelve el tablero completo y HTMX lo reemplaza, lo que destruye las instancias de Sortable. `board.js` no menciona reinicializar tras `htmx:load` o `htmx:afterSwap`. Faltan también el `id` del contenedor, el `swap` y el origen de la URL (por ejemplo `data-move-url`).
* **Rationale & Recommendation**: Documentar una reinicialización idempotente en `htmx:load` y el selector de destino de `htmx.ajax`.

### Entorno y settings sin especificar - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L289, 301
* **Discrepancy Description**: No se dice cómo `django-environ` carga `.env` (`read_env`), ni cómo se combinan `DATABASE_URL` y `OPTIONS` (el parser no trae `charset` ni `init_command`). `pytest` falla sin `SECRET_KEY` y no hay entorno de pruebas definido. `DEBUG` en CI, `APP_TIMEZONE`, `LOGIN_REDIRECT_URL` y los ajustes de proxy HTTPS (`SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`) tampoco están definidos.
* **Rationale & Recommendation**: Describir `Env.read_env`, el diccionario final de `DATABASES` y el entorno mínimo de pytest (en `pyproject.toml` o `.env.test`).

### Campos, formularios, rutas y excepciones sin especificar - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L99, 139, 311-317, 324-326
* **Discrepancy Description**:
  * El formulario de tarea omite `kind`, `parent`, `description` y `assignee`.
  * No se dice qué campos de `Sprint` admiten nulos.
  * Faltan rutas de edición y borrado de épicas e hitos, y de reordenar el backlog.
  * "Cambiar rol o quitar" comparten URL sin campo discriminante.
  * No hay nombres de URL, variables de contexto ni excepciones de servicio (409, 422, 403) y `core/exceptions.py` no figura en la lista de archivos.
* **Rationale & Recommendation**: Añadir una tabla por formulario (campo, tipo, obligatorio, visible para quién), los `name` de URL y un `core/exceptions.py`.

### README: estado contradictorio en el plan - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-codebase-details`
* **Affected Scope:** L269, 287, 296
* **Discrepancy Description**: L269 declara el README como "ya actualizado", pero L287 lo marca como Modify en F5. El README real (L9 y L33) sigue con "Solo existe el prompt" y "Plan generado: pendiente". Además, L287 pide poner "plan redactado; sin código" en F5, cuando el código ya existirá. L296 marca `plan-prompt.md` como "hecho", lo cual sí coincide con su contenido.
* **Rationale & Recommendation**: Decir en L269 que solo `plan-prompt.md` está actualizado. Cambiar el estado de F5 a "MVP implementado" y mencionar el cambio de "Idioma del código" a inglés. Dejar el estado en un único lugar.

### Pasos E2E no se pueden aplicar "por fase" - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness`
* **Affected Scope:** L358-369
* **Discrepancy Description**: L359 da la fase por buena si todos los pasos pasan, pero los pasos 3-10 necesitan F3 o F4. F1 y F2 no pueden ejecutarlos.
* **Rationale & Recommendation**: Indicar qué pasos aplican a cada fase (por ejemplo F1: 1-2; F2: 3 y 10; F3: 4-7; F4: 8-9) o ejecutar el E2E completo solo al cerrar F4 y F5. Presentarlo como tabla Paso / Resultado esperado.

### `--cov-fail-under=80` en `addopts` - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** L294, 358
* **Discrepancy Description**: Hace fallar cualquier ejecución parcial de `pytest` y los criterios de F1, donde aún hay pocas pruebas. No hay settings de prueba, como un hasher rápido.
* **Rationale & Recommendation**: Mover el umbral a CI o a un comando `make`, o excluir `migrations/` y `tests/`.

### CSRF en pruebas requiere `enforce_csrf_checks=True` - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L277, 340
* **Discrepancy Description**: El cliente de pruebas de Django desactiva CSRF por defecto, así que la prueba "POST sin token devuelve 403" no funcionaría.
* **Rationale & Recommendation**: Indicar `Client(enforce_csrf_checks=True)` en `conftest.py`.

### `test_migrations.py` y grafo de migraciones sin declarar - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L277-278, 314, 342
* **Discrepancy Description**: `migrate ... zero` en MySQL no es transaccional (DDL con commit implícito). La prueba requiere `django_db(transaction=True)` y debe dejar la base migrada. `migrate sprints zero` también desaplica `backlog`. `backlog.0001` depende de `projects.0001`, `board.0001` y `sprints.0001`, y la `0002` manual depende de la `0001` generada. Conviene fijar que `0001` lo genera `makemigrations`.
* **Rationale & Recommendation**: Escribir el grafo y el procedimiento de la prueba.

### `base.html` carga scripts de fases posteriores - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L321, 330, 334
* **Discrepancy Description**: En F1, `base.html` carga `board.js` y `gantt.js`, que no existen hasta F3 y F4.
* **Rationale & Recommendation**: Usar un `{% block scripts %}` por página.

### Plan B del Gantt, `effective_dates` y contrato `undated` - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** L151, 186, 263, 331
* **Discrepancy Description**: El plan B no tiene lista de archivos ni función de cálculo de barras. Falta la forma de los elementos `undated` y `milestones`. `effective_dates(task, sprint, today)` recibe `today` sin que su descripción lo use. La prueba de concepto y el plan B se repiten en L186, 263, 280 y 331.
* **Rationale & Recommendation**: Completar el contrato y dejar la descripción de la prueba de concepto en un solo lugar.

### Contradicciones y omisiones menores del diseño - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** L87, 91, 96, 114, 157, 307
* **Discrepancy Description**:
  * "Cada app tiene models, services, forms..." no se cumple en `gantt` ni `core`.
  * `admin.py` no figura en la lista, aunque `/admin/` está activo.
  * La política de borrado omite `Sprint`, `Task` y `TaskDependency`, y `Task.column` es PROTECT, por lo que borrar un proyecto desde el admin fallaría.
  * Faltan `created_by` y `updated_by`.
  * `CheckConstraint` debe usar `condition=` en Django 5.1+.
  * Con fechas de fin inclusivas, el conflicto de dependencias deja pasar a un sucesor que empieza el día en que termina el predecesor.
  * `gunicorn` con varios procesos matiza G6 ("un solo proceso").
  * El orden de las tarjetas del tablero no está definido.
  * Las peticiones HTMX sin sesión necesitan `HX-Redirect`.
  * Falta `Vary: HX-Request`.
  * `.gitignore` debe añadir `.coverage`, `.pytest_cache/`, `.ruff_cache/` y `htmlcov/`.
  * Credenciales duplicadas en `DATABASE_URL` y `MYSQL_*`.
  * Con zona horaria distinta de UTC, `__date` en MySQL necesita tablas de zonas horarias.
  * Con la regla 3, mover dentro de la misma columna no persiste el orden manual, y el contrato dice que la posición se recalcula.
* **Rationale & Recommendation**: Resolver cada punto en el plan o declararlo fuera de alcance.

### Estilo: redacción de la tabla de fases y de los ítems largos - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** L269, 271, 277-279, 280, 287, 301, 312, 331, 332, 336, 342, 347
* **Discrepancy Description**:
  * L269: "No se incluye código" no es exacto, porque hay SQL y configuración literal.
  * L269 y L283-285 repiten la definición de monorepo de L13.
  * L271 y L332: "versión fijada en un comentario de `VERSIONS.md`" es impreciso. Mejor "registrada en".
  * L271: "se fijan al instalar" no dice quién ni cómo.
  * L277-279: celdas largas con cuatro criterios; usar listas.
  * L279 y L342: "plaza", "bajan a cero y suben otra vez" y "conexiones reales" son coloquiales.
  * L287 y L301: párrafos con siete a doce elementos; usar viñetas.
  * L336: "vaciado de Django" es impreciso; nombrar `TransactionTestCase` o `transaction=True`.
  * Fuera de rango, L175: "sí se prueba" debería ser "se probará".
* **Rationale & Recommendation**: Reescribir con listas y términos precisos.

## Verificado sin hallazgos

* Django 5.2 LTS con `mysqlclient`.
* `django-environ` con `mysql://`.
* `CHECK` en MySQL 8.0.16 o superior.
* Índice único sobre columna virtual InnoDB.
* `htmx:beforeSwap` con 409 y 422 en HTMX 2.
* `hx-headers` con CSRF en `<body>`.
* SortableJS 1.15.x con `Sortable.min.js`.
* `django_db(transaction=True)`.
* `AUTH_USER_MODEL` con la etiqueta `accounts`.
