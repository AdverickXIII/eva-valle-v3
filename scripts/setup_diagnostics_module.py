"""
Setup script: genera los 7 archivos del modulo core/diagnostics/.
Migracion del Notebook 6 (Analisis Diagnostico - Por que ocurrio?).
Ejecutar una sola vez: python scripts/setup_diagnostics_module.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: core/diagnostics/correlation.py
# ═══════════════════════════════════════════════════════════
CORRELATION = '''"""
Analisis 6.1: Matriz de correlacion (Spearman) y estadisticas bivariadas.

Responde la pregunta: ¿Por que sube la produccion?
Identifica las relaciones mas fuertes entre variables productivas.

Mejora respecto al notebook:
- Separacion calculo / visualizacion.
- El nucleo solo calcula; la UI (ui/charts/) renderiza los graficos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.diagnostics.correlation")

METRICAS = [
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_t_ha",
    "ano",
]


def calculate_correlation_matrix(df: pd.DataFrame, method: str = "spearman") -> pd.DataFrame:
    """
    Calcula la matriz de correlacion entre metricas productivas.

    Args:
        df: DataFrame con las columnas de metricas.
        method: Metodo de correlacion ('spearman', 'pearson', 'kendall').

    Returns:
        DataFrame con la matriz de correlacion (n x n).
    """
    metricas_disponibles = [c for c in METRICAS if c in df.columns]
    if len(metricas_disponibles) < 2:
        log.warning("Menos de 2 metricas disponibles. No se puede calcular correlacion.")
        return pd.DataFrame()

    corr = df[metricas_disponibles].corr(method=method)
    log.info(
        "Matriz de correlacion (%s) calculada: %d x %d",
        method, len(metricas_disponibles), len(metricas_disponibles),
    )
    return corr


def calculate_bivariate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadisticas bivariadas clave para visualizacion posterior.

    Retorna pares (X, Y) con estadisticas utiles para scatterplots.

    Args:
        df: DataFrame con metricas productivas.

    Returns:
        DataFrame con columnas: pair, n, correlation, r_squared,
        x_var, y_var.
    """
    pares = [
        ("area_cosechada_ha", "produccion_t"),
        ("area_cosechada_ha", "rendimiento_t_ha"),
        ("area_sembrada_ha", "area_cosechada_ha"),
        ("ano", "produccion_t"),
    ]
    resultados = []
    for x, y in pares:
        if x not in df.columns or y not in df.columns:
            continue
        df_pos = df[(df[x] > 0) & (df[y] > 0)]
        if len(df_pos) < 10:
            continue
        r = df_pos[x].corr(df_pos[y], method="spearman")
        resultados.append({
            "pair": f"{x} vs {y}",
            "n": len(df_pos),
            "correlation": r,
            "r_squared": r ** 2,
            "x_var": x,
            "y_var": y,
        })

    log.info("Estadisticas bivariadas calculadas para %d pares.", len(resultados))
    return pd.DataFrame(resultados)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: core/diagnostics/comparison.py
# ═══════════════════════════════════════════════════════════
COMPARISON = '''"""
Analisis 6.2: Comparacion de grupos (Transitorio vs Permanente).
Mann-Whitney U para detectar diferencias en rendimiento.

Responde: ¿Son diferentes los cultivos transitorios de los permanentes?
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from core.logging import get_logger

log = get_logger("core.diagnostics.comparison")


