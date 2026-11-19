# Informe de comprensión (Etapa 6) — plan-implementacion.md (versión Django)

Revisor: egm-comprehension. Leyó solo el documento (líneas 1-266 diseño, 267-384 plan detallado). Los números de línea son los del revisor.

## Qué propone
Una aplicación web Django (plantillas, HTMX, MySQL) para gestionar proyectos con Scrum. Cada tarea se guarda una vez; de ella salen un tablero Kanban (transiciones y WIP en el servidor) y un Gantt de solo lectura. Cada proyecto tiene departamentos con monto y moneda. Cinco fases F1-F5, archivos, pruebas y un recorrido E2E manual.

## Blockers
1. **Regla 8 vs. Límites conocidos (L129, L168).** Al cerrar un sprint, las tareas no terminadas vuelven al backlog. Las terminadas conservan `sprint`, pero el tablero solo muestra el sprint activo: no queda claro dónde se ven.
2. **Sprint `planned` y tareas asignadas.** La regla 3b aplica el WIP solo si el sprint está activo; la regla 3 devuelve 422 al mover tareas de un sprint no activo. No se dice si el tablero muestra tareas de un sprint `planned`. El paso 3 del E2E lo da por hecho.
3. **Columna de una tarea sin sprint.** La tabla dice `column` nula solo para historias; la regla 3b y la 8 dan a las tareas sin sprint la primera columna. El modelo nunca lo dice.

## Major
4. `apply_placement` es el "único escritor", pero `move_task` y el cierre de sprint también modifican `column`/`sprint`. No se dice si pasan por `apply_placement` ni qué pasa si reiniciar a la primera columna supera su WIP.
5. Orden de comprobaciones en la regla 3: ¿el no-op por misma columna va antes o después de la comprobación de sprint activo (422)?
6. Qué ocurre si se baja `wip_limit` por debajo del conteo actual.
7. La transición por defecto (solo contiguas, "Por hacer → Hecho" rechazada) y el criterio F3 no aclaran que dependen de la configuración por defecto.
8. Transferencia del Product Owner: no se dice qué rol queda el saliente ni cómo se evita pasar por dos PO.
9. "El primer usuario crea el primer proyecto" (L171) vs. cualquiera puede crear proyectos (`/projects/new/`); la matriz de permisos no cubre "crear proyecto".
10. Tabla de permisos incompleta: borrar tareas, crear sprints, notas de review/retro, dependencias. El PO no puede asignar sprints, decisión sin justificar.
11. Códigos HTTP inconsistentes: formulario inválido 422; departamento duplicado 409; dependencia duplicada y correo repetido 422. No hay criterio para 409 vs. 422.
12. Rutas ambiguas: `POST …/members/<user_id>/` para cambiar rol o quitar; `columns/` para crear o editar. No hay ruta para crear columna, editar/borrar épicas e hitos, editar proyecto ni borrar sprints.
13. Borrado de tarea (409): no se dice si falla por estar asignada a un sprint.
14. Hitos: sin relación definida con sprints, épicas o tareas; sin edición ni borrado.
15. Gantt: las historias se dibujan como resumen, pero la estructura de datos no distingue historias de tareas ni qué pasa si no tienen tareas con fechas.
16. `is_late` para historias (con `column` nula): no definido.
17. Regla 4 vs. G3/G5 y la decisión "híbrido": con sprint y una sola fecha propia se mezclan fechas propia y de sprint; la redacción sugiere que se toman en bloque.
18. Tarea con fin anterior al inicio va a `undated`: no se dice cómo ve el usuario el motivo.
19. Dependencias hacia tareas `undated`: `depends_on` puede incluir ids ausentes de `tasks`. "Estrictamente anterior" no define el caso del mismo día.
20. Columna generada de MySQL: el modelo no la declara; no se explica cómo `makemigrations --check` evita ruido, ni por qué MySQL no admite la restricción condicional.
21. "Fase 2" (futuro) colisiona con F2 (Backlog y sprints).
22. Criterio de F3 de concurrencia: no dice cómo se obtiene (hilos, un cliente por hilo) y un recorrido manual no la reproduce.
23. `--cov-fail-under=80` en `addopts` hace fallar `pytest` en fases con poco código o al correr una sola prueba.
24. F1: `/projects/<id>/` redirige a un tablero que no existe hasta F3; la barra de navegación enlaza a vistas inexistentes. "Cada fase deja el sistema ejecutable" no se cumple en F1.
25. `test_roles`/`test_isolation` (F2) prueban departamentos, que se crean en F5.
26. Posible ciclo de imports: `board.services` necesita `Task`/`Sprint` y `backlog.assign_sprint` llama a `board.services.apply_placement`. No se indica qué app depende de cuál. Tampoco cómo `board` "recibe el rol".
27. Operador y sesiones ajenas: no se explica cómo se borran; falta `createsuperuser` en el README.
28. Versiones de MySQL inconsistentes (8, 8.0, ≥ 8.0.16); PyMySQL como alternativa sin estar en `requirements*.txt`.
29. `tests/` fuera de las apps: conviene aclararlo.
30. Alternativa L rechazada pero su idea se adopta como plan B: redacción confusa.

## Términos sin definir o tarde
31. "El prompt", MoSCoW y "otro documento" sin nombre.
32. "Plan anterior"/"stack anterior" (FastAPI, React, JWT): el lector no lo tiene.
33. `create_default_board`, `apply_placement`, `effective_dates`, `build_gantt`, `get_board`, `set_transitions`, `undated`, `conflict` aparecen antes de definirse.
34. "Servicio" y "caso de uso" sin definir.
35. `column_changed_at` no la usa ninguna regla. `position`: el arrastre solo envía `column_id`; no se puede guardar el orden dentro de una columna.
36. `updated_by`, `created_by`: quién las asigna.
37. HTMX, `hx-headers`, `json_script`, `data-allowed`; "(H)" solo en `move`.
38. "Operador (superusuario)".
39. "Recorrido E2E" se usa antes de definirse.
40. "Idioma del código" no es una pregunta abierta real.
41. `SprintTask` sin forma definida; afirmaciones parcialmente contradictorias sobre qué se pierde al cerrar.
42. "Equipo y plazo" sin dependencias entre fases.

## Nits
43. Estado "Draft" no marca qué secciones cambiaron. 44. Conteo de librerías/archivos JS. 45. Numeración "3b". 46. `CASCADE` omite `Sprint`, `Task`, `TaskDependency`. 47. Dos índices parecidos sin explicar. 48. Fases ejecutables (ver 24). 49. "Departamento global" y `ProjectBudget` solo en alternativas. 50. Dónde se verifica la clase `is_late` (HTML vs. SVG por JS).

## Resumen
La narrativa se entiende. Los puntos débiles: ciclo de vida de `column`/`sprint` (tareas sin sprint y de sprints cerrados); inconsistencias entre fases (rutas y pruebas que usan modelos aún inexistentes, ciclo de imports `board`/`backlog`); vacíos de contrato (orden por arrastre, historias en el Gantt, 409 vs. 422, permisos).
