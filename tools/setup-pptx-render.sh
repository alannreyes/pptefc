#!/usr/bin/env bash
# Setup (una sola vez) para render_pptx.py — ver un .pptx como imágenes sin LibreOffice.
# Crea un venv en ~/.pptefc-venv con aspose.slides e instala mono-libgdiplus (GDI+).
set -e

VENV="${PPTEFC_VENV:-$HOME/.pptefc-venv}"

echo "▸ libgdiplus (GDI+ para rasterizar) …"
if ! brew --prefix mono-libgdiplus >/dev/null 2>&1; then
  brew install mono-libgdiplus
else
  echo "  ya instalado: $(brew --prefix mono-libgdiplus)"
fi

# aspose.slides NO tiene wheel para Python 3.14 → preferir 3.13 / 3.12 / 3.11
PY=""
for v in python3.13 python3.12 python3.11; do
  if command -v "$v" >/dev/null 2>&1; then PY="$v"; break; fi
done
[ -z "$PY" ] && PY="python3"
echo "▸ venv en $VENV (con $PY) …"
[ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"

echo "▸ aspose.slides …"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet aspose.slides

echo "▸ verificación …"
"$VENV/bin/python" -c "import aspose.slides; print('  aspose OK')"

echo ""
echo "✓ Listo. Para ver un pptx:"
echo "   $VENV/bin/python extractors/render_pptx.py archivo.pptx --sheet"
