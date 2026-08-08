"""
Setup script: genera los 4 scripts CLI del proyecto.
Ejecutar una sola vez: python scripts/setup_scripts_cli.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: scripts/download_data.py
# ═══════════════════════════════════════════════════════════
DOWNLOAD_DATA = '''#!/usr/bin/env python
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
            "Ejemplos:\\n"
            "  python scripts/download_data.py\\n"
            "  python scripts/download_data.py --force\\n"
            "  python scripts/download_data.py --file agricola\\n"
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: scripts/run_pipeline.py
# ═══════════════════════════════════════════════════════════
RUN_PIPELINE = '''#!/usr/bin/env python
"""
Script CLI para ejecutar el pipeline completo de EVA Valle (Pasos 1-7).

Uso:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --skip-download
    python scripts/run_pipeline.py --only-analytics
    python scripts/run_pipeline.py --persist-models false

Este script orquesta todos los pasos del pipeline:
- Paso 1: Carga y Estandarizacion
- Paso 2: Auditoria Tecnica
- Paso 3: Modelado Conceptual
- Paso 4: Analisis Descriptivo
- Paso 5: (Visualizaciones se generan en Streamlit, no aqui)
- Paso 6: Analisis Diagnostico
- Paso 7: Analisis Predictivo
"""
from __future__ import annotations

import argparse
import sys

from config.settings import settings
from core.logging import get_logger, log_section

log = get_logger("scripts.run_pipeline")


def parse_args() -> argparse.Namespace:
    """Parsea argumentos de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline completo de EVA Valle (Pasos 1-7).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\\n"
            "  python scripts/run_pipeline.py\\n"
            "  python scripts/run_pipeline.py --skip-download\\n"
            "  python scripts/run_pipeline.py --only-analytics\\n"
        ),
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Saltar el Paso 0 (descarga). Asume que los datos ya existen.",
    )
    parser.add_argument(
        "--only-analytics",
        action="store_true",
        help="Ejecutar solo los Pasos 4, 6 y 7 (analisis).",
    )
    parser.add_argument(
        "--persist-models",
        type=str,
        choices=["true", "false"],
        default="true",
        help="Persistir modelos ML con joblib (default: true).",
    )
    return parser.parse_args()


def run_step_0_download() -> bool:
    """Ejecuta el Paso 0: Descarga de datos de UPRA."""
    log_section("PASO 0 - DESCARGA DE DATOS UPRA")
    try:
        from adapters.downloader.upra_downloader import UpraDownloader
        downloader = UpraDownloader()
        for file_key in ["agricola", "pecuario"]:
            try:
                filepath = downloader.download(file_key)
                log.info("Descarga exitosa: %s", filepath)
            except Exception as e:
                log.warning("Fallo al descargar %s: %s. Continuando...", file_key, e)
        return True
    except Exception as e:
        log.error("Error en Paso 0: %s", e)
        return False


def run_step_1_load() -> bool:
    """Ejecuta el Paso 1: Carga y Estandarizacion."""
    log_section("PASO 1 - CARGA Y ESTANDARIZACION")
    try:
        from core.audit.loader import load_and_standardize
        df_valle, mapeo = load_and_standardize()
        log.info("Paso 1 completado: %d registros", len(df_valle))
        return True
    except Exception as e:
        log.error("Error en Paso 1: %s", e)
        return False


def run_step_2_audit() -> bool:
    """Ejecuta el Paso 2: Auditoria Tecnica."""
    log_section("PASO 2 - AUDITORIA TECNICA")
    try:
        from core.audit import load_and_standardize, run_all_audits, generate_audit_report
        df_valle, _ = load_and_standardize()
        findings = run_all_audits(df_valle)
        df_report = generate_audit_report(findings)
        log.info("Paso 2 completado: %d hallazgos", len(findings))
        return True
    except Exception as e:
        log.error("Error en Paso 2: %s", e)
        return False


def run_step_3_modeling() -> bool:
    """Ejecuta el Paso 3: Modelado Conceptual."""
    log_section("PASO 3 - MODELADO CONCEPTUAL")
    try:
        from core.modeling import run_conceptual_modeling
        df_modelo, artefactos = run_conceptual_modeling()
        log.info("Paso 3 completado: %d registros", len(df_modelo))
        return True
    except Exception as e:
        log.error("Error en Paso 3: %s", e)
        return False


