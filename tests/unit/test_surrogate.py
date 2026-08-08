"""Tests de llave surrogate."""
import pandas as pd

from core.modeling.surrogate_key import generate_surrogate_key, validate_natural_key


def _df():
    return pd.DataFrame({
        "codigo_dane_municipio": [76001, 76001, 76002],
        "desagregacion_cultivo": ["Acelga", "Aji", "Acelga"],
        "periodo": ["2019A", "2019A", "2019A"],
        "ciclo_del_cultivo": ["T", "T", "T"],
        "estado_fisico_del_cultivo": ["F", "F", "F"],
    })


def test_ids_unicos():
    ids = generate_surrogate_key(_df())
    assert ids.nunique() == 3


def test_llave_natural_valida():
    ok, duplicados = validate_natural_key(_df())
    assert ok and duplicados == 0
