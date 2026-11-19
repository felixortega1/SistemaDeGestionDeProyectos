# Goldfish Annotated Review Report

Status: resolved (auto accept: P1 a P20 aplicados; E1 a E3 abiertos; C1 a C6 refutados; D1 a D4 descartados)

**Target:** `docs/designs/plan-implementacion.md` (full file, 308 líneas)
**Fuente de hallazgos:** `reviews/plan/consolidated_review_report.md` y los informes de cada etapa.
**Convención:** cada ítem agrupa los hallazgos brutos que piden el mismo cambio. Las líneas citadas son las del documento antes de aplicar ninguna edición.

## Resumen de categorías

| Categoría | Ítems |
| --- | --- |
| ESCALATE (decide el autor) | E1, E2, E3 |
| PROPOSE FIX | P1 a P20 |
| CONTEST | C1 a C6 |
| DECLINE | D1 a D4 |

## ESCALATE — requieren tu decisión (no se aplican con "auto accept")

### [E1] [`egm-inventive-catalyst`, `egm-zoom-out`, `egm-design`] - Severity: Major
*   **Affected Scope:** líneas 53, 115, 131, 176-178 (`POST /auth/refresh`, límites conocidos, alternativa G), ítems 22, 44, 46.
*   **Discrepancy Description:** `refresh` acepta un token válido y devuelve otro de 30 minutos, así que un token robado se renueva sin fin y la vida corta no limita nada. Los revisores discrepan en la salida.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** El documento ya registra una decisión del autor (alternativa G: JWT propio, token no revocable). Las dos salidas la reabren en distinta medida y solo el autor sabe cuánta seguridad quiere en el MVP.
    *   **Opción A (etapa 8, recomendada por el revisor intermedio):** quitar `POST /auth/refresh`, la renovación automática (ítem 44) y el modelo de 30 minutos con refresh. Un solo access token. Declarar en Límites conocidos: sin revocación, `sessionStorage` legible por XSS, registro abierto.
    *   **Opción B (etapa 5):** access token de 5 a 10 minutos, refresh token opaco y rotativo en `refresh_tokens` (hash, `user_id`, `expires_at`, `revoked_at`), cookie `HttpOnly`, `SameSite`, ruta `/api/v1/auth`. Una tabla más, detección de reutilización, limpieza, y CSRF si hay dominios distintos.
*   ***Proposed Edit:*** según tu elección. Con A: eliminar el endpoint de la tabla de la API (línea 115), el ítem 44 (renovación) y la frase de renovación de la línea 131; añadir los tres límites. Con B: revertir la alternativa G y añadir tabla, endpoint y pruebas.

### [E2] [`egm-inventive-catalyst`, `egm-design`] - Severity: Major
*   **Affected Scope:** regla 8 (línea 108), tabla `tasks` (línea 95), `POST /sprints/{id}/close`.
*   **Discrepancy Description:** al cerrar un sprint se pone `sprint_id` en nulo y se pierde qué tareas estuvieron en él; sin eso no hay velocidad, burndown ni métricas de flujo.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Depende de si quieres velocidad y burndown en el producto. Los Goals G1 a G6 no los incluyen, pero `plan-prompt.md` pide métricas de flujo en el plan completo. La etapa 8 propone no añadir `sprint_tasks` y solo columnas `created_at`/`updated_at` más una marca de cambio de columna (ver P8).
*   ***Proposed Edit:*** si decides no añadirla, sin cambio adicional a P8. Si la quieres: nueva tabla `sprint_tasks(sprint_id, task_id, final_column_id, carried_over)` en el modelo, la migración, el cierre de sprint y `test_sprints.py`.

### [E3] [`egm-design`, `egm-structural`] - Severity: Major
*   **Affected Scope:** líneas 15-21 y 43 (Problema, Open Questions), sección "Alternatives Considered".
*   **Discrepancy Description:** el documento admite que no demuestra por qué construir esto frente a Jira o Linear y no evalúa esa alternativa.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** La respuesta (diferencial, proyecto interno o de aprendizaje) está solo en tu conocimiento. Ningún archivo la contiene.
*   ***Proposed Edit:*** o bien (a) añadir una alternativa J "Usar Jira o Linear" con tu motivo de rechazo y borrar la pregunta de la línea 43, o (b) mantener la pregunta y marcar el Problema como "incompleto: diferencial sin demostrar" en la línea 21.

