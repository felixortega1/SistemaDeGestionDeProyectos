# Consolidated Review Report — plan-implementacion.md (tercera revisión)

Documento: `docs/designs/plan-implementacion.md` (466 líneas). `FeatureRange` = 1-309, `DetailedRange` = 310-466.
Informes de cada etapa, en esta carpeta: `zoom_out_report.md` (5), `comprehension_report.md` (6), `critic_report.md` (7), `intermediate_zoom_out_report.md` (8), `implementation_readiness_report.md` (9). Revisiones anteriores en `../plan-v2-django-1/` y `../plan-v3/`.

## Veredicto
- **Converge.** No hay Blockers en ninguna etapa (0 en las etapas 5, 7 y 9). Las rondas anteriores terminaron con 3-4 Blockers; esta, con ninguno.
- **Lo que queda son huecos de redacción**, no de diseño: según la etapa 8, el plan queda listo con unas 10 ediciones de texto, sin modelos, rutas ni dependencias nuevas.
- **La etapa 9 verificó como correctos:** `GeneratedField` virtual con `UniqueConstraint` en MySQL 8.4, `CheckConstraint(condition=)`, `isolation_level` en `mysqlclient`, la API de HTMX 2 usada, y que las migraciones no tienen ciclos (`board` depende de `projects` por FK sin violar la regla de capas).

## 🔴 Blocker
Ninguno.

## 🟡 Major — acciones consolidadas (las 10 ediciones mínimas de la etapa 8)

| # | Acción | Origen |
| --- | --- | --- |
| M1 | **`assign_sprint` exige `task.sprint is None`** (422 si no); las ediciones de tarea y de sprint guardan con `update_fields` (no pisan `column`, `sprint` ni `status`). Declarar en Límites conocidos que no hay "desasignar" y que un error de planning se corrige iniciando y cerrando el sprint. Añadir pruebas. Sin esto, `assign_sprint` reabre tareas terminadas, se salta `ColumnTransition` y contradice "`SprintTask` se escribe una sola vez". | Etapas 5, 7, 8 (N1, N2, A1, C1, C4) |
| M2 | **Asignar responsable es un permiso explícito:** fila "Asignar responsable: PO y SM", el formulario del Developer excluye `assignee`; aceptar con una frase que el Developer mueve tareas sin responsable pero no las edita. | Etapas 5, 6, 7, 8 (N3) |
| M3 | **Fechas efectivas con fallback a NULL:** falta de inicio y fin → `sin fechas`; falta de uno → `una sola fecha`, con o sin sprint; sin fin efectivo, `is_late` es falso; `conflict` es falso solo si ambas heredan inicio y fin del mismo sprint (el caso mixto usa fechas efectivas); quitar `today` de `effective_dates`. | Etapas 5, 6, 7, 8 (N4, C6) |
| M4 | **Contrato de error de `move`:** `board.views.move` captura `Conflict` y `Unprocessable` y renderiza `_board.html`; el middleware cubre el resto con página de error y nunca devuelve el fragmento; `board.js` recarga el tablero ante cualquier respuesta distinta de 200, 409 o 422 (403, 404, 5xx, red); añadir `templates/error.html`. | Etapas 7, 8, 9 (N5) |
| M5 | **Eliminar el respaldo `RunSQL` de `sprints`** (código muerto que desincroniza el estado de migraciones, ya que `GeneratedField` quedó verificado); revisar a mano la migración generada; probar el índice único con un `update(status="active")` directo. | Etapas 8, 9 (N6) |
| M6 | **`create_column` toma el bloqueo del proyecto** (con `apps.get_model` o un helper en `core`, para no romper la regla de capas), columnas ordenadas por `(position, id)` y corregir el supuesto "gana la última escritura" de `position`. Sin `UniqueConstraint(project, position)`. | Etapas 7, 8 (N7, C2, C3) |
| M7 | **Una sola lista canónica de operaciones con bloqueo, cada una con su módulo** (`start_sprint` en `sprints`; `assign_sprint`, `move_task`, `close_sprint` en `backlog`; `create_column` en `board`); acotar "no hay deadlocks" a "entre ellas"; sustituir "sin consecuencias" por "el movimiento usa el valor leído; el nuevo rige desde el siguiente"; corregir el riesgo real (dos `transfer_product_owner` simultáneos) y declarar las carreras de dependencias, de miembros y de `set_transitions`. | Etapas 5, 7, 8 (N8, A4) |
| M8 | **`/admin/` y sesiones:** añadir `apps/accounts/admin.py` (registrar `User` y `Session` de solo lectura) o quitar la afirmación; `User` con `AbstractBaseUser + PermissionsMixin`. | Etapas 5, 8, 9 (N9) |
| M9 | **E2E ejecutable:** mover el cierre del sprint al final; el paso 8 se ejecuta después de liberar una plaza (hoy da 409 con "En desarrollo" en 3/3); fijar un `end_date` pasado en el paso 3 para ver una tarea retrasada; añadir un paso de presupuesto (F5). | Etapas 8, 9 (N10, C8) |
| M10 | **Ajustes menores de redacción:** rebajar "firmas de los servicios" a "firmas de los servicios principales"; línea de F3 para el cambio de redirección en `projects/views.py`; quitar "(MIT)" de la frase colectiva (HTMX 2 es 0BSD) y registrar licencias en `VERSIONS.md`; unificar los hitos ("se listan siempre y se dibujan si la prueba de concepto lo permite"); registrar la versión de `frappe-gantt` como salida de la prueba de concepto de F4. | Etapas 6, 8, 9 (N11, N12, A3) |

