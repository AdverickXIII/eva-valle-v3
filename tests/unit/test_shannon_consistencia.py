"""Regresion: el Shannon se calcula sobre el area por cultivo, no por fila.

Cada fila del dataset es cultivo x ano x ciclo; tratar las filas como categorias
inflaba el indice muy por encima de ln(n_cultivos) (p. ej. 4.9 con 22 cultivos).
"""
import math

import numpy as np
import pandas as pd
import pytest

from core.analytics.spatial import calculate_shannon_diversity
from core.diagnostics.segmentation import segment_municipalities
from ui.charts.spatial import plot_shannon_barras


def test_shannon_agrega_area_por_cultivo_antes_de_proporciones():
    # Maiz aparece en dos anos: por cultivo son 20 y 20 -> ln(2).
    # Por fila serian 10, 10, 20 -> 1.04 (el valor erroneo anterior).
    df = pd.DataFrame({
        "municipio": ["A", "A", "A"],
        "cultivo": ["Maiz", "Maiz", "Frijol"],
        "ano": [2019, 2020, 2019],
        "area_sembrada_ha": [10.0, 10.0, 20.0],
    })
    res = calculate_shannon_diversity(df).set_index("municipio")
    assert res.loc["A", "shannon_wiener"] == pytest.approx(math.log(2))
    assert res.loc["A", "cultivos_distintos"] == 2
    assert res.loc["A", "area_total"] == 40.0


def test_shannon_nunca_supera_ln_de_cultivos_distintos():
    rng = np.random.default_rng(0)
    filas = [
        {"municipio": f"M{m}", "cultivo": f"C{c}", "ano": a,
         "area_sembrada_ha": float(rng.uniform(1, 100))}
        for m in range(5) for c in range(8) for a in range(2019, 2025)
    ]
    res = calculate_shannon_diversity(pd.DataFrame(filas))
    assert (res["cultivos_distintos"] == 8).all()
    assert (res["shannon_wiener"] <= np.log(res["cultivos_distintos"]) + 1e-9).all()


def test_shannon_monocultivo_es_cero_positivo():
    df = pd.DataFrame({
        "municipio": ["A", "A"], "cultivo": ["Cana", "Cana"],
        "area_sembrada_ha": [50.0, 70.0],
    })
    v = calculate_shannon_diversity(df)["shannon_wiener"].iloc[0]
    assert v == 0.0
    assert math.copysign(1.0, v) == 1.0   # no "-0.0" en tablas ni graficos


def test_shannon_cultivo_sin_area_no_cuenta_como_categoria():
    df = pd.DataFrame({
        "municipio": ["A", "A", "A"], "cultivo": ["Maiz", "Frijol", "Yuca"],
        "area_sembrada_ha": [10.0, 10.0, 0.0],
    })
    res = calculate_shannon_diversity(df).set_index("municipio")
    assert res.loc["A", "cultivos_distintos"] == 2
    assert res.loc["A", "shannon_wiener"] == pytest.approx(math.log(2))


def test_grafico_usa_los_mismos_valores_que_la_tabla():
    df = pd.DataFrame({
        "municipio": ["A", "A", "B", "B", "C"],
        "cultivo": ["Maiz", "Frijol", "Maiz", "Frijol", "Maiz"],
        "area_sembrada_ha": [1500.0, 500.0, 1900.0, 100.0, 3000.0],
    })
    tabla = calculate_shannon_diversity(df).set_index("municipio")["shannon_wiener"]
    barra = plot_shannon_barras(df, min_area=1000).data[0]
    for mun, valor in zip(barra.y, barra.x, strict=True):
        assert valor == pytest.approx(tabla[mun])


def test_grafico_no_falla_sin_columnas_requeridas():
    fig = plot_shannon_barras(pd.DataFrame({"municipio": ["A"]}))
    assert len(fig.data) == 0


def _df_segmentacion():
    filas = []
    # 6 municipios, cada cultivo repetido en 3 anos.
    for m in range(6):
        for c in range(2 + m % 3):
            for ano in (2019, 2020, 2021):
                filas.append({
                    "municipio": f"M{m}", "cultivo": f"C{c}",
                    "desagregacion_cultivo": f"C{c}", "ano": ano,
                    "area_sembrada_ha": 100.0 * (c + 1) * (m + 1),
                    "rendimiento_t_ha": 5.0 + c + m,
                })
    return pd.DataFrame(filas)


def test_segmentacion_shannon_coincide_con_spatial():
    df = _df_segmentacion()
    seg = segment_municipalities(df)
    assert "error" not in seg
    perfiles = seg["df_clusters"].set_index("municipio")["shannon_wiener"]
    esperado = calculate_shannon_diversity(df).set_index("municipio")["shannon_wiener"]
    for mun, v in perfiles.items():
        assert v == pytest.approx(esperado[mun])
        assert v <= math.log(df[df["municipio"] == mun]["cultivo"].nunique()) + 1e-9
