"""
Auditoria 2.3: Duplicados.
Verifica duplicados exactos y por clave natural.
"""
from __future__ import annotations

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.duplicates")

# Clave natural: ano + periodo + municipio + cultivo + desagregacion
CLAVE_NATURAL = [
    "ano", "periodo", "codigo_dane_municipio",
    "cultivo", "desagregacion_cultivo",
]


def audit_duplicates(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.3: duplicados exactos y por clave natural.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    # Duplicados exactos (todas las columnas)
    n_dup_exactos = int(df.duplicated().sum())
    if n_dup_exactos > 0:
        findings.append(AuditFinding(
            codigo="AUD-DUP-001",
            severidad="ERROR",
            descripcion=f"{n_dup_exactos:,} registros duplicados exactos",
            detalle="Eliminar con drop_duplicates()",
        ))
    else:
        log.info("Sin duplicados exactos.")

    # Duplicados por clave natural
    clave_existente = [c for c in CLAVE_NATURAL if c in df.columns]
    if len(clave_existente) == len(CLAVE_NATURAL):
        n_dup_clave = int(df.duplicated(subset=CLAVE_NATURAL).sum())
        if n_dup_clave > 0:
            findings.append(AuditFinding(
                codigo="AUD-DUP-002",
                severidad="ADVERTENCIA",
                descripcion=f"{n_dup_clave:,} registros con clave natural duplicada",
                detalle="Mismo cultivo/municipio/ano/periodo con datos distintos",
            ))
        else:
            findings.append(AuditFinding(
                codigo="AUD-DUP-002",
                severidad="INFO",
                descripcion="Sin duplicados por clave natural",
            ))
    else:
        log.warning("No se pudieron verificar duplicados por clave: faltan columnas.")

    return findings
