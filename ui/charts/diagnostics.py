"""Graficos de diagnostico: correlacion y scatter."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from ui.charts.theme import PALETTE, apply_theme

def plot_correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Heatmap(z=corr_matrix.values,x=corr_matrix.columns,
        y=corr_matrix.index,colorscale="RdBu",zmin=-1,zmax=1,
        text=np.round(corr_matrix.values,2),texttemplate="%{text}",
        colorbar=dict(title="Correlacion")))
    return apply_theme(fig, "Matriz de Correlacion (Spearman)")

def plot_scatter_bivariado(df, x_col, y_col, color_col=None, log_scale=True, title=""):
    fig = go.Figure()
    if color_col and color_col in df.columns:
        for i, cat in enumerate(df[color_col].unique()):
            subset = df[df[color_col]==cat]
            fig.add_trace(go.Scatter(x=subset[x_col],y=subset[y_col],mode="markers",
                name=str(cat),marker=dict(color=PALETTE[i%len(PALETTE)],size=6,opacity=0.6)))
    else:
        fig.add_trace(go.Scatter(x=df[x_col],y=df[y_col],mode="markers",
            marker=dict(color=PALETTE[0],size=6,opacity=0.6)))
    if log_scale:
        fig.update_xaxes(type="log"); fig.update_yaxes(type="log")
    fig.update_xaxes(title_text=x_col); fig.update_yaxes(title_text=y_col)
    return apply_theme(fig, title or f"{x_col} vs {y_col}")
