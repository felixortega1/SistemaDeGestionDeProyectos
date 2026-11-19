# Goldfish Review Report

**Target:** `docs/designs/plan-implementacion.md` (`L310-466`, Detailed Implementation Plan; el resto se leyó como contexto)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-implementation-readiness` | completed |
| `egm-codebase-details` | completed |
| `egm-style` | completed |

Resumen: 0 Blockers, 18 Major, 28 Nit. Veredicto: un implementador todavía tendría que tomar decisiones de diseño (firmas, contrato de errores del tablero, datos de `board.js` y `gantt.js`, E2E). Ninguna es un bloqueo estructural. Las dependencias de migración no tienen ciclos, y las que declara el plan son correctas.

## Prioritized Findings (Blockers -> Major -> Nits)

No hay Blockers.

---

## Major

### Respaldo `RunSQL` de `sprints` desincroniza el estado de migraciones - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-implementation-readiness`
* **Affected Scope:** `L388`, `L417`, `L430`
* **Discrepancy Description**: Si se usa `0002_active_project.py` con `RunSQL`, el modelo sigue declarando el `GeneratedField` y el `UniqueConstraint`, pero el estado de migraciones no. `makemigrations --check` y `test_migrations` fallarían, y un `makemigrations` posterior intentaría un `AddField` de una columna que ya existe. "DDL esperado" no tiene criterio comprobable, y "prohibiendo después migrar `status` y `project` sin revisar ese SQL" no es verificable.
* **Rationale & Recommendation**: Usar `SeparateDatabaseAndState(state_operations=[AddField, AddConstraint], database_operations=[RunSQL(..., reverse_sql=...)])`. Dar el DDL esperado como criterio de aceptación, por ejemplo con una prueba que compare `SHOW CREATE TABLE`. Mejor aún, elegir una opción y eliminar la bifurcación. Declarar este `RunSQL` literal como excepción a "no incluye código de implementación" (L312). Corregir también "Todas las migraciones las genera `makemigrations`" (L381).

### `board.js` deja el DOM inconsistente ante respuestas distintas de 409 y 422 - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** `L404`, `L384`, contrato en `L168`
* **Discrepancy Description**: HTMX 2 no hace swap de 4xx/5xx por defecto, y el plan lo habilita solo para 409 y 422. `ServiceExceptionMiddleware` devuelve fragmento también para `Forbidden` (403) y `NotFound` (404). SortableJS ya movió la tarjeta antes de la petición. Con 403, 404, 5xx, error de red o sesión caducada, la tarjeta queda en la columna nueva aunque el servidor la rechazó. Esto contradice "la tarjeta vuelve a su columna".
* **Rationale & Recommendation**: En `htmx:beforeSwap`, incluir 403 y 404 o no devolver fragmento para ellos. Para `htmx:responseError`, `htmx:sendError` y `htmx:timeout`, repetir `GET .../board/` o revertir con Sortable. Con 409/422 fijar `evt.detail.shouldSwap = true` y `isError = false`. El 401 con `HX-Redirect` sí funciona.

### Excepciones, middleware y contrato de `move` incompatibles - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `L384`, `L168`, `L127`
* **Discrepancy Description**: El middleware genérico debe devolver "la página con un mensaje o el fragmento", pero `move` exige `board/_board.html` completo (con contexto del tablero) en 409 y 422, y redirección con mensajes sin HTMX. `Conflict` y `Unprocessable` no tienen atributos definidos, y los mensajes con "límite y conteo" o "columnas permitidas" necesitan datos estructurados. No hay plantilla de error en la lista de archivos.
* **Rationale & Recommendation**: Definir `ServiceError(Exception)` con `message` y `status`. Hacer que `board.views.move` capture las excepciones y renderice `_board.html`, y limitar el middleware al resto de las vistas. Añadir `templates/error.html`, `404.html` y `403.html` con su fase.

