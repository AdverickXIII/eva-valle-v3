#!/usr/bin/env python
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
import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path para que los imports funcionen
sys.path.insert(0, str(Path(__file__).parent.parent))


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
            "Ejemplos:\n"
            "  python scripts/run_pipeline.py\n"
            "  python scripts/run_pipeline.py --skip-download\n"
            "  python scripts/run_pipeline.py --only-analytics\n"
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
        from config.settings import settings
        df_modelo, artefactos = run_conceptual_modeling()
        # Guardar el CSV del modelo conceptual (requerido por Pasos 4, 6, 7)
        ruta = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        df_modelo.to_csv(ruta, index=False, encoding="utf-8-sig")
        log.info("Paso 3 completado: %d registros. Guardado: %s", len(df_modelo), ruta.name)
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
