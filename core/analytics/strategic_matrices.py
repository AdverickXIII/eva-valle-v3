"""Matrices estrategicas de posicionamiento para el storytelling.

Matriz 1 (cultivos): crecimiento (CAGR) x participacion.
Matriz 2 (municipios): produccion x productividad relativa.
Umbrales = mediana (robusto a la dominancia de la cana).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# =====================================================================
# MATRIZ 1: CULTIVOS (crecimiento x participacion)
# =====================================================================
def matriz_cultivos(df: pd.DataFrame, min_prod: float = 500.0) -> pd.DataFrame:
    """Clasifica cultivos en 4 cuadrantes segun participacion y CAGR.

    Cuadrantes:
      Motor       = alta participacion + alto crecimiento
      Consolidado = alta participacion + bajo crecimiento
      Emergente   = baja participacion + alto crecimiento
      Rezagado    = baja participacion + bajo crecimiento
    """
    prod = df.groupby("cultivo")["produccion_t"].sum()
    total = prod.sum()
    participacion = (prod / total * 100)

    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ini, fin = anos[0], anos[-1]
    n = fin - ini
    p_ini = df[df["ano"] == ini].groupby("cultivo")["produccion_t"].sum()
    p_fin = df[df["ano"] == fin].groupby("cultivo")["produccion_t"].sum()
    cagr_df = pd.DataFrame({"ini": p_ini, "fin": p_fin}).dropna()
    cagr_df = cagr_df[cagr_df["ini"] > 0]
    cagr_df["cagr"] = ((cagr_df["fin"] / cagr_df["ini"]) ** (1 / n) - 1) * 100

    result = pd.DataFrame({
        "participacion_pct": participacion,
        "produccion": prod,
    })
    result = result.join(cagr_df[["cagr"]])
    result = result.dropna(subset=["cagr"])
    if min_prod:
        result = result[result["produccion"] >= min_prod]
    result = result.reset_index()

    if result.empty:
        return result

    umbral_part = result["participacion_pct"].median()
    umbral_cagr = result["cagr"].median()

    def _clasificar(row):
        alta_part = row["participacion_pct"] >= umbral_part
        alto_crec = row["cagr"] >= umbral_cagr
        if alta_part and alto_crec:
            return "Motor"
        if alta_part and not alto_crec:
            return "Consolidado"
        if not alta_part and alto_crec:
            return "Emergente"
        return "Rezagado"

    result["cuadrante"] = result.apply(_clasificar, axis=1)
    result["participacion_pct"] = result["participacion_pct"].round(2)
    result["cagr"] = result["cagr"].round(1)
    result["produccion"] = result["produccion"].round(0)
    return result.sort_values("participacion_pct", ascending=False).reset_index(drop=True)


# =====================================================================
# MATRIZ 2: MUNICIPIOS (produccion x productividad)
# =====================================================================
def matriz_municipios(df: pd.DataFrame) -> pd.DataFrame:
    """Clasifica municipios en 4 cuadrantes segun produccion y productividad.

    Productividad = rendimiento del municipio vs mediana departamental.
    Cuadrantes:
      Motores     = alta produccion + alta productividad
      Mejora      = alta produccion + baja productividad
      Potenciales = baja produccion + alta productividad
      Rezagados   = baja produccion + baja productividad
    """
    mun = df.groupby("municipio").agg(
        produccion=("produccion_t", "sum"),
        area_cos=("area_cosechada_ha", "sum"),
    ).reset_index()
    mun["rendimiento"] = mun["produccion"] / mun["area_cos"].replace(0, 1)

    # Productividad relativa: rendimiento del municipio vs mediana de rendimientos
    mediana_rend = mun["rendimiento"].median()
    mun["productividad_relativa"] = (mun["rendimiento"] / mediana_rend
                                     if mediana_rend > 0 else 1.0)

    umbral_prod = mun["produccion"].median()
    umbral_rend = 1.0  # ya esta normalizado contra la mediana

    def _clasificar(row):
        alta_prod = row["produccion"] >= umbral_prod
        alta_rend = row["productividad_relativa"] >= umbral_rend
        if alta_prod and alta_rend:
            return "Motores"
        if alta_prod and not alta_rend:
            return "Mejora"
        if not alta_prod and alta_rend:
            return "Potenciales"
        return "Rezagados"

    mun["cuadrante"] = mun.apply(_clasificar, axis=1)
    mun["produccion"] = mun["produccion"].round(0)
    mun["rendimiento"] = mun["rendimiento"].round(2)
    mun["productividad_relativa"] = mun["productividad_relativa"].round(2)
    return mun.sort_values("produccion", ascending=False).reset_index(drop=True)


# =====================================================================
# RESUMEN NARRATIVO (para storytelling)
# =====================================================================
def resumen_matrices(df: pd.DataFrame) -> dict:
    """Genera conteos y ejemplos por cuadrante para la narrativa."""
    cultivos = matriz_cultivos(df)
    municipios = matriz_municipios(df)

    def _top(df_q, col, cuadrante, n=3):
        sub = df_q[df_q["cuadrante"] == cuadrante].head(n)
        return ", ".join(sub[col].astype(str).tolist()) if not sub.empty else "-"

    return {
        "cultivos": {
            "total": len(cultivos),
            "motores": _top(cultivos, "cultivo", "Motor"),
            "consolidados": _top(cultivos, "cultivo", "Consolidado"),
            "emergentes": _top(cultivos, "cultivo", "Emergente"),
            "rezagados": _top(cultivos, "cultivo", "Rezagado"),
            "n_motores": int((cultivos["cuadrante"] == "Motor").sum()),
            "n_consolidados": int((cultivos["cuadrante"] == "Consolidado").sum()),
            "n_emergentes": int((cultivos["cuadrante"] == "Emergente").sum()),
            "n_rezagados": int((cultivos["cuadrante"] == "Rezagado").sum()),
        },
        "municipios": {
            "total": len(municipios),
            "motores": _top(municipios, "municipio", "Motores"),
            "mejora": _top(municipios, "municipio", "Mejora"),
            "potenciales": _top(municipios, "municipio", "Potenciales"),
            "rezagados": _top(municipios, "municipio", "Rezagados"),
            "n_motores": int((municipios["cuadrante"] == "Motores").sum()),
            "n_mejora": int((municipios["cuadrante"] == "Mejora").sum()),
            "n_potenciales": int((municipios["cuadrante"] == "Potenciales").sum()),
            "n_rezagados": int((municipios["cuadrante"] == "Rezagados").sum()),
        },
    }
