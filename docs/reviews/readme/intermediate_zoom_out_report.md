# Intermediate Zoom Out Report — README.md (Stage 8)

Revisor: egm-zoom-out. Lee los informes de las etapas 5, 6 y 7. El README no ha cambiado (líneas 1-40).

## Veredicto
Las etapas anteriores coinciden en que el archivo es un prompt y no un README. Pero el informe del Critic y partes del Inventive Catalyst empujan el alcance mucho más allá del encargo. Si se aplican todas las mitigaciones, el README se convierte en especificación de requisitos, registro de decisiones y registro de riesgos a la vez.

## 1. Alcance nuevo introducido por las mitigaciones

- 🟡 **Critic 4, 7, 8 (seguridad, GDPR, OWASP, copias de seguridad, auditoría, latencia p95, disponibilidad, máximo de tareas).** Son requisitos no funcionales especulativos para un sistema sin usuarios ni repositorio. Basta una línea: "el plan debe declarar sus supuestos de escala y seguridad". Adoptar esa opción y rechazar las cifras.
- 🟡 **Critic 2 ("Alternativas consideradas" obligatorio sobre Gantt, ruta crítica, autenticación, hosting, monolito o servicios).** Es contenido de registro de decisiones y va en el plan generado, no en el README. Se solapa con la sección 8. Mínimo: una lista de "decisiones ya tomadas".
- 🟡 **Catalyst 2 (presupuesto ligado a tareas, horas, tarifas por rol, alertas).** El encargo pide un monto manual por área. Esto añade un módulo nuevo y contradice Zoom Out Major 5 (un campo numérico por área) y Critic 6. Mantener área + monto + moneda; consumo y alertas como no-objetivo o fase posterior.
- 🟡 **Catalyst 1 (tarea como fuente única, motor de recálculo, reglas de propagación).** El diagnóstico es correcto y es la tensión central de diseño. La solución propuesta es un motor de planificación, demasiado para un MVP. El README solo necesita la decisión: la tarea es la fuente de verdad, y tablero y Gantt son vistas derivadas. En el MVP el Gantt es de solo lectura, lo que elimina el problema de propagación.
- 🟢 **Catalyst 5 (caché del último Gantt válido, WIP aplicado en backend).** La caché es una optimización prematura. Aplicar WIP en backend es correcto pero es detalle de implementación.
- 🟢 **Critic 16 (comentarios, adjuntos, notificaciones, auditoría, etiquetas, equipos, carriles).** Riesgo puro de YAGNI. Dejarlos como no-objetivos.
- 🟢 **Critic 18 y criterios de comparación (Catalyst 4, Critic 12).** Solo refinan el prompt; no pasan al README.

## 2. Conflictos entre correcciones

- 🔴 **README vs prompt.** Zoom Out Blocker 1, Comprehension 1 y Critic 3 coinciden en separar `README.md` y `docs/plan-prompt.md`. Pero Critic 1, 2, 4, 7, 8, 10, 11, 12, 14 y 18 y Catalyst 4 mezclan los dos destinos. Antes de aplicar nada, etiquetar cada corrección como README o prompt. Regla: formato de salida, persona, estructura del plan y reglas de comparación van al prompt; problema, alcance, estado, stack y cómo ejecutar van al README.
- 🟡 **"Alternativas según presupuesto" (línea 32).** Zoom Out dice eliminar, Comprehension 5 dice dar una cifra, Critic 9 dice precisar qué varía o eliminar. Elegir una. Eliminar es lo más simple y coherente con el stack "definido". Si se conserva, renombrar a "costo de infraestructura" para no chocar con el presupuesto por área (línea 21).
- 🟡 **Stack (líneas 9-13).** Añadir autenticación, ORM, migraciones, despliegue, librerías, versiones y gestor de estado es sobreespecificar un proyecto sin código. Nombrar los valores por defecto en una línea, cada uno con una razón de una línea, sin alternativas.
- 🟡 **Escala.** Comprehension 3, Critic 7 y Catalyst 3 piden cifras. Dar uno o dos supuestos de tamaño (equipo, tareas esperadas) y descartar p95 y disponibilidad. El monolito modular ya cubre ambos tamaños de empresa.
- 🟢 **Coherencia Scrum/Kanban/Gantt.** Critic 5 (¿el WIP aplica dentro del sprint?, ¿el tablero muestra solo el sprint actual?) se responde en el plan con la regla de una línea anterior. El README no debe resolverlo.
- 🟢 **Orden de secciones.** Critic 13 no aplica: el orden actual sirve para un prompt y no importa para un README.

## 3. Contenido mínimo del README final
Aproximadamente una página, sin persona ni sección "Estilo".

1. **Nombre y problema (2-3 frases)** con el diferencial: Scrum + Kanban + Gantt + presupuesto manual por área en una sola herramienta. Decir por qué no bastan Jira o Linear, o declarar que es un proyecto interno o de aprendizaje.
2. **Estado:** si es proyecto nuevo y si solo existe el plan.
3. **Alcance.**
   - MVP: proyectos, backlog, sprints, Kanban con WIP, Gantt de solo lectura derivado de tareas y sprints, campo de presupuesto por área (monto y moneda).
   - No-objetivos: facturación, control de horas y consumo de costos, móvil, integraciones, notificaciones, edición avanzada de Gantt, línea base y ruta crítica (fase 2).
4. **Decisiones clave:** la tarea es fuente de verdad y tablero y Gantt son vistas derivadas; FastAPI + React + MySQL más ORM, migraciones, autenticación y despliegue en una línea; un monolito modular.
5. **Índice de documentación:** ubicación del plan generado y de `docs/plan-prompt.md`. Instrucciones de ejecución: "aún no aplicable" hasta que exista código.
6. **Idioma** del proyecto y si el código va en inglés.

Todo lo demás (esquema de 11 secciones, comparación de herramientas, persona, estilo, MoSCoW, métricas, categorías de riesgo, lista larga de entidades) va a `docs/plan-prompt.md` o al plan generado. En el prompt solo versiones ligeras: "declara tus supuestos de escala y seguridad" y "menciona alternativas solo para decisiones no fijadas".
