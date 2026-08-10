"""Graficos historicos: areas vs produccion y rendimiento."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.charts.theme import COLOR_POSITIVO, PALETTE, apply_theme

def plot_historico_cruces(df: pd.DataFrame) -> go.Figure:
    hist = df.groupby("ano").agg(
        sembrada=("area_sembrada_ha","sum"),
        cosechada=("area_cosechada_ha","sum"),
        produccion=("produccion_t","sum"),
    ).reset_index()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=hist["ano"],y=hist["sembrada"],fill="tonexty",
        fillcolor="rgba(231,76,60,0.15)",name="Brecha de Perdida (ha)",
        line=dict(width=0),hoverinfo="skip"), secondary_y=False)
    fig.add_trace(go.Scatter(x=hist["ano"],y=hist["sembrada"],mode="lines+markers",
        name="Area Sembrada (ha)",line=dict(color=PALETTE[1],width=3),
        marker=dict(size=8)), secondary_y=False)
    fig.add_trace(go.Scatter(x=hist["ano"],y=hist["cosechada"],mode="lines+markers",
        name="Area Cosechada (ha)",line=dict(color=PALETTE[2],width=3),
        marker=dict(size=8,symbol="square")), secondary_y=False)
    fig.add_trace(go.Scatter(x=hist["ano"],y=hist["produccion"],mode="lines+markers",
        name="Produccion (t)",line=dict(color=COLOR_POSITIVO,width=3,dash="dash"),
        marker=dict(size=8,symbol="triangle-up")), secondary_y=True)
    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig.update_yaxes(title_text="Hectareas (ha)", secondary_y=False)
    fig.update_yaxes(title_text="Toneladas (t)", secondary_y=True)
    return apply_theme(fig, "Evolucion Historica del Valle del Cauca (2019-2025)")

def plot_rendimiento_historico(df: pd.DataFrame) -> go.Figure:
    hist = df.groupby("ano").agg(
        produccion=("produccion_t","sum"),cosechada=("area_cosechada_ha","sum"),
    ).reset_index()
    hist["rendimiento"] = hist["produccion"] / hist["cosechada"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=hist["ano"],y=hist["rendimiento"],name="Rendimiento (t/ha)",
        marker_color="rgba(74,144,217,0.6)",
        text=[f"{v:.1f}" for v in hist["rendimiento"]],textposition="outside"))
    fig.add_trace(go.Scatter(x=hist["ano"],y=hist["rendimiento"],mode="lines+markers",
        name="Tendencia",line=dict(color="#E74C3C",width=2),marker=dict(size=8)))
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(title_text="Toneladas por Hectarea")
    return apply_theme(fig, "Evolucion del Rendimiento Promedio Departamental (t/ha)")
