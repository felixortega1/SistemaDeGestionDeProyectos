# Prompt para generar el plan del sistema

Eres un project manager senior con experiencia en Scrum y un arquitecto de software. Construye el plan de un sistema de seguimiento de proyectos que combine un tablero Kanban y un diagrama de Gantt, siguiendo Scrum. Alcance y decisiones ya tomadas: ver [README.md](../README.md).

## Objetivo

Un documento de plan que sirva como hoja de ruta de desarrollo. Toma como referencia 3 o 4 sistemas líderes (por ejemplo Jira, Trello, Linear, ClickUp), compáralos con criterios definidos (WIP, burndown, dependencias, costo) y justifica qué replicar o adaptar.

## Requisitos que el sistema debe cumplir

- **Scrum:** roles (Product Owner, Scrum Master, equipo de desarrollo), eventos (sprint planning, daily, review, retrospectiva) y artefactos (product backlog, sprint backlog, incremento) reflejados en el sistema.
- **Kanban:** columnas, límites de trabajo en curso (WIP) y una política de transición por columna.
- **Gantt:** dependencias, hitos y relación con los sprints. Ruta crítica y línea base son fase 2.
- **Fuente de verdad:** la tarea (estado, estimación, dependencias, sprint). Tablero y Gantt son vistas derivadas. Indica cómo se aplica el WIP dentro del sprint.
- **Presupuesto:** el sistema permite ingresar manualmente un monto, con su moneda, para cada área del proyecto. Define qué es un "área" y añádela al modelo de datos.
- **Escala:** funciona para startups y empresas con un monolito modular único. Declara tus supuestos de escala y seguridad.

## Stack (decidido)

Django (plantillas y HTMX, solo Python salvo un JavaScript mínimo) y MySQL, en un monorepo. Menciona alternativas solo para decisiones que no estén fijadas.

## Estructura del documento

1. Resumen y alcance.
2. Análisis comparativo de herramientas existentes.
3. Modelo de datos (proyectos, épicas, historias, tareas, sprints, hitos, dependencias, áreas y presupuesto, usuarios y roles).
4. Integración Scrum.
5. Tablero Kanban: columnas, políticas, WIP y métricas de flujo (lead time, cycle time, throughput; define cada una).
6. Módulo Gantt: visualización, dependencias, detección de retrasos.
7. Requisitos funcionales y no funcionales, priorizados (MoSCoW).
8. Arquitectura técnica sobre el stack indicado.
9. Roadmap por fases, con criterios de aceptación comprobables.
10. Riesgos, supuestos y mitigaciones.
11. Métricas de éxito, con valor objetivo y método de medición.

## Formato

Markdown en español, con tablas y listas donde aporten claridad. Sin relleno genérico; cada sección termina con las decisiones tomadas.
