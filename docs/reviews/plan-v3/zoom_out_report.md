# Goldfish Review Report

**Target:** `docs/designs/plan-implementacion.md` (`1-451`; FeatureRange 1-296, DetailedRange 297-451)

**Estándar:** `zoom-out-standard.md`. Contexto: `README.md` y `docs/plan-prompt.md`. No se reabrieron las decisiones ya tomadas por el autor.

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-zoom-out` | completed |
| `egm-inventive-catalyst` | completed |

Resumen: 0 Blockers, 10 Major, 16 Nit (deduplicados). El contexto es suficiente y el plan es ejecutable en lo esencial. Los hallazgos son contradicciones internas y huecos de reglas.

## Prioritized Findings (Blockers -> Major -> Nits)

### Capas violadas por el propio plan, y la prueba no lo detecta - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L65, L281, L367, L372, L400
* **Discrepancy Description**: Un `services.py` solo importa de capas inferiores, y `projects` está por debajo de `board`. Pero `projects.services.create_project` llama a `board.services.create_default_board`. `test_imports` solo detecta `ImportError` por ciclos y no el orden de capas, aunque L281 afirma que "una prueba lo verifica".
* **Rationale & Recommendation**: Subir `board` por debajo de `projects` (sus FK ya son cadenas), o mover la orquestación a una capa superior, o declarar una excepción con importación diferida. Sustituir o ampliar la prueba con un recorrido del AST de imports que falle ante una app que importe de una capa superior.

### `create_column` e `is_done` se contradicen - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L50, L100, L169, L373
* **Discrepancy Description**: `create_column` añade al final y siembra transiciones con la antigua última columna ("Hecho"). La misma línea exige una sola columna `is_done` y que sea la última, así que tras crear una columna "Hecho" deja de ser la última. L50 dice que solo se edita nombre, WIP y texto, pero `update_column` también edita `is_done`. L169 menciona la edición concurrente de `position`, pero no existe operación de reordenar.
* **Rationale & Recommendation**: Dejar `is_done` inmutable, fijado en el sembrado. Insertar las columnas nuevas antes de la columna `is_done`, con transiciones bidireccionales hacia sus dos vecinas. Quitar `is_done` de `update_column` y el supuesto de `position` de L169.

### El recorrido E2E no es ejecutable por fases - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L299, L422-434
* **Discrepancy Description**: El paso 2 (F1) verifica las 4 columnas en la página de columnas, que es de F3. El paso 11 (F2) va al final y espera que las terminadas conserven el sprint, pero antes de F3 no existe `move_task` y ningún paso lleva una tarea a "Hecho" (hay que pasar por "En revisión"). Contradice "cada fase deja el sistema ejecutable y probable".
* **Rationale & Recommendation**: Reordenar la tabla por fase. Verificar las columnas de F1 por otro medio (lista de proyectos o admin). Mover el cierre de sprint a F3 o después, e incluir el paso de mover una tarea hasta "Hecho" y comprobar su estado tras el cierre.

### Criterio F4 no verificable con pytest - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** L181, L337-338
* **Discrepancy Description**: El criterio exige la clase `is_late` en el HTML de la página. El servidor solo emite JSON con `json_script`. La clase la agrega `gantt.js`, que según L181 no tiene pruebas automáticas. Lo mismo ocurre con `conflict`.
* **Rationale & Recommendation**: Redactar el criterio contra el JSON (`is_late: true`, `conflict: true`, `undated`). Dejar la clase visual para el E2E manual.

### `assign_sprint`: salto de la política, WIP en la fase equivocada y sin vía de salida - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`, `egm-zoom-out`
* **Affected Scope:** L109, L127, L134, L136, L140, L310-311, L375
* **Discrepancy Description**:
  * `assign_sprint` no exige que la tarea no tenga sprint. Sobre una tarea ya en "En desarrollo" o "Hecho" la devuelve a la primera columna sin pasar por `ColumnTransition`, e incluso reabre una terminada de un sprint cerrado.
  * Dice que aplica el WIP si el sprint está activo, pero ese código es `move_task`, que es F3.
  * No hay operación para sacar una tarea de un sprint `planned`, y ese sprint no se puede cerrar ni borrar. Una tarea que estuvo en un sprint no se puede borrar (409), ni siquiera las terminadas.
* **Rationale & Recommendation**: Limitar `assign_sprint` a tareas con `sprint IS NULL` y definir `assign_sprint(task, None)` para desasignar mientras el sprint esté `planned`. Poner el WIP dentro de `apply_placement`, el único escritor, para tenerlo desde F2. Declarar como límite conocido que lo ya ejecutado en un sprint no se borra.