## PROPOSE FIX

### [P1] [`egm-design`, `egm-zoom-out`, `egm-inventive-catalyst`, `egm-implementation-readiness`, `egm-codebase-details`] - Severity: Blocker
*   **Affected Scope:** regla 3 (línea 103), ítem 26 (línea 243), migración (ítem 8), pruebas (ítems 29 y 34).
*   **Discrepancy Description:** el bloqueo `SELECT … FOR UPDATE` sobre las tareas de la columna no serializa con 0 o pocas filas, depende de gap locks e índices no definidos y puede dar deadlock (1213) en lugar del 409.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; lo confirman cinco revisores. El documento ya usa un bloqueo de fila única en `start` (ítem 25).
*   ***Proposed Edit:***
    *   Regla 3 e ítem 26: dentro de una transacción, bloquear con `SELECT … FOR UPDATE` la fila de `board_columns` destino; luego `COUNT` de las tareas de esa columna en el sprint activo, **sin contar la tarea que se mueve**; rechazar con 409 si `count >= wip_limit`. `wip_limit` nulo = sin límite; `0` bloquea toda entrada. Mover a la misma columna es un no-op que devuelve 200. Deadlock (error 1213): reintentar una vez y, si persiste, devolver 409. Decir que los movimientos hacia una misma columna y las ediciones de `wip_limit` se serializan por esa fila.
    *   Ítem 8: índice `tasks(sprint_id, column_id)`; índices también en `tasks(project_id, sprint_id, column_id)` y `tasks.assignee_id`.
    *   Prueba 34: usar sesiones y transacciones reales y confirmadas; dos hilos mueven a la última plaza; uno gana y el otro recibe 409. Ítem 29: limpiar con `TRUNCATE` (no rollback por prueba) y fijar que las pruebas de concurrencia lo necesitan.
    *   Fase 3: unificar la redacción con la prueba 34 ("uno gana, otro 409").

### [P2] [`egm-inventive-catalyst`, `egm-zoom-out`, `egm-design`, `egm-implementation-readiness`] - Severity: Blocker
*   **Affected Scope:** reglas 3 y 8, ítems 24-26, tabla de la API.
*   **Discrepancy Description:** `column_id` y `sprint_id` se pueden escribir por otros caminos que esquivan el WIP y las transiciones: `PATCH /tasks/{id}`, asignar al sprint, reabrir tras un cierre.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; contradice G2 y G5.
*   ***Proposed Edit:*** añadir como regla 3b: `column_id` y `sprint_id` solo se escriben mediante `board.service.apply_placement(task, sprint, column)`. Se excluyen de los esquemas de entrada de `PATCH /tasks/{id}` y de `PATCH /sprints/{id}` (tampoco se acepta `status`). Añadir `POST /tasks/{id}/assign-sprint` (cuerpo `{sprint_id | null}`) en la tabla de la API: comprueba que el sprint no esté `closed`, deja la tarea en la primera columna y aplica el WIP si el sprint está activo. Tarea nueva: primera columna y última posición. Al cerrar, las tareas sin terminar vuelven al backlog con `column_id` reiniciado a la primera columna. Mover una tarea cuyo sprint no es el activo: 422.

### [P3] [`egm-design`, `egm-structural`, `egm-zoom-out`] - Severity: Blocker
*   **Affected Scope:** líneas 127-132 ("Límites conocidos") y línea 39.
*   **Discrepancy Description:** no hay sección de Riesgos y Mitigaciones ni supuestos de escala y seguridad, que el prompt exige y la línea 39 promete.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido. La etapa 8 limita la sección a 5-7 filas para no inflar el alcance.
*   ***Proposed Edit:*** tras "Límites conocidos", añadir `## Riesgos y mitigaciones` con una tabla de 6 filas (bloqueo del WIP; autenticación; acceso a objetos de otro proyecto; `GET /gantt` calculado en cada petición; ciclo de dependencias concurrente; clave de firma y límite de intentos de login diferidos) y `### Supuestos`: una organización por instalación; hasta 50 usuarios, 20 proyectos y 2.000 tareas por proyecto; HTTPS en producción; sin disponibilidad ni latencia medidas. Esas cifras son supuestos que debes confirmar o cambiar.

