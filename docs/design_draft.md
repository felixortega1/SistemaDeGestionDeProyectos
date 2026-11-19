# Sistema de Gestión de Proyectos — Plan de implementación

*   **Author:** felixortega1
*   **Status:** Draft
*   **Date:** 2026-11-16

--------------------------------------------------------------------------------

## Overview

Un sistema web para seguir proyectos con Scrum. Cada tarea vive en un solo lugar y se ve de dos formas: un tablero Kanban con límites de trabajo en curso (WIP) y un diagrama de Gantt de solo lectura. El sistema guarda además un monto de presupuesto, ingresado a mano, para cada área del proyecto.

El proyecto está en cero: no hay código. Este documento define qué se construye primero (el MVP) y lista los archivos que hay que crear. Stack decidido: Python con FastAPI, React y MySQL, en un monolito modular. Contexto de origen: [README.md](./README.md) y [docs/plan-prompt.md](./docs/plan-prompt.md).

## The Problem

Los equipos que trabajan con Scrum suelen repartir su trabajo entre varias herramientas: una para el backlog y los sprints, otra para el tablero, otra para el cronograma y una hoja de cálculo para el presupuesto. Las fechas, el estado y el avance de una misma tarea se duplican y se desfasan entre esas herramientas.

La propuesta es una sola fuente de verdad, la tarea (estado, estimación, dependencias, sprint). El tablero y el Gantt se calculan a partir de ella, así que no pueden contradecirse.

Este documento no demuestra que ese problema justifique construir la herramienta en lugar de usar Jira o Linear. Ese punto sigue abierto (ver Open Questions).

## Goals

*   **G1. Backlog y sprints:** crear proyectos, un product backlog y sprints con su sprint backlog, y reflejar en el sistema los roles Scrum (Product Owner, Scrum Master, equipo de desarrollo).
*   **G2. Tablero Kanban:** columnas con una política de transición por columna y un límite WIP que el servidor hace cumplir (no solo la interfaz).
*   **G3. Gantt de solo lectura:** mostrar tareas, dependencias e hitos con fechas calculadas a partir de las tareas y los sprints. No se guardan fechas del Gantt como dato aparte.
*   **G4. Presupuesto por área:** guardar un monto y una moneda por cada área del proyecto, ingresados a mano.
*   **G5. Una sola fuente de verdad:** mover una tarea de columna o de sprint cambia tablero y Gantt sin pasos manuales.
*   **G6. Despliegue simple:** el sistema corre como un solo backend FastAPI, un frontend React y una base MySQL, sin servicios adicionales.

## Non-Goals

*   Facturación, registro de horas y seguimiento del gasto real contra el presupuesto.
*   App móvil, integraciones con otras herramientas y notificaciones.
*   Edición del Gantt arrastrando barras, ruta crítica y línea base (fase 2).
*   Comentarios, adjuntos, etiquetas y registro de auditoría.
*   Multi-tenant (varias empresas aisladas en una misma instalación). Se asume una sola organización por instalación hasta que se decida otra cosa.
*   Cifras de escala y disponibilidad (p95, usuarios concurrentes). El plan declara supuestos, no objetivos medidos.

## Open Questions

*   **Diferencial:** ¿por qué esta herramienta y no Jira o Linear, o es un proyecto interno o de aprendizaje? Cambia cuánto del MVP se justifica.
*   **Idioma del código:** nombres de tablas, endpoints y variables en inglés o en español. Este borrador usa inglés para identificadores y español para la documentación.
*   **Equipo y plazo:** tamaño del equipo y fecha objetivo del MVP, que se necesitan para dimensionar las fases.
*   **Transiciones por defecto:** el borrador permite mover una tarea solo a la columna contigua, en ambos sentidos. ¿Se necesita otra regla inicial (por ejemplo, poder pasar de "Por hacer" directo a "Hecho")?

## Decisiones de diseño tomadas por el autor

