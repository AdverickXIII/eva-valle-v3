"""Analisis de concentracion dual (con/sin cana), territorial y calidad."""
from __future__ import annotations

import unicodedata

import pandas as pd

from core.reports.crop_data import _gini


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _is_cana(nombre: str) -> bool:
    return "cana" in _norm(nombre)


def pareto(df: pd.DataFrame, exclude_cana: bool = False, top_n: int = 12) -> pd.DataFrame:
    d = df.copy()
    if exclude_cana:
        d = d[~d["cultivo"].map(_is_cana)]
    g = d.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    total = g.sum()
    head = g.head(top_n)
    if len(g) > top_n:
        head = pd.concat([head, pd.Series({"Otros": g.iloc[top_n:].sum()})])
    dfp = head.reset_index()
    dfp.columns = ["cultivo", "produccion"]
    dfp["share"] = (dfp["produccion"] / total * 100).round(1)
    dfp["cum"] = dfp["share"].cumsum().round(1)
    return dfp


def conc_metrics(df: pd.DataFrame, exclude_cana: bool = False) -> dict:
    d = df[~df["cultivo"].map(_is_cana)] if exclude_cana else df
    g = d.groupby("cultivo")["produccion_t"].sum()
    g = g[g > 0].sort_values(ascending=True)
    shares = g / g.sum() * 100
    desc = g.sort_values(ascending=False)
    cum = (desc / desc.sum() * 100).cumsum()
    n80 = int((cum < 80).sum() + 1)
    return {
        "hhi": round(float((shares ** 2).sum()), 0),
        "gini": round(_gini(g.values), 3),
        "top1_pct": round(float(shares.max()), 1),
        "top1": str(desc.idxmax()),
        "n80": n80,
        "cultivos": int(len(g)),
    }


def territorial(df: pd.DataFrame) -> dict:
    g = df.groupby("municipio")["produccion_t"].sum()
    g = g[g > 0]
    shares = g / g.sum() * 100
    return {
        "gini": round(_gini(g.values), 3),
        "hhi": round(float((shares ** 2).sum()), 0),
        "top": str(g.idxmax()),
        "top_pct": round(float(shares.max()), 1),
        "municipios": int(len(g)),
    }


def tiering(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False)
    q66, q33 = g.quantile(0.66), g.quantile(0.33)
    rows = []
    for m, v in g.items():
        t = "Lider" if v >= q66 else ("Intermedio" if v >= q33 else "Rezagado")
        rows.append((m, round(float(v), 0), t))
    return pd.DataFrame(rows, columns=["municipio", "produccion", "tier"])


def quality(df: pd.DataFrame) -> dict:
    total = len(df)
    anom = int((df["area_cosechada_ha"] > df["area_sembrada_ha"]).sum())
    nulos = int(df[["produccion_t", "area_sembrada_ha", "area_cosechada_ha"]]
                .isna().any(axis=1).sum())
    return {
        "registros": total,
        "pct_anomalia": round(anom / total * 100, 2),
        "pct_nulos": round(nulos / total * 100, 2),
        "fuente": "UPRA - EVA (autodeclaracion municipal)",
        "cobertura": "42 municipios, 2019-2025",
    }


def recomendaciones(df: pd.DataFrame) -> list:
    cc = conc_metrics(df, exclude_cana=False)
    sc = conc_metrics(df, exclude_cana=True)
    ter = territorial(df)
    recs = []
    if cc["hhi"] > 2500:
        recs.append(("Diversificacion productiva",
                     f"Con cana, HHI={cc['hhi']:,.0f} (monocultivo). Sin cana, HHI="
                     f"{sc['hhi']:,.0f}: hay base para diversificar hacia cultivos de "
                     f"mayor valor."))
    if ter["gini"] >= 0.5:
        recs.append(("Priorizacion territorial",
                     f"Gini territorial={ter['gini']:.2f}: la produccion se concentra en "
                     f"pocos municipios ({ter['top']} lidera con {ter['top_pct']:.1f}%). "
                     f"Focalizar inversion en municipios intermedios/rezagados."))
    recs.append(("Separar lectura caña vs resto",
                 "Reportar siempre ambos escenarios: la cana domina el tonelaje, pero la "
                 "economia agricola no-canera tiene dinamica propia (frutas, exportacion)."))
    recs.append(("Mejora de calidad del dato",
                 "Declarar anomalias (area cosechada > sembrada) y vacios; validar con "
                 "teledeteccion o aforos en proximos ciclos."))
    return recs
