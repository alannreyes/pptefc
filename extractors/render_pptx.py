#!/usr/bin/env python3
"""
render_pptx.py — Renderiza un .pptx (o .ppt) a PNG por slide, para VER plantillas/PPTs
y extraer sus infografías. Usa aspose.slides + mono-libgdiplus (NO requiere LibreOffice).

Por qué: el fuerte del skill es convertir pptx/pdf → HTML+CSS con identidad EFC. Para
re-vestir bien una plantilla hay que VERLA primero — python-pptx solo lee texto/estructura,
no renderiza. Esta herramienta cierra ese hueco.

SETUP (una sola vez):
    bash tools/setup-pptx-render.sh
    # equivale a:
    #   brew install mono-libgdiplus
    #   python3.13 -m venv ~/.pptefc-venv && ~/.pptefc-venv/bin/pip install aspose.slides
    #   (aspose NO tiene wheel para Python 3.14 → usar 3.13)

USO (correr con el python del venv):
    ~/.pptefc-venv/bin/python extractors/render_pptx.py archivo.pptx [outdir] [--sheet] [--scale N]
    # --sheet  → además arma un contact sheet (_sheet.png) con magick
    # --scale  → factor de render (default 1.3; subir para más nitidez)

NOTA: la versión gratuita de aspose.slides estampa una marca de agua "Evaluation only".
Sirve para ANALIZAR (ver las slides), NO para producir deliverables. El flujo correcto:
ver la plantilla → re-vestir sus PATRONES con la identidad EFC (componentes deck.css),
nunca copiar su estilo ni reusar sus imágenes con watermark.
"""
import os
import sys
import glob
import shutil
import subprocess


def _ensure_gdiplus_and_reexec():
    """libgdiplus debe estar en DYLD_LIBRARY_PATH ANTES de cargar el runtime .NET de aspose.
    Como no se puede setear después del import, ponemos el env y re-ejecutamos el proceso."""
    if os.environ.get("_PPTEFC_GDIPLUS_READY"):
        return
    libdir = None
    try:
        pref = subprocess.check_output(["brew", "--prefix", "mono-libgdiplus"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
        cand = os.path.join(pref, "lib")
        if os.path.isdir(cand):
            libdir = cand
    except Exception:
        pass
    env = dict(os.environ)
    env["_PPTEFC_GDIPLUS_READY"] = "1"
    if libdir:
        env["DYLD_LIBRARY_PATH"] = libdir + os.pathsep + env.get("DYLD_LIBRARY_PATH", "")
    os.execve(sys.executable, [sys.executable] + sys.argv, env)


def main():
    _ensure_gdiplus_and_reexec()

    try:
        import aspose.slides as slides
    except ImportError:
        sys.exit("✗ Falta aspose.slides. Corré primero:  bash tools/setup-pptx-render.sh\n"
                 "  y ejecutá ESTE script con  ~/.pptefc-venv/bin/python")

    pos = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = [a for a in sys.argv[1:] if a.startswith("-")]
    if not pos:
        sys.exit("uso: render_pptx.py archivo.pptx [outdir] [--sheet] [--scale N]")

    src = os.path.expanduser(pos[0])
    if not os.path.isfile(src):
        sys.exit(f"✗ no existe: {src}")
    outdir = os.path.expanduser(pos[1]) if len(pos) > 1 else os.path.splitext(src)[0] + "_render"
    scale = 1.3
    for f in flags:
        if f.startswith("--scale"):
            try:
                scale = float(f.split("=", 1)[1]) if "=" in f else float(pos[pos.index(f) + 1])
            except Exception:
                pass
    os.makedirs(outdir, exist_ok=True)

    with slides.Presentation(src) as p:
        n = len(p.slides)
        for i, s in enumerate(p.slides, 1):
            s.get_image(scale, scale).save(os.path.join(outdir, f"s{i:02d}.png"),
                                           slides.ImageFormat.PNG)
    print(f"✓ {n} slides → {outdir}/s01.png … s{n:02d}.png")

    if "--sheet" in flags and shutil.which("magick"):
        pngs = sorted(glob.glob(os.path.join(outdir, "s*.png")))
        sheet = os.path.join(outdir, "_sheet.png")
        subprocess.run(["magick", "montage", *pngs, "-tile", "5x",
                        "-geometry", "320x180+2+2", "-background", "#222", sheet], check=False)
        print(f"✓ contact sheet → {sheet}")


if __name__ == "__main__":
    main()
