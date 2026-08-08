# EVA Valle v3.0

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
