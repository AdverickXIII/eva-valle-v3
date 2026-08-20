"""Diagnostico por cultivo: serie, motor CAGR con leyenda, elasticidad y top municipios."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.charts.theme import apply_theme


def diagnostic_subset(sub: pd.DataFrame, total_ref: float) -> dict:
    agg = (sub.groupby("ano")
           .agg(p=("produccion_t", "sum"), a=("area_sembrada_ha", "sum"),
                c=("area_cosechada_ha", "sum"))
           .sort_index())
    agg = agg[(agg.p > 0) & (agg.c > 0)]
    f, l = agg.iloc[0], agg.iloc[-1]
    n = max(len(agg) - 1, 1)
    cagr_p = ((l.p / f.p) ** (1 / n) - 1) * 100
    cagr_a = ((l.a / f.a) ** (1 / n) - 1) * 100 if (l.a > 0 and f.a > 0) else 0.0
    cagr_r = (((l.p / l.c) / (f.p / f.c)) ** (1 / n) - 1) * 100

    elast = None
    area_varia = bool(agg.a.max() / agg.a.min() >= 1.15) if (agg.a > 0).all() else False
    if len(agg) >= 4 and agg.a.nunique() > 1 and area_varia:
        elast = float(np.polyfit(np.log(agg.a.values), np.log(agg.p.values), 1)[0])

    prod_total = sub["produccion_t"].sum()
    if cagr_p <= -5:
        tipo = "Colapso"
    elif cagr_a > 2 and cagr_r > 2:
        tipo = "Expansion con tecnologia"
    elif cagr_a > 2:
        tipo = "Expansion extensiva"
    elif cagr_r > 2:
        tipo = "Intensificacion"
    else:
        tipo = "Estable"

    top_mun = (sub.groupby("municipio")["produccion_t"].sum()
               .sort_values(ascending=False).head(5))
    top_df = pd.DataFrame({"municipio": top_mun.index, "produccion_t": top_mun.values})
    top_df["share_pct"] = (top_df["produccion_t"] / prod_total * 100).round(1)

    narrativa = (
        f"{prod_total:,.0f} t acumuladas "
        f"({prod_total / total_ref * 100:.1f}% del ambito de referencia). "
        f"CAGR {cagr_p:+.1f}% anual. "
        f"Motor: {tipo.lower()} (area {cagr_a:+.1f}% / rendimiento {cagr_r:+.1f}%). "
    )
    if elast is not None:
        narrativa += (f"Elasticidad area-produccion ≈ {elast:.2f}: "
                      + ("crecimiento sensible al area (extensivo)."
                         if elast > 0.8
                         else "crecimiento poco dependiente del area (intensivo)."))
    else:
        narrativa += "Elasticidad no concluyente (pocos anos o area casi constante); el motor se lee por los CAGR de area y rendimiento."

    return {"prod_total": prod_total, "cagr_prod": cagr_p, "cagr_area": cagr_a,
            "cagr_rend": cagr_r, "tipo": tipo, "elasticidad": elast,
            "top_mun": top_df, "narrativa": narrativa, "agg": agg}


def crop_diagnostic(df: pd.DataFrame, cultivo: str) -> dict:
    d = diagnostic_subset(df[df["cultivo"] == cultivo], df["produccion_t"].sum())
    d["narrativa"] = f"**{cultivo}**: " + d["narrativa"]
    return d


def plot_crop_serie(diag: dict, titulo: str):
    agg = diag["agg"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Produccion (t)", "Rendimiento (t/ha)"],
                        vertical_spacing=0.12)
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p, mode="lines+markers",
                             line=dict(color="#2E8B57", width=3), name="Produccion"), 1, 1)
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p / agg.c, mode="lines+markers",
                             line=dict(color="#5FA8DC", width=2), name="Rendimiento"), 2, 1)
    fig.update_layout(height=480, margin=dict(t=40, b=10), showlegend=False,
                      xaxis_title="Ano")
    return apply_theme(fig, titulo)


def plot_crop_motor(diag: dict):
    vals = [diag["cagr_prod"], diag["cagr_area"], diag["cagr_rend"]]
    labs = ["CAGR produccion", "CAGR area", "CAGR rendimiento"]
    fig = go.Figure()
    for lab, v in zip(labs, vals):
        fig.add_trace(go.Bar(x=[v], y=[lab], orientation="h", name=lab,
                             marker_color="#2E8B57" if v >= 0 else "#D62728",
                             text=[f"{v:+.1f}%"], textposition="outside"))
    fig.add_vline(x=0, line_color="gray")
    fig.update_layout(barmode="group", showlegend=True,
                      legend=dict(orientation="h", y=-0.25),
                      margin=dict(t=40, b=10, l=10), height=420,
                      xaxis_title="CAGR (%)")
    return apply_theme(fig, "Motor del crecimiento (leyenda por componente)")


def plot_top_municipios(sub: pd.DataFrame, cultivo: str):
    top = sub.groupby("municipio")["produccion_t"].sum().sort_values(ascending=False).head(10)
    fig = go.Figure(go.Bar(x=top.values, y=top.index, orientation="h",
                           marker_color="#2E8B57",
                           text=[f"{v:,.0f} t" for v in top.values],
                           textposition="outside"))
    fig.update_layout(margin=dict(t=40, b=10, l=10), height=420,
                      xaxis_title="Produccion acumulada (t)", showlegend=False)
    return apply_theme(fig, f"Top 10 municipios en {cultivo}")


def plot_crop_indice(diag: dict, titulo: str):
    """Lineas indexadas 2019=100: produccion vs area vs rendimiento."""
    agg = diag["agg"]
    base_p = float(agg.p.iloc[0])
    base_a = float(agg.a.iloc[0])
    base_r = float((agg.p / agg.c).iloc[0])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p / base_p * 100,
                             mode="lines+markers", name="Produccion",
                             line=dict(color="#2E8B57", width=3)))
    fig.add_trace(go.Scatter(x=agg.index, y=agg.a / base_a * 100,
                             mode="lines+markers", name="Area sembrada",
                             line=dict(color="#F4A261", width=2)))
    fig.add_trace(go.Scatter(x=agg.index, y=(agg.p / agg.c) / base_r * 100,
                             mode="lines+markers", name="Rendimiento",
                             line=dict(color="#5FA8DC", width=2)))
    fig.add_hline(y=100, line_dash="dash", line_color="gray")
    fig.update_layout(yaxis_title="Indice (2019=100)", height=460,
                      legend=dict(orientation="h", y=-0.15),
                      hovermode="x unified", margin=dict(t=40, b=10))
    return apply_theme(fig, titulo)
