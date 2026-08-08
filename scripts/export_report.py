#!/usr/bin/env python
"""
Script CLI para generar un reporte HTML consolidado de todos los artefactos.

Uso:
    python scripts/export_report.py
    python scripts/export_report.py --output outputs/reports/eva_valle_report.html

Este script lee todos los artefactos CSV generados por el pipeline
y genera un reporte HTML consolidado con resumen ejecutivo.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent.parent))


import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import settings
from core.logging import get_logger, log_section

log = get_logger("scripts.export_report")


def parse_args() -> argparse.Namespace:
    """Parsea argumentos de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Genera reporte HTML consolidado.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta de salida del HTML (default: outputs/reports/eva_valle_report.html).",
    )
    return parser.parse_args()


def generate_html_report(artefactos: dict[str, pd.DataFrame], output_path: Path) -> None:
    """Genera el reporte HTML consolidado."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '  <meta charset="utf-8">',
        "  <title>EVA Valle del Cauca - Reporte Consolidado</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 40px; }",
        "    h1 { color: #2E8B57; }",
        "    h2 { color: #1A1F2E; border-bottom: 2px solid #2E8B57; }",
        "    table { border-collapse: collapse; width: 100%; margin: 10px 0; }",
        "    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "    th { background-color: #2E8B57; color: white; }",
        "    tr:nth-child(even) { background-color: #f2f2f2; }",
        "  </style>",
        "</head>",
        "<body>",
        f"  <h1>EVA Valle del Cauca - Reporte Consolidado</h1>",
        f"  <p>Generado: {timestamp}</p>",
        f"  <p>Artefactos incluidos: {len(artefactos)}</p>",
    ]

    for nombre, df_art in artefactos.items():
        html_parts.append(f"  <h2>{nombre}</h2>")
        if df_art.empty:
            html_parts.append("  <p>Sin datos disponibles.</p>")
        else:
            html_parts.append(df_art.to_html(index=False, border=0))

    html_parts.extend(["</body>", "</html>"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(html_parts), encoding="utf-8")
    log.info("Reporte HTML generado: %s", output_path)


def main() -> int:
    """Punto de entrada principal."""
    args = parse_args()
    log_section("GENERACION DE REPORTE CONSOLIDADO")

    try:
        # Leer todos los artefactos CSV
        log.info("Leyendo artefactos desde %s...", settings.OUTPUTS_TABLES_PATH)
        artefactos: dict[str, pd.DataFrame] = {}

        for csv_file in sorted(settings.OUTPUTS_TABLES_PATH.glob("*.csv")):
            try:
                df = pd.read_csv(csv_file, encoding="utf-8-sig")
                artefactos[csv_file.stem] = df
                log.info("Leido: %s (%d filas)", csv_file.name, len(df))
            except Exception as e:
                log.warning("No se pudo leer %s: %s", csv_file.name, e)

        if not artefactos:
            log.warning("No se encontraron artefactos CSV. Ejecute el pipeline primero.")
            return 0

        # Generar HTML
        output_path = Path(args.output) if args.output else (
            settings.OUTPUTS_REPORTS_PATH / "eva_valle_report.html"
        )
        generate_html_report(artefactos, output_path)

        log.info("Reporte generado exitosamente.")
        return 0

    except Exception as e:
        log.error("Error fatal: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
