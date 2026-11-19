# Zoom Out, Etapa 8 (intermedia): crecimiento de alcance y conflictos entre correcciones

**Objetivo:** `docs/designs/plan-implementacion.md` (452 líneas, revisado completo)

## Estado de revisores

| Revisor | Estado |
| --- | --- |
| `egm-zoom-out` | completed |

Insumos: `zoom_out_report.md`, `comprehension_report.md`, `critic_report.md`, `implementation_readiness_report.md`, `README.md` y `docs/plan-prompt.md`. No se reabren las decisiones fijadas por el autor (Django-only, sesiones Django, MySQL 8.4, monorepo, capas con operaciones de tareas en `backlog.services`, PO con todos los permisos de SM, `GeneratedField` + `UniqueConstraint` para un solo sprint activo, tabla de historial `SprintTask`, diferenciador frente a Jira/Linear).

**Veredicto:** el contexto es suficiente y el plan sigue siendo un MVP razonable. El riesgo ahora es que los informes anteriores proponen unas 25 correcciones, y varias se pisan o agregan mecanismos nuevos. Con un bloqueo por proyecto, tres recortes de reglas y ediciones de texto se resuelven los 3 Blockers de `implementation_readiness_report.md` y el del crítico.

---

## 1. Correcciones necesarias para el MVP frente a alcance innecesario

### 1.1 Necesarias (contradicciones o invariantes rotos; costo de una frase a pocas líneas)

| Corrección | Líneas | Por qué es necesaria |
| --- | --- | --- |
| Capas: `create_project` llama a `board.services` y `board` está por encima de `projects` | L65, L281, L367, L372, L400 | El plan se contradice. Blocker B2 en implementation_readiness; Major en zoom_out y comprehension. |
| `is_done` frente a `create_column` | L50, L100, L169, L373 | Blocker B1. "`is_done` es la última" no se cumple al crear columnas "al final". |
| E2E y fases: el paso 2 usa una página de F3; el paso 11 (F2) se ejecuta tras F4 sin mover nada a "Hecho" | L425, L434 | Contradice L299 ("cada fase deja el sistema ejecutable y probable"). Blocker B3 y Major M12. |
| Criterio F4 verificable solo en el JSON, no en la clase CSS | L181, L337-338, L391 | `pytest` no comprueba una clase que agrega `gantt.js`. |
| `assign_sprint` sin precondiciones | L134, L136 | Puede reabrir tareas terminadas y saltarse `ColumnTransition`; cita el WIP, que se especifica en F3. |
| Carrera mover frente a cerrar, y PO/ciclos concurrentes | L115, L134, L136, L179 | Blocker del crítico: puede dejar una columna sin sprint. Un solo mecanismo cubre todo (sección 3). |
| `GeneratedField` con la expresión literal (`output_field`, `db_persist`, nombre `active_project`, no `active_project_id`) | L99, L374 | Decisión fijada pero mal especificada: con un `ForeignKey` como `output_field`, MySQL rechaza la columna. |
| Conflicto de dependencia siempre verdadero dentro del mismo sprint | L116-117, L338, L411 | Caso más común en Scrum; el Gantt marcaría `conflict` en casi toda dependencia. |
| `is_late` con `column` nulo | L118 | Una tarea sin sprint con `due_date` vencida se marca retrasada sin serlo. |
| Fechas de `Sprint` nulables y `start` las exige | L99, L134 | Hay que decidir y escribirlo. |
| `from_column_id` y decorador o middleware que convierte excepciones en respuestas | L148, L163, L370 | Sin ellos no existe la ruta `columns/<id>/edit/` ni el 4xx. |
| `apps.get_model("backlog","Task")` lanza `LookupError` en F1 | L372 | `try/except` o `apps.is_installed` basta. |
| `.gitattributes` con `*.sh text eol=lf` | L352 | Sin él, el MySQL de Docker falla en Windows (M11). |
| Prohibir `product_owner` en `members/<id>/role/` | L145 | Protege el invariante del PO único sin un `GeneratedField` extra. |
| Reducir la promesa de `SprintTask` a "velocidad" | L38, L292, L442 | El plan promete burndown y métricas de flujo; `SprintTask` solo guarda el estado final. |
| Quitar "lo que hay que confirmar" sobre MySQL 8.0 | L303 | Dato ya decidido; hoy es 2026-11-17. |

### 1.2 Alcance añadido que no hace falta para el MVP (rechazar)

