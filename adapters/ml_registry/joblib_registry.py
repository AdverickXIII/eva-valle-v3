"""
Adaptador de persistencia de modelos ML usando joblib.
Implementa el puerto ModelRegistryPort.

Resuelve el problema identificado en Fase 0:
los notebooks originales entrenaban modelos pero NO los persistian,
obligando a re-entrenar en cada ejecucion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from config.settings import settings
from core.exceptions import ModelTrainingError
from core.logging import get_logger

log = get_logger("adapters.ml_registry.joblib")


class JoblibModelRegistry:
    """Registro de modelos ML persistidos con joblib."""

    def __init__(self) -> None:
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)

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
        path = settings.MODELS_PATH / f"{name}.joblib"
        try:
            joblib.dump(model, path)
            log.info("Modelo guardado: %s (%.1f KB)", name, path.stat().st_size / 1024)
            return path
        except Exception as e:
            raise ModelTrainingError(name, f"Fallo al serializar: {e}") from e

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
        path = settings.MODELS_PATH / f"{name}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {path}")
        log.info("Modelo cargado: %s", name)
        return joblib.load(path)

    def model_exists(self, name: str) -> bool:
        """Verifica si un modelo existe en el registro."""
        return (settings.MODELS_PATH / f"{name}.joblib").exists()

    def list_models(self) -> list[str]:
        """Lista todos los modelos disponibles en el registro."""
        return [
            p.stem
            for p in settings.MODELS_PATH.glob("*.joblib")
        ]
