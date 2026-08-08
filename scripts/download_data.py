#!/usr/bin/env python
"""
Script CLI para descargar las bases de datos de UPRA (Paso 0).

Uso:
    python scripts/download_data.py
    python scripts/download_data.py --force
    python scripts/download_data.py --file agricola
    python scripts/download_data.py --headless false

Este script usa el adaptador UpraDownloader para descargar las bases
Agricola y Pecuaria del portal EVA de la UPRA.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent.parent))


import argparse
import sys

from adapters.downloader.upra_downloader import UpraDownloader
from config.settings import settings
from core.logging import get_logger, log_section

log = get_logger("scripts.download_data")


def parse_args() -> argparse.Namespace:
    """Parsea argumentos de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Descarga las bases de datos de UPRA (Paso 0).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python scripts/download_data.py\n"
            "  python scripts/download_data.py --force\n"
            "  python scripts/download_data.py --file agricola\n"
        ),
    )
    parser.add_argument(
        "--file",
        type=str,
        choices=["agricola", "pecuario", "ambos"],
        default="ambos",
        help="Archivo a descargar (default: ambos).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar re-descarga aunque el checksum sea igual.",
    )
    parser.add_argument(
        "--headless",
        type=str,
        choices=["true", "false"],
        default="true",
        help="Ejecutar navegador en modo headless (default: true).",
    )
    return parser.parse_args()


def main() -> int:
    """Punto de entrada principal."""
    args = parse_args()
    log_section("PASO 0 - DESCARGA DE DATOS UPRA")

    try:
        downloader = UpraDownloader(force_redownload=args.force)
        headless = args.headless.lower() == "true"

        if args.file == "ambos":
            files_to_download = ["agricola", "pecuario"]
        else:
            files_to_download = [args.file]

        log.info("Descargando archivos: %s", files_to_download)
        for file_key in files_to_download:
            try:
                filepath = downloader.download(file_key, force=args.force)
                log.info("Descarga exitosa: %s", filepath)
            except Exception as e:
                log.error("Fallo al descargar %s: %s", file_key, e)
                return 1

        log.info("Descargas completadas exitosamente.")
        return 0

    except Exception as e:
        log.error("Error fatal: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
