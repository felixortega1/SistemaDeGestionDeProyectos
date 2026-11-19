# Informe Intermedio de Zoom Out (Etapa 8, ronda 3)

**Objetivo:** `docs/designs/plan-implementacion.md` (archivo completo). Las citas de línea son las del archivo actual; los informes anteriores usan numeraciones distintas.

## Estado de los revisores

| Revisor | Estado |
| --- | --- |
| `egm-zoom-out` | completado |

## Veredicto

No hay Blockers. El plan queda listo con unas 10 ediciones de texto, sin modelos, rutas ni dependencias nuevas. Los cuatro informes anteriores proponen muchas correcciones. La mayoría son huecos de redacción, pero cinco añaden código o alcance y conviene rechazarlas (sección 1.2). Hay conflictos entre correcciones que deben resolverse antes de aplicarlas (sección 2). No se reabren las decisiones del autor.

## 1. Correcciones necesarias para el MVP frente a las que añaden alcance

### 1.1 Necesarias

### N1. `assign_sprint` exige `task.sprint is None` (422 en otro caso) - Severity: Major
* **Affected Scope:** regla 10 (L149), regla 8 (L147), `test_backlog` (L420).
* **Rationale:** sin la precondición, `assign_sprint` permite reabrir una tarea terminada de un sprint cerrado y saltarse `ColumnTransition`. También contradice "`SprintTask` se escribe una sola vez" (L117). Es una condición de una línea, compatible con que `assign_sprint` funcione en `planned` y `active`. Añadir un caso de prueba. Declarar en Límites conocidos (L185-194) que una asignación errónea a un sprint `planned` no se revierte en el MVP (ver A1).

### N2. Las ediciones de tarea y de sprint no pisan `column`, `sprint` ni `status` - Severity: Major
* **Affected Scope:** regla 10 (L149), riesgo L200, servicios de edición (L388-389).
* **Rationale:** la regla 10 promete "único escritor" y L200 lo repite como mitigación, pero un `ModelForm.save()` sobre una instancia obsoleta lo viola. Fix mínimo: los servicios de edición guardan con `save(update_fields=<campos del formulario>)`, más una frase en la regla 10 y una prueba. Es más barato que tomar el bloqueo en la edición (ver C4).

### N3. Asignar responsable es un permiso explícito - Severity: Major
* **Affected Scope:** matriz (L138, L146).
* **Rationale:** la matriz niega al Scrum Master editar tareas, pero el texto le permite asignar. Un Developer que "edita sus tareas" podría reasignarlas. Fix: fila "Asignar responsable: PO sí, SM sí, Developer no", y el formulario del Developer excluye `assignee`. La asimetría de que el Developer mueve una tarea sin responsable pero no la edita se acepta con una frase.

### N4. Fechas efectivas con valor nulo - Severity: Major
* **Affected Scope:** regla 4 (L128), regla 6 (L130), `effective_dates` (L390).
* **Rationale:** un sprint `planned` puede tener fechas nulas (L111) y la regla 4 solo define motivos para tareas sin sprint, así que `effective_dates` no se puede implementar. Fix:
  * Fallback a `NULL`. Falta de inicio y fin da `sin fechas`; falta de uno solo da `una sola fecha`, con o sin sprint.
  * Sin fin efectivo, `is_late` es falso.
  * Quitar `today` de `effective_dates`, porque solo lo usa `build_gantt`.
  * `conflict` es falso solo si ambas tareas heredan inicio y fin del mismo sprint. El caso mixto se calcula con las fechas efectivas.

### N5. Contrato de error de `move` y middleware - Severity: Major
* **Affected Scope:** L168, ítem 15 (L384), `board.js` (L404).
* **Rationale:** sin esto, el criterio de F3 y el paso 6 del E2E no son ejecutables. Un middleware genérico no puede reconstruir `_board.html`. Fix en tres partes:
  * `board.views.move` captura `Conflict` y `Unprocessable` y renderiza `_board.html`.
  * `ServiceExceptionMiddleware` cubre el resto con página de error o mensaje y redirección, y nunca devuelve el fragmento del tablero. Añadir `templates/error.html`.
  * En `board.js`, ante cualquier respuesta distinta de 200, 409 o 422 (403, 404, 5xx, red), recargar el tablero, para que la tarjeta que Sortable ya movió no quede en el sitio equivocado.

