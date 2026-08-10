"""Pagina 1: Dashboard - Vista general."""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.error_handler import run_safe

from config.settings import settings
from ui.components.filter_panel import render_filter_panel, apply_filters
from ui.components.metrics_cards import render_kpi_row
from ui.charts.historical import plot_historico_cruces, plot_rendimiento_historico
from ui.charts.concentration import plot_pareto_concentracion
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Dashboard | EVA Valle", page_icon="\U0001F4CA", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def main() -> None:
    st.title("\U0001F4CA Dashboard - EVA Valle del Cauca")
    st.caption("Vista general de la produccion agricola 2019-2025")
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
        {"label": "Produccion Total", "value": f"{prod_total:,.0f} t", "icon": "\U0001F33E"},
        {"label": "Area Sembrada", "value": f"{area_total:,.0f} ha", "icon": "\U0001F4D0"},
        {"label": "Rendimiento Prom.", "value": f"{rend_prom:.1f} t/ha", "icon": "\U0001F4C8"},
        {"label": "Cultivos Activos", "value": f"{n_cultivos}", "icon": "\U0001F331"},
    ])
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("\U0001F4C9 Evolucion Historica")
        st.plotly_chart(plot_historico_cruces(df_f), use_container_width=True)
    with col2:
        st.subheader("\U0001F4CA Rendimiento Promedio")
        st.plotly_chart(plot_rendimiento_historico(df_f), use_container_width=True)
    st.markdown("---")
    st.subheader("\U0001F3AF Concentracion de la Produccion (Pareto)")
    st.plotly_chart(plot_pareto_concentracion(df_f, top_n=10), use_container_width=True)
    st.markdown("---")
    st.subheader("\U0001F3D8\uFE0F Resumen por Municipio")
    resumen = (df_f.groupby("municipio")
        .agg(produccion_t=("produccion_t","sum"), area=("area_sembrada_ha","sum"),
             cultivos=("cultivo","nunique"))
        .sort_values("produccion_t", ascending=False).reset_index())
    st.dataframe(resumen, use_container_width=True, height=400)

run_safe(main)
