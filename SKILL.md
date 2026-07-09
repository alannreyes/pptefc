---
name: pptefc
description: Construye presentaciones comerciales (decks) y guías panorámicas con la identidad visual de EFC, 100% en LOCAL — sin servidor, sin VPS, sin accesos. Genera HTML auto-contenido (logo en base64, CSS/JS inline, tipografía de sistema) que se abre con doble-click y se puede enviar por correo, más export a PDF de calidad. Úsalo cuando el usuario pida "armar una presentación de X producto para Y cliente", "un deck EFC", "convertir este PPTX/PDF a presentación EFC", o trabajar con decks/guías en cualquier carpeta local.
---

# pptefc — Fábrica LOCAL de presentaciones EFC

Skill para construir **decks cinematográficos** (propuestas comerciales 1-cliente) y
**guías panorámicas** (educativas) con la identidad oficial de EFC, **enteramente en local**.

> Esta es la edición **portátil** de la fábrica de presentaciones EFC: pensada para que
> cualquiera del equipo EFC o partner, con Claude Code y este skill, arme presentaciones
> profesionales **sin infraestructura** y comparta el resultado por correo.

> **No es una librería de templates. Es una memoria operativa.** Acumula reglas que se
> pagaron iterando con clientes reales. Léelas. Aplicalas. No las re-descubras.

---

## Principio rector · TODO en local, TODO auto-contenido

`pptefc` NO usa servidor, NO publica a ningún catálogo, NO requiere login ni VPS.
El producto final es **un archivo que viaja solo**:

- **HTML auto-contenido** que se abre con doble-click (offline) y se puede **adjuntar a un correo**.
- **PDF de calidad** (1280×720, una slide por página) para descarga/impresión.

> **🔴 Entrada vs. salida.** El skill **lee** PPTX / PDF / HTML (para migrar presentaciones viejas a
> identidad EFC), pero **genera solo HTML + PDF** — **NO produce `.pptx` editable**. Es deliberado: el
> entregable viaja por correo y se ve idéntico en cualquier equipo. Si te piden un PowerPoint editable,
> este no es el flujo.

Para que el HTML viaje por correo y funcione sin internet, **TODO va embebido**:

1. **CSS embebido**: leer `design-system/tokens.css` + `design-system/deck.css` (o `guide.css`
   para guías) con la tool `Read` y pegar su contenido entero dentro de un `<style>` en el `<head>`.
2. **JS embebido**: navegación con flechas + interacciones inline en un `<script>` antes de `</body>`.
   NUNCA `<script src="...">`.
3. **Logo EFC en base64**: `base64 -i assets/efc_logo.png` y usarlo como
   `<img src="data:image/png;base64,...">`. NUNCA una ruta absoluta ni una URL.
4. **🔴 Tipografía de sistema — NUNCA Google Fonts.** El stack ya es de sistema
   (`"Helvetica Neue", "Inter", "Calibri", system-ui, -apple-system, sans-serif`, en `tokens.css`).
   **NO agregar** `<link href="fonts.googleapis.com">` ni `@import url(...)`: rompe el offline y
   el correo. Si se necesita fidelidad pixel exacta, embeber la fuente en base64 (`@font-face` con
   `src:url(data:font/woff2;base64,...)`) — pero por defecto, stack de sistema.
5. **Imágenes/videos del producto**: van en una subcarpeta `assets/` JUNTO al HTML, con ruta
   relativa (`assets/foto.jpg`). Para enviar por correo: **zippear la carpeta** (HTML + assets) o,
   si son pocas imágenes y el peso lo permite, embeberlas también en base64 para un único archivo.

**Estructura de salida** (en la carpeta donde trabaja el usuario):
```
{nombre-deck}/
├── index.html      ← auto-contenido, abrible con doble-click, adjuntable
├── {slug}.pdf      ← generado con exporters/to_pdf.py
└── assets/         ← fotos/videos propios (solo si los usás por ruta relativa)
```

NO generar `meta.json` ni nada de catálogo: este skill no publica a ningún sitio.

---

## Cinco tipos. Una sola identidad.

Cada tipo tiene estructura propia pero **toda con la misma identidad visual EFC**
(verde sobre negro, tipografía, logo, fondo cinematográfico).

