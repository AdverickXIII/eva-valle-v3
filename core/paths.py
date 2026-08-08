"""
Utilidades para resolucion de rutas del proyecto.
Extraido de los 7 notebooks originales para eliminar duplicacion (DRY).

Uso:
    from core.paths import find_project_root, get_paths
    root = find_project_root()
    paths = get_paths(root)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

# Importacion diferida para evitar dependencia circular con config.constants
# (ROOT_MARKERS se usa aqui pero se define en constants)


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Sube el arbol de directorios buscando marcadores de raiz del proyecto.

    Args:
        start: Directorio de inicio. Si es None, usa cwd().

    Returns:
        Path absoluta al directorio raiz del proyecto.
        Si no encuentra marcadores, retorna start.resolve().

    Ejemplo:
        >>> root = find_project_root()
        >>> print(root.name)
        'eva-valle-v3.0'
    """
    # Importar aqui para romper dependencia circular
    from config.constants import ROOT_MARKERS

    if start is None:
        start = Path.cwd()
    candidate = start.resolve()

    for directory in [candidate, *candidate.parents]:
        if any((directory / marker).exists() for marker in ROOT_MARKERS):
            return directory

    return candidate


def get_paths(root: Optional[Path] = None) -> dict[str, Path]:
    """
    Construye un diccionario con todas las rutas estandar del proyecto.

    Args:
        root: Raiz del proyecto. Si es None, se detecta automaticamente.

    Returns:
        Diccionario con claves: data_raw, data_clean, data_modelo,
        data_external, outputs_figures, outputs_tables, outputs_reports, logs.

    Nota:
        Este helper es legado del pipeline original. En la nueva arquitectura
        se recomienda usar directamente `config.settings.settings.DATA_RAW_PATH`, etc.
        Se mantiene para compatibilidad durante la migracion.
    """
    if root is None:
        root = find_project_root()

    return {
        "data_raw": root / "data" / "raw" / "upra",
        "data_clean": root / "data" / "processed" / "01_clean",
        "data_modelo": root / "data" / "processed" / "02_modelo",
        "data_external": root / "data" / "external",
        "outputs_figures": root / "outputs" / "figures",
        "outputs_tables": root / "outputs" / "tables",
        "outputs_reports": root / "outputs" / "reports",
        "logs": root / "logs",
    }


def ensure_directories(paths: dict[str, Path]) -> None:
    """
    Crea todos los directorios del diccionario si no existen (idempotente).

    Args:
        paths: Diccionario de rutas (como el retornado por get_paths).
    """
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
