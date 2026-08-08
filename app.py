"""EVA Valle v3.0 - Dashboard Analitico."""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="EVA Valle del Cauca",
    page_icon="\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("\U0001F33E EVA Agricola 2019-2024 - Valle del Cauca")
st.markdown("---")
st.info(
    "**Estado:** En construccion (Fase 3).\n"
    "Las paginas estaran disponibles tras la Fase 4 (migracion)."
)
st.markdown("### Paginas del Dashboard")
st.markdown(
    "- Dashboard\n- Descriptivo\n- Diagnostico\n"
    "- Predictivo\n- Auditoria\n- Configuracion"
)
st.markdown("---")
st.caption("EVA Valle v3.0 - Arquitectura Hexagonal - UPRA")
