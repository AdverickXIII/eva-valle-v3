"""
Orquestador del Paso 1: Carga y Estandarizacion.

Migrado del Notebook 2 (funcion ejecutar_paso1).
Mejoras:
- Sin prints (solo logging)
- Configuracion desde config.settings
- Usa adaptadores de storage (ExcelStorage, CsvStorage)
- Retorna el DataFrame y el mapeo de columnas
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from adapters.storage.excel_storage import ExcelStorage
from config.constants import (
    CODIGO_DANE_VALLE,
    HEADER_ROW_AGRICOLA,
    NOMBRE_DEPTO_VALLE,
    SHEET_NAME_AGRICOLA,
)
from config.settings import settings
from core.audit.normalization import normalize_column_name, normalize_territorial_name
from core.audit.territorial_filter import filter_by_department
from core.audit.type_conversion import convert_to_numeric
from core.logging import get_logger

log = get_logger("core.audit.loader")

_excel_storage = ExcelStorage()
_csv_storage = CsvStorage()


def load_and_standardize(
    input_path: Path | None = None,
    sheet_name: str = SHEET_NAME_AGRICOLA,
    expected_header_row: int = HEADER_ROW_AGRICOLA,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Ejecuta el pipeline completo de carga y estandarizacion (Paso 1).

    Args:
        input_path: Ruta al archivo Excel. Si es None, usa la ruta por defecto.
        sheet_name: Nombre de la hoja a leer.
        expected_header_row: Fila esperada del header (base 0).

    Returns:
        Tupla (DataFrame estandarizado del Valle, dict de mapeo columnas).

    Raises:
        DatasetNotFoundError: Si el archivo no existe.
        ValueError: Si la hoja no existe o el header no se encuentra.
    """
    if input_path is None:
        input_path = settings.DATA_RAW_PATH / "base_agricola_2024.xlsx"

    log.info("Iniciando Paso 1: Carga y Estandarizacion")
    log.info("Archivo entrada: %s", input_path)

    # Verificar hojas disponibles
    hojas = _excel_storage.get_sheet_names(input_path)
    log.info("Hojas disponibles: %s", hojas)
    if sheet_name not in hojas:
        raise ValueError(f"Hoja '{sheet_name}' no encontrada. Disponibles: {hojas}")

    # Detectar header
    header_detectado = _excel_storage.detect_header_row(input_path, sheet_name)
    if header_detectado != expected_header_row:
        log.warning(
            "Header esperado en fila %d, detectado en %d. Usando valor detectado.",
            expected_header_row, header_detectado,
        )

    # Carga
    df_raw = _excel_storage.read_excel(input_path, sheet_name, header_detectado)
    df_raw_backup = df_raw.copy(deep=True)
    df_trabajo = df_raw.copy(deep=True)

    # Estandarizar columnas
    cols_orig = df_trabajo.columns.tolist()
    cols_std = [normalize_column_name(c) for c in cols_orig]

    colisiones = [k for k, v in Counter(cols_std).items() if v > 1]
    if colisiones:
        log.warning("Colision de nombres: %s", colisiones)
    else:
        log.info("Sin colisiones en nombres estandarizados.")

    df_trabajo.columns = cols_std

    # Mapeo para retornar
    mapeo = dict(zip(cols_orig, cols_std))

    # Conversion de tipos
    anomalias_total: list[str] = []
    cols_int = [
        "codigo_dane_departamento", "codigo_dane_municipio",
        "ano", "codigo_del_cultivo",
    ]
    for col in cols_int:
        if col in df_trabajo.columns:
            df_trabajo, anom = convert_to_numeric(df_trabajo, col, "int")
            anomalias_total.extend(anom)

    cols_float = [
        "area_sembrada_ha", "area_cosechada_ha",
        "produccion_t", "rendimiento_t_ha",
    ]
    for col in cols_float:
        if col in df_trabajo.columns:
            df_trabajo, anom = convert_to_numeric(df_trabajo, col, "float")
            anomalias_total.extend(anom)

    # Columnas string: limpiar sin convertir NaN a "nan"
    cols_str = [
        "departamento", "municipio", "desagregacion_cultivo", "cultivo",
        "ciclo_del_cultivo", "grupo_cultivo", "subgrupo", "periodo",
        "nombre_cientifico_del_cultivo", "estado_fisico_del_cultivo",
    ]
    for col in cols_str:
        if col in df_trabajo.columns:
            df_trabajo[col] = (
                df_trabajo[col]
                .astype(str)
                .str.strip()
                .replace("nan", np.nan)
            )

    # Normalizacion territorial
    df_trabajo["departamento"] = normalize_territorial_name(df_trabajo["departamento"])
    df_trabajo["municipio"] = normalize_territorial_name(df_trabajo["municipio"])

    nombre_valle = df_trabajo.loc[
        df_trabajo["codigo_dane_departamento"] == CODIGO_DANE_VALLE,
        "departamento",
    ].unique()
    log.info("Nombre Valle en datos tras normalizacion: %s", nombre_valle)

    # Filtrar Valle del Cauca
    df_valle = filter_by_department(df_trabajo)

    # Guardar dataset limpio
    ruta_salida = settings.DATA_PROCESSED_PATH / "01_clean" / "eva_agricola_valle_2019_2024_estandarizado.csv"
    _csv_storage.write_csv(df_valle, ruta_salida)

    # Reporte
    n_total = len(df_raw_backup)
    n_valle = len(df_valle)
    pct = (n_valle / n_total) * 100 if n_total > 0 else 0
    log.info(
        "Paso 1 completado: %d registros originales, %d Valle del Cauca (%.2f%%).",
        n_total, n_valle, pct,
    )

    return df_valle, mapeo