### Concurrencia: bloqueo parcial en `move_task` - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L115, L134, L136
* **Discrepancy Description**: `move_task` valida permiso, transición y columna actual con una lectura previa fuera de `atomic()`. Solo bloquea la columna destino. Dos movimientos de la misma tarea pueden pasar con una columna actual vencida, y `close_sprint` y `start_sprint` no bloquean nada. La regla "sin haber leído antes tareas dentro de la transacción" es frágil y depende de InnoDB y `READ COMMITTED`.
* **Rationale & Recommendation**: Valorar un único bloqueo por proyecto (`Project.select_for_update()`) como primera sentencia en todo escritor de `column` o `sprint`, releyendo y validando dentro de la transacción. Eliminaría el reintento de deadlock. Costo: se serializan los movimientos del mismo proyecto, algo despreciable a la escala supuesta (L167). Alternativa mínima: releer la tarea con `select_for_update()` dentro de `atomic()`.

### Reglas de permisos incompletas para el Developer - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L102, L125, L128, L133, L136, L145
* **Discrepancy Description**: El Developer edita "solo sus tareas", pero una tarea nueva no tiene responsable. No queda claro si puede crear tareas ni cómo toma una. Puede moverla (sin responsable) pero no tomarla. Un Developer que edita su tarea podría reasignarla. La ruta `members/<user_id>/role/` podría fijar `product_owner` en vez de usar `transfer-po`.
* **Rationale & Recommendation**: Definir si el Developer crea tareas. Añadir una acción "tomar tarea" (solo si `assignee` es nulo) y reservar el resto de la edición de `assignee` al PO y SM. Prohibir `product_owner` en el endpoint de rol.

### Quitar un miembro puede bloquearse para siempre - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L96, L102, L109
* **Discrepancy Description**: Quitar un miembro con tareas asignadas da 409 y las tareas terminadas de sprints cerrados conservan el `assignee`. Un miembro que terminó una sola tarea no se puede quitar nunca.
* **Rationale & Recommendation**: Quitar el miembro con desactivación lógica (`ProjectMember.is_active`), o rechazar solo si tiene tareas en un sprint activo o sin terminar. Otra opción es que `Task.assignee` apunte a `ProjectMember` para eliminar la validación "responsable es miembro".

### `SprintTask` no basta para burndown ni métricas de flujo - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L38, L105, L292, L442
* **Discrepancy Description**: `SprintTask` guarda solo el estado final. No sirve para burndown (falta cuándo se terminó cada tarea) ni para lead o cycle time. L292 y L442 prometen lo contrario.
* **Rationale & Recommendation**: Reducir la promesa a "velocidad" en L292 y L442, o añadir un registro mínimo `TaskMove(task, from_column, to_column, at)` escrito por `apply_placement`. Esto no contradice el Non-Goal de auditoría de ediciones.

### Datos de `Sprint` y rutas ambiguas - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** L99, L134, L146-147
* **Discrepancy Description**: `start` exige `start_date` y `end_date`, pero la tabla no dice que sean nulables. No se define si se editan con el sprint `active` o `closed`. En `dependencies/<dep_id>/delete/` no está claro si `dep_id` es el id de `TaskDependency` o el de `depends_on`.
* **Rationale & Recommendation**: Resolver cada punto en el modelo de datos o en las rutas antes de implementar.

### `is_late` con `column` nulo y página de sprints cerrados - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L114, L116, L118, L385
* **Discrepancy Description**: Una tarea sin sprint, sin columna y con fecha propia vencida queda marcada `is_late` porque "su columna no es `is_done`". Además, las tareas sin terminar de un sprint cerrado ya no tienen sprint, así que la página de sprints solo mostraría las terminadas.
* **Rationale & Recommendation**: No marcar retraso si `column` es nulo, o decirlo explícitamente. Que la página lea `SprintTask` para sprints cerrados.

### Detalle de bajo nivel en secciones de alto nivel - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L115, L163, L374, L390, L408
* **Discrepancy Description**: Error 1213 y reintento, `ALTER TABLE` con `RunSQL`, `htmx.ajax(...)` y `threading.Barrier`.
* **Rationale & Recommendation**: Dejar una frase y mover el resto a notas de implementación. El punto del error 1213 desaparece si se aplica el bloqueo por proyecto.

