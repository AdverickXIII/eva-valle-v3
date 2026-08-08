"""
Auditoria 2.2: Nulos y cobertura.
Verifica la presencia de valores nulos por columna.
"""
from __future__ import annotations

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.nulls")


def audit_nulls(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.2: cobertura de nulos por columna.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []
    n = len(df)
    cols_con_nulos: list[tuple[str, int, float]] = []

    for col in df.columns:
        nul = int(df[col].isna().sum())
        pct = (nul / n) * 100 if n > 0 else 0
        if nul > 0:
            cols_con_nulos.append((col, nul, pct))

    if cols_con_nulos:
        for col, cnt, pct in cols_con_nulos:
            sev = "ADVERTENCIA" if pct < 5 else "ERROR"
            findings.append(AuditFinding(
                codigo=f"AUD-NUL-{col[:8].upper()}",
                severidad=sev,
                descripcion=f"'{col}': {cnt:,} nulos ({pct:.2f}%)",
                detalle="Cero reportado vs dato faltante",
            ))
        log.warning("Se encontraron %d columnas con nulos.", len(cols_con_nulos))
    else:
        findings.append(AuditFinding(
            codigo="AUD-003",
            severidad="INFO",
            descripcion="Sin valores nulos",
            detalle=f"Registros: {n:,}",
        ))
        log.info("Sin valores nulos en %d registros.", n)

    return findings
