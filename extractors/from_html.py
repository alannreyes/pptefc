#!/usr/bin/env python3
"""
Extrae secciones, texto e imágenes desde un .html legacy y produce manifest.json.

Reglas heurísticas:
  - Cada <section> o <h1>/<h2> abre un slide nuevo.
  - <h1>/<h2> dentro de la sección se toma como title.
  - <p> → paragraphs.
  - <li> → bullets.
  - <table> → tables.
  - <img src=...> → images (se copian al assets_dir si son rutas locales).

Uso:
    python3 from_html.py input.html output_dir/

Requisito: pip install beautifulsoup4 lxml
"""
from __future__ import annotations
import argparse
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: instalar bs4 → pip install beautifulsoup4 lxml", file=sys.stderr)
    sys.exit(1)

from common import Manifest, Slide, ImageRef, ensure_assets_dir, safe_filename


def copy_image(src: str, base_dir: Path, assets_dir: Path) -> str | None:
    """Copia (o descarga) la imagen al assets_dir y retorna su path relativo."""
    parsed = urllib.parse.urlparse(src)
    fname = safe_filename(Path(parsed.path).name or "img.png")
    dst = assets_dir / fname

    try:
        if parsed.scheme in ("http", "https"):
            urllib.request.urlretrieve(src, dst)
        else:
            # ruta local relativa al HTML
            local = (base_dir / src).resolve()
            if local.exists():
                shutil.copy(local, dst)
            else:
                return None
        return f"assets/{fname}"
    except Exception as e:
        print(f"  ⚠ no pude copiar imagen {src}: {e}", file=sys.stderr)
        return None


def text_of(node) -> str:
    return " ".join(node.get_text(separator=" ", strip=True).split())


def slide_from_section(section, idx: int, base_dir: Path, assets_dir: Path,
                       images_collector: list[ImageRef]) -> Slide:
    sld = Slide(order=idx + 1, source_index=idx)

    title_node = section.find(["h1", "h2"])
    if title_node:
        sld.title = text_of(title_node)

    # subtítulos h3/h4 los unimos como subtitle
    sub = section.find(["h3", "h4"])
    if sub:
        sld.subtitle = text_of(sub)

    # bullets
    for li in section.find_all("li"):
        t = text_of(li)
        if t:
            sld.bullets.append(t)

    # paragraphs
    for p in section.find_all("p"):
        t = text_of(p)
        if t and t not in sld.bullets:
            sld.paragraphs.append(t)

    # tables
    for tbl in section.find_all("table"):
        rows = []
        for tr in tbl.find_all("tr"):
            row = [text_of(td) for td in tr.find_all(["td", "th"])]
            if row:
                rows.append(row)
        if rows:
            sld.tables.append(rows)

    # imágenes
    for img in section.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        copied = copy_image(src, base_dir, assets_dir)
        if copied:
            sld.images.append(copied)
            images_collector.append(ImageRef(
                path=copied, from_=f"section:{idx + 1}",
            ))

    return sld


def extract(input_path: Path, out_dir: Path) -> Manifest:
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    raw = input_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "lxml")

    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = ensure_assets_dir(out_dir)
    base_dir = input_path.parent

    manifest = Manifest(source_type="html", source_path=str(input_path))

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        desc = md["content"].strip()

    manifest.metadata = {
        "title": title,
        "subtitle": desc,
        "author": "",
        "language": soup.html.get("lang", "es") if soup.html else "es",
        "page_count": 0,
        "raw_metadata": {},
    }

    # secciones: <section> primero; si no hay, inferir por <h2>
    sections = soup.find_all("section")
    if not sections:
        # fallback: agrupar contenido por <h2>
        body = soup.body or soup
        chunks = []
        current = None
        for el in body.children:
            if getattr(el, "name", None) in ("h1", "h2"):
                if current is not None:
                    chunks.append(current)
                current = soup.new_tag("section")
                current.append(el)
            elif current is not None:
                current.append(el)
        if current is not None:
            chunks.append(current)
        sections = chunks

    for idx, sec in enumerate(sections):
        sld = slide_from_section(sec, idx, base_dir, assets_dir, manifest.images_extracted)
        manifest.slides.append(sld)

    manifest.metadata["page_count"] = len(manifest.slides)

    # links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(("http://", "https://")) and href not in manifest.links:
            manifest.links.append(href)

    return manifest


def main() -> int:
    p = argparse.ArgumentParser(description="Extrae .html → manifest.json + assets/")
    p.add_argument("input",  type=Path, help="archivo .html")
    p.add_argument("output", type=Path, help="carpeta destino")
    args = p.parse_args()

    print(f"📥 leyendo {args.input}")
    m = extract(args.input, args.output)
    out = m.save(args.output)
    print(f"✅ {len(m.slides)} secciones · {len(m.images_extracted)} imágenes · {len(m.links)} links")
    print(f"   manifest:    {out}")
    print(f"   assets:      {args.output / 'assets'}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
