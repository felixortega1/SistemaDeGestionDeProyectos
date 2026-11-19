# Goldfish Review Report

**Target:** `C:\Users\Usuario\Documents\Proyectos\SistemaDeGestionDeProyectos\docs\designs\plan-implementacion.md` (`1-466`; FeatureRange 1-309, DetailedRange 310-466)

**Estándar:** `zoom-out-standard.md`. Contexto: `README.md` y `docs/plan-prompt.md`. Las decisiones ya tomadas por el autor no se reabren.

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-zoom-out` | completed |
| `egm-inventive-catalyst` | completed |

Los dos reviewers coinciden en que el contexto es suficiente y el plan es coherente con el README. Ninguno encontró Blockers.

## Prioritized Findings (Blockers -> Major -> Nits)

No hay Blockers.

### Quién asigna el responsable: la matriz y el texto se contradicen - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `138`, `146`
* **Discrepancy Description**: La matriz dice que "Editar tareas" es `no` para el Scrum Master. La regla 7 dice que el responsable lo asigna "un Product Owner o Scrum Master" y que cambiar `assignee` lo hace "quien puede editar la tarea". Con la matriz, el SM no puede asignar. Un Developer que edita "sus tareas" podría reasignarlas o vaciar el `assignee`. No se dice qué hace `can_edit_task` con ese campo.
* **Rationale & Recommendation**: Añadir una fila "Asignar responsable" (PO y SM) y excluir `assignee` del formulario del Developer. También se puede darle al SM esa edición en la matriz.

### Una tarea no puede salir de un sprint `planned`; `assign_sprint` no define qué hace con una tarea que ya tiene sprint - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `121`, `149`, `153`, `160`, `340`
* **Discrepancy Description**: `assign-sprint` es la única ruta que escribe el sprint de una tarea. No hay "quitar del sprint". `close` solo vale desde `active` y los sprints no se borran, así que una asignación errónea a un sprint `planned` es permanente. El plan tampoco exige que la tarea no tenga sprint: `assign_sprint` podría reasignar una tarea terminada de un sprint cerrado o una de otro sprint activo, y reescribir su historia. Una tarea con filas en `SprintTask` nunca se puede borrar (`PROTECT`, 409), incluidas las que volvieron al backlog sin terminar. Eso no aparece en Límites conocidos.
* **Rationale & Recommendation**: Definir que `assign_sprint` exige una tarea sin sprint. Añadir `unassign_sprint` (solo desde un sprint `planned`, pasando por `apply_placement` y el bloqueo), o declarar la limitación en Límites conocidos junto con la imposibilidad de borrar tareas con historial.

### La edición de tarea puede pisar `column` y `sprint` - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `127`, `149`, `200`, `389`
* **Discrepancy Description**: La regla 10 afirma que `apply_placement` es el único escritor de `column` y `sprint`, y que los formularios no incluyen esos campos. Pero el plan no dice cómo se guarda la edición. Un `ModelForm.save()` sobre una instancia leída antes escribe todas las columnas, sin el bloqueo del proyecto. Un `move_task`, `assign_sprint` o `close_sprint` concurrente puede quedar revertido, con lo que se rompen el WIP y el invariante sprint/columna. La mitigación del riesgo (línea 200) promete una garantía que el plan no cumple.
* **Rationale & Recommendation**: Exigir en el servicio de edición `save(update_fields=<campos del formulario>)`, o releer la tarea bajo el bloqueo del proyecto. Añadir una prueba.

### Resolución de fechas efectivas incompleta para un sprint `planned` sin fechas - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`, `egm-zoom-out`
* **Affected Scope:** `111`, `128`, `390`
* **Discrepancy Description**: Las fechas del sprint pueden ser nulas mientras está `planned`, y esas tareas sí tienen sprint. La regla 4 define los motivos de `undated` solo para tareas "sin sprint". Una tarea con sprint de fechas nulas, o con una fecha propia más una del sprint nula, no tiene motivo, ni valor de `start_source` o `end_source`. `effective_dates` no se puede implementar sin decidirlo.
* **Rationale & Recommendation**: Definir el fallback como "valor efectivo nulo". Una fecha efectiva ausente da `sin fechas`; si solo hay una da `una sola fecha`, con independencia del sprint.

