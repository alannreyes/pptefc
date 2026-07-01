#!/usr/bin/env python3
"""Exporter canonico de decks EFC a PDF (landscape 1280x720, una slide por pagina).

Uso:
    python3 to_pdf.py <ruta-al-deck>
    # <ruta-al-deck> puede ser la carpeta del deck o su index.html.
    # Genera <slug>.pdf junto al index.html.
    python3 to_pdf.py <ruta> --out otro-nombre.pdf
    python3 to_pdf.py <ruta> --keep-tmp   # conserva el _pdf.html intermedio
    python3 to_pdf.py <ruta> --raster     # fuerza modo raster (foto a sangre)
    python3 to_pdf.py <ruta> --print      # fuerza modo print (texto sobre negro)

Dos modos (auto-detectados; ver `pick_mode`):
  • PRINT  -> decks del catalogo (texto sobre negro, enlazan /lib/deck.css).
             Reflow real: cada .slide pasa a 720px, encoge con `zoom`. CSS y
             logo /lib se inembeben. Tipografia vectorial nitida, PDF liviano.
  • RASTER -> decks STANDALONE / image-forward (CSS embebido y/o fondos a sangre
             `<img class="bg">`). Rasteriza cada slide con Chrome (1280x720 @2x)
             y las une en PDF. Fiel al render real (full-bleed, veils, gradientes
             text-clip) que el reflow de print rompe. Pesa mas (fotos).

Por que existe (lecciones pagadas en produccion):
  1) Los decks del catalogo referencian /lib/tokens.css, /lib/deck.css y
     /lib/efc_logo.png. En file:// esos enlaces NO resuelven -> el PDF saldria
     sin CSS base. El modo PRINT INEMBEBE el CSS y el logo (base64).
     Los decks STANDALONE ya traen el CSS embebido y NO tienen /lib -> antes el
     exporter ABORTABA con "No encontre /lib". Ahora /lib es opcional.
  2) Las fuentes usan clamp(...vw...), que dependen del ANCHO de la ventana. Hay
     que medir con viewport = ancho de pagina (1280) para que medicion e
     impresion coincidan -> Chrome con --window-size=1280,720.
  3) En paged media, Chrome fragmenta/recorta segun la caja de layout ANTES de
     aplicar transform:scale -> recorta el contenido alto. Por eso encogemos con
     `zoom` (reduce la caja de layout REAL), centrando con flexbox.
  4) El reflow de PRINT envuelve todos los hijos del slide en un `.pdf-fit`
     centrado -> en decks con fondo a sangre (`<img class="bg">`) eso ARRUINA el
     full-bleed (la foto se mete en la caja centrada). Para esos decks va RASTER.

Requisitos: Google Chrome instalado. Modo RASTER une PNGs a PDF con img2pdf o
ImageMagick (magick/convert), lo que haya. No requiere Playwright ni Node.

PDF DE ENTREGA AL CLIENTE (leccion pagada, deck Glencore/Antapaccay):
  • Slides INTERACTIVOS (hover/tabs como "8 divisiones", carruseles/marquee) en
    estatico muestran solo 1 estado / recortado. Para el PDF hay que EXPANDIRLOS:
    una pagina por estado desarrollado, o el marquee -> grilla completa.
  • Forzar layout de ESCRITORIO: neutralizar @media (max-width: <=1200px) -> si no,
    donuts/grillas salen en version MOVIL rota (breakpoints tipicos 1100px).
  • 🔴 NUNCA comprimir el PDF con Ghostscript (gs/pdfwrite). Reescribe las mascaras
    de transparencia (soft-mask) de PNG/logos y VISTA PREVIA de Mac (Quartz) las
    muestra EN BLANCO -> abre en unos visores y en otros no. El PDF NATIVO de Chrome
    funciona en todos lados. Si pesa mucho para correo: reducir las imagenes ORIGEN
    y re-render con Chrome (sigue nativo), o mandar LINK. ~8-9MB pasa por Gmail
    (25MB)/Outlook (20MB); ojo topes corporativos de 10MB (base64 viaja ~+33%).
"""
import re, sys, base64, pathlib, subprocess, argparse, shutil, tempfile

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if pathlib.Path(c).exists():
            return c
    raise SystemExit("No encontre Google Chrome / Chromium. Instala Chrome.")


