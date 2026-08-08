"""
Puertos de SALIDA (outbound): definen lo que el nucleo de dominio
necesita del mundo exterior (persistencia, descarga, serializacion).

Los adaptadores de infraestructura (adapters/) implementan estos
protocolos. El nucleo solo conoce los contratos, no las implementaciones.
"""
from core.ports.outbound.storage_port import StoragePort
from core.ports.outbound.downloader_port import DownloaderPort
from core.ports.outbound.model_registry_port import ModelRegistryPort

__all__ = [
    "StoragePort",
    "DownloaderPort",
    "ModelRegistryPort",
]
