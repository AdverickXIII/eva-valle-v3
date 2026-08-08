"""
Puerto de entrada para Machine Learning predictivo.

Define el contrato para ejecutar los modelos del Paso 7:
7.1 Feature engineering, 7.2 Regresion RF, 7.3 Clasificacion RF,
7.4 Holt-Winters, 7.5 Scoring.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class MLPort(Protocol):
    """Contrato para ejecutar modelos predictivos del Paso 7."""

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """7.1: Feature engineering (lags, target encoding, log)."""
        ...

    def train_regression(self, df: pd.DataFrame) -> dict[str, Any]:
        """7.2: Random Forest Regressor sobre log(produccion)."""
        ...

    def train_classification(self, df: pd.DataFrame) -> dict[str, Any]:
        """7.3: Random Forest Classifier para perdida de cosecha."""
        ...

    def forecast_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """7.4: Holt-Winters para proyeccion tendencial."""
        ...

    def get_model_metrics(self) -> dict[str, Any]:
        """Retorna metricas consolidadas de todos los modelos."""
        ...
