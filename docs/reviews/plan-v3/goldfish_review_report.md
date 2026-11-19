# Goldfish Review Report — resolución (segunda revisión)

Status: resolved. Decisiones del autor: `create_column` inserta antes de "Hecho"; `assign_sprint` también al sprint activo (con WIP, en F2); un bloqueo por proyecto.

## Aplicado
- **B1 Bloqueo:** `Project.select_for_update()` en `start_sprint`, `assign_sprint`, `move_task` y `close_sprint`, con relectura bajo el bloqueo; WIP dentro de `apply_placement`; `CheckConstraint` de sprint y columna; sin reintento de deadlock.
- **B2 Capas:** orden `core`, `accounts`, `board`, `projects`, `sprints`, `backlog`, `gantt`, `budget`; `test_imports` comprueba el orden con `ast` y usa `django.setup()`.
- **B3 `create_column`:** se inserta antes de la columna `is_done`; `is_done` no se edita.
- **B4 E2E:** pasos reordenados por fase; paso nuevo para llevar una tarea a "Hecho"; el cierre del sprint se comprueba tras F3.
- `is_late` nunca para tareas sin sprint; sin `conflict` cuando ambas heredan fechas del mismo sprint; fechas de `Sprint` nulables hasta iniciar.
- Developer no crea tareas; el endpoint de rol rechaza `product_owner`; baja de miembro solo bloqueada por tareas sin terminar.
- `SprintTask` solo para velocidad; `GeneratedField` literal con el nombre `active_project_id`; criterio F4 verificable en el JSON; `from_column_id`, `middleware.py` de excepciones, `.gitattributes`, `LookupError` en F1; credenciales de MySQL en una sola fuente (`MYSQL_*`); texto de MySQL 8.0.

## No aplicado
`TaskMove`/`done_at`, `ProjectMember.is_active`, "tomar tarea", segundo `GeneratedField` para el PO, `UniqueConstraint(position)`, orden de bloqueo con reintento de deadlock, tabla de firmas, `hx-sync`/`Vary`, reestructuración editorial.

## Pendiente
- Mejoras editoriales de la etapa 7 (estructura del Technical Plan, decisiones duplicadas, referencias sin enlace, términos sin definir) quedan para el final.
- El plan no se volvió a revisar tras estos cambios.
