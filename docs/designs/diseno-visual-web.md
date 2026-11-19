# Sistema de Gestión de Proyectos — Diseño visual de la web

*   **Author:** felixortega1
*   **Status:** Approved
*   **Date:** 2026-11-18

--------------------------------------------------------------------------------

## Overview

Este documento define cómo se ve y cómo responde la interfaz web del [sistema de gestión de proyectos](plan-implementacion.md): colores, tipografía, formas, botones, animaciones y el aspecto de cada pantalla. El plan de implementación define qué hace el sistema; este documento define su apariencia. No cambia ninguna regla de negocio, ruta ni modelo de datos.

El estilo pedido por el autor es minimalista y moderno, con una paleta que transmita facilidad de uso, botones redondeados y animaciones interactivas. Todo se construye con CSS y con el JavaScript que ya existe, sin proceso de compilación y sin librerías ni fuentes nuevas.

Alcance: solo la versión web. No hay app móvil (ver Non-Goals del plan).

## The Problem

La interfaz actual funciona, pero su estilo es provisional: un CSS corto escrito para poder probar el sistema, sin criterios documentados. Tiene tres problemas concretos:

1.  **Sin sistema de diseño.** Los colores, radios y espacios están escritos a mano en cada regla. Cambiar el acento o agregar un componente obliga a revisar todo el CSS.
2.  **Sin respuesta visible a las acciones.** Mover una tarjeta, rechazar un movimiento por el límite WIP o guardar un formulario cambian la página sin ninguna transición. El usuario tiene que comparar la pantalla antes y después para saber qué pasó.
3.  **Sin criterios de accesibilidad.** No hay reglas de contraste, de foco ni de movimiento reducido.

La propuesta es un conjunto pequeño de reglas visuales (tokens de color, escala de espacio y de radios, componentes y animaciones) que el CSS aplica de forma uniforme.

## Goals

*   **G1. Minimalismo.** Una sola acción principal por pantalla, mucho espacio libre y un solo color de acento. Todo elemento en pantalla ayuda a decidir o a actuar.
*   **G2. Facilidad de uso.** Textos cortos en español y estados siempre visibles: «conteo / límite» en cada columna del tablero, chip de estado del sprint, etiqueta «retrasada» o «conflicto» en el Gantt.
*   **G3. Estilo moderno y redondeado.** Botones en forma de píldora, tarjetas con esquinas de 12 px, sombras suaves y una sola familia tipográfica.
*   **G4. Respuesta visual a cada gesto.** Arrastrar, soltar, rechazar, guardar y navegar tienen una animación de 120 a 250 ms que confirma lo ocurrido. Ninguna animación es decorativa.
*   **G5. Accesibilidad.** Contraste AA, foco siempre visible, uso completo con teclado y sin JavaScript, y respeto por `prefers-reduced-motion` y `prefers-color-scheme`.
*   **G6. Cambio barato.** Todo color, radio, sombra y duración sale de variables CSS, de modo que cambiar el acento o el radio es editar un valor.

## Non-Goals

*   Logotipo e identidad de marca: se usa solo el nombre en texto.
*   Ilustraciones personalizadas: los estados vacíos llevan un icono lineal simple.
*   Temas elegibles por el usuario o panel de personalización (el modo claro/oscuro es automático).
*   Animaciones de transición entre páginas completas.
*   Cambios en reglas de negocio, rutas, modelos o permisos.
*   Aplicación móvil nativa.

## Open Questions

Resueltas en la revisión (2026-11-18):

*   **Color de acento:** se mantiene el índigo suave `#4F6BED` (el autor aprobó la maqueta).
*   **Fuente `Inter`:** no se incluye; se usa la fuente del sistema. Se puede agregar después sin cambiar el resto del CSS.
*   **Selector manual de tema:** queda en Future Improvements; el tema sigue al sistema operativo.

Abierta:

*   **Verificación de contraste:** los valores de la paleta están elegidos para cumplir AA, pero no se han medido con una herramienta. Se miden al implementar.

