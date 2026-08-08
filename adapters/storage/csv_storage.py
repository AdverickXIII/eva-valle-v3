"""
Adaptador de almacenamiento CSV.
Implementa el puerto StoragePort para archivos CSV.

Resuelve problemas del pipeline original:
- Validacion de existencia antes de leer
- Encoding consistente (utf-8-sig para compatibilidad con Excel)
- Logging centralizado
- Excepciones personalizadas con mensajes claros
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.exceptions import DatasetNotFoundError
from core.logging import get_logger

log = get_logger("adapters.storage.csv")


class CsvStorage:
    """Adaptador para lectura/escritura de archivos CSV."""

    def read_csv(
        self,
        path: Path,
        encoding: str = "utf-8-sig",
        low_memory: bool = False,
    ) -> pd.DataFrame:
        """
        Lee un archivo CSV y retorna un DataFrame.

        Args:
            path: Ruta al archivo CSV.
            encoding: Codificacion del archivo (default utf-8-sig).
            low_memory: Si False, pandas infiere tipos de forma consistente.

        Returns:
            DataFrame con los datos del CSV.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        if not path.exists():
            raise DatasetNotFoundError(
                path,
                "Ejecuta el paso anterior del pipeline primero.",
            )

        log.info("Leyendo CSV: %s", path.name)
        df = pd.read_csv(path, encoding=encoding, low_memory=low_memory)
        log.info(
            "CSV cargado: %s (%d filas x %d columnas)",
            path.name,
            len(df),
            len(df.columns),
        )
        return df

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
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=index, encoding=encoding)
        log.info("CSV guardado: %s (%d filas)", path.name, len(df))

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo CSV existe."""
        return path.exists()

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size
