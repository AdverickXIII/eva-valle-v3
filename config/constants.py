"""
Constantes de negocio inmutables.
Estas NO deben estar en .env porque son parte del dominio del problema
(no cambian entre entornos de desarrollo/produccion).
"""
from __future__ import annotations

# ── Identificadores territoriales ──────────────────────────
CODIGO_DANE_VALLE: int = 76
NOMBRE_DEPTO_VALLE: str = "Valle del Cauca"

# ── Estructura del archivo Excel de UPRA ───────────────────
SHEET_NAME_AGRICOLA: str = "BasePagina"
HEADER_ROW_AGRICOLA: int = 7  # Fila 0-indexed donde esta el header real

# ── Validacion de archivos ─────────────────────────────────
MIN_FILE_BYTES: int = 100_000  # 100 KB minimo para considerar un Excel valido
RENDIMIENTO_TOLERANCIA_PCT: float = 5.0  # % de desviacion tolerable en rendimiento

# ── Grupos de cultivo relevantes para analisis ─────────────
GRUPO_CULTIVO_CANA: str = "Cultivos tropicales tradicionales"

# ── Columnas esperadas del dataset EVA ─────────────────────
COLUMNAS_ESPERADAS: tuple[str, ...] = (
    "codigo_dane_departamento",
    "departamento",
    "codigo_dane_municipio",
    "municipio",
    "desagregacion_cultivo",
    "cultivo",
    "ciclo_del_cultivo",
    "grupo_cultivo",
    "subgrupo",
    "ano",
    "periodo",
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_t_ha",
    "nombre_cientifico_del_cultivo",
    "codigo_del_cultivo",
    "estado_fisico_del_cultivo",
)

# ── Columnas metricas (numericas) ──────────────────────────
COLUMNAS_METRICAS: tuple[str, ...] = (
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_t_ha",
)

# ── Columnas enteras (Int64 nullable) ─────────────────────
COLUMNAS_ENTERAS: tuple[str, ...] = (
    "codigo_dane_departamento",
    "codigo_dane_municipio",
    "ano",
    "codigo_del_cultivo",
)

# ── Llave natural propuesta (5 campos) ─────────────────────
LLAVE_NATURAL: tuple[str, ...] = (
    "codigo_dane_municipio",
    "desagregacion_cultivo",
    "periodo",
    "ciclo_del_cultivo",
    "estado_fisico_del_cultivo",
)

# ── Marcadores de raiz del proyecto ────────────────────────
ROOT_MARKERS: tuple[str, ...] = (
    ".git",
    "pyproject.toml",
    "setup.py",
    "README.md",
    "requirements.txt",
    ".env",
    "app.py",
)
