"""
Adaptador de descarga de datos del portal UPRA.
Implementa el puerto core.ports.outbound.DownloaderPort.
"""
from adapters.downloader.upra_downloader import UpraDownloader

__all__ = ["UpraDownloader"]
