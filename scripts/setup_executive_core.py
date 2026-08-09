"""Crea core/analytics/executive.py: motor del resumen de alto nivel."""
from pathlib import Path

EXEC = '''"""Calculo del resumen ejecutivo de alto nivel."""
from __future__ import annotations

import pandas as pd

from core.analytics.alerts import generate_alerts
from core.reports.crop_data import _gini, interpretar_gini


def _pct(new: float, old: float) -> float:
    return float((new / old - 1) * 100) if old else 0.0


def _cagr(df: pd.DataFrame, min_prod: float = 500.0) -> pd.DataFrame:
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2:
        return pd.DataFrame()
    ini_y, fin_y = int(min(anos)), int(max(anos))
    n = fin_y - ini_y
    ini = df[df["ano"] == ini_y].groupby("cultivo")["produccion_t"].sum()
    fin = df[df["ano"] == fin_y].groupby("cultivo")["produccion_t"].sum()
    d = pd.DataFrame({"ini": ini, "fin": fin}).dropna()
    d = d[d["ini"] >= min_prod]
    if d.empty:
        return d.reset_index()
    d["cagr"] = ((d["fin"] / d["ini"]) ** (1 / n) - 1) * 100
    return d.reset_index()


def executive_summary(df: pd.DataFrame) -> dict:
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    last = anos[-1]
    prev = anos[-2] if len(anos) > 1 else last
    dl, dp = df[df["ano"] == last], df[df["ano"] == prev]

    prod_l, prod_p = dl["produccion_t"].sum(), dp["produccion_t"].sum()
    area_l, area_p = dl["area_sembrada_ha"].sum(), dp["area_sembrada_ha"].sum()
    cos_l, cos_p = dl["area_cosechada_ha"].sum(), dp["area_cosechada_ha"].sum()
    rend_l = prod_l / cos_l if cos_l else 0
    rend_p = prod_p / cos_p if cos_p else 0

    g = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=True)
    shares = g / g.sum() * 100
    hhi = float((shares ** 2).sum())
    gini = _gini(g.values)
    top1_name, top1_pct = str(g.idxmax()), float(shares.max())

    cagr = _cagr(df)
    crecen = cagr.sort_values("cagr", ascending=False).head(3) if not cagr.empty else cagr
    declinan = cagr.sort_values("cagr").head(3) if not cagr.empty else cagr

    mensajes = [
        f"{top1_name} concentra {top1_pct:.1f}% de la produccion departamental.",
        f"Concentracion productiva: Gini={gini:.2f} (por cultivo).",
    ]
    if not cagr.empty:
        c, d = crecen.iloc[0], declinan.iloc[0]
        mensajes.append(f"{c['cultivo']} es el motor de crecimiento (CAGR +{c['cagr']:.1f}%).")
        mensajes.append(f"{d['cultivo']} muestra el mayor declive (CAGR {d['cagr']:.1f}%).")
    mensajes.append(f"Produccion {last} vs {prev}: {_pct(prod_l, prod_p):+.1f}%.")

    tendencia = (df.groupby("ano")
                 .agg(produccion=("produccion_t", "sum"),
                      area=("area_sembrada_ha", "sum"),
                      cosechada=("area_cosechada_ha", "sum"))
                 .reset_index())
    tendencia["rendimiento"] = (tendencia["produccion"] /
                                tendencia["cosechada"].replace(0, 1)).round(2)

    return {
        "kpis": [
            {"label": "Produccion", "value": f"{prod_l:,.0f} t",
             "delta": f"{_pct(prod_l, prod_p):+.1f}%"},
            {"label": "Area", "value": f"{area_l:,.0f} ha",
             "delta": f"{_pct(area_l, area_p):+.1f}%"},
            {"label": "Rendimiento", "value": f"{rend_l:.1f} t/ha",
             "delta": f"{_pct(rend_l, rend_p):+.1f}%"},
            {"label": "Municipios", "value": str(int(df["municipio"].nunique())),
             "delta": None},
            {"label": "Cultivos", "value": str(int(df["cultivo"].nunique())),
             "delta": None},
        ],
        "concentracion": {"hhi": hhi, "gini": gini, "top1": top1_name,
                          "top1_pct": top1_pct},
        "tendencia": tendencia,
        "top_cultivos": df.groupby("cultivo")["produccion_t"].sum()
                         .sort_values(ascending=False).head(6).reset_index(),
        "top_municipios": df.groupby("municipio")["produccion_t"].sum()
                           .sort_values(ascending=False).head(6).reset_index(),
        "crecen": crecen, "declinan": declinan,
        "mensajes": mensajes,
        "alertas": generate_alerts(df)[:5],
        "anos": anos,
    }
'''

Path("core/analytics/executive.py").write_text(EXEC, encoding="utf-8")
print("[OK] core/analytics/executive.py")
print("\nRecarga Streamlit (Ctrl+R).")