"""Pagina 6: Configuracion - Estado y acciones."""
from __future__ import annotations
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.error_handler import run_safe

from config.settings import settings

st.set_page_config(page_title="Configuracion | EVA Valle", page_icon="\u2699\uFE0F", layout="wide")

def main() -> None:
    st.title("\u2699\uFE0F Configuracion del Sistema")
    st.caption("Estado del pipeline, descargas y parametros")
    st.markdown("---")
    st.subheader("\U0001F4CA Estado del Pipeline")
    archivos_clave = {
        "Dataset estandarizado": settings.DATA_PROCESSED_PATH / "01_clean" / "eva_agricola_valle_2019_2024_estandarizado.csv",
        "Modelo conceptual": settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
        "Reporte auditoria": settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv",
    }
    for nombre, path in archivos_clave.items():
        col1, col2 = st.columns([3, 1])
        with col1: st.markdown(f"**{nombre}**  \n`{path}`")
        with col2:
            if path.exists():
                size_mb = path.stat().st_size / (1024*1024)
                st.success(f"\u2705 {size_mb:.2f} MB")
            else:
                st.warning("\u274C No existe")
    st.markdown("---")
    st.subheader("\u2699\uFE0F Parametros del Sistema")
    col1, col2 = st.columns(2)
    with col1:
        st.code(f"PROJECT: {settings.PROJECT_NAME}\nENV: {settings.ENV}\nROOT: {settings.PROJECT_ROOT}")
    with col2:
        st.code(f"ML_RANDOM_STATE: {settings.ML_RANDOM_STATE}\nML_TEST_SIZE: {settings.ML_TEST_SIZE}")
    st.markdown("---")
    st.subheader("\u25B6\uFE0F Ejecutar Pasos del Pipeline")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\U0001F504 Paso 1+2: Carga y Auditoria"):
            with st.spinner("Ejecutando..."):
                try:
                    from core.audit.loader import load_and_standardize
                    from core.audit import run_all_audits
                    from core.audit.report import generate_audit_report
                    df_valle, _ = load_and_standardize()
                    findings = run_all_audits(df_valle)
                    generate_audit_report(findings)
                    st.success(f"\u2705 Completado: {len(findings)} hallazgos")
                except Exception as e:
                    st.error(f"\u274C Error: {e}")
        if st.button("\U0001F3D7\uFE0F Paso 3: Modelado"):
            with st.spinner("Ejecutando..."):
                try:
                    from core.modeling import run_conceptual_modeling
                    df_modelo, _ = run_conceptual_modeling()
                    st.success(f"\u2705 Completado: {len(df_modelo):,} registros")
                except Exception as e:
                    st.error(f"\u274C Error: {e}")
    with col2:
        if st.button("\U0001F4C8 Paso 4: Analisis Descriptivo"):
            with st.spinner("Ejecutando 12 analisis..."):
                try:
                    from core.analytics import run_all_analytics
                    artefactos = run_all_analytics()
                    st.success(f"\u2705 Completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\u274C Error: {e}")
        if st.button("\U0001F52C Paso 6: Diagnostico"):
            with st.spinner("Ejecutando 5 analisis..."):
                try:
                    from core.diagnostics import run_all_diagnostics
                    artefactos = run_all_diagnostics()
                    st.success(f"\u2705 Completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\u274C Error: {e}")
    st.markdown("---")
    st.caption("EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular")

run_safe(main)