def run_step_4_analytics() -> bool:
    """Ejecuta el Paso 4: Analisis Descriptivo."""
    log_section("PASO 4 - ANALISIS DESCRIPTIVO")
    try:
        from core.analytics import run_all_analytics
        artefactos = run_all_analytics()
        log.info("Paso 4 completado: %d artefactos", len(artefactos))
        return True
    except Exception as e:
        log.error("Error en Paso 4: %s", e)
        return False


def run_step_6_diagnostics() -> bool:
    """Ejecuta el Paso 6: Analisis Diagnostico."""
    log_section("PASO 6 - ANALISIS DIAGNOSTICO")
    try:
        from core.diagnostics import run_all_diagnostics
        artefactos = run_all_diagnostics()
        log.info("Paso 6 completado: %d artefactos", len(artefactos))
        return True
    except Exception as e:
        log.error("Error en Paso 6: %s", e)
        return False


def run_step_7_ml(persist_models: bool = True) -> bool:
    """Ejecuta el Paso 7: Analisis Predictivo."""
    log_section("PASO 7 - ANALISIS PREDICTIVO")
    try:
        from core.ml import run_all_ml
        artefactos = run_all_ml(persist_models=persist_models)
        log.info("Paso 7 completado: %d artefactos", len(artefactos))
        return True
    except Exception as e:
        log.error("Error en Paso 7: %s", e)
        return False


def main() -> int:
    """Punto de entrada principal."""
    args = parse_args()
    log_section("PIPELINE COMPLETO - EVA VALLE DEL CAUCA")

    persist_models = args.persist_models.lower() == "true"

    if args.only_analytics:
        # Solo ejecutar Pasos 4, 6 y 7
        steps = [
            ("Paso 4", run_step_4_analytics, {}),
            ("Paso 6", run_step_6_diagnostics, {}),
            ("Paso 7", run_step_7_ml, {"persist_models": persist_models}),
        ]
    else:
        # Pipeline completo
        steps = []
        if not args.skip_download:
            steps.append(("Paso 0", run_step_0_download, {}))
        steps.extend([
            ("Paso 1", run_step_1_load, {}),
            ("Paso 2", run_step_2_audit, {}),
            ("Paso 3", run_step_3_modeling, {}),
            ("Paso 4", run_step_4_analytics, {}),
            ("Paso 6", run_step_6_diagnostics, {}),
            ("Paso 7", run_step_7_ml, {"persist_models": persist_models}),
        ])

    failed_steps = []
    for step_name, step_func, kwargs in steps:
        try:
            success = step_func(**kwargs)
            if not success:
                failed_steps.append(step_name)
        except Exception as e:
            log.error("%s fallo con excepcion: %s", step_name, e)
            failed_steps.append(step_name)

    if failed_steps:
        log.error("Pipeline completado con errores en: %s", failed_steps)
        return 1
    else:
        log.info("Pipeline completado exitosamente.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: scripts/run_audit.py
# ═══════════════════════════════════════════════════════════
RUN_AUDIT = '''#!/usr/bin/env python
"""
Script CLI para ejecutar solo la auditoria tecnica (Paso 2).

Uso:
    python scripts/run_audit.py
    python scripts/run_audit.py --output-dir outputs/reports

Este script ejecuta las 8 auditorias del Paso 2 sobre el dataset
estandarizado y genera el reporte consolidado.
"""
from __future__ import annotations

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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: scripts/export_report.py
# ═══════════════════════════════════════════════════════════
EXPORT_REPORT = '''#!/usr/bin/env python
"""
Script CLI para generar un reporte HTML consolidado de todos los artefactos.

Uso:
    python scripts/export_report.py
    python scripts/export_report.py --output outputs/reports/eva_valle_report.html

Este script lee todos los artefactos CSV generados por el pipeline
y genera un reporte HTML consolidado con resumen ejecutivo.
"""
from __future__ import annotations

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
    output_path.write_text("\\n".join(html_parts), encoding="utf-8")
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
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "scripts/download_data.py": DOWNLOAD_DATA,
        "scripts/run_pipeline.py": RUN_PIPELINE,
        "scripts/run_audit.py": RUN_AUDIT,
        "scripts/export_report.py": EXPORT_REPORT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} scripts CLI creados.")
    print('Ejecuta: python scripts\\run_pipeline.py --help')