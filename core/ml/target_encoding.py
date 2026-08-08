"""
Target Encoding sin data leakage.

⚠️ CORRECCION CRITICA (Fase 0 - Bug P6):
El codigo original usaba df.groupby(...).transform("mean") sobre TODO
el dataset ANTES del train_test_split. Esto causaba data leakage:
el modelo "veia" informacion del test set durante el entrenamiento,
inflando artificialmente las metricas.

Solucion: Separar fit (calcular medias con train) de transform
(aplicar medias a cualquier dataset). Esto sigue el patron de sklearn:
fit() solo con train, transform() con train y test.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from core.logging import get_logger

log = get_logger("core.ml.target_encoding")

# Columnas a las que se aplica target encoding
ENCODING_COLUMNS = ["municipio", "desagregacion_cultivo"]
TARGET_COLUMN = "rendimiento_t_ha"


def fit_target_encoding(df_train: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Calcula las medias de target encoding SOLO con el set de entrenamiento.

    ⚠️ Esta funcion debe llamarse DESPUES del train_test_split,
    usando exclusivamente df_train. Nunca usar el dataset completo.

    Args:
        df_train: DataFrame de entrenamiento (post-split).

    Returns:
        Diccionario con las medias por columna de encoding.
        Claves: nombres de columnas. Valores: Series con las medias.
    """
    encoding_maps: dict[str, pd.Series] = {}
    for col in ENCODING_COLUMNS:
        if col in df_train.columns:
            encoding_maps[col] = df_train.groupby(col)[TARGET_COLUMN].mean()
        else:
            log.warning("Columna '%s' no encontrada en df_train.", col)

    log.info(
        "Target encoding ajustado con %d registros de train. Columnas: %s",
        len(df_train), list(encoding_maps.keys()),
    )
    return encoding_maps


def apply_target_encoding(
    df: pd.DataFrame,
    encoding_maps: dict[str, pd.Series],
) -> pd.DataFrame:
    """
    Aplica las medias pre-calculadas a cualquier dataset (train o test).

    ⚠️ Para el test set, se usan las medias calculadas con train.
    Esto evita que el modelo "vea" informacion del test set.

    Args:
        df: DataFrame al que aplicar el encoding (train o test).
        encoding_maps: Diccionario retornado por fit_target_encoding().

    Returns:
        DataFrame con columnas target_enc_* agregadas.
    """
    df = df.copy()
    for col, medias in encoding_maps.items():
        col_enc = f"target_enc_{col}"
        df[col_enc] = df[col].map(medias)
        # Rellenar NaN (categorias no vistas en train) con la media global
        if df[col_enc].isna().any():
            n_missing = df[col_enc].isna().sum()
            global_mean = medias.mean()
            df[col_enc] = df[col_enc].fillna(global_mean)
            log.warning(
                "target_enc_%s: %d valores NaN rellenados con media global (%.2f).",
                col, n_missing, global_mean,
            )

    log.info("Target encoding aplicado a %d registros.", len(df))
    return df
