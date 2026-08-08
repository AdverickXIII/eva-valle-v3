"""Tema visual claro para graficos Plotly."""
from __future__ import annotations
import plotly.graph_objects as go

PRIMARY_COLOR = "#2E8B57"
BACKGROUND_COLOR = "#FFFFFF"
SECONDARY_BG = "#F8F9FA"
TEXT_COLOR = "#1A202C"
GRID_COLOR = "#E2E8F0"
PALETTE = ["#2E8B57","#3182CE","#DD6B20","#805AD5","#E53E3E","#319795","#D69E2E","#3182CE"]
COLOR_POSITIVO = "#2F855A"
COLOR_NEGATIVO = "#C53030"

def apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=TEXT_COLOR), x=0.5),
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=SECONDARY_BG,
        font=dict(color=TEXT_COLOR, family="Arial, sans-serif"),
        margin=dict(l=60, r=40, t=80, b=60),
        hovermode="closest",
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, color=TEXT_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, color=TEXT_COLOR)
    return fig
