# Consolidated Review Report — plan-implementacion.md (versión Django)

Documento: `docs/designs/plan-implementacion.md` (384 líneas). `FeatureRange` = 1-266, `DetailedRange` = 267-384.
Informes de cada etapa, en esta carpeta: `zoom_out_report.md` (5), `comprehension_report.md` (6), `critic_report.md` (7), `intermediate_zoom_out_report.md` (8), `implementation_readiness_report.md` (9). Los informes de la versión FastAPI están en `../plan-v1-fastapi/`.

## Veredicto
- **Especificación (1-266):** el cambio a Django no dejó restos funcionales de FastAPI, React ni JWT. Pero el modelo de roles hace inejecutable el flujo con un solo usuario, y el ciclo de vida de `column` y `sprint` se contradice entre reglas.
- **Plan de implementación (267-384):** **no está listo.** El orden de las fases no es ejecutable (`apply_placement` y `get_board` están en F3 y F2 los necesita), hay un ciclo de imports entre apps y varias configuraciones no funcionarían tal como están escritas.
- **Etapa 8:** de unas 60 correcciones propuestas, 16 son necesarias y 13 añaden alcance que un MVP sin código no necesita. El conjunto mínimo son 10 ediciones de texto, sin modelos ni apps nuevos.

## 🔴 Blocker — acciones consolidadas

| # | Acción | Origen |
| --- | --- | --- |
| B1 | **Roles.** Hoy el creador es Product Owner y solo el Scrum Master abre sprints y edita columnas, así que un solo usuario no puede ejecutar el E2E. Decisión mínima: el PO tiene también los permisos del SM. Completar la matriz con crear sprints, notas de review/retro y dependencias. | Etapas 5, 7, 9; Etapa 8 (cambio 1) |
| B2 | **Orden de fases.** Mover `apply_placement` y `get_board` a F2 y dejar en F3 `move_task`, las vistas y `board.js`. Repartir `test_roles` y `test_isolation` por fase, y marcar los archivos que se modifican en cada fase (`settings.py`, `urls.py`, `core/permissions.py`, `base.html`). En F1, `/projects/<id>/` redirige a la lista de proyectos. | Etapas 5, 6, 9; Etapa 8 (cambios 2 y 8) |
| B3 | **Ciclo de imports entre `backlog`, `board`, `sprints` y `core`.** Escribir una jerarquía de capas (`accounts`, `projects`, `board`, `sprints`, `backlog`, `budget`) o fusionar `backlog`, `sprints` y `board`; hacer que `core.permissions` no importe modelos de apps posteriores en el nivel del módulo. Es una decisión de arquitectura del autor (ver "Decisiones del autor"). | Etapas 5, 6, 9 |

## 🟡 Major — acciones consolidadas

**Modelo y reglas (todas son ediciones de texto, según la etapa 8):**
- **Tareas sin sprint e historias.** Dejar `column` nula en tareas sin sprint y asignarla solo en `assign_sprint`; el cierre deja `sprint` y `column` nulos. Solo las tareas (`kind=task`) van a sprint y tienen dependencias; el Gantt dibuja solo tareas y se retira el resumen de historia. Esto elimina las contradicciones de la regla 3b, la 8 y el tablero.
- **Campos sin uso.** Quitar `column_changed_at`, `position` (ordenar por `id`) y `TaskDependency.type`; declarar las métricas de flujo como Non-Goal.
- **Orden de validaciones en `move`:** permiso, columna destino, `kind=task`, sprint activo, misma columna (200), transición (422), WIP (409).
- **Códigos HTTP:** 422 para errores de formulario y de unicidad; 409 solo para estado y carreras (WIP, segundo sprint activo, borrados protegidos).
- **Reglas de una frase:** `wip_limit` se valida solo al entrar; transferencia atómica del Product Owner; quitar un miembro con tareas asignadas devuelve 409; reescribir "el primer usuario crea el primer proyecto" (cualquier usuario puede crear proyectos); sesión expirada en una petición HTMX.
- **Columnas y transiciones:** definir la creación (se añade al final y siembra la transición con la antigua última), unicidad de posición y que la "primera columna" es la de menor `position`.
- **Rutas:** "crear y listar" para épicas e hitos en el MVP; distinguir cambiar rol y quitar miembro; nombres de URL y excepciones de servicio (`core/exceptions.py`).
- **Formularios:** completar campos de tarea (`kind`, `parent`, `description`, `assignee`) y campos nulos de `Sprint`.

**Concurrencia y plataforma:**
- **WIP y aislamiento.** Con REPEATABLE READ, una lectura previa al `select_for_update` puede fijar un snapshot y el conteo ignoraría un commit concurrente. Fijar `isolation_level = "read committed"`, el orden dentro de `atomic()` (bloquear columna, contar, actualizar), que el reintento de deadlock envuelva todo el bloque, y una prueba de concurrencia. No ampliar el protocolo de bloqueos (etapa 8).
- **MySQL 8.0 está fuera de soporte** (fin de vida: abril de 2026, según el revisor, sin verificar). Confirmar y fijar MySQL 8.4 LTS; mantener el mínimo 8.0.16 por los `CHECK`.
- **Controlador de MySQL.** Elegir una sola opción (`mysqlclient` con rueda binaria, o PyMySQL con el parche en `config/__init__.py` y `cryptography`); hoy el fallback no tiene archivo ni dependencia asignados. El desarrollo es en Windows.
- **Docker.** `01-grants.sql` no expande variables: usar un `.sh` que lea `$MYSQL_USER`, o un nombre fijo; documentar que corre solo con el volumen vacío.
- **Columna generada.** Usar `GeneratedField` más `UniqueConstraint`, o justificar `RunSQL` e incluir el DDL de ida y vuelta y prohibir migraciones posteriores sobre `status` y `project`.
- **Settings y entorno.** Cómo se carga `.env` (`read_env`), el diccionario final de `DATABASES`, entorno mínimo de pytest (`SECRET_KEY`), `LOGIN_REDIRECT_URL`.
- **Frontend (JS).** SortableJS se destruye al reemplazar el tablero con HTMX: `board.js` debe reinicializar de forma idempotente en `htmx:load`, con selector de destino y URL de movimiento en un `data-`. Para `frappe-gantt`, fijar la versión antes de cerrar la lista de archivos (los nombres de archivo y opciones cambian entre 0.6.x y 1.x) y definir cómo se dibujan hitos y combinan `is_late` y `conflict`.
- **Permisos a nivel de objeto:** `can_edit_task` y `can_move_task` en `core.permissions` y cómo llega el proyecto a la vista.