def find_repo_root(start: pathlib.Path):
    """Sube directorios buscando lib/deck.css (raiz del sitio). None si standalone."""
    for p in [start, *start.parents]:
        if (p / "lib").is_dir() and (p / "lib" / "deck.css").exists():
            return p
    return None


def pick_mode(index_html: pathlib.Path) -> str:
    """Auto-detecta 'print' (texto sobre negro) vs 'raster' (foto a sangre).

    Senal precisa y conservadora: RASTER solo si el deck tiene fondos a sangre
    `<img ... class="bg">` como hijos de slide (image-forward) -> el reflow de
    PRINT (que envuelve los hijos en un .pdf-fit centrado) ARRUINARIA el full-bleed.
    El resto va PRINT (vectorial, liviano), incluyendo decks standalone de texto.
    Regla: los decks de texto sobre negro tienen 0 `<img class="bg">` -> siguen en
    PRINT; este criterio NO los voltea a RASTER.
    Senales mas laxas (enlaza-/lib, o cualquier .bg) daban falsos positivos:
    `\\bbg\\b` matchea ".bg-video"; y varios decks de catalogo embeben el CSS.
    Un deck image-forward que prefiera vectorial puede forzar --print.
    """
    src = index_html.read_text(encoding="utf-8")
    return "raster" if re.search(r'<img[^>]*class="[^"]*\bbg\b[^"]*"', src) else "print"


