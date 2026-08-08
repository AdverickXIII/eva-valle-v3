"""
Analisis 4.3: Estadistica descriptiva profunda.
Calcula momentos, percentiles y Coeficiente de Variacion para las 4 metricas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.descriptive")

METRICAS = ["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]


def calculate_descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula momentos, percentiles y CV para las 4 metricas productivas.

    Args:
        df: DataFrame con las columnas de metricas.

    Returns:
        DataFrame con una fila por metrica y columnas:
        variable, n, media, mediana, desv_std, cv, asimetria, curtosis,
        p10, p25, p75, p90, iqr.
    """
    resultados = []
    for col in METRICAS:
        if col not in df.columns:
            log.warning("Columna '%s' no encontrada. Omitiendo.", col)
            continue
        s = df[col].dropna()
        if len(s) == 0:
            continue
        media = s.mean()
        resultados.append({
            "variable": col,
            "n": len(s),
            "media": media,
            "mediana": s.median(),
            "desv_std": s.std(),
            "cv": (s.std() / media) if media != 0 else np.nan,
            "asimetria": s.skew(),
            "curtosis": s.kurtosis(),
            "p10": s.quantile(0.10),
            "p25": s.quantile(0.25),
            "p75": s.quantile(0.75),
            "p90": s.quantile(0.90),
            "iqr": s.quantile(0.75) - s.quantile(0.25),
        })

    log.info("Estadistica descriptiva calculada para %d metricas.", len(resultados))
    return pd.DataFrame(resultados)