*   **Área = departamento de la empresa**, definido dentro de cada proyecto (`departments` con `project_id`). El monto y la moneda están en la misma fila. Un departamento no se comparte entre proyectos.
*   **Fechas del Gantt híbridas:** la tarea hereda las fechas de su sprint. Si tiene fechas propias, estas mandan.
*   **WIP:** máximo 3 tareas en la columna "En desarrollo", contadas solo dentro del sprint activo.
*   **Autenticación:** JWT propio con usuarios en MySQL.
*   **Política de transición hecha cumplir por el servidor:** una tabla de transiciones permitidas entre columnas. El servidor rechaza los movimientos que no están en la tabla.

## Technical Plan (Architecture)

### Componentes

Un backend FastAPI, un frontend React y una base MySQL. El backend es un monolito modular: cada módulo tiene su propio paquete y solo se comunica con los demás a través de funciones de servicio, no por HTTP.

```text
 Navegador (React + TypeScript)
   ├─ Vista Backlog / Sprints
   ├─ Vista Tablero (Kanban)
   ├─ Vista Gantt (solo lectura)
   └─ Vista Presupuesto
          │  HTTPS, JSON, cabecera Authorization: Bearer <JWT>
          ▼
 Backend FastAPI  (/api/v1)
   ├─ auth        usuarios, login, emisión y validación de JWT
   ├─ projects    proyectos, miembros y roles Scrum
   ├─ backlog     épicas, historias, tareas, dependencias, hitos
   ├─ sprints     sprints, asignación de tareas, notas de review y retro
   ├─ board       columnas, movimientos, límite WIP
   ├─ gantt       cálculo de fechas efectivas y marcas de retraso
   └─ budget      departamentos con monto y moneda
          │  SQLAlchemy 2 (sesión por petición)
          ▼
 MySQL 8 (InnoDB)  ── migraciones con Alembic
```

### Modelo de datos

| Tabla | Campos principales | Reglas |
| --- | --- | --- |
| `users` | `id`, `email` (único), `password_hash`, `name` | La contraseña se guarda con hash (bcrypt o argon2). |
| `projects` | `id`, `name`, `description`, `created_by` | |
| `project_members` | `project_id`, `user_id`, `role` | `role` es `product_owner`, `scrum_master` o `developer`. Un proyecto tiene un solo Product Owner. |
| `departments` | `id`, `project_id`, `name`, `budget_amount` DECIMAL(14,2), `currency` CHAR(3) | Índice único (`project_id`, `name`). El monto es ≥ 0. La moneda es un código ISO 4217. |
| `epics` | `id`, `project_id`, `title` | |
| `sprints` | `id`, `project_id`, `name`, `goal`, `start_date`, `end_date`, `status`, `review_notes`, `retro_notes` | `status` es `planned`, `active` o `closed`. Solo un sprint `active` por proyecto. `end_date` ≥ `start_date`. |
| `board_columns` | `id`, `project_id`, `name`, `position`, `wip_limit` (nulo = sin límite), `policy_text`, `is_done` | Por defecto: "Por hacer", "En desarrollo" (`wip_limit` 3), "En revisión", "Hecho" (`is_done`). `policy_text` describe la política y no se evalúa. |
| `column_transitions` | `project_id`, `from_column_id`, `to_column_id` | Clave primaria (`from_column_id`, `to_column_id`). Ambas columnas deben ser del mismo proyecto. Por defecto: cada columna a la contigua, en ambos sentidos. |
| `tasks` | `id`, `project_id`, `epic_id` (nulo), `sprint_id` (nulo), `parent_id` (nulo), `kind`, `title`, `description`, `column_id`, `position`, `estimate_points`, `assignee_id` (nulo), `start_date` (nulo), `due_date` (nulo) | `kind` es `story` o `task`. Una tarea con `parent_id` es hija de una historia. |
| `task_dependencies` | `task_id`, `depends_on_id`, `type` | Solo tipo `finish_to_start` en el MVP. No se permite un ciclo. |
| `milestones` | `id`, `project_id`, `name`, `date` | |

### Reglas del sistema

