"""
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