def build_autocontained_html(index_html: pathlib.Path) -> str:
    src = index_html.read_text(encoding="utf-8")
    repo = find_repo_root(index_html.parent)
    lib = (repo / "lib") if repo else None

    # 1+2) Inembeber CSS y logo /lib SOLO si el deck es de catalogo (enlaza /lib).
    #      Los standalone ya traen el CSS embebido -> se saltan estos pasos.
    if lib:
        def inline_css(match):
            href = match.group(1)
            css_file = lib / pathlib.Path(href).name
            if css_file.exists():
                return f'<style data-inlined="{css_file.name}">\n{css_file.read_text(encoding="utf-8")}\n</style>'
            return ""
        src = re.sub(r'<link[^>]+href="/lib/([^"]+\.css)"[^>]*>', inline_css, src)

        def inline_img(match):
            name = match.group(1)
            f = lib / pathlib.Path(name).name
            if not f.exists():
                return match.group(0)
            ext = f.suffix.lstrip(".").lower()
            mime = {"svg": "svg+xml", "jpg": "jpeg"}.get(ext, ext)
            b64 = base64.b64encode(f.read_bytes()).decode()
            return f'data:image/{mime};base64,{b64}'
        src = re.sub(r'/lib/([^"\')\s]+\.(?:png|jpe?g|svg|webp))', inline_img, src)

    # 3) Impresion == desktop (desactivar breakpoints moviles).
    #    Tolerante a espacios: neutraliza CUALQUIER @media (max-width: <=1000px) ->
    #    max-width:1px (nunca activo en pagina de 1280). Antes era un str.replace literal
    #    que solo matcheaba la version con espacio "@media (max-width: 900px)"; los decks
    #    con "@media (max-width:900px)" (sin espacio) seguian apilando los grids 2-col en el PDF.
    src = re.sub(
        r'@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)',
        lambda m: '@media (max-width: 1px)' if int(m.group(1)) <= 1000 else m.group(0),
        src,
    )

    STYLE = """
<style id="pdf-export">
@page { size: 1280px 720px; margin: 0; }
* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
/* El fondo del PDF es negro solido (ocultamos video/veil) -> el text-shadow no
   aporta y algunos visores (Preview/Acrobat) lo pintan como mancha gris sobre
   las letras. Lo anulamos para tipografia nitida en todos los visores. */
* { text-shadow: none !important; }
html, body { margin: 0 !important; padding: 0 !important; background: #000 !important;
  height: auto !important; overflow: visible !important; }
html { scroll-snap-type: none !important; }
.bg-video, .bg-veil, .bg-deck-static, .scroll-hint, .nav-dots, .topbar,
.slide-bg-video, .slide-bg-veil, .logo-marquee, .client-tag { display: none !important; }
.brand { position: fixed !important; top: 30px !important; left: 64px !important; }
.slide {
  width: 1280px !important; height: 720px !important;
  min-height: 720px !important; max-height: 720px !important;
  margin: 0 !important; padding: 78px 0 46px 0 !important; box-sizing: border-box !important;
  overflow: hidden !important; position: relative !important;
  display: flex !important; align-items: center !important; justify-content: center !important;
  page-break-after: always; break-after: page;
  background: var(--bg-deck, #000) !important;
}
.slide:last-of-type { page-break-after: auto; break-after: auto; }
.pdf-fit { width: 100%; box-sizing: border-box; padding-left: 96px; padding-right: 96px; }
.page-num { position: absolute !important; bottom: 26px !important; right: 64px !important; }
</style>
"""

    SCRIPT = """
<script id="pdf-fit-script">
(function () {
  var TOP = 78, BOT = 46, PAGE = 720, band = PAGE - TOP - BOT;
  function wrap() {
    document.querySelectorAll('.slide').forEach(function (slide) {
      if (slide.querySelector(':scope > .pdf-fit')) return;
      var fit = document.createElement('div');
      fit.className = 'pdf-fit';
      Array.prototype.slice.call(slide.children).forEach(function (k) {
        if (k.classList && k.classList.contains('page-num')) return;
        fit.appendChild(k);
      });
      slide.insertBefore(fit, slide.firstChild);
    });
  }
  function fitAll() {
    document.querySelectorAll('.slide > .pdf-fit').forEach(function (fit) {
      fit.style.zoom = '1';
      var H = fit.scrollHeight;
      fit.style.zoom = Math.min(1, (band - 6) / H);   // zoom: encoge la caja real (no pre-recorta en print)
    });
    document.body.setAttribute('data-pdf-ready', '1');
  }
  function imagesReady() {
    return Promise.all(Array.prototype.slice.call(document.images).map(function (img) {
      if (img.complete) return Promise.resolve();
      return new Promise(function (res) { img.addEventListener('load', res); img.addEventListener('error', res); });
    }));
  }
  function run() { wrap(); fitAll(); }
  run();
  var fonts = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();
  Promise.all([fonts, imagesReady()]).then(function () { run(); setTimeout(run, 50); });
  window.addEventListener('load', run);
  window.addEventListener('beforeprint', run);
})();
</script>
"""
    return src.replace("</head>", STYLE + "</head>", 1).replace("</body>", SCRIPT + "</body>", 1)