### [P4] [`egm-codebase-details`] - Severity: Blocker
*   **Affected Scope:** ítems 5, 13, 22 (líneas 219, 227, 239) y `.env.example` (ítem 3).
*   **Discrepancy Description:** PyJWT 2.10 o posterior rechaza un `sub` que no sea cadena; PyMySQL necesita `cryptography` para `caching_sha2_password` de MySQL 8; falta el algoritmo de firma y el formato de `DATABASE_URL`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido según el conocimiento del revisor (confianza alta); el comportamiento de PyJWT y PyMySQL no se verificó ejecutando código.
*   ***Proposed Edit:*** ítem 13: `create_token` guarda `sub` como `str(user_id)` y `decode_token` lo convierte a entero; algoritmo HS256 fijo en `decode(..., algorithms=["HS256"])`. Ítem 5: añadir `cryptography`. Ítem 3: `DATABASE_URL=mysql+pymysql://usuario:clave@localhost:3306/gestion?charset=utf8mb4`, `TEST_DATABASE_URL`, `JWT_ALGORITHM`, `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`. Ítem 13: `verify_password` captura `VerifyMismatchError` y devuelve falso; el servicio lo traduce a 401.

### [P5] [`egm-implementation-readiness`, `egm-design`] - Severity: Blocker
*   **Affected Scope:** tabla de modelo de datos (líneas 85-97), ítems 8 y 16-21.
*   **Discrepancy Description:** no hay tipos, nulabilidad, longitudes, `ON DELETE`, claves primarias ni política de borrado.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; sin esto el implementador decide el esquema.
*   ***Proposed Edit:*** reemplazar la tabla por una con tipo y restricciones de cada columna. Decisiones fijadas: ids `BIGINT UNSIGNED AUTO_INCREMENT`; textos cortos `VARCHAR(200)`, descripciones `TEXT`; `kind`, `status` y `role` como `VARCHAR` con `CHECK … IN (…)`; `estimate_points` `SMALLINT UNSIGNED` nulo; `position` `INT`; fechas `DATE` y marcas de tiempo `DATETIME` en UTC; `task_dependencies` con clave primaria (`task_id`, `depends_on_id`) y `CHECK (task_id <> depends_on_id)`; `ON DELETE RESTRICT` por defecto salvo `project_members`, `departments`, `epics`, `milestones` y `board_columns`, que se borran en cascada con el proyecto; borrar una tarea con hijas o dependientes devuelve 409; `DELETE …/members` del Product Owner devuelve 409. Una sola frase de política en el documento.

### [P6] [`egm-implementation-readiness`, `egm-codebase-details`] - Severity: Blocker
*   **Affected Scope:** tabla de la API (líneas 111-121) y ítems 22-28.
*   **Discrepancy Description:** no hay cuerpos de petición ni respuesta, forma de errores, ni campos editables por `PATCH`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; la línea 196 promete esquemas y no los hay. Los tipos de `types.ts` dependen de ellos.
*   ***Proposed Edit:*** añadir `### Contratos de la API` con: errores `{"detail": …}` de FastAPI; 409 del WIP `{"detail": {"code": "wip_limit", "limit": n, "count": n}}`; 422 de transición `{"detail": {"code": "transition_not_allowed", "allowed_column_ids": […]}}`; `POST /tasks/{id}/move` con cuerpo `{column_id}` (la posición se recalcula como última de la columna); `GET /projects/{id}/board` → `{sprint: {…} | null, columns: [{id, name, wip_limit, tasks: […], allowed_to: [column_id]}]}` (con `sprint` nulo, `columns` vacío); `GET /projects/{id}/gantt` → `{tasks: [{id, title, start, end, start_source, end_source, is_late, conflict, depends_on: […]}], undated: […], milestones: […]}`; login devuelve `{access_token, token_type}`; `PUT …/columns/transitions` reemplaza todo el conjunto con `{pairs: [[from, to], …]}`; lista de campos editables por `PATCH` de cada recurso; listas sin paginación en el MVP.

