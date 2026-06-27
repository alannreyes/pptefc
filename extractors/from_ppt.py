#!/usr/bin/env python3
"""
Extrae .ppt (Office <= 2003). Como python-pptx no soporta .ppt, primero lo
convertimos a .pptx con LibreOffice headless y delegamos a from_pptx.

Requisitos:
  - LibreOffice instalado:
      macOS:  brew install --cask libreoffice
      Linux:  apt install libreoffice
  - python-pptx (vía from_pptx)

Uso:
    python3 from_ppt.py input.ppt output_dir/
"""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import Manifest


def find_soffice() -> str | None:
    for cmd in ("soffice", "libreoffice"):
        if shutil.which(cmd):
            return cmd
    candidates = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def ppt_to_pptx(ppt_path: Path) -> Path:
    """Convierte .ppt → .pptx usando LibreOffice headless. Devuelve la ruta del .pptx generado."""
    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(
            "No encuentro LibreOffice. Instálalo con:\n"
            "  macOS:  brew install --cask libreoffice\n"
            "  Linux:  sudo apt install libreoffice\n"
            "O abrir el archivo .ppt en PowerPoint y guardar como .pptx manualmente."
        )

    tmp = Path(tempfile.mkdtemp(prefix="efcdeck_ppt2pptx_"))
    cmd = [soffice, "--headless", "--convert-to", "pptx", "--outdir", str(tmp), str(ppt_path)]
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice falló:\n{result.stderr}")
    out = tmp / (ppt_path.stem + ".pptx")
    if not out.exists():
        raise RuntimeError(f"No se generó {out}\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Extrae .ppt → manifest.json + assets/")
    p.add_argument("input",  type=Path, help="archivo .ppt")
    p.add_argument("output", type=Path, help="carpeta destino")
    args = p.parse_args()

    if not args.input.exists():
        print(f"ERROR: no existe {args.input}", file=sys.stderr)
        return 2

    # Convertir .ppt → .pptx
    print(f"📥 convirtiendo {args.input} a .pptx con LibreOffice...")
    try:
        pptx_path = ppt_to_pptx(args.input)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    print(f"  ✓ generado: {pptx_path}")

    # Delegar a from_pptx (importamos su función, no re-shell)
    from from_pptx import extract as extract_pptx
    m = extract_pptx(pptx_path, args.output)

    # Sobrescribir el source_type a 'ppt' (no 'pptx') porque el original era .ppt
    m.source_type = "ppt"
    m.source_path = str(args.input)
    out = m.save(args.output)
    print(f"✅ {len(m.slides)} slides · {len(m.images_extracted)} imágenes")
    print(f"   manifest:    {out}")
    print(f"   assets:      {args.output / 'assets'}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
