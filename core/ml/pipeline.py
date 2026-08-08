"""
Orquestador del Paso 7: Analisis Predictivo.

Migrado del Notebook 7 (funcion ejecutar_paso7).
Mejoras:
- Sin prints (solo logging)
- Target encoding sin data leakage (fit solo con train)
- Persistencia de modelos con JoblibModelRegistry
- Configuracion desde config.settings
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.logging import get_logger, log_section
from core.ml.classification import train_classification
from core.ml.features import create_features_ml
from core.ml.forecasting import forecast_time_series
from core.ml.regression import train_regression
from core.ml.target_encoding import apply_target_encoding, fit_target_encoding

log = get_logger("core.ml.pipeline")

_csv_storage = CsvStorage()


def run_all_ml(
    input_path: Path | None = None,
    export_artifacts: bool = True,
    persist_models: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta el pipeline completo de analisis predictivo (Paso 7).

    Args:
        input_path: Ruta al CSV con modelo conceptual. Si es None, usa
            la ruta por defecto.
        export_artifacts: Si True, exporta los artefactos a CSV.
        persist_models: Si True, persiste los modelos con joblib.

    Returns:
        Diccionario con todos los artefactos generados.

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
    """
    log_section("PASO 7 - ANALISIS PREDICTIVO (QUE PODRIA OCURRIR?)")

    if input_path is None:
        input_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d registros", len(df))

    artefactos: dict[str, Any] = {}

    # 7.1 Feature Engineering (sin target encoding)
    log.info("Ejecutando 7.1 Feature Engineering...")
    df_ml = create_features_ml(df)
    if df_ml.empty:
        return {"error": "Feature engineering fallo. Verificar columnas de entrada."}
    log.info("Matriz de features lista: %d registros", len(df_ml))

    # Split ANTES del target encoding (evita data leakage)
    df_train, df_test = train_test_split(
        df_ml,
        test_size=settings.ML_TEST_SIZE,
        random_state=settings.ML_RANDOM_STATE,
    )
    log.info("Split completado: train=%d, test=%d", len(df_train), len(df_test))

    # Target encoding: fit con train, apply a ambos
    log.info("Ejecutando target encoding (fit solo con train)...")
    encoding_maps = fit_target_encoding(df_train)
    df_train_enc = apply_target_encoding(df_train, encoding_maps)
    df_test_enc = apply_target_encoding(df_test, encoding_maps)

    # Recombinar para pasar a los modelos (ya con encoding correcto)
    df_enc = pd.concat([df_train_enc, df_test_enc], ignore_index=True)

    # 7.2 Modelo de Regresion
    log.info("Ejecutando 7.2 Regresion (Random Forest)...")
    resultado_reg = train_regression(df_enc, persist_model=persist_models)
    artefactos["7_2_metricas_regresion"] = pd.DataFrame([resultado_reg["metricas"]])
    artefactos["7_2_importancia_variables"] = resultado_reg["importancia"].to_frame("importancia")
    artefactos["7_2_predicciones_regresion"] = resultado_reg["df_residuos"]

    # 7.3 Modelo de Clasificacion
    log.info("Ejecutando 7.3 Clasificacion (Random Forest)...")
    resultado_clf = train_classification(df_enc, persist_model=persist_models)
    if "error" not in resultado_clf.get("metricas", {}):
        clf_reporte_df = pd.DataFrame(resultado_clf["metricas"]).T
        artefactos["7_3_metricas_clasificacion"] = clf_reporte_df

    # 7.4 Proyeccion de Serie de Tiempo
    log.info("Ejecutando 7.4 Proyeccion (Holt-Winters)...")
    resultado_forecast = forecast_time_series(df)
    if "error" not in resultado_forecast:
        artefactos["7_4_proyeccion_macro"] = resultado_forecast["df_proyeccion"]

    # Exportar artefactos
    if export_artifacts:
        log.info("Exportando %d artefactos...", len(artefactos))
        for nombre, df_art in artefactos.items():
            if isinstance(df_art, pd.DataFrame) and not df_art.empty:
                ruta = settings.OUTPUTS_TABLES_PATH / f"{nombre}.csv"
                _csv_storage.write_csv(df_art, ruta)

    log.info("Paso 7 completado. %d artefactos generados.", len(artefactos))
    return artefactos
