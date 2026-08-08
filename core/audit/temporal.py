"""
Auditoria 2.5: Coherencia temporal.
Verifica anos, periodos y su coherencia cruzada.
"""
from __future__ import annotations

import re

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.temporal")

_ANOS_ESPERADOS = set(range(2019, 2025))
_PATRON_PERIODO = re.compile(r"^\d{4}[AB]$")


def audit_temporal(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.5: anos, periodos, coherencia cruzada.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    anos_unicos = sorted(df["ano"].dropna().unique())
    ano_min, ano_max = int(df["ano"].min()), int(df["ano"].max())

    if ano_min >= 2019 and ano_max <= 2024:
        findings.append(AuditFinding(
            codigo="AUD-TEM-001",
            severidad="INFO",
            descripcion=f"Rango de anos dentro de lo esperado: {ano_min}-{ano_max}",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TEM-001",
            severidad="ADVERTENCIA",
            descripcion=f"Rango de anos inesperado: {ano_min}-{ano_max}",
            detalle="Esperado: 2019-2024",
        ))

    # Anos faltantes
    anos_presentes = set(int(a) for a in anos_unicos if pd.notna(a))
    anos_faltantes = _ANOS_ESPERADOS - anos_presentes
    if anos_faltantes:
        findings.append(AuditFinding(
            codigo="AUD-TEM-002",
            severidad="ADVERTENCIA",
            descripcion=f"Anos faltantes en el dataset: {sorted(anos_faltantes)}",
        ))

    # Formato de periodos
    periodos_unicos = sorted(df["periodo"].dropna().unique())
    periodos_mal = [p for p in periodos_unicos if not _PATRON_PERIODO.match(str(p))]
    if periodos_mal:
        findings.append(AuditFinding(
            codigo="AUD-TEM-003",
            severidad="ADVERTENCIA",
            descripcion=f"Periodos con formato inesperado: {periodos_mal}",
            detalle="Formato esperado: YYYY[A|B] (ej: 2023A, 2023B)",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TEM-003",
            severidad="INFO",
            descripcion="Todos los periodos tienen formato YYYY[A|B] correcto",
        ))

    # Coherencia ano-periodo
    if "ano" in df.columns and "periodo" in df.columns:
        df_temp = df.dropna(subset=["ano", "periodo"]).copy()
        df_temp["ano_periodo"] = df_temp["periodo"].str[:4].astype(int)
        discrepancias = df_temp[df_temp["ano"] != df_temp["ano_periodo"]]
        n_disc = len(discrepancias)
        if n_disc > 0:
            findings.append(AuditFinding(
                codigo="AUD-TEM-004",
                severidad="ERROR",
                descripcion=f"{n_disc:,} registros con ano != ano del periodo",
                detalle=f"Ej: ano={discrepancias['ano'].iloc[0]}, periodo={discrepancias['periodo'].iloc[0]}",
            ))

    return findings
