"""Pagina 2: Descriptivo - 12 analisis del Paso 4."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.performance import (cached_outliers, cached_time_series, cached_seasonality, cached_segmentation, cached_root_cause)
from ui.services.error_handler import run_safe

from config.settings import settings
from ui.components.filter_panel import render_filter_panel, apply_filters
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.distributions import plot_distribuciones_log
from ui.charts.concentration import plot_ex_cana_donuts
from ui.charts.growth import plot_cagr_divergente
from ui.charts.spatial import plot_lq_heatmap, plot_shannon_barras
from core.analytics.descriptive import calculate_descriptive_statistics
from core.analytics.distributions import fit_distributions
from core.analytics.outliers import detect_multivariate_outliers
from core.analytics.concentration import calculate_concentration
from core.analytics.time_series import analyze_time_series
from core.analytics.seasonality import test_seasonality_ab
from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity
from core.analytics.elasticity import calculate_elasticity
from core.analytics.inferential import run_inferential_test
from core.analytics.growth import calculate_cagr
from core.analytics.ex_cana import analyze_ex_cana

st.set_page_config(page_title="Descriptivo | EVA Valle", page_icon="\U0001F4C8", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\U0001F4C8 Analisis Descriptivo Profundo")
    st.caption("12 analisis estadisticos del Paso 4")
    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return
    filters = render_filter_panel(df, key_prefix="desc")
    df_f = apply_filters(df, filters)
    if df_f.empty:
        render_empty_state("Sin datos con los filtros seleccionados")
        return
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "\U0001F4CA Descriptiva", "\U0001F4C9 Distribuciones",
        "\U0001F3AF Concentracion", "\U0001F4C5 Series de Tiempo",
        "\U0001F30D Espacial", "\U0001F4C8 Crecimiento",
    ])
    with tab1:
        st.subheader("4.3 Estadistica Descriptiva")
        df_desc = calculate_descriptive_statistics(df_f)
        st.dataframe(df_desc, use_container_width=True)
        st.markdown("---")
        st.subheader("4.5 Outliers (Isolation Forest)")
        with st.spinner("Detectando anomalias..."):
            df_out = cached_outliers(df_f)
        if not df_out.empty:
            st.info(f"{len(df_out)} registros anomalos ({len(df_out)/len(df_f)*100:.1f}%)")
            st.dataframe(df_out.head(20), use_container_width=True)
            render_download_button(df_out, "outliers.csv")
        else:
            st.success("No se detectaron outliers.")
    with tab2:
        st.subheader("4.4 Ajuste de Distribuciones")
        df_dist = fit_distributions(df_f)
        if not df_dist.empty:
            st.dataframe(df_dist, use_container_width=True)
        st.plotly_chart(plot_distribuciones_log(df_f), use_container_width=True)
    with tab3:
        st.subheader("4.6 Concentracion (Gini, HHI)")
        conc = calculate_concentration(df_f)
        if conc:
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("HHI", f"{conc.get('hhi',0):,.0f}")
            with col2: st.metric("Gini", f"{conc.get('gini',0):.3f}")
            with col3: st.metric("Top 1", f"{conc.get('top1_share',0):.1f}%")
        st.plotly_chart(plot_ex_cana_donuts(df_f), use_container_width=True)
    with tab4:
        st.subheader("4.7 Series de Tiempo (STL)")
        with st.spinner("Ejecutando STL..."):
            df_stl = cached_time_series(df_f)
        if not df_stl.empty:
            st.dataframe(df_stl, use_container_width=True)
        st.subheader("4.8 Estacionalidad A vs B")
        with st.spinner("Ejecutando Wilcoxon..."):
            df_est = cached_seasonality(df_f)
        if not df_est.empty:
            st.dataframe(df_est.head(15), use_container_width=True)
            render_download_button(df_est, "estacionalidad_ab.csv")
    with tab5:
        st.subheader("4.9 Location Quotient")
        st.plotly_chart(plot_lq_heatmap(df_f, top_n=15), use_container_width=True)
        st.subheader("4.10 Shannon-Wiener")
        st.plotly_chart(plot_shannon_barras(df_f, min_area=1000), use_container_width=True)
    with tab6:
        st.subheader("4.13 CAGR por Cultivo")
        st.plotly_chart(plot_cagr_divergente(df_f, min_prod=1000), use_container_width=True)
        st.subheader("4.11 Elasticidad")
        elast = calculate_elasticity(df_f)
        if "error" not in elast:
            st.metric("Elasticidad", f"{elast['elasticidad']:.3f}")
            st.info(f"Un 1% de aumento en area genera ~{elast['elasticidad']:.2f}% en produccion.")

run_safe(main)
