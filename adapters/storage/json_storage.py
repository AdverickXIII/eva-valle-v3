"""
Adaptador de almacenamiento JSON.
Implementa el puerto StoragePort para archivos JSON.

Usado para:
- Mapa conceptual (Paso 3)
- Manifest de checksums (Paso 0)
- Configuraciones exportadas
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.exceptions import DatasetNotFoundError
from core.logging import get_logger

log = get_logger("adapters.storage.json")


class JsonStorage:
    """Adaptador para lectura/escritura de archivos JSON."""

    def read_json(self, path: Path) -> dict[str, Any]:
        """
        Lee un archivo JSON y retorna un diccionario.

        Args:
            path: Ruta al archivo JSON.

        Returns:
            Diccionario con los datos del JSON.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        if not path.exists():
            raise DatasetNotFoundError(path)

        log.info("Leyendo JSON: %s", path.name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info("JSON cargado: %s", path.name)
        return data

    def write_json(
        self,
        data: dict[str, Any],
        path: Path,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """
        Escribe un diccionario como JSON.

        Args:
            data: Diccionario a guardar.
            path: Ruta de destino.
            indent: Nivel de indentacion (default 2).
            ensure_ascii: Si False, permite caracteres Unicode (tildes).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        log.info("JSON guardado: %s", path.name)

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo JSON existe."""
        return path.exists()

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size
