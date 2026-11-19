# Goldfish Review Report — resolución (plan-implementacion.md, versión Django)

Status: resolved. Decisiones del autor: jerarquía de capas, PO con permisos de SM, `GeneratedField` con `UniqueConstraint` (respaldo `RunSQL`), MySQL 8.4 LTS.

## Aplicado
- **B1 Roles:** el PO tiene los permisos del SM; matriz completada (crear proyecto, borrar tareas, sprints, dependencias); `transfer_product_owner` atómico; `can_edit_task` y `can_move_task`.
- **B2 Fases:** `apply_placement`, `assign_sprint` y `close_sprint` en F2; `move_task` y `get_board` en F3; pruebas de roles y aislamiento por fase; ítems de cada fase que modifican `settings`, `urls`, `base.html`, `styles.css` y `core/permissions.py`; `/projects/<id>/` redirige a la lista en F1.
- **B3 Ciclo de imports:** orden de capas, operaciones sobre tareas en `backlog.services`, `core.permissions` con `apps.get_model`, `tests/test_imports.py`. Alternativa N documenta el rechazo de fusionar apps.
- Tareas sin sprint sin columna; historias fuera de sprint, dependencias y Gantt; quitados `position`, `column_changed_at` y `TaskDependency.type`.
- Orden de validaciones en `move`, `READ COMMITTED`, bloqueo antes de leer tareas, reintento de todo el bloque, límite WIP solo al entrar.
- 422 para unicidad de formulario; 409 para estado y carreras; excepciones en `core/exceptions.py`.
- Rutas de miembros y columnas desambiguadas; épicas e hitos solo crear y listar; sesión expirada en HTMX (401 con `HX-Redirect`).
- `mysqlclient` como único controlador; MySQL 8.4; `initdb` como `.sh`; settings y entorno de pytest especificados; cobertura fuera de `addopts`; `enforce_csrf_checks`; prueba de migraciones con `transaction=True`.
- `board.js` idempotente tras `htmx:load`; `frappe-gantt` con versión fijada antes de F4 y plan B detallado.
- E2E como tabla por fase con un solo usuario; README corregido; referencias al plan anterior quitadas; idioma del código cerrado; recorte del prompt declarado.

## No aplicado (recomendación de la etapa 8)
`TaskEvent`, `SprintTask`, roles como conjunto (Alternativa M), columna generada para un solo PO, bloqueos ampliados, manejadores HTMX generales, claves foráneas compuestas, documento comparativo, checklist de despliegue, CRUD completo de épicas, hitos, columnas y sprints.

## Abierto
- Historial de sprints (`SprintTask`) y la pregunta de Jira o Linear (Open Questions).
- Fecha de fin de soporte de MySQL 8.0 y versión de `frappe-gantt`: sin verificar.
- El plan no se volvió a revisar tras estos cambios.
