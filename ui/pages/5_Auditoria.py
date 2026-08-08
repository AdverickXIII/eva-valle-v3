"""Pagina 5: Auditoria - Calidad de datos."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.error_handler import run_safe

from config.settings import settings
from ui.components.metrics_cards import render_kpi_row
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
import plotly.express as px

st.set_page_config(page_title="Auditoria | EVA Valle", page_icon="\U0001F50D", layout="wide")

@st.cache_data(ttl=3600)
def load_audit_report() -> pd.DataFrame:
    path = settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\U0001F50D Auditoria de Calidad de Datos")
    st.caption("Paso 2 - Reporte de auditoria tecnica")
    df_audit = load_audit_report()
    if df_audit.empty:
        render_empty_state("Reporte de auditoria no encontrado",
            hint="Ejecuta: python scripts/run_audit.py")
        return
    st.markdown("---")
    n_errors = len(df_audit[df_audit["severidad"] == "ERROR"])
    n_warnings = len(df_audit[df_audit["severidad"] == "ADVERTENCIA"])
    n_info = len(df_audit[df_audit["severidad"] == "INFO"])
    render_kpi_row([
        {"label": "Errores", "value": str(n_errors), "icon": "\u274C"},
        {"label": "Advertencias", "value": str(n_warnings), "icon": "\u26A0\uFE0F"},
        {"label": "Info", "value": str(n_info), "icon": "\u2139\uFE0F"},
        {"label": "Total", "value": str(len(df_audit)), "icon": "\U0001F4CB"},
    ])
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        sev_counts = df_audit["severidad"].value_counts()
        fig_sev = px.pie(values=sev_counts.values, names=sev_counts.index, hole=0.4,
            color=sev_counts.index,
            color_discrete_map={"ERROR":"#F56565","ADVERTENCIA":"#ECC94B","INFO":"#4299E1"},
            template="plotly_dark")
        st.plotly_chart(fig_sev, use_container_width=True)
    with col2:
        st.subheader("Detalle de Hallazgos")
        st.dataframe(df_audit[["codigo","severidad","descripcion","detalle"]],
            use_container_width=True, height=350)
        render_download_button(df_audit, "reporte_auditoria.csv")

run_safe(main)
