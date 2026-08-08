"""
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
            msg += f"\n  -> {hint}"
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
