"""Logging de acciones del usuario en la UI."""
from __future__ import annotations

from core.logging import get_logger

log = get_logger("ui.actions")


def log_action(action: str, detalle: str = "") -> None:
    """Registra una accion del usuario en el log del sistema."""
    log.info("UI | %s %s", action, detalle)
