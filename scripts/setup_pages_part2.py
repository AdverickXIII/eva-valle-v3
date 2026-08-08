"""Setup pages part 2: Diagnostico + Predictivo."""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# PAGINA 3: DIAGNOSTICO
# ═══════════════════════════════════════════════════════════
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
from core.diagnostics.correlation import calculate_correlation_matrix, calculate_bivariate_stats
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
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\\U0001F52C Analisis Diagnostico")
    st.caption("Responde la pregunta: Por que ocurrio?")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py")
        return

    filters = render_filter_panel(df, key_prefix="diag")
    df_f = apply_filters(df, filters)

    if df_f.empty:
        render_empty_state("Sin datos con los filtros seleccionados")
        return

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "\\U0001F517 Correlacion",
        "\\U0001F504 Ciclos",
        "\\U0001F3D8\\uFE0F Segmentacion",
        "\\U0001F333 Causa Raiz",
        "\\U0001F4A5 Shock 2020",
    ])

    # ── Tab 1: Correlacion ───────────────────────────────────
    with tab1:
        st.subheader("6.1 Matriz de Correlacion (Spearman)")
        with st.spinner("Calculando correlaciones..."):
            corr = calculate_correlation_matrix(df_f)
        if not corr.empty:
            fig_corr = plot_correlation_heatmap(corr)
            st.plotly_chart(fig_corr, use_container_width=True)

            # Hallazgo clave
            if "produccion_t" in corr.index and "rendimiento_t_ha" in corr.columns:
                r_prod_rend = corr.loc["produccion_t", "rendimiento_t_ha"]
                st.info(
                    f"**Hallazgo clave:** Correlacion Produccion-Rendimiento = {r_prod_rend:.3f}. "
                    f"Esto indica que el rendimiento es {'dependiente' if abs(r_prod_rend) > 0.6 else 'relativamente independiente'} "
                    f"del volumen de produccion."
                )

            st.markdown("---")
            st.subheader("Relaciones Bivariadas")
            fig_scatter = plot_scatter_bivariado(
                df_f, "area_cosechada_ha", "produccion_t",
                color_col="ciclo_del_cultivo", log_scale=True,
                title="Produccion vs Area Cosechada (Log-Log)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("No se pudo calcular la matriz de correlacion.")

    # ── Tab 2: Ciclos ────────────────────────────────────────
    with tab2:
        st.subheader("6.2 Transitorio vs Permanente (Mann-Whitney U)")
        with st.spinner("Ejecutando test de Mann-Whitney..."):
            res_ciclos = compare_cycles(df_f)

        if "error" not in res_ciclos:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("p-value", f"{res_ciclos['p_value']:.4f}")
            with col2:
                st.metric("CV Transitorio", f"{res_ciclos['CV_Transitorio']:.1f}%")
            with col3:
                st.metric("CV Permanente", f"{res_ciclos['CV_Permanente']:.1f}%")

            st.info(f"**Conclusion:** {res_ciclos['conclusion']}")

            # Boxplot interactivo
            df_box = df_f[["ciclo_del_cultivo", "rendimiento_t_ha"]].dropna()
            fig_box = px.box(
                df_box, x="ciclo_del_cultivo", y="rendimiento_t_ha",
                color="ciclo_del_cultivo",
                title="Distribucion de Rendimiento por Ciclo",
                labels={"ciclo_del_cultivo": "Ciclo", "rendimiento_t_ha": "Rendimiento (t/ha)"},
            )
            fig_box.update_layout(template="plotly_dark")
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.error(res_ciclos["error"])

    # ── Tab 3: Segmentacion ──────────────────────────────────
    with tab3:
        st.subheader("6.3 Perfiles de Municipios (K-Means)")
        with st.spinner("Ejecutando K-Means con analisis de silueta..."):
            res_seg = segment_municipalities(df_f)

        if "error" not in res_seg:
            df_clusters = res_seg["df_clusters"]
            k_optimo = res_seg["k_optimo"]
            silhouette_scores = res_seg["silhouette_scores"]

            st.success(f"**k optimo seleccionado:** {k_optimo} clusters")

            # Mostrar silhouette scores
            df_sil = pd.DataFrame(silhouette_scores, columns=["k", "silhouette_score"])
            fig_sil = px.line(df_sil, x="k", y="silhouette_score", markers=True,
                title="Analisis de Silueta por numero de clusters")
            fig_sil.update_layout(template="plotly_dark")
            st.plotly_chart(fig_sil, use_container_width=True)

            # Scatter de clusters
            fig_clusters = px.scatter(
                df_clusters, x="area_total", y="rendimiento_medio",
                color="Perfil", hover_name="municipio",
                log_x=True, size="diversidad",
                title="Segmentacion de Municipios (Tamano vs Eficiencia)",
                labels={"area_total": "Area Total (ha)", "rendimiento_medio": "Rendimiento Mediano (t/ha)"},
            )
            fig_clusters.update_layout(template="plotly_dark")
            st.plotly_chart(fig_clusters, use_container_width=True)

            # Tabla de perfiles
            st.markdown("**Detalle de municipios por perfil:**")
            st.dataframe(df_clusters.sort_values("area_total", ascending=False),
                use_container_width=True)
            render_download_button(df_clusters, "perfiles_municipios.csv")
        else:
            st.error(res_seg["error"])

    # ── Tab 4: Causa Raiz ────────────────────────────────────
    with tab4:
        st.subheader("6.4 Que determina la produccion? (Arbol de Decision)")
        with st.spinner("Entrenando arbol de decision..."):
            res_arbol = find_root_causes(df_f)

        if "error" not in res_arbol:
            imp_df = res_arbol["importancia_df"]
            r2 = res_arbol["r2_score"]
            reglas = res_arbol["top_rules"]

            st.metric("R2 del Arbol", f"{r2:.3f}")

            # Bar chart de importancia
            fig_imp = px.bar(
                imp_df.reset_index(), x="importancia", y="index",
                orientation="h",
                title="Importancia de Variables en la Prediccion de Produccion",
                labels={"importancia": "Importancia", "index": "Variable"},
            )
            fig_imp.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_imp, use_container_width=True)

            st.info(
                f"**Hallazgo:** La variable mas predictiva es "
                f"**{imp_df.index[0]}** con {imp_df.iloc[0]*100:.1f}% de importancia."
            )

            # Reglas principales
            if reglas:
                st.markdown("**Reglas principales del arbol:**")
                for i, regla in enumerate(reglas, 1):
                    with st.expander(f"Regla {i} ({regla['n_registros']:,} registros)"):
                        st.code(regla["condiciones"], language=None)
                        st.metric("Produccion predicha", f"{regla['produccion_predicha']:,.0f} t")
        else:
            st.error(res_arbol["error"])

    # ── Tab 5: Shock 2020 ────────────────────────────────────
    with tab5:
        st.subheader("6.5 Impacto del Shock Exogeno (2020)")
        with st.spinner("Analizando variaciones interanuales..."):
            res_shock = analyze_shock(df_f)

        if "error" not in res_shock:
            df_hist = res_shock["df_historico"]
            impacto = res_shock.get("impacto_shock", {})

            if impacto:
                col1, col2, col3 = st.columns(3)
                with col1:
                    var_prod = impacto.get("var_produccion", 0)
                    st.metric("Var. Produccion 2020", f"{var_prod:.1f}%",
                        delta_type="negative" if var_prod < 0 else "positive")
                with col2:
                    var_area = impacto.get("var_area", 0)
                    st.metric("Var. Area 2020", f"{var_area:.1f}%",
                        delta_type="negative" if var_area < 0 else "positive")
                with col3:
                    desv = impacto.get("desviacion_vs_tendencia", 0)
                    st.metric("Desviacion vs Tendencia", f"{desv:.1f}%")

                if impacto.get("impacto_significativo"):
                    st.warning("**Impacto significativo detectado** (desviacion > 5%)")
                else:
                    st.success("El shock no desvio significativamente la tendencia productiva.")

            # Grafico de variaciones
            fig_shock = go.Figure()
            fig_shock.add_trace(go.Bar(
                x=df_hist["ano"], y=df_hist["var_produccion"],
                name="Var. Produccion (%)", marker_color="steelblue",
            ))
            fig_shock.add_trace(go.Bar(
                x=df_hist["ano"], y=df_hist["var_area"],
                name="Var. Area Sembrada (%)", marker_color="orange",
            ))
            fig_shock.add_hline(y=0, line_color="white")
            fig_shock.update_layout(
                barmode="group", template="plotly_dark",
                title="Variacion Interanual de Produccion y Area",
                xaxis_title="Anio", yaxis_title="Variacion (%)",
            )
            st.plotly_chart(fig_shock, use_container_width=True)
        else:
            st.error(res_shock["error"])