## 🟢 Nit — resumen
Vocabulario de dominio ausente de Términos (épica, historia, hito, fin-a-inicio) y definición de backlog frente a las historias; "política" usada para `ColumnTransition` y `policy_text`; permiso del paso 1 de la regla 3 frente al decorador de la regla 7; `dep_id` ambiguo; `position` sin numeración; pie "Drafted with EGM"; densidad de la regla 3 y de varios ítems; "Rejected by author" repetido; Nits de configuración (CSRF sin JavaScript, `CONN_MAX_AGE`, Python 3.12 y Windows/Linux); falta una prueba nombrada de la vista del Gantt.

## Qué no añadir (recomendación de la etapa 8)
`unassign_sprint` o cancelar sprints `planned`; `UniqueConstraint(project, position)`; tabla de firmas de todos los servicios y atributos `data-*`; bloqueos adicionales en dependencias, miembros o `set_transitions`; reescribir `READ COMMITTED` o añadir alternativas de bloqueo; `GeneratedField` para el Product Owner.

## Decisiones del autor
Ninguna nueva: todas las correcciones son coherentes con las decisiones ya tomadas. Único punto a confirmar: que **no haya "desasignar"** en el MVP (M1); un error de planning se corrige iniciando y cerrando el sprint.

## Matriz de trazabilidad (resumen)

| Hallazgo bruto | Acción consolidada |
| --- | --- |
| Etapa 5 Major 2; Etapa 6 #3; Etapa 7 F3-F4; Etapa 9 (assign sobre tarea con sprint) | M1 |
| Etapa 5 Major 1; Etapa 6 #3; Etapa 7 F6 | M2 |
| Etapa 5 Major 4; Etapa 6 #25-27; Etapa 7 F5; Etapa 9 (`conflict`, `effective_dates`) | M3 |
| Etapa 5 Major 6; Etapa 9 Major (`board.js`, excepciones) | M4 |
| Etapa 9 Major (RunSQL); Etapa 6 #5 | M5 |
| Etapa 5 Major 5; Etapa 7 F2 | M6 |
| Etapa 6 #4, #28; Etapa 7 F7-F9 | M7 |
| Etapa 5 Major 6; Etapa 9 (`/admin/` falso) | M8 |
| Etapa 6 #1; Etapa 9 (E2E) | M9 |
| Etapa 6 #12-19; Etapa 9 (licencia, fases) | M10 y Nits |
