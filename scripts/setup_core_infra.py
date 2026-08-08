"""
Setup script: genera los 5 archivos de infraestructura base del proyecto.
Ejecutar una sola vez: python scripts/setup_core_infra.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: config/__init__.py
# ═══════════════════════════════════════════════════════════
CONFIG_INIT = '''"""Paquete de configuracion del proyecto eva-valle-v3.0."""
from config.settings import settings
from config.constants import (
    CODIGO_DANE_VALLE,
    NOMBRE_DEPTO_VALLE,
    SHEET_NAME_AGRICOLA,
    HEADER_ROW_AGRICOLA,
    MIN_FILE_BYTES,
)

__all__ = [
    "settings",
    "CODIGO_DANE_VALLE",
    "NOMBRE_DEPTO_VALLE",
    "SHEET_NAME_AGRICOLA",
    "HEADER_ROW_AGRICOLA",
    "MIN_FILE_BYTES",
]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: config/settings.py
# ═══════════════════════════════════════════════════════════
CONFIG_SETTINGS = '''"""
Configuracion centralizada del proyecto.
Carga variables desde .env usando python-dotenv.

Uso:
    from config.settings import settings
    print(settings.DATA_RAW_PATH)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Cargar .env ANTES de leer variables (idempotente)
load_dotenv(override=False)


def _env_str(key: str, default: str = "") -> str:
    """Lee variable de entorno con valor por defecto."""
    return os.getenv(key, default)


