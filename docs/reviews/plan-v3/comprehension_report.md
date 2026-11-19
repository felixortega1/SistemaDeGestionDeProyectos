# Informe de comprensión (Etapa 6) — segunda revisión

Revisor: egm-comprehension. Alcance: FeatureRange 1-296, DetailedRange 297-451. Pudo parafrasear todas las secciones; no hay Blockers. Números de línea del revisor.

## Contradicciones e inconsistencias
1. **Major.** `update_column` dice que solo hay una columna `is_done` y es la última; `create_column` añade al final. No se dice qué pasa con `is_done`, `position` ni si la siembra de transiciones con la antigua última es en ambos sentidos.
2. **Major.** La matriz mezcla permisos heredados del SM y propios del PO; la fila "Crear un proyecto" deja vacías las columnas de SM y Developer (¿n/a o no?).
3. **Major.** `assign_sprint` deja la tarea en la primera columna aunque el sprint esté `planned` (fuera del tablero): no se explica qué significa `column` mientras el sprint no está activo.
4. **Major.** E2E: el paso 11 (cerrar sprint, F2) va después de pasos de F3 y F4; ningún paso mueve una tarea a "Hecho" de forma válida, así que "las terminadas conservan el sprint" no se comprueba.
5. **Major.** Criterio F2 "terminadas conservan ambos" requiere una columna `is_done`, pero `move_task` llega en F3; en F2 solo se prueba con datos preparados a mano y no se dice.
6. **Major.** `test_migrations`: `migrate sprints zero` desaplica `backlog`, pero el criterio habla de "migraciones de `sprints` y `backlog`" y no cubre `board`.
7. **Major.** Códigos de borrado: 409 por borrado protegido vs. 403/422; la política de borrado no menciona departamentos aunque existe `POST /departments/<id>/delete/`; "borrar" vs. "quitar" miembro.
8. **Major.** Regla 3: las comprobaciones 2 y 4 requieren leer la tarea y las transiciones, pero se pide no leer tareas antes del bloqueo; no queda claro qué ocurre dentro o fuera de la transacción ni con una instancia obsoleta (la prueba "carga la tarea antes"). No se dice qué función de edición de `wip_limit` bloquea la fila.
9. **Major.** `assign_sprint` frente a un tablero sin columnas no está declarado (improbable porque no se borran columnas).
10. **Major.** Tareas sin terminar de un sprint cerrado quedan sin sprint: con fechas propias se dibujan, sin ellas van a `undated`. `is_late` usa `column.is_done`: una tarea sin sprint (sin columna) siempre se consideraría no terminada y retrasada si su `due_date` pasó; no se dice si es intencional.
11. **Major.** Hitos: sin relación con sprints o tareas; no queda claro para qué sirven más allá de mostrar una fecha.
12. **Nit.** "8.0 llega al fin de su soporte en 2026, lo que hay que confirmar": la decisión se presenta abierta.
13. **Nit.** README y `plan-prompt.md` "ya actualizados": el lector no puede verificarlo.
14. **Nit.** Open Questions solo tiene "Equipo y plazo"; no se dice qué decisión bloquea.

## Términos y referencias
15. **Major.** "El prompt" y MoSCoW sin definir.
16. **Major.** "regla 4", "regla 7", "regla 10": referencias sin enlace a "Reglas del sistema".
17. **Major.** "Product backlog" y "sprint backlog" no son entidades del modelo (el backlog son las tareas sin sprint); "Daily: el tablero" sin explicar; "equipo de desarrollo" = `developer` solo se infiere.
18. **Major.** `apply_placement`: no se dice si solo escribe o también valida (WIP, sprint cerrado, transición); reparto de responsabilidades con `assign_sprint` y `move_task` ambiguo.
19. **Major.** `start_source`, `end_source`, `undated`, `custom_class`, `data-allowed`, `hx-headers` sin explicación para quien no conoce frappe-gantt o HTMX.
20. **Major.** `effective_dates(task, sprint, today)` recibe `today` que solo usa `is_late`; `is_late` y `conflict` se calculan en `build_gantt`: reparto poco claro.
21. **Minor.** "Fase 2" (futuro) vs. "F2" (fase de implementación).
22. **Minor.** "Operador" sin definir.
23. **Minor.** "Alternativa O" se cita 270 líneas antes de definirse, sin enlace.
24. **Minor.** "Ver Supuestos" sin enlace; sin prueba de rendimiento para 2.000 tareas.

## Plan de implementación
25. **Major.** Casi todos los archivos pertenecen a varias fases ("cada fase modifica…"), pero cada ítem lleva una sola etiqueta; ítems 18 y 20 mezclan fases.
26. **Major.** Las vistas de `board` llaman a `backlog.services` (capa superior): coherente solo por la excepción de las vistas; el motivo de `apps.get_model` no se explica.
27. **Major.** `DATABASE_URL` repite las credenciales `MYSQL_*` y no hay chequeo si divergen; `01-grants.sh` no explica cómo se conecta como root.
28. **Major.** Criterio F3 de concurrencia: con reintento de deadlock "una vez", un deadlock persistente daría 409 en ambos; no se dice cuántos tolera la prueba.
29. **Major.** `test_roles`: "403 o 404 según corresponda" sin enumerar casos.
30. **Minor.** Cobertura: el comando y el lugar donde se ejecuta (¿CI?) no están definidos.
31. **Minor.** `APP_TIMEZONE` sin valor por defecto.
32. **Minor.** `frappe-gantt`: los criterios de F4 asumen `custom_class`; "combinar retraso y conflicto" queda sin decidir hasta la prueba de concepto.
33. **Nit.** `SprintTask.estimate_points` se copia pero ningún consumidor del MVP la usa.
34. **Nit.** Formato de los "pares `from_to`" de transiciones no definido; no hay ruta para corregir un hito mal escrito.

## Resumen
Casi autocontenido. Lo que más bloquearía a un lector nuevo: incoherencias entre fases (4, 5, 25), `column` en sprints `planned` (3), comportamiento de `is_done` al añadir columnas (1), y quién valida qué en `apply_placement` (18).
