"""Setup charts parte 1: theme, historical, distributions, growth."""
from pathlib import Path

THEME = '''"""Tema visual para graficos Plotly."""
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
'''

HISTORICAL = '''"""Graficos historicos: areas vs produccion y rendimiento."""
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
    return apply_theme(fig, "Evolucion Historica del Valle del Cauca (2019-2024)")

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
'''

DISTRIBUTIONS = '''"""Graficos de distribuciones log."""
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
'''

GROWTH = '''"""Graficos de crecimiento: CAGR divergente."""
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
'''

if __name__ == "__main__":
    archivos = {
        "ui/charts/theme.py": THEME,
        "ui/charts/historical.py": HISTORICAL,
        "ui/charts/distributions.py": DISTRIBUTIONS,
        "ui/charts/growth.py": GROWTH,
    }
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
    print("Parte 1 completada. Ejecuta ahora: python scripts\\setup_charts_part2.py")