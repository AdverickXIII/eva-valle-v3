"""Genera README.md."""
from pathlib import Path

README = '''# EVA Valle v3.0

Dashboard analitico de produccion agricola del Valle del Cauca.
UPRA - EVA 2019-2024.

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-15%20passed-brightgreen.svg)](docs/TESTS.md)
[![Arquitectura](https://img.shields.io/badge/Arquitectura-Hexagonal-orange.svg)](docs/ARQUITECTURA.md)

## Descripcion

Analiza 6 anos (2019-2024) de datos agricolas del Valle del Cauca:
42 municipios, 97 desagregaciones de cultivo, 9,032 registros.
Ofrece analisis descriptivo, diagnostico causal y proyecciones predictivas.

## Caracteristicas

- 8 paginas interactivas con graficos Plotly
- 12 analisis descriptivos (Gini, HHI, Lorenz, Shannon, LQ, STL, CAGR)
- 5 analisis diagnosticos (correlacion, K-Means, arbol, shock 2020)
- 3 modelos predictivos (Random Forest x2, Holt-Winters)
- Analisis por cultivo con 3 tablas (municipio, comparativa, ranking)
- Auditoria de calidad (14 hallazgos por severidad)
- Arquitectura Hexagonal (nucleo puro y testeable)
- 15 tests automatizados

## Stack

Python 3.14 | Streamlit + Plotly | Pandas/NumPy | scikit-learn | Selenium | pytest

## Instalacion rapida

    python -m venv .venv
    .venv\\Scripts\\activate.bat
    pip install -r requirements-dev.txt
    (copiar base_agricola_2024.xlsx a data\\raw\\upra\\)
    python scripts\\run_pipeline.py --skip-download
    streamlit run app.py

## Correcciones clave

| Bug original | Correccion | Test |
|---|---|---|
| Gini negativo | Lorenz ascendente (Gini=0.979) | test_gini_en_rango_valido |
| Data leakage | fit solo con train | test_fit_calcula_medias_de_train |
| Modelos no persistidos | JoblibModelRegistry | - |

## Documentacion

- docs/ARQUITECTURA.md | docs/USO_DASHBOARD.md | docs/PIPELINE.md
- docs/TESTS.md | CONTRIBUTING.md | CHANGELOG.md
'''

Path("README.md").write_text(README, encoding="utf-8")
print("[OK] README.md")