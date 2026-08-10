"""Metadatos de autoria y branding de los reportes."""
from __future__ import annotations

AUTOR = "Moises Zúñiga Grueso"
CARGO = "Data Analyst"
SISTEMA = "EVA Valle v3.0"
FUENTE = "UPRA - Encuestas de Valuacion Agropecuaria (EVA) 2019-2025"


def firma() -> str:
    """Linea de autoria estandar para todos los informes."""
    return f"Elaborado por {AUTOR} - {CARGO}"