### Faltan firmas pese a la promesa "El plan incluye firmas" - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-style`
* **Affected Scope:** `L312`, `L384-L391`
* **Discrepancy Description**: Solo tienen firma `move_task`, `apply_placement`, `transfer_product_owner`, `create_column`, `effective_dates`, `build_gantt` y `project_role_required`. Faltan `create_project`, miembros, `create_sprint`, `update_sprint`, `start_sprint`, `assign_sprint`, `close_sprint`, `add_dependency`, `get_board` (estructura de retorno), `set_transitions`, `update_column` y el servicio de `budget`. No se dice dónde se comprueba el permiso por objeto ni qué devuelven los servicios.
* **Rationale & Recommendation**: Añadir una tabla "servicio, parámetros, retorno, excepciones, dónde se comprueba el permiso". Ejemplos: `close_sprint(sprint, review_notes, retro_notes, user)` y `get_board(project)` con sprint activo o `None` y columnas con conteo, límite, tareas y destinos permitidos. Si no, rebajar L312 a "firmas de los servicios principales".

### `assign_sprint` sobre una tarea que ya tiene sprint no está definido - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `L389`, `L420`, regla 10 (`L149`)
* **Discrepancy Description**: Solo se define el caso de una tarea sin sprint. No hay endpoint para desasignar y una tarea con sprint no se borra (409), así que una asignación errónea a un sprint `planned` queda atrapada.
* **Rationale & Recommendation**: Decidir: rechazar con 422 si `task.sprint` no es nulo, o admitir `sprint_id` vacío para volver al backlog desde `planned`. Añadir el caso a `test_backlog`.

### Contrato de `effective_dates` y definición de `conflict` incompletos - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-style`
* **Affected Scope:** `L390`, `L352`, `L425`, regla 5 (`L129`)
* **Discrepancy Description**: No se define el tipo de retorno de `effective_dates` (dataclass, tupla o excepción), y `test_gantt_dates` lo prueba directamente. El parámetro `today` no se usa para fechas efectivas, solo para el retraso. La excepción "ambas heredan del mismo sprint" no cubre el caso mixto (inicio propio y fin heredado). El criterio de F4 (L352) omite esa excepción y la prueba tampoco la cubre.
* **Rationale & Recommendation**: Definir `EffectiveDates(start, end, start_source, end_source)` y `Undated(reason)`, y quitar `today` si no se usa. Formular `conflict` con fuentes y `sprint_id` explícitos. Añadir la excepción a L352 y un caso a `test_gantt_dates`.

### `frappe-gantt`: versión sin fijar y mapeo de campos sin definir - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details` (Nit N3)
* **Affected Scope:** `L316`, `L405`, `L406`, `L170`
* **Discrepancy Description**: La versión se difiere a antes de cerrar F4, y los archivos, el modo solo lectura y el formato de `dependencies` cambian entre 0.6.x y 1.x. La librería espera `{id, name, start, end, progress, dependencies, custom_class}` y el contrato del plan usa `title` y `depends_on`. En 0.6.x `custom_class` admite una sola clase, y no hay modo solo lectura. Con un arreglo vacío la librería falla. Los ids de hitos pueden chocar con los de tareas.
* **Rationale & Recommendation**: Fijar ahora versión y archivos CSS/JS. Definir el mapeo (`title→name`, `depends_on→dependencies` como cadena, `progress=0`, ids como cadena `t<id>` y `m<id>`). No instanciar sin tareas con fechas. Dejar la prueba de concepto solo para la decisión entre `frappe-gantt` y el plan B.

