"""Tests de normalizacion de nombres."""
from core.audit.normalization import normalize_column_name


def test_snake_case():
    assert normalize_column_name("Area sembrada (ha)") == "area_sembrada_ha"


def test_elimina_tildes():
    assert normalize_column_name("Código Dane departamento") == "codigo_dane_departamento"


def test_colapsa_guiones():
    assert normalize_column_name("Rendimiento  (t/ha)") == "rendimiento_t_ha"
