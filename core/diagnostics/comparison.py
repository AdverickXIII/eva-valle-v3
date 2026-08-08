"""
Analisis 6.2: Comparacion de grupos (Transitorio vs Permanente).
Mann-Whitney U para detectar diferencias en rendimiento.

Responde: ¿Son diferentes los cultivos transitorios de los permanentes?
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.diagnostics.comparison")


def compare_cycles(df: pd.DataFrame) -> dict[str, Any]:
    """
    Mann-Whitney U para comparar rendimiento entre ciclos.

    Args:
        df: DataFrame con columnas ciclo_del_cultivo y rendimiento_t_ha.

    Returns:
        Diccionario con estadistico_U, p_value, CV por ciclo, medias,
        medianas y conclusion.
    """
    required_cols = ["ciclo_del_cultivo", "rendimiento_t_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    trans = df[df["ciclo_del_cultivo"] == "Transitorio"]["rendimiento_t_ha"].dropna()
    perm = df[df["ciclo_del_cultivo"] == "Permanente"]["rendimiento_t_ha"].dropna()

    if len(trans) < 10 or len(perm) < 10:
        return {"error": f"Muestras insuficientes: trans={len(trans)}, perm={len(perm)}"}

    stat_u, p_val = sp_stats.mannwhitneyu(trans, perm, alternative="two-sided")

    cv_trans = float((trans.std() / trans.mean()) * 100) if trans.mean() > 0 else np.nan
    cv_perm = float((perm.std() / perm.mean()) * 100) if perm.mean() > 0 else np.nan

    conclusion = (
        "Si hay diferencia estadisticamente significativa en rendimiento."
        if p_val < 0.05
        else "No hay evidencia suficiente para decir que sean diferentes."
    )

    resultado = {
        "estadistico_U": float(stat_u),
        "p_value": float(p_val),
        "CV_Transitorio": cv_trans,
        "CV_Permanente": cv_perm,
        "media_Transitorio": float(trans.mean()),
        "mediana_Transitorio": float(trans.median()),
        "n_Transitorio": len(trans),
        "media_Permanente": float(perm.mean()),
        "mediana_Permanente": float(perm.median()),
        "n_Permanente": len(perm),
        "conclusion": conclusion,
        "diferencia_significativa": bool(p_val < 0.05),
    }

    log.info("Mann-Whitney U completado (p=%.2e). %s", p_val, conclusion)
    return resultado
