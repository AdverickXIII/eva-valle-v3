"""
Reconversion de tipos tras la carga de CSV.

pd.read_csv degrada Int64 nullable a int64/float64.
Esta funcion restaura los tipos correctos.
"""
from __future__ import annotations

import pandas as pd

from core.logging import get_logger

log = get_logger("core.modeling.type_reconversion")

# Columnas que deben ser Int64 nullable
INT_COLUMNS = [
    "codigo_dane_departamento",
    "codigo_dane_municipio",
    "ano",
    "codigo_del_cultivo",
]

# Columnas que deben ser float64
FLOAT_COLUMNS = [
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_t_ha",
]


def reconvert_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Restaura los tipos correctos tras la degradacion de read_csv.

    Args:
        df: DataFrame cargado desde CSV.

    Returns:
        DataFrame con tipos restaurados (copia, no modifica el original).
    """
    df = df.copy()
    anomalias: list[str] = []

    for col in INT_COLUMNS:
        if col in df.columns:
            antes = df[col].copy()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            n_fail = df[col].isna().sum() - antes.isna().sum()
            if n_fail > 0:
                anomalias.append(f"'{col}': {n_fail} valores no convertibles")
            if df[col].notna().all():
                df[col] = df[col].astype("Int64")

    for col in FLOAT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")

    if anomalias:
        for a in anomalias:
            log.warning("Reconversion: %s", a)
    else:
        log.info("Reconversion de tipos sin anomalias.")

    return df
