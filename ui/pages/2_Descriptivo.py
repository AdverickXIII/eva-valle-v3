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
from ui.charts.ts_charts import (plot_serie_produccion, plot_shocks, plot_estacionalidad_ab)
from ui.charts.spatial import plot_lq_heatmap, plot_shannon_barras
from core.analytics.descriptive import calculate_descriptive_statistics
from core.analytics.distributions import fit_distributions
from core.analytics.outliers import detect_multivariate_outliers
from core.analytics.concentration import calculate_concentration
from core.analytics.time_series import analyze_time_series
from core.analytics.seasonality import test_seasonality_ab
from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity
from core.analytics.lq_table import lq_top
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
        st.subheader("4.6 Concentracion: con caña vs sin caña")

        # Calcular ambos escenarios
        conc_con = calculate_concentration(df_f)
        df_sin_cana = df_f[df_f["cultivo"] != "Caña"]
        conc_sin = calculate_concentration(df_sin_cana) if not df_sin_cana.empty else {}

        # Calcular N80 (cultivos que explican el 80% de la produccion)
        def calcular_n80(sub):
            if sub.empty:
                return 0
            prod = sub.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
            tot = prod.sum()
            if tot == 0:
                return 0
            cum = (prod.cumsum() / tot) * 100
            return int((cum < 80).sum() + 1)

        n80_con = calcular_n80(df_f)
        n80_sin = calcular_n80(df_sin_cana)

        # Nombre del top 1
        def top1_name(sub):
            if sub.empty:
                return "-"
            prod = sub.groupby("cultivo")["produccion_t"].sum()
            return prod.idxmax() if not prod.empty else "-"

        top1_con_name = top1_name(df_f)
        top1_sin_name = top1_name(df_sin_cana)

        # Tabla dual
        hhi_con = conc_con.get("hhi", 0)
        hhi_sin = conc_sin.get("hhi", 0)
        gini_con = conc_con.get("gini", 0)
        gini_sin = conc_sin.get("gini", 0)
        top1_con = conc_con.get("top1_share", 0)
        top1_sin = conc_sin.get("top1_share", 0)

        tabla = pd.DataFrame({
            "Indicador": ["HHI", "Gini", f"Top 1 ({top1_con_name})", f"Top 1 ({top1_sin_name})", "Cultivos que explican 80%"],
            "Con cana": [f"{hhi_con:,.0f}", f"{gini_con:.3f}", f"{top1_con:.1f}%", "-", str(n80_con)],
            "Sin cana": [f"{hhi_sin:,.0f}", f"{gini_sin:.3f}", "-", f"{top1_sin:.1f}%", str(n80_sin)],
        })
        st.dataframe(tabla, use_container_width=True, hide_index=True)

        st.info(
            "💡 **Interpretacion dual:** el HHI salta de "
            f"**{hhi_con:,.0f}** (monocultivo extremo, caña domina) a "
            f"**{hhi_sin:,.0f}** (zona diversificada). "
            f"Sin caña emergen **{n80_sin} cultivos** que explican el 80% de la producción restante."
        )

        st.plotly_chart(plot_ex_cana_donuts(df_f), use_container_width=True)

    with tab4:
        st.subheader("4.7 Series de Tiempo (STL)")
        with st.spinner("Ejecutando STL..."):
            df_stl = cached_time_series(df_f)
        if not df_stl.empty:
            st.dataframe(df_stl, use_container_width=True)
            st.caption("Dickey-Fuller con p > 0.05 = serie **no estacionaria**: tiene "
                       "tendencia propia (crecimiento estructural), por eso se modela aparte.")
        colA, colB = st.columns(2)
        with colA:
            st.plotly_chart(plot_serie_produccion(df_f), use_container_width=True)
        with colB:
            st.plotly_chart(plot_shocks(df_f), use_container_width=True)
        st.caption("Rojo = ano que se desvio >2% de la tendencia (candidato a shock: "
                   "clima, paro, plaga). Verde = comportamiento normal.")

        st.subheader("4.8 Estacionalidad A vs B")
        with st.spinner("Ejecutando Wilcoxon..."):
            df_est = cached_seasonality(df_f)
        if not df_est.empty:
            st.plotly_chart(plot_estacionalidad_ab(df_est), use_container_width=True)
            st.caption("Verde = diferencia significativa entre semestres (p < 0.05): "
                       "cultivo con estacionalidad marcada. Gris = no significativa.")
            st.dataframe(df_est.head(15), use_container_width=True)
            render_download_button(df_est, "estacionalidad_ab.csv")

    with tab5:
        st.subheader("4.9 Location Quotient")
        sin_cana = st.checkbox("Analizar sin cana (economia agricola real)", value=True,
                               help="Con cana, los LQ se inflan: la cana aplasta los porcentajes departamentales.")
        st.plotly_chart(plot_lq_heatmap(df_f, top_n=15, excluye_cana=sin_cana), use_container_width=True)
        st.markdown("**Top 20 especializaciones (LQ)** — municipios vs grupos de cultivo:")
        solo_pesadas = st.checkbox("Solo vocaciones con peso (participacion municipal >= 5%)", value=True)
        df_lq = lq_top(df_f, 200, excluye_cana=sin_cana)
        if solo_pesadas:
            df_lq = df_lq[df_lq['share_municipio_pct'] >= 5].head(20)
        else:
            df_lq = df_lq.head(20)
        st.dataframe(df_lq.round(2), use_container_width=True, hide_index=True)
        st.caption("LQ = (% del grupo en el municipio) / (% del grupo en el Valle). "
                   "LQ > 1 = especializacion; LQ >= 4 = vocacion fuerte.")

        st.subheader("4.10 Shannon-Wiener")
        st.plotly_chart(plot_shannon_barras(df_f, min_area=1000), use_container_width=True)
        st.markdown("""
**Matriz de decision (LQ x Shannon):**
| Combinacion | Lectura | Accion sugerida |
|---|---|---|
| LQ alto + Shannon bajo | Especializado y dependiente | Proteger la cadena + diversificar marginalmente |
| LQ alto + Shannon alto | Especializado con colchon | Fortalecer la vocacion |
| LQ bajo + Shannon alto | Diversificado sin vocacion clara | Detectar cadenas emergentes |
| LQ bajo + Shannon bajo | Sin vocacion y concentrado | Prioridad de inversion publica |
""")

    with tab6:
        st.subheader("4.13 CAGR por Cultivo")
        st.plotly_chart(plot_cagr_divergente(df_f, min_prod=1000), use_container_width=True)
        st.subheader("4.11 Elasticidad")
        elast = calculate_elasticity(df_f)
        if "error" not in elast:
            st.metric("Elasticidad", f"{elast['elasticidad']:.3f}")
            st.info(f"Un 1% de aumento en area genera ~{elast['elasticidad']:.2f}% en produccion.")

run_safe(main)
