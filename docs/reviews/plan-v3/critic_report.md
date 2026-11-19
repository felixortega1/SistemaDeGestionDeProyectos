# Goldfish Review Report

**Target:** `docs/designs/plan-implementacion.md` (`líneas 1-296`)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-design` | completed |
| `egm-structural` | completed |
| `egm-style` | completed |

Las decisiones fijadas por el autor no se discuten; las críticas apuntan a huecos de ejecución dentro de ellas.

## Prioritized Findings (Blockers -> Major -> Nits)

### Carrera entre mover tarea y cerrar sprint / reasignar, sin bloqueo - Severity: Blocker
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L115, L134, L136, L102`
* **Discrepancy Description**: `move_task` valida los pasos 2 a 4 (sprint activo, columna actual, transición) antes de bloquear nada. Solo después bloquea la fila `BoardColumn` destino. Bajo READ COMMITTED esas lecturas pueden quedar obsoletas. Si `close_sprint` o `assign_sprint` deja la tarea con `sprint=NULL` y `column=NULL` entre la validación y el UPDATE, `move_task` escribe una columna sin sprint o en un sprint cerrado y rompe el invariante "sprint y column van juntos". Dos movimientos de la misma tarea también validan la transición contra la misma columna origen obsoleta y se saltan la política. `close_sprint` no declara ningún bloqueo. El invariante no tiene `CHECK` en la base de datos.
* **Rationale & Recommendation**: Fijar un orden de bloqueo único para `apply_placement` y sus llamadores (por ejemplo `Sprint`, luego `BoardColumn` destino, luego `Task`). Releer la tarea con `select_for_update()` dentro del `atomic` y validar los pasos 2 a 4 después de bloquear. Hacer que `close_sprint` bloquee el sprint y sus tareas antes de escribir `SprintTask`. Añadir `CheckConstraint((sprint IS NULL) = (column IS NULL))` y un `CheckConstraint` por `kind`. Añadir una prueba de concurrencia de mover contra cerrar.

### Conflictos de dependencia siempre verdaderos dentro de un mismo sprint - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L116-117, L47`
* **Discrepancy Description**: Dos tareas del mismo sprint sin fechas propias heredan fechas idénticas. Con la regla "inicio del sucesor <= fin del predecesor", toda dependencia dentro de un sprint se marca `conflict`. Es el caso más común en Scrum.
* **Rationale & Recommendation**: Documentar el caso: no marcar conflicto cuando ambas heredan del mismo sprint, o exigir fechas propias para evaluarlo. Hoy lo decidiría el implementador.

### La regla de capas se viola al sembrar el tablero por defecto - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L50, L65, L100` (y `projects.create_project` en L372)
* **Discrepancy Description**: `projects` está por debajo de `board`, y un `services.py` solo importa capas inferiores. Aun así `create_project` llama a `board.services.create_default_board`. La prueba de ciclos de import fallaría o el implementador improvisará. Tampoco se define cómo se asigna `position` al crear una columna ni la unicidad `(project, position)`, ni qué pasa con las transiciones contiguas de "Hecho".
* **Rationale & Recommendation**: Elegir y documentar una vía: orquestar desde la vista, mover `create_project` a una capa superior o usar una señal. Añadir `UniqueConstraint(project, position)` y la regla de inserción de columnas.

### Errores HTMX distintos de 409/422 sin manejo - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L140, L155`
* **Discrepancy Description**: HTMX no intercambia respuestas 4xx/5xx por defecto. `board.js` solo habilita 409 y 422. Un 403, 404, 500, fallo de CSRF o un 401 sin `HX-Redirect` no dan feedback y el tablero parece no responder. La versión de HTMX no está fijada y el mecanismo cambia entre 1.x y 2.x.
* **Rationale & Recommendation**: Fijar la versión, definir el manejo de cada código y ponerlo en una configuración global, no en `board.js`.

### SortableJS tras el reemplazo y sincronización de peticiones - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L155-156, L107, L115`
* **Discrepancy Description**: Cada respuesta reemplaza `_board.html` completo, por lo que las instancias de Sortable quedan ligadas a nodos destruidos si no se reinician. Dos arrastres seguidos pueden solaparse (falta `hx-sync`). Arrastrar dentro de la misma columna es un no-op sin orden manual.
* **Rationale & Recommendation**: Reinicializar en `htmx:afterSwap` o usar delegación, añadir `hx-sync` y deshabilitar el reordenamiento dentro de la misma columna.

### Product Owner único y ciclos concurrentes sin cerrar - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L96, L133, L169, L179, L191, L109`
* **Discrepancy Description**: Se aceptan dos PO y ciclos concurrentes como límite, aunque el plan ya usa `GeneratedField` + `UniqueConstraint` para el sprint activo (mismo patrón sirve para un PO único). Para los ciclos basta bloquear la fila `Project` al crear dependencias. La ruta `members/<user_id>/role/` no impide asignar `product_owner` a otro ni dejar el proyecto sin PO; solo `remove` devuelve 409.
* **Rationale & Recommendation**: Aplicar el mismo patrón para el PO único, bloquear `Project` en dependencias y validar los cambios de rol.

