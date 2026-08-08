"""Servicio centralizado de carga y validacion de datos para la UI."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import settings

COLUMNAS_REQUERIDAS = [
    "municipio", "cultivo", "grupo_cultivo", "ano", "periodo",
    "area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha",
]


@st.cache_data(ttl=3600)
def load_model_dataset() -> pd.DataFrame:
    """Carga el dataset del modelo conceptual con cache de 1 hora."""
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def validate_dataset(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Verifica que el dataset tenga las columnas requeridas y datos.

    Returns:
        Tupla (es_valido, lista_de_problemas).
    """
    problemas = []
    if df is None or df.empty:
        return False, ["El dataset esta vacio o no existe. Ejecuta el pipeline."]
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        problemas.append(f"Columnas faltantes: {faltantes}")
    return (len(problemas) == 0), problemas