1.  **Fuente de verdad.** La tarea guarda su estado (`column_id`), su sprint y sus dependencias. El tablero y el Gantt se calculan a partir de ella. Ninguna fecha del Gantt se guarda aparte.
2.  **Tablero.** `GET /projects/{id}/board` devuelve las tareas del sprint activo agrupadas por columna. Las tareas sin sprint no aparecen en el tablero.
3.  **Transiciones y WIP.** Mover una tarea primero comprueba que el par (columna actual, columna destino) esté en `column_transitions`; si no, responde `422` con las columnas destino permitidas. Después se aplica el límite WIP. Mover una tarea a una columna con `wip_limit` se hace en una transacción: se bloquean las filas de las tareas de esa columna y sprint (`SELECT … FOR UPDATE`), se cuentan, y si el conteo ya es igual al límite se responde `409 Conflict` con el límite y el conteo. Así dos movimientos simultáneos no superan el límite. La interfaz también deshabilita el movimiento, pero la regla vive en el servidor.
4.  **Fechas efectivas del Gantt.** `inicio = task.start_date`, si no existe `sprint.start_date`. `fin = task.due_date`, si no existe `sprint.end_date`. Una tarea sin fechas propias y sin sprint no se dibuja y aparece en una lista "Sin fecha". Si una tarea tiene fechas propias, mover su sprint no las cambia.
5.  **Dependencias.** Al crear una dependencia, el servidor recorre el grafo desde `depends_on_id`. Si llega a `task_id`, rechaza con `422`. El Gantt marca como "conflicto" una dependencia cuyo sucesor empieza antes de que termine el predecesor. No reprograma nada.
6.  **Retraso.** Una tarea cuya fecha efectiva de fin es anterior a hoy y cuya columna no es `is_done` se marca "retrasada".
7.  **Roles.** El Product Owner edita el backlog y las prioridades. El Scrum Master abre y cierra sprints y edita las columnas y el WIP. Los desarrolladores mueven y editan sus tareas. Cualquier miembro lee todo el proyecto. Solo el Product Owner y el Scrum Master editan departamentos y presupuesto. La comprobación se hace en el backend en cada endpoint.
8.  **Eventos Scrum.** Sprint planning: asignar tareas del backlog al sprint y pasarlo a `active`. Daily: el tablero. Review y retrospectiva: los campos `review_notes` y `retro_notes` del sprint, que se editan al cerrarlo. Al cerrar un sprint, las tareas que no están en una columna `is_done` quedan con `sprint_id` nulo y vuelven al backlog.
9.  **Presupuesto.** `departments` guarda un monto y una moneda por departamento y proyecto. El sistema no compara el monto con ningún gasto.

### API (REST, prefijo `/api/v1`)

| Grupo | Endpoints principales |
| --- | --- |
| auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| projects | `GET/POST /projects`, `GET/PATCH /projects/{id}`, `GET/POST/DELETE /projects/{id}/members` |
| backlog | `GET/POST /projects/{id}/tasks`, `GET/PATCH/DELETE /tasks/{id}`, `POST/DELETE /tasks/{id}/dependencies`, `GET/POST /projects/{id}/epics`, `GET/POST /projects/{id}/milestones` |
| sprints | `GET/POST /projects/{id}/sprints`, `PATCH /sprints/{id}`, `POST /sprints/{id}/start`, `POST /sprints/{id}/close` |
| board | `GET /projects/{id}/board`, `POST /tasks/{id}/move`, `GET/PATCH /projects/{id}/columns`, `GET/PUT /projects/{id}/columns/transitions` |
| gantt | `GET /projects/{id}/gantt` |
| budget | `GET/POST /projects/{id}/departments`, `PATCH/DELETE /departments/{id}` |

### Decisiones sin alternativas defendibles

SQLAlchemy 2 con Alembic para el acceso a datos y las migraciones. Pydantic para validar entradas y salidas. Configuración desde variables de entorno (cadena de MySQL, clave de firma del JWT). React con TypeScript y Vite en el frontend.

### Límites conocidos

