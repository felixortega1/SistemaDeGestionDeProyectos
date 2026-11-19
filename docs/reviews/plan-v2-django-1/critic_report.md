# Goldfish Review Report

**Target:** `docs/designs/plan-implementacion.md` (`líneas 1-266`)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-design` | completed |
| `egm-structural` | completed |
| `egm-style` | completed |

Resumen: 0 Blockers, 14 Majors, 14 Nits. Stack no relitigado. Las afirmaciones de Django/MySQL/HTMX son conocimiento del revisor, no ejecutadas.

## Prioritized Findings (Blockers -> Major -> Nits)

(Sin Blockers.)

## Major

### Un solo rol por usuario impide operar a un usuario solo - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L93, L118-125, L128, L171`
* **Discrepancy Description**: `ProjectMember` es único por (project, user). El creador queda como PO y solo el SM abre/cierra sprints y edita columnas/WIP/transiciones. Un usuario solo o un equipo de dos no puede ejecutar un sprint. La transferencia de PO (L128) no define atomicidad ni el rol del PO anterior.
* **Rationale & Recommendation**: Permitir rol PO+SM combinado o dar al PO los permisos del SM; definir la transferencia como intercambio atómico.

### El lock del WIP no cubre toda la concurrencia - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L111-112, L129, L181`
* **Discrepancy Description**: Solo se bloquea la columna destino. Dos POST sobre la misma tarea validan contra una columna origen obsoleta; `close`/`start` de sprint pueden cruzarse con un `move`; `start` no aplica WIP y puede arrancar excediendo el límite de la primera columna; no se define bajar `wip_limit` por debajo del conteo.
* **Rationale & Recommendation**: Fijar orden de locks (sprint, tarea, columna destino), bloquear el sprint en `start`/`close`, documentar que `wip_limit` solo se valida al entrar.

### Corrección del WIP depende del aislamiento y del reintento - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L111`
* **Discrepancy Description**: "Lock y luego COUNT" solo es correcto si el COUNT lee lo último confirmado (REPEATABLE READ con snapshot previo daría conteo viejo). No se fija `isolation_level`, ni se aclara que ATOMIC_REQUESTS o lecturas previas no deben abrir la transacción antes del lock. El reintento de deadlock (1213) debe envolver todo el `atomic()` externo; falta 1205.
* **Rationale & Recommendation**: Fijar y documentar `isolation_level` en `DATABASES` y la política de reintento externa (1213 y 1205).

### Historias y `assign-sprint` se contradicen - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L99, L103, L112`
* **Discrepancy Description**: La regla 3b deja la tarea en la primera columna al asignar sprint, pero una historia tiene `column` nulo y no cuenta para WIP; no se dice si una historia puede tener `sprint`. Faltan CheckConstraint (story implica column y parent nulos).
* **Rationale & Recommendation**: Decidir: solo `kind=task` se asigna a sprint, o la asignación de historia se propaga a sus hijas. Añadir los CheckConstraint.

### Invariantes "mismo proyecto" solo en servicios - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L87, L98-99, L123, L139`
* **Discrepancy Description**: Epic, sprint, parent, column, assignee y ColumnTransition deben ser del mismo proyecto, pero no es expresable con CHECK/FK simples; admin, shell o scripts las saltan. Quitar un miembro (L139) no define qué pasa con sus tareas, y un developer no podría mover tareas de un ex-miembro.
* **Rationale & Recommendation**: FK compuestas o `clean()`/`save()` más pruebas de invariantes; definir quitar miembro (409, desasignar o reasignar).

### Manejo HTMX incompleto fuera de 409/422 - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L134, L149, L170`
* **Discrepancy Description**: HTMX no hace swap de 4xx/5xx por defecto; `board.js` solo habilita 409 y 422. Sesión expirada produce 302 a login que HTMX sigue e inyecta la página completa en el tablero. 403/404/500 quedan sin feedback. Las rutas (H) varían por cabecera y requieren `Vary: HX-Request`. El drag rechazado deja la tarjeta movida en el DOM hasta el reemplazo.
* **Rationale & Recommendation**: `HX-Redirect`/401 con `HX-Request`; manejador `htmx:responseError`/`beforeSwap` general; `Vary: HX-Request`; escribir como contrato el reemplazo del tablero.