### N6. Eliminar la bifurcación `RunSQL` de `sprints` - Severity: Major
* **Affected Scope:** ítem 19 (L388), L381, `test_migrations` (L417).
* **Rationale:** el informe de implementación verificó que `GeneratedField(db_persist=False)` con `UniqueConstraint` funciona en MySQL 8.4 y que `makemigrations` lo soporta. El respaldo literal es código muerto, desincroniza el estado de migraciones y contradice "todas las migraciones las genera `makemigrations`" (L381). Fix: borrar el respaldo y revisar a mano la migración generada. La prueba del índice único usa un `update(status="active")` directo vía ORM. La traducción de `IntegrityError` en `start_sprint` queda como red de seguridad. Esto reduce el alcance.

### N7. `create_column` toma el bloqueo del proyecto - Severity: Major
* **Affected Scope:** ítem 18 (L387), regla 10, supuesto L182.
* **Rationale:** L182 acepta "gana la última escritura" para `position`, pero "primera columna" y "antes de `is_done`" dependen de `position`. Con el bloqueo ya disponible, aceptar la carrera es un falso compromiso. Fix: `create_column` toma el mismo bloqueo (ver C2), las columnas se ordenan por `(position, id)` como desempate, y se corrige L182 (solo `create_column` toca `position`). No añadir `UniqueConstraint(project, position)` (ver C3).

### N8. Una sola lista de operaciones con bloqueo, cada una con su módulo - Severity: Major
* **Affected Scope:** L77, regla 10 (L149), riesgo L200, afirmación de "sin deadlocks" (L127).
* **Rationale:** hoy hay tres listas distintas. `start_sprint` no tiene módulo declarado (debe ser `sprints.services`) y `apply_placement` no toma bloqueo (lo toma quien lo llama). Fix: una lista canónica con `start_sprint` (sprints), `assign_sprint`, `move_task` y `close_sprint` (backlog), y `create_column` (board). Acotar "no hay deadlocks" a "entre ellas". Reemplazar "sin consecuencias" (L127) por "el movimiento usa el valor leído; el nuevo rige desde el siguiente". Corregir L192 (el riesgo real es dos `transfer_product_owner` simultáneos) y añadir a Límites conocidos la carrera al quitar miembros.

### N9. `/admin/` y sesiones - Severity: Major (cierre rápido)
* **Affected Scope:** L176, L189, ítem 16 (L385), `User` (L106).
* **Rationale:** `Session` no está registrada en el admin y ningún `admin.py` figura en la lista. Fix: añadir `apps/accounts/admin.py` (F1) que registre `User` y `Session` de solo lectura, o quitar la afirmación de L189. Declarar `AbstractBaseUser + PermissionsMixin` en `User` para que `createsuperuser` y el admin funcionen.

### N10. E2E ejecutable - Severity: Major
* **Affected Scope:** tabla L436-449.
* **Rationale:** tres pasos no se pueden ejecutar tal como están.
  * El paso 12 (cierre) destruye el sprint que usan los pasos 10 y 11 de F4. Ponerlo al final.
  * El paso 8 ("repetir el paso 5") da 409 porque "En desarrollo" ya está en 3/3. Ejecutarlo después del paso 9, que libera una plaza, y mover una tarea restante con "Mover a…".
  * El paso 3 debe fijar un `end_date` pasado para que el paso 10 vea una tarea retrasada.
  * Añadir además un paso de presupuesto (F5).

### N11. Una línea de F3 en `projects/views.py` - Severity: Nit
* **Affected Scope:** L158, criterio de F1 (L335), L314.
* **Rationale:** la redirección de `/projects/<id>/` cambia en F3 y su prueba de F1 fallaría sin aviso. Basta una línea en el ítem de F3.

