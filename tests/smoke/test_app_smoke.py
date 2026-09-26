"""Prueba de humo de la app: ejecuta app.py y cada pagina como un admin ya logueado.

Atrapa lo que los tests unitarios no ven: imports rotos (p. ej. un modulo archivado
que otro sigue importando) y paginas que lanzan una excepcion al renderizar.
Es lo mas parecido a abrir la app en Streamlit Cloud sin abrir un navegador.

    python -m pytest tests/smoke -v
"""
from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "ui" / "pages"

# 0_Home usa st.page_link, que solo funciona con las paginas registradas por
# st.navigation en app.py; se cubre en test_app_completa (es la pagina por defecto).
PAGINAS = sorted(p.name for p in PAGES.glob("[0-9]*_*.py") if p.name != "0_Home.py")


@pytest.fixture(autouse=True)
def _desde_la_raiz(monkeypatch):
    monkeypatch.chdir(ROOT)
    monkeypatch.syspath_prepend(str(ROOT))


def _ejecutar(ruta: Path) -> AppTest:
    at = AppTest.from_file(str(ruta), default_timeout=180)
    at.session_state["authenticated"] = True
    at.session_state["username"] = "admin"
    at.session_state["role"] = "admin"
    at.session_state["last_activity"] = datetime.now()
    at.run()
    return at


def _excepciones(at: AppTest) -> list[str]:
    return [str(e.value)[:300] for e in at.exception]


def test_app_completa_sin_excepciones():
    at = _ejecutar(ROOT / "app.py")
    assert not _excepciones(at), _excepciones(at)


def test_hay_paginas_que_probar():
    # Evita que el parametrize quede vacio (y el test "pase") si cambia la estructura.
    assert len(PAGINAS) >= 15, PAGINAS


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_sin_excepciones(pagina):
    at = _ejecutar(PAGES / pagina)
    assert not _excepciones(at), _excepciones(at)


def test_reporte_municipal_pdf_y_excel():
    import pandas as pd

    from config.settings import settings
    from core.reports import build_municipality_excel, build_municipality_pdf

    ruta = Path(settings.DATA_MODEL_PATH) / "eva_agricola_valle_modelo_conceptual.csv"
    assert ruta.exists(), f"falta el dataset del modelo: {ruta}"
    df = pd.read_csv(ruta, low_memory=False)

    pdf = build_municipality_pdf(df, "Palmira")
    assert pdf[:5] == b"%PDF-" and len(pdf) > 10_000

    xlsx = build_municipality_excel(df, "Palmira")
    assert xlsx[:2] == b"PK" and len(xlsx) > 1_000   # .xlsx es un zip