*   Las tareas sin sprint no tienen tablero: solo se ven en el backlog.
*   Un sprint que se mueve no arrastra a las tareas con fechas propias.
*   El JWT no se revoca antes de vencer. Se usa una vida corta (30 minutos) con renovación. Cerrar sesión borra el token del navegador, no lo invalida en el servidor.
*   El Gantt no reprograma ni propaga cambios: solo muestra y marca conflictos.

## Alternatives Considered

Cada rechazo es una decisión del autor. Los motivos son los límites técnicos que se presentaron al elegir.

### Alternativa A: "Área" como categoría de costo, equipo o épica

*   **Pros**: la categoría de costo es la opción más simple; el equipo y la épica permiten sumar trabajo por área.
*   **Cons**: la categoría de costo no se vincula con las tareas. El equipo obliga a asignar un equipo a cada tarea. La épica no permite presupuestar lo que no es una épica y el presupuesto se mueve si cambian las épicas.
*   **Reason for Rejection**: Rejected by author: el área es un departamento de la empresa (contabilidad, operaciones, marketing), un concepto que ninguna de las tres opciones representa.

### Alternativa B: Departamento compartido entre proyectos

*   **Pros**: un solo "Marketing" para toda la organización, con nombre único y presupuesto sumable entre proyectos (opción 1 con tabla de unión `project_budgets`).
*   **Cons**: hace falta una tabla de unión y una regla para borrar o renombrar un departamento con presupuestos asociados.
*   **Reason for Rejection**: Rejected by author: se eligió el departamento dentro de cada proyecto (`departments.project_id`). Consecuencia aceptada: nombres duplicados entre proyectos y ninguna suma de presupuesto por departamento entre proyectos.

### Alternativa C: Un único presupuesto en el departamento global

*   **Pros**: una tabla menos y ninguna tabla de unión.
*   **Cons**: un departamento que participa en varios proyectos tiene un solo monto, que no se puede repartir. No existe presupuesto por proyecto.
*   **Reason for Rejection**: Rejected by author: el requisito es un monto por área de cada proyecto, y esta opción no lo permite.

### Alternativa D: Fechas guardadas solo en la tarea

*   **Pros**: el Gantt es una consulta directa.
*   **Cons**: al mover un sprint, las fechas de sus tareas no cambian y el Gantt contradice al sprint.
*   **Reason for Rejection**: Rejected by author: reproduce el desfase entre sprint y cronograma que el diseño busca evitar. Se eligió el híbrido, que mantiene el desfase solo para las tareas con fechas propias.

### Alternativa E: Fechas solo calculadas

*   **Pros**: mover un sprint mueve todas sus tareas sin pasos manuales.
*   **Cons**: las tareas sin sprint no tendrían fechas. Un ciclo de dependencias impide el cálculo, y un grafo grande se recalcularía en cada petición.
*   **Reason for Rejection**: Rejected by author: no cubre las tareas sin sprint ni las excepciones con fecha propia.

### Alternativa F: WIP sobre todo el proyecto

*   **Pros**: Kanban clásico, sin tareas fuera del tablero (con o sin filtro de vista).
*   **Cons**: el límite no refleja la capacidad del sprint. El tablero acumula tareas de varios sprints y el sprint planning y el WIP se pisan.
*   **Reason for Rejection**: Rejected by author: se eligió el WIP de 3 tareas en "En desarrollo" contado solo dentro del sprint activo. Consecuencia aceptada: las tareas sin sprint no tienen tablero.

### Alternativa G: Sesión con cookie o proveedor externo (OIDC)

*   **Pros**: la sesión se revoca al instante y la cookie `HttpOnly` no queda expuesta a JavaScript. OIDC delega contraseñas y SSO.
*   **Cons**: la cookie exige tratar CSRF y cookies entre dominios si el frontend y el backend viven separados. OIDC añade una dependencia externa y configuración por entorno.
*   **Reason for Rejection**: Rejected by author: se eligió el JWT propio. Consecuencia aceptada: el token no se revoca antes de vencer.

### Alternativa H: Librerías de Gantt distintas de `frappe-gantt`

