"""Graficos espaciales: Heatmap LQ y Shannon-Wiener."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from ui.charts.theme import PALETTE, apply_theme

def plot_lq_heatmap(df: pd.DataFrame, top_n: int = 15, excluye_cana: bool = True) -> go.Figure:
    """Heatmap LQ legible: municipios en Y, grupos en X, un valor por celda."""
    df_sin = df[df["cultivo"] != "Caña"] if excluye_cana else df
    mg = df_sin.groupby(["municipio", "grupo_cultivo"])["produccion_t"].sum()
    m_tot = df_sin.groupby("municipio")["produccion_t"].sum()
    g_tot = df_sin.groupby("grupo_cultivo")["produccion_t"].sum()
    total = float(df_sin["produccion_t"].sum())

    rows = []
    for (m, g), v in mg.items():
        sm = v / m_tot[m] * 100 if m_tot[m] else 0.0
        sd = g_tot[g] / total * 100 if total else 0.0
        if sd > 0 and v > 0:
            rows.append({"municipio": m, "grupo": g, "lq": sm / sd})
    d = pd.DataFrame(rows)

    top_m = m_tot.sort_values(ascending=False).head(top_n).index.tolist()
    piv = (d[d["municipio"].isin(top_m)]
           .pivot_table(index="municipio", columns="grupo", values="lq", fill_value=0)
           .reindex(top_m))

    fig = go.Figure(go.Heatmap(
        z=piv.values,
        x=piv.columns.tolist(),
        y=piv.index.tolist(),
        xgap=2, ygap=2,
        colorscale="YlOrRd", zmin=0, zmax=5,
        colorbar=dict(title="LQ"),
        hovertemplate="%{y} · %{x}<br>LQ = %{z:.2f}<extra></extra>"))

    fig = apply_theme(fig, "Especializacion Territorial (LQ) - Top 15 Municipios")

    # Un solo numero por celda, con contraste segun fondo
    for i, m in enumerate(piv.index):
        for j, g in enumerate(piv.columns):
            v = float(piv.iloc[i, j])
            fig.add_annotation(
                x=g, y=m,
                text=f"{v:.1f}" if v >= 0.05 else "",
                showarrow=False,
                font=dict(size=9, color="white" if v >= 2.5 else "black"))

    fig.update_layout(
        yaxis=dict(type="category", autorange="reversed",
                   tickfont=dict(size=10), title_text=""),
        xaxis=dict(tickangle=-35, type="category"),
        height=560, margin=dict(t=40, b=10, l=10, r=10))
    return fig



def plot_shannon_barras(df: pd.DataFrame, min_area: float = 1000) -> go.Figure:
    def shannon_index(s):
        p = s/s.sum(); p = p[p>0]
        return float(-np.sum(p*np.log(p)))
    diversidad = df.groupby("municipio")["area_sembrada_ha"].agg(
        shannon=shannon_index, area_total="sum").reset_index()
    diversidad = diversidad[diversidad["area_total"]>min_area].sort_values("shannon")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=diversidad["shannon"],y=diversidad["municipio"],
        orientation="h",marker_color=PALETTE[0],
        text=[f"{v:.2f}" for v in diversidad["shannon"]],textposition="outside"))
    fig.update_xaxes(title_text="Indice Shannon-Wiener")
    fig.update_layout(height=600)
    return apply_theme(fig, "Indice de Diversificacion Shannon-Wiener por Municipio")
