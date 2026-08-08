"""Reescribe ui/charts/spatial_map.py para aceptar rango_color (animacion comparable)."""
from pathlib import Path

SPATIAL = '''"""Mapa coropletico de municipios del Valle del Cauca."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px

GEOJSON_PATH = (
    Path(__file__).parent.parent.parent / "data" / "external" / "valle_municipios.geojson"
)


def load_geojson() -> dict | None:
    if not GEOJSON_PATH.exists():
        return None
    return json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))


def plot_choropleth_municipios(
    df: pd.DataFrame,
    metrica: str = "produccion_t",
    titulo: str = "",
    rango_color: tuple | None = None,
):
    """
    Coropletico coloreado por metrica agregada por municipio.

    Args:
        df: DataFrame filtrado.
        metrica: 'produccion_t', 'area_sembrada_ha' o 'rendimiento_t_ha'.
        titulo: Titulo del mapa.
        rango_color: (min, max) fijo para comparar entre anos (animacion).
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

    g["MPIOS"] = g["codigo_dane_municipio"].astype(str).str.zfill(5)

    fig = px.choropleth(
        g,
        geojson=geo,
        locations="MPIOS",
        color="valor",
        featureidkey="properties.MPIOS",
        hover_name="municipio",
        color_continuous_scale="Viridis",
        range_color=rango_color,
        labels={"valor": titulo or metrica},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(text=titulo, x=0.5),
        height=620,
    )
    return fig
'''

Path("ui/charts/spatial_map.py").write_text(SPATIAL, encoding="utf-8")
print("[OK] ui/charts/spatial_map.py (v2: rango_color)")
print("Sigue: python scripts\\setup_mapa_animado_page.py")