"""
Setup script: genera los 8 archivos del modulo core/modeling/.
Migracion del Notebook 3 (Modelado Conceptual).
Ejecutar una sola vez: python scripts/setup_modeling_module.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: core/modeling/data_dictionary.py
# ═══════════════════════════════════════════════════════════
DATA_DICTIONARY = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: core/modeling/classifications.py
# ═══════════════════════════════════════════════════════════
CLASSIFICATIONS = '''"""
Clasificacion de variables por rol analitico.

Define el rol de cada variable en el analisis:
LLAVE, DIMENSION, METRICA, FEATURE, CONTEXTO.
"""
from __future__ import annotations

import pandas as pd

# Clasificacion por rol analitico
CLASIFICACION: dict[str, list[tuple[str, str]]] = {
    "LLAVE - Identifican univocamente cada registro": [
        ("id_registro", "Surrogate generado: cod_municipio + cultivo + periodo + estado + ciclo"),
        ("codigo_dane_municipio", "Codigo DANE 5 digitos - componente de llave natural"),
        ("desagregacion_cultivo", "Nivel mas fino de cultivo - componente de llave natural"),
        ("periodo", "Codigo de periodo YYYY/YYYYA/YYYYB - componente de llave"),
        ("estado_fisico_del_cultivo", "Forma de reporte de produccion - componente de llave"),
        ("ciclo_del_cultivo", "Transitorio/Permanente - componente de llave natural"),
    ],
    "DIMENSION - Segmentan y agrupan el analisis": [
        ("departamento", "Constante (Valle del Cauca) - solo para contexto"),
        ("municipio", "Nombre legible del municipio"),
        ("codigo_dane_departamento", "Constante (76) - util para joins externos"),
        ("grupo_cultivo", "Nivel 1 jerarquia cultivo - 8 categorias"),
        ("subgrupo", "Nivel 2 jerarquia cultivo - 23 categorias"),
        ("cultivo", "Nivel 3 jerarquia cultivo - 78 cultivos"),
        ("ano", "Anio calendario - para tendencias"),
    ],
    "METRICA - Variables cuantitativas medidas": [
        ("area_sembrada_ha", "Esfuerzo productivo (ha). Correlacion r=0.990 con cosechada"),
        ("area_cosechada_ha", "Resultado de cosecha (ha). Denominador del rendimiento"),
        ("produccion_t", "TARGET PRINCIPAL. Volumen total (t). Sesgado a derecha"),
        ("rendimiento_t_ha", "TARGET SECUNDARIO. Eficiencia (t/ha). Variable derivada"),
    ],
    "FEATURE - Predictores para modelos ML": [
        ("ciclo_del_cultivo", "Binaria. Determina estacionalidad del cultivo"),
        ("grupo_cultivo", "Categorica (8). Captura perfil productivo"),
        ("subgrupo", "Categorica (23). Mas especifica que grupo"),
        ("municipio", "Categorica (42). Captura condiciones agroecologicas locales"),
        ("ano", "Numerica ordinal. Captura tendencia historica"),
        ("periodo", "Categorica. Captura estacionalidad semestral"),
        ("area_sembrada_ha", "Numerica. Mejor predictor de produccion (r=0.953)"),
        ("area_cosechada_ha", "Numerica. Predictor directo de produccion (r=0.968)"),
        ("estado_fisico_del_cultivo", "Categorica (8). Ajusta escala de tonelaje reportado"),
    ],
    "CONTEXTO - Enriquecimiento informativo": [
        ("nombre_cientifico_del_cultivo", "Alta cardinalidad. Util para join con bases botanicas"),
        ("codigo_del_cultivo", "Clave de join con catalogo UPRA"),
    ],
}


def get_classifications() -> dict[str, list[tuple[str, str]]]:
    """
    Retorna la clasificacion de variables por rol analitico.

    Returns:
        Diccionario donde cada clave es una categoria de rol y el valor
        es una lista de tuplas (nombre_variable, descripcion).
    """
    return CLASIFICACION


def get_classifications_dataframe() -> pd.DataFrame:
    """
    Retorna la clasificacion como DataFrame plano.

    Returns:
        DataFrame con columnas: categoria_rol, variable, descripcion.
    """
    filas = []
    for categoria, variables in CLASIFICACION.items():
        for nombre, desc in variables:
            filas.append({
                "categoria_rol": categoria,
                "variable": nombre,
                "descripcion": desc,
            })
    return pd.DataFrame(filas)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: core/modeling/conceptual_map.py
# ═══════════════════════════════════════════════════════════
CONCEPTUAL_MAP = '''"""
Mapa conceptual estructurado del dataset EVA Valle del Cauca.

