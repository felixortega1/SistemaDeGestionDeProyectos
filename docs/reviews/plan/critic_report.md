# Goldfish Review Report

**Target:** `docs/designs/plan-implementacion.md` (`líneas 1-309`)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-design` | completed |
| `egm-structural` | completed |
| `egm-style` | completed |

Notas: los tres reportaron que `agents/egm-*.md` no existe y usaron `agents/{design,structural,style}.md`. Las fases y los criterios de aceptación (líneas 310-353 en adelante) quedaron fuera del rango y no se cruzaron. Ningún reviewer aplicó estándares de `document_standards/` salvo structural (feature-spec e implementation-readiness). Las decisiones del autor no se discuten.

## Prioritized Findings (Blockers -> Major -> Nits)

No hay Blockers.

### F1. Las vistas de edición evaden el bloqueo y el "único escritor" - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** L111, L114, L149, L159-160, L192
* **Discrepancy Description**: `POST /tasks/<id>/edit/` y `POST /sprints/<id>/edit/` no toman el bloqueo de proyecto. Un `ModelForm.save()` hace UPDATE de todas las columnas con los valores leídos al cargar el formulario. Si otro usuario mueve la tarea o inicia el sprint entre la carga y el guardado, se revierte `column`, `sprint` o `Sprint.status` (puede borrar un sprint activo sin pasar por `start_sprint`, y saltarse transición y WIP). La regla 10 dice "dos de ellas nunca se ejecutan a la vez" sin aclarar que otras escrituras (edición, borrado, `transfer_product_owner`, dependencias, transiciones) quedan fuera.
* **Rationale & Recommendation**: Usar `save(update_fields=[...])` en ambas ediciones, o tomar el mismo bloqueo. Declarar en la regla 10 qué escrituras quedan fuera. Añadir prueba de concurrencia.

### F2. `create_column` regresiona la política, la posición y el bloqueo - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-structural`, `egm-style`
* **Affected Scope:** L50, L112-113, L119, L149, L161, L171, L182
* **Discrepancy Description**:
  * Al insertar N entre P y D (`is_done`) se siembran P↔N y N↔D, pero P↔D ya existía y nada dice que se borre; se puede saltar N, contra la intención de la política por defecto. Tampoco se define el caso de transiciones personalizadas ni si "contiguas" significa ambos sentidos.
  * `create_column` desplaza `position` sin bloqueo de proyecto y no hay unicidad `(project, position)`; dos altas simultáneas dejan posiciones duplicadas. `assign_sprint` depende de "menor `position`".
  * No se garantiza exactamente una columna `is_done` (ninguna restricción).
  * `create_column` no figura como servicio nombrado (L77, L88) ni en las reglas.
  * L182 habla de "edición concurrente de `position`", pero ninguna ruta la edita; solo la toca `create_column`.
  * `POST …/columns/transitions/` reemplaza el conjunto completo: un formulario abierto antes de crear la columna borra en silencio sus transiciones.
  * L50 dice que solo el Scrum Master edita transiciones, omitiendo al Product Owner (L52, L142).
* **Rationale & Recommendation**: Redactar una regla verificable ("al crear X entre A e `is_done`: se elimina A↔`is_done` si es automática, se crean A↔X y X↔`is_done`, las demás no cambian"). Meter `create_column` en el bloqueo de proyecto, añadir `UniqueConstraint(project, position)` o desempate por `id`, y que el reemplazo de transiciones opere solo sobre las columnas que trajo el formulario. Nombrar el servicio y su capa.

### F3. `assign_sprint` no valida el estado de origen de la tarea - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** L116-117, L119, L147, L149
* **Discrepancy Description**: Solo exige `kind = task` y sprint destino `planned` o `active`; deja siempre la tarea en la primera columna. Reasignar una tarea ya en el tablero la devuelve a "Por hacer" desde cualquier columna, evadiendo `ColumnTransition`. Una tarea terminada de un sprint `closed` puede reabrirse en otro, y `SprintTask` del sprint cerrado queda diciendo `is_done` (contradice "se escribe una vez"). No se define el caso del mismo sprint.
* **Rationale & Recommendation**: Exigir `task.sprint is None`, o definir reglas explícitas de movimiento entre sprints (solo hacia `planned`).

### F4. Sin salida para sprints `planned` ni para tareas asignadas por error - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** L111, L147, L153, L158-161
* **Discrepancy Description**: No hay ruta para desasignar una tarea. Un sprint `planned` no se puede cerrar (`close` solo desde `active`) ni borrar; sus tareas solo vuelven al backlog por `close_sprint`. Un error de planning no es reversible.
* **Rationale & Recommendation**: Añadir "desasignar" (`apply_placement(task, None, None)` bajo bloqueo) y/o cancelar/borrar un `planned`.

