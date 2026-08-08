"""
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
