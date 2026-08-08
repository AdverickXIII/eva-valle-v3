"""Configura navegacion multi-pagina con st.navigation()."""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# PAGINA 0: HOME (hub de navegacion)
# ═══════════════════════════════════════════════════════════
HOME = '''"""Pagina 0: Inicio - Hub de navegacion."""
from __future__ import annotations
import streamlit as st

st.title("\\U0001F33E EVA Agricola 2019-2024 - Valle del Cauca")
st.markdown(
    "Dashboard analitico de produccion agricola basado en datos de la UPRA.  \\n"
    "**42 municipios** | **97 desagregaciones de cultivo** | **6 anos de datos**"
)
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\\U0001F4CA</div>'
        '<div class="metric-label">Dashboard</div>'
        '<div class="metric-value" style="font-size:1rem;">Vista general con KPIs</div></div>',
        unsafe_allow_html=True)
with col2:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\\U0001F4C8</div>'
        '<div class="metric-label">Descriptivo</div>'
        '<div class="metric-value" style="font-size:1rem;">12 analisis estadisticos</div></div>',
        unsafe_allow_html=True)
with col3:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\\U0001F52C</div>'
        '<div class="metric-label">Diagnostico</div>'
        '<div class="metric-value" style="font-size:1rem;">5 analisis causales</div></div>',
        unsafe_allow_html=True)

st.markdown("---")
col4, col5, col6 = st.columns(3)
with col4:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\\U0001F916</div>'
        '<div class="metric-label">Predictivo</div>'
        '<div class="metric-value" style="font-size:1rem;">Modelos ML y proyecciones</div></div>',
        unsafe_allow_html=True)
with col5:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\\U0001F50D</div>'
        '<div class="metric-label">Auditoria</div>'
        '<div class="metric-value" style="font-size:1rem;">Calidad de datos</div></div>',
        unsafe_allow_html=True)
with col6:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\\u2699\\uFE0F</div>'
        '<div class="metric-label">Configuracion</div>'
        '<div class="metric-value" style="font-size:1rem;">Descarga y parametros</div></div>',
        unsafe_allow_html=True)

st.markdown("---")
st.info("\\U0001F4A1 **Navega usando la barra lateral** para acceder a cada pagina.")

st.markdown('<div class="eva-footer">EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular</div>',
    unsafe_allow_html=True)
'''

# ═══════════════════════════════════════════════════════════
# APP.PY: Punto de entrada con st.navigation()
# ═══════════════════════════════════════════════════════════
APP = '''"""
EVA Valle v3.0 - Dashboard Analitico de Produccion Agricola
Punto de entrada con navegacion multi-pagina (st.navigation).
"""
from __future__ import annotations

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon="\\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar CSS personalizado
css_path = Path(__file__).parent / "ui" / "assets" / "css" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# Sidebar global
with st.sidebar:
    st.title("\\U0001F33E EVA Valle")
    st.markdown("**Agricola 2019-2024**")
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")
    st.caption("Arquitectura Hexagonal Modular v3.0")

# Navegacion multi-pagina
pg = st.navigation([
    st.Page("ui/pages/0_Home.py", title="Inicio", icon="\\U0001F3E0", default=True),
    st.Page("ui/pages/1_Dashboard.py", title="Dashboard", icon="\\U0001F4CA"),
    st.Page("ui/pages/2_Descriptivo.py", title="Descriptivo", icon="\\U0001F4C8"),
    st.Page("ui/pages/3_Diagnostico.py", title="Diagnostico", icon="\\U0001F52C"),
    st.Page("ui/pages/4_Predictivo.py", title="Predictivo", icon="\\U0001F916"),
    st.Page("ui/pages/5_Auditoria.py", title="Auditoria", icon="\\U0001F50D"),
    st.Page("ui/pages/6_Configuracion.py", title="Configuracion", icon="\\u2699\\uFE0F"),
])

pg.run()
'''

if __name__ == "__main__":
    archivos = {
        "ui/pages/0_Home.py": HOME,
        "app.py": APP,
    }
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
    print("\nNavegacion configurada. Ejecuta: streamlit run app.py")