## Critical User Journeys (CUJs)

### CUJ 1: Mover una tarea y ver el límite WIP

*   **Given**: Un sprint activo con 3 tareas en «En desarrollo» (3 / 3) y una cuarta en «Por hacer».
*   **When**: El usuario arrastra la cuarta tarea hacia «En desarrollo».
*   **Then**: Al empezar el arrastre, «En desarrollo» y «En revisión» se iluminan y las demás columnas bajan al 50 % de opacidad. Al soltar, el servidor responde 409; la tarjeta vuelve a su columna con un breve temblor horizontal, la columna destino parpadea en rojo suave y aparece el mensaje «En desarrollo alcanzó su límite WIP (3 / 3)». Con `prefers-reduced-motion` se omite el temblor y queda el cambio de color y el mensaje.

### CUJ 2: Mover una tarea con éxito

*   **Given**: Un sprint activo con «En desarrollo» en 2 / 3.
*   **When**: El usuario suelta una tarea permitida sobre esa columna.
*   **Then**: La tarjeta asienta con un pequeño rebote y el contador de la columna cambia de 2 a 3 con una animación corta. No hay recarga de página.

### CUJ 3: Mover una tarea sin JavaScript

*   **Given**: Un navegador con JavaScript desactivado y un sprint activo.
*   **When**: El usuario elige una columna en «Mover a…» de la tarjeta y pulsa el botón.
*   **Then**: La página se recarga con la tarea movida (o con el mensaje de rechazo). Los botones y las tarjetas conservan su aspecto y sus transiciones de hover, que son solo CSS.

### CUJ 4: Entender el Gantt de un vistazo

*   **Given**: Un proyecto con tareas con fechas, una retrasada y una con conflicto de dependencia.
*   **When**: El usuario abre el Gantt.
*   **Then**: Las barras crecen de izquierda a derecha al cargar; la retrasada se ve en rojo y la que tiene conflicto lleva un borde ámbar. Debajo, una tabla repite el dato con las etiquetas «retrasada» y «conflicto», de modo que el color no es la única señal.

### CUJ 5: Crear una tarea desde el backlog

*   **Given**: El Product Owner en la página de backlog.
*   **When**: Pulsa «Nueva historia o tarea», completa el formulario y envía.
*   **Then**: El formulario se despliega con altura animada. Si hay un error de validación (422), el campo con error se marca en rojo con su mensaje debajo, que entra con un desvanecimiento. Si es válido, se redirige al backlog y aparece un aviso de confirmación que se cierra a los 5 segundos.

## Technical Plan (Architecture)

### Enfoque

El diseño se implementa solo con CSS y las clases que ya genera Django y HTMX. No hay sistema de componentes de JavaScript ni librería de interfaz. La única adición de datos es la lista de proyectos, que muestra el sprint activo y el avance de tareas (ver Detailed Implementation Plan). Tres piezas lo sostienen:

1.  **Tokens (variables CSS)** en `:root`, con un bloque de valores para el modo oscuro bajo `prefers-color-scheme: dark`.
2.  **Clases de componente** reutilizadas en todas las plantillas (`.btn`, `.card`, `.chip`, `.field`, `.table`, `.toast`).
3.  **Animaciones** con transiciones y `@keyframes` de CSS. Las clases que HTMX agrega durante un intercambio (`htmx-request`, `htmx-swapping`, `htmx-added`) y las que agrega `board.js` (`dragging`, `allowed`, `forbidden`, `rejected`) las activan.

```text
  styles.css
  ├─ tokens        colores, espacio, radios, sombras, duraciones, curvas
  ├─ base          reset, tipografía, enlaces, foco
  ├─ componentes   .btn  .field  .card  .chip  .table  .nav  .toast
  ├─ páginas       .board  .gantt  .sprint-card  .budget
  └─ animaciones   @keyframes + clases de HTMX y de board.js

  Django/HTMX   ──clases──►  CSS   ──►  animación
  board.js      ──clases──►  CSS
```

