"""
Adaptador de almacenamiento Excel.
Implementa el puerto StoragePort para archivos .xlsx.

Resuelve problemas del pipeline original:
- Validacion de tamano minimo antes de leer
- Validacion de magic bytes (firma Excel)
- Deteccion automatica de fila de header
- Excepciones personalizadas
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.constants import MIN_FILE_BYTES
from core.exceptions import DatasetNotFoundError
from core.logging import get_logger

log = get_logger("adapters.storage.excel")

# Firmas binarias de archivos Excel
_EXCEL_MAGIC_BYTES = {
    b"PK\x03\x04": ".xlsx",   # ZIP (Office Open XML)
    b"\xd0\xcf\x11\xe0": ".xls",  # OLE2 (Excel 97-2003)
}


class ExcelStorage:
    """Adaptador para lectura de archivos Excel (.xlsx/.xls)."""

    def read_excel(
        self,
        path: Path,
        sheet_name: str,
        skiprows: int = 0,
        dtype: type | None = str,
    ) -> pd.DataFrame:
        """
        Lee un archivo Excel y retorna un DataFrame.

        Args:
            path: Ruta al archivo Excel.
            sheet_name: Nombre de la hoja a leer.
            skiprows: Filas a saltar antes del header.
            dtype: Tipo de dato para todas las columnas (default str).

        Returns:
            DataFrame con los datos del Excel.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
            ValueError: Si el archivo es demasiado pequeno o no es Excel valido.
        """
        if not path.exists():
            raise DatasetNotFoundError(
                path,
                "Ejecuta el Downloader (Paso 0) primero.",
            )

        # Validar tamano minimo
        size = path.stat().st_size
        if size < MIN_FILE_BYTES:
            raise ValueError(
                f"Archivo sospechosamente pequeno: {size:,} bytes "
                f"(minimo: {MIN_FILE_BYTES:,}). Posible descarga truncada."
            )

        # Validar magic bytes
        if not self._is_valid_excel(path):
            raise ValueError(
                f"El archivo {path.name} no tiene firma Excel valida."
            )

        log.info(
            "Leyendo Excel: %s | Hoja: %s | skiprows=%d",
            path.name,
            sheet_name,
            skiprows,
        )
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl",
            skiprows=skiprows,
            header=0,
            dtype=dtype,
        )
        log.info(
            "Excel cargado: %s (%d filas x %d columnas)",
            path.name,
            len(df),
            len(df.columns),
        )
        return df

    def detect_header_row(
        self,
        path: Path,
        sheet_name: str,
        search_term: str = "departamento",
        max_scan: int = 15,
    ) -> int:
        """
        Detecta automaticamente la fila del header buscando un termino.

        Args:
            path: Ruta al archivo Excel.
            sheet_name: Nombre de la hoja.
            search_term: Termino a buscar en las filas.
            max_scan: Maximo de filas a escanear.

        Returns:
            Indice (base 0) de la fila del header.

        Raises:
            ValueError: Si no se encuentra el header.
        """
        df_scan = pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl",
            nrows=max_scan,
            header=None,
        )
        for idx, row in df_scan.iterrows():
            valores = [
                str(v).strip().lower()
                for v in row.values
                if str(v) != "nan"
            ]
            if any(search_term in v for v in valores):
                log.info("Header detectado en fila %d (base 0).", idx)
                return idx

        raise ValueError(
            f"No se encontro '{search_term}' en las primeras "
            f"{max_scan} filas. El archivo pudo haber cambiado de formato."
        )

    def get_sheet_names(self, path: Path) -> list[str]:
        """Retorna los nombres de todas las hojas del archivo Excel."""
        xl = pd.ExcelFile(path, engine="openpyxl")
        return xl.sheet_names

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo Excel existe."""
        return path.exists()

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size

    @staticmethod
    def _is_valid_excel(path: Path) -> bool:
        """Verifica que el archivo tenga firma Excel valida (magic bytes)."""
        if not path.exists() or path.stat().st_size == 0:
            return False
        with open(path, "rb") as f:
            header = f.read(8)
        return any(header.startswith(magic) for magic in _EXCEL_MAGIC_BYTES)
