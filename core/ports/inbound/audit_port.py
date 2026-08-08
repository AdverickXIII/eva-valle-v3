"""
Puerto de entrada para auditoria de datos.

Define el contrato para ejecutar las 8 auditorias del Paso 2:
2.1 Estructura, 2.2 Nulos, 2.3 Duplicados, 2.4 Territorial,
2.5 Temporal, 2.6 Rangos, 2.7 Consistencia logica, 2.8 Reporte.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class AuditPort(Protocol):
    """Contrato para ejecutar auditorias de calidad de datos."""

    def run_all_audits(self, df: pd.DataFrame) -> list[dict]:
        """
        Ejecuta las 8 auditorias secuenciales sobre el DataFrame.

        Args:
            df: DataFrame estandarizado del Paso 1.

        Returns:
            Lista de hallazgos, cada uno con:
            {codigo, severidad, descripcion, detalle}.
        """
        ...

    def run_structure_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.1: columnas esperadas, tipos, memoria."""
        ...

    def run_nulls_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.2: cobertura de nulos por columna."""
        ...

    def run_duplicates_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.3: duplicados exactos y por clave natural."""
        ...

    def run_territorial_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.4: coherencia codigos/nombres territoriales."""
        ...

    def run_temporal_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.5: anos, periodos, coherencia cruzada."""
        ...

    def run_ranges_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.6: rangos validos, outliers 3xIQR."""
        ...

    def run_logic_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.7: reglas de negocio R1-R6."""
        ...
