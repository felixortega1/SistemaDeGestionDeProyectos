# Goldfish Review Report — resolución (tercera revisión)

Status: resolved. Se aplicaron las 10 ediciones mínimas de la etapa 8 (M1-M10). Decisión del autor confirmada: no hay "desasignar" en el MVP.

## Aplicado
- **M1:** `assign_sprint` exige que la tarea no tenga sprint (422); las ediciones guardan con `update_fields`; el límite "no hay desasignar" queda declarado.
- **M2:** "Asignar o cambiar el responsable" es un permiso aparte (PO y SM); el formulario del Developer excluye `assignee`.
- **M3:** fechas efectivas con valor nulo (tres motivos de `undated`); `is_late` falso sin fin efectivo; `conflict` aclarado para el caso mixto; `effective_dates` sin `today`.
- **M4:** `board.views.move` renderiza el fragmento en 409 y 422; el middleware nunca devuelve el tablero; `board.js` recarga ante cualquier otro error; `templates/error.html`.
- **M5:** eliminado el respaldo `RunSQL`; el índice único se prueba con un `update` directo.
- **M6/M7:** `core.locks.lock_project`; lista única de cinco operaciones con bloqueo y su módulo (incluye `create_column`); columnas ordenadas por `(position, id)`; "sin deadlocks" acotado; carreras declaradas en Límites conocidos.
- **M8:** `User` con `AbstractBaseUser` y `PermissionsMixin`; `apps/accounts/admin.py` registra `User` y `Session`.
- **M9:** E2E reordenado (cierre al final, plaza liberada antes del paso sin JS, sprint con fin pasado, paso de presupuesto).
- **M10:** firmas "principales"; redirección de `projects/views.py` en F3; licencias en `VERSIONS.md`; hitos unificados; versión de `frappe-gantt` como salida de la prueba de concepto.

## No aplicado
`unassign_sprint`, `UniqueConstraint(project, position)`, tabla de firmas y `data-*`, bloqueos adicionales, alternativas de bloqueo, `GeneratedField` para el PO. Nits editoriales pendientes (vocabulario de dominio en Términos, "política", pie "Drafted with EGM").

## Pendiente
El plan no se volvió a revisar tras estas ediciones.
