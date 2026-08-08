"""Aplica tema claro: style.css, config.toml, theme.py y Plotly."""
from pathlib import Path

CSS = '''/* EVA Valle v3.0 - Tema Claro Profesional (Boceto A) */
:root {
    --eva-primary: #2E8B57;
    --eva-bg: #F8F9FA;
    --eva-bg-secondary: #EDF2F7;
    --eva-card: #FFFFFF;
    --eva-text: #1A202C;
    --eva-muted: #4A5568;
    --eva-border: #E2E8F0;
    --eva-radius: 12px;
    --eva-shadow: 0 2px 8px rgba(26,32,44,0.08);
}
.stApp { background-color: var(--eva-bg); color: var(--eva-text); }
.eva-metric-card {
    background: var(--eva-card);
    border: 1px solid var(--eva-border);
    border-radius: var(--eva-radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--eva-shadow);
    height: 100%;
}
.eva-metric-card .metric-label { color: var(--eva-muted); font-size:.8rem;
    text-transform: uppercase; letter-spacing:.05em; font-weight:600; }
.eva-metric-card .metric-value { color: var(--eva-text); font-size:1.8rem; font-weight:700; }
.eva-metric-card .metric-delta.positive { color:#2F855A; }
.eva-metric-card .metric-delta.negative { color:#C53030; }
.eva-metric-card .metric-delta.neutral { color: var(--eva-muted); }
section[data-testid="stSidebar"] { background: var(--eva-bg-secondary); }
.stButton > button {
    background: var(--eva-primary); color:#fff; border:none; border-radius:8px;
    padding:.6rem 1.5rem; font-weight:600;
}
.stButton > button:hover { background:#276749; }
.eva-footer { text-align:center; color:var(--eva-muted); padding:2rem 0 1rem;
    border-top:1px solid var(--eva-border); margin-top:3rem; font-size:.85rem; }
'''

TOML = '''[theme]
base = "light"
primaryColor = "#2E8B57"
backgroundColor = "#F8F9FA"
secondaryBackgroundColor = "#EDF2F7"
textColor = "#1A202C"

[server]
headless = true
'''

THEME = '''"""Tema visual claro para graficos Plotly."""
from __future__ import annotations
import plotly.graph_objects as go

PRIMARY_COLOR = "#2E8B57"
BACKGROUND_COLOR = "#FFFFFF"
SECONDARY_BG = "#F8F9FA"
TEXT_COLOR = "#1A202C"
GRID_COLOR = "#E2E8F0"
PALETTE = ["#2E8B57","#3182CE","#DD6B20","#805AD5","#E53E3E","#319795","#D69E2E","#3182CE"]
COLOR_POSITIVO = "#2F855A"
COLOR_NEGATIVO = "#C53030"

def apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=TEXT_COLOR), x=0.5),
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=SECONDARY_BG,
        font=dict(color=TEXT_COLOR, family="Arial, sans-serif"),
        margin=dict(l=60, r=40, t=80, b=60),
        hovermode="closest",
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, color=TEXT_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, color=TEXT_COLOR)
    return fig
'''

if __name__ == "__main__":
    Path("ui/assets/css").mkdir(parents=True, exist_ok=True)
    Path("ui/assets/css/style.css").write_text(CSS, encoding="utf-8")
    print("[OK] style.css (tema claro)")

    Path(".streamlit").mkdir(parents=True, exist_ok=True)
    Path(".streamlit/config.toml").write_text(TOML, encoding="utf-8")
    print("[OK] .streamlit/config.toml (tema claro)")

    Path("ui/charts/theme.py").write_text(THEME, encoding="utf-8")
    print("[OK] ui/charts/theme.py (colores claros)")

    # Reemplazar plotly_dark -> plotly_white en paginas y charts
    n = 0
    for f in list(Path("ui/pages").glob("*.py")) + list(Path("ui/charts").glob("*.py")):
        c = f.read_text(encoding="utf-8")
        if "plotly_dark" in c:
            f.write_text(c.replace("plotly_dark", "plotly_white"), encoding="utf-8")
            n += 1
    print(f"[OK] {n} archivos con graficos cambiados a plotly_white")

    print("\nTema claro aplicado. Ejecuta: streamlit run app.py")