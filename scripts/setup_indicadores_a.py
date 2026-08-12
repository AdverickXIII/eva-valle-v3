"""Crea informe_indicators.py PARTE A: LQ, diversificacion, CR, IDAM."""
from pathlib import Path

PART_A = '''"""Indicadores avanzados para el informe tecnico EVA Valle 2019-2025."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


# =====================================================================
# 1. LOCATION QUOTIENT (LQ) - Especializacion territorial
# =====================================================================
def location_quotient(df, municipio, cultivo):
    """LQ = (participacion cultivo en municipio) / (participacion cultivo en dpto)."""
    df_m = df[df["municipio"] == municipio]
    df_c = df[df["cultivo"] == cultivo]
    total_m = df_m["produccion_t"].sum()
    total_dpto = df["produccion_t"].sum()
    if total_m == 0 or total_dpto == 0:
        return 0.0
    part_municipio = df_m[df_m["cultivo"] == cultivo]["produccion_t"].sum() / total_m
    part_dpto = df_c["produccion_t"].sum() / total_dpto
    if part_dpto == 0:
        return 0.0
    return round(part_municipio / part_dpto, 2)


def tabla_lq(df, top_n=20):
    """Top combinaciones municipio-cultivo con mayor LQ."""
    registros = []
    for m in df["municipio"].unique():
        for c in df["cultivo"].unique():
            lq = location_quotient(df, m, c)
            if lq > 1.0:
                registros.append({"municipio": m, "cultivo": c, "lq": lq})
    result = pd.DataFrame(registros)
    if result.empty:
        return result
    return result.sort_values("lq", ascending=False).head(top_n).reset_index(drop=True)


def interpretar_lq(lq):
    if lq >= 2.0:
        return "Especializacion muy alta"
    if lq >= 1.5:
        return "Alta especializacion"
    if lq >= 1.0:
        return "Especializacion moderada"
    return "Sin especializacion"


# =====================================================================
# 2. INDICES DE DIVERSIFICACION (Shannon, Simpson)
# =====================================================================
def shannon_index(share):
    """0 = monocultivo absoluto, ln(n) = diversidad maxima."""
    share = np.asarray(share, dtype=float)
    share = share[share > 0]
    if len(share) == 0:
        return 0.0
    p = share / share.sum()
    return float(-np.sum(p * np.log(p)))


def simpson_index(share):
    """0 = diversidad maxima, 1 = monocultivo absoluto."""
    share = np.asarray(share, dtype=float)
    share = share[share > 0]
    if len(share) == 0:
        return 0.0
    p = share / share.sum()
    return float(np.sum(p ** 2))


def diversificacion_municipal(df):
    """Shannon y Simpson por municipio."""
    registros = []
    for m, grupo in df.groupby("municipio"):
        produccion = grupo.groupby("cultivo")["produccion_t"].sum()
        produccion = produccion[produccion > 0]
        n_cultivos = len(produccion)
        registros.append({
            "municipio": m,
            "n_cultivos": n_cultivos,
            "shannon": round(shannon_index(produccion.values), 3),
            "simpson": round(simpson_index(produccion.values), 3),
            "cultivo_dominante": str(produccion.idxmax()) if n_cultivos else "-",
            "pct_dominante": round(float(produccion.max() / produccion.sum() * 100), 1)
                             if n_cultivos else 0.0,
        })
    return (pd.DataFrame(registros)
            .sort_values("shannon", ascending=False).reset_index(drop=True))


# =====================================================================
# 3. CONCENTRACION CR1 / CR4 / CR10
# =====================================================================
def concentracion_cr(df, nivel="municipio"):
    """Porcentaje de produccion en los top 1, 4 y 10."""
    col = "municipio" if nivel == "municipio" else "cultivo"
    total = df.groupby(col)["produccion_t"].sum().sort_values(ascending=False)
    total_produccion = total.sum()
    if not total_produccion:
        return {"cr1": 0, "cr4": 0, "cr10": 0, "nivel": nivel}
    return {
        "cr1": round(float(total.head(1).sum() / total_produccion * 100), 1),
        "cr4": round(float(total.head(4).sum() / total_produccion * 100), 1),
        "cr10": round(float(total.head(10).sum() / total_produccion * 100), 1),
        "nivel": nivel,
    }


# =====================================================================
# 4. INDICE DE DESEMPENO AGRICOLA MUNICIPAL (IDAM)
# =====================================================================
def idam(df):
    """IDAM 0-100: produccion 25%, rendimiento 20%, diversificacion 20%,
    crecimiento 20%, estabilidad 15%."""
    registros = []
    for m, df_m in df.groupby("municipio"):
        prod_total = df_m["produccion_t"].sum()
        cos = df_m["area_cosechada_ha"].sum()
        rend = prod_total / cos if cos > 0 else 0
        prod_cultivo = df_m.groupby("cultivo")["produccion_t"].sum()
        prod_cultivo = prod_cultivo[prod_cultivo > 0]
        shannon = shannon_index(prod_cultivo.values)
        anos = sorted(df_m["ano"].unique())
        if len(anos) >= 2:
            p_ini = df_m[df_m["ano"] == anos[0]]["produccion_t"].sum()
            p_fin = df_m[df_m["ano"] == anos[-1]]["produccion_t"].sum()
            crecimiento = ((p_fin / p_ini) - 1) * 100 if p_ini > 0 else 0
        else:
            crecimiento = 0
        prod_anual = df_m.groupby("ano")["produccion_t"].sum()
        if len(prod_anual) > 1 and prod_anual.mean() > 0:
            estabilidad = max(0, 1 - prod_anual.std() / prod_anual.mean())
        else:
            estabilidad = 0.5
        registros.append({"municipio": m, "produccion": prod_total,
                          "rendimiento": rend, "shannon": shannon,
                          "crecimiento_pct": crecimiento, "estabilidad": estabilidad})

    result = pd.DataFrame(registros)
    if result.empty:
        return result
    for col in ["produccion", "rendimiento", "shannon", "crecimiento_pct", "estabilidad"]:
        mn, mx = result[col].min(), result[col].max()
        result[f"{col}_norm"] = ((result[col] - mn) / (mx - mn)) if mx > mn else 0.5
    result["idam"] = (result["produccion_norm"] * 0.25 +
                      result["rendimiento_norm"] * 0.20 +
                      result["shannon_norm"] * 0.20 +
                      result["crecimiento_pct_norm"] * 0.20 +
                      result["estabilidad_norm"] * 0.15) * 100
    q33, q66 = result["idam"].quantile(0.33), result["idam"].quantile(0.66)
    result["clasificacion"] = pd.cut(result["idam"], bins=[-1, q33, q66, 101],
                                     labels=["Rezagado", "Intermedio", "Lider"]).astype(str)
    return result.sort_values("idam", ascending=False).reset_index(drop=True)
'''

Path("core/analytics/informe_indicators.py").write_text(PART_A, encoding="utf-8")
print("[OK] Parte A creada (LQ, Shannon/Simpson, CR, IDAM)")
print("Sigue: python scripts\\setup_indicadores_b.py")