*   **Pros**: `dhtmlx-gantt` es la más completa; un SVG propio da control total de las marcas de retraso y conflicto.
*   **Cons**: `dhtmlx-gantt` en su edición estándar es GPLv2, lo que obliga a publicar el código o a comprar licencia. El SVG propio exige escribir la escala de tiempo, el zoom y las flechas de dependencia.
*   **Reason for Rejection**: Rejected by author: se eligió `frappe-gantt` (MIT, SVG). Consecuencia aceptada: hay que envolverla en un componente React y las marcas de retraso y conflicto se hacen con CSS.

### Alternativa I: Política de transición solo como texto

*   **Pros**: una tabla menos y ninguna regla de movimiento que probar.
*   **Cons**: el texto no se evalúa. Cualquiera puede mover una tarea a cualquier columna y la política queda sin efecto.
*   **Reason for Rejection**: Rejected by author: el README y el prompt piden una política de transición por columna y se decidió hacerla cumplir en el servidor. Consecuencia aceptada: hay que mantener una tabla de transiciones por proyecto.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

El proyecto está vacío. Todos los archivos son nuevos, salvo `README.md`. Las rutas son relativas a la raíz del repositorio. No se incluye código: solo firmas, esquemas y reglas.

### Orden de implementación y criterios de aceptación

| Fase | Contenido | Criterio de aceptación |
| --- | --- | --- |
| 1. Base | Repositorio, MySQL local, migración inicial, `auth`, `projects` | Un usuario se registra, inicia sesión, crea un proyecto y la migración se aplica y se revierte sin errores. |
| 2. Backlog y sprints | `backlog`, `sprints`, dependencias, hitos | Se crean historias y tareas, una dependencia que cierra un ciclo se rechaza con 422 y un segundo sprint activo se rechaza. |
| 3. Tablero | `board`, transiciones, límite WIP | Con 3 tareas del sprint activo en "En desarrollo", mover una cuarta devuelve 409, también con dos movimientos simultáneos. Mover de "Por hacer" a "Hecho" devuelve 422. |
| 4. Gantt | `gantt`, vista con `frappe-gantt` | El Gantt muestra fechas de la tarea o, si no tiene, las del sprint; marca retrasos y conflictos de dependencia. |
| 5. Presupuesto y cierre | `budget`, cierre de sprint, README | Se guarda un monto y una moneda por departamento; al cerrar un sprint, las tareas sin terminar vuelven al backlog. |

### Target Files to Create/Modify

#### Raíz

1.  `README.md` (**Modify**). Añadir cómo instalar, configurar `.env` y ejecutar backend, frontend y pruebas. Cambiar "Estado" de "sin código" a la fase en curso. Enlazar a este documento.
2.  `.gitignore` (**Create**). Excluir `.env`, `__pycache__/`, `.venv/`, `node_modules/`, `dist/` y datos locales de MySQL.
3.  `.env.example` (**Create**). Variables sin valores reales: `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES` (30), `CORS_ORIGINS`. Evita guardar secretos en el repositorio.
4.  `docker-compose.yml` (**Create**). Un servicio MySQL 8 con volumen y una segunda base para pruebas. Supone que Docker está disponible; si no, se instala MySQL a mano.

#### Backend (`backend/`)

