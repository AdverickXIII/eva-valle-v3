"""
Analisis 4.6: Concentracion (Gini, HHI, Lorenz).

⚠️ CORRECCION CRITICA (Fase 0 - Bug P2):
El codigo original ordenaba los datos de forma DESCENDENTE (ascending=False),
lo cual producia un Gini NEGATIVO (-0.966). La curva de Lorenz requiere
ordenamiento ASCENDENTE (ascending=True) para acumular desde los mas
pequenos hacia los mas grandes.

Referencia: https://en.wikipedia.org/wiki/Lorenz_curve
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.concentration")


def _trapezoid(y: np.ndarray, x: np.ndarray) -> float:
    """
    Calcula el area bajo la curva usando la regla del trapecio.
    Compatible con NumPy 1.x (trapz) y 2.x (trapezoid).
    """
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def calculate_concentration(
    df: pd.DataFrame,
    grupo: str = "cultivo",
    valor: str = "produccion_t",
) -> dict[str, Any]:
    """
    Calcula HHI, Gini y datos para curva de Lorenz.

    ⚠️ CORRECCION: Los datos se ordenan ASCENDENTE (ascending=True)
    para que la curva de Lorenz acumule correctamente desde los mas
    pequenos hacia los mas grandes. El codigo original usaba
    ascending=False, produciendo Gini negativo.

    Args:
        df: DataFrame con las columnas de agrupacion y valor.
        grupo: Columna por la que agrupar (default 'cultivo').
        valor: Columna de valor a concentrar (default 'produccion_t').

    Returns:
        Diccionario con: grupo_analisis, variable, hhi, gini,
        n_entidades, top1_share, top3_share, lorenz_x, lorenz_y.
    """
    if grupo not in df.columns or valor not in df.columns:
        log.warning("Columnas '%s' o '%s' no encontradas.", grupo, valor)
        return {}

    # ⚠️ CORRECCION: ascending=True (antes era ascending=False → Gini negativo)
    agrupado = df.groupby(grupo)[valor].sum().sort_values(ascending=True)

    if agrupado.sum() == 0:
        log.warning("Suma total de '%s' es cero. No se puede calcular concentracion.", valor)
        return {}

    shares = agrupado / agrupado.sum()

    # HHI: suma de cuadrados de las participaciones, escalado a 10,000
    hhi = float((shares ** 2).sum() * 10_000)

    # Curva de Lorenz y Gini
    cum_shares = shares.cumsum()
    lorenz_x = np.arange(1, len(cum_shares) + 1) / len(cum_shares)
    lorenz_y = cum_shares.values
    auc = _trapezoid(lorenz_y, lorenz_x)
    gini = float(1 - 2 * auc)

    # Validar que el Gini este en el rango esperado [0, 1]
    if gini < 0 or gini > 1:
        log.warning(
            "Gini fuera de rango [0,1]: %.3f. Verificar ordenamiento de datos.",
            gini,
        )

    # Para top1 y top3, necesitamos orden descendente
    shares_desc = shares.sort_values(ascending=False)

    resultado = {
        "grupo_analisis": grupo,
        "variable": valor,
        "hhi": hhi,
        "gini": gini,
        "n_entidades": len(shares),
        "top1_share": float(shares_desc.iloc[0] * 100),
        "top3_share": float(shares_desc.head(3).sum() * 100),
        "lorenz_x": lorenz_x.tolist(),
        "lorenz_y": lorenz_y.tolist(),
    }

    log.info(
        "Concentracion (%s por %s): HHI=%.0f, Gini=%.3f, Top1=%.1f%%",
        valor, grupo, hhi, gini, resultado["top1_share"],
    )
    return resultado
