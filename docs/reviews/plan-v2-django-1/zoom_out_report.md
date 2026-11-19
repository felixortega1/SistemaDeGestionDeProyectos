# Informe de revisión Goldfish (zoom-out)

**Objetivo:** `docs/designs/plan-implementacion.md` (líneas 1-384; FeatureRange 1-266, DetailedRange 267-384)
**Estándar:** `zoom-out-standard.md`. **Contexto:** proyecto solo de diseño; stack ya cambiado a Django-only (no se reabre).

## Estado de los revisores

| Revisor | Estado |
| --- | --- |
| `egm-zoom-out` | completed |
| `egm-inventive-catalyst` | completed |

Restos del stack anterior: no hay referencias funcionales a FastAPI, React, JWT ni API JSON. Solo quedan menciones narrativas (ver Nit N1).

## Hallazgos priorizados

### B1. El rol único por usuario bloquea el recorrido E2E - Severity: Blocker
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** líneas 93, 118-128, 277, 312, 359-369
* **Discrepancy Description:** el creador del proyecto queda como Product Owner (PO) y `ProjectMember` es único por `(project, user)`, o sea, un solo rol. Solo el Scrum Master (SM) puede abrir, cerrar y asignar sprints y editar columnas, WIP y transiciones. El PO no puede hacer ninguna de esas cosas. Los pasos 3 y 10 del E2E y el criterio de F2 (segundo sprint activo da 409) no se pueden ejecutar con un solo usuario.
* **Rationale & Recommendation:** modelar los roles como conjunto (`MemberRole` o banderas `is_po`/`is_sm`/`is_dev`), o dar PO+SM al creador. Coste: la matriz y `test_roles` pasan a evaluar uniones de roles.

### M1. Orden de fases contradictorio - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** líneas 269, 277-281, 310, 313-315, 319, 341-344
* **Discrepancy Description:** F2 exige `assign_sprint` y el cierre de sprint con tareas "a la primera columna", que llaman a `board.services.apply_placement`, pero este se sitúa en F3. Además `test_roles` y `test_isolation` de F2 cubren acciones de F3 y F5 (mover, editar columnas, departamentos).
* **Rationale & Recommendation:** mover `apply_placement` y `get_board` a F2 (o un esqueleto en F1) y repartir las pruebas por fase. Si no, se rompe la promesa de que cada fase deja el sistema ejecutable.

### M2. Dependencias circulares entre apps y sobre-segmentación - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** líneas 63, 307, 310, 313-321
* **Discrepancy Description:** la regla "solo importar `services`/`models` de otra app" permite ciclos `board` ↔ `backlog` ↔ `sprints`. `core.permissions` importa modelos de casi todas las apps, así que no es una hoja. Hay ocho apps para un MVP; `budget` es un modelo y `gantt` no tiene modelos.
* **Rationale & Recommendation:** fijar un orden de capas (por ejemplo `core` sin imports de apps) o fusionar `backlog`, `sprints` y `board`, que comparten el invariante de la regla 3b.

### M3. Alcance frente al objetivo del proyecto y documento inexistente - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** líneas 4, 13, 21, 55, 287; `plan-prompt.md` 22-34; README 9, 33
* **Discrepancy Description:** el plan omite lo que pide el prompt (comparativo de herramientas, MoSCoW, métricas de éxito, lead/cycle time, throughput, incremento) y lo difiere a un documento que no existe. F5 enlaza este plan desde el README como "plan generado". `column_changed_at` (línea 99) queda huérfano.
* **Rationale & Recommendation:** crear el documento complementario o declarar formalmente el recorte, y alinear el enlace del README.

### M4. Falta la alternativa "no construir" - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** líneas 21, 54, 191-263
* **Discrepancy Description:** el documento admite que no justifica construir frente a Jira o Linear, pero las alternativas A-L no la tratan; queda solo como pregunta abierta.
* **Rationale & Recommendation:** añadir esa alternativa o declarar el proyecto como de aprendizaje y dejar que condicione el alcance.

