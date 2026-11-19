# Informe de comprensión (Etapa 6) — tercera revisión

Revisor: egm-comprehension. FeatureRange 1-309, DetailedRange 310-466. Sin Blockers de comprensión global; pudo parafrasear todas las secciones. Números de línea del revisor.

## Contradicciones e inconsistencias
1. **Major.** Paso 12 del E2E marcado F3 pero la lógica de cierre es de F2; el desfase se reconoce entre paréntesis y confunde.
2. **Major.** `apps/backlog/` "F2 y F3": no queda claro qué entrega cada fase (`move_task` y `get_board` en F3 sobre migraciones ya existentes).
3. **Major.** Permisos del Developer: "cambiar el `assignee` lo hace quien puede editar la tarea" permite que un Developer se reasigne o desasigne a sí mismo; una tarea sin responsable no la edita ningún Developer pero sí la mueve (asimétrico, sin justificar).
4. **Major.** El bloqueo "evita que dos operaciones corran a la vez", pero editar `wip_limit` no lo toma (solo se dice en la regla 3); no se explica cuándo ocurre una carrera si todo está serializado (`IntegrityError` → 409).
5. **Major.** `GeneratedField` con `db_persist=False` presentado como decisión cerrada, aunque el ítem 19 admite que no se ha verificado que `makemigrations` genere el DDL.
6. **Major.** La Alternativa L ("sin JavaScript propio") se rechaza pero el plan usa su idea como respaldo; la redacción confunde.
7. **Minor.** Rutas `columns/transitions/` vs `columns/<id>/edit/` mezclan estilos.
8. **Major.** Tarea terminada con responsable que ya no es miembro: no se define qué ocurre al editarla.
9. **Minor.** Comprobación redundante de "columna del mismo proyecto" (paso 2) y la tabla de transiciones; la lista de orden de `test_board_wip` se nombra distinto.
10. **Minor.** `board` es "inferior" a `projects` en imports, pero `board.0001` depende de `projects.0001` en migraciones (FK por cadena); se explica solo en parte.
11. **Minor.** `position`: sin numeración definida ni cálculo de la siguiente posición al insertar una columna.

## Términos sin definir o sin enlazar
12. **Major.** "Fin-a-inicio". 13. **Major.** "Hito" (propósito y que no se relaciona con sprints). 14. **Major.** "Épica" e "historia" y su relación con tareas (una historia con épica y sin sprint ¿es válida?). 15. **Major.** "Backlog = tareas sin sprint" choca con que las historias nunca tienen sprint y con las terminadas de sprints cerrados. 16. **Major.** "Política" designa a la vez `ColumnTransition` y `policy_text`. 17. **Major.** `is_done`: quién lo fija en una columna nueva y por qué hay una sola. 18. **Major.** `SprintTask` y tareas que pasan por varios sprints; explicación de por qué no hay burndown en una línea. 19. **Major.** "Operador" se explica lejos de su primera aparición y `createsuperuser` solo está en el README (F5). 20-22. **Minor.** Términos de Django (`GeneratedField`, `db_persist`), "E2E" y "idempotente". 23. **Minor.** Enlaces no verificables; quién hará el análisis comparativo. 24. **Minor.** `HX-Request` y `HX-Redirect`.

## Ambigüedades
25. **Major.** `conflict`: el caso mixto (inicio heredado, fin propio) y fechas propias iguales quedan sin resolver.
26. **Major.** Tarea con sprint cuyas fechas son nulas (`planned`) y sin fechas propias: ¿`undated` con `sin fechas`? Hitos "si la prueba de concepto lo permite" queda sin decidir.
27. **Major.** `is_late` nunca para tareas sin sprint, aunque tengan fechas propias vencidas, sin justificar.
28. **Major.** "Una edición simultánea de `wip_limit` puede aplicarse a un movimiento en curso, sin consecuencias": sin explicar.
29. **Major.** CSRF en formularios sin JavaScript no se explica.
30. **Minor.** `CONN_MAX_AGE`/"una conexión por petición". 31. **Minor.** Open Questions no recoge la justificación comparativa. 32. **Minor.** "Tres librerías pequeñas". 33. **Minor.** No hay prueba de la vista del Gantt (`is_late` en `json_script`) en la lista de pruebas. 34. **Minor.** Criterios de F5 incompletos (roles en presupuesto). 35. **Minor.** Python 3.12 sin motivo; mezcla de comandos de Windows y Linux. 36. **Minor.** "EGM" sin definir.

## Resumen
Autocontenido y honesto sobre sus premisas. Lo principal para un lector nuevo: vocabulario de dominio (épica, historia, hito, fin-a-inicio) fuera de Términos; backlog definido como "tareas sin sprint" aunque las historias nunca tienen sprint; casos de fechas sin resolver; el Developer puede reasignarse; solapamiento F2/F3 en backlog y en el paso 12 del E2E; capas vs. migraciones de `board`; `GeneratedField` sin verificar presentado como cerrado.