### F5. Gantt: tareas con sprint `planned` sin fechas no tienen motivo en `undated` ni regla de `is_late` - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-structural`, `egm-style`
* **Affected Scope:** L111, L128, L130
* **Discrepancy Description**: Los tres motivos (`sin fechas`, `una sola fecha`, `fin anterior al inicio`) describen solo "sin sprint". Una tarea con sprint cuyas fechas son nulas, o con una sola fecha propia más sprint sin fechas, queda sin fecha efectiva y sin motivo. La regla 6 no define `is_late` con fin efectivo nulo.
* **Rationale & Recommendation**: Añadir el motivo (p. ej. `sprint sin fechas`) y declarar que sin fin efectivo no hay `is_late`.

### F6. Contradicción sobre quién asigna responsable - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** L133-146
* **Discrepancy Description**: El texto dice que PO o Scrum Master asignan responsable y que "cambiar el `assignee` lo hace quien puede editar la tarea", pero la matriz niega al Scrum Master editar tareas. Además, un Developer que edita "sus tareas" puede cambiar el `assignee` y traspasarlas, contra "un Developer no toma tareas".
* **Rationale & Recommendation**: Separar un permiso para `assignee` (PO y Scrum Master) y excluir el campo de la edición del Developer.

### F7. Afirmaciones sobreafirmadas en la regla 3 (deadlocks, "sin consecuencias", `READ COMMITTED`) - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-style`
* **Affected Scope:** L127
* **Discrepancy Description**: "No hay deadlocks" y "el servicio no reintenta" solo valen entre las cuatro operaciones; las escrituras fuera del protocolo toman bloqueos de fila o de FK sobre `Project`/`Task`. No se fija `innodb_lock_wait_timeout` ni se mapean los errores 1205/1213 a 409. "Sin consecuencias" no tiene evidencia. La justificación de `READ COMMITTED` ("para que el conteo vea los commits") es débil: con el bloqueo de proyecto bastaría cualquier nivel.
* **Rationale & Recommendation**: Acotar la afirmación, documentar el mapeo 1205/1213 a 409, y decir qué ocurre con una edición simultánea de `wip_limit` ("el movimiento usa el valor leído; el nuevo rige desde el siguiente").

### F8. Listas de operaciones con bloqueo y módulos inconsistentes - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** L77, L89, L149, L200
* **Discrepancy Description**: Tres listas no coinciden: L77 (`apply_placement`, `assign_sprint`, `move_task`, `close_sprint`, `get_board`), regla 10 (`start_sprint`, `assign_sprint`, `move_task`, `close_sprint`) y L200 ("las cuatro operaciones que escriben sprint o columna", aunque `start_sprint` no escribe tareas y `apply_placement` no toma bloqueo). `start_sprint` no tiene módulo declarado (debería ser `sprints.services`). La regla 10 mezcla dos reglas (único escritor y bloqueo) y "ni `status`" es ambiguo: `Task` no tiene `status` y quién escribe `Sprint.status` no se dice.
* **Rationale & Recommendation**: Una sola lista con módulo de cada servicio; dividir la regla 10 en 10a (único escritor) y 10b (bloqueo por proyecto); aclarar el `status`.

### F9. Permiso en la regla 3 frente al decorador de la regla 7 - Severity: Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** L127, L131, L168
* **Discrepancy Description**: El paso 1 comprueba el permiso dentro del servicio, bajo bloqueo; la regla 7 lo asigna a un decorador con lectura sin bloqueo. `can_move_task` depende de `assignee`, que puede cambiar por edición concurrente. No se dice cuál manda, ni qué devuelve la relectura si la tarea fue borrada entre lectura y bloqueo; 403/404 no están en los contratos de respuesta.
* **Rationale & Recommendation**: Declarar que el servicio re-comprueba bajo bloqueo y definir la respuesta ante tarea borrada.

### F10. Contratos de respuesta incompletos para otras rutas con 409/422 - Severity: Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** L159-160, L167-168
* **Discrepancy Description**: Solo `move` tiene contrato de error. `assign-sprint` (409 WIP, 422), `start`, `close` y `delete` (409) no están marcadas (H) ni dicen qué página se redibuja o cómo se muestra el 409.
* **Rationale & Recommendation**: Ampliar la sección de contratos con estas rutas.

### F11. La regla 3 es un párrafo único con unas diez afirmaciones - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** L127
* **Discrepancy Description**: Mezcla secuencia de validación, aislamiento, semántica de `wip_limit`, no expulsión, deadlocks, edición concurrente y resaltado del navegador. El paso (2) agrupa cuatro condiciones bajo un `422`; en el paso (5) no queda claro si valida `move_task` o `apply_placement`. `count >= wip_limit` está inline.
* **Rationale & Recommendation**: Lista numerada de validaciones más bloques "Semántica del límite" y "Concurrencia"; nombrar un solo responsable del WIP; mover el resaltado a L169.

### F12. Índice `(sprint, column)` citado pero no definido - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** L114, L200
* **Discrepancy Description**: La mitigación de riesgo cita el índice pero el modelo no lo declara (ni ningún otro índice de `Task`).
* **Rationale & Recommendation**: Declararlo en el modelo de datos.

