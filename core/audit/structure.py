"""
Auditoria 2.1: Estructura del dataset.
Verifica dimensiones, columnas esperadas, tipos y memoria.
"""
from __future__ import annotations

import pandas as pd

from config.constants import COLUMNAS_ESPERADAS
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.structure")


def audit_structure(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.1: verifica columnas esperadas y dimensiones.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    n_rows, n_cols = df.shape
    mem_mb = df.memory_usage(deep=True).sum() / 1_048_576
    log.info(
        "Auditoria 2.1: %d filas x %d columnas, %.2f MB",
        n_rows, n_cols, mem_mb,
    )

    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    extras = [c for c in df.columns if c not in COLUMNAS_ESPERADAS]

    if faltantes:
        findings.append(AuditFinding(
            codigo="AUD-001",
            severidad="ERROR",
            descripcion=f"Columnas faltantes: {faltantes}",
            detalle="Cambio de estructura en la fuente",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-001",
            severidad="INFO",
            descripcion="Todas las columnas esperadas presentes",
            detalle=f"Total: {len(COLUMNAS_ESPERADAS)}",
        ))

    if extras:
        findings.append(AuditFinding(
            codigo="AUD-002",
            severidad="ADVERTENCIA",
            descripcion=f"Columnas inesperadas: {extras}",
            detalle="Verificar si son nuevas variables",
        ))

    return findings
