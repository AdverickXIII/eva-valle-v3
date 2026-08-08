"""
Setup script: genera los 8 archivos del modulo ui/charts/.
Migracion del Notebook 5 (Fabrica de Visualizaciones) a Plotly.
Ejecutar una sola vez: python scripts/setup_charts_module.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: ui/charts/__init__.py
# ═══════════════════════════════════════════════════════════
CHARTS_INIT = '''"""
Modulo de visualizaciones interactivas con Plotly.

Migrado del Notebook 5 (matplotlib/seaborn) a Plotly para
aprovechar la interactividad nativa de Streamlit.

Uso:
    from ui.charts import plot_historico_cruces, plot_pareto_concentracion

    fig = plot_historico_cruces(df)
    st.plotly_chart(fig, use_container_width=True)
"""
from ui.charts.historical import (
    plot_historico_cruces,
    plot_rendimiento_historico,
)
from ui.charts.distributions import plot_distribuciones_log
from ui.charts.concentration import (
    plot_pareto_concentracion,
    plot_ex_cana_donuts,
)
from ui.charts.growth import plot_cagr_divergente
from ui.charts.spatial import (
    plot_lq_heatmap,
    plot_shannon_barras,
)
from ui.charts.diagnostics import (
    plot_correlation_heatmap,
    plot_scatter_bivariado,
)

__all__ = [
    "plot_historico_cruces",
    "plot_rendimiento_historico",
    "plot_distribuciones_log",
    "plot_pareto_concentracion",
    "plot_ex_cana_donuts",
    "plot_cagr_divergente",
    "plot_lq_heatmap",
    "plot_shannon_barras",
    "plot_correlation_heatmap",
    "plot_scatter_bivariado",
]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: ui/charts/theme.py
# ═══════════════════════════════════════════════════════════
THEME = '''"""
Tema visual para graficos Plotly.

Alineado con el tema oscuro de .streamlit/config.toml:
- primaryColor = "#2E8B57"
- backgroundColor = "#0E1117"
- secondaryBackgroundColor = "#1A1F2E"
- textColor = "#FAFAFA"
"""
from __future__ import annotations

import plotly.graph_objects as go

# Colores del tema (alineados con .streamlit/config.toml)
PRIMARY_COLOR = "#2E8B57"
BACKGROUND_COLOR = "#0E1117"
SECONDARY_BG = "#1A1F2E"
TEXT_COLOR = "#FAFAFA"
GRID_COLOR = "#2A2F3E"

# Paleta para graficos categoricos
PALETTE = [
    "#2E8B57",  # Verde mar
    "#4A90D9",  # Azul
    "#E67E22",  # Naranja
    "#9B59B6",  # Purpura
    "#E74C3C",  # Rojo
    "#1ABC9C",  # Turquesa
    "#F39C12",  # Amarillo
    "#3498DB",  # Azul claro
]

# Colores para graficos de crecimiento/decrecimiento
COLOR_POSITIVO = "#2E8B57"
COLOR_NEGATIVO = "#E74C3C"


def apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """
    Aplica el tema visual a una figura de Plotly.

    Args:
        fig: Figura de Plotly.
        title: Titulo del grafico.

    Returns:
        Figura con tema aplicado.
    """
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color=TEXT_COLOR),
            x=0.5,
            xanchor="center",
        ),
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=SECONDARY_BG,
        font=dict(color=TEXT_COLOR, family="Arial, sans-serif"),
        margin=dict(l=60, r=40, t=80, b=60),
        hovermode="closest",
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_COLOR),
        ),
    )
    # Aplicar colores de ejes
    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        color=TEXT_COLOR,
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        color=TEXT_COLOR,
    )
    return fig
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: ui/charts/historical.py
# ═══════════════════════════════════════════════════════════
HISTORICAL = '''"""
Graficos historicos: areas vs produccion y rendimiento.

Migrado de plot_00_historico_cruces() y plot_01_rendimiento_historico().
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.charts.theme import (
    COLOR_POSITIVO,
    PALETTE,
    apply_theme,
)


