"""
Puerto de entrada para analisis diagnostico.

Define el contrato para ejecutar los 5 analisis del Paso 6:
6.1 Correlacion, 6.2 Comparacion grupos, 6.3 K-Means,
6.4 Arbol de decision, 6.5 Shock 2020.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class DiagnosticsPort(Protocol):
    """Contrato para ejecutar analisis diagnosticos del Paso 6."""

    def correlation_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """6.1: Matriz Spearman + scatterplots clave."""
        ...

    def group_comparison(self, df: pd.DataFrame) -> dict[str, Any]:
        """6.2: Mann-Whitney U (Transitorio vs Permanente)."""
        ...

    def municipality_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """6.3: K-Means clustering de municipios."""
        ...

    def root_cause_analysis(self, df: pd.DataFrame) -> pd.Series:
        """6.4: Arbol de decision regresor (importancia de variables)."""
        ...

    def shock_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """6.5: Variacion interanual 2020 vs tendencia."""
        ...
