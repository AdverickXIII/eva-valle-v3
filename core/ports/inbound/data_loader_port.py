"""
Puerto de entrada para carga de datasets.

Define el contrato para cargar los datasets del pipeline:
- Dataset estandarizado (salida del Paso 1+2)
- Dataset con modelo conceptual (salida del Paso 3)

Los Pasos 4, 5, 6 y 7 consumen este puerto al inicio.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class DataLoaderPort(Protocol):
    """Contrato para cargar datasets del pipeline EVA."""

    def load_clean_dataset(self) -> pd.DataFrame:
        """
        Carga el dataset estandarizado del Paso 1+2.

        Returns:
            DataFrame con ~9,032 registros del Valle del Cauca,
            18 columnas, tipos correctos (Int64, float64, str).

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        ...

    def load_model_dataset(self) -> pd.DataFrame:
        """
        Carga el dataset con modelo conceptual del Paso 3.
        Incluye la columna id_registro (llave surrogate).

        Returns:
            DataFrame con ~9,032 registros, 19 columnas
            (18 originales + id_registro).

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        ...

    def get_record_count(self) -> int:
        """
        Retorna el numero de registros del dataset cargado.
        Util para validaciones rapidas sin cargar todo el DataFrame.
        """
        ...