def compare_cycles(df: pd.DataFrame) -> dict[str, Any]:
    """
    Mann-Whitney U para comparar rendimiento entre ciclos.

    Args:
        df: DataFrame con columnas ciclo_del_cultivo y rendimiento_t_ha.

    Returns:
        Diccionario con estadistico_U, p_value, CV por ciclo, medias,
        medianas y conclusion.
    """
    required_cols = ["ciclo_del_cultivo", "rendimiento_t_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    trans = df[df["ciclo_del_cultivo"] == "Transitorio"]["rendimiento_t_ha"].dropna()
    perm = df[df["ciclo_del_cultivo"] == "Permanente"]["rendimiento_t_ha"].dropna()

    if len(trans) < 10 or len(perm) < 10:
        return {"error": f"Muestras insuficientes: trans={len(trans)}, perm={len(perm)}"}

    stat_u, p_val = sp_stats.mannwhitneyu(trans, perm, alternative="two-sided")

    cv_trans = float((trans.std() / trans.mean()) * 100) if trans.mean() > 0 else np.nan
    cv_perm = float((perm.std() / perm.mean()) * 100) if perm.mean() > 0 else np.nan

    conclusion = (
        "Si hay diferencia estadisticamente significativa en rendimiento."
        if p_val < 0.05
        else "No hay evidencia suficiente para decir que sean diferentes."
    )

    resultado = {
        "estadistico_U": float(stat_u),
        "p_value": float(p_val),
        "CV_Transitorio": cv_trans,
        "CV_Permanente": cv_perm,
        "media_Transitorio": float(trans.mean()),
        "mediana_Transitorio": float(trans.median()),
        "n_Transitorio": len(trans),
        "media_Permanente": float(perm.mean()),
        "mediana_Permanente": float(perm.median()),
        "n_Permanente": len(perm),
        "conclusion": conclusion,
        "diferencia_significativa": bool(p_val < 0.05),
    }

    log.info("Mann-Whitney U completado (p=%.2e). %s", p_val, conclusion)
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: core/diagnostics/segmentation.py
# ═══════════════════════════════════════════════════════════
SEGMENTATION = '''"""
Analisis 6.3: Segmentacion territorial (K-Means).
Identifica perfiles ocultos de municipios.

Mejora respecto al notebook:
- Analisis de silueta para justificar n_clusters (no hardcodeado a 3).
- Nombres de clusters derivados automaticamente del perfil estadistico.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from config.settings import settings
from core.logging import get_logger

log = get_logger("core.diagnostics.segmentation")


def _shannon_index(s: pd.Series) -> float:
    """Calcula el indice de Shannon-Wiener de una serie."""
    p = s / s.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


def find_optimal_clusters(
    X_scaled: np.ndarray,
    k_range: range = range(2, 6),
) -> tuple[int, list[tuple[int, float]]]:
    """
    Encuentra el numero optimo de clusters usando silhouette score.

    Args:
        X_scaled: Matriz de features escaladas.
        k_range: Rango de k a evaluar (default 2 a 5).

    Returns:
        Tupla (k_optimo, lista_de_(k, score)).
    """
    scores: list[tuple[int, float]] = []
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=settings.ML_RANDOM_STATE, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        scores.append((k, float(score)))
        log.info("k=%d: silhouette=%.3f", k, score)

    best_k = max(scores, key=lambda x: x[1])[0]
    return best_k, scores


def segment_municipalities(
    df: pd.DataFrame,
    k_range: range = range(2, 6),
) -> dict[str, Any]:
    """
    Segmenta municipios usando K-Means con seleccion automatica de k.

    Args:
        df: DataFrame con columnas municipio, area_sembrada_ha,
            rendimiento_t_ha, desagregacion_cultivo.
        k_range: Rango de k a evaluar.

    Returns:
        Diccionario con: df_clusters (DataFrame), k_optimo, silhouette_scores,
        centroides_df.
    """
    required_cols = ["municipio", "area_sembrada_ha", "rendimiento_t_ha", "desagregacion_cultivo"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    # Construir features por municipio
    features = (
        df.groupby("municipio")
        .agg(
            area_total=("area_sembrada_ha", "sum"),
            rendimiento_medio=("rendimiento_t_ha", "median"),
            diversidad=("desagregacion_cultivo", "nunique"),
            shannon_wiener=("area_sembrada_ha", _shannon_index),
        )
        .dropna()
    )

    if len(features) < 4:
        return {"error": f"Muy pocos municipios para clustering ({len(features)})."}

    # Escalar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # Encontrar k optimo
    k_optimo, silhouette_scores = find_optimal_clusters(X_scaled, k_range)
    log.info("k optimo seleccionado: %d", k_optimo)

    # Ajustar K-Means con k optimo
    kmeans = KMeans(n_clusters=k_optimo, random_state=settings.ML_RANDOM_STATE, n_init=10)
    features["Cluster"] = kmeans.fit_predict(X_scaled)

    # Nombrar clusters por perfil estadistico (ordenados por area_total)
    centroides = features.groupby("Cluster").mean(numeric_only=True)
    orden_area = centroides["area_total"].sort_values().index.tolist()
    mapa_nombres = {}
    if k_optimo == 2:
        mapa_nombres = {orden_area[0]: "Pequenos", orden_area[1]: "Grandes"}
    elif k_optimo == 3:
        mapa_nombres = {
            orden_area[0]: "Pequenos / Diversos",
            orden_area[1]: "Medianos / Especializados",
            orden_area[2]: "Grandes / Monocultores",
        }
    else:
        for i, c in enumerate(orden_area, 1):
            mapa_nombres[c] = f"Cluster_{i}"

    features["Perfil"] = features["Cluster"].map(mapa_nombres)

    resultado = {
        "df_clusters": features.reset_index()[
            ["municipio", "Cluster", "Perfil", "area_total", "rendimiento_medio", "diversidad", "shannon_wiener"]
        ],
        "k_optimo": k_optimo,
        "silhouette_scores": silhouette_scores,
        "centroides_df": centroides,
    }

    log.info(
        "Segmentacion completada: %d municipios en %d clusters (silhouette=%.3f).",
        len(features), k_optimo, max(s for _, s in silhouette_scores),
    )
    return resultado
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: core/diagnostics/root_cause.py
# ═══════════════════════════════════════════════════════════
ROOT_CAUSE = '''"""
Analisis 6.4: Analisis de causa raiz (Arbol de decision regresor).
Identifica las variables que mejor explican la produccion.

Mejora respecto al notebook:
- Parametros configurables (max_depth, min_samples_leaf).
- Retorna importancia de variables + reglas principales.
- Sin plot_tree (la visualizacion va en ui/charts/).
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.tree import DecisionTreeRegressor

from config.settings import settings
from core.logging import get_logger

log = get_logger("core.diagnostics.root_cause")


def find_root_causes(
    df: pd.DataFrame,
    max_depth: int = 3,
    min_samples_leaf: int = 50,
) -> dict[str, Any]:
    """
    Arbol de decision regresor para identificar causas de la produccion.

    Args:
        df: DataFrame con variables predictoras y produccion_t.
        max_depth: Profundidad maxima del arbol (default 3 para interpretabilidad).
        min_samples_leaf: Minimo de muestras por hoja (default 50).

    Returns:
        Diccionario con: importancia_df (DataFrame), top_rules (list),
        r2_score (float).
    """
    cols_modelo = ["area_cosechada_ha", "rendimiento_t_ha", "ano", "grupo_cultivo", "ciclo_del_cultivo"]
    required_cols = cols_modelo + ["produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    df_tree = df.dropna(subset=required_cols).copy()
    if len(df_tree) < min_samples_leaf * 2:
        return {"error": f"Insuficientes datos ({len(df_tree)}) para arbol con min_samples_leaf={min_samples_leaf}"}

    X = pd.get_dummies(df_tree[cols_modelo], drop_first=True)
    y = df_tree["produccion_t"]

    tree = DecisionTreeRegressor(
        max_depth=max_depth,
        random_state=settings.ML_RANDOM_STATE,
        min_samples_leaf=min_samples_leaf,
    )
    tree.fit(X, y)

    importancia = pd.Series(tree.feature_importances_, index=X.columns).sort_values(ascending=False)
    r2 = float(tree.score(X, y))

    # Extraer reglas principales del arbol
    reglas = _extract_rules(tree, X.columns)

    log.info("Arbol de decision ajustado (R2=%.3f). %d features evaluadas.", r2, len(X.columns))
    return {
        "importancia_df": importancia.to_frame("importancia"),
        "top_rules": reglas,
        "r2_score": r2,
        "n_features": len(X.columns),
        "max_depth": max_depth,
    }


def _extract_rules(tree: DecisionTreeRegressor, feature_names) -> list[dict[str, Any]]:
    """
    Extrae las reglas principales del arbol como lista de diccionarios.
    Util para mostrar en UI sin necesidad de plot_tree.
    """
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != -2 else "undefined"
        for i in tree_.feature
    ]

    reglas: list[dict[str, Any]] = []

    def recurse(node: int, condiciones: list[str]) -> None:
        if tree_.feature[node] != -2:  # Nodo de decision
            name = feature_name[node]
            threshold = tree_.threshold[node]
            recurse(tree_.children_left[node], condiciones + [f"{name} <= {threshold:.2f}"])
            recurse(tree_.children_right[node], condiciones + [f"{name} > {threshold:.2f}"])
        else:  # Hoja
            valor_hoja = tree_.value[node][0][0]
            muestras = tree_.n_node_samples[node]
            if muestras >= 50:
                reglas.append({
                    "condiciones": " AND ".join(condiciones),
                    "produccion_predicha": float(valor_hoja),
                    "n_registros": int(muestras),
                })

    recurse(0, [])
    reglas.sort(key=lambda r: r["n_registros"], reverse=True)
    return reglas[:5]  # Top 5 reglas mas frecuentes
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: core/diagnostics/shock.py
# ═══════════════════════════════════════════════════════════
SHOCK = '''"""
Analisis 6.5: Analisis del shock exogeno (Impacto 2020).
Aislamiento del efecto COVID-19 vs tendencia historica.

Responde: ¿Que paso en 2020? ¿La produccion cayo o siguio creciendo?
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from core.logging import get_logger

log = get_logger("core.diagnostics.shock")

ANOS_EXPECTED = [2019, 2020, 2021, 2022, 2023, 2024]
SHOCK_YEAR = 2020


def analyze_shock(df: pd.DataFrame, shock_year: int = SHOCK_YEAR) -> dict[str, Any]:
    """
    Calcula variaciones interanuales y detecta shocks exogenos.

    Args:
        df: DataFrame con columnas ano, produccion_t, area_sembrada_ha.
        shock_year: Ano del shock a analizar (default 2020).

    Returns:
        Diccionario con: df_historico (variaciones anuales),
        impacto_shock (variacion en shock_year vs tendencia).
    """
    required_cols = ["ano", "produccion_t", "area_sembrada_ha"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    hist = (
        df.groupby("ano")
        .agg(produccion=("produccion_t", "sum"), area=("area_sembrada_ha", "sum"))
        .reset_index()
    )
    hist["var_produccion"] = hist["produccion"].pct_change() * 100
    hist["var_area"] = hist["area"].pct_change() * 100

    # Calcular tendencia pre-shock (promedio de variaciones antes del shock)
    pre_shock = hist[hist["ano"] < shock_year]
    tendencia_previa_prod = pre_shock["var_produccion"].mean() if len(pre_shock) > 0 else 0

    # Impacto del shock
    shock_data = hist[hist["ano"] == shock_year]
    if shock_data.empty:
        return {
            "error": f"Ano {shock_year} no encontrado en el dataset.",
            "df_historico": hist,
        }

    var_shock_prod = float(shock_data["var_produccion"].iloc[0])
    var_shock_area = float(shock_data["var_area"].iloc[0])

    # Diferencia entre lo observado y la tendencia esperada
    desviacion_vs_tendencia = var_shock_prod - tendencia_previa_prod

    impacto = {
        "shock_year": shock_year,
        "var_produccion": var_shock_prod,
        "var_area": var_shock_area,
        "tendencia_previa_prod": float(tendencia_previa_prod) if not pd.isna(tendencia_previa_prod) else 0.0,
        "desviacion_vs_tendencia": desviacion_vs_tendencia,
        "direccion": "caida" if var_shock_prod < 0 else "crecimiento",
        "impacto_significativo": abs(desviacion_vs_tendencia) > 5.0,
    }

    log.info(
        "Analisis de shock %d: produccion %.2f%%, desviacion vs tendencia %.2f%%",
        shock_year, var_shock_prod, desviacion_vs_tendencia,
    )

    return {
        "df_historico": hist,
        "impacto_shock": impacto,
    }
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: core/diagnostics/pipeline.py
# ═══════════════════════════════════════════════════════════
PIPELINE = '''"""
Orquestador del Paso 6: Analisis Diagnostico.

Migrado del Notebook 6 (funcion ejecutar_paso6).
Mejoras:
- Sin prints (solo logging)
- Separacion calculo / visualizacion
- Configuracion desde config.settings
- Usa adaptadores de storage (CsvStorage)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.diagnostics.comparison import compare_cycles
from core.diagnostics.correlation import calculate_bivariate_stats, calculate_correlation_matrix
from core.diagnostics.root_cause import find_root_causes
from core.diagnostics.segmentation import segment_municipalities
from core.diagnostics.shock import analyze_shock
from core.logging import get_logger, log_section

log = get_logger("core.diagnostics.pipeline")

_csv_storage = CsvStorage()


def run_all_diagnostics(
    input_path: Path | None = None,
    export_artifacts: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta los 5 analisis diagnosticos del Paso 6.

    Args:
        input_path: Ruta al CSV con modelo conceptual. Si es None, usa
            la ruta por defecto.
        export_artifacts: Si True, exporta los artefactos a CSV.

    Returns:
        Diccionario con los 5 artefactos generados.

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
    """
    log_section("PASO 6 - ANALISIS DIAGNOSTICO (POR QUE OCURRIO?)")

    if input_path is None:
        input_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d registros", len(df))

    artefactos: dict[str, Any] = {}

    # 6.1 Correlacion
    log.info("Ejecutando 6.1 Correlacion y estadisticas bivariadas...")
    artefactos["6_1_matriz_correlacion"] = calculate_correlation_matrix(df)
    artefactos["6_1_bivariadas"] = calculate_bivariate_stats(df)

    # 6.2 Comparacion de ciclos
    log.info("Ejecutando 6.2 Comparacion Transitorio vs Permanente...")
    comparacion = compare_cycles(df)
    artefactos["6_2_comparacion_ciclos"] = pd.DataFrame([comparacion])

    # 6.3 Segmentacion de municipios
    log.info("Ejecutando 6.3 Segmentacion territorial (K-Means)...")
    segmentacion = segment_municipalities(df)
    if "error" not in segmentacion:
        artefactos["6_3_perfiles_municipios"] = segmentacion["df_clusters"]
        artefactos["6_3_silhouette_scores"] = pd.DataFrame(
            segmentacion["silhouette_scores"], columns=["k", "silhouette_score"]
        )
    else:
        artefactos["6_3_error"] = segmentacion["error"]

    # 6.4 Arbol de causa raiz
    log.info("Ejecutando 6.4 Arbol de causa raiz...")
    causa_raiz = find_root_causes(df)
    if "error" not in causa_raiz:
        artefactos["6_4_importancia_variables"] = causa_raiz["importancia_df"]
    else:
        artefactos["6_4_error"] = causa_raiz["error"]

    # 6.5 Shock exogeno
    log.info("Ejecutando 6.5 Analisis del shock 2020...")
    shock = analyze_shock(df)
    if "error" not in shock:
        artefactos["6_5_variacion_shock_2020"] = shock["df_historico"]
        artefactos["6_5_impacto_shock"] = pd.DataFrame([shock["impacto_shock"]])
    else:
        artefactos["6_5_error"] = shock["error"]

    # Exportar artefactos
    if export_artifacts:
        log.info("Exportando %d artefactos...", len(artefactos))
        for nombre, df_art in artefactos.items():
            if isinstance(df_art, pd.DataFrame) and not df_art.empty:
                ruta = settings.OUTPUTS_TABLES_PATH / f"{nombre}.csv"
                _csv_storage.write_csv(df_art, ruta)

    log.info("Paso 6 completado. %d artefactos generados.", len(artefactos))
    return artefactos
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: core/diagnostics/__init__.py (FACHADA)
# ═══════════════════════════════════════════════════════════
DIAGNOSTICS_INIT = '''"""
Modulo de analisis diagnostico del proyecto eva-valle-v3.0.

Fachada que orquesta los 5 analisis del Paso 6.
Responde la pregunta: ¿Por que ocurrio?

Uso:
    from core.diagnostics import run_all_diagnostics, calculate_correlation_matrix

    # Ejecutar los 5 analisis
    artefactos = run_all_diagnostics()

    # O ejecutar un analisis individual
    corr = calculate_correlation_matrix(df)
"""
from core.diagnostics.pipeline import run_all_diagnostics
from core.diagnostics.correlation import (
    calculate_correlation_matrix,
    calculate_bivariate_stats,
)
from core.diagnostics.comparison import compare_cycles
from core.diagnostics.segmentation import (
    segment_municipalities,
    find_optimal_clusters,
)
from core.diagnostics.root_cause import find_root_causes
from core.diagnostics.shock import analyze_shock

__all__ = [
    "run_all_diagnostics",
    "calculate_correlation_matrix",
    "calculate_bivariate_stats",
    "compare_cycles",
    "segment_municipalities",
    "find_optimal_clusters",
    "find_root_causes",
    "analyze_shock",
]
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "core/diagnostics/correlation.py": CORRELATION,
        "core/diagnostics/comparison.py": COMPARISON,
        "core/diagnostics/segmentation.py": SEGMENTATION,
        "core/diagnostics/root_cause.py": ROOT_CAUSE,
        "core/diagnostics/shock.py": SHOCK,
        "core/diagnostics/pipeline.py": PIPELINE,
        "core/diagnostics/__init__.py": DIAGNOSTICS_INIT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} archivos del modulo de diagnostico creados.")
    print('Ejecuta: python -c "from core.diagnostics import run_all_diagnostics; print(\'OK\')"')