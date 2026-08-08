"""
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