### N12. Dos aclaraciones menores - Severity: Nit
* **Affected Scope:** L406 y L172 (hitos).
* **Rationale:** quitar "(MIT)" de la frase colectiva (HTMX no es MIT) y registrar licencia en `VERSIONS.md`. Unificar los hitos como "se listan siempre y se dibujan si la prueba de concepto lo permite".

### 1.2 Correcciones que añaden alcance (recomendado no incorporarlas)

### A1. `unassign_sprint`, cancelar o borrar un sprint `planned` - Severity: Nit (si se declara como límite)
* **Rationale:** añade ruta, servicio, tests, interacción con `SprintTask` y política de borrado. Un error de planning se corrige hoy iniciando y cerrando el sprint, y las tareas vuelven al backlog. Declarar el límite junto con N1. No contradice la decisión del autor.

### A2. `UniqueConstraint(project, position)` y exactamente una columna `is_done` por restricción - Severity: Nit
* **Rationale:** el bloqueo de N7 y la ausencia de borrado o edición de `is_done` ya garantizan ambos puntos. Ver C3.

### A3. Tabla de firmas de todos los servicios, atributos `data-*`, mapeo de `frappe-gantt`, contenido de `settings.py`, reglas de Ruff - Severity: Nit
* **Rationale:** contradice el principio anti-weeds, porque el plan ya baja a nivel de código en varios puntos. Rebajar L312 a "firmas de los servicios principales". Dejar el mapeo de `frappe-gantt` como salida de la prueba de concepto de F4, y fijar allí la versión y registrarla en Open Questions.

### A4. Bloqueo adicional en `add_dependency`, `transfer_product_owner`, quitar miembro, `set_transitions` - Severity: Nit
* **Rationale:** ya figuran como "poco probables" en L192. Ampliar el protocolo agranda la lista de la regla 10 y debilita la afirmación de "sin deadlocks". Dejarlos como límites declarados. Si se quiere una excepción, `set_transitions` es la más barata (mismo helper que `create_column`), pero no es necesaria.

### A5. Contratos (H) completos, nuevas alternativas, métricas, mapeo de errores 1205/1213, `READ COMMITTED` reescrito, `GeneratedField` para el Product Owner - Severity: Nit
* **Rationale:** sobreingeniería para 50 usuarios. Para el resto de POST basta la regla general: `Conflict` o `Unprocessable` redirigen a la página de origen con un mensaje de Django (comportamiento por defecto del middleware de N5). Ver C5. Los Nits de estilo (densidad de ítems, "Rejected by author", encabezados mixtos, README "fase 2") son cosméticos. Aplicar solo el del pie "Drafted with EGM" al publicar.

## 2. Conflictos entre correcciones

### C1. `unassign_sprint` o `sprint_id` vacío frente a N1 y a la decisión del autor - Severity: Major
* La variante "admitir `sprint_id` vacío en `assign_sprint`" contradice la decisión de que `assign_sprint` exija un sprint `planned` o `active` (L149). La variante `unassign_sprint` añade el alcance de A1.
* **Resolución:** N1 más la declaración como límite. No aplicar ninguna de las dos variantes.

### C2. Bloqueo en `create_column` frente a la regla de capas - Severity: Major
* Es un conflicto que genera la propia corrección N7. `board.services` no puede importar `projects` (L77) y el bloqueo es `Project.objects.select_for_update()`, así que `test_imports` (L414) fallaría.
* **Resolución:** `board.services.create_column` obtiene `Project` con `apps.get_model("projects", "Project")`, igual que `core.permissions` (L77). Mejor, que el helper del bloqueo viva en `core` y lo usen todas las capas. Indicarlo en una frase en L387.

### C3. `UniqueConstraint(project, position)` frente al desplazamiento al insertar - Severity: Major
* Con la restricción, el orden de escritura importa: primero subir `is_done`, luego insertar la nueva columna. Un `UPDATE` masivo de posiciones fallaría fila a fila en MySQL.
* **Resolución:** con el bloqueo de N7 la restricción es innecesaria (A2). Elegir bloqueo más desempate por `id`.

