# Sistema de Gestión de Proyectos — Plan de implementación

*   **Author:** felixortega1
*   **Status:** Draft
*   **Date:** 2026-11-17

> **Cambios posteriores al plan (2026-11-18):** se eliminó la épica (modelo `Epic` y campo `Task.epic`) porque solo agrupaba etiquetas y duplicaba a la historia. Se añadieron la empresa (`Company`), las fechas y los objetivos de cada proyecto, la historia con solicitante (`stakeholder`), los comentarios sobre historias y actividades, y la asignación de una historia completa a un sprint. El flujo de uso es empresa, proyecto, historias, actividades (backlog) y sprints. Consulta [docs/guia-de-uso.md](../guia-de-uso.md).

--------------------------------------------------------------------------------

## Overview

Una aplicación web para seguir proyectos con Scrum. Cada tarea se guarda una sola vez y se ve de dos formas: un tablero Kanban con límites de trabajo en curso (WIP) y un diagrama de Gantt de solo lectura. El sistema guarda además un monto de presupuesto, ingresado a mano, para cada área del proyecto. Un área es un departamento de la empresa (por ejemplo contabilidad, operaciones o marketing).

El proyecto no tiene código. Este documento es el plan de implementación: define qué se construye primero (el MVP) y, en el Detailed Implementation Plan, lista los archivos que hay que crear. El análisis comparativo de herramientas, la priorización MoSCoW (clasificar requisitos en Must, Should, Could y Won't) y las métricas de éxito que pide [plan-prompt.md](../plan-prompt.md), el prompt con el que se pidió este plan, quedan fuera de este documento y del MVP. Stack decidido: una sola aplicación Django escrita en Python, con plantillas HTML, HTMX y MySQL, en un monorepo (un solo repositorio con la aplicación, la documentación y la configuración de desarrollo). El único JavaScript son tres librerías pequeñas incluidas en el repositorio y dos archivos propios cortos (arrastrar tarjetas y dibujar el Gantt). Contexto de origen: [README.md](../../README.md). Los términos propios se explican en [Términos](#términos).

## The Problem

Los equipos que trabajan con Scrum suelen repartir su trabajo entre varias herramientas: una para el backlog y los sprints, otra para el tablero, otra para el cronograma y una hoja de cálculo para el presupuesto. Esta es la premisa del autor, sin una fuente que la respalde. Las fechas, el estado y el avance de una misma tarea se duplican y pueden desfasarse entre esas herramientas.

La propuesta es una sola fuente de verdad, la tarea (estado, estimación, dependencias, sprint). El tablero y el Gantt se calculan a partir de ella, así que no pueden contradecirse, salvo en las tareas con fechas propias ([regla 4](#reglas-del-sistema)).

**Diferencial frente a Jira y Linear.** Lo que ofrece esta herramienta es tener, bajo la misma fuente de verdad, el tablero Kanban con WIP, el Gantt derivado de los sprints y el presupuesto por departamento de cada proyecto, sin una hoja de cálculo aparte, y que una organización la despliegue por sí misma con un proceso Django y una base MySQL. Es una premisa del autor: este documento no comparó esas herramientas ni verificó si Jira o Linear cubren el presupuesto por departamento (por ejemplo con extensiones); el análisis comparativo queda fuera de este documento. Usar Jira o Linear se documenta en la [Alternativa O](#alternativa-o-usar-jira-o-linear).

## Goals

*   **G1. Backlog y sprints:** crear proyectos, un product backlog y sprints con su sprint backlog, y reflejar en el sistema los roles Scrum (Product Owner, Scrum Master, equipo de desarrollo).
*   **G2. Tablero Kanban:** columnas con una política de transición por columna y un límite WIP que el servidor hace cumplir (no solo el navegador).
*   **G3. Gantt de solo lectura:** mostrar tareas, dependencias e hitos con fechas calculadas a partir de las tareas y los sprints. No hay una tabla de fechas del Gantt aparte; las tareas pueden tener fechas propias.
*   **G4. Presupuesto por área:** guardar un monto y una moneda por cada departamento del proyecto, ingresados a mano.
*   **G5. Una sola fuente de verdad:** mover una tarea de columna o de sprint cambia tablero y Gantt sin pasos manuales, salvo en las tareas con fechas propias.
*   **G6. Despliegue simple:** el sistema corre como un solo proceso Django (que también sirve los archivos estáticos) y una base MySQL, sin otros servicios. Docker se usa solo para MySQL local.

## Non-Goals

*   Facturación, registro de horas y seguimiento del gasto real contra el presupuesto.
*   App móvil, API pública para otros clientes, integraciones con otras herramientas y notificaciones.
*   Edición del Gantt arrastrando barras, ruta crítica y línea base (versión posterior).
*   Comentarios, adjuntos, etiquetas y registro de auditoría.
*   Pantallas y cálculo de velocidad: el MVP solo guarda el historial de cada sprint cerrado (`SprintTask`). Burndown y métricas de flujo no son posibles con ese historial, porque solo guarda el estado al cierre.
*   Multi-tenant: se asume una sola organización por instalación.
*   Actualización en vivo entre usuarios (WebSockets): el tablero se actualiza al recargar o al actuar.
*   Objetivos medidos de disponibilidad y latencia. El plan declara supuestos de escala (ver [Supuestos](#supuestos)), no metas.

## Decisiones de diseño tomadas por el autor

*   **Aplicación web solo en Python:** Django con plantillas y HTMX; sin React ni proceso de compilación del frontend. Monorepo.
*   **Área = departamento de la empresa**, definido dentro de cada proyecto (`Department` con `project`). El monto y la moneda están en la misma fila. Un departamento no se comparte entre proyectos.
*   **Fechas del Gantt híbridas:** la tarea hereda las fechas de su sprint. Si tiene fechas propias, estas mandan.
*   **WIP:** máximo 3 tareas en la columna "En desarrollo", contadas solo dentro del sprint activo.
*   **Autenticación:** sesiones de Django con usuarios en MySQL. Registro abierto; sesión de 8 horas; cierre de sesión que la borra en el servidor.
*   **Política de transición hecha cumplir por el servidor:** una tabla de transiciones permitidas entre columnas. Por defecto solo se permite mover a la columna contigua, en ambos sentidos; "Por hacer → Hecho" se rechaza por defecto. El Scrum Master puede editar las transiciones. Crear una columna la inserta antes de la columna `is_done` y siembra sus transiciones contiguas; borrar columnas no se admite en el MVP (solo se edita nombre, WIP y texto de la política).
*   **Interfaz:** plantillas de Django con HTMX para actualizar partes de la página, SortableJS para arrastrar tarjetas y `frappe-gantt` (MIT, SVG) para el Gantt. Los tres se descargan una vez y se guardan en el repositorio (`static/vendor/`).
*   **Roles:** el Product Owner tiene también todos los permisos del Scrum Master. El creador de un proyecto queda como Product Owner y puede operarlo solo.
*   **Capas entre apps:** las apps tienen un orden fijo y las operaciones sobre tareas viven en `backlog.services` (ver Componentes).
*   **Base de datos:** MySQL 8.4 LTS. El sprint activo único se garantiza con un `GeneratedField` y un `UniqueConstraint`.
*   **Idioma:** identificadores del código en inglés; textos de la interfaz y documentación en español.

## Open Questions

*   **Versión y opciones de `frappe-gantt`:** se fijan al terminar la prueba de concepto de F4, que decide también cómo se dibujan los hitos y cómo se combinan las clases `is_late` y `conflict`.
*   **Equipo y plazo:** tamaño del equipo y fecha objetivo del MVP, que se necesitan para dimensionar las fases.

## Technical Plan (Architecture)

### Términos

*   **Backlog (o product backlog):** las tareas de un proyecto que no tienen sprint. No es una tabla aparte. **Sprint backlog:** las tareas que tienen ese sprint.
*   **Daily:** la reunión diaria de Scrum; en el sistema es el tablero del sprint activo.
*   **Equipo de desarrollo:** los miembros con rol `developer`.
*   **Área:** un departamento de la empresa (modelo `Department`).
*   **WIP:** el número máximo de tareas que puede haber a la vez en una columna.
*   **Servicio:** una función de un `services.py` que ejecuta un caso de uso completo (por ejemplo, mover una tarea) dentro de una transacción.
*   **Fragmento:** un trozo de HTML que HTMX pide al servidor y coloca en lugar de otro trozo de la página, sin recargarla. **HTMX:** una librería que lo hace con atributos HTML (`hx-…`).
*   **`undated`:** la lista de tareas que el Gantt no puede dibujar por no tener fechas efectivas válidas (regla 4).
*   **Operador:** la persona que administra la instalación (ver Límites conocidos).

### Componentes

Un solo proyecto Django (`config/`) con una app por módulo, más MySQL. Es un monolito modular: cada app tiene su paquete y las dependencias entre ellas siguen un orden de capas, de abajo hacia arriba: `core` (sin modelos), `accounts`, `board`, `projects`, `sprints`, `backlog`, y encima `gantt` y `budget`. `board.services` no importa nada de `projects`: recibe el proyecto ya cargado, y por eso `projects.services` puede llamar a `board.services.create_default_board`. Un `services.py` solo importa modelos y servicios de capas inferiores; los modelos se refieren a los de otras apps con cadenas (`"sprints.Sprint"`) y las vistas pueden usar los servicios de cualquier app. Por eso todas las operaciones que escriben tareas (`apply_placement`, `assign_sprint`, `move_task`, `close_sprint`) y la consulta del tablero (`get_board`) viven en `backlog.services`, dueña de `Task`; `board` solo guarda columnas y transiciones. `core.permissions` obtiene los modelos con `django.apps.apps.get_model`, sin importarlos al cargar el módulo. Una prueba comprueba el orden de capas leyendo los `import` de cada `services.py` y falla si importa una app de una capa superior. Las vistas devuelven HTML. Cuando una acción solo cambia una parte de la página (por ejemplo, mover una tarjeta), HTMX pide un fragmento HTML y lo reemplaza; si el navegador no tiene JavaScript, el mismo formulario funciona como envío normal con redirección.

```text
 Navegador (HTML de Django + HTMX + SortableJS + frappe-gantt)
   ├─ Páginas: Backlog, Sprints, Tablero, Columnas, Gantt, Presupuesto
   └─ Formularios POST con token CSRF y cookie de sesión HttpOnly
          │  HTTPS, HTML (y fragmentos HTML para HTMX)
          ▼
 Django (proyecto config/, apps en apps/)
   ├─ accounts    usuario propio (correo como login), registro, login, logout
   ├─ projects    proyectos, miembros y roles Scrum
   ├─ board       columnas y transiciones (modelos y edición)
   ├─ sprints     sprints, notas de review y retro
   ├─ backlog     historias, tareas, dependencias, hitos,
   │              movimientos, límite WIP y consulta del tablero
   ├─ gantt       cálculo de fechas efectivas y marcas de retraso
   ├─ budget      departamentos con monto y moneda
   └─ core        permisos por rol y utilidades de HTMX
          │  Django ORM (una conexión por petición)
          ▼
 MySQL 8.4 (InnoDB)  ── migraciones de Django
```

### Modelo de datos

Convenciones: ids `BigAutoField` (`BIGINT AUTO_INCREMENT`); textos cortos `CharField(max_length=200)`; descripciones y notas `TextField`; fechas `DateField`; marcas de tiempo `DateTimeField` con `USE_TZ = True` (se guardan en UTC); `kind`, `status` y `role` son `CharField` con `choices` y un `CheckConstraint`. Las restricciones `CHECK` exigen MySQL ≥ 8.0.16 (el plan fija 8.4 LTS). Django aplica `on_delete` en Python y no en la base: `PROTECT` por defecto; `CASCADE` en `ProjectMember`, `Department`, `Milestone`, `BoardColumn` y `ColumnTransition` cuando se borra su proyecto (el MVP no ofrece borrar proyectos; `Sprint`, `Task` y `TaskDependency` usan `PROTECT`).

| Modelo (app) | Campos | Reglas |
| --- | --- | --- |
| `User` (accounts) | `id`, `email` (único, en minúsculas), `password`, `name`, `is_active`, `is_staff`, `is_superuser`, `date_joined` | Modelo propio (`AbstractBaseUser` más `PermissionsMixin`) con `USERNAME_FIELD = "email"` y sin `username`. Contraseña con hash argon2. |
| `Project` (projects) | `id`, `name`, `description`, `created_by`, `created_at` | |
| `ProjectMember` (projects) | `project`, `user`, `role` | Único (`project`, `user`). `role` es `product_owner`, `scrum_master` o `developer`. Un proyecto tiene un solo Product Owner (lo valida el servicio). |
| `Department` (budget) | `id`, `project`, `name`, `budget_amount` DecimalField(14,2), `currency` CharField(3), `created_at`, `updated_at`, `updated_by` | Único (`project`, `name`). `CHECK budget_amount >= 0`. La moneda es un código de tres letras mayúsculas; solo se comprueba el formato. |
| `Sprint` (sprints) | `id`, `project`, `name`, `goal`, `start_date`, `end_date`, `status`, `review_notes`, `retro_notes`, `created_at`, `updated_at` | `status` es `planned`, `active` o `closed`. Solo un sprint `active` por proyecto: el campo `active_project_id` es un `GeneratedField(expression=Case(When(status="active", then=F("project_id")), default=Value(None)), output_field=BigIntegerField(null=True), db_persist=False)` (virtual: igual a `project` cuando `status = 'active'` y nulo en otro caso) con un `UniqueConstraint(fields=["active_project_id"])`; MySQL admite varios NULL en un índice único. `start_date` y `end_date` admiten nulo mientras el sprint está `planned`; `start` las exige. `CHECK end_date >= start_date` (MySQL lo da por válido si alguna es nula). |
| `BoardColumn` (board) | `id`, `project`, `name`, `position`, `wip_limit` (nulo = sin límite), `policy_text`, `is_done` | Por defecto: "Por hacer", "En desarrollo" (`wip_limit` 3), "En revisión", "Hecho" (`is_done`). `policy_text` describe la política y no se evalúa. |
| `ColumnTransition` (board) | `from_column`, `to_column` | Único (`from_column`, `to_column`). Ambas columnas son del mismo proyecto. |
| `Task` (backlog) | `id`, `project`, `sprint` (nulo), `parent` (nulo), `kind`, `title`, `description`, `column` (nulo en historias y en tareas sin sprint), `estimate_points` PositiveSmallIntegerField (nulo), `assignee` (nulo), `start_date` (nulo), `due_date` (nulo), `created_at`, `updated_at` | `kind` es `story` o `task`. `parent` apunta a una `story`; una `story` no tiene padre. `sprint`, `parent`, `column` y `assignee` son del mismo proyecto y el responsable es miembro (salvo en tareas terminadas, que conservan al responsable aunque lo quiten del proyecto). Solo una `task` puede tener `sprint`, `column`, fechas o dependencias. `sprint` y `column` van juntos: o ambos nulos o ambos con valor, y lo garantiza un `CheckConstraint` en la base. |
| `TaskDependency` (backlog) | `task`, `depends_on` | Único (`task`, `depends_on`). `CHECK task <> depends_on`. Todas las dependencias son de tipo fin-a-inicio. Ambas son tareas (`kind = task`) del mismo proyecto. No se permite un ciclo. |
| `Milestone` (backlog) | `id`, `project`, `name`, `date` | |
| `SprintTask` (backlog) | `sprint`, `task`, `column_name`, `is_done`, `estimate_points` | Único (`sprint`, `task`). Historial de cada sprint: al cerrarlo (solo sprints cerrados), `close_sprint` guarda una fila por cada tarea que estaba en él, con el nombre de su columna final, si estaba terminada (`is_done`) y una copia de sus puntos. Se escribe una sola vez y no se edita. |

Semántica de `Task`: las tareas (`kind = task`) son lo que se planifica: pueden tener sprint, columna, fechas y dependencias, y las del sprint activo aparecen en el tablero y cuentan para el WIP. Las historias (`kind = story`) solo agrupan tareas mediante `parent`: no tienen sprint, columna, fechas ni dependencias, y no se dibujan en el Gantt. Una tarea sin sprint no tiene columna; `assign_sprint` le da el sprint y la primera columna (la de menor `position`). Dentro de una columna las tarjetas se ordenan por `id`: no hay orden manual en el MVP. `estimate_points` es informativo y no entra en ningún cálculo.

Política de borrado: borrar una tarea con hijas, con dependencias, con sprint o con filas en `SprintTask` devuelve 409; quitar a un miembro que es Product Owner, o que tiene tareas asignadas que no están en una columna `is_done`, devuelve 409. Las tareas terminadas conservan su responsable aunque lo quiten del proyecto.

### Reglas del sistema

1.  **Fuente de verdad.** La tarea guarda su estado (`column`), su sprint y sus dependencias. El tablero y el Gantt se calculan a partir de ella.
2.  **Tablero.** `GET /projects/<id>/board/` muestra las tareas del sprint activo agrupadas por columna. Las tareas sin sprint, y las de un sprint `planned` o `closed`, no aparecen en el tablero. Las tareas terminadas de un sprint cerrado conservan su sprint y se ven en la página de sprints y en el Gantt.
3.  **Mover y WIP.** `backlog.services.move_task(task, column, user)` hace sus comprobaciones dentro de `transaction.atomic()`, después de tomar el bloqueo del proyecto (regla 10). Con la tarea releída bajo el bloqueo, valida en este orden: (1) permiso (regla 7); (2) la tarea es de `kind = task`, tiene sprint y ese sprint es el activo, y la columna destino es del mismo proyecto, si no `422`; (3) si la columna destino es la actual, no hace nada y responde 200; (4) el par (columna actual, columna destino) está en `ColumnTransition`, si no `422` con las columnas destino permitidas; (5) el límite WIP, que aplica `apply_placement`: se cuentan las tareas de esa columna en el sprint activo, sin contar la que se mueve, y si `count >= wip_limit` se responde `409 Conflict` con el límite y el conteo; solo entonces se escribe la tarea. `DATABASES` fija `isolation_level = "read committed"` para que el conteo vea los commits ya hechos. `wip_limit` nulo significa sin límite y `0` bloquea toda entrada. El límite solo se comprueba al entrar: bajarlo por debajo del conteo actual no expulsa tareas. Como todas las operaciones de la regla 10 toman el mismo bloqueo, no hay deadlocks entre ellas (cada una toma un solo bloqueo) y el servicio no reintenta. Editar el `wip_limit` de una columna no toma ese bloqueo: un movimiento en curso usa el valor que leyó y el nuevo rige desde el siguiente. El navegador también resalta los destinos permitidos, pero la regla vive en el servidor.
4.  **Fechas efectivas del Gantt.** Inicio y fin se resuelven por separado. `inicio = task.start_date`, si no existe `sprint.start_date`. `fin = task.due_date`, si no existe `sprint.end_date`. Si no hay valor en ninguno de los dos sitios (sin sprint, o con un sprint `planned` de fechas nulas), el inicio o el fin queda sin definir. `start_source` y `end_source` valen `task` o `sprint`. Una tarea sin inicio ni fin efectivos, con solo uno de los dos (tenga o no sprint), o cuyo fin efectivo es anterior a su inicio, no se dibuja y va a la lista `undated`, con su motivo (`sin fechas`, `una sola fecha` o `fin anterior al inicio`). Si una tarea tiene fechas propias, mover su sprint no las cambia. Los hitos se listan siempre y se dibujan con su fecha en una fila aparte si la prueba de concepto de F4 lo permite; no entran en dependencias ni en el retraso en el MVP.
5.  **Dependencias.** Al crear una dependencia, el servidor rechaza con `422` una autodependencia, una dependencia duplicada, una dependencia entre proyectos distintos, una que involucre una historia y una que cierre un ciclo (recorrido del grafo desde `depends_on`). El Gantt marca `conflict` cuando el inicio del sucesor es anterior o igual al fin del predecesor (el fin es inclusivo); es falso si alguna de las dos no tiene fechas efectivas, y también cuando ambas heredan inicio y fin del mismo sprint (tendrían siempre las mismas fechas); en el caso mixto se comparan las fechas efectivas. No reprograma nada.
6.  **Retraso.** Una tarea cuya fecha efectiva de fin es anterior a hoy y cuya columna no es `is_done` se marca `is_late`; sin fecha efectiva de fin, `is_late` es falso. Una tarea sin sprint (y por tanto sin columna) nunca se marca `is_late`. "Hoy" es `timezone.localdate()`, en la zona horaria de la instalación (`TIME_ZONE`, tomada de `APP_TIMEZONE`).
7.  **Roles y permisos.** Cada vista pasa por un decorador de `core.permissions` que resuelve el proyecto (directo o cargando la tarea, el sprint o el departamento por su id) y comprueba el rol. Un usuario que no es miembro recibe 404; un miembro sin el rol necesario recibe 403; sin sesión se redirige a `/accounts/login/`.

    | Acción | Product Owner | Scrum Master | Developer |
    | --- | --- | --- | --- |
    | Crear un proyecto | cualquier usuario con sesión; el creador queda como Product Owner | n/a | n/a |
    | Leer todo el proyecto, incluido el presupuesto | sí | sí | sí |
    | Crear historias, tareas e hitos | sí | no | no |
    | Editar tareas y sus dependencias (sin cambiar el responsable) | sí | no | solo sus tareas |
    | Asignar o cambiar el responsable | sí | sí | no |
    | Borrar tareas | sí | no | no |
    | Crear y editar sprints, abrirlos, cerrarlos (con notas de review y retro) y asignarles tareas | sí | sí | no |
    | Mover una tarea | sí | sí | si es el responsable, o si no tiene responsable |
    | Editar columnas, WIP y transiciones | sí | sí | no |
    | Editar departamentos y presupuesto | sí | sí | no |
    | Gestionar miembros y roles | sí | no | no |

    El Product Owner tiene todos los permisos del Scrum Master, así que quien crea un proyecto puede operarlo solo. "Sus tareas" significa `assignee` igual al usuario; asignar o cambiar el responsable es un permiso aparte (Product Owner y Scrum Master) y el formulario de edición del Developer no incluye `assignee`. `core.permissions` ofrece `can_edit_task(user, task)` y `can_move_task(user, task)` para estas comprobaciones por objeto. El Product Owner se transfiere con `transfer_product_owner(project, nuevo_po, rol_del_saliente)`, en una sola transacción: el saliente pasa al rol indicado (`scrum_master` o `developer`) y el nuevo pasa a `product_owner`. El endpoint de cambio de rol rechaza `product_owner` con 422: solo `transfer_product_owner` crea un Product Owner. Un Developer no "toma" tareas: si una tarea no tiene responsable puede moverla, pero seguirá sin responsable hasta que un Product Owner o Scrum Master se lo asigne. Que un Developer pueda mover una tarea sin responsable, pero no editarla, es intencional.
8.  **Eventos Scrum y estados del sprint.** Sprint planning: asignar tareas del backlog al sprint (también cuando está `planned`; el tablero solo muestra el activo) y pasarlo a `active`. `start` solo vale desde `planned` y exige `start_date` y `end_date`; un segundo sprint activo se rechaza con 409. `close` solo vale desde `active`. Daily: el tablero. Review y retrospectiva: los campos `review_notes` y `retro_notes`, que se editan al cerrar. Al cerrar un sprint (`close_sprint`, regla 10), las tareas que no están en una columna `is_done` quedan sin sprint y sin columna y vuelven al backlog; las terminadas conservan ambos. Antes de modificar las tareas, `close_sprint` guarda una fila de `SprintTask` por cada tarea del sprint (regla 10), en la misma transacción.
9.  **Presupuesto.** `Department` guarda un monto y una moneda por departamento y proyecto. El sistema no compara el monto con ningún gasto.
10. **Único escritor de columna y sprint y bloqueo por proyecto.** `column` y `sprint` solo se escriben mediante `backlog.services.apply_placement(task, sprint, column)`, que usan `assign_sprint`, `move_task` y `close_sprint` y que aplica el límite WIP cuando el sprint de destino está activo. Estas cinco operaciones empiezan con `core.locks.lock_project(project_id)`, que obtiene `Project` con `apps.get_model` (para que `board` no importe `projects`) y ejecuta `Project.objects.select_for_update().get(pk=…)` dentro de `transaction.atomic()` y releen la tarea y el sprint después de tomarlo: `start_sprint` (en `sprints.services`), `assign_sprint`, `move_task` y `close_sprint` (en `backlog.services`) y `create_column` (en `board.services`). `apply_placement` no toma el bloqueo: lo toma quien la llama. Así dos de ellas sobre el mismo proyecto nunca se ejecutan a la vez (a la escala del plan, 50 usuarios y 2.000 tareas por proyecto, esa serialización es aceptable). Los formularios de tareas y de sprints no incluyen esos campos (ni `status`), y los servicios de edición guardan solo los campos del formulario (`save(update_fields=…)`), de modo que una edición con datos obsoletos no pisa `column`, `sprint` ni `status`. `assign_sprint` (`POST /tasks/<id>/assign-sprint/`) exige `kind = task`, que la tarea no tenga sprint (si ya lo tiene, `422`) y un sprint `planned` o `active`, deja la tarea en la primera columna y, si el sprint está activo, aplica el WIP, por lo que puede responder 409. Una tarea nueva no tiene sprint ni columna. `close_sprint` deja sin sprint ni columna a las tareas que no están en una columna `is_done`; como no entran en ninguna columna, no aplica el WIP. Antes de escribir, guarda el historial en `SprintTask`.

### Rutas (HTML)

No hay API JSON. Las rutas devuelven páginas HTML; las marcadas con (H) devuelven un fragmento si la petición trae la cabecera `HX-Request` y redirigen a la página completa si no la trae. Todos los `POST` exigen el token CSRF de Django (HTMX lo envía mediante `hx-headers` en `<body>`). En el MVP los hitos solo se crean y se listan, y los sprints no se borran. Una petición HTMX sin sesión recibe `401` con la cabecera `HX-Redirect: /accounts/login/`.

| App | Rutas principales |
| --- | --- |
| accounts | `GET/POST /accounts/register/`, `GET/POST /accounts/login/`, `POST /accounts/logout/` |
| projects | `GET /` (lista de proyectos), `GET/POST /projects/new/`, `GET /projects/<id>/` (redirige a la lista de proyectos en F1 y al tablero desde F3), `GET /projects/<id>/members/`, `POST /projects/<id>/members/add/`, `POST /projects/<id>/members/<user_id>/role/`, `POST /projects/<id>/members/<user_id>/remove/`, `POST /projects/<id>/transfer-po/` |
| backlog | `GET /projects/<id>/backlog/`, `POST /projects/<id>/tasks/new/`, `GET/POST /tasks/<id>/edit/`, `POST /tasks/<id>/delete/`, `POST /tasks/<id>/assign-sprint/`, `POST /tasks/<id>/dependencies/add/`, `POST /tasks/<id>/dependencies/<dep_id>/delete/`, `POST /projects/<id>/milestones/new/` |
| sprints | `GET /projects/<id>/sprints/`, `POST /projects/<id>/sprints/new/`, `POST /sprints/<id>/edit/`, `POST /sprints/<id>/start/`, `POST /sprints/<id>/close/` |
| board | `GET /projects/<id>/board/`, `POST /tasks/<id>/move/` (H), `GET /projects/<id>/columns/`, `POST /projects/<id>/columns/new/`, `POST /columns/<id>/edit/`, `POST /projects/<id>/columns/transitions/` |
| gantt | `GET /projects/<id>/gantt/` |
| budget | `GET /projects/<id>/budget/`, `POST /projects/<id>/departments/new/`, `POST /departments/<id>/edit/`, `POST /departments/<id>/delete/` |

### Contratos de las respuestas

*   **Formularios inválidos:** la página se vuelve a dibujar con los errores y estado `422`, también cuando el error es de unicidad (correo repetido, nombre de departamento duplicado, dependencia duplicada). El `409` queda para conflictos de estado y carreras (WIP, segundo sprint activo, borrados protegidos). Un formulario válido responde con redirección (`302`) a la página de origen (patrón post/redirect/get).
*   **Mover (`POST /tasks/<id>/move/`):** recibe `column_id`. Con HTMX devuelve el fragmento `board/_board.html` (el tablero completo, con las tarjetas en su sitio y un mensaje) y estado `200`, `409` (WIP) o `422` (transición o sprint no activo). El mensaje del `409` incluye el límite y el conteo; el del `422` incluye los nombres de las columnas permitidas. Sin HTMX redirige al tablero y usa el sistema de mensajes de Django. `board.views.move` captura `Conflict` y `Unprocessable` y es quien renderiza `board/_board.html` con el mensaje; cualquier otra excepción la maneja `ServiceExceptionMiddleware` con una página de error o con un mensaje y una redirección, y nunca devuelve el fragmento del tablero. `board.js` hace que HTMX acepte los estados `409` y `422` para reemplazar el tablero y, ante cualquier otra respuesta (403, 404, 5xx o error de red), recarga el tablero, para que la tarjeta que SortableJS ya movió no quede en la columna equivocada.
*   **Tablero:** `GET /projects/<id>/board/` dibuja el sprint activo y sus columnas, cada una con "conteo / límite", sus tarjetas (ordenadas por `id`) y las columnas destino permitidas (`data-allowed`). Cada tarjeta incluye además un selector "Mover a…" que funciona sin JavaScript. Sin sprint activo, la página dice que no hay sprint activo.
*   **Gantt:** la vista calcula una estructura `{tasks: [{id, title, start, end, start_source, end_source, is_late, conflict, depends_on: [id]}], undated: [{id, title, reason}], milestones: [{id, name, date}]}` y la inserta en la página con `json_script`; `gantt.js` la lee y la pasa a `frappe-gantt`. `depends_on` solo incluye ids de tareas dibujadas. La lista `undated` (con su motivo) y los hitos se muestran también como HTML. Los hitos se dibujan como barras de un día con una clase propia; si la prueba de concepto de F4 no lo permite, solo se listan en HTML.
*   **Transiciones:** `POST …/columns/transitions/` reemplaza todo el conjunto con las casillas marcadas (pares `from_to`).
*   **Listas:** sin paginación en el MVP.

### Decisiones adicionales

Django 5.2 LTS con el ORM y las migraciones de Django; `django-environ` lee la configuración del entorno; `WhiteNoise` sirve los archivos estáticos desde el mismo proceso; `gunicorn` es el servidor de producción en Linux y `runserver` el de desarrollo. El controlador de MySQL es `mysqlclient` (con rueda binaria en Windows; en Linux necesita `libmysqlclient-dev` y `pkg-config`). Las vistas son funciones o clases síncronas. Cada caso de uso vive en `services.py` y se ejecuta en una transacción; la unicidad se valida antes en el formulario (422) y un `IntegrityError` por carrera se traduce a 409 en el servicio. Los servicios lanzan las excepciones de `core/exceptions.py` (`Conflict` para 409, `Unprocessable` para 422, `Forbidden` para 403 y `NotFound` para 404) y las vistas las convierten en respuestas. El sitio de administración de Django queda activo en `/admin/` solo para el operador (superusuario) y no forma parte del producto. Los textos de la interfaz están en español.

### Supuestos

*   Una organización por instalación; hasta 50 usuarios, 20 proyectos y 2.000 tareas por proyecto (suposición del autor, sin medición). A esa escala la página del Gantt se calcula en cada petición y no se pagina.
*   HTTPS en producción (`SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` activos cuando `DEBUG` es falso). Detrás de un proxy HTTPS hay que fijar también `SECURE_PROXY_SSL_HEADER` y `CSRF_TRUSTED_ORIGINS`; el despliegue detallado queda fuera de este plan. La zona horaria de la instalación se fija con `APP_TIMEZONE`.
*   Solo `create_column` escribe `position` y toma el bloqueo del proyecto; las columnas se ordenan por `(position, id)`. El recorrido de dependencias no tiene límite de profundidad.
*   Sin medición de disponibilidad ni latencia.

### Límites conocidos

*   Las tareas sin sprint no tienen tablero: solo se ven en el backlog.
*   No hay "desasignar": una tarea con sprint no puede pasar a otro sprint ni volver al backlog, salvo cuando el sprint se cierra. Un error de planning se corrige iniciando y cerrando el sprint.
*   Un sprint que se mueve no arrastra a las tareas con fechas propias.
*   La sesión dura 8 horas (`SESSION_COOKIE_AGE = 28800`) y el cierre de sesión la borra en el servidor. El operador (la persona que administra la instalación y tiene un superusuario de Django) puede cerrar sesiones ajenas borrándolas de la tabla de sesiones desde `/admin/`. El límite de intentos de login y la política de contraseñas quedan diferidos.
*   El registro es abierto: cualquiera con acceso a la URL puede crear una cuenta. Cualquier usuario con sesión puede crear proyectos; el creador queda como Product Owner.
*   El Gantt no reprograma ni propaga cambios: solo muestra y marca conflictos.
*   Dos peticiones concurrentes pueden crear dependencias que cierren un ciclo; dos `transfer_product_owner` simultáneos (o un cambio de rol y una transferencia) pueden dejar un proyecto con dos Product Owner o con ninguno; quitar a un miembro mientras se le asigna una tarea, y guardar transiciones con un formulario obsoleto, también pueden competir. Todos son poco probables a esta escala y no toman el bloqueo del proyecto.
*   Dos usuarios no ven los movimientos del otro hasta que recargan o actúan; un movimiento ya inválido se rechaza con 409 o 422 y el tablero se vuelve a dibujar.
*   El JavaScript propio (arrastrar tarjetas y dibujar el Gantt) no tiene pruebas automáticas; se verifica a mano en el recorrido E2E. Toda regla de negocio está en el servidor y sí se prueba.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Dos movimientos simultáneos superan el WIP | El tablero rompe su regla central | Bloqueo del proyecto en las cinco operaciones de la regla 10, relectura bajo el bloqueo, `READ COMMITTED`, índice `(sprint, column)` y prueba de concurrencia con transacciones reales (reglas 3 y 10) |
| Sesión robada o petición falsificada (CSRF) | Acceso con la cuenta de otro usuario | Cookie `HttpOnly` y `Secure`, token CSRF en todos los `POST`, sesión de 8 horas, cierre de sesión que borra la sesión en el servidor, contraseñas con argon2; límite de intentos de login diferido |
| Acceso a recursos de otro proyecto | Fuga de datos entre proyectos | Decorador que resuelve el proyecto de cada objeto y verifica el rol; 404 a no miembros; prueba entre proyectos |
| La página del Gantt se calcula en cada petición | Lentitud con proyectos grandes | Supuesto de 2.000 tareas por proyecto; `effective_dates` es una función pura; caché diferida |
| Dependencias concurrentes forman un ciclo | Grafo inválido | Límite conocido; baja probabilidad a esta escala |
| `frappe-gantt` no cubre lo que se necesita | Hay que reescribir el dibujo del Gantt | Prueba de concepto al empezar la fase 4; plan B: tabla con barras dibujadas por el servidor en HTML y CSS |
| El arrastre de tarjetas falla y no hay prueba automática | El tablero queda inutilizable en algún navegador | Selector "Mover a…" que funciona sin JavaScript y sí se prueba; recorrido E2E manual |

## Alternatives Considered

Cada rechazo es una decisión del autor.

### Alternativa A: "Área" como categoría de costo, equipo o épica

*   **Pros**: la categoría de costo es la más simple (no necesita vínculo con las tareas); el equipo y la épica permiten sumar trabajo por área.
*   **Cons**: la categoría de costo no se vincula con las tareas. El equipo obliga a asignar un equipo a cada tarea. La épica no permite presupuestar lo que no es una épica, y el presupuesto se mueve si cambian las épicas.
*   **Reason for Rejection**: Rejected by author: el área es un departamento de la empresa (contabilidad, operaciones, marketing), un concepto que ninguna de las tres formas representa.

### Alternativa B: Departamento compartido entre proyectos

*   **Pros**: un solo "Marketing" para toda la organización, con nombre único y presupuesto sumable entre proyectos, mediante un modelo de unión `ProjectBudget(project, department, monto, moneda)`.
*   **Cons**: hace falta el modelo de unión y una regla para borrar o renombrar un departamento con presupuestos asociados.
*   **Reason for Rejection**: Rejected by author: se eligió el departamento dentro de cada proyecto. Consecuencia aceptada: nombres duplicados entre proyectos y ninguna suma de presupuesto por departamento entre proyectos.

### Alternativa C: Un único presupuesto en el departamento global

*   **Pros**: una tabla menos y ninguna tabla de unión.
*   **Cons**: un departamento que participa en varios proyectos tiene un solo monto; no hay presupuesto por proyecto.
*   **Reason for Rejection**: Rejected by author: el requisito es un monto por departamento de cada proyecto.

### Alternativa D: Fechas guardadas solo en la tarea

*   **Pros**: el Gantt es una consulta directa.
*   **Cons**: al mover un sprint, las fechas de sus tareas no cambian y el Gantt contradice al sprint.
*   **Reason for Rejection**: Rejected by author: reproduce el desfase entre sprint y cronograma que el diseño busca evitar. Se eligió el híbrido, que mantiene el desfase solo para las tareas con fechas propias.

### Alternativa E: Fechas solo calculadas

*   **Pros**: mover un sprint mueve todas sus tareas.
*   **Cons**: las tareas sin sprint no tendrían fechas.
*   **Reason for Rejection**: Rejected by author: no cubre las tareas sin sprint ni las excepciones con fecha propia.

### Alternativa F: WIP sobre todo el proyecto

*   **Pros**: Kanban clásico, sin tareas fuera del tablero (con o sin filtro de vista).
*   **Cons**: el límite no refleja la capacidad del sprint. El tablero acumula tareas de varios sprints y el sprint planning y el WIP se pisan.
*   **Reason for Rejection**: Rejected by author: se eligió el WIP de 3 tareas en "En desarrollo" contado solo dentro del sprint activo. Consecuencia aceptada: las tareas sin sprint no tienen tablero.

### Alternativa G: JWT propio con una API separada del frontend

*   **Pros**: la API puede servir a una app móvil u otro cliente más adelante.
*   **Cons**: el token no se revoca antes de vencer y vive en JavaScript, donde un script inyectado lo puede leer. Exige un frontend aparte.
*   **Reason for Rejection**: Rejected by author: se pasó a una aplicación web hecha solo en Python. La sesión de Django se revoca en el servidor, usa cookie `HttpOnly` y trae protección CSRF. Consecuencia aceptada: no hay API para otros clientes.

### Alternativa H: Librerías de Gantt distintas de `frappe-gantt`

*   **Pros**: `dhtmlx-gantt` tiene más funciones; un SVG propio da control total.
*   **Cons**: la edición estándar de `dhtmlx-gantt` es GPLv2; el SVG propio exige escribir escala de tiempo, zoom y flechas.
*   **Reason for Rejection**: Rejected by author: se eligió `frappe-gantt` (MIT). Consecuencia aceptada: hay que guardar sus archivos en `static/vendor/`, escribir un `gantt.js` corto y hacer las marcas de retraso y conflicto con CSS.

### Alternativa I: Política de transición solo como texto

*   **Pros**: una tabla menos y ninguna regla de movimiento que probar.
*   **Cons**: el texto no se evalúa. Cualquiera puede mover una tarea a cualquier columna y la política queda sin efecto.
*   **Reason for Rejection**: Rejected by author: el README y el prompt piden una política de transición por columna (ver [plan-prompt.md](../plan-prompt.md)) y se decidió hacerla cumplir en el servidor. Consecuencia aceptada: hay que mantener una tabla de transiciones por proyecto.

### Alternativa J: FastAPI y React

*   **Pros**: API reutilizable, interfaz de página única más fluida y tipos compartidos desde OpenAPI.
*   **Cons**: dos lenguajes (Python y TypeScript), dos procesos de desarrollo, un proceso de compilación del frontend, y hay que escribir autenticación, migraciones y permisos que Django ya trae.
*   **Reason for Rejection**: Rejected by author: se quiere una aplicación web hecha solo en Python, en un monorepo.

### Alternativa K: Django con Django REST Framework y un frontend en JavaScript

*   **Pros**: conserva una interfaz de página única y una API para otros clientes.
*   **Cons**: reintroduce un frontend en JavaScript y duplica capas (serializadores, vistas de API y la aplicación cliente).
*   **Reason for Rejection**: Rejected by author: contradice "todo en Python".

### Alternativa L: Django con plantillas y sin JavaScript propio

*   **Pros**: cero JavaScript; el Gantt sería una tabla con barras dibujadas por el servidor y el tablero movería tarjetas con botones.
*   **Cons**: sin arrastrar y soltar y con un Gantt sin zoom ni interacción.
*   **Reason for Rejection**: Rejected by author: se eligió HTMX con JavaScript mínimo para conservar el arrastre y el Gantt interactivo. Este diseño reutiliza la idea como respaldo: el selector "Mover a…" y la tabla de Gantt del plan B.

### Alternativa M: Roles combinados por usuario

*   **Pros**: respeta la separación estricta de Product Owner y Scrum Master y permite que una persona tenga ambos roles.
*   **Cons**: cambia `ProjectMember` a un conjunto de roles, la matriz de permisos, las pruebas y la regla del Product Owner único.
*   **Reason for Rejection**: Rejected by author: se eligió que el Product Owner tenga los permisos del Scrum Master. Consecuencia aceptada: no hay separación estricta entre ambos roles.

### Alternativa N: Una sola app para `backlog`, `sprints` y `board`

*   **Pros**: no hay ciclo de imports posible entre ellas y se quitan archivos del plan.
*   **Cons**: la app queda grande y se pierde el límite entre módulos.
*   **Reason for Rejection**: Rejected by author: se eligió mantener apps separadas con un orden fijo de capas. Consecuencia aceptada: hay que respetar el orden y una prueba lo verifica.

### Alternativa O: Usar Jira o Linear

*   **Pros**: ya existen, se mantienen solos y traen integraciones, notificaciones y aplicaciones móviles.
*   **Cons**: el autor no comparó si cubren el presupuesto por departamento junto al tablero y el Gantt derivado del sprint, ni su costo por usuario.
*   **Reason for Rejection**: Rejected by author: se quiere una sola fuente de verdad que incluya el presupuesto por departamento, desplegada por la propia organización (ver el diferencial en The Problem). Consecuencia aceptada: hay que construir y mantener la herramienta.

### Alternativa P: Sin historial de sprints

*   **Pros**: ningún modelo nuevo ni escritura extra al cerrar un sprint.
*   **Cons**: las tareas sin terminar pierden su vínculo con el sprint y no se puede calcular la velocidad después.
*   **Reason for Rejection**: Rejected by author: se eligió guardar `SprintTask` al cerrar cada sprint. Consecuencia aceptada: un modelo más y una segunda fuente de pertenencia que `close_sprint` escribe una sola vez y nunca modifica.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

El proyecto no tiene código. Todos los archivos son nuevos, salvo `README.md` (ya apunta a este plan y cita el stack Django; en F5 solo se le añaden las instrucciones de instalación y arranque) y `docs/plan-prompt.md` (ya actualizado con el stack Django). Las rutas son relativas a la raíz del repositorio (monorepo: aplicación, documentación y configuración de desarrollo viven juntas). El plan incluye las firmas de los servicios principales, reglas y el mínimo de configuración literal necesario; no incluye código de implementación. Cada archivo lleva su fase (F1 a F5) y cada fase deja el sistema ejecutable y probable.

Cada fase que añade una app modifica además, sin repetirlo en cada ítem: `config/settings.py` (`INSTALLED_APPS`), `config/urls.py`, `templates/base.html` (enlace de navegación), `static/css/styles.css` y `apps/core/permissions.py` (el resolvedor de sus modelos).

Versiones: Python 3.12, Django 5.2 LTS, MySQL 8.4 LTS (imagen `mysql:8.4`; se fija 8.4 porque 8.0 ya terminó su soporte; los `CHECK` exigen ≥ 8.0.16), `mysqlclient`, `argon2-cffi`, `django-environ`, `whitenoise` y `gunicorn`; en desarrollo `pytest`, `pytest-django`, `pytest-cov`, `pytest-env` y `ruff`. Quien implementa fija las versiones exactas con `==` en `requirements*.txt` al instalar por primera vez. Librerías de JavaScript guardadas en el repositorio: HTMX 2.x, SortableJS 1.15.x y `frappe-gantt`. La versión de `frappe-gantt` se fija antes de cerrar la lista de archivos de F4, porque los nombres de archivo y las opciones cambian entre las series 0.6.x y 1.x. Las versiones se registran en `static/vendor/VERSIONS.md`.

### Orden de implementación y criterios de aceptación

| Fase | Contenido |
| --- | --- |
| F1. Base | Repositorio (`git init`), MySQL local, proyecto Django, `core`, `accounts`, `projects`, modelos de `board` y `create_default_board`, páginas de registro, login, proyectos y miembros |
| F2. Backlog y sprints | `sprints` y `backlog`: modelos, formularios, dependencias, hitos, `apply_placement` (con WIP y bloqueo del proyecto), `assign_sprint` y `close_sprint`; páginas de backlog y de sprints |
| F3. Tablero | `move_task`, `get_board`, vistas del tablero, `board.js`, editor de columnas y transiciones |
| F4. Gantt | Vista `gantt`, `gantt.js` con `frappe-gantt` (empieza con una prueba de concepto) |
| F5. Presupuesto y cierre | `budget`, instrucciones en el README y cobertura mínima |

Criterios de aceptación (cada fase cumple los suyos y los de las anteriores; `pytest` pasa en todas):

*   **F1**
    *   `python manage.py migrate` corre sin errores sobre una base vacía.
    *   Un usuario se registra, inicia y cierra sesión; al cerrar sesión se borra su fila de `django_session`.
    *   Crear un proyecto produce 4 columnas, WIP 3 en "En desarrollo" y transiciones contiguas.
    *   Un `POST` sin token CSRF devuelve 403.
    *   `/projects/<id>/` redirige a la lista de proyectos.
*   **F2**
    *   Una dependencia que cierra un ciclo, o que involucra una historia, devuelve 422.
    *   Abrir un segundo sprint activo devuelve 409.
    *   Asignar una tarea a un sprint le da la primera columna; asignarla a un sprint activo cuya primera columna tiene `wip_limit` 0 devuelve 409.
    *   Al cerrar un sprint, las tareas sin terminar quedan sin sprint y sin columna y las terminadas conservan ambos.
    *   Un usuario del proyecto B recibe 404 sobre una tarea o un sprint del proyecto A.
    *   Las migraciones de `sprints` y `backlog` bajan a cero y suben otra vez.
    *   Las pruebas de cierre preparan las tareas terminadas asignando directamente una columna `is_done` (el movimiento por el tablero llega en F3).
*   **F3**
    *   Con 3 tareas del sprint activo en "En desarrollo", mover una cuarta devuelve 409.
    *   Con dos movimientos simultáneos a la última plaza libre, uno recibe 200 y el otro 409.
    *   Mover de "Por hacer" a "Hecho" devuelve 422.
    *   Mover con el selector "Mover a…" funciona sin JavaScript.
*   **F4**
    *   Una tarea sin fechas propias se dibuja con las del sprint; una con fechas propias, con las suyas.
    *   Una tarea retrasada tiene `is_late: true` en los datos que la página inserta con `json_script` (lo verifica pytest); la clase CSS que `gantt.js` aplica con `custom_class` se verifica a mano en el recorrido E2E.
    *   Una dependencia cuyo sucesor empieza el día en que termina el predecesor, o antes, lleva `conflict`.
*   **F5**
    *   Crear un departamento con monto 1500 y moneda "USD" lo guarda; un monto negativo o la moneda "usd" devuelve 422.
    *   `pytest --cov=apps --cov-fail-under=80` pasa.
    *   El README documenta la instalación y el arranque.

### Target Files to Create/Modify

#### Raíz del monorepo

1.  `README.md` (**Modify**, F5). Añadir la instalación (`python -m venv`, `pip install -r requirements-dev.txt`), la configuración de `.env`, cómo levantar MySQL (`docker compose up -d`; sin Docker se instala MySQL a mano), `python manage.py migrate`, `python manage.py createsuperuser` (para `/admin/`), `python manage.py runserver` y `pytest`. Cambiar "Estado" a "MVP implementado".
2.  `.gitignore` y `.gitattributes` (**Create**, F1). Excluir `.env`, `__pycache__/`, `.venv/`, `staticfiles/`, `.coverage`, `htmlcov/`, `.pytest_cache/`, `.ruff_cache/` y datos locales de MySQL. Se crea también `.gitattributes` con `*.sh text eol=lf`, para que el script de Docker no se rompa con los finales de línea de Windows.
3.  `.env.example` (**Create**, F1). Variables sin valores reales: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `APP_TIMEZONE`, `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_HOST` (por defecto `127.0.0.1`) y `MYSQL_PORT` (por defecto `3306`). No hay `DATABASE_URL`: `settings.py` construye la conexión con las mismas variables `MYSQL_*` que usa Docker, así que las credenciales viven en un solo lugar. `APP_TIMEZONE` vale `UTC` si falta. La base de pruebas la crea Django con el nombre `test_<base>`.
4.  `docker-compose.yml` (**Create**, F1). Un servicio MySQL `8.4` con volumen, variables `MYSQL_*` y el directorio `docker/initdb/` montado en `/docker-entrypoint-initdb.d`.
5.  `docker/initdb/01-grants.sh` (**Create**, F1). Script de shell que lee `$MYSQL_USER` y `$MYSQL_ROOT_PASSWORD` y concede `ALL` sobre `` `test\_%`.* `` a `'$MYSQL_USER'@'%'`, para que Django pueda crear la base de pruebas. Corre solo con el volumen vacío: si ya existe, hay que recrearlo (`docker compose down -v`).
6.  `requirements.txt` (**Create**, F1). Django, mysqlclient, argon2-cffi, django-environ, whitenoise, gunicorn.
7.  `requirements-dev.txt` (**Create**, F1). Incluye `requirements.txt` más pytest, pytest-django, pytest-cov, pytest-env y ruff.
8.  `pyproject.toml` (**Create**, F1). Solo configuración de herramientas. Pytest: `DJANGO_SETTINGS_MODULE = "config.settings"`, `testpaths = ["tests"]` y `env = ["SECRET_KEY=test-only-key", "DEBUG=true"]` (sin umbral de cobertura en `addopts`). Ruff: reglas y exclusión de `migrations/`.
9.  `manage.py` (**Create**, F1). Punto de entrada estándar de Django.

#### Proyecto Django (`config/`)

10. `config/__init__.py` (**Create**, F1). Marca el paquete.
11. `config/settings.py` (**Create**, F1). Carga `.env` con `Env.read_env` si existe; falla al arrancar si falta `SECRET_KEY`. `INSTALLED_APPS` con las apps de `apps/`; `AUTH_USER_MODEL = "accounts.User"`; `PASSWORD_HASHERS` con argon2 primero; `DATABASES["default"]` con motor `django.db.backends.mysql`, `NAME`, `USER`, `PASSWORD`, `HOST` y `PORT` tomados de `MYSQL_*`, y `OPTIONS = {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'", "isolation_level": "read committed"}`; `DEFAULT_AUTO_FIELD = BigAutoField`; `USE_TZ = True`, `TIME_ZONE = APP_TIMEZONE`, `LANGUAGE_CODE = "es"`; `SESSION_COOKIE_AGE = 28800`; cookies `Secure` cuando `DEBUG` es falso; `LOGIN_URL = "/accounts/login/"` y `LOGIN_REDIRECT_URL = "/"`; `WhiteNoise` en el middleware, `STATIC_ROOT = staticfiles/` y `STATICFILES_DIRS = [static/]`; plantillas en `templates/` con el procesador de mensajes.
12. `config/urls.py` (**Create**, F1). Incluye las `urls.py` de cada app (cada ruta con `name`) y `/admin/`.
13. `config/wsgi.py` (**Create**, F1). Entrada WSGI para `gunicorn config.wsgi`.

#### Apps (`apps/`)

Orden de capas (regla de Componentes): `core`, `accounts`, `board`, `projects`, `sprints`, `backlog`, y encima `gantt` y `budget`. Cada app con modelos es un paquete con `__init__.py`, `models.py`, `services.py`, `forms.py`, `views.py`, `urls.py` y `migrations/`. Todas las migraciones las genera `makemigrations` y se revisan. Sus dependencias son: `projects.0001` depende de `accounts.0001`; `board.0001` y `sprints.0001` de `projects.0001`; `backlog.0001` de `projects.0001`, `board.0001` y `sprints.0001`; `budget.0001` de `projects.0001`.

14. `apps/__init__.py` (**Create**, F1). Marca el paquete.
15. `apps/core/` (**Create**, F1: `__init__.py`, `permissions.py`, `exceptions.py`, `middleware.py`, `locks.py`, `htmx.py`; no tiene modelos ni `services.py`). `permissions.py`: decorador `project_role_required(roles, resolver)` y resolvedores `from_project_id`, `from_task_id`, `from_sprint_id`, `from_column_id` y `from_department_id` que cargan el objeto con `apps.get_model` y deducen su proyecto (404 si el usuario no es miembro, 403 si no tiene el rol); además `can_edit_task` y `can_move_task` (regla 7). En F1 solo existe el resolvedor de proyecto; cada fase añade los suyos. `exceptions.py`: `Conflict` (409), `Unprocessable` (422), `Forbidden` (403) y `NotFound` (404). `middleware.py`: `ServiceExceptionMiddleware`, cuyo `process_exception` convierte esas excepciones en respuestas (una página de error con `templates/error.html`, o un mensaje de Django y una redirección a la página de origen; nunca el fragmento del tablero, que construye la vista `move`); se registra en `MIDDLEWARE`. `htmx.py`: `is_htmx(request)`, la respuesta `401` con `HX-Redirect` para peticiones HTMX sin sesión y una función que decide entre devolver el fragmento o redirigir.
16. `apps/accounts/` (**Create**, F1). `User` con `UserManager` (`create_user`, `create_superuser`; correo en minúsculas), `admin.py` que registra `User` y `Session` de solo lectura (para que el operador pueda ver y borrar sesiones desde `/admin/`), formularios de registro y login (un correo repetido es un error del formulario con estado 422), vistas de registro, login y logout (`POST`), `urls.py` y plantillas.
17. `apps/projects/` (**Create**, F1). `Project` y `ProjectMember`. `create_project` (el creador queda como Product Owner y se llama a `board.services.create_default_board`), listar los proyectos del usuario (en F3 `views.py` cambia la redirección de `/projects/<id>/` al tablero), añadir miembros por correo (el usuario debe estar registrado), cambiar el rol, quitar un miembro (409 si es Product Owner o tiene tareas asignadas sin terminar; la comprobación de tareas usa `apps.get_model("backlog", "Task")` y se omite mientras `backlog` no esté instalada, es decir, en F1) y `transfer_product_owner` (regla 7).
18. `apps/board/` (**Create**, F1 para los modelos y `create_default_board`; F3 para las vistas). Modelos `BoardColumn` y `ColumnTransition`. `services.py`: `create_default_board(project)`, `create_column(project, name, wip_limit, policy_text)` (se inserta justo antes de la columna `is_done`, que pasa a la posición siguiente; siembra transiciones en ambos sentidos con la columna anterior y con la `is_done`; no borra las transiciones existentes, así que la anterior sigue pudiendo pasar a la `is_done` hasta que el Scrum Master la quite; toma el bloqueo del proyecto con `lock_project`), `update_column` (solo nombre, WIP y texto de política; `is_done` no se edita; sin borrado; hay una sola columna `is_done` y es la última) y `set_transitions` (valida que ambas columnas sean del proyecto). La "primera columna" es la de menor `position`; las columnas se ordenan por `(position, id)`. Las vistas del tablero y del editor de columnas llaman a `backlog.services`.
19. `apps/sprints/` (**Create**, F2). Modelo `Sprint` con `CheckConstraint(condition=…)` de fechas, el campo generado `active_project_id` y su `UniqueConstraint` (ver el modelo de datos). `makemigrations` genera la migración (columna virtual con índice único) y quien implementa la revisa a mano al generarla. `services.py`: `create_sprint`, `update_sprint` y `start_sprint` (estado `planned` y las dos fechas; toma el bloqueo con `lock_project`; traduce el `IntegrityError` del índice único a `Conflict`). El cierre vive en `backlog.services.close_sprint`; la vista de cierre de `sprints` lo llama.
20. `apps/backlog/` (**Create**, F2 y F3). Modelos `Task`, `Comment`, `TaskDependency`, `Milestone` y `SprintTask` con las invariantes del modelo de datos (`CheckConstraint` y validaciones del servicio). Índices `Task(sprint, column)`, `Task(project, sprint, column)` y `Task(assignee)`. `services.py` (F2): CRUD de tareas e hitos (los hitos solo se crean y se listan), `add_dependency` y `remove_dependency` (422 por autodependencia, duplicado, proyectos distintos, historia o ciclo; el recorrido del grafo es iterativo), `apply_placement` (con el límite WIP y el bloqueo de la regla 10), `assign_sprint` y `close_sprint` (con `review_notes` y `retro_notes`; escribe `SprintTask` y aplica la regla 10). `services.py` (F3): `move_task` (regla 3) y `get_board(project)`. Formularios de tarea: `title`, `kind`, `parent`, `description`, `estimate_points`, `assignee`, `start_date` y `due_date`; no incluyen `column` ni `sprint`.
21. `apps/gantt/` (**Create**, F4: `__init__.py`, `services.py`, `views.py`, `urls.py`). `effective_dates(task, sprint)` es una función pura que devuelve inicio, fin y sus fuentes, o el motivo por el que la tarea va a `undated`. `build_gantt(project, today)` arma la estructura del contrato (con `is_late` y `conflict`). Solo se leen tareas; nunca se escribe.
22. `apps/budget/` (**Create**, F5). Modelo `Department`; el servicio valida monto ≥ 0 y moneda de tres letras mayúsculas y registra `updated_by` y `updated_at`; vistas de listar, crear, editar y borrar.

#### Plantillas y archivos estáticos

23. `templates/base.html` y `templates/error.html` (**Create**, F1). Diseño común, barra de navegación del proyecto, bloque de mensajes, `{% block content %}` y `{% block scripts %}` (cada página carga los suyos), y `hx-headers` con el token CSRF en `<body>`. `error.html` muestra el estado y el mensaje de un error.
24. `templates/accounts/login.html` y `register.html` (**Create**, F1).
25. `templates/projects/list.html`, `new.html` y `members.html` (**Create**, F1). Lista, creación, miembros, cambio de rol y transferencia del Product Owner.
26. `templates/backlog/backlog.html` y `task_form.html` (**Create**, F2). Backlog con historias, tareas, dependencias e hitos; formulario compartido de tarea.
27. `templates/sprints/sprints.html` (**Create**, F2). Crear sprints, asignar tareas, iniciar y cerrar con las notas de review y retro; lista de las tareas de cada sprint con su columna.
28. `templates/board/board.html`, `_board.html`, `_card.html` y `columns.html` (**Create**, F3). `_board.html` es el fragmento que devuelve `move`. Cada columna muestra "conteo / límite" y lleva `data-column-id`; el tablero lleva el `id` `board` y `data-move-url`; cada tarjeta lleva el selector "Mover a…". `columns.html` edita columnas, WIP, texto de política y transiciones (Product Owner y Scrum Master).
29. `templates/gantt/gantt.html` (**Create**, F4). Contenedor del Gantt, `json_script` con los datos y las listas `undated` e hitos.
30. `templates/budget/budget.html` (**Create**, F5). Tabla de departamentos; edición solo para Product Owner y Scrum Master.
31. `static/css/styles.css` (**Create**, F1). Estilos; en F3 las columnas y tarjetas, en F4 las marcas de retraso y conflicto.
32. `static/js/board.js` (**Create**, F3). Una función idempotente `initBoard()` que crea SortableJS en cada columna del contenedor `#board`; se ejecuta en `htmx:load`, porque HTMX reemplaza el tablero y destruye las instancias anteriores. Al soltar una tarjeta llama a `htmx.ajax("POST", url, {target: "#board", swap: "outerHTML", values: {column_id}})`. El manejador `htmx:beforeSwap` acepta los estados 409 y 422 para reemplazar el tablero; ante cualquier otra respuesta distinta de 200, 409 o 422 (403, 404, 5xx o error de red) recarga el tablero. Las columnas permitidas (`data-allowed`) se resaltan al empezar el arrastre.
33. `static/js/gantt.js` (**Create**, F4). Lee los datos de `json_script`, crea `frappe-gantt` en modo solo lectura y pasa el retraso y el conflicto como clases de cada tarea (`custom_class`; la prueba de concepto decide cómo combinar ambas). Pasa a la librería solo las tareas con fechas. La fase empieza con esa prueba de concepto: confirmar que se puede desactivar la edición, pasar clases por tarea, dibujar dependencias y vaciar el contenedor al recargar. Si no, el plan B es una tabla con barras dibujadas por el servidor en HTML y CSS, con los mismos datos (el servidor calcula el desplazamiento y el ancho de cada barra en días desde la fecha mínima).
34. `static/vendor/htmx/`, `static/vendor/sortable/` y `static/vendor/frappe-gantt/` (**Create**, F1 para HTMX, F3 para SortableJS, F4 para `frappe-gantt`) y `static/vendor/VERSIONS.md`. Copias descargadas de los paquetes oficiales; los nombres de archivo dependen de la versión descargada y se registran en `VERSIONS.md` junto con la licencia de cada una (HTMX 2 es 0BSD y `frappe-gantt` es MIT).

#### Pruebas (`tests/`)

Las pruebas usan la base MySQL de pruebas que crea Django (`test_<base>`), no SQLite, porque el bloqueo de filas y la columna generada no se comportan igual. Las que necesitan transacciones reales usan `@pytest.mark.django_db(transaction=True)`.

35. `tests/__init__.py` (**Create**, F1). Marca el paquete.
36. `tests/conftest.py` (**Create**, F1). Fixtures: usuarios con cada rol, un proyecto de ejemplo con su tablero por defecto, y clientes de Django autenticados creados con `Client(enforce_csrf_checks=True)` (de lo contrario Django no comprueba CSRF en pruebas).
37. `tests/test_imports.py` (**Create**, F1). Lee con `ast` los `import` de cada `apps/*/services.py` y falla si importa una app de una capa superior según el orden de capas; además importa cada módulo `services` en un intérprete nuevo (`subprocess` con `django.setup()`) y falla ante un `ImportError`.
38. `tests/test_accounts.py` (**Create**, F1). Registro, correo repetido (422), login incorrecto, cierre de sesión (borra la sesión de la base), `POST` sin CSRF (403), redirección a login sin sesión, `401` con `HX-Redirect` en una petición HTMX sin sesión.
39. `tests/test_projects.py` (**Create**, F1; se amplía en F2). Valores por defecto al crear un proyecto (4 columnas, WIP 3, transiciones contiguas), Product Owner único, `transfer_product_owner` (atómico y con el rol del saliente), quitar al Product Owner (409) y, desde F2, quitar a un miembro con tareas asignadas sin terminar (409; una terminada no lo impide).
40. `tests/test_migrations.py` (**Create**, F2). Con `transaction=True`: `migrate sprints zero` (que desaplica también `backlog`) y `migrate` otra vez, de modo que la base quede migrada; `makemigrations --check --dry-run` no encuentra cambios; el índice único de sprint activo rechaza un segundo sprint con `status = 'active'` en el mismo proyecto (se prueba con un `update` directo por el ORM, sin pasar por `start_sprint`).
41. `tests/test_roles.py` (**Create**, F2; se amplía en F3 y F5). Matriz de la regla 7 con 403 o 404 según corresponda, por fase: F2 cubre proyectos, tareas y sprints; F3, columnas y movimientos; F5, departamentos.
42. `tests/test_isolation.py` (**Create**, F2; se amplía en F5). Un usuario del proyecto B recibe 404 sobre tareas y sprints del proyecto A; en F5, también sobre departamentos.
43. `tests/test_backlog.py` (**Create**, F2). Ciclo (422), autodependencia (422), duplicado (422), dependencia entre proyectos (422), dependencia con una historia (422), mismo proyecto en las referencias de una tarea, jerarquía historia y tarea, `sprint` y `column` juntos, borrar una tarea con hijas, con dependencias o con sprint (409), `assign_sprint` (primera columna; sprint cerrado rechazado; historia rechazada; tarea que ya tiene sprint rechazada con 422; sprint activo con WIP), y una edición con datos obsoletos no pisa `column`, `sprint` ni `status`.
44. `tests/test_sprints.py` (**Create**, F2). Segundo sprint activo (409, incluido el caso que lo rechaza el índice único de la base), `start` desde un estado no válido, cierre con tareas sin terminar (quedan sin sprint y sin columna) y terminadas (conservan ambos), y filas de `SprintTask` creadas para ambos tipos con el nombre de columna, `is_done` y puntos correctos; un segundo cierre del mismo sprint es rechazado y no duplica filas.
45. `tests/test_board_wip.py` (**Create**, F3). Cuarta tarea a "En desarrollo" (409 con límite y conteo); tarea sin sprint, de una historia o de un sprint no activo (422); mover a la misma columna (200, sin cambios); `wip_limit` nulo y `0`; bajar el límite no expulsa tareas; orden de validaciones (permiso, 422, no-op, transición, WIP); una prueba pasa al servicio una instancia de tarea cargada antes y ya obsoleta, y comprueba que la relee bajo el bloqueo; concurrencia: dos hilos, cada uno con su propia conexión (que cierran con `connection.close()`), sincronizados con `threading.Barrier`, mueven dos tareas distintas a la última plaza libre y uno recibe 200 y el otro 409; otra prueba hace lo mismo con `move_task` y `close_sprint`, y con `assign_sprint` y `move_task`, y el invariante de sprint y columna se mantiene.
46. `tests/test_board_transitions.py` (**Create**, F3). Movimiento a columna contigua (permitido), "Por hacer" a "Hecho" (422 con destinos permitidos), transiciones editadas por el Scrum Master y por el Product Owner (permitido) y por un developer (403), columna de otro proyecto en la tabla (422), crear una columna la inserta antes de la columna `is_done`, desplaza su posición y siembra sus transiciones.
47. `tests/test_board_views.py` (**Create**, F3). Con la cabecera `HX-Request`, `move` devuelve el fragmento con 200, 409 o 422 y el mensaje correcto; sin ella, redirige; el selector "Mover a…" envía el mismo `POST`.
48. `tests/test_gantt_dates.py` (**Create**, F4). Hereda fechas del sprint; fechas propias mandan; una sola fecha y sin sprint va a `undated`; fin anterior al inicio va a `undated` con su motivo; retraso con `today` inyectado; conflicto de dependencia (incluido el mismo día); `depends_on` omite tareas sin fechas; estructura de datos de la página.
49. `tests/test_budget.py` (**Create**, F5). Monto negativo (422), moneda inválida (422), nombre duplicado en el proyecto (422), el mismo nombre en otro proyecto (permitido), `updated_by`.

### Verification Plan

*   **Compilation/Build**: `python manage.py check`; `python manage.py makemigrations --check --dry-run` (no debe haber migraciones pendientes); `python manage.py migrate` sobre una base vacía; `python manage.py collectstatic --noinput`.
*   **Unit Tests**: `pytest` desde la raíz.
*   **Static Analysis & Linting**: `ruff check`.
*   **Test Coverage Requirement**: al cerrar F5, `pytest --cov=apps --cov-fail-under=80` (80 % de líneas en `apps/`, un umbral de partida del autor). Antes de F5 no hay umbral.
*   **E2E/Integration**: recorrido manual con la aplicación corriendo (`python manage.py runserver`) y un solo usuario, que es Product Owner y por eso puede hacer todos los pasos. Lo hace quien implementa; cada fase se da por buena si pasan los pasos que le corresponden, y el recorrido completo se repite al cerrar F5.

    | Paso | Fase | Resultado esperado |
    | --- | --- | --- |
    | 1. Registrarse e iniciar sesión | F1 | Se llega a la lista de proyectos |
    | 2. Crear un proyecto | F1 | Aparece en la lista; sus 4 columnas, el WIP 3 de "En desarrollo" y las transiciones contiguas los comprueba `test_projects` (desde F3 también se ven en la página de columnas) |
    | 3. Crear 5 tareas, crear un sprint que empiece hace una semana y termine ayer, asignarle las tareas e iniciarlo | F2 | La página de sprints lista las 5 tareas en "Por hacer" |
    | 4. Abrir el tablero | F3 | Muestra las 5 en "Por hacer" y "En desarrollo" muestra "0 / 3" |
    | 5. Arrastrar 3 tareas a "En desarrollo" | F3 | Las 3 pasan y la columna muestra "3 / 3" |
    | 6. Arrastrar una cuarta tarea | F3 | La tarjeta vuelve a su columna y aparece el mensaje del límite |
    | 7. Mover una tarea de "Por hacer" a "Hecho" | F3 | Se rechaza y se muestran los destinos permitidos |
    | 8. Llevar una tarea de "En desarrollo" a "En revisión" y a "Hecho" | F3 | Cada movimiento a una columna contigua se acepta y "En desarrollo" vuelve a mostrar "2 / 3" |
    | 9. Con JavaScript desactivado, mover con "Mover a…" una tarea de "Por hacer" a "En desarrollo" y luego otra | F3 | La primera pasa ("3 / 3") y la segunda se rechaza con el mensaje del límite |
    | 10. Abrir el Gantt | F4 | Las tareas aparecen con las fechas del sprint y las que no están en "Hecho" con la marca de retraso, porque el sprint ya terminó |
    | 11. Fijar fechas propias en una tarea | F4 | El Gantt usa esas fechas |
    | 12. Crear un departamento con monto 1500 y moneda "USD", y probar con un monto negativo | F5 | El primero aparece en la tabla de presupuesto y el segundo se rechaza |
    | 13. Cerrar el sprint (se ejecuta al final del recorrido) | F3 | La tarea en "Hecho" conserva el sprint; las demás quedan sin sprint en el backlog (la lógica de cierre se construye en F2 y la prueban sus tests) |

--------------------------------------------------------------------------------

### Future Improvements

*   **Ruta crítica y línea base** sobre el grafo de dependencias (versión posterior).
*   **Edición del Gantt** arrastrando barras, con reglas de propagación (versión posterior).
*   **Velocidad por sprint** a partir de `SprintTask` (versión posterior). Burndown y métricas de flujo requieren guardar además cada cambio de columna.
*   **Seguimiento del gasto real** contra el presupuesto de cada departamento (versión posterior).
*   **Límite de intentos de login y política de contraseñas** (versión posterior).
*   **Actualización en vivo del tablero** con Server-Sent Events o WebSockets (versión posterior).
*   **Políticas de transición por rol**, por ejemplo que solo el Product Owner mueva a "Hecho" (versión posterior).
*   **Orden manual de las tarjetas** dentro de una columna (versión posterior).

--------------------------------------------------------------------------------

*Drafted with EGM*
