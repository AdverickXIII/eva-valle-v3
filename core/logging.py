"""
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