### Datos que `board.js` y la plantilla necesitan no están definidos - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details` (N4), `egm-style` (22)
* **Affected Scope:** `L400`, `L404`, `L169`
* **Discrepancy Description**: `data-move-url` va en `#board`, pero la URL lleva el id de tarea. No se dice si `data-allowed` va en la columna o en la tarjeta, ni su formato. El selector sin JavaScript necesita un botón de envío. Sortable necesita `group` compartido y `sort: false` (el orden es por `id`). `htmx:load` con `outerHTML` no encuentra `#board` si se busca dentro de `evt.target`.
* **Rationale & Recommendation**: Especificar `data-task-id` y `data-allowed="2,3"` en la tarjeta, la plantilla de URL, el botón del selector, `group` y `sort: false`. Hacer que `initBoard()` consulte `document`.

### `test_imports` solo cubre `services.py` y no define el mapa de capas - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `L414`, `L77`, `L381`
* **Discrepancy Description**: La regla "los modelos usan cadenas" no tiene prueba, y `board/models.py` podría importar `projects.models`. No se define cómo se mapea un import a una capa (`apps.projects` o `projects`, imports dentro de funciones, imports de la misma app).
* **Rationale & Recommendation**: Poner el orden de capas como constante literal en el test, incluir `models.py` (solo `django.*`, `settings` y la propia app) y fijar el patrón `apps.<app>`. Aclarar en L381 que las capas solo gobiernan los imports. Las FK por cadena y las dependencias de migración (incluida `board.0001` dependiendo de `projects.0001`) las genera `makemigrations` sin edición manual.

### `INSTALLED_APPS`, `apps.py` y `settings.py` incompletos - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details` (N6)
* **Affected Scope:** `L11/L375`, `L314`, `L386`, `L381`
* **Discrepancy Description**: El ítem 11 pide en F1 las apps de `apps/`, pero L314 dice que cada fase añade la suya, y L386 solo tiene sentido con `INSTALLED_APPS` incremental. No se fija el formato (`apps.<app>`), ni si `apps.py` se omite a propósito (el label debe ser el último segmento para `get_model` y las migraciones). Faltan `django.contrib.sessions`, `messages`, `auth`, `contenttypes`, `staticfiles` y `admin`, `STATIC_URL`, `ROOT_URLCONF`, `WSGI_APPLICATION` y el orden del middleware (WhiteNoise tras `SecurityMiddleware`). `sql_mode='STRICT_TRANS_TABLES'` sustituye el `sql_mode` por defecto de MySQL 8.4 sin justificación.
* **Rationale & Recommendation**: Fijar formato y label, listar los contrib apps y el orden del middleware, dar los defaults de `DEBUG` y `ALLOWED_HOSTS`, y justificar o ampliar `sql_mode`.

### Ítem 15 se contradice sobre los resolvedores de permisos - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `L384`
* **Discrepancy Description**: Lista en F1 todos los resolvedores y dice a la vez que en F1 solo existe el de proyecto. No se define el tipo de `roles`, que `product_owner` satisface `scrum_master`, ni si `can_edit_task` y `can_move_task` devuelven `bool` o lanzan excepción.
* **Rationale & Recommendation**: Tabla "resolvedor, fase", `roles` como `frozenset` de strings, herencia del Product Owner explícita y `can_*` devolviendo `bool`.

### Fases y archivos que cambian pero no están mapeados - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `L314`, `L322-L326`, `L158`, `L387`
* **Discrepancy Description**: La regla "cada fase que añade una app modifica…" no cubre F3, que no añade app pero modifica `config/urls.py`, `permissions.py` y la navegación. `projects/views.py` cambia su redirección en F3 (L158) y no figura en F3, así que el test de F1 "redirige a la lista" fallaría sin aviso. Los `forms.py`, `views.py` y `urls.py` de `board` y `backlog` y la navegación no tienen fase explícita.
* **Rationale & Recommendation**: Añadir una sección "Modificaciones por fase" que incluya el cambio de la redirección y de su prueba en F3.