### M5. Historias sin invariantes y sin especificar en el Gantt - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** líneas 99, 103, 112-113, 151, 280, 316, 350
* **Discrepancy Description:** no se dice si una historia puede asignarse a un sprint o tener dependencias. El resumen de historia en el Gantt no aparece en `effective_dates`, el contrato JSON, el criterio F4 ni `test_gantt_dates`. No se define el caso sin tareas fechadas, ni `is_late` y `conflict` para historias (una historia con columna nula quedaría siempre como retrasada).
* **Rationale & Recommendation:** definir los invariantes o quitar el resumen del MVP.

### M6. Transferencia del PO indefinida y carrera aceptada - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`, `egm-zoom-out`
* **Affected Scope:** líneas 93, 128, 173, 312
* **Discrepancy Description:** promover a B mientras A es PO viola "un solo PO", y degradar a A primero deja el proyecto sin PO. La carrera de dos PO se acepta como "poco probable", aunque ya se usa un índice único sobre columna generada para el sprint activo.
* **Rationale & Recommendation:** operación atómica `transfer_product_owner(from, to)` y el mismo patrón de columna generada. Para ciclos de dependencias, `select_for_update` sobre `Project`.

### M7. Historia de sprint perdida y métricas de flujo no calculables - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** líneas 13, 55, 99, 129
* **Discrepancy Description:** al cerrar un sprint las tareas sin terminar quedan con `sprint` nulo y se pierde qué había en él. Sin eventos de movimiento no se pueden calcular lead time, cycle time ni burndown.
* **Rationale & Recommendation:** una tabla append-only `TaskEvent`, escrita solo desde `apply_placement` (único escritor), que sustituya a `column_changed_at`. Coste: una escritura extra por movimiento.

### M8. Matriz de permisos incompleta - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`, `egm-zoom-out`
* **Affected Scope:** líneas 105, 117-128, 140-142, 171
* **Discrepancy Description:** no se define quién crea o edita sprints, quién edita las notas de review y retro, ni quién gestiona dependencias y columnas. Un Developer edita "sus tareas", pero solo el PO asigna responsables, así que no se sabe quién crea las tareas de un Developer. Quitar a un miembro con tareas choca con `assignee` PROTECT. "El primer usuario crea el primer proyecto" contradice que cualquiera pueda crear proyectos. Faltan rutas para editar o borrar épicas e hitos pese a "crear y editar" en la matriz.
* **Rationale & Recommendation:** completar la matriz y las rutas y definir la baja de miembros.

### M9. Códigos de respuesta inconsistentes en unicidad - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** líneas 148, 157, 311, 349
* **Discrepancy Description:** formularios inválidos y correo repetido dan 422, pero el nombre duplicado de departamento da 409 y toda `IntegrityError` se traduce a 409.
* **Rationale & Recommendation:** validar unicidad en el formulario (422) y reservar 409 para carreras y conflictos de estado.

### M10. MySQL 8.0 posiblemente fuera de soporte - Severity: Major
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** líneas 82, 271, 290
* **Discrepancy Description:** a 2026-11-17 MySQL 8.0 habría llegado a fin de vida (abril de 2026; el revisor pidió confirmarlo).
* **Rationale & Recommendation:** confirmar y valorar 8.4 LTS, o justificar 8.0 de forma explícita.

## Nits

### N1. Restos narrativos del stack anterior - Severity: Nit
* **Reviewer Lens:** ambos
* **Affected Scope:** líneas 4, 48, 229-257
* **Discrepancy Description:** "reemplaza al JWT del plan anterior", "decisión anterior de este plan" y "plan anterior" remiten a un plan que un lector nuevo no ha visto. El estado "sin revisar tras el cambio" (línea 4) debe quitarse al cerrar la revisión.
* **Rationale & Recommendation:** describir las alternativas sin historial, o mover el historial a un registro de decisiones.