main()
'''

# ═══════════════════════════════════════════════════════════
# PAGINA 4: PREDICTIVO
# ═══════════════════════════════════════════════════════════
PAGE_PREDICTIVO = '''"""Pagina 4: Predictivo - Que podria ocurrir?"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from core.ml.features import create_features_ml
from core.ml.target_encoding import fit_target_encoding, apply_target_encoding
from core.ml.regression import train_regression
from core.ml.classification import train_classification
from core.ml.forecasting import forecast_time_series
from sklearn.model_selection import train_test_split
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Predictivo | EVA Valle", page_icon="\\U0001F916", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_resource(ttl=7200)
def run_ml_pipeline():
    """Ejecuta el pipeline ML completo (cached por 2 horas)."""
    df = load_dataset()
    if df.empty:
        return None

    # Feature engineering
    df_ml = create_features_ml(df)
    if df_ml.empty:
        return None

    # Split ANTES del target encoding (evita data leakage)
    df_train, df_test = train_test_split(
        df_ml, test_size=settings.ML_TEST_SIZE,
        random_state=settings.ML_RANDOM_STATE,
    )

    # Target encoding: fit solo con train
    encoding_maps = fit_target_encoding(df_train)
    df_train_enc = apply_target_encoding(df_train, encoding_maps)
    df_test_enc = apply_target_encoding(df_test, encoding_maps)
    df_enc = pd.concat([df_train_enc, df_test_enc], ignore_index=True)

    # Modelos
    res_reg = train_regression(df_enc, persist_model=False)
    res_clf = train_classification(df_enc, persist_model=False)
    res_forecast = forecast_time_series(df)

    return {
        "regresion": res_reg,
        "clasificacion": res_clf,
        "forecast": res_forecast,
    }


def main() -> None:
    st.title("\\U0001F916 Analisis Predictivo")
    st.caption("Responde la pregunta: Que podria ocurrir?")
    st.info(
        "\\u26A0\\uFE0F **Nota:** Los modelos se entrenan con target encoding "
        "sin data leakage (fit solo con train set)."
    )

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py")
        return

    # Ejecutar pipeline ML con spinner
    with st.spinner("Entrenando modelos ML (puede tardar 1-2 minutos)..."):
        resultados = run_ml_pipeline()

    if resultados is None:
        render_empty_state("No se pudieron entrenar los modelos")
        return

    st.markdown("---")

    # ── Seccion 1: Metricas de Regresion ─────────────────────
    st.subheader("\\U0001F4C9 7.2 Modelo de Regresion (Random Forest)")

    res_reg = resultados["regresion"]
    metricas = res_reg["metricas"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("R2", f"{metricas['R2']:.3f}",
            help="Capacidad explicativa. 1.0 = perfecto.")
    with col2:
        st.metric("MAE", f"{metricas['MAE_Toneladas']:,.0f} t",
            help="Error medio absoluto en toneladas.")
    with col3:
        st.metric("RMSE (Log)", f"{metricas['RMSE_Log']:.3f}")
    with col4:
        st.metric("N Test", f"{metricas['n_test']:,}")

    st.markdown("---")

    # ── Seccion 2: Importancia de Variables ──────────────────
    st.subheader("\\U0001F3AF Importancia de Variables")
    imp = res_reg["importancia"]
    fig_imp = px.bar(
        imp.reset_index(), x="importance" if "importance" in imp.reset_index().columns else imp.name,
        y=imp.index.tolist(),
        orientation="h",
        title="Que variables predicen mejor la produccion?",
        labels={"value": "Importancia", "variable": "Variable"},
    )
    fig_imp.update_layout(template="plotly_dark", height=350)
    st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("---")

    # ── Seccion 3: Real vs Predicho ──────────────────────────
    st.subheader("\\U0001F4CA Real vs Predicho")
    df_residuos = res_reg["df_residuos"]

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=df_residuos["Real_t"], y=df_residuos["Pred_t"],
        mode="markers", marker=dict(opacity=0.4, size=5),
        name="Predicciones",
    ))
    max_val = max(df_residuos["Real_t"].max(), df_residuos["Pred_t"].max())
    fig_scatter.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines", line=dict(color="red", dash="dash"),
        name="Linea 45 grados",
    ))
    fig_scatter.update_layout(
        template="plotly_dark",
        title=f"Real vs Predicho (R2 = {metricas['R2']:.3f})",
        xaxis_title="Produccion Real (t)",
        yaxis_title="Produccion Predicha (t)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    render_download_button(df_residuos, "predicciones_regresion.csv")

    st.markdown("---")

    # ── Seccion 4: Clasificacion ─────────────────────────────
    st.subheader("\\U0001F6A8 7.3 Modelo de Clasificacion (Perdida de Cosecha)")

    res_clf = resultados["clasificacion"]
    metricas_clf = res_clf.get("metricas", {})

    if "error" not in metricas_clf:
        col1, col2 = st.columns(2)
        with col1:
            auc = metricas_clf.get("ROC_AUC", float("nan"))
            if not np.isnan(auc):
                st.metric("ROC-AUC", f"{auc:.3f}",
                    help="Capacidad de detectar perdidas. 1.0 = perfecto.")
            else:
                st.metric("ROC-AUC", "N/A")
        with col2:
            precision = metricas_clf.get("1", {}).get("precision", "N/A")
            if precision != "N/A":
                st.metric("Precision (Perdida)", f"{precision:.3f}")
            else:
                st.metric("Precision (Perdida)", "N/A")
    else:
        st.warning(metricas_clf["error"])

    st.markdown("---")

    # ── Seccion 5: Proyeccion Holt-Winters ───────────────────
    st.subheader("\\U0001F4C8 7.4 Proyeccion Tendencial (Holt-Winters)")

    res_forecast = resultados["forecast"]
    if "error" not in res_forecast:
        df_proy = res_forecast["df_proyeccion"]
        metodo = res_forecast.get("metodo", "desconocido")

        if metodo == "holt_winters":
            st.success("Proyeccion generada con Holt-Winters (tendencia aditiva).")
        else:
            st.warning(f"Metodo: {metodo}. Serie muy corta para Holt-Winters.")

        fig_forecast = go.Figure()

        # Historico
        df_hist = df_proy[df_proy["tipo"] == "Historico"]
        fig_forecast.add_trace(go.Scatter(
            x=df_hist["periodo"], y=df_hist.get("produccion_t", df_hist.get("produccion_predicha")),
            mode="lines+markers", name="Historico Real",
            line=dict(color="steelblue", width=2),
        ))

        # Pronostico
        df_future = df_proy[df_proy["tipo"] == "Pronostico"]
        if not df_future.empty:
            fig_forecast.add_trace(go.Scatter(
                x=df_future["periodo"], y=df_future["produccion_predicha"],
                mode="lines+markers", name="Pronostico 2025",
                line=dict(color="red", dash="dash", width=2),
                marker=dict(size=10, symbol="star"),
            ))

        fig_forecast.update_layout(
            template="plotly_dark",
            title="Proyeccion de Produccion Total - Valle del Cauca",
            xaxis_title="Periodo", yaxis_title="Toneladas",
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

        render_download_button(df_proy, "proyeccion_macro.csv")

        st.info(
            "\\u26A0\\uFE0F **Advertencia:** Esta proyeccion se basa en ~12 puntos "
            "de datos. Es una tendencia pura sin considerar shocks externos, "
            "politica agricola ni cambio climatico."
        )
    else:
        st.error(res_forecast["error"])


main()
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "ui/pages/3_\\U0001F52C_Diagnostico.py": PAGE_DIAGNOSTICO,
        "ui/pages/4_\\U0001F916_Predictivo.py": PAGE_PREDICTIVO,
    }

    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")

    print(f"\n{len(archivos)} paginas creadas.")
    print("Ejecuta: streamlit run app.py")