| Propuesta | Origen | Razón |
| --- | --- | --- |
| Tabla `TaskMove` o campo `done_at` | zoom_out, critic | Modelo y escritura nuevos en `apply_placement`. L37 excluye métricas de flujo y L442 las difiere. Basta con bajar la promesa. |
| `ProjectMember.is_active`, o `Task.assignee` apuntando a `ProjectMember` | zoom_out | Cambia el modelo y todas las consultas de miembros. Basta con acotar el 409 a tareas sin terminar. |
| Acción "tomar tarea" para Developer | zoom_out, critic | L128 ya deja mover una tarea sin responsable. Basta con que el PO asigne y el Developer no cree tareas. |
| Segundo `GeneratedField` + `UniqueConstraint` para el PO único | critic | El bloqueo por proyecto más validar el rol ya lo cubren. (No afecta al `GeneratedField` del sprint activo, que es decisión fijada.) |
| `UniqueConstraint(project, position)` | critic | Choca con insertar columnas (2.C). |
| Orden de bloqueo Sprint, Column, Task y reintento de deadlock | critic | Lo reemplaza el bloqueo único. |
| Tabla de firmas, retornos, excepciones y permiso por servicio | implementation_readiness M2 | Sube el nivel de detalle y empeora el anti-weeds. |
| `related_name`, `max_length`, `on_delete` por campo | implementation_readiness M7 | Detalle de implementación. |
| Respaldo `RunSQL` y `SeparateDatabaseAndState` | implementation_readiness M5, L374 | Especulativo; la prueba de migración (L403) ya detecta el problema. Quitar el texto. |
| `hx-sync`, `Vary: HX-Request`, `CONN_MAX_AGE`, colación, tarea operativa `clearsessions`, `CheckConstraint` por `kind` | critic | Innecesario para 50 usuarios; `board.js` ya reinicia Sortable en `htmx:load` (L390). |
| Presupuesto en paralelo a F4, `permissions.py` por app | zoom_out | Reordenar o repartir no resuelve un problema del MVP. |
| Reestructurar el documento (unir Decisiones, mover Supuestos y Límites, condensar las 16 alternativas, anclas) | critic | Trabajo editorial que renumera líneas e invalida las referencias de los informes. Hacerlo al final. |
| Healthcheck de Docker, `apps.py`, `admin.py`, `BASE_DIR` | implementation_readiness N6-N7 | El implementador lo resuelve. |

---

## 2. Conflictos entre correcciones

**A. WIP en `assign_sprint`.** zoom_out lo pone en `apply_placement`; implementation_readiness M1 extrae `_enforce_wip` a F2; critic exige bloquear también `BoardColumn`. Las tres añaden lógica de F3 a F2 y chocan con el caso "primera columna con `wip_limit = 0`". Salida: sección 3, punto 4.

**B. Mecanismo de bloqueo (cuatro versiones).** Plan actual (L115): fila de columna destino, `READ COMMITTED` y reintento de deadlock. critic: orden Sprint, Column, Task, más `CHECK`. zoom_out: `Project.select_for_update()` en todo escritor. implementation_readiness N1: releer la tarea tras bloquear la columna. Son incompatibles; mantener varias deja L115, L187, L408 y la nota de `update_column` con reglas distintas. El bloqueo por proyecto subsume a los demás.

**C. Insertar columnas y `position` único.** critic y zoom_out piden insertar antes de la columna `is_done`; critic añade `UniqueConstraint(project, position)`. Insertar exige renumerar y MySQL comprueba la unicidad fila a fila, así que el `UPDATE` falla a mitad. L169 supone una reordenación que no existe.

**D. Promesa de `SprintTask` y Non-Goals.** `TaskMove` contradice L37 y L442. Bajar la promesa a "velocidad" es coherente; `SprintTask.estimate_points` (L105) solo se justifica con velocidad.

**E. Baja de miembros.** `is_active`, `assignee` a `ProjectMember` y acotar el 409 son tres soluciones al mismo problema. La primera, combinada con un PO único por `GeneratedField`, interactúa con la baja del PO.

**F. Gantt frente a criterios y pruebas escritas.** Excluir el conflicto "mismo sprint" cambia el criterio F4 (L338) y la prueba L411 ("incluido el mismo día"). Hay que acotar ambos a tareas con fechas propias.

**G. Configuración de MySQL.** zoom_out: construir `DATABASES` desde `MYSQL_*`. implementation_readiness N4 y M8: mantener `DATABASE_URL`, usar `127.0.0.1`, codificar contraseñas y añadir la URL al `env` de pytest. Hay que elegir una vía.

**H. Developer.** implementation_readiness M9 fija la regla en `can_edit_task`; zoom_out y critic piden además "tomar tarea", que crea permiso y ruta nuevos que L128 hace innecesarios.

**I. Capas.** Subir `board` por debajo de `projects` (zoom_out, implementation_readiness) o llamar desde la vista (critic) son excluyentes. Una prueba AST de capas se solapa con la prueba de ciclos (L400). Orquestar desde la vista pierde atomicidad en `create_project`.

**J. Editorial frente a contenido.** La reestructuración (critic) y las tablas (implementation_readiness M2) tocan el mismo archivo; hacerlas antes que el contenido invalida los números de línea de los informes.

---

## 3. Conjunto mínimo de cambios

