"""
Puerto de entrada para analisis descriptivo profundo.

Define el contrato para ejecutar los 12 analisis del Paso 4:
4.3 Descriptiva, 4.4 Distribuciones, 4.5 Outliers, 4.6 Concentracion,
4.7 Series de tiempo, 4.8 Estacionalidad, 4.9 LQ, 4.10 Shannon,
4.11 Elasticidades, 4.12 Inferencial, 4.13 CAGR, 4.14 Ex-Cana.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class AnalyticsPort(Protocol):
    """Contrato para ejecutar analisis descriptivos del Paso 4."""

    def descriptive_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.3: Momentos, percentiles, CV para las 4 metricas."""
        ...

    def distribution_fitting(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.4: KS-test para Normal, Lognormal, Gamma sobre rendimiento."""
        ...

    def multivariate_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.5: Isolation Forest sobre las 4 metricas."""
        ...

    def concentration_analysis(
        self,
        df: pd.DataFrame,
        group: str = "cultivo",
        value: str = "produccion_t",
    ) -> dict[str, Any]:
        """4.6: HHI, Gini (CORREGIDO), datos para curva de Lorenz."""
        ...

    def time_series_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.7: STL + Dickey-Fuller sobre produccion total semestral."""
        ...

    def seasonality_ab(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.8: Wilcoxon A vs B en cultivos transitorios."""
        ...

    def location_quotient(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.9: LQ por municipio x grupo de cultivo."""
        ...

    def shannon_diversity(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.10: Shannon-Wiener por municipio."""
        ...

    def elasticity_analysis(self, df: pd.DataFrame) -> dict[str, float]:
        """4.11: Regresion log-log produccion vs area."""
        ...

    def inferential_test(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.12: Kruskal-Wallis rendimiento por municipio."""
        ...

    def cagr_by_crop(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.13: CAGR por cultivo 2019-2024."""
        ...

    def ex_cana_analysis(self, df: pd.DataFrame) -> dict[str, Any]:
        """4.14: HHI/Gini excluyendo Cultivos Tropicales Tradicionales."""
        ...
