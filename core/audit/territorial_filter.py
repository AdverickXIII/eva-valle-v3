"""
Filtrado territorial del dataset nacional al departamento objetivo.

Migrado del Notebook 2 (Paso 1).
Mejora: la configuracion (codigo DANE, nombre) se lee de config.constants.
"""
from __future__ import annotations

import pandas as pd

from config.constants import CODIGO_DANE_VALLE, NOMBRE_DEPTO_VALLE
from core.logging import get_logger

log = get_logger("core.audit.territorial_filter")


def filter_by_department(
    df: pd.DataFrame,
    codigo_dane: int = CODIGO_DANE_VALLE,
    nombre_depto: str = NOMBRE_DEPTO_VALLE,
) -> pd.DataFrame:
    """
    Filtra por codigo DANE (primario) con verificacion cruzada por nombre.

    Args:
        df: DataFrame nacional completo.
        codigo_dane: Codigo DANE del departamento objetivo (default 76).
        nombre_depto: Nombre del departamento para verificacion cruzada.

    Returns:
        DataFrame filtrado con indice reseteado.
    """
    mask_codigo = df["codigo_dane_departamento"] == codigo_dane
    mask_nombre = df["departamento"].str.lower() == nombre_depto.lower()

    solo_codigo = mask_codigo & ~mask_nombre
    solo_nombre = ~mask_codigo & mask_nombre

    if solo_codigo.sum() > 0:
        log.warning(
            "%d registros con codigo %d pero nombre != '%s'.",
            solo_codigo.sum(), codigo_dane, nombre_depto,
        )
    if solo_nombre.sum() > 0:
        log.warning(
            "%d registros con nombre '%s' pero codigo != %d.",
            solo_nombre.sum(), nombre_depto, codigo_dane,
        )

    df_filtrado = df[mask_codigo].copy().reset_index(drop=True)
    log.info("Filtro aplicado (DANE=%d): %d registros.", codigo_dane, len(df_filtrado))
    return df_filtrado
