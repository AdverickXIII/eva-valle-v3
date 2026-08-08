"""
Analisis 4.7: Series de tiempo.
Descomposicion STL y prueba Dickey-Fuller sobre produccion total semestral.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.time_series")


def analyze_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descomposicion STL y prueba Dickey-Fuller sobre produccion total.

    Args:
        df: DataFrame con columnas periodo y produccion_t.

    Returns:
        DataFrame con resultados de la prueba Dickey-Fuller.
    """
    if "periodo" not in df.columns or "produccion_t" not in df.columns:
        log.warning("Columnas periodo o produccion_t no encontradas.")
        return pd.DataFrame()

    # Agregar produccion por periodo
    df_temp = df.groupby("periodo")["produccion_t"].sum().reset_index()

    # Ordenar cronologicamente
    df_temp["orden"] = df_temp["periodo"].str[:4].astype(int) + np.where(
        df_temp["periodo"].str.len() == 5,
        np.where(df_temp["periodo"].str[-1] == "A", 0.25, 0.75),
        0.5,
    )
    df_temp = df_temp.sort_values("orden")

    resultados = []
    if len(df_temp) >= 8:
        try:
            from statsmodels.tsa.seasonal import STL
            from statsmodels.tsa.stattools import adfuller

            stl = STL(df_temp["produccion_t"], period=2, robust=True)
            res = stl.fit()
            df_temp["tendencia"] = res.trend
            df_temp["estacional"] = res.seasonal
            df_temp["residuo"] = res.resid

            adf_stat, adf_pval, _, _, _, _ = adfuller(df_temp["produccion_t"])
            resultados.append({
                "test": "Dickey-Fuller (Produccion Total)",
                "statistic": adf_stat,
                "p_value": adf_pval,
                "es_estacionaria": adf_pval < 0.05,
            })
            log.info("STL y Dickey-Fuller completados (p=%.4f).", adf_pval)
        except Exception as e:
            log.warning("STL fallo (muestra pequena): %s", e)
    else:
        log.warning("Serie muy corta (%d < 8). Omitiendo STL.", len(df_temp))

    return pd.DataFrame(resultados)