### Paleta (modo claro)

Un acento (índigo suave) sobre neutros fríos. Verde, ámbar y rojo solo expresan estado.

| Token | Valor | Uso |
| --- | --- | --- |
| `--bg` | `#F7F8FA` | Fondo de la página |
| `--surface` | `#FFFFFF` | Tarjetas, tablas, paneles |
| `--surface-2` | `#F0F2F6` | Columnas del tablero, campos en reposo |
| `--border` | `#E6E8EE` | Bordes finos y separadores |
| `--text` | `#1B2030` | Texto principal |
| `--text-muted` | `#6B7385` | Texto secundario y ayudas |
| `--accent` | `#4F6BED` | Botón primario, enlaces, foco, pestaña activa |
| `--accent-hover` | `#425BD4` | Hover del primario |
| `--accent-soft` | `#E8ECFD` | Fondo de selección, chips y hover de filas |
| `--success` / `--success-soft` | `#2FA37A` / `#E3F5EE` | Terminado, guardado, destino permitido |
| `--warning` / `--warning-soft` | `#D9901A` / `#FBF0DC` | Conflicto de dependencia, WIP casi lleno |
| `--danger` / `--danger-soft` | `#E5584F` / `#FCE9E7` | Retraso, borrar, rechazo (409 y 422) |

### Paleta (modo oscuro)

Se activa con `prefers-color-scheme: dark`. En oscuro, el texto del botón primario pasa a `#0F1218` y las sombras se reemplazan por un borde más claro, porque casi no se ven.

| Token | Valor |
| --- | --- |
| `--bg` | `#0F1218` |
| `--surface` | `#171B24` |
| `--surface-2` | `#1E2330` |
| `--border` | `#272D3B` |
| `--text` | `#E9ECF3` |
| `--text-muted` | `#9AA3B5` |
| `--accent` / `--accent-hover` | `#8197FF` / `#99AAFF` |
| `--accent-soft` | `#222A4A` |
| `--success` / `--warning` / `--danger` | `#4CC38A` / `#F0B24A` / `#FF7B6B` |

Reglas de uso: un solo botón primario por vista; el color nunca es la única señal (el retraso lleva la etiqueta «retrasada», el WIP lleno muestra el número); contraste mínimo de 4,5:1 en texto normal y 3:1 en texto grande y bordes de controles.

### Tipografía

*   Familia: `system-ui, -apple-system, "Segoe UI", sans-serif`. Una sola familia en toda la web, sin descargas.
*   Los números del tablero y del presupuesto usan `font-variant-numeric: tabular-nums` para que no cambien de ancho al actualizarse.

| Rol | Tamaño | Peso |
| --- | --- | --- |
| `h1` | 28 px | 650 |
| `h2` | 20 px | 600 |
| `h3` (título de columna) | 16 px | 600 |
| Texto | 15 px | 400 |
| Metadatos y ayudas | 13 px | 400 |
| Chips y etiquetas | 12 px | 500 |

### Espacio, forma y elevación

*   Rejilla de 4 px. Escala: 4, 8, 12, 16, 24, 32, 48. Ancho máximo del contenido: 1200 px.
*   Radios: `--radius-sm` 8 px (campos), `--radius-md` 12 px (tarjetas y columnas), `--radius-lg` 20 px (paneles grandes), `--radius-pill` 999 px (botones, chips, pestañas).
*   Sombras: `--shadow-1` `0 1px 2px rgba(27,32,48,.06)` en reposo; `--shadow-2` `0 6px 20px rgba(27,32,48,.10)` en hover, arrastre y menús.

### Componentes

**Botones** (todos con `--radius-pill`, altura 40 px, o 32 px en tablas y tarjetas):

