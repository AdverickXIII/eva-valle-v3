"""Reescribe ui/charts/concentration.py con donuts adaptativos al filtro."""
from pathlib import Path

MOD = '''"""Graficos de concentracion: Pareto y donas ex-cana (adaptativas al filtro)."""
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
    fig.add_trace(go.Bar(x=top.index, y=top.values, name="Produccion Total (t)",
        marker_color=PALETTE[:top_n]), secondary_y=False)
    fig.add_trace(go.Scatter(x=top.index, y=acumulado.values, mode="lines+markers",
        name="% Acumulado", line=dict(color="#E74C3C", width=2),
        marker=dict(size=8)), secondary_y=True)
    fig.add_hline(y=80, line_dash="dash", line_color="gray", secondary_y=True)
    fig.update_yaxes(title_text="Produccion Total (t)", secondary_y=False)
    fig.update_yaxes(title_text="Porcentaje Acumulado (%)", range=[0, 105],
                     secondary_y=True)
    fig.update_xaxes(tickangle=45)
    return apply_theme(fig, "Concentracion de la Produccion: Diagrama de Pareto")


def plot_ex_cana_donuts(df: pd.DataFrame) -> go.Figure:
    grupos = df["grupo_cultivo"].dropna().unique()
    tiene_cana = GRUPO_CULTIVO_CANA in grupos
    multi_grupo = len(grupos) > 1

    # --- Modo adaptativo: filtro deja 1 grupo o excluye la cana ---
    if not (tiene_cana and multi_grupo):
        cult = (df.groupby("cultivo")["produccion_t"].sum()
                .sort_values(ascending=False))
        top5 = cult.head(5)
        otros = pd.Series({"Otros": cult[5:].sum()})
        data = pd.concat([top5, otros])
        data = data[data > 0]
        contexto = str(grupos[0]) if len(grupos) == 1 else "filtros activos"
        fig = go.Figure(go.Pie(labels=data.index, values=data.values, hole=0.4,
                               textinfo="label+percent",
                               marker=dict(colors=PALETTE[:len(data)])))
        fig = apply_theme(fig, f"Composicion por cultivo - {contexto}")
        fig.add_annotation(
            text="Con este filtro la comparacion CON/SIN cana no aplica: "
                 "se muestra la composicion interna por cultivo.",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="#666666"))
        return fig

    # --- Vista departamental: dual CON/SIN cana ---
    con_cana = (df.groupby("grupo_cultivo")["produccion_t"].sum()
                .sort_values(ascending=False))
    sin_cana = (df[df["grupo_cultivo"] != GRUPO_CULTIVO_CANA]
                .groupby("grupo_cultivo")["produccion_t"].sum()
                .sort_values(ascending=False))
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "pie"}, {"type": "pie"}]],
                        subplot_titles=["Matriz CON Cana de Azucar",
                                        "Matriz SIN Cana de Azucar"])
    fig.add_trace(go.Pie(labels=con_cana.index, values=con_cana.values, hole=0.4,
                         name="Con Cana", marker=dict(colors=PALETTE),
                         textinfo="label+percent"), row=1, col=1)
    top5 = sin_cana.head(5)
    otros = pd.Series({"Otros": sin_cana[5:].sum()})
    sin_cana_plot = pd.concat([top5, otros])
    fig.add_trace(go.Pie(labels=sin_cana_plot.index, values=sin_cana_plot.values,
                         hole=0.4, name="Sin Cana",
                         marker=dict(colors=PALETTE[:len(sin_cana_plot)]),
                         textinfo="label+percent"), row=1, col=2)
    fig = apply_theme(fig, "Analisis Ex-Cana: Revelando la Matriz Oculta del Valle")
    fig.add_annotation(
        text="Nota: HHI, Gini y Top 1 se calculan por CULTIVO; "
             "las donas agregan por GRUPO de cultivo.",
        xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
        font=dict(size=10, color="#666666"))
    return fig
'''

Path("ui/charts/concentration.py").write_text(MOD, encoding="utf-8")
print("[OK] ui/charts/concentration.py (donuts adaptativos)")
print("Recarga: Ctrl+R en el navegador")