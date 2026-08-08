"""
Adaptadores de persistencia de archivos.
Implementan el puerto core.ports.outbound.StoragePort.
"""
from adapters.storage.csv_storage import CsvStorage
from adapters.storage.excel_storage import ExcelStorage
from adapters.storage.json_storage import JsonStorage

__all__ = ["CsvStorage", "ExcelStorage", "JsonStorage"]