| Variante | Aspecto | Cuándo |
| --- | --- | --- |
| Primario | Fondo `--accent`, texto blanco | La única acción principal de la vista |
| Secundario | Transparente, borde `--border` | Acciones alternativas |
| Texto | Sin fondo ni borde, texto `--accent` | Acciones discretas (Salir) |
| Peligro | Fondo `--danger-soft`, texto `--danger`; en hover, fondo `--danger` y texto blanco | Borrar, Quitar; nunca es el primario |

Estados: hover sube 1 px y cambia de color; pulsado escala 0,97; foco con anillo de 3 px en `--accent` al 40 % y 2 px de separación (nunca se quita); deshabilitado al 45 % de opacidad; cargando (petición HTMX) reemplaza el texto por tres puntos pulsantes y bloquea el botón para evitar doble envío.

**Campos:** fondo `--surface-2`, radio 8 px, altura 40 px, etiqueta encima en 13 px muted. Al enfocar, fondo `--surface` y borde `--accent` de 2 px. Con error, borde `--danger` y mensaje debajo con icono.

**Tarjetas:** fondo `--surface`, radio 12 px, `--shadow-1`, relleno de 16 px. Las interactivas suben 2 px y pasan a `--shadow-2` en hover. La tarjeta de tarea muestra título, avatar de iniciales del responsable, puntos en un chip y el selector «Mover a…».

**Chips:** píldoras de 12 px con fondo `*-soft` y texto del color pleno: `retrasada` (danger), `conflicto` (warning), `activo` (success), `planificado` (neutro), etiqueta de solicitante (`--accent-soft`).

**Tablas:** sin bordes verticales, separadores horizontales de 1 px, cabecera de 13 px muted, hover de fila en `--accent-soft`. En pantallas de menos de 640 px, cada fila se vuelve una tarjeta apilada.

**Navegación:** barra superior de 56 px con fondo `--surface` y desenfoque ligero al hacer scroll. La navegación del proyecto son pestañas en píldora; la activa usa `--accent-soft` y `--accent`, y el indicador se desliza entre pestañas.

**Mensajes:** avisos en píldora ancha con icono, fondo `*-soft`, que entran desde arriba; los de éxito se cierran a los 5 s y los errores permanecen hasta cerrarlos.

### Animación

Duraciones de 120 a 250 ms (ninguna supera 400 ms). Se animan solo `transform` y `opacity`. Curvas: entrada `cubic-bezier(.2, .8, .2, 1)`, salida `cubic-bezier(.4, 0, 1, 1)`, resorte suave `cubic-bezier(.34, 1.56, .64, 1)` solo en confirmaciones.

| Interacción | Animación | Duración |
| --- | --- | --- |
| Hover en botón | Sube 1 px y cambia de color | 150 ms |
| Pulsar botón | Escala 0,97 y vuelve | 100 ms |
| Hover en tarjeta | Sube 2 px, sombra a `--shadow-2` | 180 ms |
| Arrastrar tarjeta | Se inclina 2°, se eleva al 90 % de opacidad; el hueco queda como silueta punteada | continuo |
| Columnas al arrastrar | Las permitidas se iluminan en verde; las no permitidas bajan al 50 % | 150 ms |
| Soltar con éxito | Rebote corto de la tarjeta y conteo animado del contador | 250 ms |
| Rechazo (409 o 422) | Temblor horizontal de la tarjeta y parpadeo rojo suave de la columna | 300 ms |
| Contador WIP lleno | El número pasa a rojo con un pulso | 250 ms |
| Fragmento HTMX nuevo | Se desvanece y sube 6 px (`htmx-added`); el saliente se desvanece (`htmx-swapping`) | 200 ms |
| Petición en curso | Barra fina de progreso bajo la barra superior (`htmx-request`) | continuo |
| Mensajes | Entran y salen por arriba con desvanecimiento | 220 ms |
| Pestañas del proyecto | La pestaña activa cambia de color y de fondo con transición | 220 ms |
| `details` (nuevo sprint, editar) | Altura animada al abrir | 200 ms |
| Barras del Gantt | Crecen de izquierda a derecha con retardo escalonado | 400 ms |
| Carga de página | Las tarjetas entran con desvanecimiento escalonado (30 ms de diferencia, hasta 10) | 250 ms |

