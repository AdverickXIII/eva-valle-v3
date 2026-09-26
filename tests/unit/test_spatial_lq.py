"""Tests de Location Quotient, Shannon-Wiener y descriptiva (core.analytics)."""
import numpy as np
import pandas as pd
import pytest

from core.analytics.descriptive import calculate_descriptive_statistics
from core.analytics.lq_table import lq_top
from core.analytics.spatial import (
    calculate_location_quotient,
    calculate_shannon_diversity,
)


@pytest.fixture
def panel_area():
    # Valle: G1=40, G2=60 (40% / 60%). M1 total 40, M2 total 60.
    return pd.DataFrame({
        "codigo_dane_municipio": ["1", "1", "2", "2"],
        "grupo_cultivo": ["G1", "G2", "G1", "G2"],
        "area_sembrada_ha": [30.0, 10.0, 10.0, 50.0],
    })


# --- calculate_location_quotient --------------------------------------------

def test_lq_valores_calculados_a_mano(panel_area):
    res = calculate_location_quotient(panel_area)
    lq = res.set_index(["codigo_dane_municipio", "grupo_cultivo"])["LQ"]
    assert lq[("1", "G1")] == pytest.approx(0.75 / 0.40)
    assert lq[("1", "G2")] == pytest.approx(0.25 / 0.60)
    assert lq[("2", "G1")] == pytest.approx((10 / 60) / 0.40)
    assert lq[("2", "G2")] == pytest.approx((50 / 60) / 0.60)


def test_lq_promedio_ponderado_por_area_es_uno(panel_area):
    # Propiedad del LQ: sum_m (area_m / area_total) * LQ_mg = 1 para cada grupo.
    res = calculate_location_quotient(panel_area)
    peso = panel_area.groupby("codigo_dane_municipio")["area_sembrada_ha"].sum()
    peso = peso / peso.sum()
    for g, sub in res.groupby("grupo_cultivo"):
        total = (sub.set_index("codigo_dane_municipio")["LQ"] * peso).sum()
        assert total == pytest.approx(1.0)


def test_lq_columnas_faltantes_devuelve_vacio():
    assert calculate_location_quotient(pd.DataFrame({"grupo_cultivo": ["G1"]})).empty


# --- calculate_shannon_diversity --------------------------------------------

def test_shannon_reparto_igual_es_ln_n():
    df = pd.DataFrame({
        "municipio": ["A", "A", "A", "B"],
        "area_sembrada_ha": [10.0, 20.0, 30.0, 5.0],
    })
    res = calculate_shannon_diversity(df).set_index("municipio")
    p = np.array([10, 20, 30]) / 60
    assert res.loc["A", "shannon_wiener"] == pytest.approx(float(-(p * np.log(p)).sum()))
    assert res.loc["B", "shannon_wiener"] == pytest.approx(0.0)
    assert res.loc["A", "area_total"] == 60.0


def test_shannon_ordenado_descendente():
    df = pd.DataFrame({
        "municipio": ["A", "B", "B"],
        "area_sembrada_ha": [10.0, 10.0, 20.0],
    })
    res = calculate_shannon_diversity(df)
    assert list(res["municipio"]) == ["B", "A"]


def test_shannon_columnas_faltantes_devuelve_vacio():
    assert calculate_shannon_diversity(pd.DataFrame({"municipio": ["A"]})).empty


def test_shannon_cultivos_distintos_cuenta_cultivos_no_valores_de_area():
    # Regresion: antes hacia nunique sobre area_sembrada_ha, asi que dos cultivos
    # con la misma area contaban como uno.
    df = pd.DataFrame({
        "municipio": ["A", "A", "B"],
        "cultivo": ["Maiz", "Frijol", "Maiz"],
        "area_sembrada_ha": [10.0, 10.0, 7.0],
    })
    res = calculate_shannon_diversity(df).set_index("municipio")
    assert res.loc["A", "cultivos_distintos"] == 2
    assert res.loc["B", "cultivos_distintos"] == 1


def test_shannon_cultivos_distintos_repite_cultivo_en_varios_anos():
    df = pd.DataFrame({
        "municipio": ["A", "A", "A"],
        "cultivo": ["Maiz", "Maiz", "Frijol"],
        "area_sembrada_ha": [10.0, 12.0, 5.0],
    })
    res = calculate_shannon_diversity(df).set_index("municipio")
    assert res.loc["A", "cultivos_distintos"] == 2


