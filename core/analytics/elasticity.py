"""
Analisis 4.11: Elasticidades y analisis de eficiencia productiva.
Regresion log-log OLS de produccion vs area sembrada.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.elasticity")


def calculate_elasticity(df: pd.DataFrame, min_observaciones: int = 30) -> dict[str, Any]:
    """
    Elasticidad produccion-area (Log-Log OLS).

    Args:
        df: DataFrame con columnas produccion_t y area_sembrada_ha.
        min_observaciones: Minimo de observaciones validas (default 30).

    Returns:
        Diccionario con: elasticidad, r_cuadrado, p_value, n_regresion.
        Si hay error, retorna {"error": "mensaje"}.
    """
    required_cols = ["produccion_t", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    df_reg = df[(df["produccion_t"] > 0) & (df["area_sembrada_ha"] > 0)].copy()
    if len(df_reg) < min_observaciones:
        return {"error": f"Insuficientes datos > 0 para regresion log-log ({len(df_reg)} < {min_observaciones})"}

    df_reg["log_prod"] = np.log(df_reg["produccion_t"])
    df_reg["log_area"] = np.log(df_reg["area_sembrada_ha"])

    slope, intercept, r_value, p_value, std_err = sp_stats.linregress(
        df_reg["log_area"], df_reg["log_prod"]
    )

    resultado = {
        "elasticidad": float(slope),
        "r_cuadrado": float(r_value ** 2),
        "p_value": float(p_value),
        "n_regresion": len(df_reg),
    }

    log.info(
        "Elasticidad calculada: %.3f (R2=%.3f, n=%d)",
        resultado["elasticidad"], resultado["r_cuadrado"], len(df_reg),
    )
    return resultado
