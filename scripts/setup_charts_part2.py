"""Setup charts parte 2: concentration, spatial, diagnostics, __init__."""
from pathlib import Path

CONCENTRATION = '''"""Graficos de concentracion: Pareto y donas ex-cana."""
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
'''

SPATIAL = '''"""Graficos espaciales: Heatmap LQ y Shannon-Wiener."""
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
'''

DIAGNOSTICS = '''"""Graficos de diagnostico: correlacion y scatter."""
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
'''

CHARTS_INIT = '''"""Modulo de visualizaciones interactivas con Plotly."""
from ui.charts.historical import plot_historico_cruces, plot_rendimiento_historico
from ui.charts.distributions import plot_distribuciones_log
from ui.charts.concentration import plot_pareto_concentracion, plot_ex_cana_donuts
from ui.charts.growth import plot_cagr_divergente
from ui.charts.spatial import plot_lq_heatmap, plot_shannon_barras
from ui.charts.diagnostics import plot_correlation_heatmap, plot_scatter_bivariado

__all__ = [
    "plot_historico_cruces","plot_rendimiento_historico","plot_distribuciones_log",
    "plot_pareto_concentracion","plot_ex_cana_donuts","plot_cagr_divergente",
    "plot_lq_heatmap","plot_shannon_barras","plot_correlation_heatmap",
    "plot_scatter_bivariado",
]
'''

if __name__ == "__main__":
    archivos = {
        "ui/charts/concentration.py": CONCENTRATION,
        "ui/charts/spatial.py": SPATIAL,
        "ui/charts/diagnostics.py": DIAGNOSTICS,
        "ui/charts/__init__.py": CHARTS_INIT,
    }
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
    print("Parte 2 completada. Todos los graficos creados.")