# Pruebas Automatizadas

Ejecutar: python -m pytest tests/unit -v  (esperado: 15 passed)
Cobertura: python -m pytest tests/unit --cov=core --cov-report=term-missing

| Test | Previene |
|---|---|
| test_gini_en_rango_valido | Gini negativo |
| test_fit_calcula_medias_de_train | Data leakage |
| test_apply_..._rellena_no_vistos | Fuga de categorias |
| test_ids_unicos | Llaves duplicadas |
| test_nulls_* | Auditorias sin deteccion |

Anadir test: crear tests/unit/test_modulo.py con datos sinteticos
deterministas y aserciones claras; ejecutar pytest.
