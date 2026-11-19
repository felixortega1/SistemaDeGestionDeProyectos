# Comprehension Report — README.md (Stage 6)

Revisor: egm-comprehension (lector sin contexto). Rango: líneas 1-40.

## What this proposes
The document is a prompt/brief, not a plan. It asks an AI (cast as a senior Scrum project manager) to write a "complete plan" for a project-tracking system. The system would combine a Kanban board (columns, WIP limits, transition policies) with a Gantt chart (dependencies, milestones, critical path, baseline, delay detection), all organized around Scrum roles, events and artifacts. The stack is fixed as FastAPI, React and MySQL. The system must work for both established companies and startups, and it must let users enter a budget amount by hand for each project area. The expected output is an 11-section document, from executive summary to success metrics. It should compare leading tools (Jira, Trello, Asana, Linear, ClickUp, Monday.com) and justify what to copy or adapt.

## How the existing system works, per this document
The document describes no existing system. It never says whether this is a greenfield build or an extension of something already built. The title says "Plan / README", but the body contains no plan and no project description, only instructions to a third party. Nothing is said about current code, users, deployment, or constraints beyond the stack.

## Findings

### 🔴 Blocker
1. **Rol del documento ambiguo (todo el archivo).** Se titula "Plan / README" pero es un prompt dirigido a una IA. Un miembro nuevo no puede saber qué es el sistema, en qué estado está ni qué se decidió. Declarar si es plantilla de prompt, README o plan. Si es README, necesita contenido real: qué es, cómo se ejecuta, dónde vive el plan generado.

### 🟡 Major
2. **Ubicación y estado del entregable (línea 7).** No se dice dónde se guardará el plan ni si ya existe.
3. **Usuarios y escala sin definir (líneas 3, 20).** Faltan tamaños de equipo y volumen (usuarios, proyectos, tareas). "Escalabilidad y equipos pequeños" no permite dimensionar la arquitectura.
4. **"Presupuesto" con dos sentidos (líneas 21, 32).** Uno es el monto por "área del proyecto", otro parece el presupuesto de desarrollo o infraestructura. "Área" no está definida (¿épica, equipo, categoría de costo?), no hay moneda, y no se dice si se compara con gasto real.
5. **"Alternativas según presupuesto" sin cifra (línea 32).** Sin restricción presupuestaria no se pueden ofrecer alternativas.
6. **Relación Scrum, Kanban y Gantt sin modelo (líneas 17, 19).** No se dice si los sprints son ventanas dentro del Gantt ni si el tablero muestra solo el sprint actual. Es la tensión central de diseño y queda sin resolver.

### 🟢 Nit
7. **Conjunto de comparación abierto (línea 7).** Las herramientas van como ejemplos ("por ejemplo") y no hay criterios para elegir qué replicar.
8. **Términos técnicos sin definir (líneas 17, 29, 31).** MoSCoW, WIP, lead time, cycle time y throughput: aceptables, pero no se indica si el plan debe definirlos.
9. **Stack incompleto (líneas 9-13).** Sin versiones, destino de despliegue, autenticación ni si frontend y backend se entregan juntos. "Definido" sugiere decisión final con detalles abiertos.
10. **Estilo subjetivo (línea 39).** "Nivel profesional" y "evita el relleno" no fijan extensión ni audiencia.
