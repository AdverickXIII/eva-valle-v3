"""
Generacion del reporte consolidado de auditoria.
Reemplaza auditoria_28_reporte_consolidado() del Notebook 2.
Mejora: recibe los hallazgos como parametro (no lee global).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.report")

_csv_storage = CsvStorage()


def generate_audit_report(
    findings: list[AuditFinding],
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Genera el reporte consolidado de auditoria y lo exporta a CSV.

    Args:
        findings: Lista de hallazgos de todas las auditorias.
        output_path: Ruta de salida del CSV. Si es None, usa la ruta por defecto.

    Returns:
        DataFrame con todos los hallazgos.
    """
    if not findings:
        log.info("No se registraron hallazgos de auditoria.")
        return pd.DataFrame()

    df_hallazgos = pd.DataFrame([f.to_dict() for f in findings])

    # Resumen por severidad
    for sev in ["ERROR", "ADVERTENCIA", "INFO"]:
        n = len(df_hallazgos[df_hallazgos["severidad"] == sev])
        log.info("Auditoria [%s]: %d hallazgo(s)", sev, n)

    # Guardar CSV
    if output_path is None:
        output_path = (
            settings.OUTPUTS_TABLES_PATH / "auditoria_agricola_valle_2019_2024.csv"
        )
    _csv_storage.write_csv(df_hallazgos, output_path)
    log.info("Reporte de auditoria guardado: %s", output_path.name)

    return df_hallazgos
