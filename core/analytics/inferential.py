"""
Analisis 4.12: Analisis estadistico inferencial.
Kruskal-Wallis: ¿El rendimiento difiere entre municipios?
"""
from __future__ import annotations

import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.inferential")


def run_inferential_test(
    df: pd.DataFrame,
    min_por_grupo: int = 5,
    min_grupos: int = 3,
) -> pd.DataFrame:
    """
    Kruskal-Wallis: ¿El rendimiento difiere significativamente entre municipios?

    Args:
        df: DataFrame con columnas municipio y rendimiento_t_ha.
        min_por_grupo: Minimo de observaciones por grupo (default 5).
        min_grupos: Minimo de grupos para ejecutar el test (default 3).

    Returns:
        DataFrame con el resultado del test.
    """
    required_cols = ["municipio", "rendimiento_t_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para Kruskal-Wallis: %s", faltantes)
        return pd.DataFrame()

    grupos = [
        group["rendimiento_t_ha"].dropna().values
        for name, group in df.groupby("municipio")
        if len(group) > min_por_grupo
    ]

    if len(grupos) < min_grupos:
        log.warning("Menos de %d grupos con datos suficientes.", min_grupos)
        return pd.DataFrame()

    stat, pval = sp_stats.kruskal(*grupos)

    resultado = pd.DataFrame([{
        "test": "Kruskal-Wallis (Rendimiento por Municipio)",
        "statistic_H": stat,
        "p_value": pval,
        "hay_diferencia_significativa": pval < 0.05,
    }])

    log.info("Kruskal-Wallis completado (H=%.2f, p=%.2e).", stat, pval)
    return resultado