1. **Capas (L65, L281, L367).** Reordenar a `core`, `accounts`, `board`, `projects`, `sprints`, `backlog`, y encima `gantt` y `budget`. Los modelos de `board` ya usan cadenas: sin cambio de esquema. Mantener la prueba de imports con `django.setup()` antes de importar (L400). Si se conserva "una prueba lo verifica" (L281), añadir la comprobación de orden por AST; si no, quitar la frase.
2. **Columnas (L50, L100, L169, L373).** Opción preferida: retirar `create_column` del MVP; las 4 columnas se siembran y solo se editan nombre, WIP, política y transiciones. Desaparecen insert, siembra, `position` y el supuesto de L169; quitar la prueba L409. Opción B (decisión del autor): insertar antes de la columna `is_done` con transiciones bidireccionales hacia sus vecinas, sin `UniqueConstraint(position)`. En ambos casos `is_done` es inmutable y sale de `update_column`.
3. **Un bloqueo por proyecto (L115, L134, L136, L187, L408).** Todo escritor de `column`, `sprint`, dependencias o roles (`move_task`, `assign_sprint`, `close_sprint`, `start_sprint`, `add_dependency`, `transfer_product_owner`, edición de `wip_limit`) abre `atomic()` y toma `Project.select_for_update()` primero; luego relee la tarea y valida. Se eliminan bloqueo de columna, reintento de deadlock (1213) y la regla "sin leer tareas antes". Cubre ciclos concurrentes y PO duplicado: quitar esos dos límites conocidos (L179). Mantener la prueba de L408 y añadir mover frente a cerrar. Añadir un solo `CheckConstraint` `(sprint IS NULL) = (column IS NULL)`.
4. **`assign_sprint` (L109, L134, L136).** Solo vale con `sprint IS NULL` y hacia un sprint `planned`. Decisión del autor: esto impide agregar tareas a un sprint activo; a cambio desaparecen WIP en F2, `_enforce_wip` y el caso `wip_limit = 0`. Si se quiere permitir sprint activo, enviar la tarea por `move_task` y mover el WIP a F2. Añadir `assign_sprint(task, None)` para desasignar mientras el sprint sea `planned` (un sprint `planned` no se cierra y la tarea quedaría atrapada). Declarar en Límites conocidos que lo ejecutado en un sprint no se borra (L109).
5. **Permisos de Developer (L125, L128, L133, L145).** El Developer no crea tareas y edita solo las asignadas a él; solo PO y SM cambian `assignee`; el endpoint `role` rechaza `product_owner`.
6. **Baja de miembros (L109).** El 409 aplica solo a tareas asignadas que no estén en una columna `is_done`; documentar que el responsable de una tarea terminada puede quedar fuera.
7. **Sprint y Gantt (L99, L116-118, L338, L411).** `start_date` y `end_date` obligatorias al crear el sprint y editables solo en `planned`. `conflict = false` si ambas tareas heredan del mismo sprint. Acotar criterio F4 y prueba a fechas propias. `is_late` exige `column` no nulo. `dep_id` es el id de `TaskDependency` y debe pertenecer a la tarea de la URL.
8. **`GeneratedField` (L99, L374).** Escribir la expresión literal: `Case(When(status='active', then=F('project_id')))`, `output_field=BigIntegerField(null=True)`, `db_persist=False`. Dejar la prueba de migración (L403) y borrar el respaldo `RunSQL`.
9. **Sprints cerrados (L114, L385).** Las páginas leen `SprintTask` para sprints `closed`; es el único consumidor de esa tabla.
10. **Promesas (L38, L292, L442).** Cambiar a "velocidad por sprint"; burndown y métricas de flujo pasan a "requiere registrar movimientos" en fase 2.
11. **E2E y criterios por fase (L422-434, L323-329).** Verificar el paso 2 en F1 por la lista de proyectos o el admin; mover la página de columnas a F3. Reordenar la tabla por fase y añadir un paso que lleve una tarea a "Hecho" pasando por "En revisión". Mover el cierre de sprint después de F3. Aclarar que el criterio F2 "las terminadas conservan ambos" se prueba con datos preparados a mano.
12. **Cableado.** Resolvedor `from_column_id` (F3) y conversión común de excepciones (decorador o middleware). `apps.is_installed` para el `LookupError` de F1. Aceptar 403 y 404 en el manejador global de HTMX (L155, L390). Añadir `.gitattributes`. Entorno: una sola vía, construir `DATABASES` desde `MYSQL_*` y listar `.env` como requisito de las pruebas.
13. **Texto (L303).** Quitar "lo que hay que confirmar" de MySQL 8.0.
14. **Al final, solo editorial.** Unificar decisiones, recortar las alternativas M, N y P (L271-281, L289-293), aviso único de "premisa del autor". Alinear `plan-prompt.md` (comparativo, MoSCoW y métricas como "histórico" o retirados; L13, L21).

**Efecto neto:** se evitan `TaskMove`, `is_active`, un segundo `GeneratedField`, el reintento de deadlock, la tabla de firmas y el respaldo `RunSQL`. Se descartan o simplifican `create_column`, `position` y el WIP en F2. Las ediciones mínimas son: capas, un bloqueo, tres restricciones de reglas (`assign_sprint`, Developer, baja de miembros) y ediciones de texto.
