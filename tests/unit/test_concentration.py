"""Tests del analisis de concentracion (previene Gini negativo)."""
import pandas as pd

from core.analytics.concentration import calculate_concentration


def test_gini_en_rango_valido():
    """El Gini SIEMPRE debe estar en [0, 1]. Previene el bug de Gini negativo."""
    df = pd.DataFrame({
        "cultivo": ["A", "B", "C", "D"],
        "produccion_t": [10, 20, 30, 40],
    })
    res = calculate_concentration(df)
    assert 0.0 <= res["gini"] <= 1.0, f"Gini fuera de rango: {res['gini']}"


def test_gini_cercano_a_cero_con_igualdad():
    """Distribucion uniforme -> Gini cercano a 0."""
    df = pd.DataFrame({
        "cultivo": ["A", "B", "C", "D"],
        "produccion_t": [10, 10, 10, 10],
    })
    res = calculate_concentration(df)
    assert res["gini"] < 0.1


def test_gini_alto_con_concentracion_extrema():
    """Un cultivo dominante -> Gini alto (cerca de 1)."""
    df = pd.DataFrame({
        "cultivo": ["A", "B", "C", "D"],
        "produccion_t": [1000, 1, 1, 1],
    })
    res = calculate_concentration(df)
    assert res["gini"] > 0.5


def test_hhi_maximo_con_monopolio():
    """Un solo productor -> HHI = 10,000."""
    df = pd.DataFrame({"cultivo": ["A"], "produccion_t": [100]})
    res = calculate_concentration(df)
    assert abs(res["hhi"] - 10000) < 1
