"""
Funciones de normalizacion de nombres para el pipeline de carga.

Migrado del Notebook 2 (Paso 1). Funciones puras sin efectos secundarios.
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from core.logging import get_logger

log = get_logger("core.audit.normalization")


def normalize_column_name(name: str) -> str:
    """
    Normaliza un nombre de columna a snake_case sin tildes.

    Pipeline: strip -> NFD (eliminar diacriticos) -> lower ->
              reemplazar no-alfanumericos por _ -> colapsar _ -> trim.

    Args:
        name: Nombre original de la columna.

    Returns:
        Nombre normalizado en snake_case.

    Ejemplo:
        >>> normalize_column_name("Area sembrada (ha)")
        'area_sembrada_ha'
        >>> normalize_column_name("Codigo Dane departamento")
        'codigo_dane_departamento'
    """
    s = str(name).strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[\s/()\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def normalize_territorial_name(series: pd.Series) -> pd.Series:
    """
    Limpia y estandariza nombres territoriales preservando tildes.

    Aplica title() y luego corrige particulas ("Del" -> "del", etc.)
    que title() capitaliza incorrectamente.

    Args:
        series: Serie con nombres territoriales.

    Returns:
        Serie normalizada con title case corregido.

    Ejemplo:
        >>> normalize_territorial_name(pd.Series(["SANTIAGO DE CALI"]))
        0    Santiago de Cali
    """
    result = (
        series
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )
    particulas = {
        " Del ": " del ",
        " De ": " de ",
        " La ": " la ",
        " Las ": " las ",
        " Los ": " los ",
        " El ": " el ",
        " Y ": " y ",
    }
    for incorrecta, correcta in particulas.items():
        result = result.str.replace(incorrecta, correcta, regex=False)
    return result
