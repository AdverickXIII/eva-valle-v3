"""Setup paginas finales parte 1: Dashboard, Descriptivo, Diagnostico."""
from pathlib import Path

PAGE_DASHBOARD = '''"""Pagina 1: Dashboard - Vista general."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.filter_panel import render_filter_panel, apply_filters
from ui.components.metrics_cards import render_kpi_row
from ui.charts.historical import plot_historico_cruces, plot_rendimiento_historico
from ui.charts.concentration import plot_pareto_concentracion
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Dashboard | EVA Valle", page_icon="\\U0001F4CA", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\\U0001F4CA Dashboard - EVA Valle del Cauca")
    st.caption("Vista general de la produccion agricola 2019-2024")
    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return
    filters = render_filter_panel(df, key_prefix="dash")
    df_f = apply_filters(df, filters)
    if df_f.empty:
        render_empty_state("Sin datos con los filtros seleccionados")
        return
    st.markdown("---")
    prod_total = df_f["produccion_t"].sum()
    area_total = df_f["area_sembrada_ha"].sum()
    rend_prom = df_f["produccion_t"].sum() / max(df_f["area_cosechada_ha"].sum(), 1)
    n_cultivos = df_f["cultivo"].nunique()
    render_kpi_row([
        {"label": "Produccion Total", "value": f"{prod_total:,.0f} t", "icon": "\\U0001F33E"},
        {"label": "Area Sembrada", "value": f"{area_total:,.0f} ha", "icon": "\\U0001F4D0"},
        {"label": "Rendimiento Prom.", "value": f"{rend_prom:.1f} t/ha", "icon": "\\U0001F4C8"},
        {"label": "Cultivos Activos", "value": f"{n_cultivos}", "icon": "\\U0001F331"},
    ])
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("\\U0001F4C9 Evolucion Historica")
        st.plotly_chart(plot_historico_cruces(df_f), use_container_width=True)
    with col2:
        st.subheader("\\U0001F4CA Rendimiento Promedio")
        st.plotly_chart(plot_rendimiento_historico(df_f), use_container_width=True)
    st.markdown("---")
    st.subheader("\\U0001F3AF Concentracion de la Produccion (Pareto)")
    st.plotly_chart(plot_pareto_concentracion(df_f, top_n=10), use_container_width=True)
    st.markdown("---")
    st.subheader("\\U0001F3D8\\uFE0F Resumen por Municipio")
    resumen = (df_f.groupby("municipio")
        .agg(produccion_t=("produccion_t","sum"), area=("area_sembrada_ha","sum"),
             cultivos=("cultivo","nunique"))
        .sort_values("produccion_t", ascending=False).reset_index())
    st.dataframe(resumen, use_container_width=True, height=400)

main()
'''

PAGE_DESCRIPTIVO = '''"""Pagina 2: Descriptivo - 12 analisis del Paso 4."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

st.set_page_config(page_title="Descriptivo | EVA Valle", page_icon="\\U0001F4C8", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\\U0001F4C8 Analisis Descriptivo Profundo")
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
        "\\U0001F4CA Descriptiva", "\\U0001F4C9 Distribuciones",
        "\\U0001F3AF Concentracion", "\\U0001F4C5 Series de Tiempo",
        "\\U0001F30D Espacial", "\\U0001F4C8 Crecimiento",
    ])
    with tab1:
        st.subheader("4.3 Estadistica Descriptiva")
        df_desc = calculate_descriptive_statistics(df_f)
        st.dataframe(df_desc, use_container_width=True)
        st.markdown("---")
        st.subheader("4.5 Outliers (Isolation Forest)")
        with st.spinner("Detectando anomalias..."):
            df_out = detect_multivariate_outliers(df_f)
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
            df_stl = analyze_time_series(df_f)
        if not df_stl.empty:
            st.dataframe(df_stl, use_container_width=True)
        st.subheader("4.8 Estacionalidad A vs B")
        with st.spinner("Ejecutando Wilcoxon..."):
            df_est = test_seasonality_ab(df_f)
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

main()
'''

PAGE_DIAGNOSTICO = '''"""Pagina 3: Diagnostico - Por que ocurrio?"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

st.set_page_config(page_title="Diagnostico | EVA Valle", page_icon="\\U0001F52C", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\\U0001F52C Analisis Diagnostico")
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
        "\\U0001F517 Correlacion", "\\U0001F504 Ciclos",
        "\\U0001F3D8\\uFE0F Segmentacion", "\\U0001F333 Causa Raiz",
        "\\U0001F4A5 Shock 2020",
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
            res_seg = segment_municipalities(df_f)
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
            res_arbol = find_root_causes(df_f)
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

main()
'''

if __name__ == "__main__":
    archivos = {
        "ui/pages/1_Dashboard.py": PAGE_DASHBOARD,
        "ui/pages/2_Descriptivo.py": PAGE_DESCRIPTIVO,
        "ui/pages/3_Diagnostico.py": PAGE_DIAGNOSTICO,
    }
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
    print(f"\n{len(archivos)} paginas creadas (parte 1).")
    print("Ejecuta ahora: python scripts\\setup_pages_final_p2.py")