### Configuración sin efecto (YAGNI) - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L90, L163, L375
* **Discrepancy Description**: `CASCADE` describe un borrado de proyectos que el MVP no ofrece (el admin sí lo permite, y esquiva los servicios). Los índices `Task(sprint, column)` y `Task(project, sprint, column)` son casi redundantes a 2.000 tareas por proyecto.
* **Rationale & Recommendation**: `PROTECT` en todo, registrar en `/admin/` solo lo necesario (por ejemplo `User`) y dejar un solo índice.

### `test_imports` mal especificado - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L400
* **Discrepancy Description**: Un subproceso que importa `services` sin `DJANGO_SETTINGS_MODULE` ni `django.setup()` falla con `AppRegistryNotReady`, no por ciclos.
* **Rationale & Recommendation**: Fijar el entorno y llamar a `django.setup()` antes de importar.

### Texto desactualizado sobre MySQL 8.0 - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L303
* **Discrepancy Description**: "lo que hay que confirmar al implementar" cubre un dato ya decidido, y el documento es de noviembre de 2026.
* **Rationale & Recommendation**: Dejar solo "se fija 8.4 LTS".

### Open Question sin consumidor - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L59, L305-313
* **Discrepancy Description**: Equipo y plazo "dimensionan las fases", pero las fases solo se ordenan por dependencia.
* **Rationale & Recommendation**: Quitar la pregunta o añadir una estimación relativa por fase.

### Alcance frente a `plan-prompt.md` - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** L13, L21
* **Discrepancy Description**: El plan excluye el comparativo, MoSCoW y las métricas de éxito, pero `plan-prompt.md` los sigue pidiendo.
* **Rationale & Recommendation**: Ajustar el prompt o marcarlo como histórico para evitar ambigüedad.

### Matriz de permisos y rutas desalineadas - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L50, L52, L125, L146-147
* **Discrepancy Description**: La matriz permite "editar" épicas e hitos, pero las rutas solo los crean. L50 dice "El Scrum Master puede editar las transiciones" y omite al PO.
* **Rationale & Recommendation**: Alinear el texto con "PO o SM" y con "solo se crean y se listan".

### Ambigüedades de modelo y presentación - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** L102, L107, L116, L157
* **Discrepancy Description**: `Task.epic` no aclara si aplica a historias, tareas o ambas. Los hitos se dibujan "en una fila aparte" y también "como barras de un día". El product backlog no tiene prioridad (se ordena por `id`) y el "incremento" del prompt no se menciona.
* **Rationale & Recommendation**: Aclarar cada punto y declarar el orden por `id` en Límites conocidos.

### Contrato de `move` incompleto para 403 y 404 - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L155, L390
* **Discrepancy Description**: `board.js` solo acepta 409 y 422. Un 403 o 404 con HTMX no se reemplaza y falla en silencio.
* **Rationale & Recommendation**: Aceptar también 403 y 404 o devolver un fragmento de error.

### Doble camino HTMX y no-JS por acción - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** L140
* **Discrepancy Description**: Solo `move` está marcada (H); no se dice que el resto de las vistas tiene solo camino normal.
* **Rationale & Recommendation**: Declararlo para no duplicar trabajo.

### Configuración de entorno y Docker - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L48, L350, L352
* **Discrepancy Description**: `DATABASE_URL` repite las credenciales de `MYSQL_*`. `01-grants.sh` falla en Windows si Git lo convierte a CRLF. Sin Docker, los permisos sobre `test_%` no están documentados.
* **Rationale & Recommendation**: Construir `DATABASES` desde `MYSQL_*`, añadir `.gitattributes` con `*.sh text eol=lf` y documentar los permisos para la instalación manual.

### `core.permissions` acoplado a todas las apps - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L119, L301
* **Discrepancy Description**: `core.permissions` conoce por nombre los modelos de todas las apps mediante `get_model`, y cada fase lo modifica.
* **Rationale & Recommendation**: Cada app podría aportar sus `from_*_id` y `can_*` en su propio `permissions.py`. Costo: las reglas quedan repartidas.

### Presupuesto en la última fase - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** L21, L313
* **Discrepancy Description**: El presupuesto es parte del diferencial pero se construye en F5. Solo depende de `projects`.
* **Rationale & Recommendation**: Hacerlo en paralelo a F4, que es la fase con riesgo (prueba de concepto de `frappe-gantt`).

### Demasiadas alternativas - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** L195-293
* **Discrepancy Description**: Son 16 alternativas, y M, N y P son decisiones menores presentadas como arquitectónicas.
* **Rationale & Recommendation**: Condensarlas.