def _env_int(key: str, default: int = 0) -> int:
    """Lee variable de entorno como entero."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    """Lee variable de entorno como float."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    """Lee variable de entorno como booleano."""
    val = os.getenv(key, str(default)).lower()
    return val in ("1", "true", "yes", "on", "si", "sí")


def _resolve_project_root() -> Path:
    """Resuelve la raiz del proyecto desde EVA_PROJECT_ROOT o marcadores."""
    explicit = _env_str("EVA_PROJECT_ROOT", "")
    if explicit:
        p = Path(explicit).resolve()
        if p.exists():
            return p

    # Fallback: buscar marcadores hacia arriba
    from core.paths import find_project_root
    return find_project_root()


@dataclass(frozen=True)
class Settings:
    """Configuracion inmutable del proyecto. Se instancia una sola vez."""

    # ── Metadata ─────────────────────────────────────────────
    PROJECT_NAME: str = field(default_factory=lambda: _env_str("EVA_PROJECT_NAME", "eva-valle-v3.0"))
    ENV: str = field(default_factory=lambda: _env_str("EVA_ENV", "development"))

    # ── Raiz del proyecto ────────────────────────────────────
    PROJECT_ROOT: Path = field(default_factory=_resolve_project_root)

    # ── Rutas de datos ───────────────────────────────────────
    DATA_RAW_PATH: Path = field(init=False)
    DATA_PROCESSED_PATH: Path = field(init=False)
    DATA_MODEL_PATH: Path = field(init=False)
    DATA_EXTERNAL_PATH: Path = field(init=False)
    OUTPUTS_PATH: Path = field(init=False)
    OUTPUTS_TABLES_PATH: Path = field(init=False)
    OUTPUTS_FIGURES_PATH: Path = field(init=False)
    OUTPUTS_REPORTS_PATH: Path = field(init=False)
    MODELS_PATH: Path = field(init=False)
    LOGS_PATH: Path = field(init=False)

    # ── Descarga UPRA ────────────────────────────────────────
    UPRA_BASE_URL: str = field(
        default_factory=lambda: _env_str(
            "EVA_UPRA_BASE_URL", "https://upra.gov.co/es-co/eva/eva-2024"
        )
    )
    DOWNLOAD_TIMEOUT: int = field(default_factory=lambda: _env_int("EVA_DOWNLOAD_TIMEOUT", 60))
    DOWNLOAD_RETRIES: int = field(default_factory=lambda: _env_int("EVA_DOWNLOAD_RETRIES", 3))
    HEADLESS: bool = field(default_factory=lambda: _env_bool("EVA_HEADLESS", True))

    # ── Streamlit ────────────────────────────────────────────
    ST_THEME: str = field(default_factory=lambda: _env_str("EVA_ST_THEME", "dark"))
    ST_PAGE_WIDTH: str = field(default_factory=lambda: _env_str("EVA_ST_PAGE_WIDTH", "wide"))

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = field(default_factory=lambda: _env_str("EVA_LOG_LEVEL", "INFO"))
    LOG_FILE: Path = field(init=False)

    # ── Machine Learning ─────────────────────────────────────
    ML_RANDOM_STATE: int = field(default_factory=lambda: _env_int("EVA_ML_RANDOM_STATE", 42))
    ML_TEST_SIZE: float = field(default_factory=lambda: _env_float("EVA_ML_TEST_SIZE", 0.2))

    def __post_init__(self) -> None:
        """Calcula rutas derivadas de PROJECT_ROOT."""
        raw = _env_str("EVA_DATA_RAW_PATH", "data/raw/upra")
        processed = _env_str("EVA_DATA_PROCESSED_PATH", "data/processed")
        outputs = _env_str("EVA_OUTPUTS_PATH", "outputs")
        models = _env_str("EVA_ML_MODELS_PATH", "models")
        log_file = _env_str("EVA_LOG_FILE", "logs/eva_valle.log")

        # Usar object.__setattr__ porque el dataclass es frozen
        object.__setattr__(self, "DATA_RAW_PATH", self.PROJECT_ROOT / raw)
        object.__setattr__(self, "DATA_PROCESSED_PATH", self.PROJECT_ROOT / processed)
        object.__setattr__(self, "DATA_MODEL_PATH", self.PROJECT_ROOT / processed / "02_modelo")
        object.__setattr__(self, "DATA_EXTERNAL_PATH", self.PROJECT_ROOT / "data" / "external")
        object.__setattr__(self, "OUTPUTS_PATH", self.PROJECT_ROOT / outputs)
        object.__setattr__(self, "OUTPUTS_TABLES_PATH", self.PROJECT_ROOT / outputs / "tables")
        object.__setattr__(self, "OUTPUTS_FIGURES_PATH", self.PROJECT_ROOT / outputs / "figures")
        object.__setattr__(self, "OUTPUTS_REPORTS_PATH", self.PROJECT_ROOT / outputs / "reports")
        object.__setattr__(self, "MODELS_PATH", self.PROJECT_ROOT / models)
        object.__setattr__(self, "LOGS_PATH", self.PROJECT_ROOT / "logs")
        object.__setattr__(self, "LOG_FILE", self.PROJECT_ROOT / log_file)

    def ensure_directories(self) -> None:
        """Crea todos los directorios si no existen (idempotente)."""
        dirs = [
            self.DATA_RAW_PATH,
            self.DATA_PROCESSED_PATH,
            self.DATA_MODEL_PATH,
            self.DATA_EXTERNAL_PATH,
            self.OUTPUTS_PATH,
            self.OUTPUTS_TABLES_PATH,
            self.OUTPUTS_FIGURES_PATH,
            self.OUTPUTS_REPORTS_PATH,
            self.MODELS_PATH,
            self.LOGS_PATH,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return (
            f"Settings(\\n"
            f"  PROJECT_NAME={self.PROJECT_NAME!r},\\n"
            f"  ENV={self.ENV!r},\\n"
            f"  PROJECT_ROOT={str(self.PROJECT_ROOT)!r},\\n"
            f"  DATA_RAW_PATH={str(self.DATA_RAW_PATH)!r},\\n"
            f"  LOG_LEVEL={self.LOG_LEVEL!r}\\n"
            f")"
        )


# Instancia unica global (singleton por modulo)
settings = Settings()
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: config/constants.py
# ═══════════════════════════════════════════════════════════
CONFIG_CONSTANTS = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: core/paths.py
# ═══════════════════════════════════════════════════════════
CORE_PATHS = '''"""
Utilidades para resolucion de rutas del proyecto.
Extraido de los 7 notebooks originales para eliminar duplicacion (DRY).

