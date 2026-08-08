"""Pagina 4: Predictivo - Que podria ocurrir?"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.error_handler import run_safe

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

st.set_page_config(page_title="Predictivo | EVA Valle", page_icon="\U0001F916", layout="wide")

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
    st.title("\U0001F916 Analisis Predictivo")
    st.caption("Responde: Que podria ocurrir?")
    st.info("\u26A0\uFE0F Los modelos usan target encoding sin data leakage (fit solo con train).")
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
    st.subheader("\U0001F4C9 7.2 Regresion (Random Forest)")
    res_reg = resultados["regresion"]
    metricas = res_reg["metricas"]
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("R2", f"{metricas['R2']:.3f}")
    with col2: st.metric("MAE", f"{metricas['MAE_Toneladas']:,.0f} t")
    with col3: st.metric("RMSE (Log)", f"{metricas['RMSE_Log']:.3f}")
    with col4: st.metric("N Test", f"{metricas['n_test']:,}")
    st.markdown("---")
    st.subheader("\U0001F3AF Importancia de Variables")
    imp = res_reg["importancia"]
    fig_imp = px.bar(imp.reset_index(), x=imp.name, y=imp.index.tolist(),
        orientation="h", template="plotly_dark", height=350)
    st.plotly_chart(fig_imp, use_container_width=True)
    st.markdown("---")
    st.subheader("\U0001F4CA Real vs Predicho")
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
    st.subheader("\U0001F4C8 7.4 Proyeccion Holt-Winters")
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

run_safe(main)