### `create_column` y `set_transitions` no están serializados - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** `127`, `182`, `387`
* **Discrepancy Description**: `create_column` desplaza posiciones y la "primera columna" es la de menor `position`. No hay `UniqueConstraint(project, position)` y el supuesto de la línea 182 dice que gana la última escritura. Dos creaciones simultáneas pueden dejar posiciones duplicadas. Entonces "primera columna" y "antes de `is_done`" quedan ambiguas, y eso afecta a `assign_sprint`. El bloqueo de proyecto ya existe, así que aceptar esta carrera es un falso compromiso.
* **Rationale & Recommendation**: Que `create_column` y `set_transitions` tomen el mismo bloqueo, y añadir la restricción de unicidad de `position`.

### El middleware de excepciones no puede construir el fragmento del tablero - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `168`, `384`, `395`
* **Discrepancy Description**: `ServiceExceptionMiddleware.process_exception` es genérico ("la página con un mensaje, o el fragmento HTMX con el mismo estado"). Para `move`, el 409 o 422 debe devolver `_board.html` con el tablero redibujado y el mensaje, y un middleware no tiene ese contexto. Sin decidirlo, el criterio de F3 y el paso 6 del E2E no son ejecutables. Tampoco hay plantilla de error o de mensaje para las demás respuestas.
* **Rationale & Recommendation**: Decidir que la vista `move` captura la excepción y renderiza el fragmento, o que el middleware delega en la vista. Añadir la plantilla genérica de error a la lista de archivos.

### `/admin/` no puede cumplir lo que el plan le asigna - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `176`, `189`, `362`, `385`, `391`
* **Discrepancy Description**: El plan dice que el operador cierra sesiones ajenas borrándolas "desde `/admin/`". `Session` no está registrada en el admin por defecto, y el `User` propio tampoco tiene `ModelAdmin`. Ningún `admin.py` figura en la lista de archivos.
* **Rationale & Recommendation**: Añadir `apps/accounts/admin.py` con ambos registros, o quitar la afirmación.

### Dos o cero Product Owner y carreras aceptadas con el bloqueo ya disponible - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `108`, `146`, `192`
* **Discrepancy Description**: La línea 192 acepta como límite el ciclo de dependencias y el doble Product Owner por concurrencia. Tomar el bloqueo del proyecto en `add_dependency` y `transfer_product_owner` lo evitaría sin coste relevante. Para el PO también sirve un `GeneratedField` con `UniqueConstraint`, igual que con el sprint activo. Además, el endpoint de rol rechaza `product_owner` pero no dice qué pasa si cambia el rol del PO actual (queda un proyecto sin PO) ni si `members/add` recibe `product_owner`.
* **Rationale & Recommendation**: Tomar el bloqueo en esas dos operaciones y definir el rechazo de esos dos casos.

### WIP no se valida al asignar a un sprint `planned` - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `111`, `149`, `339`
* **Discrepancy Description**: Se pueden asignar a un sprint `planned` más tareas que el límite de la primera columna. Al iniciarlo, la columna queda por encima del límite sin rechazo. Es coherente con "el límite solo se comprueba al entrar", pero no está dicho.
* **Rationale & Recommendation**: Una frase en las reglas 8 o 10.

### Borrado de miembros: no se dice si las historias asignadas cuentan - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** `121`, `386`
* **Discrepancy Description**: La regla "tareas asignadas que no están en una columna `is_done`" incluye historias y tareas de backlog, que nunca tienen columna. Un miembro con una historia asignada no se podría quitar.
* **Rationale & Recommendation**: Decir explícitamente si cuentan o no.

### Ruta `dependencies/<dep_id>/delete/` ambigua - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `115`, `159`
* **Discrepancy Description**: `TaskDependency` no tiene `id` en la tabla. No queda claro si `dep_id` es el id de la fila o el de la tarea `depends_on`. Afecta al resolvedor de permisos.
* **Rationale & Recommendation**: Fijar el significado de `dep_id`.

