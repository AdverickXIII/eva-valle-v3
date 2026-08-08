"""Calculos compartidos para los reportes por municipio."""
from __future__ import annotations

import pandas as pd


def filter_municipio(df: pd.DataFrame, municipio: str) -> pd.DataFrame:
    return df[df["municipio"] == municipio].copy()


def kpis(df_m: pd.DataFrame, df_all: pd.DataFrame) -> dict:
    prod = df_m["produccion_t"].sum()
    area = df_m["area_sembrada_ha"].sum()
    cosech = df_m["area_cosechada_ha"].sum()
    rend = prod / cosech if cosech else 0.0
    total_dpto = df_all["produccion_t"].sum()
    share = prod / total_dpto * 100 if total_dpto else 0.0
    return {
        "Produccion total (t)": round(float(prod), 1),
        "Area sembrada (ha)": round(float(area), 1),
        "Rendimiento promedio (t/ha)": round(float(rend), 2),
        "Cultivos activos": int(df_m["cultivo"].nunique()),
        "Periodos con datos": int(df_m["periodo"].nunique()),
        "% de la produccion departamental": round(float(share), 2),
    }


def yearly(df_m: pd.DataFrame) -> pd.DataFrame:
    g = (df_m.groupby("ano")
         .agg(produccion=("produccion_t", "sum"),
              area_sembrada=("area_sembrada_ha", "sum"),
              area_cosechada=("area_cosechada_ha", "sum"))
         .reset_index())
    g["rendimiento"] = (g["produccion"] / g["area_cosechada"].replace(0, 1)).round(2)
    return g


def top_cultivos(df_m: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    g = (df_m.groupby("cultivo")["produccion_t"].sum()
         .sort_values(ascending=False).head(n).reset_index())
    total = g["produccion_t"].sum()
    g["share_pct"] = (g["produccion_t"] / total * 100).round(1) if total else 0.0
    return g


def ranking_posicion(df_all: pd.DataFrame, municipio: str):
    r = (df_all.groupby("municipio")["produccion_t"].sum()
         .sort_values(ascending=False).reset_index())
    hit = r[r["municipio"] == municipio].index
    return (int(hit[0]) + 1, len(r)) if len(hit) else (None, len(r))
