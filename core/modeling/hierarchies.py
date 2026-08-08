"""
Generacion de jerarquias del modelo conceptual.

Tres jerarquias:
1. Territorial: Pais > Departamento > Municipio
2. Cultivo: Grupo > Subgrupo > Cultivo > Desagregacion
3. Temporal: Anio > Periodo
"""
from __future__ import annotations

import pandas as pd

from core.logging import get_logger

log = get_logger("core.modeling.hierarchies")


def generate_territorial_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera la jerarquia territorial con estadisticas por municipio.

    Args:
        df: DataFrame con datos del Valle del Cauca.

    Returns:
        DataFrame con codigo, nombre y estadisticas por municipio.
    """
    hier_muni = (
        df.groupby([
            "codigo_dane_departamento", "departamento",
            "codigo_dane_municipio", "municipio",
        ])
        .agg(
            total_registros=("id_registro", "count"),
            cultivos_distintos=("desagregacion_cultivo", "nunique"),
            grupos_cultivo=("grupo_cultivo", "nunique"),
            anos_presentes=("ano", "nunique"),
            area_sembrada_total=("area_sembrada_ha", "sum"),
            produccion_total_t=("produccion_t", "sum"),
            rendimiento_mediano=("rendimiento_t_ha", "median"),
        )
        .reset_index()
        .sort_values("codigo_dane_municipio")
    )
    log.info("Jerarquia territorial: %d municipios", len(hier_muni))
    return hier_muni


def generate_crop_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera la jerarquia de cultivos con estadisticas por desagregacion.

    Args:
        df: DataFrame con datos del Valle del Cauca.

    Returns:
        DataFrame con la jerarquia completa de cultivos.
    """
    hier_cultivo = (
        df.groupby([
            "grupo_cultivo", "subgrupo", "cultivo", "desagregacion_cultivo",
            "codigo_del_cultivo", "nombre_cientifico_del_cultivo", "ciclo_del_cultivo",
        ])
        .agg(
            total_registros=("id_registro", "count"),
            municipios_activos=("codigo_dane_municipio", "nunique"),
            anos_presentes=("ano", "nunique"),
            primer_ano=("ano", "min"),
            ultimo_ano=("ano", "max"),
            produccion_total_t=("produccion_t", "sum"),
            rendimiento_mediana=("rendimiento_t_ha", "median"),
        )
        .reset_index()
        .sort_values(["grupo_cultivo", "subgrupo", "cultivo"])
    )
    log.info("Jerarquia de cultivos: %d desagregaciones", len(hier_cultivo))
    return hier_cultivo


def generate_temporal_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera la jerarquia temporal (anio > periodo).

    Args:
        df: DataFrame con datos del Valle del Cauca.

    Returns:
        DataFrame con conteo de registros por anio/ciclo/periodo.
    """
    temp = (
        df.groupby(["ano", "ciclo_del_cultivo", "periodo"])
        .size()
        .reset_index(name="registros")
        .sort_values(["ano", "ciclo_del_cultivo", "periodo"])
    )
    log.info("Jerarquia temporal: %d periodos", len(temp))
    return temp
