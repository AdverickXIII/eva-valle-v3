"""Fix definitivo 4.4: histograma manual en log10 con go.Bar (plotly no soporta Histogram+log)."""
from pathlib import Path

CODE = '''"""Graficos de distribuciones log (histograma manual en espacio log10)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.charts.theme import apply_theme

METRICAS = [
    ("area_sembrada_ha", "Area Sembrada (ha)"),
    ("area_cosechada_ha", "Area Cosechada (ha)"),
    ("produccion_t", "Produccion (t)"),
    ("rendimiento_t_ha", "Rendimiento (t/ha)"),
]

TICKVALS = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7]
TICKTEXT = ["0.01", "0.1", "1", "10", "100", "1k", "10k", "100k", "1M", "10M"]


def plot_distribuciones_log(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    if "rendimiento_t_ha" not in df.columns:
        df["rendimiento_t_ha"] = (
            df["produccion_t"] / df["area_cosechada_ha"].replace(0, np.nan)
        )

    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=[t for _, t in METRICAS])
    pos = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for (col, titulo), (r, c) in zip(METRICAS, pos):
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        s = s.replace([np.inf, -np.inf], np.nan).dropna()
        s = s[s > 0]
        if s.empty:
            continue
        # Histograma MANUAL en espacio log10 (aqui esta el fix)
        l = np.log10(s)
        hist, edges = np.histogram(l, bins=60)
        centers = (edges[:-1] + edges[1:]) / 2.0
        fig.add_trace(go.Bar(
            x=centers, y=hist, marker_color="#2E8B57", opacity=0.75,
            showlegend=False, customdata=10 ** centers,
            hovertemplate="valor ≈ %{customdata:,.1f}<br>n=%{y}<extra></extra>"),
            row=r, col=c)

    fig = apply_theme(fig, "Distribuciones Logaritmicas de Metricas Productivas")

    # Ticks en potencias de 10 DESPUES del tema (por si el tema pisa ejes)
    for r in (1, 2):
        for c in (1, 2):
            fig.update_xaxes(type="linear", tickvals=TICKVALS,
                             ticktext=TICKTEXT, row=r, col=c)
            fig.update_yaxes(title_text="Frecuencia", row=r, col=c)
    return fig
'''

Path("ui/charts/distributions.py").write_text(CODE, encoding="utf-8")
print("[OK] distributions.py v2: histograma manual log10 con go.Bar")
print("Reinicia Streamlit y revisa Descriptivo -> Distribuciones -> 4.4")