#!/usr/bin/env python3
"""
Extrae texto e imágenes desde un .pdf y produce manifest.json común.
Cada página del PDF se mapea a un slide.

Uso:
    python3 from_pdf.py input.pdf output_dir/

Requisito: pip install PyMuPDF
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: instalar PyMuPDF → pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)

from common import Manifest, Slide, ImageRef, ensure_assets_dir, safe_filename


def extract(input_path: Path, out_dir: Path, render_pages: bool = True) -> Manifest:
    """
    render_pages=True → además de extraer las imágenes embebidas, también renderiza
    cada página completa como PNG (útil cuando el PDF original tiene texto en imagen).
    """
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    doc = fitz.open(str(input_path))
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = ensure_assets_dir(out_dir)

    manifest = Manifest(source_type="pdf", source_path=str(input_path))

    md = doc.metadata or {}
    manifest.metadata = {
        "title":    md.get("title", "") or "",
        "subtitle": md.get("subject", "") or "",
        "author":   md.get("author", "") or "",
        "language": "es",
        "page_count": doc.page_count,
        "raw_metadata": dict(md),
    }

    for idx, page in enumerate(doc):
        slide = Slide(order=idx + 1, source_index=idx)

        # texto
        text = page.get_text("text").strip()
        if text:
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if lines:
                slide.title = lines[0][:120]
                # heurística mínima: bullets si comienzan con marca, sino paragraphs
                for ln in lines[1:]:
                    if ln.startswith(("•", "-", "▸", "·", "*")):
                        slide.bullets.append(ln.lstrip("•-▸·* ").strip())
                    elif len(ln) < 100 and ln == ln.strip("."):
                        slide.bullets.append(ln)
                    else:
                        slide.paragraphs.append(ln)

        # imágenes embebidas
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
                ext = base["ext"]
                fname = safe_filename(f"page{idx + 1}_img{img_idx + 1}.{ext}")
                (assets_dir / fname).write_bytes(base["image"])
                ref = ImageRef(
                    path=f"assets/{fname}",
                    width=base.get("width", 0),
                    height=base.get("height", 0),
                    from_=f"page:{idx + 1}",
                )
                slide.images.append(ref.path)
                manifest.images_extracted.append(ref)
            except Exception as e:
                print(f"  ⚠ no pude extraer imagen {img_idx} en pág {idx + 1}: {e}", file=sys.stderr)

        # opcionalmente renderiza la página completa como PNG (300 DPI)
        if render_pages:
            try:
                pix = page.get_pixmap(dpi=200)
                fname = safe_filename(f"page{idx + 1}_render.png")
                pix.save(str(assets_dir / fname))
                ref = ImageRef(
                    path=f"assets/{fname}",
                    width=pix.width, height=pix.height,
                    from_=f"page:{idx + 1}:render",
                )
                slide.images.append(ref.path)
                manifest.images_extracted.append(ref)
            except Exception as e:
                print(f"  ⚠ no pude renderizar pág {idx + 1}: {e}", file=sys.stderr)

        # links externos
        for link in page.get_links():
            uri = link.get("uri")
            if uri and uri not in manifest.links:
                manifest.links.append(uri)

        manifest.slides.append(slide)

    doc.close()
    return manifest


def main() -> int:
    p = argparse.ArgumentParser(description="Extrae .pdf → manifest.json + assets/")
    p.add_argument("input",  type=Path, help="archivo .pdf")
    p.add_argument("output", type=Path, help="carpeta destino")
    p.add_argument("--no-render", action="store_true",
                   help="no renderizar páginas completas como PNG (default: renderiza)")
    args = p.parse_args()

    print(f"📥 leyendo {args.input}")
    m = extract(args.input, args.output, render_pages=not args.no_render)
    out = m.save(args.output)
    print(f"✅ {len(m.slides)} páginas · {len(m.images_extracted)} imágenes")
    print(f"   manifest:    {out}")
    print(f"   assets:      {args.output / 'assets'}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
