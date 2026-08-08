"""
Funciones de conversion de tipos para el pipeline de carga.

Migrado del Notebook 2 (Paso 1).
Mejora: la funcion original modificaba in-place; esta version retorna
una copia del DataFrame (funcion pura).
"""
from __future__ import annotations

import pandas as pd

from core.logging import get_logger

log = get_logger("core.audit.type_conversion")


def convert_to_numeric(
    df: pd.DataFrame,
    column: str,
    dtype: str,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Convierte una columna a tipo numerico. NO modifica el original in-place.

    Args:
        df: DataFrame de trabajo (no se modifica).
        column: Nombre de columna a convertir.
        dtype: Tipo destino: 'int' (Int64 nullable) o 'float' (float64).

    Returns:
        Tupla (DataFrame con columna convertida, lista de mensajes de anomalia).

    Ejemplo:
        >>> df_new, anomalies = convert_to_numeric(df, "ano", "int")
    """
    df = df.copy()
    original = df[column].copy()
    df[column] = pd.to_numeric(df[column], errors="coerce")

    anomalies: list[str] = []
    n_coerced = df[column].isna().sum() - original.isna().sum()
    if n_coerced > 0:
        vals = original[df[column].isna() & original.notna()].unique()[:5]
        msg = (
            f"Col '{column}': {n_coerced} valor(es) no convertible(s) a NaN. "
            f"Ejemplos: {list(vals)}"
        )
        anomalies.append(msg)
        log.warning(msg)

    if dtype == "int" and df[column].notna().all():
        df[column] = df[column].astype("Int64")
    elif dtype == "float":
        df[column] = df[column].astype("float64")

    return df, anomalies
