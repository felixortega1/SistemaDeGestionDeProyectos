# Informe Zoom Out intermedio (Etapa 8)

**Objetivo:** `docs/designs/plan-implementacion.md` (completo, L1-384)
**Estándar:** `zoom-out-standard.md`
**Enfoque:** crecimiento de alcance y conflictos entre las correcciones propuestas en `zoom_out_report.md`, `comprehension_report.md` y `critic_report.md`.

## Estado de revisores

| Revisor | Estado |
| --- | --- |
| `egm-zoom-out` | completed |

Nota: la ruta `agents/zoom-out.md` no existe. El revisor usó `agents/zoom_out.md`. Proyecto solo de diseño, no se cuestiona el stack. Los números de línea son del plan.

## 0. Contexto

El objetivo y el porqué se entienden (L9-21). Los tres informes previos suman unos 60 hallazgos. Aplicarlos todos haría crecer el plan en modelos, rutas, permisos, locks y pruebas.

## 1. Correcciones necesarias para el MVP

| Corrección | Origen | Por qué es necesaria | Coste mínimo |
| --- | --- | --- | --- |
| Rol único por usuario bloquea el E2E (L93, L118-128, L359-369) | critic B1, zoom_out B1 | El creador es PO y solo el SM abre sprints y edita columnas. Pasos 3 y 10 del E2E y criterio de F2 inejecutables con un usuario. | Dar al PO los permisos del SM en la matriz (L124-125). Sin modelo nuevo. |
| `apply_placement` en F3 pero usado en F2 (L277-281, L313, L315) | zoom_out M1, comprehension 24-25 | Rompe "cada fase deja el sistema ejecutable" (L269). | Mover `apply_placement` y `get_board` a F2, o fusionar F2 y F3. Repartir `test_roles` y `test_isolation` por fase. |
| Ciclo de imports `board`/`backlog`/`sprints` (L307, L310, L315) | zoom_out M2, comprehension 26 | `backlog.assign_sprint` llama a `board.services`. | Una frase con el orden de capas, o fusionar las tres apps. |
| Invariantes de historias (L99, L103, L112) | zoom_out M5, critic | `column` nula contradice la regla 3b. | Solo `kind=task` va a sprint y tiene dependencias. |
| `column` de tareas sin sprint (L112, L129) | zoom_out N2, comprehension B3 | Contradicción en el modelo. | `column` nula sin sprint, asignada solo en `assign_sprint`. Elimina el reinicio al cerrar. |
| "Primer usuario" vs "cualquiera crea proyectos" (L171, L139) | zoom_out M8, comprehension 9 | Contradicción textual. | Reescribir L171. |
| Matriz de permisos incompleta (L118-128) | zoom_out M8, comprehension 10 | Faltan crear sprints, notas, dependencias. | 3 o 4 filas, solo las que usa el E2E. |
| Quitar miembro con tareas asignadas (L139) | zoom_out, critic | `assignee` PROTECT deja ruta inconsistente. | 409 si tiene tareas. |
| README "ya actualizado" (L269) vs README real (L9, L33) | zoom_out N8 | Afirmación falsa. | Corregir README o la frase. |
| "sin revisar" (L4) y "plan anterior" (L48, L229-257) | zoom_out N1, critic | El lector nuevo no tiene ese historial. | Edición de texto. |
| `--cov-fail-under=80` en `addopts` (L294) | zoom_out N6, comprehension 23 | Falla en F1 y en ejecuciones parciales. | Moverlo a CI o a F5. |
| `initdb/01-grants.sql` sin expansión de variables (L289-291) | zoom_out N7 | No funciona como está. | Nombre fijo en el SQL o un `.sh`. |
| 409 vs 422 inconsistentes (L148, L157, L349) | zoom_out M9, critic | Contrato ambiguo. | Unicidad de formulario: 422. 409 solo para estado y carreras. |
| Transferencia de PO (L128, L173) | zoom_out M6 | Puede dejar dos PO o ninguno. | Operación atómica `transfer_product_owner`. |
| Bajar `wip_limit` bajo el conteo (L111) | zoom_out N9, critic, comprehension 6 | Falta especificación. | El límite solo se valida al entrar. |
| `column_changed_at` y `position` (L99, L149) | zoom_out M3/N9, comprehension 35 | Campos sin uso o incoherentes con el arrastre. | Quitarlos u ordenar por `id`. |

