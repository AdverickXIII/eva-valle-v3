"""Tests del CAGR por cultivo (core.analytics.growth)."""
import pandas as pd
import pytest

from core.analytics.growth import calculate_cagr


def _df(filas):
    return pd.DataFrame(filas, columns=["ano", "cultivo", "produccion_t"])


def test_cagr_valor_conocido_duplicacion_en_5_anios():
    df = _df([(2019, "A", 100), (2024, "A", 200)])
    res = calculate_cagr(df)
    esperado = (2 ** (1 / 5) - 1) * 100
    assert res.loc[res["cultivo"] == "A", "cagr"].iloc[0] == pytest.approx(esperado)


def test_cagr_sin_cambio_es_cero():
    res = calculate_cagr(_df([(2019, "A", 50), (2024, "A", 50)]))
    assert res["cagr"].iloc[0] == pytest.approx(0.0)


def test_cagr_negativo_si_cae():
    res = calculate_cagr(_df([(2019, "A", 100), (2024, "A", 50)]))
    assert res["cagr"].iloc[0] < 0


def test_cagr_ordenado_descendente():
    df = _df([
        (2019, "A", 100), (2024, "A", 100),
        (2019, "B", 100), (2024, "B", 300),
        (2019, "C", 100), (2024, "C", 50),
    ])
    res = calculate_cagr(df)
    assert list(res["cultivo"]) == ["B", "A", "C"]


def test_cagr_suma_filas_del_mismo_cultivo_y_ano():
    df = _df([
        (2019, "A", 60), (2019, "A", 40),   # 100 en 2019
        (2024, "A", 200),
    ])
    res = calculate_cagr(df)
    assert res["prod_inicio"].iloc[0] == 100
    assert res["prod_fin"].iloc[0] == 200


def test_cagr_excluye_cultivo_con_produccion_inicial_cero():
    df = _df([(2019, "A", 0), (2024, "A", 100), (2019, "B", 10), (2024, "B", 20)])
    res = calculate_cagr(df)
    assert list(res["cultivo"]) == ["B"]


def test_cagr_excluye_cultivo_ausente_en_un_extremo():
    df = _df([(2019, "A", 10), (2024, "B", 20), (2019, "C", 10), (2024, "C", 20)])
    res = calculate_cagr(df)
    assert list(res["cultivo"]) == ["C"]


def test_cagr_un_solo_ano_devuelve_vacio():
    assert calculate_cagr(_df([(2024, "A", 10)])).empty


def test_cagr_columnas_faltantes_devuelve_vacio():
    assert calculate_cagr(pd.DataFrame({"ano": [2019], "cultivo": ["A"]})).empty