### C4. Bloqueo en las vistas de edición frente a `update_fields` - Severity: Major
* Los informes proponen cosas distintas. Tomar el bloqueo en la edición amplía el protocolo y repite el problema de deadlocks de A4.
* **Resolución:** N2, solo `update_fields`. El permiso de mover se vuelve a comprobar bajo el bloqueo (paso 1 de la regla 3), así que una edición concurrente del `assignee` queda cubierta.

### C5. Reescritura de `READ COMMITTED` y nueva alternativa de bloqueo frente a la decisión del autor - Severity: Nit
* Critic F7 y F14 piden reabrir la justificación del aislamiento y añadir alternativas (bloqueo por fila, control optimista). El autor ya decidió un bloqueo de proyecto.
* **Resolución:** dejar `READ COMMITTED` como está y no añadir alternativas. Solo acotar las afirmaciones de deadlock (N8).

### C6. Dos soluciones para sprint sin fechas - Severity: Major
* Critic F5 propone un motivo nuevo `sprint sin fechas`. Zoom Out ronda 1 propone el fallback a `NULL` con los motivos existentes. Un motivo nuevo añade una cadena, un caso de prueba y rutas del `undated`.
* **Resolución:** el fallback a `NULL` de N4, con los tres motivos actuales.

### C7. Tabla de firmas y atributos `data-*` frente a "sin código de implementación" (L312) - Severity: Nit
* **Resolución:** A3, rebajar L312.

### C8. Mover el paso 12 del E2E frente al criterio de F3 - Severity: Nit
* Si el cierre pasa al final, el criterio de F3 deja de comprobar `close_sprint` desde el tablero. F2 ya lo cubre con tests (L343, L421).
* **Resolución:** mover el paso al final y etiquetarlo "F3 (se ejecuta al final del recorrido)", sin cambiar sus criterios de aceptación.

## 3. Conjunto mínimo de cambios para dar el plan por listo

Son 10 ediciones de texto. Ninguna añade modelos, rutas ni dependencias, y N6 reduce código.

1. Regla 10 (L149) y `test_backlog` (L420): `assign_sprint` exige `task.sprint is None`; ediciones con `update_fields`. Declarar en Límites conocidos que no hay "desasignar" (N1, N2, A1).
2. Matriz (L138) y regla 7 (L146): fila "Asignar responsable: PO y SM"; el formulario del Developer excluye `assignee` (N3).
3. Reglas 4 y 6 (L128, L130) y L390: fallback a `NULL`, `conflict` aclarado, `is_late` falso sin fin efectivo, `effective_dates` sin `today` (N4).
4. L168, L384 y L404: `move` captura `Conflict` y `Unprocessable` y renderiza `_board.html`; el middleware cubre el resto sin fragmento; `board.js` recarga el tablero ante cualquier otro error; añadir `templates/error.html` (N5).
5. L388 y L381: eliminar el respaldo `RunSQL`; el índice único se prueba con un `update` directo (N6).
6. L387, L182 y regla 10: `create_column` toma el bloqueo (helper en `core` o vía `apps.get_model`), con desempate por `(position, id)` (N7, C2, C3).
7. L77, regla 10, L127, L192 y L200: una sola lista canónica de operaciones con bloqueo y su módulo; acotar "sin deadlocks"; sustituir "sin consecuencias"; corregir el riesgo de `transfer_product_owner`; añadir a Límites conocidos las carreras de dependencias, de miembros y de `set_transitions` con un formulario obsoleto (N8, A4).
8. L176, L189 y L385: añadir `apps/accounts/admin.py` (registrar `User` y `Session`) o quitar la afirmación; `PermissionsMixin` en `User` (N9).
9. Tabla E2E (L436-449): reordenar los pasos 8 y 12, fijar `end_date` pasado en el paso 3 y añadir el paso de presupuesto (N10).
10. L312, L158 y L406: rebajar L312 a "firmas de los servicios principales"; línea de F3 para `projects/views.py`; quitar "(MIT)" de la frase colectiva; mencionar la versión de `frappe-gantt` en Open Questions como salida de la prueba de concepto de F4 (N11, N12, A3).

Las ediciones 1 a 6 son las de más valor: hacen ciertas la regla de "único escritor" (regla 10) y la promesa de L200. El resto de hallazgos son Nits cosméticos o ampliaciones de alcance.