### E2E paso 8 no ejecutable - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-style`
* **Affected Scope:** `L445` (tabla `L436-L449`)
* **Discrepancy Description**: "Repetir el paso 5" exige 3 tareas en "Por hacer", pero tras los pasos 5 a 7 "En desarrollo" está en 3 / 3 y quedan 2 tareas en "Por hacer". El resultado sería 409, no "Mismo resultado".
* **Rationale & Recommendation**: Crear 3 tareas más o un sprint nuevo, o mover el paso 8 antes del 5, o usar un movimiento a "En revisión". Indicar de qué tareas parte cada paso.

### E2E paso 12 (cierre, F3) va después de los pasos de F4 - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** `L447-L449`
* **Discrepancy Description**: Quien cierra F3 ejecuta el paso 12 y destruye el sprint activo que F4 necesita para los pasos 10 y 11.
* **Rationale & Recommendation**: Mover el cierre antes del Gantt, o dejarlo como paso final de F4/F5, o dividirlo en "cierre en F3" y "recorrido completo al cerrar F5".

### E2E: faltan datos de preparación y cobertura - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-style`
* **Affected Scope:** `L440`, `L447`, `L434`, `L194`
* **Discrepancy Description**: El paso 10 espera "las retrasadas con su marca", pero el paso 3 no fija fechas y con fechas futuras no hay retrasadas. No hay pasos para lo que L194 dice que solo se verifica a mano: clase CSS de conflicto, dependencias, hitos, lista `undated` y editor de columnas y transiciones. No hay paso de F5 (presupuesto), aunque el recorrido se repite al cerrar F5.
* **Rationale & Recommendation**: Fijar un `end_date` pasado en el paso 3 y añadir pasos para dependencia con conflicto el mismo día, hito, tarea sin fechas, editor de columnas y presupuesto.

### Afirmación sobre `/admin/` y sesiones es falsa (fuera del rango) - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-style`
* **Affected Scope:** `L189` (relacionado con `L379-L391`)
* **Discrepancy Description**: `django.contrib.sessions` no registra `Session` en el admin, y ningún ítem incluye un `admin.py`.
* **Rationale & Recommendation**: Registrar `Session` en un `admin.py` (por ejemplo en `accounts`) y añadirlo a la lista de archivos, o documentar `manage.py clearsessions` o SQL directo.

### Ítem 45 (`test_board_wip`) ambiguo y de una sola oración - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness` (Nit)
* **Affected Scope:** `L422`
* **Discrepancy Description**: Una oración de unas 170 palabras. "Lo mismo con `move_task` y `close_sprint`" es ambiguo, porque `close_sprint` no ocupa plaza WIP. "422" y "transición" se presentan como etiquetas distintas aunque ambas dan 422. Los hilos no dicen si usan el `Client` o el servicio, y "el invariante se mantiene" no tiene aserciones.
* **Rationale & Recommendation**: Lista con una prueba por viñeta, con resultado esperado y aserciones concretas (cuántas tareas quedan con sprint y columna).

### Licencia "(MIT)" aplicada a los tres paquetes JS - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-codebase-details` (N2)
* **Affected Scope:** `L406`, `L51`
* **Discrepancy Description**: HTMX 2.x se distribuye bajo 0BSD (no verificado por el reviewer de estilo, afirmado por el técnico). SortableJS y frappe-gantt son MIT. "Paquetes oficiales" es vago.
* **Rationale & Recommendation**: Quitar "(MIT)" de la frase colectiva y registrar licencia y URL de descarga por librería en `VERSIONS.md`.

### Descripciones y densidad de ítems con contenido contradictorio o excesivo - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** `L375`, `L384`, `L387`, `L388`, `L389`, `L405`, `L420`
* **Discrepancy Description**: Cada ítem es un párrafo con 10 a 15 elementos separados por punto y coma o paréntesis anidados. En L387 la invariante "hay una sola columna `is_done` y es la última" está escondida. L389 dice "CRUD de épicas, tareas e hitos" y luego "solo se crean y se listan", mientras que las rutas (L159) sí editan y borran tareas.
* **Rationale & Recommendation**: Listas de 3 a 6 viñetas por ítem. Reescribir L389 como "crear y listar épicas e hitos; crear, editar y borrar tareas".

