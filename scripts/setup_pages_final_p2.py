"""Setup paginas finales parte 2: Predictivo, Auditoria, Configuracion."""
from pathlib import Path

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
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

@st.cache_resource(ttl=7200)
def run_ml_pipeline():
    df = load_dataset()
    if df.empty: return None
    df_ml = create_features_ml(df)
    if df_ml.empty: return None
    df_train, df_test = train_test_split(df_ml, test_size=settings.ML_TEST_SIZE,
        random_state=settings.ML_RANDOM_STATE)
    encoding_maps = fit_target_encoding(df_train)
    df_train_enc = apply_target_encoding(df_train, encoding_maps)
    df_test_enc = apply_target_encoding(df_test, encoding_maps)
    df_enc = pd.concat([df_train_enc, df_test_enc], ignore_index=True)
    res_reg = train_regression(df_enc, persist_model=False)
    res_clf = train_classification(df_enc, persist_model=False)
    res_forecast = forecast_time_series(df)
    return {"regresion": res_reg, "clasificacion": res_clf, "forecast": res_forecast}

def main() -> None:
    st.title("\\U0001F916 Analisis Predictivo")
    st.caption("Responde: Que podria ocurrir?")
    st.info("\\u26A0\\uFE0F Los modelos usan target encoding sin data leakage (fit solo con train).")
    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return
    with st.spinner("Entrenando modelos ML (1-2 minutos)..."):
        resultados = run_ml_pipeline()
    if resultados is None:
        render_empty_state("No se pudieron entrenar los modelos")
        return
    st.markdown("---")
    st.subheader("\\U0001F4C9 7.2 Regresion (Random Forest)")
    res_reg = resultados["regresion"]
    metricas = res_reg["metricas"]
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("R2", f"{metricas['R2']:.3f}")
    with col2: st.metric("MAE", f"{metricas['MAE_Toneladas']:,.0f} t")
    with col3: st.metric("RMSE (Log)", f"{metricas['RMSE_Log']:.3f}")
    with col4: st.metric("N Test", f"{metricas['n_test']:,}")
    st.markdown("---")
    st.subheader("\\U0001F3AF Importancia de Variables")
    imp = res_reg["importancia"]
    fig_imp = px.bar(imp.reset_index(), x=imp.name, y=imp.index.tolist(),
        orientation="h", template="plotly_dark", height=350)
    st.plotly_chart(fig_imp, use_container_width=True)
    st.markdown("---")
    st.subheader("\\U0001F4CA Real vs Predicho")
    df_res = res_reg["df_residuos"]
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(x=df_res["Real_t"], y=df_res["Pred_t"],
        mode="markers", marker=dict(opacity=0.4, size=5), name="Predicciones"))
    max_val = max(df_res["Real_t"].max(), df_res["Pred_t"].max())
    fig_scatter.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val],
        mode="lines", line=dict(color="red", dash="dash"), name="Linea 45"))
    fig_scatter.update_layout(template="plotly_dark",
        title=f"Real vs Predicho (R2 = {metricas['R2']:.3f})")
    st.plotly_chart(fig_scatter, use_container_width=True)
    render_download_button(df_res, "predicciones_regresion.csv")
    st.markdown("---")
    st.subheader("\\U0001F4C8 7.4 Proyeccion Holt-Winters")
    res_forecast = resultados["forecast"]
    if "error" not in res_forecast:
        df_proy = res_forecast["df_proyeccion"]
        fig_f = go.Figure()
        df_hist = df_proy[df_proy["tipo"] == "Historico"]
        fig_f.add_trace(go.Scatter(x=df_hist["periodo"],
            y=df_hist.get("produccion_t", df_hist.get("produccion_predicha")),
            mode="lines+markers", name="Historico", line=dict(color="steelblue")))
        df_future = df_proy[df_proy["tipo"] == "Pronostico"]
        if not df_future.empty:
            fig_f.add_trace(go.Scatter(x=df_future["periodo"],
                y=df_future["produccion_predicha"], mode="lines+markers",
                name="Pronostico 2025", line=dict(color="red", dash="dash")))
        fig_f.update_layout(template="plotly_dark",
            title="Proyeccion de Produccion Total")
        st.plotly_chart(fig_f, use_container_width=True)
        render_download_button(df_proy, "proyeccion_macro.csv")

