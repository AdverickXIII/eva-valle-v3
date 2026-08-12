"""Crea core/analytics/informe_indicators.py: motor estadistico del informe tecnico."""
from pathlib import Path

MODULE = '''"""Indicadores avanzados para el informe tecnico EVA Valle 2019-2025."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


# =====================================================================
# 1. LOCATION QUOTIENT (LQ) - Especializacion territorial
# =====================================================================
def location_quotient(df: pd.DataFrame, municipio: str, cultivo: str) -> float:
    """LQ = (participacion del cultivo en municipio) / (participacion del cultivo en dpto).
    LQ > 1.5: alta especializacion | LQ 1-1.5: especializacion moderada | LQ < 1: baja.
    """
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


def tabla_lq(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Top combinaciones municipio-cultivo con mayor LQ."""
    registros = []
    municipios = df["municipio"].unique()
    cultivos = df["cultivo"].unique()
    for m in municipios:
        for c in cultivos:
            lq = location_quotient(df, m, c)
            if lq > 1.0:
                registros.append({"municipio": m, "cultivo": c, "lq": lq})
    result = pd.DataFrame(registros)
    if result.empty:
        return result
    return result.sort_values("lq", ascending=False).head(top_n).reset_index(drop=True)


def interpretar_lq(lq: float) -> str:
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
def shannon_index(share: np.ndarray) -> float:
    """Indice de Shannon: 0 = monocultivo absoluto, ln(n) = diversidad maxima."""
    share = share[share > 0]
    if len(share) == 0:
        return 0.0
    p = share / share.sum()
    return float(-np.sum(p * np.log(p)))


def simpson_index(share: np.ndarray) -> float:
    """Indice de Simpson: 0 = diversidad maxima, 1 = monocultivo absoluto."""
    share = share[share > 0]
    if len(share) == 0:
        return 0.0
    p = share / share.sum()
    return float(np.sum(p ** 2))


def diversificacion_municipal(df: pd.DataFrame) -> pd.DataFrame:
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
            "cultivo_dominante": str(produccion.idxmax()) if n_cultivos > 0 else "-",
            "pct_dominante": round(float(produccion.max() / produccion.sum() * 100), 1)
                             if n_cultivos > 0 else 0.0,
        })
    return pd.DataFrame(registros).sort_values("shannon", ascending=False).reset_index(drop=True)


# =====================================================================
# 3. CONCENTRACION CR4 / CR10
# =====================================================================
def concentracion_cr(df: pd.DataFrame, nivel: str = "municipio") -> dict:
    """CR4 y CR10: porcentaje de produccion en los top 4 y top 10."""
    col = "municipio" if nivel == "municipio" else "cultivo"
    total = df.groupby(col)["produccion_t"].sum().sort_values(ascending=False)
    total_produccion = total.sum()
    cr4 = float(total.head(4).sum() / total_produccion * 100) if total_produccion else 0
    cr10 = float(total.head(10).sum() / total_produccion * 100) if total_produccion else 0
    cr1 = float(total.head(1).sum() / total_produccion * 100) if total_produccion else 0
    return {"cr1": round(cr1, 1), "cr4": round(cr4, 1), "cr10": round(cr10, 1),
            "nivel": nivel}


# =====================================================================
# 4. INDICE DE DESEMPENO AGRICOLA MUNICIPAL (IDAM)
# =====================================================================
def idam(df: pd.DataFrame) -> pd.DataFrame:
    """IDAM: indice compuesto 0-100 por municipio.
    Componentes (pesos):
      - Produccion relativa (25%)
      - Rendimiento relativo (20%)
      - Diversificacion Shannon (20%)
      - Crecimiento 2019-2025 (20%)
      - Estabilidad (baja volatilidad) (15%)
    """
    municipios = df["municipio"].unique()
    registros = []

    for m in municipios:
        df_m = df[df["municipio"] == m]
        prod_total = df_m["produccion_t"].sum()

        # Rendimiento
        cos = df_m["area_cosechada_ha"].sum()
        rend = prod_total / cos if cos > 0 else 0

        # Diversificacion
        prod_por_cultivo = df_m.groupby("cultivo")["produccion_t"].sum()
        prod_por_cultivo = prod_por_cultivo[prod_por_cultivo > 0]
        shannon = shannon_index(prod_por_cultivo.values)

        # Crecimiento (primer vs ultimo ano)
        anos = sorted(df_m["ano"].unique())
        if len(anos) >= 2:
            prod_ini = df_m[df_m["ano"] == anos[0]]["produccion_t"].sum()
            prod_fin = df_m[df_m["ano"] == anos[-1]]["produccion_t"].sum()
            crecimiento = ((prod_fin / prod_ini) - 1) * 100 if prod_ini > 0 else 0
        else:
            crecimiento = 0

        # Estabilidad (1 - coeficiente de variacion anual)
        prod_anual = df_m.groupby("ano")["produccion_t"].sum()
        if len(prod_anual) > 1 and prod_anual.mean() > 0:
            cv = prod_anual.std() / prod_anual.mean()
            estabilidad = max(0, 1 - cv)
        else:
            estabilidad = 0.5

        registros.append({
            "municipio": m,
            "produccion": prod_total,
            "rendimiento": rend,
            "shannon": shannon,
            "crecimiento_pct": crecimiento,
            "estabilidad": estabilidad,
        })

    result = pd.DataFrame(registros)
    if result.empty:
        return result

    # Normalizar cada componente a 0-1
    for col in ["produccion", "rendimiento", "shannon", "crecimiento_pct", "estabilidad"]:
        min_v, max_v = result[col].min(), result[col].max()
        if max_v > min_v:
            result[f"{col}_norm"] = (result[col] - min_v) / (max_v - min_v)
        else:
            result[f"{col}_norm"] = 0.5

    # IDAM ponderado
    result["idam"] = (
        result["produccion_norm"] * 0.25 +
        result["rendimiento_norm"] * 0.20 +
        result["shannon_norm"] * 0.20 +
        result["crecimiento_pct_norm"] * 0.20 +
        result["estabilidad_norm"] * 0.15
    ) * 100

    # Clasificacion
    result["clasificacion"] = pd.cut(
        result["idam"],
        bins=[-1, result["idam"].quantile(0.33), result["idam"].quantile(0.66), 101],
        labels=["Rezagado", "Intermedio", "Lider"]
    ).astype(str)

    return result.sort_values("idam", ascending=False).reset_index(drop=True)


# =====================================================================
# 5. CORRELACIONES (Pearson + Spearman)
# =====================================================================
def correlaciones(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlaciones entre area, produccion y rendimiento."""
    registros = []
    pares = [
        ("area_sembrada_ha", "produccion_t", "Area sembrada vs Produccion"),
        ("area_cosechada_ha", "produccion_t", "Area cosechada vs Produccion"),
        ("area_cosechada_ha", "rendimiento_t_ha", "Area cosechada vs Rendimiento"),
        ("produccion_t", "rendimiento_t_ha", "Produccion vs Rendimiento"),
    ]
    for col_x, col_y, nombre in pares:
        valid = df[[col_x, col_y]].dropna()
        valid = valid[(valid[col_x] > 0) & (valid[col_y] > 0)]
        if len(valid) < 5:
            continue
        r_p, p_p = stats.pearsonr(valid[col_x], valid[col_y])
        r_s, p_s = stats.spearmanr(valid[col_x], valid[col_y])
        registros.append({
            "relacion": nombre,
            "n": len(valid),
            "pearson_r": round(r_p, 3),
            "pearson_p": round(p_p, 4),
            "spearman_r": round(r_s, 3),
            "spearman_p": round(p_s, 4),
            "interpretacion": _interpretar_correlacion(r_s),
        })
    return pd.DataFrame(registros)


def _interpretar_correlacion(r: float) -> str:
    abs_r = abs(r)
    if abs_r >= 0.8:
        return "Correlacion muy fuerte"
    if abs_r >= 0.6:
        return "Correlacion fuerte"
    if abs_r >= 0.4:
        return "Correlacion moderada"
    if abs_r >= 0.2:
        return "Correlacion debil"
    return "Sin correlacion significativa"


# =====================================================================
# 6. BRECHAS Y DESIGUALDAD
# =====================================================================
def brechas(df: pd.DataFrame) -> dict:
    """Indicadores de desigualdad entre municipios."""
    prod_mun = df.groupby("municipio")["produccion_t"].sum()
    prod_mun = prod_mun[prod_mun > 0]
    if len(prod_mun) < 2:
        return {}
    p90 = float(prod_mun.quantile(0.9))
    p10 = float(prod_mun.quantile(0.1))
    mediana = float(prod_mun.median())
    promedio = float(prod_mun.mean())
    maximo = float(prod_mun.max())
    minimo = float(prod_mun.min())
    return {
        "ratio_max_min": round(maximo / minimo, 1) if minimo > 0 else float("inf"),
        "ratio_p90_p10": round(p90 / p10, 1) if p10 > 0 else float("inf"),
        "ratio_promedio_mediana": round(promedio / mediana, 2) if mediana > 0 else 0,
        "mediana": round(mediana, 0),
        "promedio": round(promedio, 0),
        "p90": round(p90, 0),
        "p10": round(p10, 0),
    }


# =====================================================================
# 7. DINAMICA TEMPORAL AVANZADA
# =====================================================================
def dinamica_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """CAGR, volatilidad, anos de crecimiento/contraccion por municipio."""
    registros = []
    for m, grupo in df.groupby("municipio"):
        prod_anual = grupo.groupby("ano")["produccion_t"].sum().sort_index()
        anos = list(prod_anual.index)
        if len(anos) < 2:
            continue
        valores = list(prod_anual.values)
        n = anos[-1] - anos[0]

        # CAGR
        if valores[0] > 0 and n > 0:
            cagr = ((valores[-1] / valores[0]) ** (1 / n) - 1) * 100
        else:
            cagr = 0

        # Volatilidad (CV)
        cv = float(np.std(valores) / np.mean(valores) * 100) if np.mean(valores) > 0 else 0

        # Anos de crecimiento/contraccion
        diffs = np.diff(valores)
        crecimientos = int((diffs > 0).sum())
        contracciones = int((diffs < 0).sum())

        # Promedio movil 3 anos
        pm3 = pd.Series(valores).rolling(3, min_periods=1).mean().iloc[-1]

        registros.append({
            "municipio": m,
            "prod_2019": round(valores[0], 0),
            "prod_2025": round(valores[-1], 0),
            "cagr_pct": round(cagr, 1),
            "volatilidad_pct":