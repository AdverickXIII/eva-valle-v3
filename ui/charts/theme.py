"""Tema visual para graficos Plotly."""
from __future__ import annotations
import plotly.graph_objects as go

PRIMARY_COLOR = "#2E8B57"
BACKGROUND_COLOR = "#0E1117"
SECONDARY_BG = "#1A1F2E"
TEXT_COLOR = "#FAFAFA"
GRID_COLOR = "#2A2F3E"
PALETTE = ["#2E8B57","#4A90D9","#E67E22","#9B59B6","#E74C3C","#1ABC9C","#F39C12","#3498DB"]
COLOR_POSITIVO = "#2E8B57"
COLOR_NEGATIVO = "#E74C3C"

def apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=TEXT_COLOR), x=0.5, xanchor="center"),
        paper_bgcolor=BACKGROUND_COLOR, plot_bgcolor=SECONDARY_BG,
        font=dict(color=TEXT_COLOR, family="Arial, sans-serif"),
        margin=dict(l=60, r=40, t=80, b=60), hovermode="closest",
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, color=TEXT_COLOR)
    return fig
