"""Generacion de alertas inteligentes sobre el dataset agricola."""
from __future__ import annotations

import pandas as pd


def _concentracion(df: pd.DataFrame):
    g = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=True)
    shares = g / g.sum() * 100
    hhi = float((shares ** 2).sum())
    top1 = float(g.iloc[-1] / g.sum() * 100)
    return hhi, top1


def _cagr_por_cultivo(df: pd.DataFrame, min_prod: float = 1000.0) -> pd.DataFrame:
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


def _caida_municipios(df: pd.DataFrame, umbral: float = -20.0):
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2:
        return []
    a, b = int(anos[-2]), int(anos[-1])
    pa = df[df["ano"] == a].groupby("municipio")["produccion_t"].sum()
    pb = df[df["ano"] == b].groupby("municipio")["produccion_t"].sum()
    out = []
    for m in pa.index:
        if m in pb.index and pa[m] > 0:
            var = (pb[m] / pa[m] - 1) * 100
            if var <= umbral:
                out.append((m, float(var)))
    return out


def generate_alerts(df: pd.DataFrame) -> list:
    """Genera lista de alertas ordenadas por severidad."""
    alerts = []

    hhi, top1 = _concentracion(df)
    if hhi > 2500:
        alerts.append(dict(severidad="ALERTA",
            titulo="Concentracion extrema de produccion",
            detalle=f"HHI={hhi:,.0f} (>2,500). El cultivo lider aporta {top1:.1f}% "
                    f"de la produccion departamental. Riesgo por monocultivo."))

    for _, r in _cagr_por_cultivo(df).iterrows():
        if r["cagr"] <= -5:
            alerts.append(dict(severidad="ALERTA",
                titulo=f"{r['cultivo']}: declive sostenido",
                detalle=f"CAGR {r['cagr']:.1f}% en el periodo. Revisar competitividad."))
        elif r["cagr"] < 0:
            alerts.append(dict(severidad="AVISO",
                titulo=f"{r['cultivo']}: tendencia a la baja",
                detalle=f"CAGR {r['cagr']:.1f}%. Vigilar evolucion."))
        elif r["cagr"] >= 15:
            alerts.append(dict(severidad="DESTAQUE",
                titulo=f"{r['cultivo']}: oportunidad de crecimiento",
                detalle=f"CAGR +{r['cagr']:.1f}%. Candidato a incentivo/inversion."))

    for m, var in _caida_municipios(df):
        alerts.append(dict(severidad="AVISO",
            titulo=f"{m}: caida de produccion",
            detalle=f"{var:.1f}% entre los dos ultimos anos."))

    orden = {"ALERTA": 0, "AVISO": 1, "DESTAQUE": 2}
    alerts.sort(key=lambda x: orden[x["severidad"]])
    return alerts