### Fallback de migración con `RunSQL` incompleto - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`, `egm-zoom-out`
* **Affected Scope:** `388`, `417`, `421`
* **Discrepancy Description**: Si el `GeneratedField` sigue declarado en el modelo, `makemigrations --check` detectaría cambios con el `RunSQL` a mano; hace falta `SeparateDatabaseAndState`. Además, `start_sprint` toma el bloqueo del proyecto, así que el índice único solo se prueba insertando directo con el ORM, y la traducción de `IntegrityError` a `Conflict` en `start_sprint` es una red de seguridad.
* **Rationale & Recommendation**: Mencionar `SeparateDatabaseAndState` y aclarar cómo se prueba el índice.

### Contrato de los hitos inconsistente - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `128`, `170`
* **Discrepancy Description**: La regla 4 dice que los hitos "se dibujan en una fila aparte". El contrato dice que son barras de un día y que, si falla la prueba de concepto, solo se listan.
* **Rationale & Recommendation**: Unificar la formulación.

### Pasos del E2E sin cobertura o irreproducibles - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `434-449`
* **Discrepancy Description**: El paso 10 necesita una tarea retrasada, pero el paso 3 solo pide "fechas de inicio y fin". Sin fechas pasadas no hay marca. F5 (presupuesto) no tiene ningún paso, aunque el recorrido completo se repite al cerrar F5.
* **Rationale & Recommendation**: Especificar fechas pasadas en el paso 3 y añadir un paso de presupuesto.

### Resolvedores de permisos: la fase de cada uno no está clara - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `384`
* **Discrepancy Description**: El ítem 15 enumera todos los resolvedores como "Create, F1" y, dentro del mismo ítem, dice que en F1 solo existe el de proyecto.
* **Rationale & Recommendation**: Indicar la fase de cada resolvedor.

### Decisión pendiente de la versión de `frappe-gantt` y Open Questions - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `59`, `316`, `406`
* **Discrepancy Description**: La versión queda "antes de cerrar la lista de archivos de F4" y no figura en Open Questions. Esta solo recoge equipo y plazo, que el plan no usa para nada concreto, y las fases quedan sin dimensionar.
* **Rationale & Recommendation**: Fijar la versión ahora o dejarla como salida explícita de la prueba de concepto de F4, y listarla en Open Questions.

### Firma sobrante de `effective_dates` y índices redundantes - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** `200`, `389`, `390`
* **Discrepancy Description**: `effective_dates(task, sprint, today)` recibe `today`, pero el retraso se calcula en `build_gantt` (regla 6). Los índices `Task(sprint, column)` y `Task(project, sprint, column)` se solapan, y el riesgo de la línea 200 menciona solo el primero.
* **Rationale & Recommendation**: Quitar `today` de la firma y dejar un solo índice según la consulta real.

### Altura del detalle: SQL literal, `htmx.ajax`, `subprocess` y `threading.Barrier` - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `312`, `388`, `404`, `414`, `422`
* **Discrepancy Description**: La línea 312 promete "sin código de implementación", pero el plan trae SQL de respaldo, la llamada `htmx.ajax(...)` con sus parámetros y el mecanismo de `test_imports` y de las pruebas de concurrencia.
* **Rationale & Recommendation**: Dejarlos al implementador, o aceptar la excepción de forma explícita. Esto no impide ejecutar el plan.

### `plan-prompt.md` y README frente al plan; resto de proceso - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** `13`, `466`, `README.md:22`
* **Discrepancy Description**: El prompt sigue exigiendo comparativo, MoSCoW y métricas de éxito, que el plan excluye (lo reconoce, pero un lector nuevo ve un incumplimiento). El README dice "fase 2" y el plan "versión posterior" para ruta crítica, línea base y edición del Gantt. El pie `*Drafted with EGM*` (línea 466) es un resto de proceso.
* **Rationale & Recommendation**: Una línea de aclaración en el prompt o el README, unificar la terminología y quitar el pie antes de publicar.

## Consistencia verificada (sin hallazgos)

* Orden de capas, dependencias de migraciones y uso de `apps.get_model` (381).
* Orden de validaciones de `move_task` (regla 3) frente a las pruebas listadas.
* WIP con `READ COMMITTED` y bloqueo de proyecto, y su coincidencia con la tabla de riesgos.
* Criterios de aceptación F1 a F5 frente a los archivos de cada fase. El paso 12 del E2E (cierre construido en F2 y comprobado en F3) está justificado en el texto.
