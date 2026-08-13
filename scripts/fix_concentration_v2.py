"""Reescribe concentration.py: exclusion por CULTIVO y cana desagregada."""
from pathlib import Path

MOD = '''"""Graficos de concentracion: Pareto y donas ex-cana (adaptativas, exclusion por cultivo)."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui.charts.theme import PALETTE, apply_theme

CULTIVO_CANA = "Caña"


def _colors(n: int) -> list:
    return [PALETTE[i % len(PALETTE)] for i in range(n)]


def plot_pareto_concentracion(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    cult_prod = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    top = cult_prod.head(top_n)
    acumulado = top.cumsum() / cult_prod.sum() * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=top.index, y=top.values, name="Produccion Total (t)",
        marker_color=_colors(top_n)), secondary_y=False)
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
    tiene_cana = (df["cultivo"] == CULTIVO_CANA).any()
    multi_grupo = df["grupo_cultivo"].nunique() > 1

    # --- Modo adaptativo: filtro sin cana o con un solo grupo ---
    if not (tiene_cana and multi_grupo):
        cult = (df.groupby("cultivo")["produccion_t"].sum()
                .sort_values(ascending=False))
        top5 = cult.head(5)
        otros = pd.Series({"Otros": cult[5:].sum()})
        data = pd.concat([top5, otros])
        data = data[data > 0]
        grupos = df["grupo_cultivo"].dropna().unique()
        contexto = str(grupos[0]) if len(grupos) == 1 else "filtros activos"
        fig = go.Figure(go.Pie(labels=data.index, values=data.values, hole=0.4,
                               textinfo="label+percent",
                               marker=dict(colors=_colors(len(data)))))
        fig = apply_theme(fig, f"Composicion por cultivo - {contexto}")
        fig.add_annotation(
            text="Con este filtro la comparacion CON/SIN cana no aplica: "
                 "se muestra la composicion interna por cultivo.",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="#666666"))
        return fig

    # --- Vista departamental ---
    df_sin = df[df["cultivo"] != CULTIVO_CANA]
    cana_prod = df[df["cultivo"] == CULTIVO_CANA]["produccion_t"].sum()

    # CON cana: cana desagregada como etiqueta propia + resto por grupo
    por_grupo = (df_sin.groupby("grupo_cultivo")["produccion_t"].sum()
                 .sort_values(ascending=False))
    labels_con = ["Cana de azucar"] + list(por_grupo.index)
    values_con = [cana_prod] + list(por_grupo.values)

    # SIN cana: por grupo (cafe, cacao y algodon permanecen)
    top5 = por_grupo.head(5)
    otros = pd.Series({"Otros": por_grupo[5:].sum()})
    sin_plot = pd.concat([top5, otros])

    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "pie"}, {"type": "pie"}]],
                        subplot_titles=["Matriz CON Cana (desagregada)",
                                        "Matriz SIN Cana"])
    fig.add_trace(go.Pie(labels=labels_con, values=values_con, hole=0.4,
                         name="Con Cana", marker=dict(colors=_colors(len(labels_con))),
                         textinfo="label+percent"), row=1, col=1)
    fig.add_trace(go.Pie(labels=sin_plot.index, values=sin_plot.values, hole=0.4,
                         name="Sin Cana", marker=dict(colors=_colors(len(sin_plot))),
                         textinfo="label+percent"), row=1, col=2)
    fig = apply_theme(fig, "Analisis Ex-Cana: Revelando la Matriz Oculta del Valle")
    fig.add_annotation(
        text="Nota: HHI, Gini y Top 1 se calculan por CULTIVO; las donas agregan por "
             "GRUPO. La exclusion es por cultivo (Cana), no por grupo.",
        xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
        font=dict(size=10, color="#666666"))
    return fig
'''

Path("ui/charts/concentration.py").write_text(MOD, encoding="utf-8")
print("[OK] concentration.py v2: exclusion por cultivo + cana desagregada")