Uso:
    from core.paths import find_project_root, get_paths
    root = find_project_root()
    paths = get_paths(root)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

# Importacion diferida para evitar dependencia circular con config.constants
# (ROOT_MARKERS se usa aqui pero se define en constants)


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Sube el arbol de directorios buscando marcadores de raiz del proyecto.

    Args:
        start: Directorio de inicio. Si es None, usa cwd().

    Returns:
        Path absoluta al directorio raiz del proyecto.
        Si no encuentra marcadores, retorna start.resolve().

    Ejemplo:
        >>> root = find_project_root()
        >>> print(root.name)
        'eva-valle-v3.0'
    """
    # Importar aqui para romper dependencia circular
    from config.constants import ROOT_MARKERS

    if start is None:
        start = Path.cwd()
    candidate = start.resolve()

    for directory in [candidate, *candidate.parents]:
        if any((directory / marker).exists() for marker in ROOT_MARKERS):
            return directory

    return candidate


def get_paths(root: Optional[Path] = None) -> dict[str, Path]:
    """
    Construye un diccionario con todas las rutas estandar del proyecto.

    Args:
        root: Raiz del proyecto. Si es None, se detecta automaticamente.

    Returns:
        Diccionario con claves: data_raw, data_clean, data_modelo,
        data_external, outputs_figures, outputs_tables, outputs_reports, logs.

    Nota:
        Este helper es legado del pipeline original. En la nueva arquitectura
        se recomienda usar directamente `config.settings.settings.DATA_RAW_PATH`, etc.
        Se mantiene para compatibilidad durante la migracion.
    """
    if root is None:
        root = find_project_root()

    return {
        "data_raw": root / "data" / "raw" / "upra",
        "data_clean": root / "data" / "processed" / "01_clean",
        "data_modelo": root / "data" / "processed" / "02_modelo",
        "data_external": root / "data" / "external",
        "outputs_figures": root / "outputs" / "figures",
        "outputs_tables": root / "outputs" / "tables",
        "outputs_reports": root / "outputs" / "reports",
        "logs": root / "logs",
    }


def ensure_directories(paths: dict[str, Path]) -> None:
    """
    Crea todos los directorios del diccionario si no existen (idempotente).

    Args:
        paths: Diccionario de rutas (como el retornado por get_paths).
    """
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: core/exceptions.py
# ═══════════════════════════════════════════════════════════
CORE_EXCEPTIONS = '''"""
Excepciones personalizadas del dominio EVA Valle.

Permiten manejar errores de forma explicita y con mensajes claros,
en lugar de depender de excepciones genericas de Python.

Uso:
    from core.exceptions import DatasetNotFoundError, AuditError

    if not path.exists():
        raise DatasetNotFoundError(path, "Ejecuta el paso anterior primero.")
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


class EvaValleError(Exception):
    """Excepcion base del proyecto. Todas las demas heredan de esta."""

    pass


class DatasetNotFoundError(EvaValleError, FileNotFoundError):
    """Se lanza cuando un dataset de entrada requerido no existe."""

    def __init__(self, path: Path, hint: str = "") -> None:
        self.path = path
        self.hint = hint
        msg = f"Dataset no encontrado: {path}"
        if hint:
            msg += f"\\n  -> {hint}"
        super().__init__(msg)


class AuditError(EvaValleError):
    """Se lanza cuando una auditoria de datos detecta un problema critico."""

    def __init__(self, audit_code: str, message: str, severity: str = "ERROR") -> None:
        self.audit_code = audit_code
        self.severity = severity
        super().__init__(f"[{audit_code}] {severity}: {message}")


class DownloaderError(EvaValleError):
    """Se lanza cuando falla la descarga desde el portal UPRA."""

    def __init__(self, file_key: str, reason: str, url: Optional[str] = None) -> None:
        self.file_key = file_key
        self.url = url
        msg = f"Descarga fallida para '{file_key}': {reason}"
        if url:
            msg += f" (URL: {url})"
        super().__init__(msg)


