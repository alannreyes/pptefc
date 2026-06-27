#!/usr/bin/env python3
"""
Extrae texto, bullets, tablas, imágenes y notas del orador desde un archivo .pptx
y produce un manifest.json común.

Uso:
    python3 from_pptx.py input.pptx output_dir/

Requisito: pip install python-pptx
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Emu
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ImportError:
    print("ERROR: instalar python-pptx → pip install python-pptx", file=sys.stderr)
    sys.exit(1)

from common import Manifest, Slide, ImageRef, ensure_assets_dir, safe_filename


def extract_text_from_shape(shape) -> dict:
    """Extrae title/bullets/paragraphs/tabla/notas de un shape."""
    out = {"title": "", "bullets": [], "paragraphs": [], "tables": []}

    if shape.has_text_frame:
        tf = shape.text_frame
        # heurística: primer párrafo en mayor tamaño = título; resto bullets/paragraphs
        for i, para in enumerate(tf.paragraphs):
            text = para.text.strip()
            if not text:
                continue
            level = para.level
            # Si es el primer párrafo y el shape es un placeholder de título → title
            is_title_ph = False
            try:
                ph = shape.placeholder_format
                if ph and ph.idx in (0,) :  # idx 0 es title
                    is_title_ph = True
            except Exception:
                pass

            if i == 0 and is_title_ph:
                out["title"] = text
            elif level >= 1 or text.startswith(("•", "-", "▸", "·")):
                out["bullets"].append(text.lstrip("•-▸· ").strip())
            else:
                out["paragraphs"].append(text)

    if shape.has_table:
        tbl = shape.table
        rows = []
        for row in tbl.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        if rows:
            out["tables"].append(rows)

    return out


def extract_images_from_shape(shape, slide_idx: int, assets_dir: Path) -> list[ImageRef]:
    """Si el shape es imagen, la guarda en assets_dir y devuelve ImageRef."""
    refs: list[ImageRef] = []
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        try:
            image = shape.image
            ext = image.ext or "png"
            blob = image.blob
            fname = safe_filename(f"slide{slide_idx + 1}_img{shape.shape_id}.{ext}")
            (assets_dir / fname).write_bytes(blob)
            refs.append(ImageRef(
                path=f"assets/{fname}",
                width=int(Emu(shape.width).pt) if shape.width else 0,
                height=int(Emu(shape.height).pt) if shape.height else 0,
                from_=f"slide:{slide_idx + 1}",
            ))
        except Exception as e:
            print(f"  ⚠ no pude extraer imagen: {e}", file=sys.stderr)
    elif shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for sub in shape.shapes:
            refs.extend(extract_images_from_shape(sub, slide_idx, assets_dir))
    return refs


def extract(input_path: Path, out_dir: Path) -> Manifest:
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    prs = Presentation(str(input_path))
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = ensure_assets_dir(out_dir)

    manifest = Manifest(
        source_type="pptx",
        source_path=str(input_path),
    )

    # Metadata core (lo que python-pptx expone)
    cp = prs.core_properties
    manifest.metadata = {
        "title":    cp.title or "",
        "subtitle": cp.subject or "",
        "author":   cp.author or "",
        "language": cp.language or "es",
        "page_count": len(prs.slides),
        "raw_metadata": {
            "comments": cp.comments or "",
            "category": cp.category or "",
            "created":  str(cp.created) if cp.created else "",
            "modified": str(cp.modified) if cp.modified else "",
            "keywords": cp.keywords or "",
        },
    }

    for idx, sld in enumerate(prs.slides):
        slide = Slide(order=idx + 1, source_index=idx)

        for shape in sld.shapes:
            t = extract_text_from_shape(shape)
            if t["title"] and not slide.title:
                slide.title = t["title"]
            slide.bullets.extend(t["bullets"])
            slide.paragraphs.extend(t["paragraphs"])
            slide.tables.extend(t["tables"])

            imgs = extract_images_from_shape(shape, idx, assets_dir)
            slide.images.extend(im.path for im in imgs)
            manifest.images_extracted.extend(imgs)

        # Notas del orador
        try:
            if sld.has_notes_slide:
                slide.notes = sld.notes_slide.notes_text_frame.text.strip()
        except Exception:
            pass

        manifest.slides.append(slide)

    return manifest


def main() -> int:
    p = argparse.ArgumentParser(description="Extrae .pptx → manifest.json + assets/")
    p.add_argument("input",  type=Path, help="archivo .pptx")
    p.add_argument("output", type=Path, help="carpeta destino")
    args = p.parse_args()

    print(f"📥 leyendo {args.input}")
    m = extract(args.input, args.output)
    out = m.save(args.output)
    print(f"✅ {len(m.slides)} slides · {len(m.images_extracted)} imágenes")
    print(f"   manifest:    {out}")
    print(f"   assets:      {args.output / 'assets'}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
