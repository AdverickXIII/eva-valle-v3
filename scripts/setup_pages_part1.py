"""Setup pages part 1: Dashboard + Descriptivo."""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# PAGINA 1: DASHBOARD
# ═══════════════════════════════════════════════════════════
PAGE_DASHBOARD = '''"""Pagina 1: Dashboard - Vista general con KPIs y tendencias."""
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
    """Carga el dataset del modelo conceptual con cache."""
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\\U0001F4CA Dashboard - EVA Valle del Cauca")
    st.caption("Vista general de la produccion agricola 2019-2024")

    # Cargar datos
    df = load_dataset()
    if df.empty:
        render_empty_state(
            "Dataset no encontrado",
            hint="Ejecuta el pipeline primero: python scripts/run_pipeline.py",
        )
        return

    # Filtros
    filters = render_filter_panel(df, key_prefix="dash")
    df_filtered = apply_filters(df, filters)

    if df_filtered.empty:
        render_empty_state("Sin datos con los filtros seleccionados")
        return

    st.markdown("---")

    # ── KPIs principales ─────────────────────────────────────
    prod_total = df_filtered["produccion_t"].sum()
    area_total = df_filtered["area_sembrada_ha"].sum()
    rend_prom = df_filtered["produccion_t"].sum() / max(df_filtered["area_cosechada_ha"].sum(), 1)
    n_cultivos = df_filtered["cultivo"].nunique()
    n_municipios = df_filtered["municipio"].nunique()

    render_kpi_row([
        {"label": "Produccion Total", "value": f"{prod_total:,.0f} t", "icon": "\\U0001F33E", "delta_type": "neutral"},
        {"label": "Area Sembrada", "value": f"{area_total:,.0f} ha", "icon": "\\U0001F4D0", "delta_type": "neutral"},
        {"label": "Rendimiento Prom.", "value": f"{rend_prom:.1f} t/ha", "icon": "\\U0001F4C8", "delta_type": "neutral"},
        {"label": "Cultivos Activos", "value": f"{n_cultivos}", "icon": "\\U0001F331", "delta_type": "neutral"},
    ])

    st.markdown("---")

    # ── Graficos principales ─────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("\\U0001F4C9 Evolucion Historica")
        fig_hist = plot_historico_cruces(df_filtered)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.subheader("\\U0001F4CA Rendimiento Promedio")
        fig_rend = plot_rendimiento_historico(df_filtered)
        st.plotly_chart(fig_rend, use_container_width=True)

    st.markdown("---")

    # ── Pareto de concentracion ──────────────────────────────
    st.subheader("\\U0001F3AF Concentracion de la Produccion (Pareto)")
    fig_pareto = plot_pareto_concentracion(df_filtered, top_n=10)
    st.plotly_chart(fig_pareto, use_container_width=True)

    # ── Tabla resumen por municipio ──────────────────────────
    st.markdown("---")
    st.subheader("\\U0001F3D8\\uFE0F Resumen por Municipio")

    resumen_muni = (
        df_filtered.groupby("municipio")
        .agg(
            produccion_t=("produccion_t", "sum"),
            area_sembrada_ha=("area_sembrada_ha", "sum"),
            cultivos=("cultivo", "nunique"),
            registros=("municipio", "count"),
        )
        .sort_values("produccion_t", ascending=False)
        .reset_index()
    )
    st.dataframe(resumen_muni, use_container_width=True, height=400)


main()
'''

