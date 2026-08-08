"""
Orquestador del Paso 6: Analisis Diagnostico.

Migrado del Notebook 6 (funcion ejecutar_paso6).
Mejoras:
- Sin prints (solo logging)
- Separacion calculo / visualizacion
- Configuracion desde config.settings
- Usa adaptadores de storage (CsvStorage)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.diagnostics.comparison import compare_cycles
from core.diagnostics.correlation import calculate_bivariate_stats, calculate_correlation_matrix
from core.diagnostics.root_cause import find_root_causes
from core.diagnostics.segmentation import segment_municipalities
from core.diagnostics.shock import analyze_shock
from core.logging import get_logger, log_section

log = get_logger("core.diagnostics.pipeline")

_csv_storage = CsvStorage()


def run_all_diagnostics(
    input_path: Path | None = None,
    export_artifacts: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta los 5 analisis diagnosticos del Paso 6.

    Args:
        input_path: Ruta al CSV con modelo conceptual. Si es None, usa
            la ruta por defecto.
        export_artifacts: Si True, exporta los artefactos a CSV.

    Returns:
        Diccionario con los 5 artefactos generados.

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
    """
    log_section("PASO 6 - ANALISIS DIAGNOSTICO (POR QUE OCURRIO?)")

    if input_path is None:
        input_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d registros", len(df))

    artefactos: dict[str, Any] = {}

    # 6.1 Correlacion
    log.info("Ejecutando 6.1 Correlacion y estadisticas bivariadas...")
    artefactos["6_1_matriz_correlacion"] = calculate_correlation_matrix(df)
    artefactos["6_1_bivariadas"] = calculate_bivariate_stats(df)

    # 6.2 Comparacion de ciclos
    log.info("Ejecutando 6.2 Comparacion Transitorio vs Permanente...")
    comparacion = compare_cycles(df)
    artefactos["6_2_comparacion_ciclos"] = pd.DataFrame([comparacion])

    # 6.3 Segmentacion de municipios
    log.info("Ejecutando 6.3 Segmentacion territorial (K-Means)...")
    segmentacion = segment_municipalities(df)
    if "error" not in segmentacion:
        artefactos["6_3_perfiles_municipios"] = segmentacion["df_clusters"]
        artefactos["6_3_silhouette_scores"] = pd.DataFrame(
            segmentacion["silhouette_scores"], columns=["k", "silhouette_score"]
        )
    else:
        artefactos["6_3_error"] = segmentacion["error"]

    # 6.4 Arbol de causa raiz
    log.info("Ejecutando 6.4 Arbol de causa raiz...")
    causa_raiz = find_root_causes(df)
    if "error" not in causa_raiz:
        artefactos["6_4_importancia_variables"] = causa_raiz["importancia_df"]
    else:
        artefactos["6_4_error"] = causa_raiz["error"]

    # 6.5 Shock exogeno
    log.info("Ejecutando 6.5 Analisis del shock 2020...")
    shock = analyze_shock(df)
    if "error" not in shock:
        artefactos["6_5_variacion_shock_2020"] = shock["df_historico"]
        artefactos["6_5_impacto_shock"] = pd.DataFrame([shock["impacto_shock"]])
    else:
        artefactos["6_5_error"] = shock["error"]

    # Exportar artefactos
    if export_artifacts:
        log.info("Exportando %d artefactos...", len(artefactos))
        for nombre, df_art in artefactos.items():
            if isinstance(df_art, pd.DataFrame) and not df_art.empty:
                ruta = settings.OUTPUTS_TABLES_PATH / f"{nombre}.csv"
                _csv_storage.write_csv(df_art, ruta)

    log.info("Paso 6 completado. %d artefactos generados.", len(artefactos))
    return artefactos
