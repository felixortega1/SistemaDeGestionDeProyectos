# Consolidated Review Report — plan-implementacion.md (segunda revisión, versión Django)

Documento: `docs/designs/plan-implementacion.md` (451 líneas). `FeatureRange` = 1-296, `DetailedRange` = 297-451.
Informes de cada etapa, en esta carpeta: `zoom_out_report.md` (5), `comprehension_report.md` (6), `critic_report.md` (7), `intermediate_zoom_out_report.md` (8), `implementation_readiness_report.md` (9). La revisión anterior está en `../plan-v2-django-1/`.

## Veredicto
- **Mejora respecto a la primera revisión:** los 3 Blockers anteriores (roles, orden de fases, ciclo de imports de modelos) están resueltos. Ahora hay 1 Blocker de diseño (concurrencia) y 3 de preparación, casi todos autoinfligidos por las correcciones anteriores.
- **Plan de implementación:** **sigue sin estar listo**, pero lo que falta es corregir contradicciones internas, no añadir diseño: capas violadas por el propio plan, `create_column` frente a `is_done`, un E2E que no se puede ejecutar fase por fase y un criterio de F4 no verificable con pytest.
- **Etapa 8:** 16 correcciones son necesarias; ~10 añaden alcance y se recomienda no aplicarlas.

## 🔴 Blocker — acciones consolidadas

| # | Acción | Origen |
| --- | --- | --- |
| B1 | **Carrera entre `move_task` y `close_sprint`/`assign_sprint`.** Las validaciones de los pasos 2-4 se hacen antes de bloquear nada, `close_sprint` no bloquea y el invariante sprint/columna no tiene `CHECK`. Mínimo (etapa 8): un solo bloqueo `Project.select_for_update()` por proyecto en las tres operaciones que escriben `sprint`/`column`, releyendo la tarea dentro del bloqueo, más un `CheckConstraint` (sprint y column ambos nulos o ambos con valor). Quitar el orden de locks y el reintento de deadlock. | Etapas 7, 8 |
| B2 | **Capas violadas por el plan.** `projects.create_project` llama a `board.services.create_default_board`, pero `board` está por encima de `projects`. Reordenar: `accounts`, `board` (solo depende de `Project` por cadena), `projects`; o que la vista cree el tablero. `test_imports` debe comprobar el orden de capas, no solo ciclos, y llamar a `django.setup()`. | Etapas 5, 7, 8, 9 |
| B3 | **`create_column` rompe `is_done`.** Una columna nueva se añade al final, pero la regla dice que `is_done` es la última, y `update_column` edita `is_done` aunque la decisión dice que solo se editan nombre, WIP y política. Decisión del autor (ver abajo). | Etapas 5, 6, 8, 9 |
| B4 | **E2E no ejecutable por fase.** El paso 2 (F1) depende de la página de columnas (F3); el paso 11 (cerrar sprint, F2) viene después de pasos de F3/F4 y ningún paso deja una tarea terminada. Reordenar los pasos por fase y añadir el paso "mover a Hecho" (F3) antes del cierre; en F1 el paso 2 se comprueba en el admin o con una prueba. | Etapas 5, 6, 9 |

## 🟡 Major — acciones consolidadas

**Reglas y modelo (necesarias según la etapa 8):**
- **`assign_sprint`.** Se permite saltarse transiciones y no hay forma de desasignar. El WIP de `assign_sprint` (F2) vive en `move_task` (F3). Decisión del autor (ver abajo).
- **`is_late` y `column` nulo.** Una tarea sin sprint nunca está "terminada" y se marcaría retrasada. Definir: `is_late` solo para tareas con columna.
- **Conflicto de dependencias dentro del mismo sprint.** Con la regla "anterior o igual", dos tareas encadenadas con las fechas del sprint son siempre conflicto. Definir que una dependencia entre tareas con las mismas fechas heredadas del sprint no marca `conflict`, o que `conflict` solo aplica si ambas tienen fechas propias.
- **Fechas del `Sprint`.** Declarar cuáles admiten nulo (`start_date`, `end_date` obligatorias solo al iniciar) y el `name` de la ruta de dependencias (`dep_id`).
- **Developer.** No queda claro cómo toma una tarea sin responsable; fijar que el Developer no crea tareas (la matriz ya dice "solo sus tareas"), y rechazar `product_owner` en el endpoint de rol (solo `transfer_product_owner` crea PO).
- **Baja de miembros.** Hoy un miembro con tareas terminadas no se puede quitar nunca. El 409 solo para tareas sin terminar; las terminadas quedan con `assignee` conservado.
- **`SprintTask` y las promesas.** No soporta burndown ni métricas de flujo (solo estado al cierre). Reducir la promesa a "velocidad" en la Alternativa P y en Future Improvements; guardar solo para sprints cerrados.
- **`GeneratedField`.** Dar la expresión literal (`Case(When(status="active", then=F("project_id")), default=None)`) y `output_field`; unificar `active_project` y `active_project_id` (el respaldo SQL usa otro nombre). La etapa 8 propone quitar el respaldo `RunSQL`; la etapa 9 lo marca incoherente: o se unifica el nombre o se quita.
- **Tareas con historial** (`SprintTask`) no se pueden borrar: está dicho; aclarar la ruta de borrado en la página.

