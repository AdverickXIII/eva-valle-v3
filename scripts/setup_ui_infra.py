"""Setup UI infraestructura: CSS, app.py, componentes."""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: ui/assets/css/style.css
# ═══════════════════════════════════════════════════════════
CSS = '''/* ═══════════════════════════════════════════════════════════
   EVA Valle v3.0 - Tema Profesional Oscuro
   Inspirado en: Power BI, Tableau, Looker Studio
   ═══════════════════════════════════════════════════════════ */

/* ── Variables de tema ─────────────────────────────────── */
:root {
    --eva-primary: #2E8B57;
    --eva-primary-light: #3DA86C;
    --eva-primary-dark: #1F6B42;
    --eva-bg: #0E1117;
    --eva-bg-secondary: #1A1F2E;
    --eva-bg-card: #1E2536;
    --eva-text: #FAFAFA;
    --eva-text-muted: #A0AEC0;
    --eva-border: #2D3748;
    --eva-success: #48BB78;
    --eva-warning: #ECC94B;
    --eva-danger: #F56565;
    --eva-info: #4299E1;
    --eva-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    --eva-radius: 12px;
}

/* ── Fondo y tipografia global ─────────────────────────── */
.stApp {
    background-color: var(--eva-bg);
    color: var(--eva-text);
}

.stApp > header {
    background-color: var(--eva-bg);
}

/* ── Cards de metricas (KPI) ───────────────────────────── */
.eva-metric-card {
    background: linear-gradient(135deg, var(--eva-bg-card) 0%, var(--eva-bg-secondary) 100%);
    border: 1px solid var(--eva-border);
    border-radius: var(--eva-radius);
    padding: 1.25rem 1.5rem;
    box-shadow: var(--eva-shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}

.eva-metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    border-color: var(--eva-primary);
}

.eva-metric-card .metric-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--eva-text-muted);
    margin-bottom: 0.5rem;
}

.eva-metric-card .metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--eva-text);
    line-height: 1.2;
}

.eva-metric-card .metric-delta {
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 0.35rem;
}

.eva-metric-card .metric-delta.positive { color: var(--eva-success); }
.eva-metric-card .metric-delta.negative { color: var(--eva-danger); }
.eva-metric-card .metric-delta.neutral  { color: var(--eva-text-muted); }

.eva-metric-card .metric-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

/* ── Secciones y encabezados ───────────────────────────── */
.eva-section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--eva-primary);
}

.eva-section-header h2 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--eva-text);
}

.eva-section-header .section-icon {
    font-size: 1.4rem;
}

/* ── Tabs personalizados ───────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 2px solid var(--eva-border);
}

.stTabs [data-baseweb="tab"] {
    padding: 0.75rem 1.25rem;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
    color: var(--eva-text-muted);
}

.stTabs [aria-selected="true"] {
    color: var(--eva-primary) !important;
    border-bottom: 3px solid var(--eva-primary);
    background-color: rgba(46, 139, 87, 0.08);
}

/* ── Expanders ─────────────────────────────────────────── */
.streamlit-expanderHeader {
    background-color: var(--eva-bg-card) !important;
    border-radius: var(--eva-radius) !important;
    border: 1px solid var(--eva-border) !important;
}

/* ── Tablas y dataframes ───────────────────────────────── */
.stDataFrame {
    border-radius: var(--eva-radius);
    overflow: hidden;
    border: 1px solid var(--eva-border);
}

/* ── Botones ───────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, var(--eva-primary) 0%, var(--eva-primary-dark) 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, var(--eva-primary-light) 0%, var(--eva-primary) 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(46, 139, 87, 0.4);
}

/* ── Sidebar ───────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: var(--eva-bg-secondary);
    border-right: 1px solid var(--eva-border);
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--eva-text);
}

/* ── Alertas e info boxes ──────────────────────────────── */
.stAlert {
    border-radius: var(--eva-radius);
    border: 1px solid var(--eva-border);
}

/* ── Footer ────────────────────────────────────────────── */
.eva-footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: var(--eva-text-muted);
    font-size: 0.85rem;
    border-top: 1px solid var(--eva-border);
    margin-top: 3rem;
}

/* ── Responsive ────────────────────────────────────────── */
@media (max-width: 768px) {
    .eva-metric-card .metric-value {
        font-size: 1.4rem;
    }
    .eva-section-header h2 {
        font-size: 1.2rem;
    }
}

/* ── Scrollbar personalizado ───────────────────────────── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--eva-bg); }
::-webkit-scrollbar-thumb {
    background: var(--eva-border);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: var(--eva-primary); }
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: app.py (Punto de entrada multi-pagina)
# ═══════════════════════════════════════════════════════════
APP = '''"""
EVA Valle v3.0 - Dashboard Analitico de Produccion Agricola
Punto de entrada de la aplicacion Streamlit (multi-page).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# Configuracion de la pagina (debe ser la primera llamada de Streamlit)
st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon="\\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.upra.gov.co/",
        "Report a bug": None,
        "About": (
            "EVA Valle v3.0 - Dashboard de produccion agricola "
            "del Valle del Cauca (UPRA - EVA 2019-2024)"
        ),
    },
)

# Cargar CSS personalizado
css_path = Path(__file__).parent / "ui" / "assets" / "css" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# ── Sidebar global ──────────────────────────────────────────
with st.sidebar:
    st.title("\\U0001F33E EVA Valle")
    st.markdown("**Agricola 2019-2024**")
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")
    st.caption("Arquitectura Hexagonal Modular v3.0")

# ── Pagina principal (hub de navegacion) ───────────────────
st.title("\\U0001F33E EVA Agricola 2019-2024 - Valle del Cauca")
st.markdown(
    "Dashboard analitico de produccion agricola basado en datos de la UPRA.  \\n"
    "**42 municipios** | **97 desagregaciones de cultivo** | **6 anos de datos**"
)
st.markdown("---")

# Cards de navegacion
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="eva-metric-card">'
        '<div class="metric-icon">\\U0001F4CA</div>'
        '<div class="metric-label">Dashboard</div>'
        '<div class="metric-value" style="font-size:1rem;">Vista general con KPIs</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="eva-metric-card">'
        '<div class="metric-icon">\\U0001F4C8</div>'
        '<div class="metric-label">Descriptivo</div>'
        '<div class="metric-value" style="font-size:1rem;">12 analisis estadisticos</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="eva-metric-card">'
        '<div class="metric-icon">\\U0001F52C</div>'
        '<div class="metric-label">Diagnostico</div>'
        '<div class="metric-value" style="font-size:1rem;">5 analisis causales</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(
        '<div class="eva-metric-card">'
        '<div class="metric-icon">\\U0001F916</div>'
        '<div class="metric-label">Predictivo</div>'
        '<div class="metric-value" style="font-size:1rem;">Modelos ML y proyecciones</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with col5:
    st.markdown(
        '<div class="eva-metric-card">'
        '<div class="metric-icon">\\U0001F50D</div>'
        '<div class="metric-label">Auditoria</div>'
        '<div class="metric-value" style="font-size:1rem;">Calidad de datos</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with col6:
    st.markdown(
        '<div class="eva-metric-card">'
        '<div class="metric-icon">\\u2699\\uFE0F</div>'
        '<div class="metric-label">Configuracion</div>'
        '<div class="metric-value" style="font-size:1rem;">Descarga y parametros</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.info(
    "\\U0001F4A1 **Navega usando la barra lateral** para acceder a cada pagina del dashboard."
)

# Footer
st.markdown(
    '<div class="eva-footer">'
    "EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular | "
    "Streamlit + Plotly + Pandas"
    "</div>",
    unsafe_allow_html=True,
)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: ui/components/__init__.py
# ═══════════════════════════════════════════════════════════
COMPONENTS_INIT = '''"""Componentes UI reutilizables para el dashboard EVA Valle."""
from ui.components.metrics_cards import render_kpi_card, render_kpi_row
from ui.components.filter_panel import render_filter_panel
from ui.components.loading_states import render_loading, render_empty_state
from ui.components.download_section import render_download_button

__all__ = [
    "render_kpi_card",
    "render_kpi_row",
    "render_filter_panel",
    "render_loading",
    "render_empty_state",
    "render_download_button",
]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: ui/components/metrics_cards.py
# ═══════════════════════════════════════════════════════════
METRICS_CARDS = '''"""Cards de metricas KPI estilizadas."""
from __future__ import annotations

import streamlit as st


def render_kpi_card(
    label: str,
    value: str,
    delta: str = "",
    delta_type: str = "neutral",
    icon: str = "",
) -> None:
    """
    Renderiza una card de metrica KPI.

    Args:
        label: Nombre de la metrica.
        value: Valor principal formateado.
        delta: Variacion porcentual o texto de cambio.
        delta_type: 'positive', 'negative' o 'neutral'.
        icon: Emoji o icono de la metrica.
    """
    delta_html = ""
    if delta:
        delta_html = f'<div class="metric-delta {delta_type}">{delta}</div>'

    icon_html = f'<div class="metric-icon">{icon}</div>' if icon else ""

    st.markdown(
        f'<div class="eva-metric-card">'
        f'{icon_html}'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_kpi_row(kpis: list[dict[str, str]], cols: int = 4) -> None:
    """
    Renderiza una fila de cards KPI.

    Args:
        kpis: Lista de dicts con keys: label, value, delta, delta_type, icon.
        cols: Numero de columnas (default 4).
    """
    columns = st.columns(cols)
    for i, kpi in enumerate(kpis):
        with columns[i % cols]:
            render_kpi_card(
                label=kpi.get("label", ""),
                value=kpi.get("value", ""),
                delta=kpi.get("delta", ""),
                delta_type=kpi.get("delta_type", "neutral"),
                icon=kpi.get("icon", ""),
            )
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: ui/components/filter_panel.py
# ═══════════════════════════════════════════════════════════
FILTER_PANEL = '''"""Panel de filtros dinamicos para el dashboard."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_filter_panel(
    df: pd.DataFrame,
    key_prefix: str = "filter",
) -> dict[str, Any]:
    """
    Renderiza el panel de filtros en el sidebar.

    Args:
        df: DataFrame completo con los datos.
        key_prefix: Prefijo para las keys de los widgets.

    Returns:
        Diccionario con los filtros seleccionados:
        {municipio, cultivo, grupo_cultivo, ano, ciclo}.
    """
    filters: dict[str, Any] = {}

    st.sidebar.markdown("### \\U0001F50D Filtros")

    # Municipio
    municipios = sorted(df["municipio"].dropna().unique().tolist())
    selected_municipio = st.sidebar.multiselect(
        "Municipio",
        options=municipios,
        key=f"{key_prefix}_municipio",
        placeholder="Todos los municipios",
    )
    filters["municipio"] = selected_municipio if selected_municipio else None

    # Grupo de cultivo
    grupos = sorted(df["grupo_cultivo"].dropna().unique().tolist())
    selected_grupo = st.sidebar.multiselect(
        "Grupo de Cultivo",
        options=grupos,
        key=f"{key_prefix}_grupo",
        placeholder="Todos los grupos",
    )
    filters["grupo_cultivo"] = selected_grupo if selected_grupo else None

    # Ciclo del cultivo
    selected_ciclo = st.sidebar.radio(
        "Ciclo del Cultivo",
        options=["Todos", "Transitorio", "Permanente"],
        key=f"{key_prefix}_ciclo",
    )
    filters["ciclo_del_cultivo"] = None if selected_ciclo == "Todos" else selected_ciclo

    # Anio
    anos = sorted(df["ano"].dropna().unique().tolist())
    selected_ano = st.sidebar.slider(
        "Rango de Anios",
        min_value=int(min(anos)),
        max_value=int(max(anos)),
        value=(int(min(anos)), int(max(anos))),
        key=f"{key_prefix}_ano",
    )
    filters["ano_range"] = selected_ano

    # Boton de limpiar filtros
    if st.sidebar.button("\\U0001F504 Limpiar Filtros", key=f"{key_prefix}_clear"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.markdown("---")
    return filters


def apply_filters(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    """
    Aplica los filtros seleccionados al DataFrame.

    Args:
        df: DataFrame completo.
        filters: Diccionario retornado por render_filter_panel().

    Returns:
        DataFrame filtrado.
    """
    df_filtered = df.copy()

    if filters.get("municipio"):
        df_filtered = df_filtered[df_filtered["municipio"].isin(filters["municipio"])]

    if filters.get("grupo_cultivo"):
        df_filtered = df_filtered[df_filtered["grupo_cultivo"].isin(filters["grupo_cultivo"])]

    if filters.get("ciclo_del_cultivo"):
        df_filtered = df_filtered[df_filtered["ciclo_del_cultivo"] == filters["ciclo_del_cultivo"]]

    if filters.get("ano_range"):
        ano_min, ano_max = filters["ano_range"]
        df_filtered = df_filtered[(df_filtered["ano"] >= ano_min) & (df_filtered["ano"] <= ano_max)]

    return df_filtered
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: ui/components/loading_states.py
# ═══════════════════════════════════════════════════════════
LOADING_STATES = '''"""Estados de carga y mensajes vacios."""
from __future__ import annotations

import streamlit as st


def render_loading(message: str = "Cargando datos...") -> None:
    """Renderiza un spinner de carga."""
    with st.spinner(message):
        pass


def render_empty_state(
    message: str = "No hay datos disponibles",
    icon: str = "\\U0001F4ED",
    hint: str = "",
) -> None:
    """
    Renderiza un estado vacio cuando no hay datos.

    Args:
        message: Mensaje principal.
        icon: Emoji de estado vacio.
        hint: Pista de como resolver (ej: 'Ejecuta el pipeline primero').
    """
    st.markdown(
        f'<div style="text-align:center; padding:3rem; color:var(--eva-text-muted);">'
        f'<div style="font-size:3rem;">{icon}</div>'
        f'<h3 style="color:var(--eva-text);">{message}</h3>'
        + (f'<p>{hint}</p>' if hint else "")
        + "</div>",
        unsafe_allow_html=True,
    )
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: ui/components/download_section.py
# ═══════════════════════════════════════════════════════════
DOWNLOAD_SECTION = '''"""Botones de descarga de artefactos."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def render_download_button(
    df: pd.DataFrame,
    filename: str,
    label: str = "\\U0001F4E5 Descargar CSV",
    key: str | None = None,
) -> None:
    """
    Renderiza un boton de descarga de DataFrame como CSV.

    Args:
        df: DataFrame a descargar.
        filename: Nombre del archivo de salida.
        label: Texto del boton.
        key: Key unica del widget.
    """
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
        key=key or f"download_{filename}",
    )


def render_file_download(
    filepath: Path,
    label: str | None = None,
) -> None:
    """
    Renderiza un boton de descarga de un archivo existente.

    Args:
        filepath: Ruta al archivo.
        label: Texto del boton. Si None, usa el nombre del archivo.
    """
    if not filepath.exists():
        st.warning(f"Archivo no disponible: {filepath.name}")
        return

    with open(filepath, "rb") as f:
        data = f.read()

    st.download_button(
        label=label or f"\\U0001F4E5 {filepath.name}",
        data=data,
        file_name=filepath.name,
        key=f"download_file_{filepath.name}",
    )
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "ui/assets/css/style.css": CSS,
        "app.py": APP,
        "ui/components/__init__.py": COMPONENTS_INIT,
        "ui/components/metrics_cards.py": METRICS_CARDS,
        "ui/components/filter_panel.py": FILTER_PANEL,
        "ui/components/loading_states.py": LOADING_STATES,
        "ui/components/download_section.py": DOWNLOAD_SECTION,
    }

    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")

    print(f"\n{len(archivos)} archivos de infraestructura visual creados.")
    print("Ejecuta: streamlit run app.py")