"""
Generacion de llave primaria surrogate para el dataset EVA.

La llave natural (5 campos) se combina en un ID legible y portable:
{municipio}_{cultivo}_{periodo}_{ciclo}_{estado}
"""
from __future__ import annotations

import pandas as pd

from core.audit.normalization import normalize_column_name
from core.logging import get_logger

log = get_logger("core.modeling.surrogate_key")

# Componentes de la llave natural
NATURAL_KEY_COLUMNS: list[str] = [
    "codigo_dane_municipio",
    "desagregacion_cultivo",
    "periodo",
    "ciclo_del_cultivo",
    "estado_fisico_del_cultivo",
]


def generate_surrogate_key(df: pd.DataFrame) -> pd.Series:
    """
    Genera el ID surrogate concatenando los 5 componentes de la llave natural.

    Args:
        df: DataFrame con las columnas de la llave natural.

    Returns:
        Serie con los IDs surrogate (uno por registro).

    Ejemplo:
        >>> df["id_registro"] = generate_surrogate_key(df)
        >>> df["id_registro"].iloc[0]
        '76001_acelga_2019A_transitorio_en_fresco'
    """
    ids = (
        df["codigo_dane_municipio"].astype(str) + "_" +
        df["desagregacion_cultivo"].apply(normalize_column_name) + "_" +
        df["periodo"].astype(str) + "_" +
        df["ciclo_del_cultivo"].apply(normalize_column_name) + "_" +
        df["estado_fisico_del_cultivo"].apply(normalize_column_name)
    )
    log.info("ID surrogate generado: %d registros", len(ids))
    return ids


def validate_natural_key(df: pd.DataFrame) -> tuple[bool, int]:
    """
    Valida que la llave natural sea unica (sin duplicados).

    Args:
        df: DataFrame con las columnas de la llave natural.

    Returns:
        Tupla (es_valida, numero_de_duplicados).
    """
    total = len(df)
    unicos = df.drop_duplicates(subset=NATURAL_KEY_COLUMNS).shape[0]
    duplicados = total - unicos
    es_valida = duplicados == 0

    if es_valida:
        log.info("Llave natural validada: 0 duplicados.")
    else:
        log.error("Llave natural NO valida: %d duplicados.", duplicados)

    return es_valida, duplicados