### N2. `column` definida en tareas sin sprint - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** líneas 112, 129
* **Discrepancy Description:** las tareas sin sprint tienen `column` aunque no se ven en el tablero, y al cerrar se reinicia.
* **Rationale & Recommendation:** `column` nula sin sprint, asignada solo en `assign_sprint`; elimina el reinicio y parte de la regla 3b.

### N3. Índices redundantes - Severity: Nit
* **Reviewer Lens:** ambos
* **Affected Scope:** líneas 181, 315, 321
* **Discrepancy Description:** `(sprint, column)` queda cubierto por `(project, sprint, column)`.
* **Rationale & Recommendation:** dejar uno.

### N4. Detalle de implementación en la sección de reglas - Severity: Nit
* **Reviewer Lens:** ambos
* **Affected Scope:** líneas 111, 301, 314
* **Discrepancy Description:** el reintento ante el error 1213, `init_command` y el SQL de la columna generada bajan de altura.
* **Rationale & Recommendation:** dejar el comportamiento en las reglas y el detalle en el plan detallado.

### N5. Abstracciones y dependencias de más - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** líneas 91, 134, 292, 301, 310
* **Discrepancy Description:** `core/htmx.py` genérico para un único uso (solo `move` es HTMX). `argon2-cffi` frente a los hashers por defecto de Django.
* **Rationale & Recommendation:** simplificar o justificar.

### N6. `--cov-fail-under=80` en `addopts` - Severity: Nit
* **Reviewer Lens:** ambos
* **Affected Scope:** línea 294
* **Discrepancy Description:** hace fallar `pytest` en F1 y en ejecuciones parciales.
* **Rationale & Recommendation:** aplicarlo solo en CI o desde F3 o F5.

### N7. `initdb/01-grants.sql` sin expansión de variables - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** líneas 289-291
* **Discrepancy Description:** los `.sql` de `docker-entrypoint-initdb.d` no expanden variables de entorno, así que no pueden usar `MYSQL_USER`.
* **Rationale & Recommendation:** usar un `.sh` o fijar el nombre en el SQL.

### N8. Estado del README y de la fase F5 - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** líneas 269, 287; README 9, 33, 37
* **Discrepancy Description:** la línea 269 dice que el README ya está actualizado, pero sigue diciendo "Solo existe el prompt". F5 manda poner "sin código" cuando ya habrá código. El README mínimo con instalación llega en F5 aunque F1 ya arranca. El idioma de los identificadores está fijado y a la vez abierto (línea 56 frente a README 37).
* **Rationale & Recommendation:** actualizar ahora, retirar la instrucción de F5, añadir un README mínimo en F1 y decidir el idioma.

### N9. Campos especulativos y semántica de WIP - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`, `egm-inventive-catalyst`
* **Affected Scope:** líneas 95, 97, 99, 100, 111
* **Discrepancy Description:** `TaskDependency.type` con un solo valor, `Epic` solo con `title`, `Task.position` sin reordenación dentro de la columna y `estimate_points` sin uso. No se define qué pasa si el SM baja `wip_limit` por debajo del conteo actual, ni si al editar columnas hay que definir `position` e `is_done`, ni qué ocurre sin columna `is_done`.
* **Rationale & Recommendation:** recortar o declarar el coste, y especificar el comportamiento.

### N10. Despliegue y registro abierto - Severity: Nit
* **Reviewer Lens:** `egm-inventive-catalyst`
* **Affected Scope:** líneas 48, 162, 171, 301
* **Discrepancy Description:** faltan `SECURE_PROXY_SSL_HEADER` y `CSRF_TRUSTED_ORIGINS` detrás de proxy HTTPS. El registro abierto, sin límite de intentos de login, queda más expuesto de lo que sugiere el texto.
* **Rationale & Recommendation:** añadir esos ajustes y valorar registro cerrado por defecto o un interruptor `REGISTRATION_OPEN`.

## Lo que está bien
Modelo de datos mínimo con fuente de verdad única para fechas, WIP en servidor con un solo escritor de `column` y `sprint`, respaldo sin JavaScript y plan B del Gantt, y reutilización de la plataforma Django (sesiones, CSRF, admin, ORM).
