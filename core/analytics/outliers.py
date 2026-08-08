"""
Analisis 4.5: Deteccion de outliers multivariados.
Isolation Forest sobre las 4 metricas para detectar anomalias conjuntas.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from config.settings import settings
from core.logging import get_logger

log = get_logger("core.analytics.outliers")

METRICAS = ["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]


def detect_multivariate_outliers(
    df: pd.DataFrame,
    contamination: float = 0.02,
) -> pd.DataFrame:
    """
    Detecta anomalias multivariadas con Isolation Forest.

    Args:
        df: DataFrame con las 4 metricas y columnas de contexto.
        contamination: Proporcion esperada de outliers (default 2%).

    Returns:
        DataFrame con los registros anomalos y sus metricas.
    """
    df_clean = df.dropna(subset=METRICAS).copy()
    if len(df_clean) < 50:
        log.warning("Muestra insuficiente (%d < 50). Omitiendo outliers.", len(df_clean))
        return pd.DataFrame()

    iso = IsolationForest(
        contamination=contamination,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=-1,
    )
    df_clean["es_outlier"] = iso.fit_predict(df_clean[METRICAS])
    outliers = df_clean[df_clean["es_outlier"] == -1].copy()
    outliers["tipo_anomalia"] = "Anomalia multivariada (Isolation Forest)"

    pct = (len(outliers) / len(df_clean)) * 100
    log.info("Outliers multivariados detectados: %d (%.1f%%)", len(outliers), pct)

    # Retornar columnas de contexto + metricas
    cols_contexto = ["id_registro", "municipio", "cultivo", "periodo"]
    cols_disponibles = [c for c in cols_contexto if c in outliers.columns]
    return outliers[cols_disponibles + METRICAS + ["tipo_anomalia"]]
