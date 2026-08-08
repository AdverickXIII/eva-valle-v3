"""Fase 9 parte 1: README.md, CHANGELOG.md, CONTRIBUTING.md."""
from pathlib import Path

README = '''# \\U0001F33E EVA Valle v3.0

**Dashboard analitico de produccion agricola del Valle del Cauca**
UPRA \\u00b7 EVA 2019\\u20132024

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.61-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-15%20passed-brightgreen.svg)](docs/TESTS.md)
[![Arquitectura](https://img.shields.io/badge/Arquitectura-Hexagonal-orange.svg)](docs/ARQUITECTURA.md)
[![Licencia](https://img.shields.io/badge/Licencia-Uso%20interno-lightgrey.svg)](#)

---

## \\U0001F4CB Descripcion

EVA Valle v3.0 es un dashboard interactivo que analiza **6 anos de datos agricolas**
(2019\\u20132024) del Valle del Cauca, basados en las Encuestas de Valuacion Agropecuaria
(EVA) de la **UPRA** (Unidad de Planificacion Rural y Agropecuaria).

Cubre **42 municipios**, **97 desagregaciones de cultivo** y **9,032 registros**,
ofreciendo analisis descriptivo, diagnostico causal y proyecciones predictivas.

## \\u2728 Caracteristicas

- \\U0001F4CA **8 paginas interactivas** con graficos Plotly (zoom, hover, tooltips)
- \\U0001F4C8 **12 analisis descriptivos**: Gini, HHI, Lorenz, Shannon, LQ, STL, CAGR...
- \\U0001F52C **5 analisis diagnosticos**: correlacion, K-Means, arbol de decision, shock 2020
- \\U0001F916 **3 modelos predictivos**: Random Forest (regresion y clasificacion), Holt-Winters
- \\U0001F331 **Analisis por cultivo**: historico departamental y por municipio (3 tablas)
- \\U0001F50D **Auditoria de calidad**: 14 hallazgos clasificados por severidad
- \\U0001F3D7\\uFE0F **Arquitectura Hexagonal** (Ports & Adapters) \\u2014 nucleo puro y testeable
- \\U0001F9EA **15 tests automatizados** que protegen las correcciones criticas

## \\U0001F6E0 Stack Tecnologico

| Capa | Tecnologia |
|---|---|
| Lenguaje | Python 3.14 |
| UI | Streamlit + Plotly |
| Datos | Pandas, NumPy, openpyxl |
| ML | scikit-learn, statsmodels, SciPy |
| Descarga | Selenium + webdriver-manager |
| Calidad | pytest, pytest-cov, ruff, mypy |

## \\U0001F680 Instalacion Rapida

```bash
# 1. Clonar y crear entorno virtual
python -m venv .venv
.venv\\Scripts\\activate.bat        # Windows

# 2. Instalar dependencias
pip install -r requirements-dev.txt

# 3. Copiar el archivo de datos (o descargarlo)
#    Opcion A: copiar base_agricola_2024.xlsx a data\\raw\\upra\\
#    Opcion B: python scripts\\download_data.py

# 4. Ejecutar el pipeline completo
python scripts\\run_pipeline.py --skip-download

# 5. Arrancar el dashboard
streamlit run app.py