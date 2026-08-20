"""Graficos de series de tiempo: serie+tendencia, shocks y estacionalidad A/B."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ui.charts.theme import apply_theme


def _serie_anual(df: pd.DataFrame):
    s = df.groupby("ano")["produccion_t"].sum().sort_index()
    x = s.index.astype(int).values
    xc = x - x.min()
    y = s.values.astype(float)
    coef = np.polyfit(xc, y, 1)
    trend = np.polyval(coef, xc)
    return x, y, trend


def plot_serie_produccion(df: pd.DataFrame) -> go.Figure:
    x, y, trend = _serie_anual(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers",
                             name="Produccion observada",
                             line=dict(color="#2E8B57", width=3),
                             marker=dict(size=9)))
    fig.add_trace(go.Scatter(x=x, y=trend, mode="lines",
                             name="Tendencia lineal",
                             line=dict(color="#94A3B8", dash="dash", width=2)))
    fig.update_layout(yaxis_title="Produccion (t)", xaxis_title="Ano",
                      yaxis_tickformat="~s", hovermode="x unified",
                      margin=dict(t=40, b=10))
    return apply_theme(fig, "Serie anual de produccion y su tendencia")


def plot_shocks(df: pd.DataFrame) -> go.Figure:
    x, y, trend = _serie_anual(df)
    resid = (y - trend) / trend * 100
    colors = ["#D62728" if abs(r) > 2 else "#52B788" for r in resid]
    fig = go.Figure(go.Bar(x=x, y=resid, marker_color=colors,
                           hovertemplate="Ano %{x}<br>Desviacion: %{y:.2f}%<extra></extra>"))
    fig.add_hline(y=0, line_color="gray")
    fig.update_layout(yaxis_title="Desviacion vs tendencia (%)",
                      showlegend=False, margin=dict(t=40, b=10))
    return apply_theme(fig, "Shocks: anos que se salieron de la tendencia")


def plot_estacionalidad_ab(df_est: pd.DataFrame) -> go.Figure:
    d = df_est.sort_values("dif_porcent", key=abs, ascending=False).head(12)
    d = d.sort_values("dif_porcent")
    colors = ["#2E8B57" if s else "#ADB5BD" for s in d["diferencia_significativa"]]
    fig = go.Figure(go.Bar(y=d["cultivo"], x=d["dif_porcent"], orientation="h",
                           marker_color=colors,
                           hovertemplate="%{y}<br>B vs A: %{x:.1f}%<extra></extra>"))
    fig.add_vline(x=0, line_color="gray")
    fig.update_layout(xaxis_title="Diferencia semestre B vs A (%)",
                      yaxis=dict(autorange="reversed"), showlegend=False,
                      margin=dict(t=40, b=10, l=10))
    return apply_theme(fig, "Estacionalidad: cultivos con diferencia significativa A vs B")
