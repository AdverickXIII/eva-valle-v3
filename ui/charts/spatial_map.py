"""Mapa coropletico de municipios del Valle del Cauca."""
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
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(text=titulo, x=0.5),
        height=620,
    )
    return fig