### `GeneratedField` sin `output_field` ni expresión especificados - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L54, L99`
* **Discrepancy Description**: "Igual a `project`" no fija la expresión ni `output_field`. Un `ForeignKey` como `output_field` genera una columna con FK que MySQL rechaza. Tampoco se fija `db_persist=False` ni hay una prueba que confirme el índice único sobre columna virtual.
* **Rationale & Recommendation**: Declarar `Case(When(status='active', then=F('project_id')))` con `output_field=BigIntegerField`, `db_persist=False` y una prueba de migración.

### `assign_sprint` con casos sin definir - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L102, L136, L134`
* **Discrepancy Description**: Una tarea ya en un sprint activo se reinicia a la primera columna y salta la política de transiciones. Una tarea terminada de un sprint cerrado conserva su sprint; `assign_sprint` solo comprueba que el destino no esté `closed`, así que podría reasignarse y desaparecer del Gantt del sprint cerrado. No se dice si bloquea la fila `BoardColumn` como `move_task`, ni qué ocurre si la primera columna tiene `wip_limit = 0`.
* **Rationale & Recommendation**: Definir precondiciones (tarea sin sprint), el bloqueo y el comportamiento con WIP 0.

### `SprintTask` no sostiene lo que promete la Alternativa P - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L38, L105, L292`
* **Discrepancy Description**: `SprintTask` guarda solo el estado final. La Alternativa P dice que permite velocidad y burndown "después", pero el burndown necesita fechas de cambio de columna (no hay `done_at`) y las tareas retiradas antes del cierre no se registran.
* **Rationale & Recommendation**: Bajar la afirmación a "velocidad por sprint" o añadir `done_at`; mantener coherente la justificación con el alcance excluido.

### Sección Technical Plan mezcla contenidos y parte los riesgos - Severity: Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** `L61-181, L172, L183`
* **Discrepancy Description**: Bajo un mismo H2 conviven arquitectura, reglas de negocio, contrato HTTP y decisiones/supuestos. "Límites conocidos" (riesgos por naturaleza) queda separado de "Riesgos y mitigaciones" (L183).
* **Rationale & Recommendation**: Mover Supuestos y Límites junto a Riesgos o hacerlos H2 hermanos.

### Decisiones del autor duplicadas en dos secciones - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L43-55, L161-163`
* **Discrepancy Description**: "Decisiones de diseño tomadas por el autor" y "Decisiones adicionales" se solapan (Django, WhiteNoise, capas, idioma). El primer bloque aparece antes del contexto de arquitectura. "Las vistas son funciones o clases síncronas" (L163) no decide cuál.
* **Rationale & Recommendation**: Consolidar en una sola sección con una convención clara de cuál manda.

### Reglas 3, 8 y 10 se repiten y están mal ordenadas; párrafos densos - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L65, L105, L111-136`
* **Discrepancy Description**: La regla 8 remite a la 10 y esta a la 8; ambas repiten el comportamiento de `close_sprint` (también L105 y L114). La regla 10 (escritor único) debería ir antes de las que la usan. L65, L115, L134 y L136 son párrafos de 8 a 12 oraciones; la regla 3 mezcla orden de validación, locking, aislamiento, deadlock y UI. La regla 7 incrusta una tabla en un ítem de lista numerada.
* **Rationale & Recommendation**: Describir `close_sprint` una sola vez, reordenar, convertir la regla 3 en lista de pasos y dividir los párrafos largos. Sacar la tabla de permisos de la lista.

### Premisas del autor repetidas y probabilidades sin medición - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-structural`
* **Affected Scope:** `L17, L21, L167, L179, L190-191, L283-287`
* **Discrepancy Description**: El aviso de "premisa sin respaldo" aparece en L17, L21, L167, README L5 y Alternativa O; el diferencial frente a Jira/Linear aparece tres veces. "Poco probables a esta escala" y "baja probabilidad" no tienen medición. La fila de riesgo L191 usa "Límite conocido" como mitigación, que no mitiga y duplica L179. L190 ("Lentitud con proyectos grandes") es vaga. Los "Cons" de la Alternativa O no son técnicos.
* **Rationale & Recommendation**: Dejar un solo aviso. Declarar el supuesto de concurrencia o decir "no se previene en el MVP". Quitar o referenciar L191. Nombrar qué se degrada en L190 y cuándo activar la caché.

### Overview denso y mezcla de funciones - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L9-13`
* **Discrepancy Description**: Un párrafo mezcla definición, alcance del documento, exclusiones, stack y enlaces. Las exclusiones (comparativo, MoSCoW, métricas) pertenecen a Non-Goals. Además remite al "Detailed Implementation Plan" (L13), que queda fuera del rango.
* **Rationale & Recommendation**: Dividir en dos párrafos y mover las exclusiones a Non-Goals.