### [P7] [`egm-implementation-readiness`, `egm-comprehension`, `egm-design`] - Severity: Blocker
*   **Affected Scope:** regla 7 (línea 107), ítems 14, 23-26, 31.
*   **Discrepancy Description:** "sus tareas" no se define, no hay matriz de permisos, `require_role` no sabe resolver el proyecto en las rutas por id, y no hay invariantes de mismo proyecto, jerarquía ni estados del sprint.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido. Se descarta de la etapa 5 la prueba que recorre las rutas (ver C2): una sola frase y una prueba entre proyectos cierran el riesgo.
*   ***Proposed Edit:*** regla 7: tabla de permisos rol por acción (crear y editar backlog: Product Owner; abrir, cerrar y asignar sprints: Scrum Master; mover una tarea: su responsable, o cualquier developer si no tiene responsable, y también PO y SM; editar columnas, WIP, transiciones: Scrum Master; departamentos: PO y SM; leer: cualquier miembro, incluido el presupuesto). "Sus tareas" = `assignee_id` igual al usuario. Ítem 14: las rutas por id cargan el objeto, deducen su proyecto y aplican `require_role`; un no miembro recibe 404 (no revela existencia). Transferir el PO: `PATCH …/members` del PO actual. Invariantes: `epic_id`, `sprint_id`, `parent_id`, `column_id` y `assignee_id` pertenecen al mismo proyecto y el responsable es miembro; `parent_id` apunta a una `story` y una `story` no tiene padre; autodependencia y duplicados: 422; sprint: `start` solo desde `planned` y con fechas, `close` solo desde `active`; segundo sprint activo: 409. Prueba nueva: un usuario del proyecto B recibe 404 sobre recursos del proyecto A.

### [P8] [`egm-zoom-out`, `egm-design`] - Severity: Major
*   **Affected Scope:** tabla `tasks` y `departments` (líneas 89-97), regla 8, `test_sprints.py`.
*   **Discrepancy Description:** el esquema no tiene marcas de tiempo; añadirlas después es una migración con historia perdida, y bloquea las métricas de flujo.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido y barato; no depende de E2.
*   ***Proposed Edit:*** `created_at` y `updated_at` en `tasks`, `sprints` y `departments`; `updated_by` en `departments`; `column_changed_at` en `tasks`.

### [P9] [`egm-zoom-out`, `egm-comprehension`, `egm-implementation-readiness`] - Severity: Major
*   **Affected Scope:** tabla `tasks` (línea 95), ítems 24 y 49.
*   **Discrepancy Description:** no se define si las historias aparecen en el tablero, cuentan para el WIP o tienen columna, ni para qué sirve `estimate_points`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; es la entidad central.
*   ***Proposed Edit:*** añadir tras la tabla: "Las tareas (`kind = task`) tienen columna, aparecen en el tablero y cuentan para el WIP. Las historias (`kind = story`) son contenedores: no aparecen en el tablero ni cuentan para el WIP, y su `column_id` es nulo. Una historia se dibuja en el Gantt como resumen (de la primera fecha de inicio a la última de fin de sus tareas). `estimate_points` es informativo en el MVP y no se usa en ningún cálculo." Aplicar el cambio de nulabilidad de `column_id` en P5.

### [P10] [`egm-implementation-readiness`, `egm-codebase-details`, `egm-design`] - Severity: Major
*   **Affected Scope:** regla 4 (línea 104), regla 6, ítem 27, prueba 35.
*   **Discrepancy Description:** casos del Gantt sin definir: una sola fecha, inicio posterior al fin, fuentes distintas para inicio y fin, zona horaria de "hoy", semántica de `conflict`, hitos.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido.
*   ***Proposed Edit:*** inicio y fin se resuelven por separado (`start_source` y `end_source` de valor `task` o `sprint`). Si el fin efectivo es anterior al inicio, la tarea va a la lista `undated`. Una tarea con una sola fecha propia y sin sprint va a `undated`. "Hoy" es la fecha de la zona horaria de la instalación (variable `APP_TIMEZONE`), y `effective_dates` recibe `today` como parámetro para poder probarla. `conflict` es verdadero cuando el inicio del sucesor es estrictamente anterior al fin del predecesor, y es falso si alguno no tiene fechas. Los hitos se dibujan con su fecha en una fila aparte y no entran en dependencias ni en `is_late` en el MVP. Si `frappe-gantt` no soporta hitos (ver P14), se muestran como lista.

