# Critic Report — README.md (Stage 7)

Revisores: egm-design, egm-structural, egm-style. Rango: líneas 1-40. Hallazgos deduplicados entre revisores.

## 🔴 Blocker

1. **Falta problema, usuarios, objetivos y no-objetivos (líneas 3-7, 15-21).** *(design, structural)* "Objetivo" describe el entregable, no el problema. No hay usuarios destino, dolor actual, escala esperada (usuarios, proyectos, equipos) ni exclusiones (facturación, control de horas, móvil, integraciones; SaaS multi-tenant o empresa única; si reemplaza a Jira). Añadir "Problema / Contexto" y "Objetivos / No-objetivos".
2. **Las alternativas solo se piden para competidores y presupuesto (líneas 7, 26, 32).** *(design, structural)* Nada exige comparar decisiones de diseño clave: librería de Gantt (construir o usar), cálculo de ruta crítica (SQL o aplicación), modelo de datos Kanban/Gantt/sprint, autenticación, hosting, monolito o servicios. Añadir "Alternativas consideradas" con motivo técnico concreto de rechazo; "buenas prácticas" no basta.

## 🟡 Major

3. **Rol del documento ambiguo (línea 1, todo el archivo).** *(structural, style, comprehension)* "Plan / README" es un prompt, no un README ni una especificación. Separar en `README.md` y un archivo de prompt (p. ej. `docs/plan-prompt.md`). La persona (línea 3) y "Estilo" (línea 37) pertenecen al prompt.
4. **Riesgos y límites sin cobertura obligatoria (línea 34, sección 10).** *(design, structural)* Exigir categorías: seguridad (autenticación, roles por proyecto, aislamiento de datos, OWASP), escalabilidad (ruta crítica en grafos grandes, detección de ciclos, Gantt con miles de tareas, ediciones concurrentes con WIP), integridad (tablero, Gantt y fechas de sprint coherentes), operación (copias de seguridad, migraciones, auditoría) y límites numéricos (tareas máximas por proyecto).
5. **Alcance contradictorio Scrum, Kanban y Gantt (líneas 3, 17-19).** *(design)* Falta indicar qué entidad es la fuente de verdad de fechas y estado y las reglas de sincronización. Preguntas abiertas: si el WIP aplica dentro del sprint y si el tablero muestra solo el sprint actual.
6. **Presupuesto sin definir (línea 21; sección 3).** *(design, style)* "Área", moneda, precisión decimal, permisos de edición y si se registra gasto real o desvío no están definidos. No aparece en el modelo de datos (línea 27) ni tiene sección propia. Añadir entidades y decidir si el seguimiento de costos queda fuera.
7. **Requisitos no funcionales sin cifras (líneas 20, 31).** *(design, style)* "Escalabilidad y equipos pequeños" no es medible. Dar objetivos (p. ej. rango de usuarios, latencia p95, disponibilidad) o exigir que el plan declare sus supuestos.
8. **Restricciones ausentes (líneas 9-13, 32-33).** *(design)* Faltan tamaño y perfil del equipo, plazo, presupuesto, destino de despliegue y cumplimiento normativo (p. ej. GDPR). Faltan también ORM, driver asíncrono, gestión de estado y justificación del stack.
9. **Contradicción: stack "definido" y "alternativas según presupuesto" (líneas 9, 32).** *(style, structural)* Indicar qué partes pueden variar o eliminar las alternativas. "Presupuesto" aquí (costo de infraestructura) se confunde con el presupuesto de la línea 21.
10. **Métricas y criterios de aceptación sin forma (líneas 33, 35).** *(design, style)* Exigir métricas con línea base, valor objetivo y método de medición; distinguir producto (adopción, previsibilidad del sprint) de sistema (latencia, disponibilidad); criterios de aceptación comprobables.
11. **Requisitos redactados como hechos y no como requisitos (líneas 15-19, 21).** *(style)* El encabezado "Requisitos que el plan debe respetar" mezcla restricciones sobre el plan y requisitos del sistema. Usar "El sistema debe…" de forma coherente. "Políticas claras" y "límites WIP" no dan valores: pedir una política por columna.
12. **"Plan completo" y "mejores características" no son verificables (líneas 3, 7, 26).** *(style)* Quitar "completo" y remitir a la lista de 11 secciones. Definir criterios de selección y si se comparan las seis herramientas o un subconjunto. Mantener "justificando cada decisión" en un solo lugar.

## 🟢 Nit

13. **Orden (líneas 23-35).** *(structural)* Los requisitos (7) van después de los diseños (3-6). Orden habitual: problema, objetivos, requisitos, diseño. Arquitectura (8) debe exigir componentes, flujos de datos e integraciones.
14. **"Estilo" al final (líneas 37-39).** *(structural, style)* Es una instrucción sobre la salida: moverla junto a la persona o a "Instrucciones de formato". Reemplazar "nivel profesional" y "evita el relleno" por restricciones comprobables (extensión máxima, qué va en tabla, idioma de salida, formato Markdown).
15. **Viñetas densas (líneas 17-19).** *(structural)* Usar listas anidadas o tabla.
16. **Entidades omitidas (secciones 3 y 5).** *(design)* Comentarios, adjuntos, notificaciones, auditoría, etiquetas, flujos de trabajo, equipos; carriles y política de bloqueados en el tablero.
17. **Términos y redacción (líneas 9, 25, 31).** *(style)* "Stack tecnológico definido" sobra "definido"; "Resumen ejecutivo" mejor "Resumen y alcance"; elegir MoSCoW u otro método; definir lead time, cycle time y throughput.
18. **Persona (línea 3).** *(design)* Un perfil de arquitecto junto al de PM encajaría mejor con las secciones 3 y 8.

## Veredicto
No cumple el estándar de especificación de funcionalidades. Corregir primero los Blocker 1 y 2 y el Major 3.