---

## Nit

### Versiones de librerías y herramientas
* **`egm-style`, `L316`**: repite el `CHECK >= 8.0.16` de L102. "8.0 ya terminó su soporte" no lleva fecha o fuente.
* **`egm-implementation-readiness`, `L369`**: Ruff sin reglas, aunque `ruff check` es una puerta de verificación (L432). Fijar `select`, `line-length` y `exclude`.
* **`egm-codebase-details` N9, `L369`**: `Env.read_env` no sobrescribe variables ya definidas, así que las de pytest-env ganan. Documentar que CI debe definir `MYSQL_*`. Con `DEBUG=true` las cookies `Secure` no se prueban (se evalúan al importar). argon2 ralentiza las fixtures, y se puede sobrescribir `PASSWORD_HASHERS` en `conftest.py`.

### Configuración y entorno
* **`egm-codebase-details` N1, `L366`**: los backticks de `` `test\_%`.* `` dentro de comillas dobles en shell son sustitución de comandos. Usar comillas simples o heredoc.
* **`egm-style`, `L363`**: "Se crea también `.gitattributes`" repite el "(Create)". "Datos locales de MySQL" es vago, y falta la ruta o el volumen.
* **`egm-style`, `L364`**: `MYSQL_HOST` y `MYSQL_PORT` no los usa Docker. Distinguir las variables de Docker de las de conexión.
* **`egm-implementation-readiness`, `L364`, `L375`**: sin defaults literales de `DEBUG` y `ALLOWED_HOSTS`. `CSRF_TRUSTED_ORIGINS` y `SECURE_PROXY_SSL_HEADER` están en Supuestos (L181) pero no en `settings.py` ni en `.env.example`.

### Modelos y migraciones
* **`egm-codebase-details` N7, `L106`/`L385`**: el admin y `createsuperuser` requieren `PermissionsMixin` y `last_login`. Declarar `AbstractBaseUser + PermissionsMixin` y `REQUIRED_FIELDS = ["name"]`.
* **`egm-codebase-details` N8, `L381`/`L417`**: citar `swappable_dependency(AUTH_USER_MODEL)` (`Task.assignee`, `Department.updated_by`, `Project.created_by`). En `test_migrations`, usar `try/finally` para volver a migrar, y `call_command(..., check=True, dry_run=True)`.
* **`egm-codebase-details` N5, `L388`/`L176`**: capturar el `IntegrityError` fuera del `atomic` (o con savepoint) antes de lanzar `Conflict`. `L421` obliga a definirlo y a explicar cómo se fuerza el rechazo del índice (por ejemplo con `update(status="active")` directo).
* **`egm-codebase-details` N10, `L127` (fuera del rango)**: la ausencia de deadlocks vale solo entre las cuatro operaciones con bloqueo. `edit_task`, `delete`, `update_column` y la creación de tareas no lo toman y pueden entrar en deadlock (error 1213). Matizar o mapear 1213 a reintento o 409.
* **`egm-implementation-readiness`, `L386`/`L387`/`L389`/`L416`**: definiciones abiertas. Si cuentan las tareas del backlog con `column` nulo al quitar un miembro, si `set_transitions` admite `from == to`, unicidad de `BoardColumn.name` por proyecto, y qué pasa con fechas o `parent` en una historia y con cambiar `kind` con hijos.
* **`egm-implementation-readiness`, `L389`**: los índices `Task(sprint, column)` y `Task(project, sprint, column)` se solapan. Dejar uno o indicar qué consulta usa cada uno.