### [P11] [`egm-comprehension`, `egm-design`] - Severity: Major
*   **Affected Scope:** línea 46 (Open Question), fase 3 (línea 204), ítems 23 y 36b.
*   **Discrepancy Description:** la pregunta sobre las transiciones por defecto sigue abierta mientras el plan ya la implementa; no hay ciclo de vida de las columnas.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido.
*   ***Proposed Edit:*** borrar la Open Question de la línea 46 y escribir como decisión: "Por defecto solo se permite mover a la columna contigua, en ambos sentidos; el Scrum Master puede editar las transiciones; 'Por hacer → Hecho' se rechaza por defecto. Crear una columna siembra sus transiciones contiguas; borrar columnas no se admite en el MVP (`PATCH` solo cambia nombre, WIP y texto de la política)." Nombrar las cuatro columnas por defecto ("Por hacer", "En desarrollo", "En revisión", "Hecho") en el ítem 23.

### [P12] [`egm-implementation-readiness`, `egm-codebase-details`] - Severity: Major
*   **Affected Scope:** ítems 3-5, 8, 37-41 y lista de archivos.
*   **Discrepancy Description:** versiones sin fijar, dependencias y archivos faltantes, `vitest` en modo watch, MySQL sin versión mínima, comandos de arranque y servicio del build de React no definidos.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido. Las versiones exactas las debe fijar quien implemente al instalar y registrar en los archivos de bloqueo; el documento fija las versiones mayores.
*   ***Proposed Edit:*** fijar Python 3.12, Node 20 LTS, MySQL `8.0` (mínimo 8.0.16, necesario para `CHECK`), SQLAlchemy 2.x, FastAPI actual, PyJWT 2.x. Añadir al backend: `backend/app/modules/__init__.py`, `backend/app/models/base.py` (`Base` declarativa), `backend/migrations/script.py.mako`, `backend/pytest.ini` (`testpaths`, `pythonpath`, `--cov-fail-under=80`), configuración de ruff en `pyproject.toml`, `backend/tests/__init__.py`, `docker/initdb/01-test-db.sql`. Añadir al frontend: `react-dom`, `@vitejs/plugin-react`, `@types/react`, `@types/react-dom`, `jsdom`, `@testing-library/react`, `@testing-library/jest-dom`, `typescript-eslint`, `eslint-plugin-react-hooks`; archivos `tsconfig.node.json`, `src/vite-env.d.ts`, `src/test/setup.ts`, `src/types/frappe-gantt.d.ts`. Scripts: `dev`, `build`, `test` = `vitest run`, `lint`. Arranque: `uvicorn app.main:app --reload` desde `backend/`. Producción: el backend sirve el build de React como archivos estáticos (un solo proceso; coherente con G6). Línea 87: "argon2". Ítem 22: leer `JWT_EXPIRE_MINUTES` y no fijar 30. Ítem 4: Docker solo para MySQL local y pruebas.

### [P13] [`egm-codebase-details`, `egm-implementation-readiness`] - Severity: Major
*   **Affected Scope:** ítem 8 (migración).
*   **Discrepancy Description:** no dice si es manual o autogenerada, si la columna generada es `VIRTUAL` o `STORED`, ni nombres de `CHECK` ni orden de borrado en `downgrade`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; Alembic maneja mal `Computed` y `CHECK`.
*   ***Proposed Edit:*** migración escrita a mano. `active_project_id` como columna generada `VIRTUAL` con expresión `IF(status = 'active', project_id, NULL)` e índice único (MySQL admite varios NULL). `CHECK` con nombre (`ck_departments_amount`, `ck_sprints_dates`, …). `downgrade` borra en orden inverso de dependencias. Añadir una prueba de migración: subir, bajar y volver a subir sin errores. El criterio de la fase 1 ("se aplica y se revierte") pasa a "sube, baja y vuelve a subir".

### [P14] [`egm-codebase-details`, `egm-design`] - Severity: Major
*   **Affected Scope:** ítems 56 y 59, fase 4, alternativa H, diagrama de arquitectura (líneas 62-81).
*   **Discrepancy Description:** las capacidades de `frappe-gantt` (destruir, solo lectura, hitos, forma de datos, tipos) no se verificaron; la librería no aparece en la arquitectura.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido. No puedo verificarlo aquí: el documento debe exigir una prueba de concepto antes de comprometer la fase 4.
*   ***Proposed Edit:*** añadir `frappe-gantt` al diagrama y a una lista de decisiones del Technical Plan. Fase 4 empieza con una prueba de concepto de medio día: confirmar que se puede (1) vaciar el contenedor al desmontar, (2) desactivar la edición, (3) pasar clases por tarea (`custom_class`), (4) dibujar dependencias con datos `{id, name, start, end, dependencies}`. Las dependencias hacia tareas en `undated` se filtran antes de pasarlas a la librería. Si falla (3) o (4), plan B: SVG propio solo para barras y flechas (alternativa descartada en H, con coste conocido). Hitos: lista aparte si no hay soporte nativo.

