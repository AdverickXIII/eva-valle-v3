"""
Orquestador del Paso 4: Analisis Descriptivo Profundo.

Migrado del Notebook 4 (funcion ejecutar_paso4).
Mejoras:
- Sin prints (solo logging)
- Configuracion desde config.settings
- Usa adaptadores de storage (CsvStorage)
- Retorna dict de artefactos en vez de imprimir
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.analytics.concentration import calculate_concentration
from core.analytics.descriptive import calculate_descriptive_statistics
from core.analytics.distributions import fit_distributions
from core.analytics.elasticity import calculate_elasticity
from core.analytics.ex_cana import analyze_ex_cana
from core.analytics.growth import calculate_cagr
from core.analytics.inferential import run_inferential_test
from core.analytics.outliers import detect_multivariate_outliers
from core.analytics.seasonality import test_seasonality_ab
from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity
from core.analytics.time_series import analyze_time_series
from core.logging import get_logger, log_section

log = get_logger("core.analytics.pipeline")

_csv_storage = CsvStorage()


def run_all_analytics(
    input_path: Path | None = None,
    export_artifacts: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta los 12 analisis descriptivos del Paso 4.

    Args:
        input_path: Ruta al CSV con modelo conceptual. Si es None, usa
            la ruta por defecto.
        export_artifacts: Si True, exporta los artefactos a CSV.

    Returns:
        Diccionario con los 12 artefactos generados.

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
    """
    log_section("PASO 4 - ANALISIS DESCRIPTIVO PROFUNDO")

    if input_path is None:
        input_path = (
            settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
        )

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d registros", len(df))

    artefactos: dict[str, Any] = {}

    # 4.3 Estadistica descriptiva profunda
    log.info("Ejecutando 4.3 Estadistica descriptiva...")
    artefactos["4_3_descriptiva_profunda"] = calculate_descriptive_statistics(df)

    # 4.4 Ajuste de distribuciones
    log.info("Ejecutando 4.4 Ajuste de distribuciones...")
    artefactos["4_4_ajuste_distribuciones"] = fit_distributions(df)

    # 4.5 Outliers multivariados
    log.info("Ejecutando 4.5 Outliers multivariados...")
    artefactos["4_5_outliers_multivariados"] = detect_multivariate_outliers(df)

    # 4.6 Concentracion (GINI CORREGIDO)
    log.info("Ejecutando 4.6 Concentracion (Gini corregido)...")
    conc = calculate_concentration(df)
    artefactos["4_6_concentracion"] = pd.DataFrame([conc])

    # 4.7 Series de tiempo
    log.info("Ejecutando 4.7 Series de tiempo...")
    artefactos["4_7_series_tiempo"] = analyze_time_series(df)

    # 4.8 Estacionalidad A vs B
    log.info("Ejecutando 4.8 Estacionalidad A vs B...")
    artefactos["4_8_estacionalidad_ab"] = test_seasonality_ab(df)

    # 4.9 Location Quotient
    log.info("Ejecutando 4.9 Location Quotient...")
    artefactos["4_9_location_quotient"] = calculate_location_quotient(df)

    # 4.10 Shannon-Wiener
    log.info("Ejecutando 4.10 Shannon-Wiener...")
    artefactos["4_10_shannon_wiener"] = calculate_shannon_diversity(df)

    # 4.11 Elasticidades
    log.info("Ejecutando 4.11 Elasticidades...")
    elasticidad = calculate_elasticity(df)
    artefactos["4_11_elasticidades"] = pd.DataFrame([elasticidad])

    # 4.12 Inferencial
    log.info("Ejecutando 4.12 Kruskal-Wallis...")
    artefactos["4_12_inferencial"] = run_inferential_test(df)

    # 4.13 CAGR
    log.info("Ejecutando 4.13 CAGR...")
    artefactos["4_13_cagr_cultivos"] = calculate_cagr(df)

    # 4.14 Ex-Cana
    log.info("Ejecutando 4.14 Ex-Cana...")
    ex_cana = analyze_ex_cana(df)
    artefactos["4_14_ex_cana"] = pd.DataFrame([ex_cana])

    # Exportar artefactos
    if export_artifacts:
        log.info("Exportando %d artefactos...", len(artefactos))
        for nombre, df_art in artefactos.items():
            if isinstance(df_art, pd.DataFrame) and not df_art.empty:
                ruta = settings.OUTPUTS_TABLES_PATH / f"{nombre}.csv"
                _csv_storage.write_csv(df_art, ruta)

    log.info("Paso 4 completado. %d artefactos generados.", len(artefactos))
    return artefactos
