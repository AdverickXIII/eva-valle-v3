"""Fase 8: crea la suite de pruebas unitarias con pytest."""
from pathlib import Path

TEST_CONCENTRATION = '''"""Tests del analisis de concentracion (previene Gini negativo)."""
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
'''

TEST_NORMALIZATION = '''"""Tests de normalizacion de nombres."""
from core.audit.normalization import normalize_column_name


def test_snake_case():
    assert normalize_column_name("Area sembrada (ha)") == "area_sembrada_ha"


def test_elimina_tildes():
    assert normalize_column_name("Código Dane departamento") == "codigo_dane_departamento"


def test_colapsa_guiones():
    assert normalize_column_name("Rendimiento  (t/ha)") == "rendimiento_t_ha"
'''

TEST_TARGET_ENCODING = '''"""Tests de target encoding (previene data leakage)."""
import pandas as pd

from core.ml.target_encoding import apply_target_encoding, fit_target_encoding


def test_fit_calcula_medias_de_train():
    train = pd.DataFrame({
        "municipio": ["M1", "M1", "M2"],
        "rendimiento_t_ha": [10.0, 20.0, 30.0],
    })
    maps = fit_target_encoding(train)
    assert maps["municipio"]["M1"] == 15.0
    assert maps["municipio"]["M2"] == 30.0


def test_apply_usa_medias_de_train_y_rellena_no_vistos():
    """Un municipio no visto en train se rellena con la media global (no con su propia media)."""
    train = pd.DataFrame({
        "municipio": ["M1", "M1"],
        "rendimiento_t_ha": [10.0, 20.0],
    })
    maps = fit_target_encoding(train)

    test = pd.DataFrame({"municipio": ["M1", "M3"]})
    res = apply_target_encoding(test, maps)

    assert res["target_enc_municipio"].iloc[0] == 15.0   # visto en train
    assert res["target_enc_municipio"].iloc[1] == 15.0   # no visto -> media global
    assert not res["target_enc_municipio"].isna().any()
'''

TEST_SURROGATE = '''"""Tests de llave surrogate."""
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
'''

TEST_AUDIT = '''"""Tests de auditorias (funciones puras)."""
import pandas as pd

from core.audit.models import AuditFinding
from core.audit.nulls import audit_nulls
from core.audit.structure import audit_structure


def test_nulls_sin_nulos_retorna_info():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    findings = audit_nulls(df)
    assert isinstance(findings, list)
    assert all(isinstance(f, AuditFinding) for f in findings)
    assert all(f.severidad == "INFO" for f in findings)


def test_nulls_detecta_nulos():
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    findings = audit_nulls(df)
    assert any(f.severidad in ("ADVERTENCIA", "ERROR") for f in findings)


def test_structure_detecta_columnas():
    df = pd.DataFrame({"a": [1], "b": [2]})
    findings = audit_structure(df)
    assert isinstance(findings, list) and len(findings) >= 1
'''

TEST_SPATIAL = '''"""Tests de analisis espacial."""
import pandas as pd

from core.analytics.spatial import calculate_shannon_diversity


def test_shannon_retorna_dataframe():
    df = pd.DataFrame({
        "municipio": ["M1", "M2"],
        "area_sembrada_ha": [10.0, 20.0],
    })
    res = calculate_shannon_diversity(df)
    assert "shannon_wiener" in res.columns
    assert len(res) == 2
'''

TESTS_INIT = '''"""Suite de pruebas unitarias."""
'''

if __name__ == "__main__":
    archivos = {
        "tests/__init__.py": TESTS_INIT,
        "tests/unit/__init__.py": TESTS_INIT,
        "tests/unit/test_concentration.py": TEST_CONCENTRATION,
        "tests/unit/test_normalization.py": TEST_NORMALIZATION,
        "tests/unit/test_target_encoding.py": TEST_TARGET_ENCODING,
        "tests/unit/test_surrogate.py": TEST_SURROGATE,
        "tests/unit/test_audit.py": TEST_AUDIT,
        "tests/unit/test_spatial.py": TEST_SPATIAL,
    }
    for ruta, contenido in archivos.items():
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
    print(f"\n{len(archivos)} archivos de pruebas creados.")
    print("Ejecuta: python -m pytest tests/unit -v")