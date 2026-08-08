"""
Analisis 7.1: Feature Engineering.
Creacion de variables predictoras: lags, log-transformacion, fraccion de cosecha.

⚠️ IMPORTANTE: Esta funcion NO incluye target encoding.
El target encoding se hace en target_encoding.py con fit/transform
separados para evitar data leakage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.ml.features")


def create_features_ml(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea la matriz de caracteristicas base (sin target encoding).

    Features generadas:
    - produccion_lag1: Produccion del periodo anterior
    - rendimiento_lag1: Rendimiento del periodo anterior
    - log_produccion: log1p(produccion_t) para normalizar sesgo
    - frac_cosechada: area_cosechada / area_sembrada
    - perdida_cosecha: Flag binario (frac_cosechada < 0.90)

    Args:
        df: DataFrame con columnas del modelo conceptual.

    Returns:
        DataFrame con features adicionales, filtrado a registros
        con lags validos.
    """
    required_cols = [
        "codigo_dane_municipio", "desagregacion_cultivo", "ano", "periodo",
        "produccion_t", "rendimiento_t_ha", "area_sembrada_ha", "area_cosechada_ha",
    ]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para feature engineering: %s", faltantes)
        return pd.DataFrame()

    df_ml = df.copy()
    df_ml = df_ml.sort_values(
        ["codigo_dane_municipio", "desagregacion_cultivo", "ano", "periodo"]
    )

    # Lags por grupo (municipio + cultivo)
    grupo = ["codigo_dane_municipio", "desagregacion_cultivo"]
    df_ml["produccion_lag1"] = df_ml.groupby(grupo)["produccion_t"].shift(1)
    df_ml["rendimiento_lag1"] = df_ml.groupby(grupo)["rendimiento_t_ha"].shift(1)

    # Log-transformacion del target (normaliza sesgo a derecha)
    df_ml["log_produccion"] = np.log1p(df_ml["produccion_t"])

    # Fraccion de area cosechada vs sembrada
    df_ml["frac_cosechada"] = np.where(
        df_ml["area_sembrada_ha"] > 0,
        df_ml["area_cosechada_ha"] / df_ml["area_sembrada_ha"],
        np.nan,
    )

    # Flag de perdida de cosecha (frac < 0.90 = perdio mas del 10% del area)
    df_ml["perdida_cosecha"] = (df_ml["frac_cosechada"] < 0.90).astype(int)

    # Filtrar registros sin lags validos (primera observacion de cada grupo)
    n_antes = len(df_ml)
    df_ml = df_ml.dropna(subset=["produccion_lag1", "rendimiento_lag1"])
    n_despues = len(df_ml)

    log.info(
        "Feature engineering completado: %d -> %d registros (%d sin lags).",
        n_antes, n_despues, n_antes - n_despues,
    )
    return df_ml
