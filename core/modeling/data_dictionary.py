"""
Diccionario de variables del dataset EVA Valle del Cauca.

Contiene la documentacion de las 18 variables del dataset original.
Cada entrada incluye: nombre, tipo, categoria, rol analitico,
descripcion, valores, fuente de origen y notas.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

# Diccionario de variables (18 entradas)
DICCIONARIO: list[dict[str, str]] = [
    {
        "nombre": "codigo_dane_departamento",
        "nombre_original": "Codigo Dane departamento",
        "tipo_dato": "Int64",
        "categoria": "Identificador",
        "rol_analitico": "Llave / Filtro territorial",
        "descripcion": "Codigo numerico oficial DANE del departamento. Fijo en 76 para Valle del Cauca.",
        "valores": "76 (constante en este dataset)",
        "fuente_origen": "DANE - DIVIPOLA",
        "notas": "Valor constante: no aporta varianza. Util solo como clave de join.",
    },
    {
        "nombre": "departamento",
        "nombre_original": "Departamento",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Contexto geografico",
        "descripcion": "Nombre oficial del departamento.",
        "valores": "Valle del Cauca (constante)",
        "fuente_origen": "DANE - DIVIPOLA",
        "notas": "Normalizado a title case. Valor constante; excluir de modelos.",
    },
    {
        "nombre": "codigo_dane_municipio",
        "nombre_original": "Codigo Dane municipio",
        "tipo_dato": "Int64",
        "categoria": "Identificador",
        "rol_analitico": "Llave territorial primaria",
        "descripcion": "Codigo numerico de 5 digitos que identifica univocamente al municipio.",
        "valores": "42 valores unicos. Rango: 76001 - 76895",
        "fuente_origen": "DANE - DIVIPOLA",
        "notas": "Usar para joins con IGAC, DNP, etc. Mas robusto que el nombre.",
    },
    {
        "nombre": "municipio",
        "nombre_original": "Municipio",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Dimension geografica",
        "descripcion": "Nombre oficial del municipio segun DIVIPOLA.",
        "valores": "42 valores unicos. Ej: Palmira, Tulua, Buenaventura",
        "fuente_origen": "DANE - DIVIPOLA",
        "notas": "Para legibilidad. Usar codigo_dane_municipio para joins.",
    },
    {
        "nombre": "grupo_cultivo",
        "nombre_original": "Grupo cultivo",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Dimension analitica - Nivel 1 jerarquia cultivo",
        "descripcion": "Agrupacion de mayor nivel de la taxonomia EVA.",
        "valores": "8 grupos: Hortalizas, Frutales, Leguminosas, Cereales, etc.",
        "fuente_origen": "UPRA - Taxonomia EVA",
        "notas": "Usar para agregaciones de alto nivel y segmentacion de analisis.",
    },
    {
        "nombre": "subgrupo",
        "nombre_original": "Subgrupo",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Dimension analitica - Nivel 2 jerarquia cultivo",
        "descripcion": "Subdivision dentro del grupo. Familias botanicas o agrupaciones productivas.",
        "valores": "23 subgrupos: Citricos, Cereales, Hortalizas de fruto, etc.",
        "fuente_origen": "UPRA - Taxonomia EVA",
        "notas": "Nivel intermedio. Util para analisis por familia botanica.",
    },
    {
        "nombre": "cultivo",
        "nombre_original": "Cultivo",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Dimension analitica - Nivel 3 jerarquia cultivo",
        "descripcion": "Nombre del cultivo a nivel de especie o nombre comun.",
        "valores": "78 cultivos unicos en Valle del Cauca.",
        "fuente_origen": "UPRA - Taxonomia EVA",
        "notas": "Un cultivo puede tener varias desagregaciones.",
    },
    {
        "nombre": "desagregacion_cultivo",
        "nombre_original": "Desagregacion cultivo",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Dimension analitica - Nivel 4 jerarquia cultivo (mas granular)",
        "descripcion": "Maxima desagregacion del cultivo. Distingue variedad o tecnologia.",
        "valores": "97 desagregaciones unicas en Valle del Cauca.",
        "fuente_origen": "UPRA - Taxonomia EVA",
        "notas": "Componente principal de la llave primaria.",
    },
    {
        "nombre": "nombre_cientifico_del_cultivo",
        "nombre_original": "Nombre cientifico del cultivo",
        "tipo_dato": "str",
        "categoria": "Dimensional",
        "rol_analitico": "Contexto taxonomico",
        "descripcion": "Nombre binomial cientifico del cultivo.",
        "valores": "76 nombres cientificos unicos.",
        "fuente_origen": "UPRA - Taxonomia EVA",
        "notas": "Util para joins con bases de datos botanicas.",
    },
    {
        "nombre": "codigo_del_cultivo",
        "nombre_original": "Codigo del cultivo",
        "tipo_dato": "Int64",
        "categoria": "Identificador",
        "rol_analitico": "Llave de cultivo para joins",
        "descripcion": "Codigo numerico unico asignado por la UPRA a cada cultivo.",
        "valores": "Entero positivo. Un codigo por cultivo.",
        "fuente_origen": "UPRA - Catalogo de cultivos EVA",
        "notas": "Mas estable que el nombre para joins historicos.",
    },
    {
        "nombre": "ciclo_del_cultivo",
        "nombre_original": "Ciclo del cultivo",
        "tipo_dato": "str",
        "categoria": "Categorica",
        "rol_analitico": "Feature / Dimension analitica",
        "descripcion": "Indica si el cultivo es transitorio o permanente.",
        "valores": "2 valores: Transitorio, Permanente",
        "fuente_origen": "UPRA - Taxonomia EVA",
        "notas": "Determina estructura temporal. Feature binaria de alto valor.",
    },
    {
        "nombre": "estado_fisico_del_cultivo",
        "nombre_original": "Estado fisico del cultivo",
        "tipo_dato": "str",
        "categoria": "Categorica",
        "rol_analitico": "Feature / Componente de llave primaria",
        "descripcion": "Forma en que se reporta y comercializa la produccion.",
        "valores": "8 valores: En fresco, Grano, Pergamino, etc.",
        "fuente_origen": "UPRA - Metodologia EVA",
        "notas": "Parte de la llave primaria.",
    },
    {
        "nombre": "ano",
        "nombre_original": "Anio",
        "tipo_dato": "Int64",
        "categoria": "Temporal",
        "rol_analitico": "Dimension temporal - anio calendario",
        "descripcion": "Anio de la campana agricola reportada.",
        "valores": "6 valores: 2019, 2020, 2021, 2022, 2023, 2024",
        "fuente_origen": "UPRA - EVA",
        "notas": "Redundante con periodo. Mantener para filtros directos.",
    },
    {
        "nombre": "periodo",
        "nombre_original": "Periodo",
        "tipo_dato": "str",
        "categoria": "Temporal",
        "rol_analitico": "Dimension temporal - semestre / anio",
        "descripcion": "Codigo del periodo de reporte. A=ene-jun, B=jul-dic.",
        "valores": "18 valores. Formato YYYY o YYYYA/YYYYB.",
        "fuente_origen": "UPRA - Metodologia EVA",
        "notas": "Componente de la llave primaria.",
    },
    {
        "nombre": "area_sembrada_ha",
        "nombre_original": "Area sembrada (ha)",
        "tipo_dato": "float64",
        "categoria": "Metrica",
        "rol_analitico": "Feature predictiva / Target secundario",
        "descripcion": "Superficie en hectareas destinada a siembra en el periodo.",
        "valores": "Rango: 0.02 - 33,990 ha. Mediana: 14 ha.",
        "fuente_origen": "Municipios / Secretarias de Agricultura",
        "notas": "Alta correlacion con area_cosechada_ha (r=0.990).",
    },
    {
        "nombre": "area_cosechada_ha",
        "nombre_original": "Area cosechada (ha)",
        "tipo_dato": "float64",
        "categoria": "Metrica",
        "rol_analitico": "Feature predictiva / Target secundario",
        "descripcion": "Superficie efectivamente cosechada en el periodo.",
        "valores": "Rango: 0.02 - 33,900 ha. Mediana: 13 ha.",
        "fuente_origen": "Municipios / Secretarias de Agricultura",
        "notas": "Denominador del rendimiento.",
    },
    {
        "nombre": "produccion_t",
        "nombre_original": "Produccion (t)",
        "tipo_dato": "float64",
        "categoria": "Metrica",
        "rol_analitico": "TARGET PRINCIPAL",
        "descripcion": "Volumen total de produccion en toneladas metricas.",
        "valores": "Rango: 0.07 - 4,776,340 t. Mediana: 112 t.",
        "fuente_origen": "Municipios / Gremios / Fedearroz / SICA / ENAM-DANE",
        "notas": "Distribucion extremadamente sesgada. Transformacion log recomendada.",
    },
    {
        "nombre": "rendimiento_t_ha",
        "nombre_original": "Rendimiento (t/ha)",
        "tipo_dato": "float64",
        "categoria": "Metrica",
        "rol_analitico": "TARGET SECUNDARIO / Feature de eficiencia",
        "descripcion": "Eficiencia productiva: toneladas por hectarea cosechada.",
        "valores": "Rango: 0.09 - 160 t/ha. Mediana: 10 t/ha.",
        "fuente_origen": "Calculado por UPRA: produccion_t / area_cosechada_ha",
        "notas": "No es independiente de produccion_t y area_cosechada_ha.",
    },
]


def get_data_dictionary() -> list[dict[str, str]]:
    """
    Retorna el diccionario de variables como lista de diccionarios.

    Returns:
        Lista de 18 diccionarios, cada uno con la documentacion de una variable.
    """
    return DICCIONARIO


def get_data_dictionary_dataframe() -> pd.DataFrame:
    """
    Retorna el diccionario de variables como DataFrame.

    Returns:
        DataFrame con 18 filas (una por variable) y 9 columnas.
    """
    return pd.DataFrame(DICCIONARIO)
