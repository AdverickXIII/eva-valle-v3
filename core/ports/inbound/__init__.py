"""
Puertos de ENTRADA (inbound): definen lo que el mundo exterior
(Streamlit, API, CLI) puede solicitar al nucleo de dominio.

Cada puerto es un Protocol (interfaz estructural). Los casos de uso
del nucleo implementan estos protocolos.
"""
from core.ports.inbound.data_loader_port import DataLoaderPort
from core.ports.inbound.audit_port import AuditPort
from core.ports.inbound.analytics_port import AnalyticsPort
from core.ports.inbound.diagnostics_port import DiagnosticsPort
from core.ports.inbound.ml_port import MLPort

__all__ = [
    "DataLoaderPort",
    "AuditPort",
    "AnalyticsPort",
    "DiagnosticsPort",
    "MLPort",
]