def plot_historico_cruces(df: pd.DataFrame) -> go.Figure:
    """
    Grafico 00: Evolucion historica de areas, produccion y brecha.

    Args:
        df: DataFrame con columnas ano, area_sembrada_ha,
            area_cosechada_ha, produccion_t.

    Returns:
        Figura de Plotly con doble eje (areas + produccion).
    """
    hist = df.groupby("ano").agg(
        sembrada=("area_sembrada_ha", "sum"),
        cosechada=("area_cosechada_ha", "sum"),
        produccion=("produccion_t", "sum"),
    ).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Brecha de perdida (area entre sembrada y cosechada)
    fig.add_trace(
        go.Scatter(
            x=hist["ano"], y=hist["sembrada"],
            fill="tonexty", fillcolor="rgba(231, 76, 60, 0.15)",
            name="Brecha de Perdida (ha)",
            line=dict(width=0),
            hoverinfo="skip",
        ),
        secondary_y=False,
    )

    # Area sembrada
    fig.add_trace(
        go.Scatter(
            x=hist["ano"], y=hist["sembrada"],
            mode="lines+markers",
            name="Area Sembrada (ha)",
            line=dict(color=PALETTE[1], width=3),
            marker=dict(size=8),
        ),
        secondary_y=False,
    )

    # Area cosechada
    fig.add_trace(
        go.Scatter(
            x=hist["ano"], y=hist["cosechada"],
            mode="lines+markers",
            name="Area Cosechada (ha)",
            line=dict(color=PALETTE[2], width=3),
            marker=dict(size=8, symbol="square"),
        ),
        secondary_y=False,
    )

    # Produccion (eje secundario)
    fig.add_trace(
        go.Scatter(
            x=hist["ano"], y=hist["produccion"],
            mode="lines+markers",
            name="Produccion (t)",
            line=dict(color=COLOR_POSITIVO, width=3, dash="dash"),
            marker=dict(size=8, symbol="triangle-up"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Hectareas (ha)", secondary_y=False)
    fig.update_yaxes(title_text="Toneladas (t)", secondary_y=True)

    return apply_theme(fig, "Evolucion Historica del Valle del Cauca (2019-2024)")


def plot_rendimiento_historico(df: pd.DataFrame) -> go.Figure:
    """
    Grafico 01: Evolucion del rendimiento promedio departamental.

    Args:
        df: DataFrame con columnas ano, produccion_t, area_cosechada_ha.

    Returns:
        Figura de Plotly con barras y linea de tendencia.
    """
    hist = df.groupby("ano").agg(
        produccion=("produccion_t", "sum"),
        cosechada=("area_cosechada_ha", "sum"),
    ).reset_index()
    hist["rendimiento"] = hist["produccion"] / hist["cosechada"]

    fig = go.Figure()

    # Barras
    fig.add_trace(
        go.Bar(
            x=hist["ano"], y=hist["rendimiento"],
            name="Rendimiento (t/ha)",
            marker_color="rgba(74, 144, 217, 0.6)",
            text=[f"{v:.1f}" for v in hist["rendimiento"]],
            textposition="outside",
        )
    )

    # Linea de tendencia
    fig.add_trace(
        go.Scatter(
            x=hist["ano"], y=hist["rendimiento"],
            mode="lines+markers",
            name="Tendencia",
            line=dict(color="#E74C3C", width=2),
            marker=dict(size=8),
        )
    )

    fig.update_layout(barmode="overlay")
    fig.update_yaxes(title_text="Toneladas por Hectarea")

    return apply_theme(fig, "Evolucion del Rendimiento Promedio Departamental (t/ha)")
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: ui/charts/distributions.py
# ═══════════════════════════════════════════════════════════
DISTRIBUTIONS = '''"""
Graficos de distribuciones: histogramas con KDE en escala log.

Migrado de plot_02_distribuciones().
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.charts.theme import PALETTE, apply_theme


def plot_distribuciones_log(df: pd.DataFrame) -> go.Figure:
    """
    Grafico 02: Distribuciones logaritmicas de metricas productivas.

    Args:
        df: DataFrame con las 4 metricas productivas.

    Returns:
        Figura de Plotly con 4 subplots (2x2).
    """
    metricas = ["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]
    titulos = ["Area Sembrada (ha)", "Area Cosechada (ha)", "Produccion (t)", "Rendimiento (t/ha)"]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=titulos,
        horizontal_spacing=0.08,
        vertical_spacing=0.12,
    )

    posiciones = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for i, (col, titulo) in enumerate(zip(metricas, titulos)):
        if col not in df.columns:
            continue
        data = df[col].dropna()
        data = data[data > 0]  # Filtrar ceros para escala log

        row, col_pos = posiciones[i]
        fig.add_trace(
            go.Histogram(
                x=data,
                nbinsx=50,
                name=titulo,
                marker_color=PALETTE[i % len(PALETTE)],
                opacity=0.75,
                showlegend=False,
            ),
            row=row, col=col_pos,
        )
        # Escala logaritmica en X
        fig.update_xaxes(type="log", row=row, col=col_pos)

    return apply_theme(fig, "Distribuciones Logaritmicas de Metricas Productivas")
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: ui/charts/concentration.py
# ═══════════════════════════════════════════════════════════
CONCENTRATION = '''"""
Graficos de concentracion: Pareto y donas ex-cana.

Migrado de plot_03_pareto_concentracion() y plot_07_ex_cana_donuts().
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.constants import GRUPO_CULTIVO_CANA
from ui.charts.theme import PALETTE, apply_theme


def plot_pareto_concentracion(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Grafico 03: Diagrama de Pareto (produccion por cultivo).

    Args:
        df: DataFrame con columnas cultivo, produccion_t.
        top_n: Numero de cultivos a mostrar (default 10).

    Returns:
        Figura de Plotly con barras y linea acumulada.
    """
    cult_prod = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    top = cult_prod.head(top_n)
    acumulado = top.cumsum() / cult_prod.sum() * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Barras
    fig.add_trace(
        go.Bar(
            x=top.index, y=top.values,
            name="Produccion Total (t)",
            marker_color=PALETTE[:top_n],
        ),
        secondary_y=False,
    )

    # Linea acumulada
    fig.add_trace(
        go.Scatter(
            x=top.index, y=acumulado.values,
            mode="lines+markers",
            name="% Acumulado",
            line=dict(color="#E74C3C", width=2),
            marker=dict(size=8),
        ),
        secondary_y=True,
    )

    # Linea del 80%
    fig.add_hline(y=80, line_dash="dash", line_color="gray", secondary_y=True)

    fig.update_yaxes(title_text="Produccion Total (t)", secondary_y=False)
    fig.update_yaxes(title_text="Porcentaje Acumulado (%)", range=[0, 105], secondary_y=True)
    fig.update_xaxes(tickangle=45)

    return apply_theme(fig, "Concentracion de la Produccion: Diagrama de Pareto")


def plot_ex_cana_donuts(df: pd.DataFrame) -> go.Figure:
    """
    Grafico 07: Donas comparativas (con cana vs sin cana).

    Args:
        df: DataFrame con columnas grupo_cultivo, produccion_t.

    Returns:
        Figura de Plotly con 2 donas lado a lado.
    """
    con_cana = df.groupby("grupo_cultivo")["produccion_t"].sum().sort_values(ascending=False)
    sin_cana = (
        df[df["grupo_cultivo"] != GRUPO_CULTIVO_CANA]
        .groupby("grupo_cultivo")["produccion_t"]
        .sum()
        .sort_values(ascending=False)
    )

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "pie"}]],
        subplot_titles=["Matriz CON Cana de Azucar", "Matriz SIN Cana de Azucar"],
    )

    # Dona izquierda: Con cana
    fig.add_trace(
        go.Pie(
            labels=con_cana.index,
            values=con_cana.values,
            hole=0.4,
            name="Con Cana",
            marker=dict(colors=PALETTE),
            textinfo="label+percent",
        ),
        row=1, col=1,
    )

    # Dona derecha: Sin cana (top 5 + Otros)
    top5 = sin_cana.head(5)
    otros = pd.Series({"Otros": sin_cana[5:].sum()})
    sin_cana_plot = pd.concat([top5, otros])

    fig.add_trace(
        go.Pie(
            labels=sin_cana_plot.index,
            values=sin_cana_plot.values,
            hole=0.4,
            name="Sin Cana",
            marker=dict(colors=PALETTE[:len(sin_cana_plot)]),
            textinfo="label+percent",
        ),
        row=1, col=2,
    )

    return apply