## 2. Correcciones que añaden alcance (no necesarias)

| Corrección | Por qué crece el alcance | Recomendación |
| --- | --- | --- |
| `TaskEvent` / `TaskColumnEvent` | Un modelo y una escritura por movimiento, para métricas que el plan no promete (L32-40). | No añadir. Métricas de flujo como Non-Goal o fase 2. Borrar `column_changed_at`. |
| Modelo `SprintTask` (L55) | Idem. | Dejar como Open Question. |
| Roles como conjunto (`MemberRole`/banderas) | Cambia modelo, matriz y `test_roles`. | Preferir PO con permisos de SM. |
| Columna generada y `UniqueConstraint` para un solo PO | Duplica el patrón de L314 por una carrera aceptada (L173). | Transacción simple o aceptar el límite. |
| `select_for_update` sobre `Project` para ciclos de dependencias | Serialización por proyecto para un caso ya en límites (L173). | Mantener como límite conocido. |
| Orden de locks y bloqueo de sprint en `start`/`close` | Amplía el protocolo de concurrencia más allá del WIP. | Mantener lock de la columna destino (L111). El resto, límite conocido. |
| `isolation_level`, reintento 1205, `HX-Redirect`/401, `Vary: HX-Request`, manejador HTMX general | Infraestructura para un único endpoint HTMX (`move`). | Solo reintento 1213 y 409/422 en `board.js`. Añadir una frase para sesión expirada. |
| FK compuestas o `clean()`/`save()` para invariantes de mismo proyecto | Las invariantes ya están en servicios (L99). FK compuestas no son idiomáticas. | Mantener servicios y declarar el límite. |
| Umbral del plan B del Gantt, N+1 | Optimización prematura. | Nota: recorrido iterativo. El resto diferido (L184). |
| Documento comparativo, MoSCoW, métricas de éxito (M3) | Documento nuevo que mantener. | Declarar el recorte en el plan. |
| Alternativa "no construir" (M4) | Una alternativa más a A-L (L191-263). | Una línea en Open Questions (L54). |
| Registro cerrado, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`, HSTS, `clearsessions` | Checklist de despliegue ajeno al MVP de diseño. | Una línea en Supuestos (L162). |
| CRUD completo de épicas, hitos, columnas, sprints (comprehension 12) | Dobla la tabla de rutas (L136-144). | "Crear y listar" en el MVP. Quitar "editar" (L121). |
| Cambio a MySQL 8.4 LTS (M10) | Decisión de stack. | Confirmar fecha de soporte y fijar versión en una línea (L271, L290). |
| Cambio a `GeneratedField` | Alternativa opcional. | Opcional, si simplifica L314 sin `RunSQL`. |

## 3. Conflictos entre correcciones

1. **Roles combinados vs un solo PO y matriz.** Roles como conjunto choca con "un PO por servicio" (L93) y con la transferencia atómica. Se evita con "PO hereda permisos de SM".
2. **Completar matriz vs recortar rutas.** Cada fila nueva exige ruta y prueba. Criterio único: solo lo que necesita el E2E (L359-369).
3. **`apply_placement` único escritor vs cierre de sprint con WIP.** El cierre reinicia a la primera columna (L129): si valida WIP puede dar 409, y si no, rompe el único escritor (L112). `column` nula sin sprint resuelve ambos.
4. **`TaskEvent` vs `column_changed_at`.** Una corrección sustituye el campo por el evento y otra borra campos especulativos. Quitar ambos.
5. **Fusionar apps vs plan de archivos y pruebas.** Afecta ítems 19-21 y 40-47. Combinar con la corrección de orden de fases para editar una sola vez.
6. **Más locks vs reintento de deadlock (L111).** Más locks, más deadlocks y reintento más complejo. Razón para no ampliar el protocolo.
7. **Quitar `position` vs regla "última posición" (L149) y modelo (L99).** Quitar ambos o mantener ambos.
8. **Historias en el Gantt (M5) vs quitar el resumen.** Definir invariantes completos (`is_late`, `conflict`) o retirar el resumen de historia (L103, L113). Lo más corto es retirarlo y dibujar solo tareas.
9. **Pruebas por fase vs F1 ejecutable.** `/projects/<id>/` redirige al tablero (L139), inexistente en F1. En F1 debe redirigir a la lista de proyectos.
10. **README: actualizar ahora vs F5 (L287).** Mover todo a F1 y vaciar F5 de README.
11. **Documento complementario vs recorte declarado.** Elegir el recorte para no ampliar la superficie.

## 4. Conjunto mínimo de cambios

Todo son ediciones de texto del plan y del README. No se añaden modelos ni apps.

1. **Roles (L93, L124-125).** El PO tiene los permisos del SM. Añadir a la matriz: crear sprints, notas de review/retro y dependencias.
2. **Fases (L277-281, L313-315, L341-344).** Mover `apply_placement` y `get_board` a F2 y repartir pruebas por fase. Fijar orden de imports, o fusionar `backlog`, `sprints` y `board`.
3. **Tareas sin sprint (L99, L112, L129).** `column` nula sin sprint, asignada solo en `assign_sprint`. El cierre deja `sprint` y `column` nulos.
4. **Historias (L103, L113, L151).** Solo `kind=task` va a sprint y a dependencias. Retirar el resumen de historia del Gantt.
5. **Campos sin uso (L97, L99, L100, L149).** Quitar `column_changed_at`, `position` (ordenar por `id`) y `TaskDependency.type`. Declarar métricas de flujo como Non-Goal (L32-40).
6. **Códigos (L148, L157, L349).** 422 para unicidad de formulario. 409 para estado y carreras.
7. **Reglas de una frase (L111, L128, L139, L171).** `wip_limit` se valida solo al entrar. Transferencia de PO atómica. Baja de miembro con tareas da 409. Reescribir "primer usuario". Sesión expirada en HTMX.
8. **Rutas (L121, L136-144).** "Crear y listar" para épicas e hitos. En F1, `/projects/<id>/` redirige a la lista de proyectos.
9. **Configuración (L162, L271, L289-294).** `--cov-fail-under` fuera de `addopts`. Corregir `initdb`. Fijar versión de MySQL tras confirmar soporte. Una línea de despliegue tras proxy HTTPS.
10. **Documentación (L4, L13, L48, L229-257, L269, L287; README L9, L33, L37).** Quitar "sin revisar" y "plan anterior". Actualizar el README en F1. Declarar el recorte (comparativo, MoSCoW, métricas) en el plan. Cerrar la pregunta de idioma del código (L56 vs README L37).

**No hacer:** `TaskEvent`, `SprintTask`, columnas generadas para el PO, FK compuestas, protocolo de locks ampliado, manejadores HTMX generales, documento complementario ni checklist de despliegue completo.

## 5. Veredicto

Con los cambios de la sección 4 el plan queda coherente y ejecutable sin crecer. Sin ellos, el E2E no se ejecuta con un solo usuario (cambio 1) y las fases no cumplen "cada fase deja el sistema ejecutable" (cambio 2). El mayor riesgo de crecimiento es aplicar a la vez `TaskEvent`, roles como conjunto y locks ampliados: chocan con el escritor único y con el reintento de deadlock.