### Configuración de MySQL/Django y reintento de deadlock - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L115, L90, L163`
* **Discrepancy Description**: `isolation_level` va en `OPTIONS`, no en `DATABASES` directo. READ COMMITTED con binlog exige `binlog_format=ROW` (por defecto en 8.4). El reintento no funciona dentro de un `atomic` externo (`ATOMIC_REQUESTS`, `TestCase`). Falta capturar el error 1205 (lock wait timeout). Las pruebas de concurrencia requieren `TransactionTestCase` con conexiones reales. Ninguna alternativa compara bloqueo pesimista, optimista o `GET_LOCK`.
* **Rationale & Recommendation**: Documentar estos puntos y fijar `CONN_MAX_AGE`.

### Colación y normalización de correos y nombres - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L94, L97`
* **Discrepancy Description**: La colación por defecto `utf8mb4_0900_ai_ci` es insensible a acentos, así que `jose@` y `josé@` o dos nombres de departamento colisionan. La normalización a minúsculas debe estar en el modelo, no solo en el formulario.
* **Rationale & Recommendation**: Fijar la colación o declarar que es aceptable.

### Integridad de `Task` y permisos ambiguos - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L102-103, L125, L128, L133`
* **Discrepancy Description**: "Mismo proyecto" y "responsable es miembro" no indican dónde se aplican (querysets de formularios); un developer podría editar `kind`, `parent` o `epic`. "Developer: solo sus tareas" no aclara la creación ni la reasignación; el Scrum Master asigna sprints pero no edita tareas. Falta el índice `(sprint, column)` en el modelo (citado en L187). El presupuesto es legible por todo developer con registro abierto.
* **Rationale & Recommendation**: Fijar los campos editables por rol, el índice y una nota de confidencialidad.

### Seguridad de sesión y login - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L176-177, L188, L30`
* **Discrepancy Description**: Registro abierto sin límite de intentos más argon2 es un vector de denegación de servicio; el 422 por correo repetido enumera cuentas; la sesión de 8 horas es absoluta; las sesiones en MySQL requieren `clearsessions` sin cron previsto.
* **Rationale & Recommendation**: Anotar el riesgo y la tarea operativa de limpieza.

### Gantt con sprint sin fechas, borrado de miembros y `Vary` - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L99, L116, L109, L140`
* **Discrepancy Description**: Un sprint `planned` puede no tener fechas y el motivo en `undated` no está definido. Un miembro con tareas terminadas no puede eliminarse nunca y falta el camino de reasignación o desactivación. Si alguna ruta GET devolviera fragmento con `HX-Request`, necesita `Vary: HX-Request`.
* **Rationale & Recommendation**: Añadir el motivo, la vía de baja de miembros y el encabezado `Vary`.

### Tabla de `Task` y esquema JSON ilegibles - Severity: Nit
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L102, L107, L157`
* **Discrepancy Description**: La fila de `Task` concentra unas 12 reglas en una celda y L107 las repite. El esquema JSON del Gantt está en línea.
* **Rationale & Recommendation**: Pasar las reglas a una lista bajo la tabla, mantenerlas en un solo lugar y usar un bloque de código para el JSON.

### Idioma, terminología y separadores - Severity: Nit
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L3-7, L11, L28, L46, L97, L197-293, L295`
* **Discrepancy Description**: Encabezados mezclan inglés y español. "Rejected by author:" se repite 16 veces pese a L197. "Área" y "departamento" alternan, igual que "aplicación" y "sistema". Las líneas horizontales se usan solo en L7 y L295. No hay enlaces internos para "regla N" o "ver Componentes". Las 16 alternativas carecen de índice.
* **Rationale & Recommendation**: Fijar una convención de idioma y términos, quitar el prefijo repetido, añadir anclas e índice.

### Líneas redundantes o sin decisión asociada - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** `L41, L170, L53, L115, L155, L168, L176, L163, L55`
* **Discrepancy Description**: L41 y L170 dicen lo mismo; L155 repite L115; L168 y L176 son avisos operativos sin decisión; "vive" es coloquial (L53, L115); L55 y L163 repiten el idioma. L105 y L293 usan sinónimos redundantes ("una sola vez y no se edita").
* **Rationale & Recommendation**: Eliminar duplicados y referenciar en lugar de repetir.

### Afirmaciones sin calibrar - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** `L181, L193, L238, L254-256, L285, L231, L157`
* **Discrepancy Description**: "Sí se prueba" (L181, L193) afirma como hecho algo que aún no existe. "El token no se revoca antes de vencer" (L238) necesita matiz ("sin lista de revocación"). "Más fluida" (L256) es subjetivo. "Se mantienen solos" (L285) no está verificado. "Kanban clásico" (L231) no está definido. L157 usa "F4" sin definirlo en el rango.
* **Rationale & Recommendation**: Reescribir como compromisos de diseño u efectos observables, y definir la referencia a fases.

### Metadatos del documento - Severity: Nit
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** `L3-5`
* **Discrepancy Description**: "Status: Draft" no coincide con el estado del README, y los metadatos no enlazan al estándar usado.
* **Rationale & Recommendation**: Alinear el estado entre ambos documentos.
