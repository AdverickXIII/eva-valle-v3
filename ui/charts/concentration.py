"""Graficos de concentracion: Pareto y donas ex-cana."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config.constants import GRUPO_CULTIVO_CANA
from ui.charts.theme import PALETTE, apply_theme

def plot_pareto_concentracion(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    cult_prod = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    top = cult_prod.head(top_n)
    acumulado = top.cumsum() / cult_prod.sum() * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=top.index,y=top.values,name="Produccion Total (t)",
        marker_color=PALETTE[:top_n]), secondary_y=False)
    fig.add_trace(go.Scatter(x=top.index,y=acumulado.values,mode="lines+markers",
        name="% Acumulado",line=dict(color="#E74C3C",width=2),
        marker=dict(size=8)), secondary_y=True)
    fig.add_hline(y=80,line_dash="dash",line_color="gray",secondary_y=True)
    fig.update_yaxes(title_text="Produccion Total (t)", secondary_y=False)
    fig.update_yaxes(title_text="Porcentaje Acumulado (%)",range=[0,105], secondary_y=True)
    fig.update_xaxes(tickangle=45)
    return apply_theme(fig, "Concentracion de la Produccion: Diagrama de Pareto")

def plot_ex_cana_donuts(df: pd.DataFrame) -> go.Figure:
    con_cana = df.groupby("grupo_cultivo")["produccion_t"].sum().sort_values(ascending=False)
    sin_cana = (df[df["grupo_cultivo"]!=GRUPO_CULTIVO_CANA]
        .groupby("grupo_cultivo")["produccion_t"].sum().sort_values(ascending=False))
    fig = make_subplots(rows=1,cols=2,specs=[[{"type":"pie"},{"type":"pie"}]],
        subplot_titles=["Matriz CON Cana de Azucar","Matriz SIN Cana de Azucar"])
    fig.add_trace(go.Pie(labels=con_cana.index,values=con_cana.values,hole=0.4,
        name="Con Cana",marker=dict(colors=PALETTE),textinfo="label+percent"),
        row=1,col=1)
    top5 = sin_cana.head(5)
    otros = pd.Series({"Otros": sin_cana[5:].sum()})
    sin_cana_plot = pd.concat([top5, otros])
    fig.add_trace(go.Pie(labels=sin_cana_plot.index,values=sin_cana_plot.values,hole=0.4,
        name="Sin Cana",marker=dict(colors=PALETTE[:len(sin_cana_plot)]),
        textinfo="label+percent"), row=1,col=2)
    return apply_theme(fig, "Analisis Ex-Cana: Revelando la Matriz Oculta del Valle")
