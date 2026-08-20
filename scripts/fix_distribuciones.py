"""Reescribe ui/charts/distributions.py con filtro de valores positivos para eje log."""
from pathlib import Path

CODE = '''"""Graficos de distribuciones log."""
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
        # FIX: solo valores positivos y finitos (el eje log no dibuja 0/inf/NaN)
        s = pd.to_numeric(df[col], errors="coerce")
        s = s.replace([np.inf, -np.inf], np.nan).dropna()
        s = s[s > 0]
        if s.empty:
            continue
        fig.add_trace(
            go.Histogram(x=s, nbinsx=60, marker_color="#2E8B57",
                         opacity=0.75, showlegend=False),
            row=r, col=c)
        fig.update_xaxes(type="log", row=r, col=c)
        fig.update_yaxes(title_text="Frecuencia", row=r, col=c)

    return apply_theme(fig, "Distribuciones Logaritmicas de Metricas Productivas")
'''

Path("ui/charts/distributions.py").write_text(CODE, encoding="utf-8")
print("[OK] ui/charts/distributions.py reescrito con filtro de positivos")
print("Reinicia Streamlit y verifica la pestana Distribuciones (4.4)")