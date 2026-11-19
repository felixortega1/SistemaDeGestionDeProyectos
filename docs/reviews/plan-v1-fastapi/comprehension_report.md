# Comprehension Report — plan-implementacion.md (Stage 6)

Revisor: egm-comprehension (lector sin contexto). Solo leyó el documento.

## What this proposes
A web system for Scrum project tracking. Each task is stored once, and two views are computed from it: a Kanban board with a work-in-progress (WIP) limit enforced by the server, and a read-only Gantt chart. Each project also stores a hand-entered budget amount and currency per department. The stack is FastAPI, React and MySQL, built as a modular monolith in five phases (base, backlog/sprints, board, Gantt, budget/close). The Detailed Plan lists about 60 files to create, plus tests and a verification plan. Whether to build this instead of using Jira or Linear is left open.

## How the existing system works, per this document
Nothing exists yet. There is no code, and the only existing file is README.md. The document describes a target design, not a current system. Tasks carry their column, sprint and dependencies. The board shows only tasks in the active sprint. Gantt dates come from the task's own dates if it has any, otherwise from its sprint. Moves between columns are checked against an allowed-transitions table, then against the WIP count under a row lock. Roles (Product Owner, Scrum Master, developer) are checked on every endpoint.

## Findings

No sección imposible de parafrasear: no hay Blockers.

### 🟡 Major
1. **Dependencia de archivos externos (Overview, línea 13; Alternativa I, línea 190).** El documento remite a `README.md` y `docs/plan-prompt.md` como fuente de requisitos ("el README y el prompt piden…"). Quien no los tenga no puede verificar los requisitos. Resumirlos en el texto o rotularlos como entradas externas.
2. **"Área" y referencias colgantes (Overview, Goals; Alternativas A y B).** "Área" se usa en G4 y el Overview sin glosa; solo se define como "departamento" en "Decisiones de diseño", después de los Goals. La alternativa A habla de "tres opciones" y la B de "opción 1 con tabla de unión `project_budgets`", pero ni las opciones ni la tabla se describen en ningún lugar.
3. **Conteo del WIP y bloqueo (regla 3, ítem 26; línea 103).** No se dice qué pasa al mover una tarea a su misma columna ni si una tarea ya contada se vuelve a contar. Con cero tareas en la columna, `SELECT … FOR UPDATE` no bloquea nada, así que la afirmación "dos movimientos simultáneos no superan el límite" no es evidente. `start` de sprint bloquea la fila del proyecto; el movimiento de tablero no dice que haga lo mismo.
4. **Transición "Por hacer → Hecho": abierta y decidida a la vez (línea 46; fase 3, línea 204; prueba 36b).** Open Questions pregunta si debe permitirse, pero la fase 3 y la prueba 36b exigen rechazarla con 422. Si el Scrum Master edita las transiciones, cambia el criterio de aceptación.
5. **Permisos por rol (regla 7).** Los developers "mueven y editan sus tareas", pero "sus tareas" no se define (¿responsable?, ¿creador?). No se dice si el Product Owner o el Scrum Master pueden mover tareas ajenas.
6. **Jerarquía de `tasks` (línea 95; ítems 24 y 49).** No se dice si una historia es elemento del tablero o del Gantt, si tiene columna y sprint, ni si cuenta para el WIP. Las épicas solo se enlazan por `epic_id` en la tarea. `estimate_points` no tiene significado ni uso declarado.
7. **Columnas por proyecto sin ciclo de vida (ítem 23; `PATCH …/columns`).** Se siembran al crear el proyecto, pero no se dice qué pasa con las tareas si se borra o renombra una columna, ni existe comportamiento de crear o borrar columnas. (El conteo "once tablas" es correcto.)
8. **Reglas del Gantt (regla 4, G3).** Una tarea con solo `start_date` y un sprint toma `end` del sprint; si queda antes de `start`, no se dice qué ocurre. Los hitos se dibujan pero no se relacionan con tareas ni dependencias.
9. **Sección de alternativas (líneas 134-193).** Dice que los motivos son "los límites técnicos que se presentaron al elegir", pero esos límites no están en el documento. `frappe-gantt` aparece por primera vez en la fase 4 y en la alternativa H, sin definición en el Technical Plan. "Decisiones sin alternativas defendibles" no justifica qué hace indefendible una alternativa.
10. **Autenticación (línea 115; ítem 46).** `refresh` acepta un token válido y devuelve otro: un token robado se renueva sin fin y debilita la vida de 30 minutos, algo que el documento no discute. `sessionStorage` queda expuesto a XSS, mientras la sección de alternativas justifica JWT en parte por evitar cookies expuestas a JavaScript. El registro es abierto y no se dice quién puede crear cuentas ni qué entrada recibe `POST /members`.

### 🟢 Nit
11. **Criterios de aceptación (fases 1 y 2).** "La migración se aplica y se revierte" es débil porque `downgrade` borra todo. En la fase 2 no se indica qué capa rechaza el segundo sprint activo (servicio o índice).
12. **Referencias y numeración.** "Punto 7 del Technical Plan" (ítems 14 y 31) es la regla 7 de "Reglas del sistema". El ítem "36b" rompe la numeración.
13. **Columna al volver al backlog (cierre de sprint).** No se dice qué `column_id` conserva una tarea devuelta, ni en qué columna empieza al entrar a un sprint nuevo.
14. **Idioma.** Los identificadores van en inglés y la documentación en español, pero los textos de la interfaz ("Límite WIP alcanzado (3)") van en español. Está reconocido como pregunta abierta.
15. **"Sin servicios adicionales" (G6) frente a Docker y segunda base de pruebas (ítem 4).** Reconciliable, pero no se dice.
