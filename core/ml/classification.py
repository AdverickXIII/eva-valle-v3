"""
Analisis 7.3: Modelo de Clasificacion (Random Forest).
Predice riesgo de perdida de cosecha (frac_cosechada < 0.90).

Mejoras respecto al notebook:
- Sin matplotlib.
- Persistencia del modelo con JoblibModelRegistry.
- Manejo robusto de clases faltantes en test set.
- Parametros configurables.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

from adapters.ml_registry.joblib_registry import JoblibModelRegistry
from config.settings import settings
from core.logging import get_logger

log = get_logger("core.ml.classification")

CLASSIFICATION_FEATURES = [
    "area_sembrada_ha",
    "rendimiento_lag1",
    "target_enc_municipio",
    "target_enc_cultivo",
    "grupo_cultivo",
    "ciclo_del_cultivo",
    "ano",
]
CLASSIFICATION_TARGET = "perdida_cosecha"
MODEL_NAME = "rf_clasificacion_v1"


def train_classification(
    df: pd.DataFrame,
    n_estimators: int = 150,
    max_depth: int = 8,
    test_size: float | None = None,
    persist_model: bool = True,
) -> dict[str, Any]:
    """
    Entrena un Random Forest Classifier para perdida de cosecha.

    Args:
        df: DataFrame con features y target (post target-encoding).
        n_estimators: Numero de arboles (default 150).
        max_depth: Profundidad maxima (default 8).
        test_size: Proporcion de test. Si None, usa settings.ML_TEST_SIZE.
        persist_model: Si True, guarda el modelo con joblib.

    Returns:
        Diccionario con: modelo, metricas (reporte de clasificacion).
        Si hay error, retorna {"error": "mensaje"}.
    """
    if test_size is None:
        test_size = settings.ML_TEST_SIZE

    available_features = [f for f in CLASSIFICATION_FEATURES if f in df.columns]
    if CLASSIFICATION_TARGET not in df.columns:
        return {"error": f"Columna target '{CLASSIFICATION_TARGET}' no encontrada."}

    X = pd.get_dummies(df[available_features], drop_first=True)
    y = df[CLASSIFICATION_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=settings.ML_RANDOM_STATE,
        stratify=y,  # ← Estratificar para preservar proporcion de clases
    )

    rf_clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    )
    rf_clf.fit(X_train, y_train)

    # Verificar si ambas clases llegaron al test set
    if len(np.unique(y_test)) < 2:
        log.warning(
            "Test set solo contiene una clase. No se pueden calcular "
            "metricas de clasificacion binaria."
        )
        return {
            "modelo": rf_clf,
            "metricas": {"error": "Test set sin clase minoritaria"},
        }

    y_pred = rf_clf.predict(X_test)

    # ROC-AUC (solo si el modelo predice ambas clases)
    if len(rf_clf.classes_) == 2:
        y_prob = rf_clf.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, y_prob))
    else:
        log.warning("Modelo solo predice una clase. ROC-AUC no calculable.")
        auc = float("nan")

    reporte = classification_report(
        y_test, y_pred, output_dict=True, zero_division=0,
    )
    reporte["ROC_AUC"] = auc

    # Persistir modelo
    if persist_model:
        registry = JoblibModelRegistry()
        registry.save_model(rf_clf, MODEL_NAME)
        log.info("Modelo de clasificacion persistido como '%s'.", MODEL_NAME)

    log.info(
        "Clasificacion completada: ROC-AUC=%.3f, Precision clase 1=%.3f",
        auc, reporte.get("1", {}).get("precision", float("nan")),
    )

    return {
        "modelo": rf_clf,
        "metricas": reporte,
        "features_usadas": list(X.columns),
    }
