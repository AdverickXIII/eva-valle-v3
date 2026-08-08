"""
Analisis 7.2: Modelo de Regresion (Random Forest).
Predice log(produccion) a partir de features productivas.

Mejoras respecto al notebook:
- Sin matplotlib (separacion calculo / visualizacion).
- Persistencia del modelo con JoblibModelRegistry.
- Parametros configurables.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from adapters.ml_registry.joblib_registry import JoblibModelRegistry
from config.settings import settings
from core.logging import get_logger

log = get_logger("core.ml.regression")

REGRESSION_FEATURES = [
    "area_sembrada_ha",
    "rendimiento_lag1",
    "produccion_lag1",
    "target_enc_municipio",
    "target_enc_cultivo",
    "ano",
]
REGRESSION_TARGET = "log_produccion"
MODEL_NAME = "rf_regresion_v1"


def train_regression(
    df: pd.DataFrame,
    n_estimators: int = 200,
    max_depth: int = 10,
    test_size: float | None = None,
    persist_model: bool = True,
) -> dict[str, Any]:
    """
    Entrena un Random Forest Regressor sobre log(produccion).

    Args:
        df: DataFrame con features y target (post target-encoding).
        n_estimators: Numero de arboles (default 200).
        max_depth: Profundidad maxima de cada arbol (default 10).
        test_size: Proporcion de test. Si None, usa settings.ML_TEST_SIZE.
        persist_model: Si True, guarda el modelo con joblib.

    Returns:
        Diccionario con: modelo, metricas, importancia, df_residuos.
    """
    if test_size is None:
        test_size = settings.ML_TEST_SIZE

    available_features = [f for f in REGRESSION_FEATURES if f in df.columns]
    faltantes = [f for f in REGRESSION_FEATURES if f not in df.columns]
    if faltantes:
        log.warning("Features faltantes para regresion: %s", faltantes)

    X = df[available_features]
    y = df[REGRESSION_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=settings.ML_RANDOM_STATE,
    )

    rf_reg = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=-1,
    )
    rf_reg.fit(X_train, y_train)

    # Predicciones y metricas
    y_pred_log = rf_reg.predict(X_test)
    rmse_log = float(np.sqrt(mean_squared_error(y_test, y_pred_log)))
    mae_log = float(mean_absolute_error(y_test, y_pred_log))
    r2 = float(r2_score(y_test, y_pred_log))

    # Metricas en escala real (toneladas)
    y_test_real = np.expm1(y_test)
    y_pred_real = np.expm1(y_pred_log)
    mae_toneladas = float(mean_absolute_error(y_test_real, y_pred_real))

    metricas = {
        "RMSE_Log": rmse_log,
        "MAE_Log": mae_log,
        "R2": r2,
        "MAE_Toneladas": mae_toneladas,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    # Importancia de variables
    importancia = pd.Series(
        rf_reg.feature_importances_, index=available_features
    ).sort_values(ascending=False)

    # DataFrame de residuos (para visualizacion posterior)
    df_residuos = pd.DataFrame({
        "Real_t": y_test_real,
        "Pred_t": y_pred_real,
        "Residuo_t": y_test_real - y_pred_real,
    })

    # Persistir modelo
    if persist_model:
        registry = JoblibModelRegistry()
        registry.save_model(rf_reg, MODEL_NAME)
        log.info("Modelo de regresion persistido como '%s'.", MODEL_NAME)

    log.info(
        "Regresion completada: R2=%.3f, MAE=%.0f t, Top feature=%s",
        r2, mae_toneladas, importancia.index[0],
    )

    return {
        "modelo": rf_reg,
        "metricas": metricas,
        "importancia": importancia,
        "df_residuos": df_residuos,
        "features_usadas": available_features,
    }
