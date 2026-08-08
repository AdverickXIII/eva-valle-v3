"""
Auditoria 2.7: Consistencia logica.
Verifica relaciones logicas entre variables (reglas de negocio).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config.constants import RENDIMIENTO_TOLERANCIA_PCT
from core.audit.models import AuditFinding
from core.logging import get_logger

log = get_logger("core.audit.logic")


def audit_logic(df: pd.DataFrame) -> list[AuditFinding]:
    """
    Auditoria 2.7: reglas de negocio R1-R6.

    Args:
        df: DataFrame estandarizado.

    Returns:
        Lista de hallazgos de auditoria.
    """
    findings: list[AuditFinding] = []

    df_check = df.dropna(
        subset=["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]
    ).copy()

    if len(df_check) == 0:
        findings.append(AuditFinding(
            codigo="AUD-LOG-000",
            severidad="ERROR",
            descripcion="No hay registros completos para verificar consistencia logica",
        ))
        return findings

    # Regla 1: area cosechada <= area sembrada
    violacion_area = df_check[df_check["area_cosechada_ha"] > df_check["area_sembrada_ha"]]
    n_viol_area = len(violacion_area)
    if n_viol_area > 0:
        max_dif = (violacion_area["area_cosechada_ha"] - violacion_area["area_sembrada_ha"]).max()
        findings.append(AuditFinding(
            codigo="AUD-LOG-001",
            severidad="ERROR",
            descripcion=f"{n_viol_area:,} registros con area cosechada > sembrada",
            detalle=f"Maxima diferencia: {max_dif:.2f} ha",
        ))

    # Regla 2: rendimiento = produccion / area cosechada
    df_rend = df_check[df_check["area_cosechada_ha"] > 0].copy()
    if len(df_rend) > 0:
        df_rend["rendimiento_calculado"] = (
            df_rend["produccion_t"] / df_rend["area_cosechada_ha"]
        )
        df_rend["desviacion_pct"] = np.where(
            df_rend["rendimiento_t_ha"] > 0,
            np.abs(df_rend["rendimiento_calculado"] - df_rend["rendimiento_t_ha"])
            / df_rend["rendimiento_t_ha"] * 100,
            np.inf,
        )
        violacion_rend = df_rend[df_rend["desviacion_pct"] > RENDIMIENTO_TOLERANCIA_PCT]
        n_viol_rend = len(violacion_rend)
        if n_viol_rend > 0:
            pct_viol = (n_viol_rend / len(df_rend)) * 100
            findings.append(AuditFinding(
                codigo="AUD-LOG-002",
                severidad="ADVERTENCIA",
                descripcion=(
                    f"{n_viol_rend:,} registros ({pct_viol:.1f}%) con rendimiento "
                    f"inconsistente (desv. > {RENDIMIENTO_TOLERANCIA_PCT}%)"
                ),
                detalle=f"Desv. media: {violacion_rend['desviacion_pct'].mean():.1f}%",
            ))
        else:
            findings.append(AuditFinding(
                codigo="AUD-LOG-002",
                severidad="INFO",
                descripcion=(
                    f"Rendimiento consistente con prod/area en todos los registros "
                    f"(tolerancia <= {RENDIMIENTO_TOLERANCIA_PCT}%)"
                ),
            ))

    # Regla 3: produccion=0 con area cosechada>0
    prod_cero_area_positiva = df_check[
        (df_check["produccion_t"] == 0) & (df_check["area_cosechada_ha"] > 0)
    ]
    n_prod_zero = len(prod_cero_area_positiva)
    if n_prod_zero > 0:
        findings.append(AuditFinding(
            codigo="AUD-LOG-003",
            severidad="ADVERTENCIA",
            descripcion=f"{n_prod_zero:,} registros con produccion=0 pero area cosechada>0",
            detalle="Posible perdida total de cosecha o dato pendiente",
        ))

    # Regla 4: area cosechada=0 con produccion>0
    area_cero_prod_positiva = df_check[
        (df_check["area_cosechada_ha"] == 0) & (df_check["produccion_t"] > 0)
    ]
    n_area_zero = len(area_cero_prod_positiva)
    if n_area_zero > 0:
        findings.append(AuditFinding(
            codigo="AUD-LOG-004",
            severidad="ERROR",
            descripcion=f"{n_area_zero:,} registros con area cosechada=0 pero produccion>0",
            detalle="Inconsistencia matematica imposible",
        ))

    return findings
