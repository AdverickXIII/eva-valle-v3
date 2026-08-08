"""Graficos de distribuciones log."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.charts.theme import PALETTE, apply_theme

def plot_distribuciones_log(df: pd.DataFrame) -> go.Figure:
    metricas = ["area_sembrada_ha","area_cosechada_ha","produccion_t","rendimiento_t_ha"]
    titulos = ["Area Sembrada (ha)","Area Cosechada (ha)","Produccion (t)","Rendimiento (t/ha)"]
    fig = make_subplots(rows=2,cols=2,subplot_titles=titulos,
        horizontal_spacing=0.08,vertical_spacing=0.12)
    posiciones = [(1,1),(1,2),(2,1),(2,2)]
    for i,(col,titulo) in enumerate(zip(metricas,titulos)):
        if col not in df.columns: continue
        data = df[col].dropna(); data = data[data > 0]
        row,col_pos = posiciones[i]
        fig.add_trace(go.Histogram(x=data,nbinsx=50,name=titulo,
            marker_color=PALETTE[i%len(PALETTE)],opacity=0.75,showlegend=False),
            row=row,col=col_pos)
        fig.update_xaxes(type="log", row=row, col=col_pos)
    return apply_theme(fig, "Distribuciones Logaritmicas de Metricas Productivas")
