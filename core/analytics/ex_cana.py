"""
Analisis 4.14: Analisis Ex-Cana.
Revelando la matriz productiva oculta: recalcula HHI y Gini
excluyendo Cultivos Tropicales Tradicionales (Cana).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from config.constants import GRUPO_CULTIVO_CANA
from core.analytics.concentration import calculate_concentration
from core.logging import get_logger

log = get_logger("core.analytics.ex_cana")


def analyze_ex_cana(
    df: pd.DataFrame,
    grupo_cana: str = GRUPO_CULTIVO_CANA,
) -> dict[str, Any]:
    """
    Recalcula HHI y Gini excluyendo Cultivos Tropicales Tradicionales (Cana).

    Args:
        df: DataFrame completo del Valle del Cauca.
        grupo_cana: Nombre del grupo de cultivo de la cana.

    Returns:
        Diccionario con comparacion Con Cana vs Sin Cana.
        Si hay error, retorna {"error": "mensaje"}.
    """
    if "grupo_cultivo" not in df.columns:
        return {"error": "Columna grupo_cultivo no encontrada."}

    if grupo_cana not in df["grupo_cultivo"].unique():
        return {
            "error": f"Grupo '{grupo_cana}' no encontrado. Verificar nombre exacto en datos."
        }

    df_ex = df[df["grupo_cultivo"] != grupo_cana]
    if len(df_ex) == 0:
        return {"error": "No quedaron datos al excluir el grupo de la cana"}

    # Calcular concentracion con y sin cana
    hhi_full = calculate_concentration(df, "cultivo", "produccion_t")
    hhi_ex = calculate_concentration(df_ex, "cultivo", "produccion_t")

    resultado = {
        "contexto": "Analisis Ex-Cana",
        "produccion_total_cana": float(
            df[df["grupo_cultivo"] == grupo_cana]["produccion_t"].sum()
        ),
        "produccion_total_ex_cana": float(df_ex["produccion_t"].sum()),
        "HHI_Con_Cana": hhi_full.get("hhi"),
        "HHI_Sin_Cana": hhi_ex.get("hhi"),
        "Gini_Con_Cana": hhi_full.get("gini"),
        "Gini_Sin_Cana": hhi_ex.get("gini"),
        "n_cultivos_activos_ex_cana": int(df_ex["cultivo"].nunique()),
    }

    log.info(
        "Ex-Cana: HHI con cana=%.0f, sin cana=%.0f | Gini con cana=%.3f, sin cana=%.3f",
        resultado["HHI_Con_Cana"] or 0,
        resultado["HHI_Sin_Cana"] or 0,
        resultado["Gini_Con_Cana"] or 0,
        resultado["Gini_Sin_Cana"] or 0,
    )
    return resultado
