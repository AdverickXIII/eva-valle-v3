"""Tests de concentracion dual, territorial y calidad (core.analytics.pareto)."""
import numpy as np
import pandas as pd
import pytest

from core.analytics.pareto import (
    conc_metrics,
    pareto,
    quality,
    recomendaciones,
    territorial,
    tiering,
)


def _cult(prod: dict) -> pd.DataFrame:
    return pd.DataFrame({"cultivo": list(prod), "produccion_t": list(prod.values())})


# --- pareto -----------------------------------------------------------------

def test_pareto_participacion_y_acumulado():
    res = pareto(_cult({"A": 60, "B": 30, "C": 10}))
    assert list(res["cultivo"]) == ["A", "B", "C"]
    assert list(res["share"]) == [60.0, 30.0, 10.0]
    assert list(res["cum"]) == [60.0, 90.0, 100.0]


def test_pareto_agrupa_resto_en_otros():
    res = pareto(_cult({"A": 60, "B": 30, "C": 6, "D": 4}), top_n=2)
    assert list(res["cultivo"]) == ["A", "B", "Otros"]
    assert res.loc[res["cultivo"] == "Otros", "produccion"].iloc[0] == 10
    assert res["cum"].iloc[-1] == pytest.approx(100.0)


def test_pareto_excluye_cana_con_o_sin_tilde():
    df = _cult({"Caña de azúcar": 900, "B": 60, "C": 40})
    res = pareto(df, exclude_cana=True)
    assert "Caña de azúcar" not in list(res["cultivo"])
    # El porcentaje se recalcula sobre el total sin caña.
    assert res["share"].iloc[0] == pytest.approx(60.0)


# --- conc_metrics -------------------------------------------------------------

def test_conc_metrics_reparto_uniforme():
    res = conc_metrics(_cult({"A": 25, "B": 25, "C": 25, "D": 25}))
    assert res["hhi"] == 2500
    assert res["top1_pct"] == 25.0
    assert res["n80"] == 4
    assert res["cultivos"] == 4
    assert res["gini"] == pytest.approx(0.0, abs=1e-9)


def test_conc_metrics_monopolio():
    res = conc_metrics(_cult({"A": 100}))
    assert res["hhi"] == 10000
    assert res["top1"] == "A"
    assert res["n80"] == 1


def test_conc_metrics_gini_en_rango_y_top1():
    res = conc_metrics(_cult({"A": 1000, "B": 5, "C": 3, "D": 2}))
    assert 0.0 <= res["gini"] <= 1.0
    assert res["top1"] == "A"
    assert res["top1_pct"] > 90


def test_conc_metrics_ignora_cultivos_sin_produccion():
    res = conc_metrics(_cult({"A": 50, "B": 50, "C": 0}))
    assert res["cultivos"] == 2
    assert res["hhi"] == 5000


def test_conc_metrics_sin_cana_baja_el_hhi():
    df = _cult({"Caña": 900, "B": 50, "C": 50})
    con = conc_metrics(df, exclude_cana=False)
    sin = conc_metrics(df, exclude_cana=True)
    assert con["hhi"] == 8150   # 90^2 + 5^2 + 5^2
    assert sin["hhi"] == 5000   # 50^2 + 50^2
    assert con["hhi"] > sin["hhi"]
    assert sin["cultivos"] == 2


# --- territorial / tiering ------------------------------------------------------

def test_territorial_valores_conocidos():
    df = pd.DataFrame({"municipio": ["X", "Y"], "produccion_t": [75, 25]})
    res = territorial(df)
    assert res["hhi"] == 6250
    assert res["top"] == "X"
    assert res["top_pct"] == 75.0
    assert res["municipios"] == 2


def test_tiering_terciles():
    df = pd.DataFrame({
        "municipio": list("ABCDEF"),
        "produccion_t": [6, 5, 4, 3, 2, 1],
    })
    res = tiering(df).set_index("municipio")["tier"]
    assert res[["A", "B"]].tolist() == ["Lider", "Lider"]
    assert res[["C", "D"]].tolist() == ["Intermedio", "Intermedio"]
    assert res[["E", "F"]].tolist() == ["Rezagado", "Rezagado"]


# --- quality -----------------------------------------------------------------

def test_quality_porcentajes():
    df = pd.DataFrame({
        "produccion_t": [10.0, 10.0, 10.0, np.nan],
        "area_sembrada_ha": [5.0, 5.0, 5.0, 5.0],
        "area_cosechada_ha": [4.0, 6.0, 5.0, 4.0],   # solo la fila 2 es anomala
    })
    res = quality(df)
    assert res["registros"] == 4
    assert res["pct_anomalia"] == 25.0
    assert res["pct_nulos"] == 25.0


# --- recomendaciones ------------------------------------------------------------

def _panel(prod_por_cultivo_municipio: dict) -> pd.DataFrame:
    filas = [
        {"cultivo": c, "municipio": m, "produccion_t": v}
        for (c, m), v in prod_por_cultivo_municipio.items()
    ]
    return pd.DataFrame(filas)


def test_recomendaciones_monocultivo_y_concentracion_territorial():
    datos = {("Caña", "M0"): 100000}
    datos.update({("B", f"M{i}"): 1 for i in range(1, 10)})
    titulos = [t for t, _ in recomendaciones(_panel(datos))]
    assert "Diversificacion productiva" in titulos
    assert "Priorizacion territorial" in titulos


def test_recomendaciones_panel_equilibrado_solo_las_fijas():
    datos = {(c, m): 10 for c in "ABCDE" for m in ("M1", "M2", "M3", "M4", "M5")}
    titulos = [t for t, _ in recomendaciones(_panel(datos))]
    assert "Diversificacion productiva" not in titulos
    assert "Priorizacion territorial" not in titulos
    assert len(titulos) == 2
