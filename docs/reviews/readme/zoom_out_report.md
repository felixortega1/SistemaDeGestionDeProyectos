# Zoom Out Report — README.md (Stage 5)

Revisores: egm-zoom-out, egm-inventive-catalyst. Rango: líneas 1-40.

## Veredicto

El archivo no funciona como README. Es un prompt dirigido a un modelo ("Eres un project manager senior… Ayúdame a construir…"). No dice qué existe, en qué estado está, cómo se ejecuta ni qué decisiones ya se tomaron.

## Zoom Out

### 🔴 Blocker
1. **El README es una instrucción a una IA, no documentación (líneas 1-3, 37-39).**
   - La persona ("Eres un project manager senior"), la sección "Estilo" y "Ayúdame" son contenido de un prompt.
   - El título "Plan / README" mezcla dos funciones.
   - Corrección: mover el prompt a `docs/plan-prompt.md`. El README debe cubrir problema, usuarios, alcance y no-objetivos, estado, stack, cómo ejecutar y enlace al plan.

### 🟡 Major
2. **No se enuncia el problema (líneas 5-7, 23-35).** El objetivo es un entregable ("obtener un plan"). No dice qué dolor resuelve ni por qué no bastan Jira, Trello o Linear. Replicar "las mejores características" es paridad de funciones, no justificación. Añadir 2-3 frases sobre problema y diferencial (Scrum + Kanban + Gantt + presupuesto por área).
3. **Alcance excesivo (líneas 15-21, 23-35).** Se piden a la vez eventos y artefactos Scrum completos, WIP y métricas de flujo, Gantt con ruta crítica y línea base, MoSCoW, escalabilidad empresa/startup y análisis competitivo. Definir un MVP (proyectos, backlog, sprints, Kanban, Gantt de solo lectura derivado de fechas) y listar el resto como no-objetivos o fases posteriores. La línea 20 ("escalabilidad") no es medible. La línea 32 ("alternativas según presupuesto") contradice que el stack ya está "definido".
4. **Stack sin justificación y con huecos (líneas 9-13, 21).** Falta decir por qué ese stack. Faltan autenticación y roles (OAuth2/JWT estándar), ORM y migraciones (SQLAlchemy y Alembic), destino de despliegue y configuración por entorno. Elegir librerías existentes para Kanban y Gantt y no diseñar a medida; la ruta crítica es un algoritmo de grafos estándar.
5. **Presupuesto sin definir (línea 21).** "Área" no existe en el modelo de datos (línea 27). Faltan moneda, si solo se ingresa o también se compara con gasto, y si es por proyecto o por sprint. Caso mínimo: un campo numérico por área.

### 🟢 Nit
6. **Altitud (líneas 23-35).** El esquema de 11 secciones es de nivel adecuado. Las secciones 7 y 10 se solapan, y también 1 y 11. La sección 2 (análisis competitivo) es investigación que va en otro documento.
7. **Idioma y términos (líneas 1, 17, 19).** Declarar el idioma del proyecto y si el código irá en inglés. "Incremento" e "hitos" no están definidos.

## Inventive Catalyst

### 🟡 Major
1. **Tres fuentes de verdad: Scrum, Kanban y Gantt (líneas 17-19, secciones 4-6).** La sección 6 pide "la relación entre el cronograma y los sprints" sin decir cuál manda. Si un sprint se mueve el Gantt se desfasa, y lo mismo si una tarea cambia de columna. Resolución: la tarea (estado, estimación, dependencias, sprint) es la única fuente. Tablero y Gantt son vistas derivadas. Las fechas del Gantt salen de sprint más dependencias, y las ediciones manuales son restricciones explícitas. Costo: hace falta un motor de recálculo y reglas de propagación cuando se edita una barra del Gantt. **Es la contradicción central y debe resolverse antes de la sección 3 (modelo de datos).**
2. **Presupuesto aislado (línea 21, sección 3).** Una cifra manual sin relación con tareas ni esfuerzo impide avisar de desvíos. Resolución: mantener la entrada manual, asociar cada área a sus tareas y épicas, y precalcular el consumo estimado (puntos u horas por tarifa) para alertar de sobrecosto. Costo: tarifas por rol, registro de horas y permisos, porque es información sensible.
3. **Empresa vs startup resuelto con arquitecturas distintas (línea 20, sección 8).** Resolución: un único monolito modular FastAPI (scrum, tablero, Gantt, presupuesto) con despliegue mínimo (un contenedor más MySQL). Réplicas, caché y workers solo cuando la carga lo pida. Funciones de empresa como configuración o feature flags. Costo: disciplina en las fronteras de módulo y más combinaciones que probar.

### 🟢 Nit
4. **README y prompt mezclados (líneas 3, 37-39, sección 2).** Mover el prompt a otro archivo. Acotar la comparación competitiva a 3-4 herramientas con criterios definidos (WIP, burndown, dependencias, costo).
5. **Riesgos como tabla pasiva (secciones 7 y 10).** Pedir mecanismos concretos: versión en caché del último Gantt válido si falla el recálculo, y WIP y políticas de transición aplicados en el backend, no solo en la interfaz.

## Acciones propuestas, por prioridad
1. Separar README y prompt (Blocker 1 y Nit 4).
2. Enunciar problema, diferencial, MVP y no-objetivos (Major 2 y 3).
3. Fijar la fuente única de verdad en la tarea (Catalyst 1) y definir "área" y presupuesto (Major 5 y Catalyst 2).
4. Completar el stack con auth, ORM, migraciones, despliegue y librerías Gantt/Kanban (Major 4); eliminar "alternativas según presupuesto" (Catalyst 3).