### F13. Sprint `planned` con primera columna sin WIP al iniciar - Severity: Major (bajo)
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** L127, L147, L149
* **Discrepancy Description**: Las tareas asignadas a un sprint `planned` ocupan la primera columna sin comprobar WIP; `start_sprint` no pasa por `apply_placement`. Al iniciar, la primera columna puede superar su `wip_limit` (o ser 0).
* **Rationale & Recommendation**: Declararlo como excepción explícita o comprobarlo en `start`.

### F14. Decisiones nuevas sin registro ni alternativa - Severity: Major (bajo)
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** L43-55, L176, L208-306
* **Discrepancy Description**: El bloqueo por proyecto, `apply_placement` como único escritor y `READ COMMITTED` no figuran en "Decisiones de diseño tomadas por el autor" ni en "Decisiones adicionales", y ninguna alternativa (bloqueo por fila o por sprint, control optimista) los cubre.
* **Rationale & Recommendation**: Añadirlos como decisiones y sumar al menos una alternativa con su trade-off.

### F15. Redundancia y término "política" con dos sentidos - Severity: Major (bajo)
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** L27, L50, L112, L117, L119, L147, L149, L260
* **Discrepancy Description**: "Política" designa a la vez la tabla `ColumnTransition` (se evalúa) y `policy_text` (informativo). Además, el historial de `close_sprint` se repite en L117, L147 y L149, y "una tarea nueva no tiene sprint ni columna" en L119 y L149.
* **Rationale & Recommendation**: Definir ambos términos en Términos y dejar una fuente canónica para `close_sprint`.

### F16. Carreras no declaradas al quitar miembros y otros límites - Severity: Major (bajo)
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** L114, L121, L147, L192
* **Discrepancy Description**: Quitar un miembro no toma el bloqueo y compite con assign/move/close; puede quedar una tarea asignada a un no miembro. L192 describe "dos cambios de rol", pero el endpoint rechaza `product_owner`; el riesgo real es dos `transfer_product_owner` simultáneos.
* **Rationale & Recommendation**: Corregir L192 y añadir la carrera de miembros a Límites conocidos.

### F17. Nits de modelo, permisos y rutas - Severity: Nit
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** L113, L138, L147, L160, L171
* **Discrepancy Description**: Falta `CHECK from_column <> to_column` en `ColumnTransition`; "mismo proyecto" de ambas columnas solo en servicio y sin validar en el POST de L171. L138 no dice si "sus tareas" se evalúa sobre `task` o `depends_on`. `sprints/<id>/edit/` no dice si se puede editar `active` o `closed`, ni cuándo se editan review/retro tras cerrar. No hay validación de solapamiento ni fechas pasadas entre sprints.
* **Rationale & Recommendation**: Declarar cada punto o documentarlo como límite.

### F18. Nits de terminología y redacción - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** L13, L38, L73, L77, L111, L114, L127, L158, L168, L170, L189, L192, L204-205
* **Discrepancy Description**:
  * "Bloqueo del proyecto" / "por proyecto" / "ese bloqueo" sin término único; "tarjeta" no está en Términos; mezcla WIP / límite WIP / `wip_limit`; "409 Conflict" solo en L127.
  * "Operador" definido dos veces (L73, L189) y usado antes (L176).
  * L77 es un párrafo de unas diez frases con un "Por eso" que no se sigue; "dueña de" es coloquial.
  * Celdas de 8 o más oraciones en las filas `Sprint` y `Task` (L111, L114).
  * `board.js` y los "dos archivos propios" no se nombran (L13, L168); F1/F3/F4 no se definen en el rango (L158, L170).
  * Hedging sin decisión: "poco probables a esta escala" (L192, L204), "no cubre lo que se necesita" (L205), "esa serialización es aceptable" (L149).
  * L38 afirma "no son posibles" burndown y flujo; mejor "no se pueden calcular con este historial".
  * L114/L121 duplican la regla del responsable de tareas terminadas.
* **Rationale & Recommendation**: Unificar términos, dividir párrafos largos, mover restricciones a listas bajo la tabla y precisar los criterios.

### F19. Estructura de encabezados e idioma - Severity: Nit
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** L43-57, L63, L210-300
* **Discrepancy Description**: H2 mezclan inglés y español; "Supuestos" y "Límites conocidos" son H3 bajo Technical Plan mientras "Riesgos y mitigaciones" es H2. "Términos" está dentro de Technical Plan pero se enlaza desde Overview. "Open Questions" precede a la arquitectura. "Rejected by author:" se repite 16 veces tras una frase que ya lo dice; en O, F y P la razón es "se quiere" o "se eligió".
* **Rationale & Recommendation**: Unificar idioma y nivel; reducir la repetición del prefijo.

## Resumen de severidad

| Severidad | Cantidad |
| --- | --- |
| Blocker | 0 |
| Major | 16 (F1-F16, de los cuales F13-F16 son de impacto bajo) |
| Nit | 3 agrupados (F17-F19) |

Los hallazgos más importantes de los últimos arreglos son F1 (edición que evade el bloqueo), F2 (`create_column`) y F3 (`assign_sprint` sobre tareas ya colocadas).
