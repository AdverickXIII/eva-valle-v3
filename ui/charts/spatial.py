"""Graficos espaciales: Heatmap LQ y Shannon-Wiener."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from ui.charts.theme import PALETTE, apply_theme

def plot_lq_heatmap(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    muni_grupo = (df.groupby(["codigo_dane_municipio","grupo_cultivo"])["area_sembrada_ha"]
        .sum().unstack(fill_value=0))
    valle_grupo = df.groupby("grupo_cultivo")["area_sembrada_ha"].sum()
    valle_grupo_safe = valle_grupo.replace(0, 1e-8)
    muni_total_safe = muni_grupo.sum(axis=1).replace(0, 1e-8)
    lq_df = (muni_grupo/muni_total_safe.values[:,None])/(valle_grupo_safe/valle_grupo_safe.sum())
    top_municipios = df.groupby("codigo_dane_municipio")["area_sembrada_ha"].sum().nlargest(top_n).index
    lq_plot = lq_df.loc[top_municipios]
    fig = go.Figure()
    fig.add_trace(go.Heatmap(z=lq_plot.values,x=lq_plot.columns,
        y=[str(m) for m in lq_plot.index],colorscale="YlOrRd",
        text=np.round(lq_plot.values,1),texttemplate="%{text}",
        colorbar=dict(title="LQ")))
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=600)
    return apply_theme(fig, f"Especializacion Territorial (LQ) - Top {top_n} Municipios")

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