### 1. `comercial` — Propuesta a cliente externo (12 slides)
Frente al cliente final (gerente, C-level, comprador). Foco en venta. Tono ejecutivo.
```
01 Portada · 02 Requerimiento · 03 La herramienta · 04 KPIs · 05 Versus · 06 Aplicaciones
07 Ficha técnica · 08 Referencias · 09 Diferenciador (opc) · 10 Por qué EFC · 11 Inversión · 12 Próximo paso
```

### 2. `interno-resumen-ejecutivo` — Caso a directorio/gerencia (5–7 slides densos)
Portada · Contexto · Diagnóstico · Opciones · Recomendación · Costo+tiempos · Decisión que pido.
Jerga técnica permitida. Sin slide "Por qué EFC". "Decisión que pido" = pregunta concreta binaria.

### 3. `interno-status-proyecto` — Status recurrente (6–8 slides)
Portada · Resumen (semáforo 🟢🟡🔴) · KPIs período-vs-período · Pipeline · Hitos · Riesgos (matriz) · Decisiones · Próximo período.

### 4. `interno-capacitacion` — Curso/proceso
Cada módulo: **concepto → ejemplo concreto → checklist accionable**. Outcomes al inicio, recursos al final.

### 5. `guia` — Guía panorámica (scroll continuo, TOC sticky, glosario al final)
Hero · TOC · Decisión · Categorías · Mapa fabricantes · Selector · Contactos · Glosario.

Si el prompt es ambiguo, **preguntar** el tipo antes de generar.

---

## Identidad visual EFC (canónica)

### Paleta (`design-system/tokens.css`)
```css
--green:#6BB017;        /* verde corporativo (sampleado del logo) */
--green-bright:#8fd62d;  /* acento luminoso */
--amber:#f59e0b;         /* acento secundario / alertas */
--bg:#0a0e0a;            /* fondo cinematográfico casi-negro */
```
Verde EFC = identidad/capacidad propia. Naranja/ámbar = cliente, fabricantes, productos, alertas.

### Tipografía (stack de sistema, ver Principio rector)
`"Helvetica Neue", "Inter", "Calibri", system-ui, sans-serif`. Sobre video/imagen: `text-shadow: 0 2px 18px rgba(0,0,0,.55)`.

### Logo
`assets/efc_logo.png` (versión limpia, **sin "55 años"** — era campaña vieja). Embeber en base64.

---

## REGLAS DURAS · Tono y lenguaje

### Regla #1 — Menos es más
**Cada slide se lee en ≤ 10 segundos.** La presentación es un guion visual, no un documento.

| Elemento | Máximo |
|---|---|
| Eyebrow + título + subtítulo (juntos) | 12 palabras |
| Cada card / tile / item de grilla | 12 palabras |
| Lista de bullets | ≤ 5 bullets, c/u ≤ 6 palabras |
| Párrafo "intro" del slide | ELIMINAR — lo cuenta el orador |
| KPI grande | la unidad en `<small>`, el número manda |

Antes de generar, **contar las palabras del slide más cargado**. Si supera 60 totales: comprimir.

### Prohibido (lint lo marca)
- ❌ Datos inventados sin fuente verificable
- ❌ Fechas vencidas · referencias al "55 años" (campaña pasada)
- ❌ Efectismo vacío: «cambia el juego», «revoluciona», «P&L roto» sin contexto
- ❌ Tono condescendiente: «en lenguaje normal», «obviamente», «honestamente»

### `comercial` (estricto · cliente externo)
- ❌ Mencionar inventario/flota del cliente · comparaciones peyorativas por marca · jerga sin aclarar
- ❌ Términos de fricción en el cierre («postventa 15 días disconformidad», «soporte limitado»)
- ✅ Comparar arquitecturas, no marcas · aclarar acrónimos la 1ª vez · ≤ 30 palabras/slide
- ✅ Cierre con 3 next-steps factibles · contactos homologados (todos teléfono o todos correo)

### `guia`
- ✅ Glosario al final · TOC sticky · CTA de cierre. Lint en modo `guide` (jerga = warn).

---

## Componentes disponibles (`design-system/deck.css`)

