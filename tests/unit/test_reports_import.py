"""Regresion: core.reports debe importarse (pdf_report depende de core.analytics.forecast)."""
import importlib

import numpy as np
import pandas as pd
import pytest


@pytest.mark.parametrize("modulo", [
    "core.reports",
    "core.reports.crop_data",
    "core.reports.comparador_pdf",
    "core.reports.riesgo_report",
    "core.reports.executive_report",
    "core.analytics.pareto",
    "core.analytics.executive",
])
def test_modulos_importan(modulo):
    importlib.import_module(modulo)


def test_proyectar_con_ic_contrato_pdf_report():
    # pdf_report.py usa modelo, ganador, mape y los tres escenarios.
    from core.analytics.forecast import proyectar_con_ic

    serie = pd.Series([100.0, 110.0, 120.0, 130.0, 140.0, 150.0], index=range(2019, 2025))
    res = proyectar_con_ic(serie, n_steps=3)
    assert res["modelo"] is not None
    assert isinstance(res["ganador"], str)
    assert np.isfinite(res["mape"])
    for k in ("conservador", "tendencial", "optimista"):
        assert len(res["escenarios"][k]) == 3
        assert np.all(np.isfinite(res["escenarios"][k]))
