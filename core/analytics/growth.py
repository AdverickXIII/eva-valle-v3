"""
Analisis 4.13: CAGR y dinamica de crecimiento por cultivo.
Tasa de Crecimiento Anual Compuesta (2019 a 2024).
"""
from __future__ import annotations

import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.growth")


def calculate_cagr(df: pd.DataFrame) -> pd.DataFrame:
    """
    CAGR por cultivo entre el primer y ultimo ano del dataset.

    Args:
        df: DataFrame con columnas ano, cultivo, produccion_t.

    Returns:
        DataFrame con columnas: cultivo, prod_inicio, prod_fin, cagr.
        Ordenado por cagr descendente.
    """
    required_cols = ["ano", "cultivo", "produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para CAGR: %s", faltantes)
        return pd.DataFrame()

    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2:
        log.warning("Menos de 2 anos en el dataset. No se puede calcular CAGR.")
        return pd.DataFrame()

    ano_ini, ano_fin = min(anos), max(anos)
    n_years = ano_fin - ano_ini

    ini = df[df["ano"] == ano_ini].groupby("cultivo")["produccion_t"].sum()
    fin = df[df["ano"] == ano_fin].groupby("cultivo")["produccion_t"].sum()

    cagr_df = pd.DataFrame({"prod_inicio": ini, "prod_fin": fin}).dropna()

    # Evitar division por cero si prod_inicio es 0
    cagr_df = cagr_df[cagr_df["prod_inicio"] > 0]

    cagr_df["cagr"] = (
        (cagr_df["prod_fin"] / cagr_df["prod_inicio"]) ** (1 / n_years) - 1
    ) * 100

    resultado = cagr_df.reset_index().sort_values("cagr", ascending=False)
    log.info("CAGR calculado para %d cultivos (%d-%d).", len(resultado), ano_ini, ano_fin)
    return resultado
