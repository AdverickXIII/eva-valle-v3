"""Crea ui/charts/spatial_map.py y ui/pages/8_Mapa.py, y registra la pagina."""
from pathlib import Path

SPATIAL_MAP = '''"""Mapa coropletico de municipios del Valle del Cauca."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px

GEOJSON_PATH = (
    Path(__file__).parent.parent.parent / "data" / "external" / "valle_municipios.geojson"
)


def load_geojson() -> dict | None:
    """Carga el GeoJSON local de municipios del Valle."""
    if not GEOJSON_PATH.exists():
        return None
    return json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))


def plot_choropleth_municipios(
    df: pd.DataFrame,
    metrica: str = "produccion_t",
    titulo: str = "",
) -> "px.Figure | None":
    """
    Mapa coropletico coloreado por metrica agregada por municipio.

    Args:
        df: DataFrame filtrado (con codigo_dane_municipio y metricas).
        metrica: 'produccion_t', 'area_sembrada_ha' o 'rendimiento_t_ha'.
        titulo: Titulo del mapa.

    Returns:
        Figura Plotly, o None si falta el GeoJSON.
    """
    geo = load_geojson()
    if geo is None:
        return None

    if metrica == "rendimiento_t_ha":
        g = (df.groupby(["codigo_dane_municipio", "municipio"])
             .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
             .reset_index())
        g["valor"] = g["prod"] / g["cos"].replace(0, 1)
    else:
        g = (df.groupby(["codigo_dane_municipio", "municipio"])[metrica]
             .sum().reset_index())
        g["valor"] = g[metrica]

    # Clave de union con el GeoJSON (5 digitos)
    g["MPIOS"] = g["codigo_dane_municipio"].astype(str).str.zfill(5)

    fig = px.choropleth(
        g,
        geojson=geo,
        locations="MPIOS",
        color="valor",
        featureidkey="properties.MPIOS",
        hover_name="municipio",
        color_continuous_scale="Viridis",
        labels={"valor": titulo or metrica},
    )
    # Encuadrar solo el Valle del Cauca
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(text=titulo, x=0.5),
        height=620,
    )
    return fig
'''

PAGE_MAPA = '''"""Pagina 8: Mapa - Coropletico de municipios del Valle."""
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

st.set_page_config(page_title="Mapa | EVA Valle", page_icon="\\U0001F5FA\\uFE0F", layout="wide")

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
    st.title("\\U0001F5FA\\uFE0F Mapa Coropletico - Valle del Cauca")
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
    st.subheader("\\U0001F3C6 Ranking de Municipios")
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
'''

if __name__ == "__main__":
    # 1. modulo de mapa
    p = Path("ui/charts/spatial_map.py")
    p.write_text(SPATIAL_MAP, encoding="utf-8")
    print(f"[OK] {p}")

    # 2. pagina
    p2 = Path("ui/pages/8_Mapa.py")
    p2.write_text(PAGE_MAPA, encoding="utf-8")
    print(f"[OK] {p2}")

    # 3. registrar en app.py
    app = Path("app.py")
    content = app.read_text(encoding="utf-8")
    anchor = 'st.Page("ui/pages/7_Cultivos.py"'
    nueva = '    st.Page("ui/pages/8_Mapa.py", title="Mapa", icon="\\U0001F5FA\\uFE0F"),\n'
    if anchor in content and "8_Mapa.py" not in content:
        idx = content.find(anchor)
        fin = content.find("\n", idx)
        content = content[: fin + 1] + nueva + content[fin + 1 :]
        app.write_text(content, encoding="utf-8")
        print("[OK] app.py actualizado (pagina Mapa registrada)")
    else:
        print("[INFO] app.py ya tenia la pagina Mapa o no encontro anchor")

    print("\nListo. Ejecuta: streamlit run app.py")