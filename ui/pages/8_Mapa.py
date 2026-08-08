"""Pagina 8: Mapa - Coropletico de municipios del Valle."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.spatial_map import plot_choropleth_municipios
from ui.services.performance import cached_outliers  # noqa: F401 (cache disponible)

st.set_page_config(page_title="Mapa | EVA Valle", page_icon="\U0001F5FA\uFE0F", layout="wide")

METRICAS = {
    "Produccion (t)": "produccion_t",
    "Area Sembrada (ha)": "area_sembrada_ha",
    "Rendimiento (t/ha)": "rendimiento_t_ha",
}


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\U0001F5FA\uFE0F Mapa Coropletico - Valle del Cauca")
    st.caption("Intensidad de la metrica seleccionada en cada municipio")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    col1, col2 = st.columns(2)
    with col1:
        nombre_metrica = st.selectbox("Metrica", list(METRICAS.keys()), index=0)
    with col2:
        cultivos = ["Todos los cultivos"] + sorted(df["cultivo"].unique().tolist())
        cultivo_sel = st.selectbox("Cultivo", cultivos, index=0)

    df_f = df.copy()
    if cultivo_sel != "Todos los cultivos":
        df_f = df_f[df_f["cultivo"] == cultivo_sel]

    metrica = METRICAS[nombre_metrica]
    titulo = f"{nombre_metrica} por municipio"
    if cultivo_sel != "Todos los cultivos":
        titulo += f" - {cultivo_sel}"

    fig = plot_choropleth_municipios(df_f, metrica, titulo)
    if fig is None:
        st.warning("GeoJSON no encontrado. Ejecuta: python scripts/download_geojson.py")
        return

    st.plotly_chart(fig, use_container_width=True)

    # Tabla de apoyo: ranking de municipios
    st.subheader("\U0001F3C6 Ranking de Municipios")
    if metrica == "rendimiento_t_ha":
        rank = (df_f.groupby("municipio")
                .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
                .assign(valor=lambda x: x["prod"] / x["cos"].replace(0, 1))
                .sort_values("valor", ascending=False))
    else:
        rank = (df_f.groupby("municipio")[metrica].sum()
                .sort_values(ascending=False).to_frame("valor"))
    rank = rank.reset_index()
    st.dataframe(rank, use_container_width=True, height=350)
    render_download_button(rank, f"mapa_{metrica}.csv")


main()
