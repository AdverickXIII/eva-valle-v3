"""
Modulo de auditoria de datos del proyecto eva-valle-v3.0.

Fachada que orquesta las 8 auditorias del Paso 2 y expone
funciones de carga/estandarizacion del Paso 1.

Uso:
    from core.audit import run_all_audits, load_and_standardize

    # Paso 1: Carga y estandarizacion
    df_valle, mapeo = load_and_standardize()

    # Paso 2: Auditoria completa
    findings = run_all_audits(df_valle)
"""
from core.audit.models import AuditFinding
from core.audit.loader import load_and_standardize
from core.audit.structure import audit_structure
from core.audit.nulls import audit_nulls
from core.audit.duplicates import audit_duplicates
from core.audit.territory import audit_territory
from core.audit.temporal import audit_temporal
from core.audit.ranges import audit_ranges
from core.audit.logic import audit_logic
from core.audit.report import generate_audit_report
from core.logging import get_logger, log_section

log = get_logger("core.audit")

__all__ = [
    "AuditFinding",
    "load_and_standardize",
    "run_all_audits",
    "audit_structure",
    "audit_nulls",
    "audit_duplicates",
    "audit_territory",
    "audit_temporal",
    "audit_ranges",
    "audit_logic",
    "generate_audit_report",
]


def run_all_audits(df) -> list[AuditFinding]:
    """
    Ejecuta las 8 auditorias secuenciales sobre el DataFrame.

    Args:
        df: DataFrame estandarizado del Paso 1.

    Returns:
        Lista consolidada de hallazgos de todas las auditorias.
    """
    log_section("PASO 2 - AUDITORIA TECNICA PROFUNDA")

    all_findings: list[AuditFinding] = []

    # 2.1 Estructura
    findings_21 = audit_structure(df)
    all_findings.extend(findings_21)
    log.info("Auditoria 2.1 completada: %d hallazgo(s)", len(findings_21))

    # 2.2 Nulos
    findings_22 = audit_nulls(df)
    all_findings.extend(findings_22)
    log.info("Auditoria 2.2 completada: %d hallazgo(s)", len(findings_22))

    # 2.3 Duplicados
    findings_23 = audit_duplicates(df)
    all_findings.extend(findings_23)
    log.info("Auditoria 2.3 completada: %d hallazgo(s)", len(findings_23))

    # 2.4 Integridad territorial
    findings_24 = audit_territory(df)
    all_findings.extend(findings_24)
    log.info("Auditoria 2.4 completada: %d hallazgo(s)", len(findings_24))

    # 2.5 Coherencia temporal
    findings_25 = audit_temporal(df)
    all_findings.extend(findings_25)
    log.info("Auditoria 2.5 completada: %d hallazgo(s)", len(findings_25))

    # 2.6 Rangos numericos
    findings_26 = audit_ranges(df)
    all_findings.extend(findings_26)
    log.info("Auditoria 2.6 completada: %d hallazgo(s)", len(findings_26))

    # 2.7 Consistencia logica
    findings_27 = audit_logic(df)
    all_findings.extend(findings_27)
    log.info("Auditoria 2.7 completada: %d hallazgo(s)", len(findings_27))

    log.info(
        "Auditoria completa: %d hallazgos en total.",
        len(all_findings),
    )
    return all_findings
