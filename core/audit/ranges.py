"""
Auditoria 2.6: Rangos numericos y anomalias.
Verifica rangos validos y detecta outliers por IQR.
"""
from __future__ import annotations

import pandas as pd

from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.ranges")

_METRICAS = {
    "area_sembrada_ha": "Area sembrada (ha)",
    "area_cosechada_ha": "Area cosechada (ha)",
    "produccion_t": "Produccion (t)",
    "rendimiento_t_ha": "Rendimiento (t/ha)",
}


def audit_ranges(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.6: rangos validos, outliers 3xIQR.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    for col in _METRICAS:
        if col not in df.columns:
            continue
        serie = df[col].dropna()
        if len(serie) == 0:
            continue

        negativos = int((serie < 0).sum())
        ceros = int((serie == 0).sum())
        pct_ceros = (ceros / len(serie)) * 100

        if negativos > 0:
            findings.append(AuditFinding(
                codigo=f"AUD-RNG-{col[:8].upper()}",
                severidad="ERROR",
                descripcion=f"'{col}': {negativos:,} valores negativos",
                detalle=f"Min: {serie.min()}",
            ))

        if pct_ceros > 10:
            findings.append(AuditFinding(
                codigo=f"AUD-ZERO-{col[:8].upper()}",
                severidad="ADVERTENCIA",
                descripcion=f"'{col}': {pct_ceros:.1f}% son ceros",
                detalle="Podrian representar datos faltantes disfrazados",
            ))

        # Outliers por IQR (3xIQR para reducir falsos positivos)
        if len(serie) > 10 and serie.std() > 0:
            q1 = serie.quantile(0.25)
            q3 = serie.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                limite_sup = q3 + 3 * iqr
                outliers = serie[serie > limite_sup]
                pct_out = (len(outliers) / len(serie)) * 100
                if len(outliers) > 0 and pct_out > 1:
                    findings.append(AuditFinding(
                        codigo=f"AUD-OUT-{col[:8].upper()}",
                        severidad="ADVERTENCIA",
                        descripcion=f"'{col}': {len(outliers):,} outliers ({pct_out:.1f}%)",
                        detalle=f"Limite 3xIQR: {limite_sup:.4f}",
                    ))

    return findings