Define la entidad central, dimensiones, reglas de negocio,
correlaciones y esquema estrella.
"""
from __future__ import annotations

from typing import Any

# Mapa conceptual completo
MAPA_CONCEPTUAL: dict[str, Any] = {
    "titulo": "MAPA CONCEPTUAL LOGICO - EVA AGRICOLA VALLE DEL CAUCA",
    "fuente": "UPRA",
    "periodo": "2019-2024",
    "alcance": "42 municipios",
    "entidad_central": {
        "nombre": "REGISTRO EVA",
        "pregunta_que_responde": (
            "Cuanto se sembro, cosecho y produjo un cultivo especifico, "
            "en un municipio y periodo determinados?"
        ),
        "llave_primaria_surrogate": (
            "municipio + cultivo_desagregado + periodo + estado_fisico + ciclo"
        ),
        "metricas": [
            {"campo": "area_sembrada_ha", "rol": "INPUT", "descripcion": "esfuerzo productivo"},
            {"campo": "area_cosechada_ha", "rol": "resultado", "descripcion": "resultado de cosecha"},
            {"campo": "produccion_t", "rol": "TARGET PRINCIPAL", "descripcion": "volumen en toneladas"},
            {
                "campo": "rendimiento_t_ha",
                "rol": "TARGET SECUNDARIO",
                "descripcion": "eficiencia t/ha (derivada: produccion / area_cosechada)",
            },
        ],
    },
    "dimensiones": {
        "lugar": {
            "descripcion": "Pais > Departamento (76=Valle) > Municipio (42)",
            "llave": "codigo_dane_municipio",
            "niveles": ["departamento", "municipio"],
        },
        "cultivo": {
            "descripcion": "Grupo (8) > Subgrupo (23) > Cultivo (78) > Desagregacion (97)",
            "llave": "desagregacion_cultivo",
            "niveles": ["grupo_cultivo", "subgrupo", "cultivo", "desagregacion_cultivo"],
        },
        "tiempo": {
            "descripcion": "Anio (6) > Periodo (18: YYYY / YYYYA / YYYYB)",
            "llave": "periodo",
            "niveles": ["ano", "periodo"],
        },
        "producto": {
            "descripcion": "Estado fisico del cultivo (8 formas de reporte)",
            "llave": "estado_fisico_del_cultivo",
            "niveles": ["estado_fisico_del_cultivo"],
        },
    },
    "reglas_de_negocio": [
        {
            "codigo": "R1",
            "regla": "area_cosechada_ha <= area_sembrada_ha",
            "excepcion": "Permanentes con cosecha diferida entre periodos",
        },
        {
            "codigo": "R2",
            "regla": "produccion_t > 0 => area_cosechada_ha > 0",
            "excepcion": "Ninguna",
        },
        {
            "codigo": "R3",
            "regla": "area_cosechada_ha > 0 => rendimiento_t_ha > 0",
            "excepcion": "Ninguna",
        },
        {
            "codigo": "R4",
            "regla": "rendimiento_t_ha = produccion_t / area_cosechada_ha",
            "excepcion": "Tolerancia ~1% por redondeos de fuente",
        },
        {
            "codigo": "R5",
            "regla": "ciclo_del_cultivo en {Transitorio, Permanente}",
            "excepcion": "Ninguna",
        },
        {
            "codigo": "R6",
            "regla": "Permanentes -> periodo YYYY; Transitorios -> YYYYA/YYYYB",
            "excepcion": "Algunos transitorios con periodo sin semestre (anomalia UPRA)",
        },
    ],
    "correlaciones": [
        {"var1": "area_sembrada_ha", "var2": "area_cosechada_ha", "r": 0.990},
        {"var1": "area_cosechada_ha", "var2": "produccion_t", "r": 0.968},
        {"var1": "area_sembrada_ha", "var2": "produccion_t", "r": 0.953},
        {"var1": "rendimiento_t_ha", "var2": "areas", "r": 0.45, "nota": "variable mas independiente"},
    ],
    "esquema_estrella": {
        "hechos": {
            "tabla": "fact_eva_agricola",
            "pk": "id_registro",
            "foreign_keys": [
                "fk_municipio -> dim_municipio.codigo_dane_municipio",
                "fk_cultivo -> dim_cultivo.desagregacion_cultivo",
                "fk_tiempo -> dim_tiempo.periodo",
                "fk_producto -> dim_producto.estado_fisico_del_cultivo",
            ],
            "medidas": [
                "area_sembrada_ha", "area_cosechada_ha",
                "produccion_t", "rendimiento_t_ha",
            ],
        },
        "dimensiones": {
            "dim_municipio": [
                "codigo_dane_municipio (PK)", "municipio",
                "departamento", "codigo_dane_departamento",
            ],
            "dim_cultivo": [
                "desagregacion_cultivo (PK)", "cultivo", "subgrupo",
                "grupo_cultivo", "ciclo_del_cultivo",
                "nombre_cientifico_del_cultivo", "codigo_del_cultivo",
            ],
            "dim_tiempo": [
                "periodo (PK)", "ano", "semestre (A/B/Anual)",
                "tipo_periodo (Transitorio/Permanente)",
            ],
            "dim_producto": ["estado_fisico_del_cultivo (PK)"],
        },
    },
}


def get_conceptual_map() -> dict[str, Any]:
    """
    Retorna el mapa conceptual completo.

    Returns:
        Diccionario con la estructura completa del modelo conceptual.
    """
    return MAPA_CONCEPTUAL
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: core/modeling/surrogate_key.py
# ═══════════════════════════════════════════════════════════
SURROGATE_KEY = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: core/modeling/hierarchies.py
# ═══════════════════════════════════════════════════════════
HIERARCHIES = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: core/modeling/type_reconversion.py
# ═══════════════════════════════════════════════════════════
TYPE_RECONVERSION = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: core/modeling/pipeline.py
# ═══════════════════════════════════════════════════════════
PIPELINE = '''"""
Orquestador del Paso 3: Modelado Conceptual.

