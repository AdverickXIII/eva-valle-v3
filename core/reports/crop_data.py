"""Estadisticas y concentracion territorial por cultivo (ficha tecnica)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def filter_cultivo(df: pd.DataFrame, cultivo: str) -> pd.DataFrame:
    return df[df["cultivo"] == cultivo].copy()


def _gini(arr: np.ndarray) -> float:
    arr = np.sort(np.asarray(arr, dtype=float))
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    i = np.arange(1, n + 1)
    return float(np.sum((2 * i - n - 1) * arr) / (n * arr.sum()))


def crop_kpis(df_c: pd.DataFrame, df_all: pd.DataFrame) -> dict:
    prod = float(df_c["produccion_t"].sum())
    area = float(df_c["area_sembrada_ha"].sum())
    cos = float(df_c["area_cosechada_ha"].sum())
    total = float(df_all["produccion_t"].sum())
    return {
        "Produccion total (t)": round(prod, 1),
        "Area sembrada (ha)": round(area, 1),
        "Rendimiento (t/ha)": round(prod / cos, 2) if cos else 0.0,
        "Municipios productores": int(df_c["municipio"].nunique()),
        "% del departamento": round(prod / total * 100, 2) if total else 0.0,
    }


def crop_yearly(df_c: pd.DataFrame) -> pd.DataFrame:
    g = (df_c.groupby("ano")
         .agg(produccion=("produccion_t", "sum"),
              area_sembrada=("area_sembrada_ha", "sum"),
              area_cosechada=("area_cosechada_ha", "sum"))
         .reset_index())
    g["rendimiento"] = (g["produccion"] / g["area_cosechada"].replace(0, 1)).round(2)
    return g


def crop_top_municipios(df_c: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    g = (df_c.groupby("municipio")["produccion_t"].sum()
         .sort_values(ascending=False).head(n).reset_index())
    total = g["produccion_t"].sum()
    g["share_pct"] = (g["produccion_t"] / total * 100).round(1) if total else 0.0
    return g


def crop_concentration(df_c: pd.DataFrame) -> dict:
    """Que tan concentrada esta la produccion del cultivo entre municipios."""
    g = df_c.groupby("municipio")["produccion_t"].sum()
    g = g[g > 0]
    if len(g) == 0:
        return {"gini": 0.0, "hhi": 0.0, "top1_pct": 0.0, "municipios": 0}
    shares = g / g.sum() * 100
    return {
        "gini": round(_gini(g.values), 3),
        "hhi": round(float((shares ** 2).sum()), 1),
        "top1_pct": round(float(shares.max()), 1),
        "municipios": int(len(g)),
    }


def interpretar_gini(gini: float) -> str:
    if gini < 0.35:
        return "Distribuido (baja dependencia territorial)"
    if gini < 0.5:
        return "Concentracion moderada"
    return "Concentrado (riesgo por dependencia de pocos municipios)"
