"""
EVA Valle v3.0 - Dashboard Analitico de Produccion Agricola
Punto de entrada con navegacion multi-pagina (st.navigation).
"""
from __future__ import annotations

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon="\U0001F33E",
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
    st.title("\U0001F33E EVA Valle")
    st.markdown("**Agricola 2019-2024**")
    st.markdown("---")
    st.caption("UPRA - Unidad de Planificacion Rural y Agropecuaria")
    st.caption("Arquitectura Hexagonal Modular v3.0")

# Navegacion multi-pagina
pg = st.navigation([
    st.Page("ui/pages/0_Home.py", title="Inicio", icon="\U0001F3E0", default=True),
    st.Page("ui/pages/1_Dashboard.py", title="Dashboard", icon="\U0001F4CA"),
    st.Page("ui/pages/2_Descriptivo.py", title="Descriptivo", icon="\U0001F4C8"),
    st.Page("ui/pages/3_Diagnostico.py", title="Diagnostico", icon="\U0001F52C"),
    st.Page("ui/pages/4_Predictivo.py", title="Predictivo", icon="\U0001F916"),
    st.Page("ui/pages/5_Auditoria.py", title="Auditoria", icon="\U0001F50D"),
    st.Page("ui/pages/6_Configuracion.py", title="Configuracion", icon="\u2699\uFE0F"),
    st.Page("ui/pages/7_Cultivos.py", title="Cultivos", icon="\U0001F331"),
])

pg.run()
