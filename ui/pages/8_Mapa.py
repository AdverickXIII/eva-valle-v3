"""Pagina 8: Mapa - Coropletico estatico y animado por ano."""
from __future__ import annotations

import numpy as np
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.spatial_map import plot_choropleth_municipios

st.set_page_config(page_title="Mapa | EVA Valle", page_icon="\U0001F5FA\uFE0F", layout="wide")

METRICAS = {
    "Produccion (t)": "produccion_t",
    "Area Sembrada (ha)": "area_sembrada_ha",
    "Area Cosechada (ha)": "area_cosechada_ha",
    "Rendimiento (t/ha)": "rendimiento_t_ha",
}


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _valor_muni(df_x: pd.DataFrame, metrica: str) -> pd.DataFrame:
    if metrica == "rendimiento_t_ha":
        g = (df_x.groupby("municipio")
             .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
             .reset_index())
        g["valor"] = (g["prod"] / g["cos"].replace(0, 1)).replace([np.inf, -np.inf], 0)
    else:
        g = df_x.groupby("municipio")[metrica].sum().reset_index()
        g["valor"] = g[metrica]
    return g


def _rango_anim(df_x: pd.DataFrame, metrica: str) -> tuple:
    """Rango global por (ano, municipio) para comparar colores entre anos."""
    if metrica == "rendimiento_t_ha":
        g = (df_x.groupby(["ano", "municipio"])
             .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
             .reset_index())
        g["valor"] = (g["prod"] / g["cos"].replace(0, 1)).replace([np.inf, -np.inf], 0)
    else:
        g = df_x.groupby(["ano", "municipio"])[metrica].sum().reset_index()
        g["valor"] = g[metrica]
    return float(g["valor"].min()), float(g["valor"].max())


def main() -> None:
    st.title("\U0001F5FA\uFE0F Mapa Coropletico - Valle del Cauca")
    st.caption("Intensidad de la metrica por municipio, estatica o animada por ano")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        nombre_metrica = st.selectbox("Metrica", list(METRICAS.keys()), index=0)
    with c2:
        cultivos = ["Todos los cultivos"] + sorted(df["cultivo"].unique().tolist())
        cultivo_sel = st.selectbox("Cultivo", cultivos, index=0)
    with c3:
        modo = st.selectbox("Vista", ["Periodo completo", "Por ano (animado)"], index=0)

    metrica = METRICAS[nombre_metrica]
    df_f = df.copy()
    if cultivo_sel != "Todos los cultivos":
        df_f = df_f[df_f["cultivo"] == cultivo_sel]

    rango = None
    if modo == "Por ano (animado)":
        anos = sorted(df_f["ano"].dropna().unique().tolist())
        ano = int(st.slider("Ano", int(min(anos)), int(max(anos)), int(max(anos))))
        df_map = df_f[df_f["ano"] == ano]
        rango = _rango_anim(df_f, metrica)
        titulo = f"{nombre_metrica} - {ano}"
    else:
        df_map = df_f
        titulo = f"{nombre_metrica} por municipio"

    if cultivo_sel != "Todos los cultivos":
        titulo += f" - {cultivo_sel}"

    fig = plot_choropleth_municipios(df_map, metrica, titulo, rango_color=rango)
    if fig is None:
        st.warning("GeoJSON no encontrado. Ejecuta: python scripts/download_geojson.py")
        return

    st.plotly_chart(fig, use_container_width=True)

    if modo == "Por ano (animado)":
        st.caption("\U0001F3AC Mueve el slider para animar la evolucion. "
                   "La escala de color es fija, asi los colores son comparables entre anos.")

    # KPIs del filtro actual (absorbidos de Mapa Cultivos)
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Municipios", df_map["municipio"].nunique())
    k2.metric("Produccion", f"{df_map['produccion_t'].sum():,.0f} t")
    k3.metric("Area sembrada", f"{df_map['area_sembrada_ha'].sum():,.0f} ha")
    cos = df_map["area_cosechada_ha"].sum()
    k4.metric("Rendimiento",
              f"{df_map['produccion_t'].sum()/cos:.2f} t/ha" if cos else "-")

    # Ranking de apoyo
    st.subheader("\U0001F3C6 Ranking de Municipios")
    rank = _valor_muni(df_map, metrica).sort_values("valor", ascending=False)
    st.dataframe(rank, use_container_width=True, height=350)
    render_download_button(rank, f"mapa_{metrica}.csv")


main()
