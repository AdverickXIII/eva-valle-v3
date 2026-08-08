"""
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