### [P15] [`egm-codebase-details`, `egm-implementation-readiness`] - Severity: Major
*   **Affected Scope:** línea 237, ítems 12, 23, 25-28.
*   **Discrepancy Description:** la regla "un módulo solo importa el `service.py` de otro" choca con la creación de columnas por defecto; no está definido el commit ni si los handlers son síncronos.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido.
*   ***Proposed Edit:*** `board.service.create_default_board(project_id)` crea columnas y transiciones y lo llama `projects.service`; `board` no importa `projects`: recibe el rol ya resuelto desde `deps.py`. Los modelos viven en `app/models/` y son compartidos. Los handlers son `def` (síncronos), porque PyMySQL es síncrono. `get_session()` solo abre y cierra; el commit lo hace el servicio al final de cada caso de uso, y un `IntegrityError` se traduce a 409 dentro del servicio. Mover el párrafo de la línea 237 por encima de la lista de archivos del backend.

### [P16] [`egm-implementation-readiness`, `egm-codebase-details`, `egm-style`] - Severity: Major
*   **Affected Scope:** ítems 29-36b, 59-60, Verification Plan.
*   **Discrepancy Description:** huecos de pruebas, "token vencido" sin mecanismo, 80 % sin fuente, E2E manual sin criterio, frontend sin simulación de la API.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido.
*   ***Proposed Edit:*** añadir pruebas para: valores por defecto al crear proyecto (4 columnas, WIP 3, transiciones contiguas), Product Owner único, `/auth/me`, CRUD y duplicados de dependencias, autodependencia, mismo proyecto, sprint cerrado, movimientos desde y hacia `is_done`, forma del JSON de `/gantt`, índice único del sprint activo a nivel de base de datos, migración arriba y abajo, aislamiento entre proyectos, 401 de `client.ts` y 422 de `BoardPage` con la API simulada. "Token vencido": `create_token` acepta `expires_delta` para pruebas. Cobertura: el 80 % es un umbral de partida del autor del plan (suposición). El E2E manual pasa a lista numerada con resultado esperado por paso. Renumerar `36b` como 37 y desplazar los siguientes.

### [P17] [`egm-implementation-readiness`, `egm-style`, `egm-zoom-out`] - Severity: Major
*   **Affected Scope:** fases (líneas 198-206) e ítems 37-60.
*   **Discrepancy Description:** ningún archivo está asignado a una fase; el frontend no figura en la fase 1; el cierre de sprint se acepta en la fase 5 pero se implementa en la 2; rutas sin `/projects/:id/`; ninguna página edita columnas, WIP o transiciones.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido.
*   ***Proposed Edit:*** añadir una columna "Fase" a cada ítem de archivos. Mover el cierre de sprint (y su criterio) a la fase 2. Fase 1 incluye `LoginPage`, `ProjectsPage` y un `App.tsx` con solo esas rutas; cada fase añade sus rutas. Rutas: `/projects/:id/backlog`, `/sprints`, `/board`, `/gantt`, `/budget`. Nueva página `ColumnsPage.tsx` (fase 3) para columnas, WIP y transiciones (Scrum Master). El mensaje del WIP lee el límite del 409. Criterios de las fases 1, 4 y 5 con entrada y resultado concretos. El presupuesto se mantiene en la fase 5 (la etapa 5 sugirió moverlo a la 2: se descarta, es de bajo valor).

