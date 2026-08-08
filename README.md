# EVA Valle v3.0

[![Tests](https://github.com/AdverickXIII/eva-valle-v3/actions/workflows/tests.yml/badge.svg)](https://github.com/AdverickXIII/eva-valle-v3/actions)
Dashboard analitico de produccion agricola del Valle del Cauca (UPRA).

## Quick Start

    .venv\Scripts\activate.bat
    pip install -r requirements-dev.txt
    streamlit run app.py

## Arquitectura

Hexagonal Modular (Ports & Adapters).

- core/ - Nucleo de dominio
- adapters/ - Infraestructura
- ui/ - Interfaz Streamlit
- config/ - Configuracion
