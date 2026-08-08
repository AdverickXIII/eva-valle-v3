"""
Auditoria 2.4: Integridad territorial.
Verifica coherencia de codigos y nombres territoriales.
"""
from __future__ import annotations

import pandas as pd

from config.constants import CODIGO_DANE_VALLE, NOMBRE_DEPTO_VALLE
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.territory")


def audit_territory(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.4: coherencia codigos/nombres territoriales.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    # Codigo DANE unico
    codigos_distintos = df["codigo_dane_departamento"].unique()
    if len(codigos_distintos) == 1 and codigos_distintos[0] == CODIGO_DANE_VALLE:
        findings.append(AuditFinding(
            codigo="AUD-TER-001",
            severidad="INFO",
            descripcion="Todos los registros tienen codigo DANE 76",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TER-001",
            severidad="ERROR",
            descripcion=f"Codigos inesperados: {list(codigos_distintos)}",
        ))

    # Nombre de departamento unico
    nombres_depto = df["departamento"].dropna().unique()
    if len(nombres_depto) == 1 and nombres_depto[0] == NOMBRE_DEPTO_VALLE:
        findings.append(AuditFinding(
            codigo="AUD-TER-002",
            severidad="INFO",
            descripcion=f"Nombre de departamento unico y correcto: '{NOMBRE_DEPTO_VALLE}'",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TER-002",
            severidad="ADVERTENCIA",
            descripcion=f"Nombres de depto inesperados: {list(nombres_depto)}",
        ))

    # Municipios: codigo -> nombre (1:1)
    n_municipios = df["codigo_dane_municipio"].nunique()
    muni_nombre = df.groupby("codigo_dane_municipio")["municipio"].nunique()
    muni_inconsistentes = muni_nombre[muni_nombre > 1]

    if len(muni_inconsistentes) > 0:
        ej_codigos = muni_inconsistentes.index[:3].tolist()
        findings.append(AuditFinding(
            codigo="AUD-TER-003",
            severidad="ADVERTENCIA",
            descripcion=f"{len(muni_inconsistentes)} municipio(s) con mas de un nombre",
            detalle=f"Ej: codigos {ej_codigos}",
        ))
    else:
        findings.append(AuditFinding(
            codigo="AUD-TER-003",
            severidad="INFO",
            descripcion="Relacion codigo-nombre municipio 1:1 consistente",
            detalle=f"{n_municipios} municipios unicos",
        ))

    # Nombre -> multiples codigos
    nombre_cod = df.groupby("municipio")["codigo_dane_municipio"].nunique()
    nombre_inconsistentes = nombre_cod[nombre_cod > 1]
    if len(nombre_inconsistentes) > 0:
        ej_nombres = nombre_inconsistentes.index[:3].tolist()
        findings.append(AuditFinding(
            codigo="AUD-TER-004",
            severidad="ADVERTENCIA",
            descripcion=f"{len(nombre_inconsistentes)} nombre(s) con multiples codigos DANE",
            detalle=f"Ej: {ej_nombres}",
        ))

    return findings
