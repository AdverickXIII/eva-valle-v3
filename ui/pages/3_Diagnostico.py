"""Pagina 3: Diagnostico - Por que ocurrio?"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.performance import (cached_outliers, cached_time_series, cached_seasonality, cached_segmentation, cached_root_cause)
from ui.services.error_handler import run_safe

from config.settings import settings
from ui.components.filter_panel import render_filter_panel, apply_filters
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.diagnostics import plot_correlation_heatmap, plot_scatter_bivariado
from core.diagnostics.correlation import calculate_correlation_matrix
from core.diagnostics.comparison import compare_cycles
from core.diagnostics.segmentation import segment_municipalities
from core.diagnostics.root_cause import find_root_causes
from core.diagnostics.shock import analyze_shock
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Diagnostico | EVA Valle", page_icon="\U0001F52C", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\U0001F52C Analisis Diagnostico")
    st.caption("Responde: Por que ocurrio?")
    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return
    filters = render_filter_panel(df, key_prefix="diag")
    df_f = apply_filters(df, filters)
    if df_f.empty:
        render_empty_state("Sin datos con los filtros seleccionados")
        return
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "\U0001F517 Correlacion", "\U0001F504 Ciclos",
        "\U0001F3D8\uFE0F Segmentacion", "\U0001F333 Causa Raiz",
        "\U0001F4A5 Shock 2020",
    ])
    with tab1:
        st.subheader("6.1 Matriz de Correlacion (Spearman)")
        with st.spinner("Calculando..."):
            corr = calculate_correlation_matrix(df_f)
        if not corr.empty:
            st.plotly_chart(plot_correlation_heatmap(corr), use_container_width=True)
            st.plotly_chart(plot_scatter_bivariado(df_f, "area_cosechada_ha",
                "produccion_t", color_col="ciclo_del_cultivo", log_scale=True,
                title="Produccion vs Area"), use_container_width=True)
    with tab2:
        st.subheader("6.2 Transitorio vs Permanente")
        with st.spinner("Ejecutando Mann-Whitney..."):
            res = compare_cycles(df_f)
        if "error" not in res:
            col1, col2 = st.columns(2)
            with col1: st.metric("p-value", f"{res['p_value']:.4f}")
            with col2: st.metric("CV Transitorio", f"{res['CV_Transitorio']:.1f}%")
            st.info(res["conclusion"])
            df_box = df_f[["ciclo_del_cultivo","rendimiento_t_ha"]].dropna()
            fig = px.box(df_box, x="ciclo_del_cultivo", y="rendimiento_t_ha",
                color="ciclo_del_cultivo", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    with tab3:
        st.subheader("6.3 Segmentacion de Municipios (K-Means)")
        with st.spinner("Ejecutando K-Means..."):
            res_seg = cached_segmentation(df_f)
        if "error" not in res_seg:
            df_clusters = res_seg["df_clusters"]
            st.success(f"k optimo: {res_seg['k_optimo']} clusters")
            fig = px.scatter(df_clusters, x="area_total", y="rendimiento_medio",
                color="Perfil", hover_name="municipio", log_x=True,
                size="diversidad", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_clusters, use_container_width=True)
            render_download_button(df_clusters, "perfiles_municipios.csv")
    with tab4:
        st.subheader("6.4 Causa Raiz (Arbol de Decision)")
        with st.spinner("Entrenando arbol..."):
            res_arbol = cached_root_cause(df_f)
        if "error" not in res_arbol:
            imp_df = res_arbol["importancia_df"]
            st.metric("R2", f"{res_arbol['r2_score']:.3f}")
            fig = px.bar(imp_df.reset_index(), x="importancia", y="index",
                orientation="h", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    with tab5:
        st.subheader("6.5 Shock 2020")
        with st.spinner("Analizando..."):
            res_shock = analyze_shock(df_f)
        if "error" not in res_shock:
            df_hist = res_shock["df_historico"]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_hist["ano"], y=df_hist["var_produccion"],
                name="Var. Produccion (%)", marker_color="steelblue"))
            fig.add_trace(go.Bar(x=df_hist["ano"], y=df_hist["var_area"],
                name="Var. Area (%)", marker_color="orange"))
            fig.add_hline(y=0, line_color="white")
            fig.update_layout(barmode="group", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

run_safe(main)
