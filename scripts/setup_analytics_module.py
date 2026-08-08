"""
Setup script: genera los 13 archivos del modulo core/analytics/.
Migracion del Notebook 4 (Analisis Descriptivo Profundo y Economia Espacial).
Incluye la CORRECCION CRITICA del Gini negativo.
Ejecutar una sola vez: python scripts/setup_analytics_module.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: core/analytics/descriptive.py
# ═══════════════════════════════════════════════════════════
DESCRIPTIVE = '''"""
Analisis 4.3: Estadistica descriptiva profunda.
Calcula momentos, percentiles y Coeficiente de Variacion para las 4 metricas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.descriptive")

METRICAS = ["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]


def calculate_descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula momentos, percentiles y CV para las 4 metricas productivas.

    Args:
        df: DataFrame con las columnas de metricas.

    Returns:
        DataFrame con una fila por metrica y columnas:
        variable, n, media, mediana, desv_std, cv, asimetria, curtosis,
        p10, p25, p75, p90, iqr.
    """
    resultados = []
    for col in METRICAS:
        if col not in df.columns:
            log.warning("Columna '%s' no encontrada. Omitiendo.", col)
            continue
        s = df[col].dropna()
        if len(s) == 0:
            continue
        media = s.mean()
        resultados.append({
            "variable": col,
            "n": len(s),
            "media": media,
            "mediana": s.median(),
            "desv_std": s.std(),
            "cv": (s.std() / media) if media != 0 else np.nan,
            "asimetria": s.skew(),
            "curtosis": s.kurtosis(),
            "p10": s.quantile(0.10),
            "p25": s.quantile(0.25),
            "p75": s.quantile(0.75),
            "p90": s.quantile(0.90),
            "iqr": s.quantile(0.75) - s.quantile(0.25),
        })

    log.info("Estadistica descriptiva calculada para %d metricas.", len(resultados))
    return pd.DataFrame(resultados)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: core/analytics/distributions.py
# ═══════════════════════════════════════════════════════════
DISTRIBUTIONS = '''"""
Analisis 4.4: Ajuste de distribuciones.
Prueba KS-test para Normal, Log-Normal y Gamma sobre el rendimiento.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.distributions")


def fit_distributions(df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Prueba KS-test para Normal, Log-Normal y Gamma sobre rendimiento_t_ha.

    Args:
        df: DataFrame con la columna rendimiento_t_ha.
        alpha: Nivel de significancia (default 0.05).

    Returns:
        DataFrame con columnas: distribucion, statistic_ks, p_value,
        rechaza_H0.
    """
    if "rendimiento_t_ha" not in df.columns:
        log.warning("Columna rendimiento_t_ha no encontrada.")
        return pd.DataFrame()

    s = df["rendimiento_t_ha"].dropna()
    s = s[s > 0]  # Lognormal y Gamma no aceptan ceros

    if len(s) < 20:
        log.warning("Muestra insuficiente (%d < 20). Omitiendo ajuste.", len(s))
        return pd.DataFrame()

    # Normal (estandarizada)
    s_norm = (s - s.mean()) / s.std()
    ks_norm = sp_stats.kstest(s_norm, "norm")

    # Log-Normal (log de los datos, estandarizado)
    s_log = np.log(s)
    s_log_norm = (s_log - s_log.mean()) / s_log.std()
    ks_lognorm = sp_stats.kstest(s_log_norm, "norm")

    # Gamma (ajuste de parametros)
    params_gamma = sp_stats.gamma.fit(s, floc=0)
    ks_gamma = sp_stats.kstest(s, "gamma", args=params_gamma)

    resultados = [
        {"distribucion": "Normal", "statistic_ks": ks_norm.statistic, "p_value": ks_norm.pvalue},
        {"distribucion": "Log-Normal", "statistic_ks": ks_lognorm.statistic, "p_value": ks_lognorm.pvalue},
        {"distribucion": "Gamma", "statistic_ks": ks_gamma.statistic, "p_value": ks_gamma.pvalue},
    ]

    res_df = pd.DataFrame(resultados)
    res_df[f"rechaza_H0 (alpha={alpha})"] = res_df["p_value"] < alpha

    log.info("Ajuste de distribuciones completado (n=%d).", len(s))
    return res_df
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: core/analytics/outliers.py
# ═══════════════════════════════════════════════════════════
OUTLIERS = '''"""
Analisis 4.5: Deteccion de outliers multivariados.
Isolation Forest sobre las 4 metricas para detectar anomalias conjuntas.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from config.settings import settings
from core.logging import get_logger

log = get_logger("core.analytics.outliers")

METRICAS = ["area_sembrada_ha", "area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]


def detect_multivariate_outliers(
    df: pd.DataFrame,
    contamination: float = 0.02,
) -> pd.DataFrame:
    """
    Detecta anomalias multivariadas con Isolation Forest.

    Args:
        df: DataFrame con las 4 metricas y columnas de contexto.
        contamination: Proporcion esperada de outliers (default 2%).

    Returns:
        DataFrame con los registros anomalos y sus metricas.
    """
    df_clean = df.dropna(subset=METRICAS).copy()
    if len(df_clean) < 50:
        log.warning("Muestra insuficiente (%d < 50). Omitiendo outliers.", len(df_clean))
        return pd.DataFrame()

    iso = IsolationForest(
        contamination=contamination,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=-1,
    )
    df_clean["es_outlier"] = iso.fit_predict(df_clean[METRICAS])
    outliers = df_clean[df_clean["es_outlier"] == -1].copy()
    outliers["tipo_anomalia"] = "Anomalia multivariada (Isolation Forest)"

    pct = (len(outliers) / len(df_clean)) * 100
    log.info("Outliers multivariados detectados: %d (%.1f%%)", len(outliers), pct)

    # Retornar columnas de contexto + metricas
    cols_contexto = ["id_registro", "municipio", "cultivo", "periodo"]
    cols_disponibles = [c for c in cols_contexto if c in outliers.columns]
    return outliers[cols_disponibles + METRICAS + ["tipo_anomalia"]]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: core/analytics/concentration.py
# ⚠️ CORRECCIÓN CRÍTICA DEL GINI NEGATIVO
# ═══════════════════════════════════════════════════════════
CONCENTRATION = '''"""
Analisis 4.6: Concentracion (Gini, HHI, Lorenz).

⚠️ CORRECCION CRITICA (Fase 0 - Bug P2):
El codigo original ordenaba los datos de forma DESCENDENTE (ascending=False),
lo cual producia un Gini NEGATIVO (-0.966). La curva de Lorenz requiere
ordenamiento ASCENDENTE (ascending=True) para acumular desde los mas
pequenos hacia los mas grandes.

Referencia: https://en.wikipedia.org/wiki/Lorenz_curve
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.concentration")


def _trapezoid(y: np.ndarray, x: np.ndarray) -> float:
    """
    Calcula el area bajo la curva usando la regla del trapecio.
    Compatible con NumPy 1.x (trapz) y 2.x (trapezoid).
    """
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def calculate_concentration(
    df: pd.DataFrame,
    grupo: str = "cultivo",
    valor: str = "produccion_t",
) -> dict[str, Any]:
    """
    Calcula HHI, Gini y datos para curva de Lorenz.

    ⚠️ CORRECCION: Los datos se ordenan ASCENDENTE (ascending=True)
    para que la curva de Lorenz acumule correctamente desde los mas
    pequenos hacia los mas grandes. El codigo original usaba
    ascending=False, produciendo Gini negativo.

    Args:
        df: DataFrame con las columnas de agrupacion y valor.
        grupo: Columna por la que agrupar (default 'cultivo').
        valor: Columna de valor a concentrar (default 'produccion_t').

    Returns:
        Diccionario con: grupo_analisis, variable, hhi, gini,
        n_entidades, top1_share, top3_share, lorenz_x, lorenz_y.
    """
    if grupo not in df.columns or valor not in df.columns:
        log.warning("Columnas '%s' o '%s' no encontradas.", grupo, valor)
        return {}

    # ⚠️ CORRECCION: ascending=True (antes era ascending=False → Gini negativo)
    agrupado = df.groupby(grupo)[valor].sum().sort_values(ascending=True)

    if agrupado.sum() == 0:
        log.warning("Suma total de '%s' es cero. No se puede calcular concentracion.", valor)
        return {}

    shares = agrupado / agrupado.sum()

    # HHI: suma de cuadrados de las participaciones, escalado a 10,000
    hhi = float((shares ** 2).sum() * 10_000)

    # Curva de Lorenz y Gini
    cum_shares = shares.cumsum()
    lorenz_x = np.arange(1, len(cum_shares) + 1) / len(cum_shares)
    lorenz_y = cum_shares.values
    auc = _trapezoid(lorenz_y, lorenz_x)
    gini = float(1 - 2 * auc)

    # Validar que el Gini este en el rango esperado [0, 1]
    if gini < 0 or gini > 1:
        log.warning(
            "Gini fuera de rango [0,1]: %.3f. Verificar ordenamiento de datos.",
            gini,
        )

    # Para top1 y top3, necesitamos orden descendente
    shares_desc = shares.sort_values(ascending=False)

    resultado = {
        "grupo_analisis": grupo,
        "variable": valor,
        "hhi": hhi,
        "gini": gini,
        "n_entidades": len(shares),
        "top1_share": float(shares_desc.iloc[0] * 100),
        "top3_share": float(shares_desc.head(3).sum() * 100),
        "lorenz_x": lorenz_x.tolist(),
        "lorenz_y": lorenz_y.tolist(),
    }

    log.info(
        "Concentracion (%s por %s): HHI=%.0f, Gini=%.3f, Top1=%.1f%%",
        valor, grupo, hhi, gini, resultado["top1_share"],
    )
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: core/analytics/time_series.py
# ═══════════════════════════════════════════════════════════
TIME_SERIES = '''"""
Analisis 4.7: Series de tiempo.
Descomposicion STL y prueba Dickey-Fuller sobre produccion total semestral.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.time_series")


def analyze_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descomposicion STL y prueba Dickey-Fuller sobre produccion total.

    Args:
        df: DataFrame con columnas periodo y produccion_t.

    Returns:
        DataFrame con resultados de la prueba Dickey-Fuller.
    """
    if "periodo" not in df.columns or "produccion_t" not in df.columns:
        log.warning("Columnas periodo o produccion_t no encontradas.")
        return pd.DataFrame()

    # Agregar produccion por periodo
    df_temp = df.groupby("periodo")["produccion_t"].sum().reset_index()

    # Ordenar cronologicamente
    df_temp["orden"] = df_temp["periodo"].str[:4].astype(int) + np.where(
        df_temp["periodo"].str.len() == 5,
        np.where(df_temp["periodo"].str[-1] == "A", 0.25, 0.75),
        0.5,
    )
    df_temp = df_temp.sort_values("orden")

    resultados = []
    if len(df_temp) >= 8:
        try:
            from statsmodels.tsa.seasonal import STL
            from statsmodels.tsa.stattools import adfuller

            stl = STL(df_temp["produccion_t"], period=2, robust=True)
            res = stl.fit()
            df_temp["tendencia"] = res.trend
            df_temp["estacional"] = res.seasonal
            df_temp["residuo"] = res.resid

            adf_stat, adf_pval, _, _, _, _ = adfuller(df_temp["produccion_t"])
            resultados.append({
                "test": "Dickey-Fuller (Produccion Total)",
                "statistic": adf_stat,
                "p_value": adf_pval,
                "es_estacionaria": adf_pval < 0.05,
            })
            log.info("STL y Dickey-Fuller completados (p=%.4f).", adf_pval)
        except Exception as e:
            log.warning("STL fallo (muestra pequena): %s", e)
    else:
        log.warning("Serie muy corta (%d < 8). Omitiendo STL.", len(df_temp))

    return pd.DataFrame(resultados)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: core/analytics/seasonality.py
# ═══════════════════════════════════════════════════════════
SEASONALITY = '''"""
Analisis 4.8: Estacionalidad semestral.
Wilcoxon signed-rank test para A vs B en cultivos transitorios.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.seasonality")


def test_seasonality_ab(df: pd.DataFrame, min_pares: int = 5) -> pd.DataFrame:
    """
    Wilcoxon signed-rank test para comparar semestres A vs B.

    Args:
        df: DataFrame con columnas ciclo_del_cultivo, periodo, cultivo,
            ano, produccion_t.
        min_pares: Minimo de pares A/B por cultivo (default 5).

    Returns:
        DataFrame con resultados por cultivo, ordenado por p_value.
    """
    required_cols = ["ciclo_del_cultivo", "periodo", "cultivo", "ano", "produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para estacionalidad: %s", faltantes)
        return pd.DataFrame()

    df_trans = df[df["ciclo_del_cultivo"] == "Transitorio"].copy()
    df_trans["semestre"] = df_trans["periodo"].str[-1].str.upper()
    df_trans = df_trans[df_trans["semestre"].isin(["A", "B"])]

    # Pivotar para obtener la produccion total de cada cultivo por ano y semestre
    pivot = df_trans.groupby(["cultivo", "ano", "semestre"])["produccion_t"].sum().reset_index()
    pivot_tab = pivot.pivot_table(index=["cultivo", "ano"], columns="semestre", values="produccion_t")

    resultados = []
    for cultivo in pivot_tab.index.get_level_values(0).unique():
        datos_cultivo = pivot_tab.loc[cultivo].dropna(subset=["A", "B"])
        if len(datos_cultivo) >= min_pares:
            stat, pval = sp_stats.wilcoxon(datos_cultivo["A"], datos_cultivo["B"])
            media_a = datos_cultivo["A"].mean()
            media_b = datos_cultivo["B"].mean()
            dif_pct = ((media_b - media_a) / media_a) * 100 if media_a != 0 else np.nan
            resultados.append({
                "cultivo": cultivo,
                "pares_analizados": len(datos_cultivo),
                "media_A": media_a,
                "media_B": media_b,
                "dif_porcent": dif_pct,
                "statistic_wilcoxon": stat,
                "p_value": pval,
                "diferencia_significativa": pval < 0.05,
            })

    if not resultados:
        log.info("No se encontraron pares A/B suficientes para el test.")
        return pd.DataFrame()

    log.info("Estacionalidad A vs B: %d cultivos analizados.", len(resultados))
    return pd.DataFrame(resultados).sort_values("p_value")
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: core/analytics/spatial.py
# ═══════════════════════════════════════════════════════════
SPATIAL = '''"""
Analisis 4.9 y 4.10: Economia espacial.
Location Quotient (LQ) e Indice Shannon-Wiener de diversificacion.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.spatial")


def calculate_location_quotient(df: pd.DataFrame) -> pd.DataFrame:
    """
    Location Quotient basado en area sembrada por grupo de cultivo y municipio.

    LQ > 1 indica especializacion del municipio en ese grupo de cultivo
    respecto al promedio departamental.

    Args:
        df: DataFrame con columnas codigo_dane_municipio, grupo_cultivo,
            area_sembrada_ha.

    Returns:
        DataFrame con columnas: codigo_dane_municipio, grupo_cultivo, LQ.
    """
    required_cols = ["codigo_dane_municipio", "grupo_cultivo", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para LQ: %s", faltantes)
        return pd.DataFrame()

    muni_grupo = (
        df.groupby(["codigo_dane_municipio", "grupo_cultivo"])["area_sembrada_ha"]
        .sum()
        .unstack(fill_value=0)
    )
    valle_grupo = df.groupby("grupo_cultivo")["area_sembrada_ha"].sum()

    # Salvaguarda: evitar division por cero
    valle_grupo_safe = valle_grupo.replace(0, 1e-8)
    muni_total_safe = muni_grupo.sum(axis=1).replace(0, 1e-8)

    lq_df = (
        (muni_grupo / muni_total_safe.values[:, None])
        / (valle_grupo_safe / valle_grupo_safe.sum())
    )

    resultado = lq_df.reset_index().melt(
        id_vars="codigo_dane_municipio",
        var_name="grupo_cultivo",
        value_name="LQ",
    )
    log.info("LQ calculado: %d combinaciones municipio x grupo.", len(resultado))
    return resultado


def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Indice de Shannon-Wiener de diversificacion por municipio.

    Mayor indice = menor dependencia de un solo cultivo.

    Args:
        df: DataFrame con columnas municipio, area_sembrada_ha.

    Returns:
        DataFrame con columnas: municipio, cultivos_distintos,
        shannon_wiener, area_total. Ordenado por shannon_wiener desc.
    """
    required_cols = ["municipio", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para Shannon: %s", faltantes)
        return pd.DataFrame()

    def shannon_index(s: pd.Series) -> float:
        p = s / s.sum()
        p = p[p > 0]
        return float(-np.sum(p * np.log(p)))

    diversidad = df.groupby("municipio")["area_sembrada_ha"].agg(
        cultivos_distintos="nunique",
        shannon_wiener=shannon_index,
        area_total="sum",
    ).reset_index()

    resultado = diversidad.sort_values("shannon_wiener", ascending=False)
    log.info("Shannon-Wiener calculado para %d municipios.", len(resultado))
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 8: core/analytics/elasticity.py
# ═══════════════════════════════════════════════════════════
ELASTICITY = '''"""
Analisis 4.11: Elasticidades y analisis de eficiencia productiva.
Regresion log-log OLS de produccion vs area sembrada.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.elasticity")


def calculate_elasticity(df: pd.DataFrame, min_observaciones: int = 30) -> dict[str, Any]:
    """
    Elasticidad produccion-area (Log-Log OLS).

    Args:
        df: DataFrame con columnas produccion_t y area_sembrada_ha.
        min_observaciones: Minimo de observaciones validas (default 30).

    Returns:
        Diccionario con: elasticidad, r_cuadrado, p_value, n_regresion.
        Si hay error, retorna {"error": "mensaje"}.
    """
    required_cols = ["produccion_t", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    df_reg = df[(df["produccion_t"] > 0) & (df["area_sembrada_ha"] > 0)].copy()
    if len(df_reg) < min_observaciones:
        return {"error": f"Insuficientes datos > 0 para regresion log-log ({len(df_reg)} < {min_observaciones})"}

    df_reg["log_prod"] = np.log(df_reg["produccion_t"])
    df_reg["log_area"] = np.log(df_reg["area_sembrada_ha"])

    slope, intercept, r_value, p_value, std_err = sp_stats.linregress(
        df_reg["log_area"], df_reg["log_prod"]
    )

    resultado = {
        "elasticidad": float(slope),
        "r_cuadrado": float(r_value ** 2),
        "p_value": float(p_value),
        "n_regresion": len(df_reg),
    }

    log.info(
        "Elasticidad calculada: %.3f (R2=%.3f, n=%d)",
        resultado["elasticidad"], resultado["r_cuadrado"], len(df_reg),
    )
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 9: core/analytics/inferential.py
# ═══════════════════════════════════════════════════════════
INFERENTIAL = '''"""
Analisis 4.12: Analisis estadistico inferencial.
Kruskal-Wallis: ¿El rendimiento difiere entre municipios?
"""
from __future__ import annotations

import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.analytics.inferential")


def run_inferential_test(
    df: pd.DataFrame,
    min_por_grupo: int = 5,
    min_grupos: int = 3,
) -> pd.DataFrame:
    """
    Kruskal-Wallis: ¿El rendimiento difiere significativamente entre municipios?

    Args:
        df: DataFrame con columnas municipio y rendimiento_t_ha.
        min_por_grupo: Minimo de observaciones por grupo (default 5).
        min_grupos: Minimo de grupos para ejecutar el test (default 3).

    Returns:
        DataFrame con el resultado del test.
    """
    required_cols = ["municipio", "rendimiento_t_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para Kruskal-Wallis: %s", faltantes)
        return pd.DataFrame()

    grupos = [
        group["rendimiento_t_ha"].dropna().values
        for name, group in df.groupby("municipio")
        if len(group) > min_por_grupo
    ]

    if len(grupos) < min_grupos:
        log.warning("Menos de %d grupos con datos suficientes.", min_grupos)
        return pd.DataFrame()

    stat, pval = sp_stats.kruskal(*grupos)

    resultado = pd.DataFrame([{
        "test": "Kruskal-Wallis (Rendimiento por Municipio)",
        "statistic_H": stat,
        "p_value": pval,
        "hay_diferencia_significativa": pval < 0.05,
    }])

    log.info("Kruskal-Wallis completado (H=%.2f, p=%.2e).", stat, pval)
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 10: core/analytics/growth.py
# ═══════════════════════════════════════════════════════════
GROWTH = '''"""
Analisis 4.13: CAGR y dinamica de crecimiento por cultivo.
Tasa de Crecimiento Anual Compuesta (2019 a 2024).
"""
from __future__ import annotations

import pandas as pd

from core.logging import get_logger

log = get_logger("core.analytics.growth")


def calculate_cagr(df: pd.DataFrame) -> pd.DataFrame:
    """
    CAGR por cultivo entre el primer y ultimo ano del dataset.

    Args:
        df: DataFrame con columnas ano, cultivo, produccion_t.

    Returns:
        DataFrame con columnas: cultivo, prod_inicio, prod_fin, cagr.
        Ordenado por cagr descendente.
    """
    required_cols = ["ano", "cultivo", "produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para CAGR: %s", faltantes)
        return pd.DataFrame()

    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2:
        log.warning("Menos de 2 anos en el dataset. No se puede calcular CAGR.")
        return pd.DataFrame()

    ano_ini, ano_fin = min(anos), max(anos)
    n_years = ano_fin - ano_ini

    ini = df[df["ano"] == ano_ini].groupby("cultivo")["produccion_t"].sum()
    fin = df[df["ano"] == ano_fin].groupby("cultivo")["produccion_t"].sum()

    cagr_df = pd.DataFrame({"prod_inicio": ini, "prod_fin": fin}).dropna()

    # Evitar division por cero si prod_inicio es 0
    cagr_df = cagr_df[cagr_df["prod_inicio"] > 0]

    cagr_df["cagr"] = (
        (cagr_df["prod_fin"] / cagr_df["prod_inicio"]) ** (1 / n_years) - 1
    ) * 100

    resultado = cagr_df.reset_index().sort_values("cagr", ascending=False)
    log.info("CAGR calculado para %d cultivos (%d-%d).", len(resultado), ano_ini, ano_fin)
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 11: core/analytics/ex_cana.py
# ═══════════════════════════════════════════════════════════
EX_CANA = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 12: core/analytics/pipeline.py
# ═══════════════════════════════════════════════════════════
PIPELINE = '''"""
Orquestador del Paso 4: Analisis Descriptivo Profundo.

Migrado del Notebook 4 (funcion ejecutar_paso4).
Mejoras:
- Sin prints (solo logging)
- Configuracion desde config.settings
- Usa adaptadores de storage (CsvStorage)
- Retorna dict de artefactos en vez de imprimir
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.analytics.concentration import calculate_concentration
from core.analytics.descriptive import calculate_descriptive_statistics
from core.analytics.distributions import fit_distributions
from core.analytics.elasticity import calculate_elasticity
from core.analytics.ex_cana import analyze_ex_cana
from core.analytics.growth import calculate_cagr
from core.analytics.inferential import run_inferential_test
from core.analytics.outliers import detect_multivariate_outliers
from core.analytics.seasonality import test_seasonality_ab
from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity
from core.analytics.time_series import analyze_time_series
from core.logging import get_logger, log_section

log = get_logger("core.analytics.pipeline")

_csv_storage = CsvStorage()


def run_all_analytics(
    input_path: Path | None = None,
    export_artifacts: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta los 12 analisis descriptivos del Paso 4.

    Args:
        input_path: Ruta al CSV con modelo conceptual. Si es None, usa
            la ruta por defecto.
        export_artifacts: Si True, exporta los artefactos a CSV.

    Returns:
        Diccionario con los 12 artefactos generados.

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
    """
    log_section("PASO 4 - ANALISIS DESCRIPTIVO PROFUNDO")

    if input_path is None:
        input_path = (
            settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
        )

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d registros", len(df))

    artefactos: dict[str, Any] = {}

    # 4.3 Estadistica descriptiva profunda
    log.info("Ejecutando 4.3 Estadistica descriptiva...")
    artefactos["4_3_descriptiva_profunda"] = calculate_descriptive_statistics(df)

    # 4.4 Ajuste de distribuciones
    log.info("Ejecutando 4.4 Ajuste de distribuciones...")
    artefactos["4_4_ajuste_distribuciones"] = fit_distributions(df)

    # 4.5 Outliers multivariados
    log.info("Ejecutando 4.5 Outliers multivariados...")
    artefactos["4_5_outliers_multivariados"] = detect_multivariate_outliers(df)

    # 4.6 Concentracion (GINI CORREGIDO)
    log.info("Ejecutando 4.6 Concentracion (Gini corregido)...")
    conc = calculate_concentration(df)
    artefactos["4_6_concentracion"] = pd.DataFrame([conc])

    # 4.7 Series de tiempo
    log.info("Ejecutando 4.7 Series de tiempo...")
    artefactos["4_7_series_tiempo"] = analyze_time_series(df)

    # 4.8 Estacionalidad A vs B
    log.info("Ejecutando 4.8 Estacionalidad A vs B...")
    artefactos["4_8_estacionalidad_ab"] = test_seasonality_ab(df)

    # 4.9 Location Quotient
    log.info("Ejecutando 4.9 Location Quotient...")
    artefactos["4_9_location_quotient"] = calculate_location_quotient(df)

    # 4.10 Shannon-Wiener
    log.info("Ejecutando 4.10 Shannon-Wiener...")
    artefactos["4_10_shannon_wiener"] = calculate_shannon_diversity(df)

    # 4.11 Elasticidades
    log.info("Ejecutando 4.11 Elasticidades...")
    elasticidad = calculate_elasticity(df)
    artefactos["4_11_elasticidades"] = pd.DataFrame([elasticidad])

    # 4.12 Inferencial
    log.info("Ejecutando 4.12 Kruskal-Wallis...")
    artefactos["4_12_inferencial"] = run_inferential_test(df)

    # 4.13 CAGR
    log.info("Ejecutando 4.13 CAGR...")
    artefactos["4_13_cagr_cultivos"] = calculate_cagr(df)

    # 4.14 Ex-Cana
    log.info("Ejecutando 4.14 Ex-Cana...")
    ex_cana = analyze_ex_cana(df)
    artefactos["4_14_ex_cana"] = pd.DataFrame([ex_cana])

    # Exportar artefactos
    if export_artifacts:
        log.info("Exportando %d artefactos...", len(artefactos))
        for nombre, df_art in artefactos.items():
            if isinstance(df_art, pd.DataFrame) and not df_art.empty:
                ruta = settings.OUTPUTS_TABLES_PATH / f"{nombre}.csv"
                _csv_storage.write_csv(df_art, ruta)

    log.info("Paso 4 completado. %d artefactos generados.", len(artefactos))
    return artefactos
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 13: core/analytics/__init__.py (FACHADA)
# ═══════════════════════════════════════════════════════════
ANALYTICS_INIT = '''"""
Modulo de analisis descriptivo profundo del proyecto eva-valle-v3.0.

Fachada que orquesta los 12 analisis del Paso 4.

Uso:
    from core.analytics import run_all_analytics, calculate_concentration

    # Ejecutar los 12 analisis
    artefactos = run_all_analytics()

    # O ejecutar un analisis individual
    conc = calculate_concentration(df)
"""
from core.analytics.pipeline import run_all_analytics
from core.analytics.descriptive import calculate_descriptive_statistics
from core.analytics.distributions import fit_distributions
from core.analytics.outliers import detect_multivariate_outliers
from core.analytics.concentration import calculate_concentration
from core.analytics.time_series import analyze_time_series
from core.analytics.seasonality import test_seasonality_ab
from core.analytics.spatial import calculate_location_quotient, calculate_shannon_diversity
from core.analytics.elasticity import calculate_elasticity
from core.analytics.inferential import run_inferential_test
from core.analytics.growth import calculate_cagr
from core.analytics.ex_cana import analyze_ex_cana

__all__ = [
    "run_all_analytics",
    "calculate_descriptive_statistics",
    "fit_distributions",
    "detect_multivariate_outliers",
    "calculate_concentration",
    "analyze_time_series",
    "test_seasonality_ab",
    "calculate_location_quotient",
    "calculate_shannon_diversity",
    "calculate_elasticity",
    "run_inferential_test",
    "calculate_cagr",
    "analyze_ex_cana",
]
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "core/analytics/descriptive.py": DESCRIPTIVE,
        "core/analytics/distributions.py": DISTRIBUTIONS,
        "core/analytics/outliers.py": OUTLIERS,
        "core/analytics/concentration.py": CONCENTRATION,
        "core/analytics/time_series.py": TIME_SERIES,
        "core/analytics/seasonality.py": SEASONALITY,
        "core/analytics/spatial.py": SPATIAL,
        "core/analytics/elasticity.py": ELASTICITY,
        "core/analytics/inferential.py": INFERENTIAL,
        "core/analytics/growth.py": GROWTH,
        "core/analytics/ex_cana.py": EX_CANA,
        "core/analytics/pipeline.py": PIPELINE,
        "core/analytics/__init__.py": ANALYTICS_INIT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} archivos del modulo de analisis descriptivo creados.")
    print('Ejecuta: python -c "from core.analytics import run_all_analytics; print(\'OK\')"')