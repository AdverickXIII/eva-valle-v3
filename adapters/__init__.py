"""
Adaptadores de infraestructura del proyecto eva-valle-v3.0.

Los adaptadores implementan los puertos definidos en core/ports/.
El nucleo de dominio NUNCA importa de este paquete directamente;
solo conoce los puertos (contratos).

Arquitectura Hexagonal:
    - adapters/storage/      → Implementa StoragePort (CSV, Excel, JSON)
    - adapters/downloader/   → Implementa DownloaderPort (Selenium UPRA)
    - adapters/ml_registry/  → Implementa ModelRegistryPort (joblib)
"""
