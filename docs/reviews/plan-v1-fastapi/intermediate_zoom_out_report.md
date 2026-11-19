# Intermediate Zoom Out Report — plan-implementacion.md (Stage 8)

Revisor: egm-zoom-out. Lee el documento completo y los informes de las etapas 5, 6 y 7.

## Veredicto
El diseño pasa, pero las etapas posteriores lo empujan hacia más alcance del que necesita un MVP sin código. De unas 40 correcciones propuestas, unas 8 son necesarias. El resto añade maquinaria, se difiere a Future Improvements o se resuelve con una frase.

## 1. Alcance creciente causado por las mitigaciones (rechazar o diferir)

1. **Tabla de refresh tokens, cookie HttpOnly y rotación (Catalyst Major 1).** Añade `refresh_tokens`, detección de reutilización, limpieza y manejo de CSRF/CORS. Revierte la alternativa G, que el autor ya decidió aceptando que el token no se revoca, y contradice G6. El defecto real es que `refresh` renueva un token indefinidamente. Quitar `POST /auth/refresh` y la renovación automática del cliente (ítem 44) y usar un solo access token. Mantener el límite de revocación en Future Improvements. Límite de intentos, política de contraseñas y gestión de la clave de firma: una línea de "diferido" en Riesgos.
2. **Tabla `sprint_tasks` y bandera `outside_sprint` (Catalyst Major 2, Critic 5, Catalyst Nit 6).** Velocidad, burndown y métricas de flujo no son objetivos de este documento. Un segundo origen de pertenencia hay que sincronizarlo con `tasks.sprint_id`. No añadir `sprint_tasks`. Sí conservar `created_at`/`updated_at` en tareas y una marca de tiempo de cambio de columna: es el único caso donde "una migración posterior pierde historia" es un argumento real. Como columnas, no como tabla.
3. **Prueba que recorre las rutas y dependencias por recurso `task_for`, `sprint_for`, `department_for` (Catalyst Major 4).** El problema de IDOR es real, pero una frase en la regla 7 lo cierra: la autorización de `/tasks/{id}`, `/sprints/{id}` y `/departments/{id}` carga el objeto y deduce su proyecto. La prueba de recorrido y su lista blanca son infraestructura especulativa. Añadir una sola prueba: un usuario del proyecto B recibe 403 o 404 sobre un recurso del proyecto A.
4. **Claves foráneas compuestas, índice generado para un solo Product Owner, bloqueos para ciclos y política de borrado por tabla (Critic 4, Catalyst Nit 5).** A escala de MVP, el servicio ya valida los cruces. Conservar lo que el documento ya hace (columna generada para un solo sprint activo) y añadir una frase de política de borrado (restringir por defecto). Las carreras de ciclos y de PO duplicado son poco probables: documentarlas como límite conocido.
5. **Sustituir `column_transitions` por excepciones `allow`/`deny` (Catalyst Nit 8) o por `allowed_from` (Zoom Out 6).** La primera es más compleja que el problema. La segunda choca con la decisión del autor (alternativa I). Mantener la tabla. El defecto real es el ciclo de vida: crear una columna siembra sus transiciones contiguas, y borrar columnas no se admite en el MVP (`PATCH` solo edita nombre, WIP y política).
6. **"Risks & Mitigations" exhaustiva (Critic Blocker 1).** El prompt pide riesgos, así que la sección se justifica, pero con 5 a 7 filas (bloqueo del WIP, autenticación, IDOR, dependencias del Gantt, supuestos de tamaño). No debe volver a listar cada mitigación.
7. **Alternativas adicionales (Critic 7).** Ya hay nueve entradas. Añadir como máximo una (Jira/Linear) y solo si el autor quiere cerrar esa pregunta abierta. No añadir las demás.
8. **Zona horaria, `date` o `datetime`, reordenamiento sin bloqueo, límite de profundidad del recorrido, `updated_by` en presupuesto (Critic 11, 12, 20).** Una línea de decisión cada una ("zona horaria de la instalación, tipo `date`; gana la última escritura; sin límite de profundidad a escala MVP"). Sin columnas ni mecanismos nuevos, salvo `updated_by`/`updated_at` en `departments`, que es barato.
9. **Completar el documento con las secciones del prompt (Zoom Out 7, Critic 22).** Este documento es un plan de implementación, no el plan de 11 secciones. No ampliarlo. Una frase en el Overview que lo diga y diga dónde irán análisis, MoSCoW y métricas, y corregir la línea 33 del README ("Plan generado: pendiente").

## 2. Conflictos entre correcciones