def test_shannon_sin_columna_cultivo_cuenta_filas_con_area_positiva():
    df = pd.DataFrame({
        "municipio": ["A", "A", "A", "B"],
        "area_sembrada_ha": [10.0, 10.0, 0.0, 4.0],
    })
    res = calculate_shannon_diversity(df).set_index("municipio")
    assert res.loc["A", "cultivos_distintos"] == 2
    assert res.loc["B", "cultivos_distintos"] == 1


def test_shannon_conserva_orden_de_columnas():
    df = pd.DataFrame({"municipio": ["A"], "area_sembrada_ha": [1.0]})
    assert list(calculate_shannon_diversity(df).columns) == [
        "municipio", "cultivos_distintos", "shannon_wiener", "area_total",
    ]


# --- lq_top --------------------------------------------------------------------

@pytest.fixture
def panel_prod():
    return pd.DataFrame({
        "municipio": ["M1", "M1", "M2", "M2"],
        "grupo_cultivo": ["G1", "G2", "G1", "G2"],
        "cultivo": ["Maiz", "Frijol", "Maiz", "Frijol"],
        "produccion_t": [30.0, 10.0, 10.0, 50.0],
    })


def test_lq_top_ordenado_y_valores(panel_prod):
    res = lq_top(panel_prod)
    assert res["lq"].is_monotonic_decreasing
    top = res.iloc[0]
    assert (top["municipio"], top["grupo_cultivo"]) == ("M1", "G1")
    assert top["lq"] == pytest.approx(0.75 / 0.40)
    assert top["share_municipio_pct"] == pytest.approx(75.0)
    assert top["share_valle_pct"] == pytest.approx(40.0)


def test_lq_top_respeta_top_n(panel_prod):
    assert len(lq_top(panel_prod, top_n=2)) == 2


def test_lq_top_excluye_cana(panel_prod):
    df = pd.concat([panel_prod, pd.DataFrame({
        "municipio": ["M1"], "grupo_cultivo": ["GC"], "cultivo": ["Caña"],
        "produccion_t": [1000.0],
    })], ignore_index=True)
    con = lq_top(df, excluye_cana=False)
    sin = lq_top(df, excluye_cana=True)
    assert "GC" in set(con["grupo_cultivo"])
    assert "GC" not in set(sin["grupo_cultivo"])


def test_lq_top_sin_filas_tras_filtrar_devuelve_vacio_con_columnas():
    # Regresion: antes fallaba con KeyError('lq'). 2_Descriptivo.py accede a
    # df_lq['share_municipio_pct'], asi que el vacio debe conservar las columnas.
    df = pd.DataFrame({
        "municipio": ["M1"], "grupo_cultivo": ["GC"], "cultivo": ["Caña"],
        "produccion_t": [100.0],
    })
    res = lq_top(df, excluye_cana=True)
    assert res.empty
    assert list(res.columns) == [
        "municipio", "grupo_cultivo", "share_municipio_pct", "share_valle_pct", "lq",
    ]
    assert res[res["share_municipio_pct"] >= 5].empty   # lo que hace la UI


# --- calculate_descriptive_statistics ------------------------------------------------

def test_descriptiva_valores_conocidos():
    df = pd.DataFrame({"produccion_t": [1.0, 2.0, 3.0, 4.0, 5.0]})
    res = calculate_descriptive_statistics(df).set_index("variable").loc["produccion_t"]
    assert res["n"] == 5
    assert res["media"] == pytest.approx(3.0)
    assert res["mediana"] == pytest.approx(3.0)
    assert res["desv_std"] == pytest.approx(np.sqrt(2.5))
    assert res["cv"] == pytest.approx(np.sqrt(2.5) / 3.0)
    assert res["asimetria"] == pytest.approx(0.0)
    assert res["p25"] == pytest.approx(2.0)
    assert res["p75"] == pytest.approx(4.0)
    assert res["iqr"] == pytest.approx(2.0)


def test_descriptiva_omite_columnas_ausentes_y_nan():
    df = pd.DataFrame({"produccion_t": [1.0, np.nan, 3.0]})
    res = calculate_descriptive_statistics(df)
    assert list(res["variable"]) == ["produccion_t"]
    assert res["n"].iloc[0] == 2


def test_descriptiva_media_cero_da_cv_nan():
    df = pd.DataFrame({"produccion_t": [-1.0, 1.0]})
    res = calculate_descriptive_statistics(df)
    assert np.isnan(res["cv"].iloc[0])
