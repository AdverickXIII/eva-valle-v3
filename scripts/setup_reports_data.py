"""Reescribe core/reports/data.py con proyeccion y CAGR por municipio."""
from pathlib import Path

DATA = '''"""Calculos compartidos para los reportes por municipio."""
from __future__ import annotations

import numpy as np
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


def forecast_municipality(df_m: pd.DataFrame, horizonte: int = 1) -> dict | None:
    """Proyeccion tendencial (regresion lineal) de la produccion anual."""
    g = df_m.groupby("ano")["produccion_t"].sum().sort_index()
    if len(g) < 3:
        return None
    years = [int(a) for a in g.index]
    values = [float(v) for v in g.values]
    x = np.arange(len(values))
    y = np.array(values)
    slope, intercept = np.polyfit(x, y, 1)
    fx = np.arange(len(values), len(values) + horizonte)
    preds = np.clip(intercept + slope * fx, 0, None)
    f_years = [years[-1] + i + 1 for i in range(horizonte)]
    return {
        "years": years,
        "values": values,
        "forecast_years": f_years,
        "forecast_values": [float(p) for p in preds],
    }


def cagr_municipality(df_m: pd.DataFrame, min_prod_inicial: float = 50.0) -> pd.DataFrame:
    """CAGR por cultivo dentro del municipio (2019 -> ultimo ano)."""
    anos = sorted(df_m["ano"].dropna().unique())
    if len(anos) < 2:
        return pd.DataFrame()
    ini_y, fin_y = int(min(anos)), int(max(anos))
    n = fin_y - ini_y
    ini = df_m[df_m["ano"] == ini_y].groupby("cultivo")["produccion_t"].sum()
    fin = df_m[df_m["ano"] == fin_y].groupby("cultivo")["produccion_t"].sum()
    d = pd.DataFrame({"prod_inicio": ini, "prod_fin": fin}).dropna()
    d = d[(d["prod_inicio"] > 0) & (d["prod_inicio"] >= min_prod_inicial)]
    if d.empty:
        return d.reset_index()
    d["cagr_pct"] = ((d["prod_fin"] / d["prod_inicio"]) ** (1 / n) - 1) * 100
    return d.sort_values("cagr_pct", ascending=False).reset_index()
'''

Path("core/reports/data.py").write_text(DATA, encoding="utf-8")
print("[OK] core/reports/data.py (v2: +forecast +CAGR)")
print("Sigue: python scripts\\setup_reports_pdf.py")