Migrado del Notebook 3 (funcion ejecutar_paso3).
Mejoras:
- Sin prints (solo logging)
- Configuracion desde config.settings
- Usa adaptadores de storage (CsvStorage, JsonStorage)
- Retorna el DataFrame y los artefactos generados
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from adapters.storage.json_storage import JsonStorage
from config.settings import settings
from core.audit.models import AuditFinding
from core.logging import get_logger, log_section
from core.modeling.classifications import get_classifications, get_classifications_dataframe
from core.modeling.conceptual_map import get_conceptual_map
from core.modeling.data_dictionary import get_data_dictionary, get_data_dictionary_dataframe
from core.modeling.hierarchies import (
    generate_crop_hierarchy,
    generate_temporal_hierarchy,
    generate_territorial_hierarchy,
)
from core.modeling.surrogate_key import (
    NATURAL_KEY_COLUMNS,
    generate_surrogate_key,
    validate_natural_key,
)
from core.modeling.type_reconversion import reconvert_types

log = get_logger("core.modeling.pipeline")

_csv_storage = CsvStorage()
_json_storage = JsonStorage()


def run_conceptual_modeling(
    input_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Ejecuta el pipeline completo de modelado conceptual (Paso 3).

    Args:
        input_path: Ruta al CSV estandarizado. Si es None, usa la ruta por defecto.

    Returns:
        Tupla (DataFrame con id_registro, dict de artefactos generados).

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
        KeyError: Si el archivo no tiene las columnas esperadas.
    """
    log_section("PASO 3 - MODELADO CONCEPTUAL")

    if input_path is None:
        input_path = (
            settings.DATA_PROCESSED_PATH / "01_clean" /
            "eva_agricola_valle_2019_2024_estandarizado.csv"
        )

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d filas x %d columnas", df.shape[0], df.shape[1])

    # Validar columnas puntero
    columnas_puntero = ["desagregacion_cultivo", "periodo", "codigo_dane_municipio"]
    faltantes = [c for c in columnas_puntero if c not in df.columns]
    if faltantes:
        raise KeyError(
            f"El archivo NO es la base agricola esperada. "
            f"Faltan: {faltantes}. Columnas: {list(df.columns)}"
        )

    # Validar alcance
    n = len(df)
    if n > 50_000:
        log.warning(
            "Dataset tiene %d registros. Se esperaban ~9,032. "
            "Posiblemente cargo el archivo nacional.", n,
        )
    elif n < 5_000:
        log.warning(
            "Dataset tiene solo %d registros. Se esperaban ~9,032. "
            "Posiblemente archivo truncado.", n,
        )
    else:
        log.info("Tamano del dataset (%d registros) dentro del rango esperado.", n)

    # Reconvertis tipos
    df = reconvert_types(df)

    # Generar ID surrogate
    df["id_registro"] = generate_surrogate_key(df)

    # Validar llave natural
    es_valida, duplicados = validate_natural_key(df)
    if not es_valida:
        log.warning("Llave natural con %d duplicados. Continuar con precaucion.", duplicados)

    # Verificar unicidad del surrogate
    ids_unicos = df["id_registro"].nunique()
    if ids_unicos < len(df):
        log.warning("Surrogate con %d colisiones.", len(df) - ids_unicos)
    else:
        log.info("ID surrogate unico: %d de %d", ids_unicos, len(df))

    # Generar jerarquias
    hier_muni = generate_territorial_hierarchy(df)
    hier_cultivo = generate_crop_hierarchy(df)
    hier_temporal = generate_temporal_hierarchy(df)

    # Artefactos
    timestamp = datetime.now().isoformat()
    artefactos: dict[str, Any] = {
        "timestamp": timestamp,
        "n_registros": len(df),
        "diccionario": get_data_dictionary_dataframe(),
        "clasificacion": get_classifications_dataframe(),
        "jerarquia_municipios": hier_muni,
        "jerarquia_cultivos": hier_cultivo,
        "jerarquia_temporal": hier_temporal,
    }

    log.info("Paso 3 completado: %d artefactos generados.", len(artefactos))
    return df, artefactos
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 8: core/modeling/__init__.py (FACHADA)
# ═══════════════════════════════════════════════════════════
MODELING_INIT = '''"""
Modulo de modelado conceptual del proyecto eva-valle-v3.0.

Fachada que expone las funciones principales del Paso 3.

Uso:
    from core.modeling import run_conceptual_modeling, get_data_dictionary

    # Ejecutar el pipeline completo
    df_modelo, artefactos = run_conceptual_modeling()

    # Acceder al diccionario de variables
    diccionario = get_data_dictionary()
"""
from core.modeling.pipeline import run_conceptual_modeling
from core.modeling.data_dictionary import (
    DICCIONARIO,
    get_data_dictionary,
    get_data_dictionary_dataframe,
)
from core.modeling.classifications import (
    CLASIFICACION,
    get_classifications,
    get_classifications_dataframe,
)
from core.modeling.conceptual_map import (
    MAPA_CONCEPTUAL,
    get_conceptual_map,
)
from core.modeling.surrogate_key import (
    NATURAL_KEY_COLUMNS,
    generate_surrogate_key,
    validate_natural_key,
)
from core.modeling.hierarchies import (
    generate_territorial_hierarchy,
    generate_crop_hierarchy,
    generate_temporal_hierarchy,
)
from core.modeling.type_reconversion import reconvert_types

__all__ = [
    "run_conceptual_modeling",
    "DICCIONARIO",
    "get_data_dictionary",
    "get_data_dictionary_dataframe",
    "CLASIFICACION",
    "get_classifications",
    "get_classifications_dataframe",
    "MAPA_CONCEPTUAL",
    "get_conceptual_map",
    "NATURAL_KEY_COLUMNS",
    "generate_surrogate_key",
    "validate_natural_key",
    "generate_territorial_hierarchy",
    "generate_crop_hierarchy",
    "generate_temporal_hierarchy",
    "reconvert_types",
]
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "core/modeling/data_dictionary.py": DATA_DICTIONARY,
        "core/modeling/classifications.py": CLASSIFICATIONS,
        "core/modeling/conceptual_map.py": CONCEPTUAL_MAP,
        "core/modeling/surrogate_key.py": SURROGATE_KEY,
        "core/modeling/hierarchies.py": HIERARCHIES,
        "core/modeling/type_reconversion.py": TYPE_RECONVERSION,
        "core/modeling/pipeline.py": PIPELINE,
        "core/modeling/__init__.py": MODELING_INIT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} archivos del modulo de modelado conceptual creados.")
    print('Ejecuta: python -c "from core.modeling import run_conceptual_modeling; print(\'OK\')"')