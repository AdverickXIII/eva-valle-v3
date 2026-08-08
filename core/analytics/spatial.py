"""
Analisis 4.9 y 4.10: Economia espacial.
Location Quotient (LQ) e Indice Shannon-Wiener de diversificacion.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.spatial")


def calculate_location_quotient(df: pd.DataFrame) -> pd.DataFrame:
    """
    Location Quotient basado en area sembrada por grupo de cultivo y municipio.

    LQ > 1 indica especializacion del municipio en ese grupo de cultivo
    respecto al promedio departamental.

    Args:
        df: DataFrame con columnas codigo_dane_municipio, grupo_cultivo,
            area_sembrada_ha.

    Returns:
        DataFrame con columnas: codigo_dane_municipio, grupo_cultivo, LQ.
    """
    required_cols = ["codigo_dane_municipio", "grupo_cultivo", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para LQ: %s", faltantes)
        return pd.DataFrame()

    muni_grupo = (
        df.groupby(["codigo_dane_municipio", "grupo_cultivo"])["area_sembrada_ha"]
        .sum()
        .unstack(fill_value=0)
    )
    valle_grupo = df.groupby("grupo_cultivo")["area_sembrada_ha"].sum()

    # Salvaguarda: evitar division por cero
    valle_grupo_safe = valle_grupo.replace(0, 1e-8)
    muni_total_safe = muni_grupo.sum(axis=1).replace(0, 1e-8)

    lq_df = (
        (muni_grupo / muni_total_safe.values[:, None])
        / (valle_grupo_safe / valle_grupo_safe.sum())
    )

    resultado = lq_df.reset_index().melt(
        id_vars="codigo_dane_municipio",
        var_name="grupo_cultivo",
        value_name="LQ",
    )
    log.info("LQ calculado: %d combinaciones municipio x grupo.", len(resultado))
    return resultado


def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Indice de Shannon-Wiener de diversificacion por municipio.

    Mayor indice = menor dependencia de un solo cultivo.

    Args:
        df: DataFrame con columnas municipio, area_sembrada_ha.

    Returns:
        DataFrame con columnas: municipio, cultivos_distintos,
        shannon_wiener, area_total. Ordenado por shannon_wiener desc.
    """
    required_cols = ["municipio", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para Shannon: %s", faltantes)
        return pd.DataFrame()

    def shannon_index(s: pd.Series) -> float:
        p = s / s.sum()
        p = p[p > 0]
        return float(-np.sum(p * np.log(p)))

    diversidad = df.groupby("municipio")["area_sembrada_ha"].agg(
        cultivos_distintos="nunique",
        shannon_wiener=shannon_index,
        area_total="sum",
    ).reset_index()

    resultado = diversidad.sort_values("shannon_wiener", ascending=False)
    log.info("Shannon-Wiener calculado para %d municipios.", len(resultado))
    return resultado
