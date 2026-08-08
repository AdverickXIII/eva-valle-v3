"""
Analisis 4.4: Ajuste de distribuciones.
Prueba KS-test para Normal, Log-Normal y Gamma sobre el rendimiento.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.distributions")


def fit_distributions(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Prueba KS-test para Normal, Log-Normal y Gamma sobre rendimiento_t_ha.

    Args:
        df: DataFrame con la columna rendimiento_t_ha.
        alpha: Nivel de significancia (default 0.05).

    Returns:
        DataFrame con columnas: distribucion, statistic_ks, p_value,
        rechaza_H0.
    """
    if "rendimiento_t_ha" not in df.columns:
        log.warning("Columna rendimiento_t_ha no encontrada.")
        return pd.DataFrame()

    s = df["rendimiento_t_ha"].dropna()
    s = s[s > 0]  # Lognormal y Gamma no aceptan ceros

    if len(s) < 20:
        log.warning("Muestra insuficiente (%d < 20). Omitiendo ajuste.", len(s))
        return pd.DataFrame()

    # Normal (estandarizada)
    s_norm = (s - s.mean()) / s.std()
    ks_norm = sp_stats.kstest(s_norm, "norm")

    # Log-Normal (log de los datos, estandarizado)
    s_log = np.log(s)
    s_log_norm = (s_log - s_log.mean()) / s_log.std()
    ks_lognorm = sp_stats.kstest(s_log_norm, "norm")

    # Gamma (ajuste de parametros)
    params_gamma = sp_stats.gamma.fit(s, floc=0)
    ks_gamma = sp_stats.kstest(s, "gamma", args=params_gamma)

    resultados = [
        {"distribucion": "Normal", "statistic_ks": ks_norm.statistic, "p_value": ks_norm.pvalue},
        {"distribucion": "Log-Normal", "statistic_ks": ks_lognorm.statistic, "p_value": ks_lognorm.pvalue},
        {"distribucion": "Gamma", "statistic_ks": ks_gamma.statistic, "p_value": ks_gamma.pvalue},
    ]

    res_df = pd.DataFrame(resultados)
    res_df[f"rechaza_H0 (alpha={alpha})"] = res_df["p_value"] < alpha

    log.info("Ajuste de distribuciones completado (n=%d).", len(s))
    return res_df