### [P18] [`egm-comprehension`, `egm-style`, `egm-structural`] - Severity: Major
*   **Affected Scope:** líneas 11, 13, 19, 29, 48, 136-153, "Overview", enlaces.
*   **Discrepancy Description:** referencias colgantes ("las tres opciones", "opción 1", `project_budgets`), "área" sin definir, afirmaciones más fuertes que el diseño, enlaces rotos, promesa de lista de archivos, y el documento no dice que es solo el plan de implementación.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Válido; un lector humano necesita el contexto.
*   ***Proposed Edit:*** línea 13: enlaces a `../../README.md` y `../plan-prompt.md`, y señalar "la lista de archivos está en el Detailed Implementation Plan". Añadir al Overview: "Este documento es el plan de implementación. El análisis comparativo, la priorización MoSCoW y las métricas de éxito del prompt quedan pendientes en otro documento." En el primer uso de "área" (Overview y G4) escribir "área (un departamento de la empresa, p. ej. contabilidad o marketing)". Alternativas A y B: reescribirlas sin referencias externas (A: cuatro formas de modelar el área, B: departamento global con tabla `project_budgets(project_id, department_id, monto, moneda)`); borrar la línea 136 (la frase sobre los "límites técnicos que se presentaron al elegir"). Línea 19: "…no pueden contradecirse, salvo en las tareas con fechas propias (regla 4)"; G5: "sin pasos manuales, salvo las tareas con fechas propias". G3: "no se guardan fechas del Gantt aparte; las tareas pueden tener fechas propias". Mover "Decisiones de diseño tomadas por el autor" antes de "Open Questions". Reemplazar "punto 7 del Technical Plan" por "regla 7" y "las once tablas del Technical Plan" por "las once tablas del Modelo de datos". "El proyecto está en cero" por "no tiene código". G6: "sin servicios adicionales, aparte de MySQL (local con Docker)". Mover el texto de "Supone que Docker…" al ítem 1 (README).

### [P19] [`egm-implementation-readiness`, `egm-style`] - Severity: Nit
*   **Affected Scope:** ítem 1 (README), línea 33 del README.
*   **Discrepancy Description:** el README dice "Plan generado: pendiente" y el ítem no da el texto de "Estado".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cambio mínimo y comprobable.
*   ***Proposed Edit:*** ítem 1: "Estado: plan de implementación redactado; sin código." Reemplazar "Plan generado: pendiente" por un enlace a `docs/designs/plan-implementacion.md`.

### [P20] [`egm-implementation-readiness`, `egm-inventive-catalyst`, `egm-zoom-out`] - Severity: Nit
*   **Affected Scope:** `api/types.ts` (ítem 45), validación de moneda (ítem 28), alternativas B, C, E y H, Future Improvements.
*   **Discrepancy Description:** tipos escritos a mano duplican OpenAPI; la moneda se llama ISO 4217 pero solo se valida el formato; alternativas largas; Future Improvements con etiquetas de fase inconsistentes.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cambios baratos.
*   ***Proposed Edit:*** ítem 45: generar `types.ts` desde el OpenAPI de FastAPI con `openapi-typescript` (script manual, sin CI). Ítem 28 y línea 90: "código de tres letras mayúsculas; solo se comprueba el formato". Alternativas B, C, E y H: reducir a una línea de motivo. Future Improvements: etiquetar todas "fase 2" o ninguna.

## CONTEST

### [C1] [`egm-inventive-catalyst`] - Severity: Major (refresh rotativo con cookie)
*   **Affected Scope:** alternativa G (línea 176), G6.
*   **Discrepancy Description:** reemplazar el JWT sin revocación por refresh rotativo con tabla `refresh_tokens`.
*   ***AI Suggestion:*** CONTEST (depende de E1; si eliges la opción B, se anula este contest)
*   ***Justification:*** La alternativa G del documento registra la decisión del autor y su consecuencia aceptada ("el token no se revoca antes de vencer"), y G6 fija un despliegue sin servicios ni tablas adicionales. La propuesta añade una tabla, limpieza y manejo de CSRF y revierte esa decisión.
*   ***Proposed Edit:*** ninguna.

### [C2] [`egm-inventive-catalyst`] - Severity: Major (prueba que recorre las rutas y dependencias `task_for`, `sprint_for`, `department_for`)
*   **Affected Scope:** regla 7, ítem 14, `test_roles.py`.
*   **Discrepancy Description:** infraestructura de autorización por recurso con prueba de recorrido de rutas y lista blanca.
*   ***AI Suggestion:*** CONTEST
*   ***Justification:*** El riesgo de IDOR queda cubierto por P7 (carga del objeto y deducción del proyecto en `deps.py`, 404 a no miembros y una prueba entre proyectos). El documento no tiene ningún endpoint todavía y la prueba de recorrido añadiría una lista blanca que mantener (Goals G1 a G6 no la requieren).
*   ***Proposed Edit:*** ninguna.