class PipelineStepError(EvaValleError):
    """Se lanza cuando un paso del pipeline falla."""

    def __init__(self, step_name: str, reason: str) -> None:
        self.step_name = step_name
        super().__init__(f"Paso '{step_name}' fallo: {reason}")


class ModelTrainingError(EvaValleError):
    """Se lanza cuando el entrenamiento de un modelo ML falla."""

    def __init__(self, model_name: str, reason: str) -> None:
        self.model_name = model_name
        super().__init__(f"Entrenamiento de '{model_name}' fallo: {reason}")


class ConfigurationError(EvaValleError):
    """Se lanza cuando la configuracion es invalida o falta."""

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        super().__init__(f"Error de configuracion en '{key}': {reason}")
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: core/logging.py
# ═══════════════════════════════════════════════════════════
CORE_LOGGING = '''"""
Sistema de logging centralizado del proyecto.

Resuelve el problema de los 7 notebooks originales: cada uno llamaba a
`logging.basicConfig()` independientemente, causando handlers duplicados
cuando se importaban varios modulos juntos.

Uso:
    from core.logging import get_logger
    log = get_logger("core.analytics.concentration")
    log.info("Calculando Gini...")

Caracteristicas:
    - Un solo handler de consola + un solo handler de archivo (globales)
    - Idempotente: llamar get_logger() N veces no duplica handlers
    - Formato consistente en todo el proyecto
    - El archivo de log rota automaticamente por tamano
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Flag global para garantizar configuracion unica
_CONFIGURED: bool = False


def _configure_once() -> None:
    """
    Configura el logging raiz del proyecto UNA SOLA VEZ.
    Las llamadas subsecuentes son no-ops (idempotente).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    # Importar aqui para evitar dependencia circular al cargar el modulo
    from config.settings import settings

    # Asegurar que exista el directorio de logs
    settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)

    # Formato comun para todos los handlers
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(settings.LOG_LEVEL)

    # Handler de archivo con rotacion (5 MB x 5 backups = 25 MB max)
    file_handler = RotatingFileHandler(
        filename=settings.LOG_FILE,
        mode="a",
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(settings.LOG_LEVEL)

    # Configurar logger raiz del proyecto
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Limpiar handlers previos (por si algun modulo llamo basicConfig antes)
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reducir verbosidad de librerias externas
    for noisy in ("urllib3", "selenium", "matplotlib", "PIL", "fsevents"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retorna un logger con el nombre dado, configurando el sistema si es necesario.

    Args:
        name: Nombre del logger. Convencion: "modulo.submodulo.funcion".
              Ej: "core.analytics.concentration", "ui.pages.dashboard".
              Si es None, retorna el logger raiz.

    Returns:
        Instancia de logging.Logger lista para usar.

    Ejemplo:
        >>> log = get_logger("core.analytics.concentration")
        >>> log.info("Gini calculado: %.3f", gini)
    """
    _configure_once()
    return logging.getLogger(name)


def log_section(title: str, char: str = "=", width: int = 70) -> None:
    """
    Imprime un encabezado de seccion tanto en consola como en log.
    Util para delimitar fases del pipeline.

    Args:
        title: Titulo de la seccion.
        char: Caracter de relleno.
        width: Ancho total de la linea.
    """
    log = get_logger("pipeline.section")
    line = char * width
    log.info(line)
    log.info("  %s", title)
    log.info(line)
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "config/__init__.py": CONFIG_INIT,
        "config/settings.py": CONFIG_SETTINGS,
        "config/constants.py": CONFIG_CONSTANTS,
        "core/paths.py": CORE_PATHS,
        "core/exceptions.py": CORE_EXCEPTIONS,
        "core/logging.py": CORE_LOGGING,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\\n{creados} archivos de infraestructura base creados.")
    print("Ejecuta: python -c \"from config.settings import settings; print(settings)\"")