🔴 **Usá los nombres de clase EXACTOS de `deck.css` — no inventes.** Antes de autorar, mirá
`examples/minera-ejemplo/index.html` como referencia de markup correcto. Los componentes reales son:

| Componente | Markup canónico |
|---|---|
| **Escala de título** | `<h1 class="titanic">` (portada) · `<h2 class="big">` / `class="huge">` (sección). La clase funciona en cualquier heading (h1..h4). |
| **Bajada / cuerpo** | `<p class="lede">` (bajada grande) · `<p class="body">` |
| **KPIs** (números grandes) | `<div class="kpi-grid"><div class="kpi"><div class="v">8 <small>líneas</small></div><div class="l">Etiqueta</div></div>…</div>` — **es `.kpi .v` y `.kpi .l`, NO `.kpi-val`/`.kpi-label`**. Grid = 4 col; para 3, `style="grid-template-columns:repeat(3,1fr)"`. |
| **Tarjetas glass** | `<div class="cards"><div class="card"><div class="tag">…</div><h3>…</h3><p>…</p></div>…</div>` (`.card.orange` para acento) |
| **Lista de prioridades** | `<ul class="big"><li><span class="n">01</span> Texto…</li>…</ul>` |
| **Cierre / próximos pasos** | `<div class="next-list"><div class="next-step"><div class="n">1</div><div><h4>…</h4><p>…</p></div></div>…</div>` |
| **Cita ancla** (apertura/cierre) | `.quote-slide` (blockquote + attribution) |
| **Roadmap / timeline** | `<div class="roadmap"><div class="rm-phase done"><div class="rm-dot">1</div><div class="rm-when">Mes 1</div><h4>…</h4><p>…</p></div>…</div>` — N fases numeradas sobre una línea (`.done` = fase cumplida) |
| **Stat-infografía** | `<div class="stats"><div class="stat"><div class="stat-ico">svg</div><div class="stat-n">38<small>%</small></div><div class="stat-l">…</div><p>…</p></div>…</div>` (`.stat.orange` para acento) |
| **Pasos de proceso** | `<div class="steps"><div class="step"><div class="step-n">01</div><h4>…</h4><p>…</p></div><div class="step-arrow">→</div>…</div>` |
| **Bar chart** | `<div class="barchart"><div class="bc-col"><div class="bc-val">$7.4<small>M</small></div><div class="bc-track"><div class="bc-fill" style="height:74%"></div></div><div class="bc-label">2023</div></div>…</div>` (`.bc-fill.proj` = proyectado punteado) |
| **Ecosistema** | `<div class="ecosystem"><svg class="eco-lines" viewBox="0 0 100 100" preserveAspectRatio="none">…líneas desde 50,50…</svg><div class="eco-node hub">…</div><div class="eco-node">…</div>×8</div>` (3×3, hub al centro) |
| **Mapa de sedes** | `<div class="sedes-map"><div class="pin" style="left:%;top:%"><div class="pin-card">…</div><div class="dot"></div></div>…</div>` |
| **Donut + stats** | `<div class="donut-stats"><div class="ds-ring"><svg viewBox="0 0 240 240">…circles con stroke-dasharray…</svg><div class="ds-center">svg</div></div><div class="ds-list"><div class="ds-row"><div class="ds-pct">50%</div><div class="ds-txt"><div class="ds-l">…</div><p>…</p></div></div>…</div></div>` |
| **Grid de íconos** | `<div class="icongrid"><div class="icard"><div class="ic">svg</div><h4>…</h4><p>…</p></div>×4</div>` |
| **Matriz de riesgo** | `<div class="riskmatrix"><div class="rm-axis y" style="grid-row:1/4;grid-column:1">Impacto</div><div class="rm-cell high"><div class="rm-dot">1</div></div>…9 celdas low/med/high… <div class="rm-axis">Prob.</div>×3</div>` → proyectos, seguridad |
| **Gantt / cronograma** | `<div class="gantt"><div class="gantt-head"><div></div><div class="g-months"><span>M1</span>…</div></div><div class="gantt-row"><div class="g-task">Tarea</div><div class="g-track"><div class="g-bar" style="left:%;width:%">…</div></div></div>…</div>` (`.g-bar.b` naranja) → proyectos, ingeniería, logística |
| **Embudo / funnel** | `<div class="funnel"><div class="funnel-stage" style="width:%;background:…"><span class="fs-label">…</span><span class="fs-val">…</span></div>…</div>` → comercio exterior, ventas. 🔴 **Una sola unidad que DECRECE** (ej. todo en ítems/mes: 190→150→132→118); NO mezclar ítems/$/% o no se entiende el embudo. El `width:%` debe ser proporcional al valor. |
| **Gauges** (anillos) | `<div class="gauges"><div class="gauge"><div class="gauge-ring"><svg viewBox="0 0 160 160">…circles stroke-dasharray…</svg><div class="gauge-pct">86%</div></div><div class="gauge-l">…</div></div>…</div>` → soporte, performance (SAC) |
| **Otros** | `.versus`/`.compare` · `.principles`/`.principle` (2 frentes) · `.axes`/`.axis` (2×2) · `.moments` · `.hitos` · `.curves` · `.ask` · `.value-chain` · `.stack` |