### [C3] [`egm-design`, `egm-inventive-catalyst`] - Severity: Major / Nit (claves foráneas compuestas, bloqueo de ciclos, Product Owner único por índice generado)
*   **Affected Scope:** líneas 85-97, regla 5, ítem 24.
*   **Discrepancy Description:** garantizar en la base de datos el mismo proyecto, la ausencia de ciclos concurrentes y un solo Product Owner.
*   ***AI Suggestion:*** CONTEST (parcial)
*   ***Justification:*** El servicio ya valida el mismo proyecto (P7). La carrera de ciclos y de PO duplicado es de baja probabilidad a la escala declarada y se documenta como riesgo en P3. Se acepta del hallazgo solo la política de borrado y la clave primaria de `task_dependencies` (P5).
*   ***Proposed Edit:*** ninguna.

### [C4] [`egm-inventive-catalyst`, `egm-zoom-out`] - Severity: Nit (transiciones por excepciones `allow`/`deny` o `allowed_from`)
*   **Affected Scope:** `column_transitions` (línea 94), alternativa I.
*   **Discrepancy Description:** reemplazar la tabla de transiciones.
*   ***AI Suggestion:*** CONTEST
*   ***Justification:*** La alternativa I del documento rechaza explícitamente la política solo como texto y registra la tabla por proyecto como decisión del autor. El defecto real (ciclo de vida de las columnas) lo resuelve P11.
*   ***Proposed Edit:*** ninguna.

### [C5] [`egm-inventive-catalyst`, `egm-zoom-out`] - Severity: Nit (simplificar o señalar el desfase de las fechas híbridas: `outside_sprint`)
*   **Affected Scope:** regla 4, alternativa D.
*   **Discrepancy Description:** heredar siempre del sprint, o añadir una bandera `outside_sprint`.
*   ***AI Suggestion:*** CONTEST
*   ***Justification:*** Las fechas híbridas son una decisión del autor registrada en "Decisiones de diseño tomadas por el autor". Solo se corrige la redacción de G3 y G5 (P18).
*   ***Proposed Edit:*** ninguna.

### [C6] [`egm-design`] - Severity: Major (alternativas adicionales: `sprint_tasks`, mecanismos de bloqueo, una tabla o dos para historia y tarea, roles globales)
*   **Affected Scope:** sección "Alternatives Considered".
*   **Discrepancy Description:** faltan alternativas para decisiones de alto impacto.
*   ***AI Suggestion:*** CONTEST
*   ***Justification:*** La sección ya tiene nueve entradas. Las decisiones relevantes quedan fijadas en P1 (mecanismo del WIP), P9 (historia y tarea) y E2 (historial). Solo se añade la alternativa de Jira o Linear si el autor lo decide (E3).
*   ***Proposed Edit:*** ninguna.

## DECLINE (Nit; registrado, no se aplica)

*   **[D1]** `egm-style`: mezcla de inglés y español en encabezados y marcadores (Create, Modify, Pros, Cons). Proviene de la plantilla de EGM; no cambia ninguna decisión.
*   **[D2]** `egm-style`: ítem 26 con unas nueve reglas en una viñeta. P1 y P2 ya trasladan las reglas a la sección de reglas del sistema.
*   **[D3]** `egm-design`: estrategia de edición concurrente de `position` y límite de profundidad del recorrido de dependencias. Decisión de una línea: gana la última escritura; sin límite de profundidad a escala MVP (se anota en Supuestos de P3).
*   **[D4]** `egm-zoom-out`: acortar el inventario de 60 archivos y mover el presupuesto a la fase 2. Reescritura sin cambio de decisión; el presupuesto se queda en la fase 5.

## Cómo seguir

Responde con una de estas opciones:

-   **Auto accept:** aplica P1 a P20 de una vez. Se saltan E1 a E3 (necesitan tu decisión), los CONTEST y los DECLINE.
-   **Interactive breakdown:** paso a paso, ítem por ítem.
-   **Continue / no changes:** no se aplica nada.
-   **Instrucción propia:** por ejemplo, tus decisiones sobre E1 (A o B), E2 (con o sin `sprint_tasks`) y E3 (alternativa J o pregunta abierta), seguida de "auto accept".
