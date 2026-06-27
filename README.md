# pptefc — Fábrica LOCAL de presentaciones EFC

Skill de **Claude Code** para construir **decks** (propuestas comerciales) y **guías** con la
identidad visual de **EFC**, **100 % en local** — sin servidor, sin VPS, sin login.

El producto final viaja solo:
- **HTML auto-contenido** (logo en base64, CSS/JS inline, tipografía de sistema) que se abre con
  doble-click, funciona **offline** y se puede **adjuntar a un correo**.
- **PDF de calidad** (1280×720, una slide por página).

> Pensado para que cualquiera del equipo EFC o partner, con Claude Code instalado, arme
> presentaciones profesionales sin infraestructura.

---

## Instalación

```bash
git clone https://github.com/alannreyes/pptefc.git ~/.claude/skills/pptefc
```

Reiniciá Claude Code. El skill se activa solo cuando pidas armar una presentación EFC.

### Prerequisitos
- **Claude Code**.
- **Chrome o Chromium** (lo usa el exportador de PDF en modo headless) + **Poppler** (`pdftoppm`, `pdfinfo`).
- **ImageMagick** (`magick`) — recomendado para preparar imágenes.
- **Python 3** con `python-pptx` y `pdfminer.six` **solo si** vas a convertir PPTX/PDF viejos
  (`pip install python-pptx pdfminer.six`).

---

## Uso

Abrí Claude Code en la carpeta donde querés el deck y decí, por ejemplo:

> «Armemos un deck EFC para Minera Ejemplo sobre iluminación industrial. Acá está la cotización y el datasheet.»

Claude lee tus archivos, pregunta lo necesario, genera el `index.html` **auto-contenido**, aplica el
lint de tono, muestra preview, itera contigo, y genera el PDF. Después adjuntás el HTML (o el PDF) al correo.

Ver `examples/minera-ejemplo/` para un deck de muestra (cliente y datos ficticios).

---

## Qué incluye

```
pptefc/
├── SKILL.md            # la memoria operativa (reglas, identidad, componentes, lecciones)
├── knowledge/efc.md    # 8 líneas EFC + subcategorías + marcas públicas
├── design-system/      # tokens.css · deck.css · guide.css · runtime.js
├── exporters/to_pdf.py # HTML → PDF de calidad (Chrome headless)
├── extractors/         # PPTX/PDF/HTML → contenido (para migrar presentaciones viejas)
├── lint/               # validador de tono EFC
├── assets/
│   ├── efc_logo.png
│   └── library/        # escenas de faena por línea + manifest.json etiquetado
└── examples/minera-ejemplo/   # deck de muestra (ficticio)
```

---

## Assets de marcas

La librería incluye **paneles de marcas** (`assets/library/marcas/`): gráficos propios de EFC que
muestran, agrupadas por rubro, las marcas que EFC distribuye (EFC es distribuidor autorizado y esos
logos ya son públicos en efc.com.pe).

Para un **logo de marca individual** (transparente, alta resolución o SVG), usá el skill hermano
**`efcvisual`**, que lo baja **oficial y al momento** desde la fuente autoritativa — así no se
mantienen decenas de logos estáticos que se desactualizan.

---

## Identidad EFC

Verde `#6BB017` sobre fondo casi-negro `#0a0e0a`, tipografía de sistema, logo limpio.
«Lo necesitas, lo hacemos.» Solo información pública de EFC — sin datos confidenciales,
sin clientes reales, sin precios.

---

Hecho con ♥ por el equipo de innovación EFC / LuxIA.
