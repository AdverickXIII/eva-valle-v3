"""Pagina 0: Inicio - Hub de navegacion."""
from __future__ import annotations
import streamlit as st

st.title("\U0001F33E EVA Agricola 2019-2025 - Valle del Cauca")
st.markdown(
    "Dashboard analitico de produccion agricola basado en datos de la UPRA.  \n"
    "**42 municipios** | **78 cultivos** | **7 anos de datos (2019-2025)**"
)
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\U0001F4CA</div>'
        '<div class="metric-label">Dashboard</div>'
        '<div class="metric-value" style="font-size:1rem;">Vista general con KPIs</div></div>',
        unsafe_allow_html=True)
with col2:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\U0001F4C8</div>'
        '<div class="metric-label">Descriptivo</div>'
        '<div class="metric-value" style="font-size:1rem;">12 analisis estadisticos</div></div>',
        unsafe_allow_html=True)
with col3:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\U0001F52C</div>'
        '<div class="metric-label">Diagnostico</div>'
        '<div class="metric-value" style="font-size:1rem;">5 analisis causales</div></div>',
        unsafe_allow_html=True)

st.markdown("---")
col4, col5, col6 = st.columns(3)
with col4:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\U0001F916</div>'
        '<div class="metric-label">Predictivo</div>'
        '<div class="metric-value" style="font-size:1rem;">Modelos ML y proyecciones</div></div>',
        unsafe_allow_html=True)
with col5:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\U0001F50D</div>'
        '<div class="metric-label">Auditoria</div>'
        '<div class="metric-value" style="font-size:1rem;">Calidad de datos</div></div>',
        unsafe_allow_html=True)
with col6:
    st.markdown('<div class="eva-metric-card"><div class="metric-icon">\u2699\uFE0F</div>'
        '<div class="metric-label">Configuracion</div>'
        '<div class="metric-value" style="font-size:1rem;">Descarga y parametros</div></div>',
        unsafe_allow_html=True)

st.markdown("---")
st.info("\U0001F4A1 **Navega usando la barra lateral** para acceder a cada pagina.")

st.markdown('<div class="eva-footer">EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular</div>',
    unsafe_allow_html=True)