5.  `backend/pyproject.toml` (**Create**). Dependencias: fastapi, uvicorn, sqlalchemy (2.x), alembic, pymysql, pydantic-settings, pyjwt, argon2-cffi. Desarrollo: pytest, pytest-cov, httpx, ruff. Fija las versiones.
6.  `backend/alembic.ini` (**Create**). Configuración de Alembic apuntando a `migrations/`.
7.  `backend/migrations/env.py` (**Create**). Lee `DATABASE_URL` desde la configuración y usa los metadatos de los modelos.
8.  `backend/migrations/versions/0001_initial_schema.py` (**Create**). Crea las once tablas del Technical Plan con sus claves foráneas. Incluye: índice único (`project_id`, `name`) en `departments`; `CHECK budget_amount >= 0`; `CHECK end_date >= start_date`; una columna generada `active_project_id` en `sprints` (igual a `project_id` si `status = 'active'`, nula si no) con índice único, que impide dos sprints activos por proyecto aunque falle la validación del servicio; `downgrade` que borra todo.
9.  `backend/app/__init__.py` (**Create**). Vacío; marca el paquete.
10. `backend/app/main.py` (**Create**). Crea la aplicación FastAPI, registra los routers de cada módulo bajo `/api/v1`, configura CORS desde `CORS_ORIGINS` y un `GET /health`.
11. `backend/app/config.py` (**Create**). Clase `Settings` (pydantic-settings) con las variables de `.env.example`; falla al arrancar si falta `JWT_SECRET`.
12. `backend/app/db.py` (**Create**). Motor y fábrica de sesiones de SQLAlchemy; dependencia `get_session()` que abre una sesión por petición y hace commit o rollback.
13. `backend/app/security.py` (**Create**). `hash_password`, `verify_password` (argon2), `create_token(user_id)`, `decode_token(token)`; el token lleva `sub` y `exp`.
14. `backend/app/deps.py` (**Create**). `get_current_user` (lee el Bearer, devuelve 401 si es inválido o venció) y `require_role(project_id, roles)` (devuelve 403 si el usuario no es miembro con alguno de esos roles). Concentra el control de acceso del punto 7 del Technical Plan.
15. `backend/app/models/__init__.py` (**Create**). Importa todos los modelos para que Alembic los vea.
16. `backend/app/models/user.py` (**Create**). Modelo `User`.
17. `backend/app/models/project.py` (**Create**). Modelos `Project` y `ProjectMember` (con enum de rol).
18. `backend/app/models/department.py` (**Create**). Modelo `Department` con `Numeric(14, 2)` y `CHAR(3)`.
19. `backend/app/models/backlog.py` (**Create**). Modelos `Epic`, `Task`, `TaskDependency` y `Milestone`.
20. `backend/app/models/sprint.py` (**Create**). Modelo `Sprint` con la columna generada `active_project_id` (`Computed`).
21. `backend/app/models/board.py` (**Create**). Modelos `BoardColumn` y `ColumnTransition`.

Cada módulo es un paquete con `__init__.py`, `schemas.py` (modelos Pydantic de entrada y salida), `service.py` (lógica y acceso a datos) y `router.py` (rutas finas que llaman al servicio). Un módulo solo importa el `service.py` de otro, nunca su `router.py`.

22. `backend/app/modules/auth/` (**Create**: `__init__.py`, `schemas.py`, `service.py`, `router.py`). `register` rechaza correos repetidos (409). `login` compara el hash y devuelve un token. `refresh` recibe un token válido y devuelve uno nuevo con 30 minutos. `me` devuelve el usuario.
23. `backend/app/modules/projects/` (**Create**: mismos cuatro archivos). Crear proyecto (el creador queda como Product Owner; se crean las cuatro columnas por defecto con WIP 3 en "En desarrollo" y las transiciones por defecto entre columnas contiguas), listar los proyectos del usuario, gestionar miembros y roles. Valida un solo Product Owner por proyecto.
24. `backend/app/modules/backlog/` (**Create**: mismos cuatro archivos). CRUD de épicas, tareas y hitos. `add_dependency(task_id, depends_on_id)` recorre el grafo y devuelve 422 si cierra un ciclo, o si ambas tareas son de proyectos distintos.
25. `backend/app/modules/sprints/` (**Create**: mismos cuatro archivos). `start` bloquea la fila del proyecto, comprueba que no haya otro activo y pasa el sprint a `active`. `close` guarda `review_notes` y `retro_notes`, pone `sprint_id` en nulo en las tareas cuya columna no es `is_done` y pasa el sprint a `closed`.
26. `backend/app/modules/board/` (**Create**: mismos cuatro archivos). `get_board` devuelve las columnas con las tareas del sprint activo. `move_task` primero comprueba que el par (columna actual, destino) esté en `column_transitions` (422 con los destinos permitidos si no) y después hace el control del WIP en una transacción: bloquea con `SELECT … FOR UPDATE` las tareas de la columna destino en el sprint activo, cuenta y, si el conteo iguala al `wip_limit`, devuelve 409 con `{limit, count}`. Solo cuenta tareas con `sprint_id` igual al sprint activo; una tarea sin sprint no se puede mover (422). Edición de columnas y de transiciones permitidas (`PUT …/columns/transitions` valida que ambas columnas sean del proyecto) solo para el Scrum Master.
27. `backend/app/modules/gantt/` (**Create**: mismos cuatro archivos). `get_gantt` devuelve, por tarea: `start`, `end`, `source` (`task` o `sprint`), `is_late`, dependencias y un indicador `conflict`. `effective_dates(task, sprint)` es una función pura, separada para probarla sin base de datos. Las tareas sin fechas van en una lista aparte `undated`. También devuelve los hitos.
28. `backend/app/modules/budget/` (**Create**: mismos cuatro archivos). CRUD de departamentos; valida `budget_amount >= 0` y que `currency` sea un código de tres letras mayúsculas. Solo Product Owner y Scrum Master escriben.