Con `prefers-reduced-motion: reduce` se eliminan desplazamientos, inclinaciones, rebotes y temblores; quedan solo cambios de color y de opacidad de 100 ms.

### Pantallas

| Pantalla | Aspecto |
| --- | --- |
| Entrar / registrarse | Tarjeta centrada de 400 px sobre `--bg`, campos y un botón primario de ancho completo |
| Lista de proyectos | Rejilla de tarjetas (3 columnas en escritorio, 1 en móvil) con nombre, descripción en dos líneas y el rol como chip; estado vacío con icono lineal y botón |
| Backlog | Filas con espacio generoso; las historias son tarjetas que agrupan sus tareas; crear tarea abre un panel desplegable |
| Sprints | Una tarjeta por sprint con chip de estado, fechas y objetivo; el activo lleva una franja de acento a la izquierda; el botón primario es «Iniciar sprint» o «Cerrar sprint» según el estado |
| Tablero | Columnas de ancho uniforme sobre `--surface-2`; cabecera con nombre y «conteo / límite» (rojo si está llena); política en 13 px muted; sin sprint activo, estado vacío con botón hacia Sprints |
| Columnas | Una tarjeta por columna; la matriz de transiciones usa interruptores redondeados en lugar de casillas |
| Gantt | Fondo `--surface`, rejilla tenue, barras de radio 6 px (normal `--accent`, retrasada `--danger`, conflicto con borde `--warning`, hito violeta `#8B6FD6` o `#A992E8` en oscuro) |
| Presupuesto | Monto en cifras tabulares alineado a la derecha, moneda como chip, edición en línea, «Borrar» como botón de peligro al final de la fila |
| Miembros | Avatar de iniciales, nombre, correo y rol como selector en píldora; acciones de rol y transferencia agrupadas en un menú |

### Adaptación a pantallas

| Ancho | Comportamiento |
| --- | --- |
| 1024 px o más | Diseño completo; el tablero muestra todas las columnas |
| 640 a 1023 px | Rejillas a 2 columnas; el tablero se desplaza en horizontal |
| Menos de 640 px | Una columna; tablas convertidas en tarjetas; navegación del proyecto con scroll horizontal; objetivos táctiles de al menos 44 px |

En pantallas táctiles el arrastre se activa con pulsación larga para no chocar con el scroll, y el selector «Mover a…» queda siempre visible.

## Alternatives Considered

Cada rechazo es una decisión del autor, tomada al aprobar la maqueta en la revisión.

### Alternative A: Un framework de CSS (Tailwind o Bootstrap)

*   **Pros**: componentes ya hechos, documentación amplia y menos CSS propio.
*   **Cons**: Tailwind exige un paso de compilación o su script de CDN, lo que contradice el plan (sin proceso de compilación del frontend). Bootstrap impone un aspecto reconocible que choca con el estilo minimalista pedido y añade CSS que no se usa.
*   **Reason for Rejection**: Rejected by author: el plan fija un solo proceso Django sin compilación, y el CSS propio es corto.

### Alternative B: Animaciones con una librería de JavaScript (GSAP o Framer Motion)

*   **Pros**: control fino de secuencias y de física.
*   **Cons**: añade una dependencia y JavaScript propio sin pruebas automáticas (ya es un límite conocido del plan), para animaciones que CSS resuelve con transiciones y `@keyframes`.
*   **Reason for Rejection**: Rejected by author: las animaciones pedidas se resuelven con CSS y con las clases de HTMX.

### Alternative C: Estilo con más color y profundidad (gradientes, sombras marcadas, varios acentos)

