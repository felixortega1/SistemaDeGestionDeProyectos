# Consolidated Review Report — plan-implementacion.md

Documento: `docs/designs/plan-implementacion.md` (308 líneas). `FeatureRange` = 1-193, `DetailedRange` = 194-308.
Informes de cada etapa, en esta misma carpeta: `zoom_out_report.md`, `comprehension_report.md`, `critic_report.md`, `intermediate_zoom_out_report.md`, `implementation_readiness_report.md`.

## Veredicto
- **Especificación (1-193):** el diseño es coherente (tarea como fuente de verdad) pero no cumple el estándar: faltan riesgos y supuestos, y la garantía del WIP falla en concurrencia.
- **Plan de implementación (194-308):** **no está listo.** Falla la regla de cero decisiones: faltan esquemas, contratos de API, mapeo de fases a archivos y hay errores técnicos que romperían la primera ejecución.
- **Etapa 8:** de unas 40 correcciones propuestas, unas 8 son necesarias. Las demás añaden alcance que un MVP sin código no necesita.

## 🔴 Blocker — acciones consolidadas

| # | Acción | Origen |
| --- | --- | --- |
| B1 | **Rediseñar el bloqueo del WIP.** Bloquear con `FOR UPDATE` la fila de `board_columns` destino y luego contar; índice `(sprint_id, column_id)`; definir `count >= limit`, `wip_limit` nulo o 0, y el movimiento a la misma columna como no-op; mapear deadlocks; prueba de concurrencia con sesiones y datos confirmados (no rollback por prueba). | Etapas 5, 7, 8, 9 |
| B2 | **Cerrar las vías que esquivan el WIP.** `column_id` y `sprint_id` fuera de `PATCH /tasks/{id}`; asignar a sprint y cerrar pasan por el servicio del tablero; tarea nueva en la primera columna; al cerrar, reiniciar `column_id` a la primera. Excluir también `status` del `PATCH` de sprints. | Etapas 5, 7, 8, 9 |
| B3 | **Añadir "Risks & Mitigations"** (5 a 7 filas) y supuestos de escala y seguridad. | Etapas 7, 8 |
| B4 | **Corregir dos errores técnicos:** `sub` del JWT como cadena y algoritmo fijado; añadir `cryptography` y el formato de `DATABASE_URL` para PyMySQL con MySQL 8. | Etapa 9 |
| B5 | **Esquema exacto por tabla** (tipos, nulabilidad, `ON DELETE`, índices, marcas de tiempo, claves primarias de `task_dependencies`) y política de borrado. | Etapas 7, 9 |
| B6 | **Contratos de API** (cuerpos, respuestas, errores 409 y 422, `GET /board`, `GET /gantt`, `PATCH`, `PUT` de transiciones, asignación a sprint). | Etapa 9 |
| B7 | **Invariantes de tarea y de sprint** (mismo proyecto, jerarquía historia/tarea, estados permitidos, códigos HTTP) y **matriz de permisos** rol por endpoint, con la resolución del proyecto en `/tasks/{id}`, `/sprints/{id}` y `/departments/{id}`. | Etapas 6, 7, 9 |
| B8 | **Mapear cada archivo a una fase** y dejar cada fase compilable y probable (incluido el frontend de la fase 1). | Etapa 9 |

## 🟡 Major — acciones consolidadas

