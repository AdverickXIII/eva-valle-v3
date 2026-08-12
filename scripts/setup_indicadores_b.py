"""Agrega PARTE B a informe_indicators.py: correlaciones, brechas, dinamica."""
from pathlib import Path

PART_B = '''


# =====================================================================
# 5. CORRELACIONES (Pearson + Spearman)
# =====================================================================
def correlaciones(df):
    """Correlaciones entre area, produccion y rendimiento."""
    pares = [
        ("area_sembrada_ha", "produccion_t", "Area sembrada vs Produccion"),
        ("area_cosechada_ha", "produccion_t", "Area cosechada vs Produccion"),
        ("area_cosechada_ha", "rendimiento_t_ha", "Area cosechada vs Rendimiento"),
        ("produccion_t", "rendimiento_t_ha", "Produccion vs Rendimiento"),
    ]
    registros = []
    for col_x, col_y, nombre in pares:
        valid = df[[col_x, col_y]].dropna()
        valid = valid[(valid[col_x] > 0) & (valid[col_y] > 0)]
        if len(valid) < 5:
            continue
        r_p, p_p = stats.pearsonr(valid[col_x], valid[col_y])
        r_s, p_s = stats.spearmanr(valid[col_x], valid[col_y])
        registros.append({
            "relacion": nombre, "n": len(valid),
            "pearson_r": round(r_p, 3), "pearson_p": round(p_p, 4),
            "spearman_r": round(r_s, 3), "spearman_p": round(p_s, 4),
            "interpretacion": _interpretar_correlacion(r_s),
        })
    return pd.DataFrame(registros)


def _interpretar_correlacion(r):
    a = abs(r)
    if a >= 0.8:
        return "Correlacion muy fuerte"
    if a >= 0.6:
        return "Correlacion fuerte"
    if a >= 0.4:
        return "Correlacion moderada"
    if a >= 0.2:
        return "Correlacion debil"
    return "Sin correlacion significativa"


# =====================================================================
# 6. BRECHAS Y DESIGUALDAD
# =====================================================================
def brechas(df):
    """Indicadores de desigualdad entre municipios."""
    prod_mun = df.groupby("municipio")["produccion_t"].sum()
    prod_mun = prod_mun[prod_mun > 0]
    if len(prod_mun) < 2:
        return {}
    p90, p10 = float(prod_mun.quantile(0.9)), float(prod_mun.quantile(0.1))
    mediana, promedio = float(prod_mun.median()), float(prod_mun.mean())
    maximo, minimo = float(prod_mun.max()), float(prod_mun.min())
    return {
        "ratio_max_min": round(maximo / minimo, 1) if minimo > 0 else float("inf"),
        "ratio_p90_p10": round(p90 / p10, 1) if p10 > 0 else float("inf"),
        "ratio_promedio_mediana": round(promedio / mediana, 2) if mediana > 0 else 0,
        "mediana": round(mediana, 0), "promedio": round(promedio, 0),
        "p90": round(p90, 0), "p10": round(p10, 0),
    }


# =====================================================================
# 7. DINAMICA TEMPORAL AVANZADA
# =====================================================================
def dinamica_temporal(df):
    """CAGR, volatilidad, anos de crecimiento/contraccion por municipio."""
    registros = []
    for m, grupo in df.groupby("municipio"):
        prod_anual = grupo.groupby("ano")["produccion_t"].sum().sort_index()
        anos = list(prod_anual.index)
        if len(anos) < 2:
            continue
        valores = list(prod_anual.values)
        n = anos[-1] - anos[0]
        cagr = ((valores[-1] / valores[0]) ** (1 / n) - 1) * 100 if valores[0] > 0 else 0
        cv = float(np.std(valores) / np.mean(valores) * 100) if np.mean(valores) > 0 else 0
        diffs = np.diff(valores)
        pm3 = pd.Series(valores).rolling(3, min_periods=1).mean().iloc[-1]
        registros.append({
            "municipio": m,
            "prod_2019": round(valores[0], 0), "prod_2025": round(valores[-1], 0),
            "cagr_pct": round(cagr, 1), "volatilidad_pct": round(cv, 1),
            "anos_crecimiento": int((diffs > 0).sum()),
            "anos_contraidos": int((diffs < 0).sum()),
            "prom_movil_3a": round(float(pm3), 0),
        })
    return (pd.DataFrame(registros)
            .sort_values("cagr_pct", ascending=False).reset_index(drop=True))
'''

p = Path("core/analytics/informe_indicators.py")
if not p.exists():
    print("[ERROR] Ejecuta primero: python scripts\\setup_indicadores_a.py")
    raise SystemExit(1)
with p.open("a", encoding="utf-8") as f:
    f.write(PART_B)
print("[OK] Parte B agregada (correlaciones, brechas, dinamica)")
print("Verifica: python -c \"from core.analytics.informe_indicators import *; print('OK')\"")