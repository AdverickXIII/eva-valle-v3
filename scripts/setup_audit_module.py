"""
Setup script: genera los 14 archivos del modulo core/audit/.
Migracion del Notebook 2 (Carga y Estandarizacion + Auditoria).
Ejecutar una sola vez: python scripts/setup_audit_module.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: core/audit/models.py
# ═══════════════════════════════════════════════════════════
MODELS = '''"""
Modelos de datos para el modulo de auditoria.

Reemplaza la lista global mutable `hallazgos_auditoria` del Notebook 2
con un dataclass inmutable y funciones puras.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AuditFinding:
    """
    Hallazgo individual de auditoria.

    Attributes:
        codigo: Identificador unico (ej: 'AUD-001', 'AUD-LOG-002').
        severidad: Nivel del hallazgo: 'INFO', 'ADVERTENCIA' o 'ERROR'.
        descripcion: Descripcion concisa del hallazgo.
        detalle: Informacion adicional opcional.
        timestamp: Momento en que se registro el hallazgo.
    """

    codigo: str
    severidad: str
    descripcion: str
    detalle: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, str]:
        """Convierte el hallazgo a diccionario para exportar a CSV."""
        return {
            "codigo": self.codigo,
            "severidad": self.severidad,
            "descripcion": self.descripcion,
            "detalle": self.detalle,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        icon = {"INFO": "i", "ADVERTENCIA": "!", "ERROR": "X"}.get(self.severidad, "*")
        return f"[{self.codigo}] {icon} {self.severidad}: {self.descripcion}"
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: core/audit/normalization.py
# ═══════════════════════════════════════════════════════════
NORMALIZATION = '''"""
Funciones de normalizacion de nombres para el pipeline de carga.

Migrado del Notebook 2 (Paso 1). Funciones puras sin efectos secundarios.
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from core.logging import get_logger

log = get_logger("core.audit.normalization")


def normalize_column_name(name: str) -> str:
    """
    Normaliza un nombre de columna a snake_case sin tildes.

    Pipeline: strip -> NFD (eliminar diacriticos) -> lower ->
              reemplazar no-alfanumericos por _ -> colapsar _ -> trim.

    Args:
        name: Nombre original de la columna.

    Returns:
        Nombre normalizado en snake_case.

    Ejemplo:
        >>> normalize_column_name("Area sembrada (ha)")
        'area_sembrada_ha'
        >>> normalize_column_name("Codigo Dane departamento")
        'codigo_dane_departamento'
    """
    s = str(name).strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[\\s/()\\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def normalize_territorial_name(series: pd.Series) -> pd.Series:
    """
    Limpia y estandariza nombres territoriales preservando tildes.

    Aplica title() y luego corrige particulas ("Del" -> "del", etc.)
    que title() capitaliza incorrectamente.

    Args:
        series: Serie con nombres territoriales.

    Returns:
        Serie normalizada con title case corregido.

    Ejemplo:
        >>> normalize_territorial_name(pd.Series(["SANTIAGO DE CALI"]))
        0    Santiago de Cali
    """
    result = (
        series
        .astype(str)
        .str.strip()
        .str.replace(r"\\s+", " ", regex=True)
        .str.title()
    )
    particulas = {
        " Del ": " del ",
        " De ": " de ",
        " La ": " la ",
        " Las ": " las ",
        " Los ": " los ",
        " El ": " el ",
        " Y ": " y ",
    }
    for incorrecta, correcta in particulas.items():
        result = result.str.replace(incorrecta, correcta, regex=False)
    return result
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: core/audit/type_conversion.py
# ═══════════════════════════════════════════════════════════
TYPE_CONVERSION = '''"""
Funciones de conversion de tipos para el pipeline de carga.

Migrado del Notebook 2 (Paso 1).
Mejora: la funcion original modificaba in-place; esta version retorna
una copia del DataFrame (funcion pura).
"""
from __future__ import annotations

import pandas as pd

from core.logging import get_logger

log = get_logger("core.audit.type_conversion")


def convert_to_numeric(
    df: pd.DataFrame,
    column: str,
    dtype: str,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Convierte una columna a tipo numerico. NO modifica el original in-place.

    Args:
        df: DataFrame de trabajo (no se modifica).
        column: Nombre de columna a convertir.
        dtype: Tipo destino: 'int' (Int64 nullable) o 'float' (float64).

    Returns:
        Tupla (DataFrame con columna convertida, lista de mensajes de anomalia).

    Ejemplo:
        >>> df_new, anomalies = convert_to_numeric(df, "ano", "int")
    """
    df = df.copy()
    original = df[column].copy()
    df[column] = pd.to_numeric(df[column], errors="coerce")

    anomalies: list[str] = []
    n_coerced = df[column].isna().sum() - original.isna().sum()
    if n_coerced > 0:
        vals = original[df[column].isna() & original.notna()].unique()[:5]
        msg = (
            f"Col '{column}': {n_coerced} valor(es) no convertible(s) a NaN. "
            f"Ejemplos: {list(vals)}"
        )
        anomalies.append(msg)
        log.warning(msg)

    if dtype == "int" and df[column].notna().all():
        df[column] = df[column].astype("Int64")
    elif dtype == "float":
        df[column] = df[column].astype("float64")

    return df, anomalies
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: core/audit/territorial_filter.py
# ═══════════════════════════════════════════════════════════
TERRITORIAL_FILTER = '''"""
Filtrado territorial del dataset nacional al departamento objetivo.

Migrado del Notebook 2 (Paso 1).
Mejora: la configuracion (codigo DANE, nombre) se lee de config.constants.
"""
from __future__ import annotations

import pandas as pd

from config.constants import CODIGO_DANE_VALLE, NOMBRE_DEPTO_VALLE
from core.logging import get_logger

log = get_logger("core.audit.territorial_filter")


def filter_by_department(
    df: pd.DataFrame,
    codigo_dane: int = CODIGO_DANE_VALLE,
    nombre_depto: str = NOMBRE_DEPTO_VALLE,
) -> pd.DataFrame:
    """
    Filtra por codigo DANE (primario) con verificacion cruzada por nombre.

    Args:
        df: DataFrame nacional completo.
        codigo_dane: Codigo DANE del departamento objetivo (default 76).
        nombre_depto: Nombre del departamento para verificacion cruzada.

    Returns:
        DataFrame filtrado con indice reseteado.
    """
    mask_codigo = df["codigo_dane_departamento"] == codigo_dane
    mask_nombre = df["departamento"].str.lower() == nombre_depto.lower()

    solo_codigo = mask_codigo & ~mask_nombre
    solo_nombre = ~mask_codigo & mask_nombre

    if solo_codigo.sum() > 0:
        log.warning(
            "%d registros con codigo %d pero nombre != '%s'.",
            solo_codigo.sum(), codigo_dane, nombre_depto,
        )
    if solo_nombre.sum() > 0:
        log.warning(
            "%d registros con nombre '%s' pero codigo != %d.",
            solo_nombre.sum(), nombre_depto, codigo_dane,
        )

    df_filtrado = df[mask_codigo].copy().reset_index(drop=True)
    log.info("Filtro aplicado (DANE=%d): %d registros.", codigo_dane, len(df_filtrado))
    return df_filtrado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: core/audit/loader.py
# ═══════════════════════════════════════════════════════════
LOADER = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: core/audit/structure.py
# ═══════════════════════════════════════════════════════════
STRUCTURE = '''"""
Auditoria 2.1: Estructura del dataset.
Verifica dimensiones, columnas esperadas, tipos y memoria.
"""
from __future__ import annotations

import pandas as pd

from config.constants import COLUMNAS_ESPERADAS
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.structure")


def audit_structure(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.1: verifica columnas esperadas y dimensiones.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    n_rows, n_cols = df.shape
    mem_mb = df.memory_usage(deep=True).sum() / 1_048_576
    log.info(
        "Auditoria 2.1: %d filas x %d columnas, %.2f MB",
        n_rows, n_cols, mem_mb,
    )

    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    extras = [c for c in df.columns if c not in COLUMNAS_ESPERADAS]

    if faltantes:
        findings.append(AuditFinding(
            codigo="AUD-001",
            severidad="ERROR",
            descripcion=f"Columnas faltantes: {faltantes}",
            detalle="Cambio de estructura en la fuente",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-001",
            severidad="INFO",
            descripcion="Todas las columnas esperadas presentes",
            detalle=f"Total: {len(COLUMNAS_ESPERADAS)}",
        ))

    if extras:
        findings.append(AuditFinding(
            codigo="AUD-002",
            severidad="ADVERTENCIA",
            descripcion=f"Columnas inesperadas: {extras}",
            detalle="Verificar si son nuevas variables",
        ))

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: core/audit/nulls.py
# ═══════════════════════════════════════════════════════════
NULLS = '''"""
Auditoria 2.2: Nulos y cobertura.
Verifica la presencia de valores nulos por columna.
"""
from __future__ import annotations

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.nulls")


def audit_nulls(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.2: cobertura de nulos por columna.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []
    n = len(df)
    cols_con_nulos: list[tuple[str, int, float]] = []

    for col in df.columns:
        nul = int(df[col].isna().sum())
        pct = (nul / n) * 100 if n > 0 else 0
        if nul > 0:
            cols_con_nulos.append((col, nul, pct))

    if cols_con_nulos:
        for col, cnt, pct in cols_con_nulos:
            sev = "ADVERTENCIA" if pct < 5 else "ERROR"
            findings.append(AuditFinding(
                codigo=f"AUD-NUL-{col[:8].upper()}",
                severidad=sev,
                descripcion=f"'{col}': {cnt:,} nulos ({pct:.2f}%)",
                detalle="Cero reportado vs dato faltante",
            ))
        log.warning("Se encontraron %d columnas con nulos.", len(cols_con_nulos))
    else:
        findings.append(AuditFinding(
            codigo="AUD-003",
            severidad="INFO",
            descripcion="Sin valores nulos",
            detalle=f"Registros: {n:,}",
        ))
        log.info("Sin valores nulos en %d registros.", n)

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 8: core/audit/duplicates.py
# ═══════════════════════════════════════════════════════════
DUPLICATES = '''"""
Auditoria 2.3: Duplicados.
Verifica duplicados exactos y por clave natural.
"""
from __future__ import annotations

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.duplicates")

# Clave natural: ano + periodo + municipio + cultivo + desagregacion
CLAVE_NATURAL = [
    "ano", "periodo", "codigo_dane_municipio",
    "cultivo", "desagregacion_cultivo",
]


def audit_duplicates(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.3: duplicados exactos y por clave natural.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    # Duplicados exactos (todas las columnas)
    n_dup_exactos = int(df.duplicated().sum())
    if n_dup_exactos > 0:
        findings.append(AuditFinding(
            codigo="AUD-DUP-001",
            severidad="ERROR",
            descripcion=f"{n_dup_exactos:,} registros duplicados exactos",
            detalle="Eliminar con drop_duplicates()",
        ))
    else:
        log.info("Sin duplicados exactos.")

    # Duplicados por clave natural
    clave_existente = [c for c in CLAVE_NATURAL if c in df.columns]
    if len(clave_existente) == len(CLAVE_NATURAL):
        n_dup_clave = int(df.duplicated(subset=CLAVE_NATURAL).sum())
        if n_dup_clave > 0:
            findings.append(AuditFinding(
                codigo="AUD-DUP-002",
                severidad="ADVERTENCIA",
                descripcion=f"{n_dup_clave:,} registros con clave natural duplicada",
                detalle="Mismo cultivo/municipio/ano/periodo con datos distintos",
            ))
        else:
            findings.append(AuditFinding(
                codigo="AUD-DUP-002",
                severidad="INFO",
                descripcion="Sin duplicados por clave natural",
            ))
    else:
        log.warning("No se pudieron verificar duplicados por clave: faltan columnas.")

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 9: core/audit/territory.py
# ═══════════════════════════════════════════════════════════
TERRITORY = '''"""
Auditoria 2.4: Integridad territorial.
Verifica coherencia de codigos y nombres territoriales.
"""
from __future__ import annotations

import pandas as pd

from config.constants import CODIGO_DANE_VALLE, NOMBRE_DEPTO_VALLE
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.territory")


def audit_territory(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.4: coherencia codigos/nombres territoriales.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    # Codigo DANE unico
    codigos_distintos = df["codigo_dane_departamento"].unique()
    if len(codigos_distintos) == 1 and codigos_distintos[0] == CODIGO_DANE_VALLE:
        findings.append(AuditFinding(
            codigo="AUD-TER-001",
            severidad="INFO",
            descripcion="Todos los registros tienen codigo DANE 76",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TER-001",
            severidad="ERROR",
            descripcion=f"Codigos inesperados: {list(codigos_distintos)}",
        ))

    # Nombre de departamento unico
    nombres_depto = df["departamento"].dropna().unique()
    if len(nombres_depto) == 1 and nombres_depto[0] == NOMBRE_DEPTO_VALLE:
        findings.append(AuditFinding(
            codigo="AUD-TER-002",
            severidad="INFO",
            descripcion=f"Nombre de departamento unico y correcto: '{NOMBRE_DEPTO_VALLE}'",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TER-002",
            severidad="ADVERTENCIA",
            descripcion=f"Nombres de depto inesperados: {list(nombres_depto)}",
        ))

    # Municipios: codigo -> nombre (1:1)
    n_municipios = df["codigo_dane_municipio"].nunique()
    muni_nombre = df.groupby("codigo_dane_municipio")["municipio"].nunique()
    muni_inconsistentes = muni_nombre[muni_nombre > 1]

    if len(muni_inconsistentes) > 0:
        ej_codigos = muni_inconsistentes.index[:3].tolist()
        findings.append(AuditFinding(
            codigo="AUD-TER-003",
            severidad="ADVERTENCIA",
            descripcion=f"{len(muni_inconsistentes)} municipio(s) con mas de un nombre",
            detalle=f"Ej: codigos {ej_codigos}",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TER-003",
            severidad="INFO",
            descripcion="Relacion codigo-nombre municipio 1:1 consistente",
            detalle=f"{n_municipios} municipios unicos",
        ))

    # Nombre -> multiples codigos
    nombre_cod = df.groupby("municipio")["codigo_dane_municipio"].nunique()
    nombre_inconsistentes = nombre_cod[nombre_cod > 1]
    if len(nombre_inconsistentes) > 0:
        ej_nombres = nombre_inconsistentes.index[:3].tolist()
        findings.append(AuditFinding(
            codigo="AUD-TER-004",
            severidad="ADVERTENCIA",
            descripcion=f"{len(nombre_inconsistentes)} nombre(s) con multiples codigos DANE",
            detalle=f"Ej: {ej_nombres}",
        ))

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 10: core/audit/temporal.py
# ═══════════════════════════════════════════════════════════
TEMPORAL = '''"""
Auditoria 2.5: Coherencia temporal.
Verifica anos, periodos y su coherencia cruzada.
"""
from __future__ import annotations

import re

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.temporal")

_ANOS_ESPERADOS = set(range(2019, 2025))
_PATRON_PERIODO = re.compile(r"^\\d{4}[AB]$")


def audit_temporal(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.5: anos, periodos, coherencia cruzada.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    anos_unicos = sorted(df["ano"].dropna().unique())
    ano_min, ano_max = int(df["ano"].min()), int(df["ano"].max())

    if ano_min >= 2019 and ano_max <= 2024:
        findings.append(AuditFinding(
            codigo="AUD-TEM-001",
            severidad="INFO",
            descripcion=f"Rango de anos dentro de lo esperado: {ano_min}-{ano_max}",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TEM-001",
            severidad="ADVERTENCIA",
            descripcion=f"Rango de anos inesperado: {ano_min}-{ano_max}",
            detalle="Esperado: 2019-2024",
        ))

    # Anos faltantes
    anos_presentes = set(int(a) for a in anos_unicos if pd.notna(a))
    anos_faltantes = _ANOS_ESPERADOS - anos_presentes
    if anos_faltantes:
        findings.append(AuditFinding(
            codigo="AUD-TEM-002",
            severidad="ADVERTENCIA",
            descripcion=f"Anos faltantes en el dataset: {sorted(anos_faltantes)}",
        ))

    # Formato de periodos
    periodos_unicos = sorted(df["periodo"].dropna().unique())
    periodos_mal = [p for p in periodos_unicos if not _PATRON_PERIODO.match(str(p))]
    if periodos_mal:
        findings.append(AuditFinding(
            codigo="AUD-TEM-003",
            severidad="ADVERTENCIA",
            descripcion=f"Periodos con formato inesperado: {periodos_mal}",
            detalle="Formato esperado: YYYY[A|B] (ej: 2023A, 2023B)",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TEM-003",
            severidad="INFO",
            descripcion="Todos los periodos tienen formato YYYY[A|B] correcto",
        ))

    # Coherencia ano-periodo
    if "ano" in df.columns and "periodo" in df.columns:
        df_temp = df.dropna(subset=["ano", "periodo"]).copy()
        df_temp["ano_periodo"] = df_temp["periodo"].str[:4].astype(int)
        discrepancias = df_temp[df_temp["ano"] != df_temp["ano_periodo"]]
        n_disc = len(discrepancias)
        if n_disc > 0:
            findings.append(AuditFinding(
                codigo="AUD-TEM-004",
                severidad="ERROR",
                descripcion=f"{n_disc:,} registros con ano != ano del periodo",
                detalle=f"Ej: ano={discrepancias['ano'].iloc[0]}, periodo={discrepancias['periodo'].iloc[0]}",
            ))

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 11: core/audit/ranges.py
# ═══════════════════════════════════════════════════════════
RANGES = '''"""
Auditoria 2.6: Rangos numericos y anomalias.
Verifica rangos validos y detecta outliers por IQR.
"""
from __future__ import annotations

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.ranges")

_METRICAS = {
    "area_sembrada_ha": "Area sembrada (ha)",
    "area_cosechada_ha": "Area cosechada (ha)",
    "produccion_t": "Produccion (t)",
    "rendimiento_t_ha": "Rendimiento (t/ha)",
}


def audit_ranges(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.6: rangos validos, outliers 3xIQR.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    for col in _METRICAS:
        if col not in df.columns:
            continue
        serie = df[col].dropna()
        if len(serie) == 0:
            continue

        negativos = int((serie < 0).sum())
        ceros = int((serie == 0).sum())
        pct_ceros = (ceros / len(serie)) * 100

        if negativos > 0:
            findings.append(AuditFinding(
                codigo=f"AUD-RNG-{col[:8].upper()}",
                severidad="ERROR",
                descripcion=f"'{col}': {negativos:,} valores negativos",
                detalle=f"Min: {serie.min()}",
            ))

        if pct_ceros > 10:
            findings.append(AuditFinding(
                codigo=f"AUD-ZERO-{col[:8].upper()}",
                severidad="ADVERTENCIA",
                descripcion=f"'{col}': {pct_ceros:.1f}% son ceros",
                detalle="Podrian representar datos faltantes disfrazados",
            ))

        # Outliers por IQR (3xIQR para reducir falsos positivos)
        if len(serie) > 10 and serie.std() > 0:
            q1 = serie.quantile(0.25)
            q3 = serie.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                limite_sup = q3 + 3 * iqr
                outliers = serie[serie > limite_sup]
                pct_out = (len(outliers) / len(serie)) * 100
                if len(outliers) > 0 and pct_out > 1:
                    findings.append(AuditFinding(
                        codigo=f"AUD-OUT-{col[:8].upper()}",
                        severidad="ADVERTENCIA",
                        descripcion=f"'{col}': {len(outliers):,} outliers ({pct_out:.1f}%)",
                        detalle=f"Limite 3xIQR: {limite_sup:.4f}",
                    ))

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 12: core/audit/logic.py
# ═══════════════════════════════════════════════════════════
LOGIC = '''"""
Auditoria 2.7: Consistencia logica.
Verifica relaciones logicas entre variables (reglas de negocio).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.constants import RENDIMIENTO_TOLERANCIA_PCT
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.logic")


def audit_logic(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.7: reglas de negocio R1-R6.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    df_check = df.dropna(
        subset=["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]
    ).copy()

    if len(df_check) == 0:
        findings.append(AuditFinding(
            codigo="AUD-LOG-000",
            severidad="ERROR",
            descripcion="No hay registros completos para verificar consistencia logica",
        ))
        return findings

    # Regla 1: area cosechada <= area sembrada
    violacion_area = df_check[df_check["area_cosechada_ha"] > df_check["area_sembrada_ha"]]
    n_viol_area = len(violacion_area)
    if n_viol_area > 0:
        max_dif = (violacion_area["area_cosechada_ha"] - violacion_area["area_sembrada_ha"]).max()
        findings.append(AuditFinding(
            codigo="AUD-LOG-001",
            severidad="ERROR",
            descripcion=f"{n_viol_area:,} registros con area cosechada > sembrada",
            detalle=f"Maxima diferencia: {max_dif:.2f} ha",
        ))

    # Regla 2: rendimiento = produccion / area cosechada
    df_rend = df_check[df_check["area_cosechada_ha"] > 0].copy()
    if len(df_rend) > 0:
        df_rend["rendimiento_calculado"] = (
            df_rend["produccion_t"] / df_rend["area_cosechada_ha"]
        )
        df_rend["desviacion_pct"] = np.where(
            df_rend["rendimiento_t_ha"] > 0,
            np.abs(df_rend["rendimiento_calculado"] - df_rend["rendimiento_t_ha"])
            / df_rend["rendimiento_t_ha"] * 100,
            np.inf,
        )
        violacion_rend = df_rend[df_rend["desviacion_pct"] > RENDIMIENTO_TOLERANCIA_PCT]
        n_viol_rend = len(violacion_rend)
        if n_viol_rend > 0:
            pct_viol = (n_viol_rend / len(df_rend)) * 100
            findings.append(AuditFinding(
                codigo="AUD-LOG-002",
                severidad="ADVERTENCIA",
                descripcion=(
                    f"{n_viol_rend:,} registros ({pct_viol:.1f}%) con rendimiento "
                    f"inconsistente (desv. > {RENDIMIENTO_TOLERANCIA_PCT}%)"
                ),
                detalle=f"Desv. media: {violacion_rend['desviacion_pct'].mean():.1f}%",
            ))
        else:
            findings.append(AuditFinding(
                codigo="AUD-LOG-002",
                severidad="INFO",
                descripcion=(
                    f"Rendimiento consistente con prod/area en todos los registros "
                    f"(tolerancia <= {RENDIMIENTO_TOLERANCIA_PCT}%)"
                ),
            ))

    # Regla 3: produccion=0 con area cosechada>0
    prod_cero_area_positiva = df_check[
        (df_check["produccion_t"] == 0) & (df_check["area_cosechada_ha"] > 0)
    ]
    n_prod_zero = len(prod_cero_area_positiva)
    if n_prod_zero > 0:
        findings.append(AuditFinding(
            codigo="AUD-LOG-003",
            severidad="ADVERTENCIA",
            descripcion=f"{n_prod_zero:,} registros con produccion=0 pero area cosechada>0",
            detalle="Posible perdida total de cosecha o dato pendiente",
        ))

    # Regla 4: area cosechada=0 con produccion>0
    area_cero_prod_positiva = df_check[
        (df_check["area_cosechada_ha"] == 0) & (df_check["produccion_t"] > 0)
    ]
    n_area_zero = len(area_cero_prod_positiva)
    if n_area_zero > 0:
        findings.append(AuditFinding(
            codigo="AUD-LOG-004",
            severidad="ERROR",
            descripcion=f"{n_area_zero:,} registros con area cosechada=0 pero produccion>0",
            detalle="Inconsistencia matematica imposible",
        ))

    return findings
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 13: core/audit/report.py
# ═══════════════════════════════════════════════════════════
REPORT = '''"""
Generacion del reporte consolidado de auditoria.
Reemplaza auditoria_28_reporte_consolidado() del Notebook 2.
Mejora: recibe los hallazgos como parametro (no lee global).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.report")

_csv_storage = CsvStorage()


def generate_audit_report(
    findings: list[AuditFinding],
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Genera el reporte consolidado de auditoria y lo exporta a CSV.

    Args:
        findings: Lista de hallazgos de todas las auditorias.
        output_path: Ruta de salida del CSV. Si es None, usa la ruta por defecto.

    Returns:
        DataFrame con todos los hallazgos.
    """
    if not findings:
        log.info("No se registraron hallazgos de auditoria.")
        return pd.DataFrame()

    df_hallazgos = pd.DataFrame([f.to_dict() for f in findings])

    # Resumen por severidad
    for sev in ["ERROR", "ADVERTENCIA", "INFO"]:
        n = len(df_hallazgos[df_hallazgos["severidad"] == sev])
        log.info("Auditoria [%s]: %d hallazgo(s)", sev, n)

    # Guardar CSV
    if output_path is None:
        output_path = (
            settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv"
        )
    _csv_storage.write_csv(df_hallazgos, output_path)
    log.info("Reporte de auditoria guardado: %s", output_path.name)

    return df_hallazgos
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 14: core/audit/__init__.py (FACHADA)
# ═══════════════════════════════════════════════════════════
AUDIT_INIT = '''"""
Modulo de auditoria de datos del proyecto eva-valle-v3.0.

Fachada que orquesta las 8 auditorias del Paso 2 y expone
funciones de carga/estandarizacion del Paso 1.

Uso:
    from core.audit import run_all_audits, load_and_standardize

    # Paso 1: Carga y estandarizacion
    df_valle, mapeo = load_and_standardize()

    # Paso 2: Auditoria completa
    findings = run_all_audits(df_valle)
"""
from core.audit.models import AuditFinding
from core.audit.loader import load_and_standardize
from core.audit.structure import audit_structure
from core.audit.nulls import audit_nulls
from core.audit.duplicates import audit_duplicates
from core.audit.territory import audit_territory
from core.audit.temporal import audit_temporal
from core.audit.ranges import audit_ranges
from core.audit.logic import audit_logic
from core.audit.report import generate_audit_report
from core.logging import get_logger, log_section

log = get_logger("core.audit")

__all__ = [
    "AuditFinding",
    "load_and_standardize",
    "run_all_audits",
    "audit_structure",
    "audit_nulls",
    "audit_duplicates",
    "audit_territory",
    "audit_temporal",
    "audit_ranges",
    "audit_logic",
    "generate_audit_report",
]


def run_all_audits(df) -> list[AuditFinding]:
    """
    Ejecuta las 8 auditorias secuenciales sobre el DataFrame.

    Args:
        df: DataFrame estandarizado del Paso 1.

    Returns:
        Lista consolidada de hallazgos de todas las auditorias.
    """
    log_section("PASO 2 - AUDITORIA TECNICA PROFUNDA")

    all_findings: list[AuditFinding] = []

    # 2.1 Estructura
    findings_21 = audit_structure(df)
    all_findings.extend(findings_21)
    log.info("Auditoria 2.1 completada: %d hallazgo(s)", len(findings_21))

    # 2.2 Nulos
    findings_22 = audit_nulls(df)
    all_findings.extend(findings_22)
    log.info("Auditoria 2.2 completada: %d hallazgo(s)", len(findings_22))

    # 2.3 Duplicados
    findings_23 = audit_duplicates(df)
    all_findings.extend(findings_23)
    log.info("Auditoria 2.3 completada: %d hallazgo(s)", len(findings_23))

    # 2.4 Integridad territorial
    findings_24 = audit_territory(df)
    all_findings.extend(findings_24)
    log.info("Auditoria 2.4 completada: %d hallazgo(s)", len(findings_24))

    # 2.5 Coherencia temporal
    findings_25 = audit_temporal(df)
    all_findings.extend(findings_25)
    log.info("Auditoria 2.5 completada: %d hallazgo(s)", len(findings_25))

    # 2.6 Rangos numericos
    findings_26 = audit_ranges(df)
    all_findings.extend(findings_26)
    log.info("Auditoria 2.6 completada: %d hallazgo(s)", len(findings_26))

    # 2.7 Consistencia logica
    findings_27 = audit_logic(df)
    all_findings.extend(findings_27)
    log.info("Auditoria 2.7 completada: %d hallazgo(s)", len(findings_27))

    log.info(
        "Auditoria completa: %d hallazgos en total.",
        len(all_findings),
    )
    return all_findings
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "core/audit/models.py": MODELS,
        "core/audit/normalization.py": NORMALIZATION,
        "core/audit/type_conversion.py": TYPE_CONVERSION,
        "core/audit/territorial_filter.py": TERRITORIAL_FILTER,
        "core/audit/loader.py": LOADER,
        "core/audit/structure.py": STRUCTURE,
        "core/audit/nulls.py": NULLS,
        "core/audit/duplicates.py": DUPLICATES,
        "core/audit/territory.py": TERRITORY,
        "core/audit/temporal.py": TEMPORAL,
        "core/audit/ranges.py": RANGES,
        "core/audit/logic.py": LOGIC,
        "core/audit/report.py": REPORT,
        "core/audit/__init__.py": AUDIT_INIT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} archivos del modulo de auditoria creados.")
    print('Ejecuta: python -c "from core.audit import run_all_audits; print(\'OK\')"')