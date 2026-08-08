"""
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
