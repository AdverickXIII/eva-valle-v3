#!/usr/bin/env python
"""
Script CLI para ejecutar solo la auditoria tecnica (Paso 2).

Uso:
    python scripts/run_audit.py
    python scripts/run_audit.py --output-dir outputs/reports

Este script ejecuta las 8 auditorias del Paso 2 sobre el dataset
estandarizado y genera el reporte consolidado.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent.parent))


import argparse
import sys

from config.settings import settings
from core.logging import get_logger, log_section

log = get_logger("scripts.run_audit")


def parse_args() -> argparse.Namespace:
    """Parsea argumentos de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Ejecuta la auditoria tecnica del Paso 2.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio de salida del reporte (default: outputs/tables/).",
    )
    return parser.parse_args()


def main() -> int:
    """Punto de entrada principal."""
    args = parse_args()
    log_section("PASO 2 - AUDITORIA TECNICA PROFUNDA")

    try:
        from core.audit.loader import load_and_standardize
        from core.audit import run_all_audits
        from core.audit.report import generate_audit_report

        # Cargar dataset
        log.info("Cargando dataset estandarizado...")
        df_valle, mapeo = load_and_standardize()
        log.info("Dataset cargado: %d registros", len(df_valle))

        # Ejecutar auditorias
        log.info("Ejecutando 8 auditorias...")
        findings = run_all_audits(df_valle)
        log.info("Auditorias completadas: %d hallazgos", len(findings))

        # Generar reporte
        log.info("Generando reporte consolidado...")
        df_report = generate_audit_report(findings)

        # Resumen por severidad
        for sev in ["ERROR", "ADVERTENCIA", "INFO"]:
            n = len([f for f in findings if f.severidad == sev])
            log.info("[%s]: %d hallazgo(s)", sev, n)

        log.info("Auditoria completada exitosamente.")
        return 0

    except Exception as e:
        log.error("Error fatal: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
