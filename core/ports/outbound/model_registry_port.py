"""
Puerto de salida para persistencia de modelos ML.

Define el contrato para guardar/cargar modelos entrenados.
El adaptador adapters/ml_registry/joblib_registry.py implementa
este protocolo usando joblib.

Este puerto resuelve el problema identificado en Fase 0:
los notebooks originales entrenaban modelos pero NO los persistian,
obligando a re-entrenar en cada ejecucion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class ModelRegistryPort(Protocol):
    """Contrato para persistencia de modelos ML."""

    def save_model(self, model: Any, name: str) -> Path:
        """
        Serializa y guarda un modelo entrenado.

        Args:
            model: Objeto del modelo (ej: RandomForestRegressor).
            name: Nombre unico del modelo (ej: "rf_regresion_v1").

        Returns:
            Ruta donde se guardo el modelo.

        Raises:
            ModelTrainingError: Si la serializacion falla.
        """
        ...

    def load_model(self, name: str) -> Any:
        """
        Carga un modelo previamente guardado.

        Args:
            name: Nombre unico del modelo.

        Returns:
            Objeto del modelo deserializado.

        Raises:
            FileNotFoundError: Si el modelo no existe.
        """
        ...

    def model_exists(self, name: str) -> bool:
        """Verifica si un modelo existe en el registro."""
        ...

    def list_models(self) -> list[str]:
        """Lista todos los modelos disponibles en el registro."""
        ...
