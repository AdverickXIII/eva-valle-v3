"""Tests del motor de forecasting (core.analytics.forecast)."""
import numpy as np
import pandas as pd
import pytest

from core.analytics.forecast import (
    _mape,
    _proyectar,
    backtest,
    elegir_mejor,
    modelo_holt,
    modelo_lineal,
    modelo_naive,
    modelo_promedio,
    proyectar_con_ic,
)


def _t_s(valores):
    s = np.array(valores, dtype=float)
    return np.arange(len(s)), s


# --- modelos individuales -------------------------------------------------

def test_lineal_recupera_pendiente_y_proyecta():
    t, s = _t_s([10, 20, 30, 40])
    m = modelo_lineal(t, s)
    assert m["a"] == pytest.approx(10.0)
    assert m["b"] == pytest.approx(10.0)
    assert list(_proyectar(m, 2)) == pytest.approx([50.0, 60.0])


def test_lineal_serie_constante_no_aplica():
    t, s = _t_s([5, 5, 5, 5])
    assert modelo_lineal(t, s) is None


def test_promedio_movil_usa_ultima_ventana():
    t, s = _t_s([1, 2, 3, 10])
    m = modelo_promedio(t, s, 3)
    assert m["last_mean"] == pytest.approx((2 + 3 + 10) / 3)
    assert list(_proyectar(m, 2)) == pytest.approx([5.0, 5.0])


def test_promedio_movil_serie_corta_no_aplica():
    t, s = _t_s([1, 2])
    assert modelo_promedio(t, s, 3) is None


def test_naive_repite_ultimo_valor():
    t, s = _t_s([4, 8, 6])
    m = modelo_naive(t, s)
    assert list(_proyectar(m, 3)) == pytest.approx([6.0, 6.0, 6.0])
    assert np.isnan(m["fitted"][0])
    assert list(m["fitted"][1:]) == pytest.approx([4.0, 8.0])


def test_naive_un_solo_punto_no_aplica():
    t, s = _t_s([4])
    assert modelo_naive(t, s) is None


def test_holt_serie_lineal_extrapola_tendencia():
    t, s = _t_s([10, 20, 30, 40, 50])
    m = modelo_holt(t, s)
    pred = _proyectar(m, 2)
    # Con tendencia exacta L y T no se desvian: L=50, T=10.
    assert list(pred) == pytest.approx([60.0, 70.0])


def test_holt_menos_de_tres_puntos_no_aplica():
    t, s = _t_s([1, 2])
    assert modelo_holt(t, s) is None


# --- MAPE -----------------------------------------------------------------

def test_mape_valor_conocido():
    assert _mape([100, 200], [110, 180]) == pytest.approx(10.0)


def test_mape_ignora_reales_en_cero():
    assert _mape([0, 100], [50, 110]) == pytest.approx(10.0)


def test_mape_todo_cero_es_infinito():
    assert _mape([0, 0], [1, 1]) == np.inf


# --- backtest / seleccion ---------------------------------------------------

def test_backtest_serie_menor_a_4_devuelve_vacio():
    assert backtest(pd.Series([1.0, 2.0, 3.0])) == []


def test_elegir_mejor_datos_insuficientes():
    res = elegir_mejor(pd.Series([1.0, 2.0, 3.0]))
    assert res["modelo"] is None
    assert res["ganador"] == "Datos insuficientes"
    assert res["ranking"] == []


def test_elegir_mejor_serie_lineal_elige_modelo_valido():
    serie = pd.Series([100.0, 110, 120, 130, 140, 150, 160], index=range(2018, 2025))
    res = elegir_mejor(serie)
    assert res["modelo"] is not None
    assert np.isfinite(res["mape"])
    assert res["ganador"] == res["modelo"]["nombre"]
    # El ranking va de menor a mayor MAPE.
    mapes = [r["mape"] for r in res["ranking"]]
    assert mapes == sorted(mapes)


# --- proyectar_con_ic -------------------------------------------------------

@pytest.fixture
def serie_creciente():
    return pd.Series([100.0, 112, 125, 133, 148, 160, 171], index=range(2018, 2025))


def test_proyectar_con_ic_forma_y_orden_de_escenarios(serie_creciente):
    res = proyectar_con_ic(serie_creciente, n_steps=3)
    esc = res["escenarios"]
    for k in ("conservador", "tendencial", "optimista", "ic_bajo", "ic_alto"):
        assert len(esc[k]) == 3
        assert np.all(np.isfinite(esc[k]))
    assert np.all(esc["conservador"] <= esc["optimista"])
    assert np.all(esc["ic_bajo"] <= esc["ic_alto"])


def test_proyectar_con_ic_escenarios_nunca_negativos():
    serie = pd.Series([50.0, 40, 30, 20, 10, 5, 2], index=range(2018, 2025))
    esc = proyectar_con_ic(serie, n_steps=5)["escenarios"]
    for k, v in esc.items():
        assert np.all(v >= 0), f"{k} tiene valores negativos: {v}"


def test_proyectar_con_ic_es_determinista(serie_creciente):
    a = proyectar_con_ic(serie_creciente, n_steps=3)["escenarios"]["tendencial"]
    b = proyectar_con_ic(serie_creciente, n_steps=3)["escenarios"]["tendencial"]
    assert list(a) == pytest.approx(list(b))


def test_proyectar_con_ic_ignora_nan(serie_creciente):
    con_nan = serie_creciente.copy()
    con_nan.iloc[3] = np.nan
    res = proyectar_con_ic(con_nan, n_steps=3)
    assert res["modelo"] is not None
    assert np.all(np.isfinite(res["escenarios"]["tendencial"]))


def test_proyectar_con_ic_serie_corta_devuelve_sin_modelo():
    res = proyectar_con_ic(pd.Series([1.0, 2.0, 3.0]), n_steps=3)
    assert res["modelo"] is None
    assert "escenarios" not in res
