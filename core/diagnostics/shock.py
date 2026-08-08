"""
Analisis 6.5: Analisis del shock exogeno (Impacto 2020).
Aislamiento del efecto COVID-19 vs tendencia historica.

Responde: ¿Que paso en 2020? ¿La produccion cayo o siguio creciendo?
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from core.logging import get_logger

log = get_logger("core.diagnostics.shock")

ANOS_EXPECTED = [2019, 2020, 2021, 2022, 2023, 2024]
SHOCK_YEAR = 2020


def analyze_shock(df: pd.DataFrame, shock_year: int = SHOCK_YEAR) -> dict[str, Any]:
    """
    Calcula variaciones interanuales y detecta shocks exogenos.

    Args:
        df: DataFrame con columnas ano, produccion_t, area_sembrada_ha.
        shock_year: Ano del shock a analizar (default 2020).

    Returns:
        Diccionario con: df_historico (variaciones anuales),
        impacto_shock (variacion en shock_year vs tendencia).
    """
    required_cols = ["ano", "produccion_t", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    hist = (
        df.groupby("ano")
        .agg(produccion=("produccion_t", "sum"), area=("area_sembrada_ha", "sum"))
        .reset_index()
    )
    hist["var_produccion"] = hist["produccion"].pct_change() * 100
    hist["var_area"] = hist["area"].pct_change() * 100

    # Calcular tendencia pre-shock (promedio de variaciones antes del shock)
    pre_shock = hist[hist["ano"] < shock_year]
    tendencia_previa_prod = pre_shock["var_produccion"].mean() if len(pre_shock) > 0 else 0

    # Impacto del shock
    shock_data = hist[hist["ano"] == shock_year]
    if shock_data.empty:
        return {
            "error": f"Ano {shock_year} no encontrado en el dataset.",
            "df_historico": hist,
        }

    var_shock_prod = float(shock_data["var_produccion"].iloc[0])
    var_shock_area = float(shock_data["var_area"].iloc[0])

    # Diferencia entre lo observado y la tendencia esperada
    desviacion_vs_tendencia = var_shock_prod - tendencia_previa_prod

    impacto = {
        "shock_year": shock_year,
        "var_produccion": var_shock_prod,
        "var_area": var_shock_area,
        "tendencia_previa_prod": float(tendencia_previa_prod) if not pd.isna(tendencia_previa_prod) else 0.0,
        "desviacion_vs_tendencia": desviacion_vs_tendencia,
        "direccion": "caida" if var_shock_prod < 0 else "crecimiento",
        "impacto_significativo": abs(desviacion_vs_tendencia) > 5.0,
    }

    log.info(
        "Analisis de shock %d: produccion %.2f%%, desviacion vs tendencia %.2f%%",
        shock_year, var_shock_prod, desviacion_vs_tendencia,
    )

    return {
        "df_historico": hist,
        "impacto_shock": impacto,
    }