- **Autenticación (decisión de alcance):** la etapa 8 recomienda quitar `POST /auth/refresh` y la renovación automática y usar un solo access token, documentando la falta de revocación, `sessionStorage` y el registro abierto (quién se registra y quién crea el primer proyecto). La etapa 5 propone lo contrario: refresh rotativo con cookie `HttpOnly`. **Conflicto abierto: lo decide el autor.**
- **Semántica de `tasks`:** definir si las historias tienen columna y cuentan para el WIP (más simple: solo las tareas con columna aparecen en el tablero y cuentan; las historias son contenedores) y para qué sirve `estimate_points`.
- **Fechas del Gantt:** casos de una sola fecha, inicio posterior al fin, zona horaria de la instalación, tipo `date`, semántica de `conflict` e `is_late`, y fuentes de inicio y fin por separado. Hitos: cómo se dibujan.
- **Transiciones:** cerrar la pregunta abierta (por defecto solo columnas contiguas; el Scrum Master las edita; "Por hacer → Hecho" se rechaza) y definir el ciclo de vida (crear una columna siembra sus transiciones; borrar columnas no se admite en el MVP).
- **Marcas de tiempo:** `created_at`, `updated_at` en tareas, `updated_by` y `updated_at` en departamentos y una marca de cambio de columna. Sin tabla `sprint_tasks`.
- **Dependencias y archivos:** fijar versiones (Python, Node, MySQL ≥ 8.0.16, librerías), completar `package.json`, añadir los archivos que faltan (`Base`, `modules/__init__.py`, configuración de pytest y ruff, `initdb`, tipos de `frappe-gantt`, etc.) y los comandos de arranque.
- **`frappe-gantt`:** verificar `destroy`, `readonly`, hitos y tipos antes de comprometer la fase 4; filtrar dependencias hacia tareas sin fecha; definir plan B.
- **Capa de servicios:** decidir qué servicio crea las columnas por defecto (evitar importaciones circulares), commit dentro del servicio, y handlers `def` frente a `async def`.
- **Pruebas:** completar los huecos (valores por defecto del proyecto, PO único, dependencias, mismo proyecto, migración arriba y abajo, aislamiento entre proyectos con una sola prueba, frontend 401 y 422).
- **Frontend:** rutas anidadas bajo `/projects/:id/`; página para editar columnas, WIP y transiciones (rol Scrum Master).
- **Problema y alcance del documento:** una frase en el Overview que diga que es solo el plan de implementación y dónde irán análisis comparativo, MoSCoW y métricas; actualizar "Plan generado: pendiente" del README. La pregunta de Jira o Linear sigue abierta: o se cierra con una alternativa, o se marca la sección como incompleta.
- **Redacción:** definir "área" = departamento en el primer uso; arreglar las referencias colgantes ("las tres opciones", "opción 1 con `project_budgets`"); calificar "no pueden contradecirse" y "sin pasos manuales" con la excepción de las tareas con fechas propias; unificar el idioma de encabezados y marcadores; unificar las menciones repetidas de una misma regla.

## 🟢 Nit — resumen
Enlaces rotos de la línea 13 (`../../README.md`, `../plan-prompt.md`); "punto 7" → "regla 7"; renumerar "36b"; `verify` de argon2 lanza excepción; validación de moneda es solo de formato; tipos del frontend generados desde OpenAPI (sin CI); mencionar `OAuth2PasswordBearer`; acortar alternativas B, C, E y H; política de edición concurrente de `position`.

## Qué no añadir (recomendación de la etapa 8)
`sprint_tasks`, tabla `refresh_tokens`, claves foráneas compuestas, prueba que recorre las rutas, transiciones por excepciones, más entradas en "Alternatives", y la bandera `outside_sprint`.

## Conflictos entre revisores que decide el autor
1. **Refresh**: quitarlo (etapa 8) o rotarlo con cookie (etapa 5).
2. **Bloqueo**: fila de columna (etapas 8 y 9) frente a fila del sprint o del proyecto (otras propuestas).
3. **Historial de sprints**: sin tabla (etapa 8) frente a `sprint_tasks` (etapas 5 y 7).
4. **Fechas híbridas**: se mantienen (decisión del autor), pese a los avisos de simplificarlas.

## Matriz de trazabilidad (resumen)

| Hallazgo bruto | Acción consolidada |
| --- | --- |
| Etapa 5 Zoom Out 2; Catalyst 3; Etapa 7 Blocker 2; Etapa 9 Blocker 5 | B1 |
| Etapa 5 Catalyst 2; Etapa 7 Major 3; Etapa 9 Blocker 6 | B2 |
| Etapa 7 Blocker 1; Etapa 8 §4.4 | B3 |
| Etapa 9 Blocker 1 y 2 | B4 |
| Etapa 7 Major 4; Etapa 9 Blocker 3 | B5 |
| Etapa 9 Blocker 4 | B6 |
| Etapa 6 Major 5 y 6; Etapa 5 Zoom Out 3; Etapa 9 Blocker 6 y 7 | B7 |
| Etapa 9 Blocker 8 | B8 |
| Etapa 5 Zoom Out 5; Catalyst 1; Etapa 7 Major 6; Etapa 8 §1.1 | Conflicto de autenticación |