#### Pruebas del backend (`backend/tests/`)

Las pruebas usan la base MySQL de pruebas de `docker-compose.yml`, no SQLite, porque el bloqueo de filas del WIP y la columna generada no se comportan igual.

29. `backend/tests/conftest.py` (**Create**). Fixtures: base limpia por prueba, cliente HTTP, usuarios y un proyecto de ejemplo con cada rol.
30. `backend/tests/test_auth.py` (**Create**). Registro, correo repetido (409), login incorrecto (401), token vencido (401), refresh.
31. `backend/tests/test_roles.py` (**Create**). Cada rol puede o no hacer las acciones del punto 7 (403 si no).
32. `backend/tests/test_backlog.py` (**Create**). Dependencia que cierra un ciclo (422), dependencia entre proyectos (422).
33. `backend/tests/test_sprints.py` (**Create**). Un segundo sprint activo (rechazado), cierre de sprint devuelve tareas sin terminar al backlog.
34. `backend/tests/test_board_wip.py` (**Create**). Cuarta tarea a "En desarrollo" (409); tarea sin sprint (422); dos movimientos simultáneos a la última plaza (uno gana, otro 409).
35. `backend/tests/test_gantt_dates.py` (**Create**). Hereda fechas del sprint; fechas propias mandan; tarea sin fechas en `undated`; retraso; conflicto de dependencia.
36. `backend/tests/test_budget.py` (**Create**). Monto negativo (422), moneda inválida (422), nombre duplicado en el proyecto (409), el mismo nombre en otro proyecto (permitido).
36b. `backend/tests/test_board_transitions.py` (**Create**). Movimiento a columna contigua (permitido), salto no permitido (422 con destinos permitidos), transiciones editadas por el Scrum Master (permitido) y por un developer (403), columna de otro proyecto en la tabla (422).

#### Frontend (`frontend/`)

