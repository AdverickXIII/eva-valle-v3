"""
Adaptador de persistencia de modelos ML.
Implementa el puerto core.ports.outbound.ModelRegistryPort.
"""
from adapters.ml_registry.joblib_registry import JoblibModelRegistry

__all__ = ["JoblibModelRegistry"]