### `position` incoherente con el arrastre - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L99, L149, L163, L200`
* **Discrepancy Description**: La posición se recalcula como última de la columna y mover dentro de la misma columna "no hace nada", por lo que no se puede reordenar; no hay ruta para reordenar el backlog; `max+1` concurrente duplica posiciones sin desempate.
* **Rationale & Recommendation**: Decidir si el MVP reordena; si no, quitar `position` y ordenar por `id`/`created_at`.

### El diseño no soporta métricas de flujo ni historial - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-structural`
* **Affected Scope:** `L13, L37, L55, L99, L186`
* **Discrepancy Description**: Solo existe `column_changed_at`, sobrescrito en cada movimiento: no se pueden calcular lead time, cycle time, throughput. No figuran como pendientes ni Non-Goal. Faltan secciones que pide `plan-prompt.md` (comparativo, MoSCoW, métricas de éxito, Integración Scrum, Roadmap con criterios de aceptación); L13 declara solo parte como pendiente y L186 habla de "fase 4" sin roadmap.
* **Rationale & Recommendation**: Añadir `TaskColumnEvent(task, from, to, at, by)` escrita en `apply_placement`, o declarar métricas fuera de alcance; listar explícitamente todo lo pendiente.

### Unicidad de sprint activo y PO frágil - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L93, L96, L173`
* **Discrepancy Description**: Columna generada + índice único vía `RunSQL` no es detectada por `makemigrations`. El "un solo PO" acepta la carrera.
* **Rationale & Recommendation**: Usar `GeneratedField` + `UniqueConstraint` (Django 5.2) o `RunSQL` con `state_operations` y `reverse_sql`; aplicar el mismo patrón al PO; mapear `IntegrityError` a 409; pruebas con `TransactionTestCase` en MySQL real.

### Rendimiento del Gantt con 2.000 tareas - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L114, L161, L163, L184`
* **Discrepancy Description**: El supuesto cubre solo el servidor; frappe-gantt dibuja SVG por barra y flecha. El plan B existe sin criterio de activación. La detección de ciclos sin límite debe ser iterativa (RecursionError). Evitar N+1.
* **Rationale & Recommendation**: Definir umbral para el plan B, ciclos iterativos, carga en pocas queries.

### Encabezados con idioma mezclado - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L3-5, L9-189, L193-262`
* **Discrepancy Description**: Overview, Goals, Non-Goals, Open Questions, Technical Plan, Alternatives Considered, Pros/Cons/Reason for Rejection en inglés; el resto en español, y README/prompt exigen español.
* **Rationale & Recommendation**: Unificar o declarar la excepción de encabezados canónicos.

### Estructura de secciones desordenada - Severity: Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** `L42-50, L159-187`
* **Discrepancy Description**: "Decisiones de diseño tomadas por el autor" es H2 fuera del esquema y duplica L111/L113 y "Decisiones adicionales". Riesgos (H2) está separado de Supuestos y Límites (H3 en Technical Plan).
* **Rationale & Recommendation**: Mover/fusionar las decisiones en Technical Plan y agrupar riesgos, supuestos y mitigaciones.

### Numeración "3b" y tabla anidada en lista - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** `L107-130`
* **Discrepancy Description**: "3b." no es lista Markdown válida; la tabla de permisos (L118-126) y la nota L128 con sangría en la regla 7 son frágiles.
* **Rationale & Recommendation**: Renumerar o hacer subregla; sacar la tabla a un H3 "Permisos por rol".

### Referencias a un "plan anterior" inaccesible y redundancias - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** `L4, L29, L39-40, L46-48, L111-113, L161-174, L182, L229, L247`
* **Discrepancy Description**: "Sin revisar tras el cambio", "plan anterior" exigen historial ausente. Sesión de 8 h, falta de mediciones y política de fechas se repiten en varias secciones.
* **Rationale & Recommendation**: Quitar referencias del cuerpo o pasarlas a un changelog; un único lugar normativo por dato con referencias cruzadas.