37. `frontend/package.json` (**Create**). React, react-router, `@dnd-kit/core`, `frappe-gantt`, TypeScript, Vite, vitest, Testing Library, eslint. Versiones fijas. Scripts `dev`, `build`, `test`, `lint`.
38. `frontend/tsconfig.json` (**Create**). TypeScript en modo estricto.
39. `frontend/vite.config.ts` (**Create**). Plugin de React, proxy de `/api` al backend en desarrollo, configuración de vitest.
40. `frontend/eslint.config.js` (**Create**). Reglas de TypeScript y de React.
41. `frontend/index.html` (**Create**). Punto de entrada de Vite.
42. `frontend/src/main.tsx` (**Create**). Monta la aplicación.
43. `frontend/src/App.tsx` (**Create**). Rutas: `/login`, `/projects`, `/projects/:id/backlog`, `/sprints`, `/board`, `/gantt`, `/budget`. Redirige a `/login` sin sesión.
44. `frontend/src/api/client.ts` (**Create**). Funciones `get/post/patch/delete` que añaden el Bearer, renuevan el token antes de que venza y redirigen a `/login` ante un 401.
45. `frontend/src/api/types.ts` (**Create**). Tipos TypeScript de las respuestas, escritos a mano a partir de los esquemas del backend.
46. `frontend/src/auth/AuthContext.tsx` (**Create**). Estado de sesión; guarda el token en `sessionStorage`.
47. `frontend/src/auth/LoginPage.tsx` (**Create**). Formulario de registro e inicio de sesión.
48. `frontend/src/pages/ProjectsPage.tsx` (**Create**). Lista y creación de proyectos, miembros y roles.
49. `frontend/src/pages/BacklogPage.tsx` (**Create**). Backlog, épicas, historias, tareas, dependencias e hitos.
50. `frontend/src/pages/SprintsPage.tsx` (**Create**). Crear sprints, asignar tareas, iniciar y cerrar con las notas de review y retro.
51. `frontend/src/pages/BoardPage.tsx` (**Create**). Tablero del sprint activo con arrastrar y soltar. Resalta las columnas destino permitidas al arrastrar. Al recibir 409, devuelve la tarjeta a su columna y muestra "Límite WIP alcanzado (3)"; al recibir 422 por transición, la devuelve y muestra los destinos permitidos.
52. `frontend/src/pages/GanttPage.tsx` (**Create**). Pide `/gantt` y pasa los datos al componente; muestra la lista "Sin fecha".
53. `frontend/src/pages/BudgetPage.tsx` (**Create**). Tabla de departamentos con monto y moneda; edición solo para PO y SM.
54. `frontend/src/components/BoardColumn.tsx` (**Create**). Columna con su límite visible ("2 / 3") y zona de soltar.
55. `frontend/src/components/TaskCard.tsx` (**Create**). Tarjeta arrastrable con título, puntos y responsable.
56. `frontend/src/components/GanttChart.tsx` (**Create**). Envuelve `frappe-gantt`: crea la instancia al montar, la rehace cuando cambian los datos, la destruye al desmontar. Marca retraso y conflicto con clases CSS. Es de solo lectura (sin arrastrar barras).
57. `frontend/src/components/TaskForm.tsx` (**Create**). Formulario compartido de tarea (título, estimación, épica, fechas opcionales).
58. `frontend/src/styles.css` (**Create**). Estilos globales y de las marcas del Gantt.
59. `frontend/src/components/GanttChart.test.tsx` (**Create**). La instancia se crea una sola vez, se destruye al desmontar y las clases de retraso y conflicto se aplican.
60. `frontend/src/pages/BoardPage.test.tsx` (**Create**). Ante un 409 la tarjeta vuelve a su columna y aparece el mensaje.

### Verification Plan

*   **Compilation/Build**: `npm run build` en `frontend/`; `alembic upgrade head` y `alembic downgrade base` en `backend/` contra la base de pruebas.
*   **Unit Tests**: `pytest` en `backend/`; `npm test` en `frontend/`.
*   **Static Analysis & Linting**: `ruff check` en `backend/`; `npm run lint` en `frontend/`.
*   **Test Coverage Requirement**: 80 % de líneas en `backend/app/modules/` (`pytest --cov`). Sin umbral en el frontend.
*   **E2E/Integration**: recorrido manual con la aplicación corriendo. Registrarse, crear un proyecto, crear 5 tareas en un sprint, iniciar el sprint, mover 3 tareas a "En desarrollo" y comprobar que la cuarta se rechaza; abrir el Gantt y ver las fechas del sprint; fijar fechas propias en una tarea y ver que mandan; cerrar el sprint y ver que las tareas sin terminar vuelven al backlog.

--------------------------------------------------------------------------------

### Future Improvements

*   **Ruta crítica y línea base** sobre el grafo de dependencias (fase 2).
*   **Edición del Gantt** arrastrando barras, con reglas de propagación.
*   **Seguimiento del gasto real** contra el presupuesto de cada departamento.
*   **Revocación de tokens** (lista de bloqueo) o cambio a sesiones de servidor.
*   **Políticas de transición por rol** (por ejemplo, solo el Product Owner mueve a "Hecho").

--------------------------------------------------------------------------------

*Drafted with EGM*
