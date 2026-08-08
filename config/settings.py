"""
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
            f"Settings(\n"
            f"  PROJECT_NAME={self.PROJECT_NAME!r},\n"
            f"  ENV={self.ENV!r},\n"
            f"  PROJECT_ROOT={str(self.PROJECT_ROOT)!r},\n"
            f"  DATA_RAW_PATH={str(self.DATA_RAW_PATH)!r},\n"
            f"  LOG_LEVEL={self.LOG_LEVEL!r}\n"
            f")"
        )


# Instancia unica global (singleton por modulo)
settings = Settings()
