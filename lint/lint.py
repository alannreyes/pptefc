#!/usr/bin/env python3
"""
EFC Deck — Linter anti-fricción.

Uso:
    python3 lint.py /path/to/deck.html [...]
    python3 lint.py --check-all /path/to/decks/

Salida:
    - Exit 0 si no hay bloqueadores.
    - Exit 1 si hay severidad 'block'.
    - Imprime hallazgos con severidad, term, sugerencia, línea.

Lee `forbidden-terms.json` (mismo directorio que este script).
Insensible a mayúsculas por defecto (a menos que la entrada diga case_sensitive=true).
Soporta regex con regex=true.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RULES_PATH = SCRIPT_DIR / "forbidden-terms.json"

# ANSI colors for terminal output
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def load_rules() -> dict:
    with RULES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def strip_html_to_text_lines(html: str) -> list[str]:
    """Quita el HTML pero conserva la estructura por líneas para reportar línea."""
    # En decks self-contained el CSS/JS va embebido en <style>/<script>: vaciamos su
    # contenido (conservando el nº de líneas) para NO escanear código como si fuera texto
    # visible (evita falsos positivos tipo «agl» dentro de una regla CSS).
    def _blank(m):
        return "\n" * m.group(0).count("\n")
    html = re.sub(r"<style\b[^>]*>.*?</style>", _blank, html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script\b[^>]*>.*?</script>", _blank, html, flags=re.DOTALL | re.IGNORECASE)
    # Sin parser DOM serio: removemos tags pero preservamos saltos de línea
    text_per_line = []
    for line in html.splitlines():
        # remover tags
        text = re.sub(r"<[^>]+>", " ", line)
        # decode entidades comunes
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
        text_per_line.append(text)
    return text_per_line


def lint_file(path: Path, rules: dict) -> tuple[int, int]:
    """Returns (block_count, warn_count)."""
    if not path.exists():
        print(f"{RED}✗ no existe: {path}{RESET}")
        return (0, 0)

    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = strip_html_to_text_lines(raw)
    block_count = 0
    warn_count = 0

    print(f"\n{BOLD}{CYAN}── {path}{RESET}")

    for category, entries in rules.items():
        if category.startswith("_"):
            continue
        for entry in entries:
            term = entry["term"]
            severity = entry.get("severity", "warn")
            is_regex = entry.get("regex", False)
            case_sensitive = entry.get("case_sensitive", False)
            reason = entry.get("reason", "")
            suggestion = entry.get("suggestion", "")

            flags = 0 if case_sensitive else re.IGNORECASE
            # Acrónimos cortos (agl, dem, ppk…) deben matchear como PALABRA completa,
            # no como substring dentro de otra (p.ej. «dem» en «demostrativo»).
            if is_regex:
                pat = term
            elif re.fullmatch(r"[A-Za-z]{2,5}", term):
                pat = r"\b" + re.escape(term) + r"\b"
            else:
                pat = re.escape(term)
            try:
                pattern = re.compile(pat, flags)
            except re.error as e:
                print(f"{YELLOW}  [warn] regex inválida en categoría {category}: {term} ({e}){RESET}")
                continue

            hits = []
            for lineno, line in enumerate(lines, 1):
                for m in pattern.finditer(line):
                    hits.append((lineno, m.group(0), line.strip()[:120]))

            if not hits:
                continue

            if severity == "block":
                block_count += len(hits)
                color = RED
                icon = "✗"
                tag = "BLOCK"
            else:
                warn_count += len(hits)
                color = YELLOW
                icon = "⚠"
                tag = "WARN "

            for lineno, matched, line_excerpt in hits:
                print(f"  {color}{icon} [{tag}]{RESET} línea {lineno}  {DIM}{category}{RESET}")
                print(f"      término: {BOLD}«{matched}»{RESET}")
                print(f"      razón:   {reason}")
                if suggestion:
                    print(f"      → {GREEN}{suggestion}{RESET}")
                print(f"      contexto: {DIM}{line_excerpt}{RESET}\n")

    return (block_count, warn_count)


def main() -> int:
    parser = argparse.ArgumentParser(description="EFC Deck/Guide linter")
    parser.add_argument("paths", nargs="+", help="Archivo HTML o carpeta")
    parser.add_argument("--check-all", action="store_true", help="Si la ruta es carpeta, revisar todos los .html dentro")
    parser.add_argument("--mode", choices=["deck", "guide", "interno"], default="deck",
                        help="deck    = comercial a cliente C-level (estricto, jerga = block); "
                             "guide   = guía panorámica técnica con glosario (jerga = warn); "
                             "interno = audiencia interna EFC (resumen ejecutivo, status, "
                             "capacitación) — jerga interna ok, sin reglas comerciales")
    args = parser.parse_args()

    rules = load_rules()

    # En modo 'guide': jerga técnica downgradeada a warn (asume glosario al final).
    if args.mode == "guide":
        for entry in rules.get("jerga_sin_aclarar", []):
            if entry.get("severity") == "block":
                entry["severity"] = "warn"
        print(f"\033[36m[modo guide]\033[0m jerga técnica downgradeada a warn (asume glosario)")

    # En modo 'interno': audiencia EFC interna conoce la jerga, y reglas
    # comerciales (asumir flota, comparar marcas peyorativas, fricción cierre)
    # NO aplican porque no hay cliente externo.
    if args.mode == "interno":
        # Jerga: warn (interno la entiende)
        for entry in rules.get("jerga_sin_aclarar", []):
            if entry.get("severity") == "block":
                entry["severity"] = "warn"
        # Categorías comerciales: bajar a warn o eliminar
        for cat in ("asume_inventario_cliente", "comparacion_peyorativa_marcas",
                    "compromisos_no_factibles", "friccion_en_cierre"):
            for entry in rules.get(cat, []):
                if entry.get("severity") == "block":
                    entry["severity"] = "warn"
        print(f"\033[36m[modo interno]\033[0m jerga + reglas comerciales downgradeadas a warn")

    total_block = 0
    total_warn = 0
    files_checked = 0

    for raw_path in args.paths:
        p = Path(raw_path)
        if p.is_dir():
            html_files = sorted(p.rglob("*.html"))
            if not html_files:
                print(f"{YELLOW}sin .html en {p}{RESET}")
                continue
            for f in html_files:
                blk, wrn = lint_file(f, rules)
                total_block += blk
                total_warn += wrn
                files_checked += 1
        else:
            blk, wrn = lint_file(p, rules)
            total_block += blk
            total_warn += wrn
            files_checked += 1

    print(f"\n{BOLD}── Resumen ──{RESET}")
    print(f"  archivos:  {files_checked}")
    print(f"  bloqueos:  {RED if total_block else GREEN}{total_block}{RESET}")
    print(f"  warnings:  {YELLOW if total_warn else GREEN}{total_warn}{RESET}")

    if total_block > 0:
        print(f"\n{RED}✗ El deck NO está listo para publicar. Resolver los {total_block} bloqueos antes.{RESET}")
        return 1
    elif total_warn > 0:
        print(f"\n{YELLOW}⚠ Sin bloqueos, pero hay {total_warn} warnings. Revisar con criterio antes de publicar.{RESET}")
        return 0
    else:
        print(f"\n{GREEN}✓ Limpio. Listo para publicar.{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