**Plan de implementación:**
- **Criterio F4.** `is_late` en el HTML no se puede verificar con pytest (la clase la pone `gantt.js`): verificar el JSON de la página (`is_late: true` en los datos) y el resto a mano.
- **Cableado y archivos que faltan:** resolvedor `from_column_id`, conversión de excepciones a respuestas (middleware o decorador en `core`), `.gitattributes` con `*.sh text eol=lf` (el `.sh` de Docker falla con CRLF en Windows), `apps.get_model("backlog", "Task")` falla en F1 (`LookupError`: la comprobación se activa en F2), configuración de pruebas.
- **Versiones y archivos de `frappe-gantt`, HTMX y SortableJS** siguen sin fijarse: fijarlas al empezar cada fase, y decidir cómo se combinan `is_late` y `conflict`.
- **`DATABASE_URL` vs `MYSQL_*`:** una sola fuente (construir `DATABASE_URL` desde `MYSQL_*` en `docker-compose` o documentar que deben coincidir).
- **MySQL 8.0:** quitar el "hay que confirmar"; hoy es noviembre de 2026 y el plan fija 8.4.

**Estructura y estilo (hacer al final, tras corregir el contenido):**
- Technical Plan mezcla contenidos; las decisiones del autor están duplicadas; las reglas 3, 8 y 10 se repiten; párrafos densos; Overview sobrecargado; premisas "sin respaldo" repetidas.
- Referencias cruzadas sin enlace ("regla 4", "Alternativa O", "ver Supuestos"); "fase 2" vs "F2"; "prompt", MoSCoW, "operador", "Daily" y términos de HTMX y frappe-gantt sin definir; fila "Crear un proyecto" de la matriz con celdas vacías; hitos sin propósito claro.

## 🟢 Nit — resumen
Configuración de MySQL/Django (colación, `CONN_MAX_AGE`), `CASCADE` e índices innecesarios, una Open Question sin consumidor, desajuste con `plan-prompt.md`, `APP_TIMEZONE` sin valor por defecto, formato de los pares `from_to` de transiciones, ruta para corregir hitos, tono y afirmaciones sin calibrar, exceso de alternativas.

## Qué no añadir (recomendación de la etapa 8)
`TaskMove`/`done_at`, `ProjectMember.is_active`, "tomar tarea", segundo `GeneratedField` para el PO, `UniqueConstraint(position)`, orden de bloqueo más reintento de deadlock, tabla de firmas de servicios, `related_name`/`max_length` por campo, `hx-sync`, `Vary`, `clearsessions`, y la reestructuración editorial antes de corregir el contenido.

## Decisiones del autor
1. **`create_column` frente a `is_done` (B3).** Opción A: retirar `create_column` del MVP (las columnas se editan, no se crean; las 4 por defecto bastan). Opción B: permitir crear columnas insertándolas siempre antes de la columna `is_done`, sin `UniqueConstraint` sobre `position`.
2. **`assign_sprint`.** Opción A: solo desde "sin sprint" hacia un sprint `planned` (más una acción para desasignar), de modo que el WIP nunca se aplica al asignar y la regla se simplifica. Opción B: mantener asignación a sprint activo con WIP, lo que obliga a mover el WIP a F2.
3. **Bloqueo (B1):** un bloqueo por proyecto (etapa 8) frente al bloqueo de la columna destino actual más protocolo de orden (etapa 7).

## Conflictos entre correcciones (etapa 8)
A. WIP en `assign_sprint` vs F2/F3. B. Cuatro mecanismos de bloqueo propuestos. C. Insertar columnas vs `position` único. D. `TaskMove` vs Non-Goals. E. Tres soluciones a la baja de miembros. F. Gantt vs criterios ya escritos. G. `DATABASE_URL` vs `MYSQL_*`. H. Developer. I. Capas por vista vs reordenar. J. Edición editorial vs contenido.

## Matriz de trazabilidad (resumen)

| Hallazgo bruto | Acción consolidada |
| --- | --- |
| Etapa 7 Blocker; Etapa 8 (bloqueo por proyecto) | B1 |
| Etapa 5 Major 1; Etapa 7 Major; Etapa 9 Blocker 2 | B2 |
| Etapa 5 Major 2; Etapa 6 #1; Etapa 9 Blocker 1 | B3 |
| Etapa 5 Major 3; Etapa 6 #4-5; Etapa 9 Blocker 3 | B4 |
| Etapa 5 Major 5; Etapa 6 #3 | `assign_sprint` |
| Etapa 6 #10; Etapa 5 Major 10 | `is_late` y `column` nulo |
| Etapa 7 Major (conflicto de dependencias) | Conflicto en el mismo sprint |
| Etapa 5 Major 9; Etapa 7 Major | `SprintTask` y promesas |
| Etapa 9 Majors (GeneratedField, CRLF, `LookupError`, `from_column_id`) | Cableado y archivos |
| Etapa 7 Major (estructura); Etapa 6 #15-24 | Estructura y estilo |