### Afirmaciones sobrecalibradas y probabilidades sin medir - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** `L17, L19, L29, L173, L185, L233`
* **Discrepancy Description**: "El token no se revoca antes de vencer" es falso en general (lista de bloqueo); "poco probables a esta escala" no está medido; "no pueden contradecirse" y "sin pasos manuales" son absolutos con excepciones posteriores.
* **Rationale & Recommendation**: Condicionar ("sin lista de revocación...", "localStorage"), nombrar la condición concreta, poner la excepción primero.

## Nit

### Prefijo "Rejected by author:" repetido - Severity: Nit
* **Reviewer Lens:** `egm-style`, `egm-structural`
* **Affected Scope:** `L191-262`
* **Discrepancy Description**: Repetido 12 veces, en inglés y redundante con L191. Alternativas de stack (G, J, K, L) mezcladas con las de diseño.
* **Rationale & Recommendation**: Dejar "Motivo del rechazo:"; agrupar bajo "Alternativas de stack".

### Detalles del modelo y de MySQL - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L87, L96-97, L113`
* **Discrepancy Description**: `PROTECT` por defecto vs `CASCADE` en hijos: borrar proyecto en `/admin/` fallaría con ProtectedError. CHECK de MySQL no admite columnas con acciones referenciales (anotar). Sprint planned con fechas nulas sin efecto definido; sin solapamiento ni cierre automático. Verificar si `end` de frappe-gantt es inclusivo. "Primera columna" y al menos una `is_done` no garantizadas; reemplazo de transiciones es last-write-wins.
* **Rationale & Recommendation**: Elegir una política de borrado y documentar las demás.

### Configuración de despliegue incompleta - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L30, L91, L157, L182`
* **Discrepancy Description**: Faltan `SECURE_PROXY_SSL_HEADER`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, HSTS, utf8mb4, `argon2-cffi` y `PASSWORD_HASHERS`. `clearsessions` periódico contradice "sin otros servicios". `/admin/` en ruta conocida. Registro abierto sin límite.
* **Rationale & Recommendation**: Añadir checklist de despliegue.

### Ambigüedades de permisos y efectos colaterales - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** `L94, L114, L121, L129-130`
* **Discrepancy Description**: "Solo sus tareas" es ambiguo al crear; no se dice quién crea/edita sprints ni si un developer puede reasignarse. Al cerrar sprint las tareas no terminadas caen en `undated` (Límite conocido). Hitos sin vínculo con sprints; historia como dependencia sin definir. `currency` sin ISO 4217; presupuesto visible a todos; sin control optimista.
* **Rationale & Recommendation**: Aclarar o listar en Límites conocidos.

### Tono y vocabulario - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** `L30, L56, L63, L157, L175, L184, L187, L195, L225, L237-238, L249`
* **Discrepancy Description**: Adjetivos subjetivos ("simple", "control total", "más fluida"); "lentitud con proyectos grandes" y "caché diferida" sin umbral; comportamiento futuro como hecho (L63, L187); L56 no es pregunta abierta; "y sí se prueba" coloquial; mysqlclient/PyMySQL sin decisor; terminología mezclada (responsable/assignee, estado/column/status).
* **Rationale & Recommendation**: Sustituir por hechos medibles, futuro o modal, y fijar un término por concepto con glosario.

### Densidad y formato - Severity: Nit
* **Reviewer Lens:** `egm-style`, `egm-structural`
* **Affected Scope:** `L3-5, L13, L49, L87, L99, L111, L113, L134-142, L265`
* **Discrepancy Description**: Párrafos densos (L87, L99, L111, L113, L49); leyenda "(H)" solo en prosa; L13 cita "Detailed Implementation Plan" (L267, fuera del rango); separadores `---` inconsistentes; diagrama ASCII con riesgo de desalineo.
* **Rationale & Recommendation**: Dividir en listas, añadir leyenda junto a la tabla, aclarar la referencia.