Color: `<span class="green">` (acento EFC) · `.orange` (cliente/producto) · `.muted`/`.dim`.

**Reglas de forma duras:**
- 🔴 **Llená el espacio.** El `.slide` centra vertical por defecto (`justify-content:center`) — NO dejes un bloque chico arriba con vacío abajo. Si un slide queda muy vacío: subí la tipografía, agregá sustancia, o usá un layout que ocupe. (`.slide.top` solo si de verdad necesitás anclar arriba.)
- 🔴 **Tamaño mínimo legible (pantalla 50"+):** títulos de sección con `.big`/`.huge` (no `<h2>` pelado, que sale ~24px) · body ≥15px (`--t-body`) · eyebrows ≥13px · labels ≥12px. Nada <12px (salvo `@media (max-width:600px)`).
- 🔴 La media query mobile (`@media (max-width:900px)`) va **al FINAL del CSS** (gana por orden).
- 🟢 Cards padding ≥1.6rem · bullets ≥1rem · si el slide tiene mucho, **subí** el título, no lo bajes.
- 🟡 Abrir y cerrar el deck con `.quote-slide` (citas ancla) da peso institucional.

---

## Workflow para un deck nuevo

1. **Leer el brief** (cliente, producto, objetivo) y todos los archivos de input con `Read`.
2. **Investigar referencias verificables** (web del fabricante, casos publicados). Sin inventar.
3. **Verificar imágenes** del fabricante con `Read` antes de aceptarlas.
4. **Confirmar al usuario** los datos clave (producto/modelo, cliente/operación, caso de uso, cotización vigente, contactos homologados).
5. **Generar las slides** (estructura del tipo elegido) como **HTML auto-contenido** (ver Principio rector).
6. **Aplicar el lint**: `python3 lint/lint.py index.html`
7. **Verificar responsive** a 375 / 768 / 1280 / 1920 px (si hay navegador) o por inspección.
8. **Generar PDF**: `python3 exporters/to_pdf.py {carpeta-del-deck}/` → `{slug}.pdf` (1280×720, 1 slide/página).
   Validar rasterizando: `pdftoppm -png -r 90 {slug}.pdf _p` y leer las slides densas. Borrar temporales.
9. **Mostrar preview** al usuario e **iterar** hasta aprobación.
10. **Compartir**: el `index.html` (+ carpeta `assets/` si la hay) se adjunta al correo o se zippea; el PDF va directo.

Para **guías**: igual, pero scroll continuo (no slide-by-slide), `guide.css`, TOC sticky, glosario. El PDF aplica solo a decks (`.slide`).

---

## Conocimiento EFC

- **Identidad y líneas de EFC** (8 líneas, subcategorías, marcas públicas, posicionamiento): ver `knowledge/efc.md`.
- EFC **no tiene eslogan en prosa por línea** — el material oficial es subcategorías + marcas (en `knowledge/efc.md`).

## Librería de assets visuales

El skill trae una librería **offline** de imágenes en `assets/library/`, indexada en `assets/library/manifest.json`
(cada asset con `tipo`, `linea`, `tags`, `licencia`). Leer el manifest para elegir por tag.

- `lineas/escena_<linea>.jpg` — **8 escenas de faena** (una por línea EFC, propias de EFC). Ideales como **fondo
  full-bleed** detrás de un slide (con velo oscuro 0.80–0.94 para legibilidad — ver lección de fondo dinámico).
- `marcas/marcas_*.png` — **paneles de marcas** (gráficos propios de EFC que muestran, agrupadas por
  rubro, las marcas que EFC distribuye). Útiles para el slide "marcas representativas".
- `productos/` — fotos de productos/máquinas EFC genéricas (`producto_<slug>_hero.jpg`).
- **Naming consistente con `efcvisual`**: `escena_<linea>.jpg`, `producto_<slug>_hero.jpg`, `marca_<slug>_logo.<ext>`.

### 🟢 Regla de derechos (qué va en el repo)
- ✅ **Assets propios de EFC**: logo, escenas de línea, **paneles de marcas que EFC distribuye**, fotos de
  productos/máquinas EFC. EFC es distribuidor autorizado de esas marcas y los logos ya son públicos en efc.com.pe.
- ✅ **Licencia libre (CC0)** con crédito en el manifest.
- 🟡 **Logo de marca individual** (transparente, alta resolución, SVG): usar **`efcvisual`** (skill hermano)
  que lo baja **oficial y al momento** — mejor que mantener decenas de logos estáticos que se desactualizan.
- ❌ **Nunca** fotos con **marca/branding de un CLIENTE** (revela relación comercial) — usar versiones genéricas.

---

## Recursos del skill

- `design-system/tokens.css` — variables, paleta, tipografía de sistema
- `design-system/deck.css` — componentes deck · `guide.css` — componentes guía · `runtime.js` — navegación
- `lint/forbidden-terms.json` + `lint/lint.py` — validador de tono
- `extractors/from_pptx.py` · `from_pdf.py` · `from_html.py` — extraen texto+imágenes de presentaciones viejas
- `exporters/to_pdf.py` — genera `{slug}.pdf` con Chrome headless (sin Playwright/Node)
- `assets/efc_logo.png` — logo oficial (embeber en base64)
- `examples/` — ejemplo de referencia (cliente ficticio)

### Prerequisitos (local, sin servidor)
- **Chrome o Chromium** instalado (lo usa `to_pdf.py` en modo headless) + **Poppler** (`pdftoppm`, `pdfinfo`) para validar.
- **Python 3** con `python-pptx` y `pdfminer.six` **solo si** usás los extractores (`pip install python-pptx pdfminer.six`).
- **ImageMagick** (`magick`) recomendado para preparar imágenes (upscale, recortes, viñetas).

### 🟢 Ver un PPTX como imágenes (analizar plantillas/PPTs sin LibreOffice) — HERRAMIENTA DEL SKILL
`python-pptx` NO renderiza (solo lee texto/estructura). Para **ver** un pptx (cuando te pasan una
plantilla o un PPT viejo y querés extraer/replicar sus infografías) usá la herramienta del skill
`extractors/render_pptx.py` (usa **aspose.slides** + **mono-libgdiplus**, sin LibreOffice):
```bash
bash tools/setup-pptx-render.sh                       # una sola vez (brew + venv ~/.pptefc-venv + aspose)
~/.pptefc-venv/bin/python extractors/render_pptx.py "plantilla.pptx" --sheet
#  → renderiza s01.png… + un _sheet.png (contact sheet) para leer todas de un vistazo
```
🔴 La versión free de aspose estampa "Evaluation only" — sirve para **analizar** (verlas), NUNCA
para deliverables. El flujo correcto: **ver** la plantilla → **re-vestir sus PATRONES con identidad
EFC** (componentes `deck.css`), jamás copiar su estilo ni reusar sus imágenes con watermark.
Esto es clave porque el fuerte del skill es **convertir pptx/pdf → HTML+CSS EFC**: hay que poder ver
el original, no trabajar a ciegas.

---

## Exporter PDF · reglas duras

Usar SIEMPRE `exporters/to_pdf.py` (Chrome headless). Pasarle la **carpeta del deck**, no el HTML. Dos modos auto-detectados:

| Modo | Cuándo | Cómo |
|---|---|---|
| **PRINT** (default) | Texto sobre negro | Reflow vectorial: cada `.slide`→720px, encoge con `zoom`, anula `text-shadow`. PDF liviano y nítido. |
| **RASTER** | Image-forward (fondo a sangre `<img class="bg">`) | Rasteriza cada slide @2× y une PNG→PDF. Fiel al full-bleed; pesa más. |

Bugs ya resueltos dentro de la tool (no re-descubrir): encoger con **`zoom`** y no `transform:scale` en print; `* { text-shadow:none !important }` para evitar sombras horneadas sobre las letras; **regex tolerante a espacios** que neutraliza `@media (max-width:≤1000px)` (sin esto, el PDF renderiza el layout móvil apilado). Validar siempre: `páginas del PDF == nº de <section class="slide">`.

---

## Lecciones de craft (genéricas, ya pagadas)

### 🟢 Sello "PENDIENTE" · estampa para data que aún no llega (defensivo + CTA)
Cuando se entrega con datos placeholder (un área aún no mandó cifras), poner una estampa visible
en vez de ocultar: cubre al autor y es llamado a la acción.
```css
.sello{position:absolute;top:84px;right:54px;z-index:6;transform:rotate(-7deg);
  border:3px dashed var(--amber);border-radius:12px;background:rgba(245,158,11,0.10);
  padding:11px 20px 9px;text-align:center;pointer-events:none;text-shadow:none}
.sello b{display:block;font-size:1.2rem;font-weight:900;letter-spacing:4px;color:var(--amber)}
.sello span{display:block;font-size:0.68rem;font-weight:700;letter-spacing:1.4px;color:var(--amber);text-transform:uppercase}
```
`<div class="sello"><b>PENDIENTE</b><span>a la espera de datos · ÁREA</span></div>` (nombrar el área = CTA).

### 🟢 Extraer cifras REALES de un PPTX (cuando el extractor solo saca texto)
Los datos de un gráfico viven en `ppt/charts/chartN.xml` (NO en el texto). `unzip` el `.pptx` y leer
con regex las categorías (`<c:cat>` → eje X) y cada serie (`<c:ser>` → `<c:tx>` nombre + `<c:val>` valores).

### 🟢 Fotos con borde gris → avatar circular + viñeta CSS (no recortar a mano)
Headshots circulares sobre gris: NO recortarlos (impreciso). Avatar circular + viñeta que oscurece
solo el borde para fundir el gris con el fondo negro:
```css
.avatar::after{content:'';position:absolute;inset:0;border-radius:50%;pointer-events:none;
  background:radial-gradient(circle at 50% 46%,transparent 52%,rgba(10,14,10,0.9) 100%)}
```

### 🟢 Componente "divisiones/portafolio interactivo" + fondo dinámico
Tiles con ícono → hover resalta y un panel muestra contenido dinámico (cobertura + marcas).
Opcional: fondo full-bleed por categoría con crossfade y **velo oscuro fuerte (0.80–0.94 negro)**
para legibilidad. 🔴 **Gotcha:** `transform:scale()` en un fondo full-bleed `position:absolute;inset:0`
SUMA al `scrollHeight` (~2%≈16px) aunque haya `overflow:hidden` → usar `background-size`, nunca `scale`.
🟡 Fondos: **escena real (faena), NO producto sobre blanco** (bajo el velo queda oscuro y vacío).

### 🟡 Menos es más en paneles de detalle
Frase de gancho + descripción concreta JUNTAS satura. Si hay la descripción concreta, esa basta.

---

## Para el equipo: cómo usar este skill

1. Instalá el skill en `~/.claude/skills/pptefc/` (cloná el repo).
2. Abrí Claude Code y decí: *"Armemos un deck para [cliente] sobre [producto]. Acá está la cotización y el datasheet."*
3. Claude lee los archivos, pregunta lo necesario, genera el deck **auto-contenido**, aplica el lint,
   muestra preview, itera, y genera el PDF.
4. Adjuntás el `index.html` (o el PDF) al correo. **Funciona sin internet, sin servidor, sin cuentas.**