# ═══════════════════════════════════════════════════════════
# PAGINA 2: DESCRIPTIVO
# ═══════════════════════════════════════════════════════════
PAGE_DESCRIPTIVO = '''"""Pagina 2: Descriptivo - 12 analisis estadisticos del Paso 4."""
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
    """Carga el dataset del modelo conceptual con cache."""
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\\U0001F4C8 Analisis Descriptivo Profundo")
    st.caption("12 analisis estadisticos del Paso 4 - Economia espacial y distribuciones")

    # Cargar datos
    df = load_dataset()
    if df.empty:
        render_empty_state(
            "Dataset no encontrado",
            hint="Ejecuta el pipeline primero: python scripts/run_pipeline.py",
        )
        return

    # Filtros
    filters = render_filter_panel(df, key_prefix="desc")
    df_filtered = apply_filters(df, filters)

    if df_filtered.empty:
        render_empty_state("Sin datos con los filtros seleccionados")
        return

    st.markdown("---")

    # ── Tabs para los 12 analisis ────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "\\U0001F4CA Descriptiva",
        "\\U0001F4C9 Distribuciones",
        "\\U0001F3AF Concentracion",
        "\\U0001F4C5 Series de Tiempo",
        "\\U0001F30D Espacial",
        "\\U0001F4C8 Crecimiento",
    ])

    # ── Tab 1: Estadistica descriptiva ───────────────────────
    with tab1:
        st.subheader("4.3 Estadistica Descriptiva Profunda")
        df_desc = calculate_descriptive_statistics(df_filtered)
        st.dataframe(df_desc, use_container_width=True)

        st.markdown("---")
        st.subheader("4.5 Outliers Multivariados (Isolation Forest)")
        with st.spinner("Detectando anomalias..."):
            df_out = detect_multivariate_outliers(df_filtered)
        if not df_out.empty:
            st.info(f"Se detectaron {len(df_out)} registros anomalos ({len(df_out)/len(df_filtered)*100:.1f}%)")
            st.dataframe(df_out.head(20), use_container_width=True)
            render_download_button(df_out, "outliers_multivariados.csv")
        else:
            st.success("No se detectaron outliers.")

    # ── Tab 2: Distribuciones ────────────────────────────────
    with tab2:
        st.subheader("4.4 Ajuste de Distribuciones (KS-test)")
        df_dist = fit_distributions(df_filtered)
        if not df_dist.empty:
            st.dataframe(df_dist, use_container_width=True)
        else:
            st.warning("Muestra insuficiente para ajuste de distribuciones.")

        st.markdown("---")
        st.subheader("Distribuciones Logaritmicas")
        fig_dist = plot_distribuciones_log(df_filtered)
        st.plotly_chart(fig_dist, use_container_width=True)

    # ── Tab 3: Concentracion ─────────────────────────────────
    with tab3:
        st.subheader("4.6 Concentracion (Gini, HHI)")
        conc = calculate_concentration(df_filtered)
        if conc:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("HHI", f"{conc.get('hhi', 0):,.0f}", help="Max 10,000. >2,500 = altamente concentrado")
            with col2:
                st.metric("Gini", f"{conc.get('gini', 0):.3f}", help="0 = igualdad perfecta, 1 = concentracion maxima")
            with col3:
                st.metric("Top 1 Cultivo", f"{conc.get('top1_share', 0):.1f}%")

        st.markdown("---")
        st.subheader("4.14 Analisis Ex-Cana")
        ex_cana = analyze_ex_cana(df_filtered)
        if "error" not in ex_cana:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("HHI Con Cana", f"{ex_cana.get('HHI_Con_Cana', 0):,.0f}")
            with col2:
                st.metric("HHI Sin Cana", f"{ex_cana.get('HHI_Sin_Cana', 0):,.0f}")
            fig_donuts = plot_ex_cana_donuts(df_filtered)
            st.plotly_chart(fig_donuts, use_container_width=True)
        else:
            st.error(ex_cana["error"])

    # ── Tab 4: Series de tiempo ──────────────────────────────
    with tab4:
        st.subheader("4.7 Series de Tiempo (STL + Dickey-Fuller)")
        with st.spinner("Ejecutando descomposicion STL..."):
            df_stl = analyze_time_series(df_filtered)
        if not df_stl.empty:
            st.dataframe(df_stl, use_container_width=True)
            es_estacionaria = df_stl["es_estacionaria"].iloc[0] if "es_estacionaria" in df_stl.columns else None
            if es_estacionaria:
                st.success("La serie ES estacionaria (p < 0.05)")
            elif es_estacionaria is not None:
                st.warning("La serie NO es estacionaria. Tiene tendencia.")
        else:
            st.warning("Serie muy corta para analisis STL.")

        st.markdown("---")
        st.subheader("4.8 Estacionalidad A vs B (Wilcoxon)")
        with st.spinner("Ejecutando test de Wilcoxon..."):
            df_est = test_seasonality_ab(df_filtered)
        if not df_est.empty:
            st.dataframe(df_est.head(15), use_container_width=True)
            n_sig = df_est["diferencia_significativa"].sum()
            st.info(f"{n_sig} de {len(df_est)} cultivos muestran diferencia significativa A vs B")
            render_download_button(df_est, "estacionalidad_ab.csv")
        else:
            st.warning("No se encontraron pares A/B suficientes.")

    # ── Tab 5: Espacial ──────────────────────────────────────
    with tab5:
        st.subheader("4.9 Especializacion Territorial (Location Quotient)")
        with st.spinner("Calculando LQ..."):
            df_lq = calculate_location_quotient(df_filtered)
        if not df_lq.empty:
            fig_lq = plot_lq_heatmap(df_filtered, top_n=15)
            st.plotly_chart(fig_lq, use_container_width=True)

            top_lq = df_lq[df_lq["LQ"] > 1].sort_values("LQ", ascending=False).head(10)
            st.markdown("**Top 10 Especializaciones (LQ > 1):**")
            st.dataframe(top_lq, use_container_width=True)

        st.markdown("---")
        st.subheader("4.10 Diversificacion (Shannon-Wiener)")
        with st.spinner("Calculando Shannon-Wiener..."):
            df_shannon = calculate_shannon_diversity(df_filtered)
        if not df_shannon.empty:
            fig_shannon = plot_shannon_barras(df_filtered, min_area=1000)
            st.plotly_chart(fig_shannon, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top 5 Mas Diversificados:**")
                st.dataframe(df_shannon.head(), use_container_width=True)
            with col2:
                st.markdown("**Top 5 Monocultores:**")
                st.dataframe(df_shannon.tail(), use_container_width=True)

    # ── Tab 6: Crecimiento ───────────────────────────────────
    with tab6:
        st.subheader("4.13 CAGR por Cultivo (2019-2024)")
        with st.spinner("Calculando CAGR..."):
            df_cagr = calculate_cagr(df_filtered)
        if not df_cagr.empty:
            fig_cagr = plot_cagr_divergente(df_filtered, min_prod=1000)
            st.plotly_chart(fig_cagr, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top 5 Crecimiento:**")
                st.dataframe(df_cagr.head(), use_container_width=True)
            with col2:
                st.markdown("**Top 5 Decrecimiento:**")
                st.dataframe(df_cagr.tail(), use_container_width=True)
            render_download_button(df_cagr, "cagr_cultivos.csv")

        st.markdown("---")
        st.subheader("4.11 Elasticidades y 4.12 Inferencia")
        col1, col2 = st.columns(2)
        with col1:
            elasticidad = calculate_elasticity(df_filtered)
            if "error" not in elasticidad:
                st.metric("Elasticidad Prod/Area", f"{elasticidad['elasticidad']:.3f}")
                st.caption(f"R2 = {elasticidad['r_cuadrado']:.3f}")
                st.info(f"Un 1% de aumento en area genera ~{elasticidad['elasticidad']:.2f}% en produccion.")
            else:
                st.warning(elasticidad["error"])
        with col2:
            df_inf = run_inferential_test(df_filtered)
            if not df_inf.empty:
                p_val = df_inf["p_value"].iloc[0]
                st.metric("Kruskal-Wallis p-value", f"{p_val:.2e}")
                if p_val < 0.05:
                    st.success("Hay diferencia significativa de rendimiento entre municipios.")
                else:
                    st.info("No hay evidencia de diferencia entre municipios.")


main()
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "ui/pages/1_\\U0001F4CA_Dashboard.py": PAGE_DASHBOARD,
        "ui/pages/2_\\U0001F4C8_Descriptivo.py": PAGE_DESCRIPTIVO,
    }

    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")

    print(f"\n{len(archivos)} paginas creadas.")
    print("Ejecuta: streamlit run app.py")