*   **Pros**: más llamativo.
*   **Cons**: contradice el minimalismo pedido y dificulta que el color de estado (retraso, conflicto, WIP lleno) destaque.
*   **Reason for Rejection**: Rejected by author: el autor pidió minimalismo y una paleta que refleje facilidad de uso.

### Alternative D: Solo modo claro

*   **Pros**: una paleta menos que mantener.
*   **Cons**: usuarios con tema oscuro en el sistema operativo ven una página clara que contrasta con el resto de su entorno.
*   **Reason for Rejection**: Rejected by author: el modo oscuro automático cuesta un bloque de variables y evita ese contraste.

## Non-Functional Requirements

*   **Accesibilidad:** contraste AA en texto y controles; foco visible con el anillo del acento; todo operable con teclado, y los menús y desplegables se cierran con Escape. Las zonas que HTMX reemplaza (tablero y mensajes) llevan `aria-live="polite"` y los errores `role="alert"`. Los iconos sin texto llevan `aria-label`.
*   **Rendimiento:** solo `transform` y `opacity` en animaciones. El CSS total debe quedar por debajo de unos 30 KB sin comprimir; WhiteNoise lo comprime. No se descarga ninguna fuente.
*   **Compatibilidad:** navegadores actuales con soporte de variables CSS, `prefers-color-scheme` y `prefers-reduced-motion`. `backdrop-filter` es un refuerzo: si no existe, la barra superior queda con fondo sólido.
*   **Despliegue:** sin cambios. No se agregan servicios ni pasos de compilación.

--------------------------------------------------------------------------------

### Additional Resources

*   [Plan de implementación](plan-implementacion.md): rutas, plantillas y comportamiento del sistema.
*   [README](../../README.md): instalación y arranque.

### Future Improvements

*   **Selector manual de tema** claro/oscuro con la preferencia guardada.
*   **Fuente `Inter`** en `static/vendor/inter/` si se quiere un aspecto idéntico entre sistemas.
*   **Orden manual de tarjetas** dentro de una columna, con su animación (depende de una mejora del plan).
*   **Atajos de teclado** en el tablero para mover tarjetas.
*   **Ilustraciones propias** para los estados vacíos.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

El código existe y funciona con un estilo provisional. Esta lista cambia su aspecto sin tocar la lógica. Las rutas son relativas a la raíz del repositorio.

### Target Files to Create/Modify

#### 1. `static/css/styles.css` (Modify)

*   **Type / Scope**: Hoja de estilos única.
*   **Proposed Changes**: Reescribir en secciones: tokens (`:root` y bloque oscuro), base y tipografía, componentes (`.btn` con sus cuatro variantes, `.field`, `.card`, `.chip`, `.table`, `.nav`, `.toast`), páginas (`.board`, `.gantt`, `.sprint-card`) y animaciones (`@keyframes` y clases `htmx-*`, `dragging`, `allowed`, `forbidden`, `rejected`). Incluir `@media (prefers-reduced-motion: reduce)` y los puntos de corte de 640 y 1024 px. Mantener las clases que ya usan las plantillas (`.card`, `.tag`, `.muted`, `.messages`, `.columns`, `.column`, `.task-card`, `.move-form`) o renombrarlas en el mismo cambio que sus plantillas.

#### 2. `templates/base.html` (Modify)

*   **Type / Scope**: Plantilla base.
*   **Proposed Changes**: Añadir la barra de progreso de HTMX bajo la barra superior, la región de mensajes con `aria-live="polite"` y la navegación del proyecto como pestañas con indicador. Un pequeño script de cierre automático de avisos de éxito (5 s).

#### 3. `templates/accounts/login.html`, `register.html`, `templates/projects/list.html`, `new.html`, `members.html` (Modify)

*   **Type / Scope**: Plantillas de cuenta y proyectos.
*   **Proposed Changes**: Usar las clases de componente (`.btn`, `.btn-secondary`, `.field`, `.card`, `.chip`), la tarjeta centrada de acceso y la rejilla de proyectos con estado vacío. Agrupar las acciones de rol y de transferencia en un menú en `members.html`.