### Criterios y pruebas
* **`egm-implementation-readiness`, `L344-L348`**: faltan criterios de F3 para el editor de columnas, `create_column` y los permisos del Developer, aunque sus pruebas existen (L423-L424).
* **`egm-style`, `L343`**: "Las pruebas de cierre preparan las tareas asignando directamente una columna `is_done`" no es un criterio de aceptación y contradice la regla 10. Pasarlo a `test_sprints` (L421) y precisar "mediante `apply_placement`".
* **`egm-implementation-readiness`, `L439`**: el paso 2 remite a `test_projects`, que no es un paso que el implementador ejecute. Indicar la verificación en pantalla o marcarlo informativo.
* **`egm-style`, `L320-L326` vs `L433`**: "cobertura mínima" frente a "umbral de partida". Unificar el término y poner el 80 % en la tabla.

### Redacción y terminología
* **`egm-style`, `L312`**: "El proyecto no tiene código" repite L13. Quitar "ya" en "ya apunta" y "ya actualizado". "Probable" debería ser "verificable". L312 dice que en F5 "solo" se añaden instrucciones, pero L362 también cambia "Estado" a "MVP implementado".
* **`egm-style`, `L381`**: "Regla de Componentes" choca con las reglas numeradas, así que usar "sección Componentes". "Sus dependencias son…" no tiene antecedente claro.
* **`egm-style`, `L384`/`L390`**: la función que decide entre fragmento y redirección no tiene nombre. En `build_gantt`, "solo se leen tareas" es impreciso, porque también se leen sprints, hitos y dependencias.
* **`egm-style`, `L388`**: reformular "prohibiendo después migrar…" como regla. `start_sprint (estado planned y las dos fechas…)` debería decir que son precondiciones.
* **`egm-style`, `L405`/`L325`/`L205`**: la prueba de concepto se describe tres veces. Dejarla en L405. "Pasa a la librería solo las tareas con fechas" repite el contrato de L170.
* **`egm-style`, terminología**: "abrir", "iniciar" y `start` nombran la misma acción del sprint (L140, regla 8, L338, paso 3), y "abrir el tablero" usa otro sentido. Fijar "iniciar" en Términos. "Última plaza libre" (L347, L422) es coloquial.
* **`egm-style`, `L22` del README**: usa "fase 2", que colisiona con F2. El plan usa "versión posterior".
* **`egm-style`, idioma de etiquetas**: hay etiquetas en inglés ("Detailed Implementation Plan", "Create/Modify", "Compilation/Build"). Si el esquema lo exige, conservar los encabezados y traducir las etiquetas en negrita.
* **`egm-style`, `L453-L462`**: "(versión posterior)" aparece 8 veces. Usar un solo encabezado. L460 menciona SSE o WebSockets, mientras que L40 solo WebSockets.

## Verificado y correcto
* `GeneratedField(expression=, output_field=, db_persist=False)` con `UniqueConstraint` sobre columna virtual en MySQL 8.4 funciona, y MySQL admite varios NULL en un índice único. `CheckConstraint(condition=)` es la sintaxis vigente en 5.2.
* `OPTIONS` con `isolation_level: "read committed"` y `charset: utf8mb4` son válidas para mysqlclient. Django 5.2 con MySQL 8.4 y Python 3.12 es compatible.
* `htmx.ajax(verb, path, {target, swap, values})`, `htmx:beforeSwap` y `htmx:load` existen en HTMX 2. El 401 con `HX-Redirect` se procesa antes del estado.
* `pytest-env` con `env = [...]`, `Client(enforce_csrf_checks=True)` y `@pytest.mark.django_db(transaction=True)` con hilos que cierran conexión son correctos.
* Las dependencias de migración declaradas (`accounts` ← `projects` ← `board`/`sprints` ← `backlog`; `budget` ← `projects`) no tienen ciclos. Que `board` dependa de `projects` por FK no viola la regla de capas, que solo restringe los imports de `services.py`.
* README y `plan-prompt.md` ya apuntan al plan y al stack Django, como afirma L312.