def export_print(index_html, out_pdf, keep_tmp):
    """Modo PRINT: reflow vectorial 1280x720 (decks de catalogo, texto sobre negro)."""
    deck_dir = index_html.parent
    tmp_html = deck_dir / "_pdf.html"
    tmp_html.write_text(build_autocontained_html(index_html), encoding="utf-8")
    cmd = [
        find_chrome(), "--headless", "--disable-gpu", "--no-sandbox",
        "--disable-application-cache", "--disk-cache-size=0",
        "--window-size=1280,720", "--force-device-scale-factor=1",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=4000", "--no-pdf-header-footer",
        "--print-to-pdf=" + str(out_pdf),
        tmp_html.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not keep_tmp:
        tmp_html.unlink(missing_ok=True)
    if not out_pdf.exists():
        sys.stderr.write((r.stderr or "")[-2000:] + "\n")
        raise SystemExit("FALLO la exportacion a PDF (print).")


def _pngs_to_pdf(pngs, out_pdf, max_w=1920):
    """Une PNGs en un PDF. Prefiere img2pdf; cae a ImageMagick (magick/convert)."""
    try:
        import img2pdf  # type: ignore
        # img2pdf no reescala; encogemos antes con magick si esta, sino tal cual.
        mk = shutil.which("magick") or shutil.which("convert")
        if mk:
            small = []
            for i, p in enumerate(pngs):
                q = p.with_name(f"_r{i:02d}.jpg")
                subprocess.run([mk, str(p), "-resize", f"{max_w}x", "-quality", "82", str(q)], check=True)
                small.append(q)
            with open(out_pdf, "wb") as f:
                f.write(img2pdf.convert([str(x) for x in small]))
            for q in small:
                q.unlink(missing_ok=True)
        else:
            with open(out_pdf, "wb") as f:
                f.write(img2pdf.convert([str(x) for x in pngs]))
        return
    except ImportError:
        pass
    mk = shutil.which("magick") or shutil.which("convert")
    if not mk:
        raise SystemExit("Para modo raster instala img2pdf o ImageMagick (magick/convert).")
    cmd = [mk, *map(str, pngs), "-resize", f"{max_w}x", "-compress", "JPEG", "-quality", "82", str(out_pdf)]
    subprocess.run(cmd, check=True)


def export_raster(index_html, out_pdf, scale=2, max_w=1920):
    """Modo RASTER: rasteriza cada slide a 1280x720 y une en PDF (image-forward)."""
    deck_dir = index_html.parent
    src = index_html.read_text(encoding="utf-8")
    n_slides = len(re.findall(r'<section[^>]*class="[^"]*\bslide\b', src))
    if n_slides == 0:
        raise SystemExit("No hay <section class='slide'> -> este deck no es slide-based.")
    # Variante que aisla una slide por hash (#sN) para capturarla en el origen.
    inject = ("<script>window.addEventListener('load',function(){"
              "var n=parseInt((location.hash.match(/\\d+/)||[1])[0],10)-1;"
              "document.querySelectorAll('.slide').forEach(function(s,i){if(i!==n)s.style.display='none';});"
              "window.scrollTo(0,0);});</script>")
    cap = deck_dir / "_cap.html"
    cap.write_text(src.replace("</body>", inject + "\n</body>"), encoding="utf-8")
    chrome = find_chrome()
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="efcdeck_pdf_"))
    pngs = []
    try:
        for i in range(1, n_slides + 1):
            png = tmp / f"p{i:02d}.png"
            subprocess.run([
                chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                f"--force-device-scale-factor={scale}", "--window-size=1280,720",
                "--virtual-time-budget=3500", "--screenshot=" + str(png),
                f"{cap.as_uri()}#s{i}",
            ], capture_output=True, text=True)
            if not png.exists():
                raise SystemExit(f"FALLO al rasterizar slide {i}.")
            pngs.append(png)
        _pngs_to_pdf(pngs, out_pdf, max_w=max_w)
    finally:
        cap.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Exporta un deck EFC a PDF 1280x720.")
    ap.add_argument("deck", help="Carpeta del deck o su index.html")
    ap.add_argument("--out", help="Nombre del PDF de salida (default: <slug>.pdf)")
    ap.add_argument("--keep-tmp", action="store_true", help="Conserva el _pdf.html (modo print)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--raster", action="store_true", help="Fuerza modo raster (foto a sangre)")
    mode.add_argument("--print", dest="force_print", action="store_true", help="Fuerza modo print")
    ap.add_argument("--max-width", type=int, default=1920, help="Ancho max de pagina en raster (px)")
    args = ap.parse_args()

    p = pathlib.Path(args.deck).resolve()
    index_html = p if p.is_file() else p / "index.html"
    if not index_html.exists():
        raise SystemExit(f"No existe {index_html}")
    deck_dir = index_html.parent
    slug = deck_dir.name
    out_pdf = deck_dir / (args.out or f"{slug}.pdf")

    mode = "raster" if args.raster else "print" if args.force_print else pick_mode(index_html)
    if mode == "raster":
        export_raster(index_html, out_pdf, max_w=args.max_width)
    else:
        export_print(index_html, out_pdf, args.keep_tmp)

    if not out_pdf.exists():
        raise SystemExit("FALLO la exportacion a PDF.")
    print(f"OK [{mode}] -> {out_pdf}  ({out_pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