#### 4. `templates/backlog/backlog.html`, `task_form.html`, `templates/sprints/sprints.html` (Modify)

*   **Type / Scope**: Plantillas de backlog y sprints.
*   **Proposed Changes**: Reemplazar estilos sueltos por las clases de componente, usar `.chip` para estados, la franja de acento del sprint activo y `details` con altura animada para los formularios de creación y edición.

#### 5. `templates/board/board.html`, `_board.html`, `_card.html`, `columns.html` (Modify)

*   **Type / Scope**: Plantillas del tablero y de columnas.
*   **Proposed Changes**: Cabecera de columna con «conteo / límite» en cifras tabulares; clase `.full` cuando se alcanza el límite; avatar de iniciales y chip de puntos en la tarjeta; `aria-live="polite"` en `#board` y `role="alert"` en el mensaje; interruptores redondeados en la matriz de transiciones de `columns.html`.

#### 6. `templates/gantt/gantt.html`, `templates/budget/budget.html`, `templates/error.html` (Modify)

*   **Type / Scope**: Plantillas de Gantt, presupuesto y error.
*   **Proposed Changes**: Chips «retrasada» y «conflicto» en la tabla del Gantt, monto en cifras tabulares y moneda como chip en el presupuesto, y estilo de error con el color de peligro suave.

#### 7. `static/js/board.js` (Modify)

*   **Type / Scope**: JavaScript del tablero.
*   **Proposed Changes**: Solo agregar y quitar clases. Al soltar con 409 o 422, agregar `rejected` a la columna destino y a la tarjeta tras el reemplazo (`htmx:afterSwap`); no calcular animaciones en JavaScript. Activar el arrastre con pulsación larga en pantallas táctiles (`delay` y `delayOnTouchOnly` de SortableJS).

#### 8. `static/js/gantt.js` (Modify)

*   **Type / Scope**: JavaScript del Gantt.
*   **Proposed Changes**: Mantener las clases `gantt-late`, `gantt-conflict` y `gantt-milestone`; los colores se definen en el CSS con tokens. No se agrega estado «terminada»: `build_gantt` no entrega ese dato y el contrato del plan no cambia.

#### 9. `apps/projects/views.py` y `templates/projects/list.html` (Modify)

*   **Type / Scope**: Vista de la lista de proyectos.
*   **Proposed Changes**: La vista añade a cada proyecto el nombre del sprint activo y el conteo de tareas terminadas sobre el total de ese sprint, para dibujar la barra de avance y el chip «Sprint activo». Es solo lectura y no cambia modelos ni rutas. Usa consultas del ORM sobre `Task` mediante `apps.get_model` (la vista puede usar cualquier app).

### Verification Plan

*   **Compilation/Build**: `python manage.py check` y `python manage.py collectstatic --noinput` (comprueba que los estáticos se resuelven).
*   **Unit Tests**: `pytest`. Las pruebas existentes no deben cambiar; solo se actualiza una aserción si depende de un texto o una clase que se renombre.
*   **Static Analysis & Linting**: `ruff check`.
*   **Test Coverage Requirement**: sin cambios (`pytest --cov=apps --cov-fail-under=80`).
*   **E2E/Integration**: recorrido manual del plan con la aplicación corriendo, más esta lista visual:
    *   Tablero: arrastre permitido, arrastre rechazado por WIP (temblor y mensaje), selector «Mover a…» con JavaScript desactivado.
    *   Gantt: barras con retraso, con conflicto y con hito.
    *   Modo oscuro (emulación de `prefers-color-scheme: dark`) y movimiento reducido (`prefers-reduced-motion: reduce`).
    *   Anchos de 375, 768 y 1280 px.
    *   Navegación completa con teclado y foco visible en todos los controles.
    *   Medición de contraste de los pares texto/fondo de ambas paletas (mínimo 4,5:1).

--------------------------------------------------------------------------------

*Drafted with EGM*
