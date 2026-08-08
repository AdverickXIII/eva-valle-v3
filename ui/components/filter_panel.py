"""Panel de filtros dinamicos para el dashboard."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def render_filter_panel(
    df: pd.DataFrame,
    key_prefix: str = "filter",
) -> dict[str, Any]:
    """
    Renderiza el panel de filtros en el sidebar.

    Args:
        df: DataFrame completo con los datos.
        key_prefix: Prefijo para las keys de los widgets.

    Returns:
        Diccionario con los filtros seleccionados:
        {municipio, cultivo, grupo_cultivo, ano, ciclo}.
    """
    filters: dict[str, Any] = {}

    st.sidebar.markdown("### \U0001F50D Filtros")

    # Municipio
    municipios = sorted(df["municipio"].dropna().unique().tolist())
    selected_municipio = st.sidebar.multiselect(
        "Municipio",
        options=municipios,
        key=f"{key_prefix}_municipio",
        placeholder="Todos los municipios",
    )
    filters["municipio"] = selected_municipio if selected_municipio else None

    # Grupo de cultivo
    grupos = sorted(df["grupo_cultivo"].dropna().unique().tolist())
    selected_grupo = st.sidebar.multiselect(
        "Grupo de Cultivo",
        options=grupos,
        key=f"{key_prefix}_grupo",
        placeholder="Todos los grupos",
    )
    filters["grupo_cultivo"] = selected_grupo if selected_grupo else None

    # Ciclo del cultivo
    selected_ciclo = st.sidebar.radio(
        "Ciclo del Cultivo",
        options=["Todos", "Transitorio", "Permanente"],
        key=f"{key_prefix}_ciclo",
    )
    filters["ciclo_del_cultivo"] = None if selected_ciclo == "Todos" else selected_ciclo

    # Anio
    anos = sorted(df["ano"].dropna().unique().tolist())
    selected_ano = st.sidebar.slider(
        "Rango de Anios",
        min_value=int(min(anos)),
        max_value=int(max(anos)),
        value=(int(min(anos)), int(max(anos))),
        key=f"{key_prefix}_ano",
    )
    filters["ano_range"] = selected_ano

    # Boton de limpiar filtros
    if st.sidebar.button("\U0001F504 Limpiar Filtros", key=f"{key_prefix}_clear"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.markdown("---")
    return filters


def apply_filters(df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    """
    Aplica los filtros seleccionados al DataFrame.

    Args:
        df: DataFrame completo.
        filters: Diccionario retornado por render_filter_panel().

    Returns:
        DataFrame filtrado.
    """
    df_filtered = df.copy()

    if filters.get("municipio"):
        df_filtered = df_filtered[df_filtered["municipio"].isin(filters["municipio"])]

    if filters.get("grupo_cultivo"):
        df_filtered = df_filtered[df_filtered["grupo_cultivo"].isin(filters["grupo_cultivo"])]

    if filters.get("ciclo_del_cultivo"):
        df_filtered = df_filtered[df_filtered["ciclo_del_cultivo"] == filters["ciclo_del_cultivo"]]

    if filters.get("ano_range"):
        ano_min, ano_max = filters["ano_range"]
        df_filtered = df_filtered[(df_filtered["ano"] >= ano_min) & (df_filtered["ano"] <= ano_max)]

    return df_filtered
