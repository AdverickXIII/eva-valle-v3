"""Graficos de crecimiento: CAGR divergente."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from ui.charts.theme import COLOR_NEGATIVO, COLOR_POSITIVO, apply_theme

def plot_cagr_divergente(df: pd.DataFrame, min_prod: float = 1000) -> go.Figure:
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2: return go.Figure()
    ano_ini, ano_fin = min(anos), max(anos)
    n_years = ano_fin - ano_ini
    ini = df[df["ano"]==ano_ini].groupby("cultivo")["produccion_t"].sum()
    fin = df[df["ano"]==ano_fin].groupby("cultivo")["produccion_t"].sum()
    cagr_df = pd.DataFrame({"prod_inicio":ini,"prod_fin":fin}).dropna()
    cagr_df = cagr_df[cagr_df["prod_inicio"]>0]
    cagr_df["cagr"] = ((cagr_df["prod_fin"]/cagr_df["prod_inicio"])**(1/n_years)-1)*100
    cagr_df = cagr_df[cagr_df["prod_inicio"]>min_prod].sort_values("cagr")
    colors = [COLOR_POSITIVO if x>0 else COLOR_NEGATIVO for x in cagr_df["cagr"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cagr_df["cagr"],y=cagr_df.index,orientation="h",
        marker_color=colors,text=[f"{v:.1f}%" for v in cagr_df["cagr"]],
        textposition="outside"))
    fig.add_vline(x=0,line_color="white",line_width=1)
    fig.update_xaxes(title_text="CAGR (%) 2019-2024")
    fig.update_layout(height=600)
    return apply_theme(fig, f"CAGR por Cultivo (Filtro: > {min_prod:,.0f} t)")
