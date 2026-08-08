"""
Puerto de salida para persistencia de archivos.

Define el contrato para leer/escribir archivos CSV, Excel y JSON.
Los adaptadores adapters/storage/ implementan este protocolo.

Este puerto es consumido por:
- Todos los pasos del pipeline (para cargar/guardar datos)
- El modulo de auditoria (para guardar reportes)
- El modulo de analytics (para exportar artefactos)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import pandas as pd


class StoragePort(Protocol):
    """Contrato para operaciones de lectura/escritura de archivos."""

    def read_csv(self, path: Path) -> pd.DataFrame:
        """
        Lee un archivo CSV y retorna un DataFrame.

        Args:
            path: Ruta al archivo CSV.

        Returns:
            DataFrame con los datos del CSV.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        ...

    def write_csv(
        self,
        df: pd.DataFrame,
        path: Path,
        encoding: str = "utf-8-sig",
        index: bool = False,
    ) -> None:
        """
        Escribe un DataFrame como CSV.

        Args:
            df: DataFrame a guardar.
            path: Ruta de destino.
            encoding: Codificacion (default utf-8-sig para Excel).
            index: Si incluir el indice (default False).
        """
        ...

    def read_excel(
        self,
        path: Path,
        sheet_name: str,
        skiprows: int = 0,
    ) -> pd.DataFrame:
        """
        Lee un archivo Excel (.xlsx) y retorna un DataFrame.

        Args:
            path: Ruta al archivo Excel.
            sheet_name: Nombre de la hoja.
            skiprows: Filas a saltar antes del header.

        Returns:
            DataFrame con los datos del Excel.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
            ValueError: Si la hoja no existe.
        """
        ...

    def read_json(self, path: Path) -> dict[str, Any]:
        """Lee un archivo JSON y retorna un diccionario."""
        ...

    def write_json(
        self,
        data: dict[str, Any],
        path: Path,
        indent: int = 2,
    ) -> None:
        """Escribe un diccionario como JSON."""
        ...

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo existe."""
        ...

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        ...
