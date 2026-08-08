"""
Analisis 6.1: Matriz de correlacion (Spearman) y estadisticas bivariadas.

Responde la pregunta: ¿Por que sube la produccion?
Identifica las relaciones mas fuertes entre variables productivas.

Mejora respecto al notebook:
- Separacion calculo / visualizacion.
- El nucleo solo calcula; la UI (ui/charts/) renderiza los graficos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.diagnostics.correlation")

METRICAS = [
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_t_ha",
    "ano",
]


def calculate_correlation_matrix(df: pd.DataFrame, method: str = "spearman") -> pd.DataFrame:
    """
    Calcula la matriz de correlacion entre metricas productivas.

    Args:
        df: DataFrame con las columnas de metricas.
        method: Metodo de correlacion ('spearman', 'pearson', 'kendall').

    Returns:
        DataFrame con la matriz de correlacion (n x n).
    """
    metricas_disponibles = [c for c in METRICAS if c in df.columns]
    if len(metricas_disponibles) < 2:
        log.warning("Menos de 2 metricas disponibles. No se puede calcular correlacion.")
        return pd.DataFrame()

    corr = df[metricas_disponibles].corr(method=method)
    log.info(
        "Matriz de correlacion (%s) calculada: %d x %d",
        method, len(metricas_disponibles), len(metricas_disponibles),
    )
    return corr


def calculate_bivariate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadisticas bivariadas clave para visualizacion posterior.

    Retorna pares (X, Y) con estadisticas utiles para scatterplots.

    Args:
        df: DataFrame con metricas productivas.

    Returns:
        DataFrame con columnas: pair, n, correlation, r_squared,
        x_var, y_var.
    """
    pares = [
        ("area_cosechada_ha", "produccion_t"),
        ("area_cosechada_ha", "rendimiento_t_ha"),
        ("area_sembrada_ha", "area_cosechada_ha"),
        ("ano", "produccion_t"),
    ]
    resultados = []
    for x, y in pares:
        if x not in df.columns or y not in df.columns:
            continue
        df_pos = df[(df[x] > 0) & (df[y] > 0)]
        if len(df_pos) < 10:
            continue
        r = df_pos[x].corr(df_pos[y], method="spearman")
        resultados.append({
            "pair": f"{x} vs {y}",
            "n": len(df_pos),
            "correlation": r,
            "r_squared": r ** 2,
            "x_var": x,
            "y_var": y,
        })

    log.info("Estadisticas bivariadas calculadas para %d pares.", len(resultados))
    return pd.DataFrame(resultados)