- **Bloqueos.** Zoom Out 4 (el índice basta para un sprint activo), Zoom Out 2 y Catalyst 3 (bloquear la fila del proyecto o del sprint para el WIP) y Catalyst Nit 5 (bloquear la fila del proyecto para ciclos) bloquean la misma fila y se serializan entre sí. Elegir un bloqueo por operación: un solo sprint activo solo con el índice único (quitar el bloqueo de proyecto en `start`); los movimientos bloquean la fila de la columna destino; las dependencias sin bloqueo.
- **Bloquear `board_columns` frente a la edición del WIP por el Scrum Master.** Aceptable por ser rara, pero el documento debe decir que movimientos y ediciones de `wip_limit` se serializan. Bloquear la fila de la columna es lo más estrecho.
- **`apply_placement` como único escritor de `column_id` y `sprint_id` (Catalyst 2) y WIP solo en `move` (Critic 3).** Son compatibles. Una regla: `column_id` y `sprint_id` se excluyen de `PATCH /tasks/{id}`; la asignación a sprint pasa por `board.service` y comprueba el WIP; la columna inicial es la primera. Esto sustituye las correcciones sueltas de asignación, reapertura y cierre, y reduce el acoplamiento entre módulos.
- **Reiniciar `column_id` al cerrar (Catalyst 2) frente a conservar historial (Critic 5).** Sin `sprint_tasks`, reiniciar no pierde nada que use el MVP. Elegir reiniciar y descartar la tabla de historial.
- **Autenticación con cookie (Catalyst 1) frente a `sessionStorage` (Comprehension 10, Critic 6).** Sin refresh, la exposición a XSS queda como límite documentado. El proxy de Vite ya da un único origen en desarrollo.
- **Fechas híbridas (Zoom Out 8, Catalyst Nit 6) frente a la decisión del autor.** No cambiar el modelo. Solo corregir la redacción de G3 y G5: "no hay tabla de fechas del Gantt aparte; las tareas pueden tener fechas propias".
- **Matriz de transiciones (Zoom Out 6) frente a pregunta abierta y criterio de aceptación (Comprehension 4, Critic 14).** Se resuelve cerrando la pregunta: por defecto solo columnas contiguas, el Scrum Master puede editarlas y "Por hacer → Hecho" se rechaza por defecto. Borrar la Open Question 4.

## 3. Especulativo para un MVP sin código

- Generar tipos con `openapi-typescript` (Zoom Out 9, Catalyst Nit 7): adoptar solo como "generar los tipos desde OpenAPI", sin CI.
- `fastapi-users` u `OAuth2PasswordBearer` (Zoom Out 5): mencionar solo `OAuth2PasswordBearer`. `fastapi-users` trae sus propias tablas y choca con `users`.
- Reordenar fases, rutas y mover el presupuesto a la fase 2 (Zoom Out 11): poco valor. Solo anidar las rutas bajo `/projects/:id/`.
- Acortar el inventario de archivos (Zoom Out 1): correcto en espíritu pero es reescribir las líneas 194-286.
- Contrato de rendimiento de `GET /gantt`: declararlo como supuesto de escala en Riesgos.

## 4. Conjunto mínimo de cambios

1. **Arreglar el bloqueo del WIP** (regla 3, ítem 26): bloquear con `FOR UPDATE` la fila de `board_columns` destino y luego `COUNT`. Índice `(sprint_id, column_id)` en la migración. Mover a la misma columna es un no-op. Mantener la prueba de concurrencia.
2. **Cerrar las vías de escape del WIP.** `PATCH /tasks/{id}` no acepta `column_id` ni `sprint_id`. La asignación y el cierre pasan por el servicio del tablero. Una tarea nueva empieza en la primera columna. Al cerrar, las tareas sin terminar vuelven al backlog con `column_id` reiniciado a la primera.
3. **Quitar `POST /auth/refresh`, la renovación automática y el modelo de 30 minutos con refresh.** Un solo access token. Escribir en Límites conocidos la falta de revocación, `sessionStorage` legible por XSS y el registro abierto. Decir quién puede registrarse y quién crea el primer proyecto.
4. **Tabla corta de Risks & Mitigations** (5 a 7 filas) y lista breve de supuestos de escala y seguridad.
5. **Definir la semántica de `tasks` en 3 o 4 líneas.** Lo más simple: solo las tareas con columna aparecen en el tablero y cuentan para el WIP; las historias son contenedores. Decir para qué sirve `estimate_points`.
6. **Cerrar la Open Question 4** y alinear la fase 3 y la prueba 36b. Una línea sobre el ciclo de vida de columnas y transiciones.
7. **Redacción y referencias.** Definir "área" = departamento en el primer uso. Corregir los enlaces de la línea 13 a `../../README.md` y `../plan-prompt.md`. Calificar "no pueden contradecirse" y "sin pasos manuales" con la excepción de las tareas con fechas propias. "Punto 7" → "regla 7". Renumerar 36b. G6 admite Docker para MySQL local y pruebas. El Overview dice que esto es solo el plan de implementación y dónde irán análisis, MoSCoW y métricas; actualizar la línea 33 del README.
8. **Añadir `created_at`/`updated_at`** (y `updated_by` en `departments`) **y una marca de cambio de columna.** Una frase de política de borrado, una línea sobre autorización resuelta por el proyecto del objeto (más una prueba entre proyectos) y una línea por cada caso del Gantt: una sola fecha, inicio posterior al fin y zona horaria de la instalación.

**No añadir:** `sprint_tasks`, `refresh_tokens`, claves foráneas compuestas, prueba de recorrido de rutas, transiciones por excepciones, más entradas de alternativas ni la bandera `outside_sprint`.
