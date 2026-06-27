"""
EFC Deck Extractors — esquema común del manifest.

Todos los extractores (HTML, PDF, PPTX, PPT) producen el MISMO esquema JSON,
para que el flujo aguas abajo (Claude → plantilla → deck.html) sea uniforme.

Manifest schema:
{
  "source": {
    "type": "pptx" | "pdf" | "html" | "ppt" | "md",
    "path": "ruta original",
    "extracted_at": "ISO timestamp",
    "extractor_version": "0.1.0"
  },
  "metadata": {
    "title": "Título inferido (si lo hay)",
    "subtitle": "...",
    "author": "...",
    "language": "es" | "en",
    "page_count": 12,
    "raw_metadata": { ... }   # metadata específica del formato
  },
  "slides": [
    {
      "order": 1,
      "title": "Título del slide o sección",
      "subtitle": "...",
      "bullets": ["línea 1", "línea 2"],
      "paragraphs": ["bloque continuo de texto"],
      "tables": [ [["h1","h2"],["v1","v2"]], ... ],
      "images": ["assets/img-001.png", "assets/img-002.jpg"],
      "notes": "Notas del orador (si aplica)",
      "source_index": 0   # índice original en el archivo (slide N o página N)
    }
  ],
  "images_extracted": [
    {"path": "assets/img-001.png", "width": 1920, "height": 1080, "from": "slide:1"}
  ],
  "links": ["https://...", "..."]
}

El "manifest.json" se guarda junto a la carpeta de assets extraídos:

  out_dir/
    manifest.json
    assets/
      img-001.png
      img-002.jpg
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

EXTRACTOR_VERSION = "0.1.0"


@dataclass
class Slide:
    order: int
    title: str = ""
    subtitle: str = ""
    bullets: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    notes: str = ""
    source_index: int = 0


@dataclass
class ImageRef:
    path: str
    width: int = 0
    height: int = 0
    from_: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "from": self.from_,
        }


@dataclass
class Manifest:
    source_type: str
    source_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    slides: list[Slide] = field(default_factory=list)
    images_extracted: list[ImageRef] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": {
                "type": self.source_type,
                "path": self.source_path,
                "extracted_at": self.extracted_at,
                "extractor_version": EXTRACTOR_VERSION,
            },
            "metadata": self.metadata,
            "slides": [asdict(s) for s in self.slides],
            "images_extracted": [i.to_json() for i in self.images_extracted],
            "links": self.links,
        }

    def save(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "manifest.json"
        with out.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return out


def ensure_assets_dir(out_dir: Path) -> Path:
    """Crea (si no existe) y devuelve la carpeta de assets dentro de out_dir."""
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    return assets


def safe_filename(name: str) -> str:
    """Sanea un nombre para que sirva de filename."""
    import re
    name = re.sub(r"[^\w\.-]", "_", name)
    return name[:80] or "asset"