main()
'''

PAGE_AUDITORIA = '''"""Pagina 5: Auditoria - Calidad de datos."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.metrics_cards import render_kpi_row
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
import plotly.express as px

st.set_page_config(page_title="Auditoria | EVA Valle", page_icon="\\U0001F50D", layout="wide")

@st.cache_data(ttl=3600)
def load_audit_report() -> pd.DataFrame:
    path = settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\\U0001F50D Auditoria de Calidad de Datos")
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
        {"label": "Errores", "value": str(n_errors), "icon": "\\u274C"},
        {"label": "Advertencias", "value": str(n_warnings), "icon": "\\u26A0\\uFE0F"},
        {"label": "Info", "value": str(n_info), "icon": "\\u2139\\uFE0F"},
        {"label": "Total", "value": str(len(df_audit)), "icon": "\\U0001F4CB"},
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

main()
'''

PAGE_CONFIGURACION = '''"""Pagina 6: Configuracion - Estado y acciones."""
from __future__ import annotations
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings

st.set_page_config(page_title="Configuracion | EVA Valle", page_icon="\\u2699\\uFE0F", layout="wide")

def main() -> None:
    st.title("\\u2699\\uFE0F Configuracion del Sistema")
    st.caption("Estado del pipeline, descargas y parametros")
    st.markdown("---")
    st.subheader("\\U0001F4CA Estado del Pipeline")
    archivos_clave = {
        "Dataset estandarizado": settings.DATA_PROCESSED_PATH / "01_clean" / "eva_agricola_valle_2019_2024_estandarizado.csv",
        "Modelo conceptual": settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
        "Reporte auditoria": settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv",
    }
    for nombre, path in archivos_clave.items():
        col1, col2 = st.columns([3, 1])
        with col1: st.markdown(f"**{nombre}**  \\n`{path}`")
        with col2:
            if path.exists():
                size_mb = path.stat().st_size / (1024*1024)
                st.success(f"\\u2705 {size_mb:.2f} MB")
            else:
                st.warning("\\u274C No existe")
    st.markdown("---")
    st.subheader("\\u2699\\uFE0F Parametros del Sistema")
    col1, col2 = st.columns(2)
    with col1:
        st.code(f"PROJECT: {settings.PROJECT_NAME}\\nENV: {settings.ENV}\\nROOT: {settings.PROJECT_ROOT}")
    with col2:
        st.code(f"ML_RANDOM_STATE: {settings.ML_RANDOM_STATE}\\nML_TEST_SIZE: {settings.ML_TEST_SIZE}")
    st.markdown("---")
    st.subheader("\\u25B6\\uFE0F Ejecutar Pasos del Pipeline")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\\U0001F504 Paso 1+2: Carga y Auditoria"):
            with st.spinner("Ejecutando..."):
                try:
                    from core.audit.loader import load_and_standardize
                    from core.audit import run_all_audits
                    from core.audit.report import generate_audit_report
                    df_valle, _ = load_and_standardize()
                    findings = run_all_audits(df_valle)
                    generate_audit_report(findings)
                    st.success(f"\\u2705 Completado: {len(findings)} hallazgos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")
        if st.button("\\U0001F3D7\\uFE0F Paso 3: Modelado"):
            with st.spinner("Ejecutando..."):
                try:
                    from core.modeling import run_conceptual_modeling
                    df_modelo, _ = run_conceptual_modeling()
                    st.success(f"\\u2705 Completado: {len(df_modelo):,} registros")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")
    with col2:
        if st.button("\\U0001F4C8 Paso 4: Analisis Descriptivo"):
            with st.spinner("Ejecutando 12 analisis..."):
                try:
                    from core.analytics import run_all_analytics
                    artefactos = run_all_analytics()
                    st.success(f"\\u2705 Completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")
        if st.button("\\U0001F52C Paso 6: Diagnostico"):
            with st.spinner("Ejecutando 5 analisis..."):
                try:
                    from core.diagnostics import run_all_diagnostics
                    artefactos = run_all_diagnostics()
                    st.success(f"\\u2705 Completado: {len(artefactos)} artefactos")
                except Exception as e:
                    st.error(f"\\u274C Error: {e}")
    st.markdown("---")
    st.caption("EVA Valle v3.0 | UPRA | Arquitectura Hexagonal Modular")

main()
'''

if __name__ == "__main__":
    archivos = {
        "ui/pages/4_Predictivo.py": PAGE_PREDICTIVO,
        "ui/pages/5_Auditoria.py": PAGE_AUDITORIA,
        "ui/pages/6_Configuracion.py": PAGE_CONFIGURACION,
    }
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
    print(f"\n{len(archivos)} paginas creadas (parte 2).")
    print("Ejecuta: python scripts\\verify_phase5.py")