**Documentación y alcance:**
- **README.** El plan dice que está "ya actualizado" pero el README real aún dice "Solo existe el prompt" y "Plan generado: pendiente". Corregir la frase y actualizar el README en F1; dejar el estado en un único lugar.
- **E2E por fase.** Indicar qué pasos aplican a cada fase (F1: 1-2; F2: 3 y 10; F3: 4-7; F4: 8-9) e indicar qué usuario ejecuta cada paso.
- **Recorte declarado.** Decir en el plan que el análisis comparativo, MoSCoW y métricas de éxito del prompt quedan fuera de este documento.
- **"Plan anterior" y "sin revisar".** Quitar las referencias al stack anterior y el "sin revisar" del estado; cerrar la pregunta de idioma del código (en conflicto con el README).
- **Mezcla de idiomas en encabezados**, numeración "3b" y tabla anidada en una lista (etapa 7).

## 🟢 Nit — resumen
`--cov-fail-under=80` en `addopts` (moverlo fuera, a un comando o a F5); `Client(enforce_csrf_checks=True)` para la prueba de CSRF; grafo de migraciones y `test_migrations` con `transaction=True` (el DDL de MySQL no es transaccional); `base.html` carga `board.js` y `gantt.js` desde F1 (usar un bloque por página); `.gitignore` con `.coverage`, `.pytest_cache/`, `.ruff_cache/`, `htmlcov/`; `CheckConstraint(condition=…)` en Django 5.1+; `admin.py`; política de borrado incompleta (`Sprint`, `Task`, `TaskDependency`); conflicto de dependencias con fechas inclusivas; credenciales duplicadas entre `DATABASE_URL` y `MYSQL_*`; orden de tarjetas; contrato de `undated` e hitos; cobertura de estilo (listas en lugar de celdas largas, "plaza", "conexiones reales", prefijo "Rejected by author:" repetido).

## Qué no añadir (recomendación de la etapa 8)
`TaskEvent`, `SprintTask`, roles como conjunto, columna generada para un solo PO, bloqueos sobre `Project` o `Sprint`, `isolation_level` más reintento 1205, manejadores HTMX generales, claves foráneas compuestas, documento comparativo, la alternativa "no construir" (basta una línea en Open Questions), CRUD completo de épicas, hitos, columnas y sprints, y la checklist de despliegue completa (una línea en Supuestos).

## Decisiones del autor (conflictos entre revisores)
1. **Ciclo de imports (B3):** jerarquía de capas con `apply_placement` en `backlog.services` (que es dueño de `Task`), o fusionar `backlog`, `sprints` y `board` en una sola app.
2. **Roles (B1):** el PO hereda los permisos del SM (recomendado por la etapa 8) frente a roles combinados por usuario (etapa 5, rechazado por añadir alcance).
3. **Columna generada:** `GeneratedField` (etapas 7 y 9) frente a `RunSQL` (plan actual); la etapa 8 lo considera opcional.
4. **MySQL 8.4:** cambio de versión que sugiere la etapa 9; la etapa 8 pide confirmar primero la fecha de soporte.
5. **Historial de sprints (`SprintTask`) y Jira o Linear:** siguen abiertos, sin cambios.

## Matriz de trazabilidad (resumen)

| Hallazgo bruto | Acción consolidada |
| --- | --- |
| Etapa 5 Blocker (rol único); Etapa 7 Major 1; Etapa 9 Blocker 3 | B1 |
| Etapa 5 Major (orden de fases); Etapa 6 #24-25; Etapa 9 Blocker 2 y Major de core/permisos | B2 |
| Etapa 5 Major (ciclos entre apps); Etapa 6 #26; Etapa 9 Blocker 1 | B3 |
| Etapa 6 Blockers 1-3; Etapa 5 (historias); Etapa 7 (historias y `assign-sprint`) | Tareas sin sprint e historias |
| Etapa 6 #35; Etapa 7 (`position`, métricas) | Campos sin uso |
| Etapa 6 #11; Etapa 5 (422 vs. 409) | Códigos HTTP |
| Etapa 7 (aislamiento y lock del WIP); Etapa 9 Major | WIP y aislamiento |
| Etapa 9 Majors (Docker, PyMySQL, MySQL 8.0, `GeneratedField`, SortableJS, `frappe-gantt`, settings) | Concurrencia y plataforma |
| Etapa 9 Majors (README, E2E); Etapa 6 #31-32 | Documentación y alcance |
| Etapa 8 §2 | Qué no añadir |
