"""
Puerto de salida para descarga de datos de UPRA.

Define el contrato para descargar las bases EVA desde el portal
de la UPRA. El adaptador adapters/downloader/upra_downloader.py
implementa este protocolo usando Selenium.

Este puerto es consumido por:
- El script scripts/download_data.py
- La pagina de Configuracion de Streamlit (Fase 5)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class DownloaderPort(Protocol):
    """Contrato para descarga de archivos desde fuente externa."""

    def download(
        self,
        file_key: str,
        force: bool = False,
    ) -> Path:
        """
        Descarga un archivo identificado por file_key.

        Args:
            file_key: Identificador del archivo ("agricola", "pecuario").
            force: Si True, re-descarga aunque el checksum sea igual.

        Returns:
            Ruta local al archivo descargado.

        Raises:
            DownloaderError: Si la descarga falla tras todos los reintentos.
        """
        ...

    def verify_checksum(self, path: Path) -> bool:
        """
        Verifica que el archivo descargado es valido (magic bytes Excel).

        Args:
            path: Ruta al archivo descargado.

        Returns:
            True si el archivo tiene firma Excel valida.
        """
        ...

    def get_download_status(self) -> dict[str, Any]:
        """
        Retorna el estado de las descargas (para mostrar en UI).

        Returns:
            Dict con estado de cada archivo: exitoso, tamano, checksum, etc.
        """
        ...
