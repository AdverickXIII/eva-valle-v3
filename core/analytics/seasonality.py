"""
Analisis 4.8: Estacionalidad semestral.
Wilcoxon signed-rank test para A vs B en cultivos transitorios.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.seasonality")


def test_seasonality_ab(df: pd.DataFrame, min_pares: int = 5) -> pd.DataFrame:
    """
    Wilcoxon signed-rank test para comparar semestres A vs B.

    Args:
        df: DataFrame con columnas ciclo_del_cultivo, periodo, cultivo,
            ano, produccion_t.
        min_pares: Minimo de pares A/B por cultivo (default 5).

    Returns:
        DataFrame con resultados por cultivo, ordenado por p_value.
    """
    required_cols = ["ciclo_del_cultivo", "periodo", "cultivo", "ano", "produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para estacionalidad: %s", faltantes)
        return pd.DataFrame()

    df_trans = df[df["ciclo_del_cultivo"] == "Transitorio"].copy()
    df_trans["semestre"] = df_trans["periodo"].str[-1].str.upper()
    df_trans = df_trans[df_trans["semestre"].isin(["A", "B"])]

    # Pivotar para obtener la produccion total de cada cultivo por ano y semestre
    pivot = df_trans.groupby(["cultivo", "ano", "semestre"])["produccion_t"].sum().reset_index()
    pivot_tab = pivot.pivot_table(index=["cultivo", "ano"], columns="semestre", values="produccion_t")

    resultados = []
    for cultivo in pivot_tab.index.get_level_values(0).unique():
        datos_cultivo = pivot_tab.loc[cultivo].dropna(subset=["A", "B"])
        if len(datos_cultivo) >= min_pares:
            stat, pval = sp_stats.wilcoxon(datos_cultivo["A"], datos_cultivo["B"])
            media_a = datos_cultivo["A"].mean()
            media_b = datos_cultivo["B"].mean()
            dif_pct = ((media_b - media_a) / media_a) * 100 if media_a != 0 else np.nan
            resultados.append({
                "cultivo": cultivo,
                "pares_analizados": len(datos_cultivo),
                "media_A": media_a,
                "media_B": media_b,
                "dif_porcent": dif_pct,
                "statistic_wilcoxon": stat,
                "p_value": pval,
                "diferencia_significativa": pval < 0.05,
            })

    if not resultados:
        log.info("No se encontraron pares A/B suficientes para el test.")
        return pd.DataFrame()

    log.info("Estacionalidad A vs B: %d cultivos analizados.", len(resultados))
    return pd.DataFrame(resultados).sort_values("p_value")
