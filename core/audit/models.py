"""
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
