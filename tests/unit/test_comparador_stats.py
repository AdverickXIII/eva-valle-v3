"""Regresion: _stats() del Comparador fallaba con UnboundLocalError si no habia produccion."""
import ast
from pathlib import Path

import numpy as np
import pandas as pd


def _cargar_stats():
    # La pagina ejecuta Streamlit al importarse; extraemos solo la funcion pura.
    src = (Path(__file__).parents[2] / "ui" / "pages" / "11_Comparador.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "_stats")
    ns = {"pd": pd, "np": np}
    exec(compile(ast.Module([fn], []), "11_Comparador.py", "exec"), ns)
    return ns["_stats"]


def _df(prod):
    n = len(prod)
    return pd.DataFrame({
        "cultivo": [f"c{i}" for i in range(n)], "ano": [2023] * n, "produccion_t": prod,
        "area_sembrada_ha": [1.0] * n, "area_cosechada_ha": [1.0] * n,
    })


def test_stats_sin_produccion_no_falla():
    df = _df([0.0, 0.0])
    r = _cargar_stats()(df, df)
    assert r["Diversidad (Shannon)"] == 0.0


def test_stats_con_produccion_calcula_shannon():
    df = _df([50.0, 50.0])
    r = _cargar_stats()(df, df)
    assert abs(r["Diversidad (Shannon)"] - np.log(2)) < 1e-9
