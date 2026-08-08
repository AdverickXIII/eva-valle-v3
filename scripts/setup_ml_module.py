"""
Setup script: genera los 7 archivos del modulo core/ml/.
Migracion del Notebook 7 (Analisis Predictivo).
Incluye la CORRECCION CRITICA del data leakage en target encoding.
Ejecutar una sola vez: python scripts/setup_ml_module.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: core/ml/features.py
# ═══════════════════════════════════════════════════════════
FEATURES = '''"""
Analisis 7.1: Feature Engineering.
Creacion de variables predictoras: lags, log-transformacion, fraccion de cosecha.

⚠️ IMPORTANTE: Esta funcion NO incluye target encoding.
El target encoding se hace en target_encoding.py con fit/transform
separados para evitar data leakage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from core.logging import get_logger

log = get_logger("core.ml.features")


def create_features_ml(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea la matriz de caracteristicas base (sin target encoding).

    Features generadas:
    - produccion_lag1: Produccion del periodo anterior
    - rendimiento_lag1: Rendimiento del periodo anterior
    - log_produccion: log1p(produccion_t) para normalizar sesgo
    - frac_cosechada: area_cosechada / area_sembrada
    - perdida_cosecha: Flag binario (frac_cosechada < 0.90)

    Args:
        df: DataFrame con columnas del modelo conceptual.

    Returns:
        DataFrame con features adicionales, filtrado a registros
        con lags validos.
    """
    required_cols = [
        "codigo_dane_municipio", "desagregacion_cultivo", "ano", "periodo",
        "produccion_t", "rendimiento_t_ha", "area_sembrada_ha", "area_cosechada_ha",
    ]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        log.warning("Columnas faltantes para feature engineering: %s", faltantes)
        return pd.DataFrame()

    df_ml = df.copy()
    df_ml = df_ml.sort_values(
        ["codigo_dane_municipio", "desagregacion_cultivo", "ano", "periodo"]
    )

    # Lags por grupo (municipio + cultivo)
    grupo = ["codigo_dane_municipio", "desagregacion_cultivo"]
    df_ml["produccion_lag1"] = df_ml.groupby(grupo)["produccion_t"].shift(1)
    df_ml["rendimiento_lag1"] = df_ml.groupby(grupo)["rendimiento_t_ha"].shift(1)

    # Log-transformacion del target (normaliza sesgo a derecha)
    df_ml["log_produccion"] = np.log1p(df_ml["produccion_t"])

    # Fraccion de area cosechada vs sembrada
    df_ml["frac_cosechada"] = np.where(
        df_ml["area_sembrada_ha"] > 0,
        df_ml["area_cosechada_ha"] / df_ml["area_sembrada_ha"],
        np.nan,
    )

    # Flag de perdida de cosecha (frac < 0.90 = perdio mas del 10% del area)
    df_ml["perdida_cosecha"] = (df_ml["frac_cosechada"] < 0.90).astype(int)

    # Filtrar registros sin lags validos (primera observacion de cada grupo)
    n_antes = len(df_ml)
    df_ml = df_ml.dropna(subset=["produccion_lag1", "rendimiento_lag1"])
    n_despues = len(df_ml)

    log.info(
        "Feature engineering completado: %d -> %d registros (%d sin lags).",
        n_antes, n_despues, n_antes - n_despues,
    )
    return df_ml
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: core/ml/target_encoding.py
# ⚠️ CORRECCIÓN CRÍTICA DEL DATA LEAKAGE
# ═══════════════════════════════════════════════════════════
TARGET_ENCODING = '''"""
Target Encoding sin data leakage.

⚠️ CORRECCION CRITICA (Fase 0 - Bug P6):
El codigo original usaba df.groupby(...).transform("mean") sobre TODO
el dataset ANTES del train_test_split. Esto causaba data leakage:
el modelo "veia" informacion del test set durante el entrenamiento,
inflando artificialmente las metricas.

Solucion: Separar fit (calcular medias con train) de transform
(aplicar medias a cualquier dataset). Esto sigue el patron de sklearn:
fit() solo con train, transform() con train y test.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from core.logging import get_logger

log = get_logger("core.ml.target_encoding")

# Columnas a las que se aplica target encoding
ENCODING_COLUMNS = ["municipio", "desagregacion_cultivo"]
TARGET_COLUMN = "rendimiento_t_ha"


def fit_target_encoding(df_train: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Calcula las medias de target encoding SOLO con el set de entrenamiento.

    ⚠️ Esta funcion debe llamarse DESPUES del train_test_split,
    usando exclusivamente df_train. Nunca usar el dataset completo.

    Args:
        df_train: DataFrame de entrenamiento (post-split).

    Returns:
        Diccionario con las medias por columna de encoding.
        Claves: nombres de columnas. Valores: Series con las medias.
    """
    encoding_maps: dict[str, pd.Series] = {}
    for col in ENCODING_COLUMNS:
        if col in df_train.columns:
            encoding_maps[col] = df_train.groupby(col)[TARGET_COLUMN].mean()
        else:
            log.warning("Columna '%s' no encontrada en df_train.", col)

    log.info(
        "Target encoding ajustado con %d registros de train. Columnas: %s",
        len(df_train), list(encoding_maps.keys()),
    )
    return encoding_maps


def apply_target_encoding(
    df: pd.DataFrame,
    encoding_maps: dict[str, pd.Series],
) -> pd.DataFrame:
    """
    Aplica las medias pre-calculadas a cualquier dataset (train o test).

    ⚠️ Para el test set, se usan las medias calculadas con train.
    Esto evita que el modelo "vea" informacion del test set.

    Args:
        df: DataFrame al que aplicar el encoding (train o test).
        encoding_maps: Diccionario retornado por fit_target_encoding().

    Returns:
        DataFrame con columnas target_enc_* agregadas.
    """
    df = df.copy()
    for col, medias in encoding_maps.items():
        col_enc = f"target_enc_{col}"
        df[col_enc] = df[col].map(medias)
        # Rellenar NaN (categorias no vistas en train) con la media global
        if df[col_enc].isna().any():
            n_missing = df[col_enc].isna().sum()
            global_mean = medias.mean()
            df[col_enc] = df[col_enc].fillna(global_mean)
            log.warning(
                "target_enc_%s: %d valores NaN rellenados con media global (%.2f).",
                col, n_missing, global_mean,
            )

    log.info("Target encoding aplicado a %d registros.", len(df))
    return df
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: core/ml/regression.py
# ═══════════════════════════════════════════════════════════
REGRESSION = '''"""
Analisis 7.2: Modelo de Regresion (Random Forest).
Predice log(produccion) a partir de features productivas.

Mejoras respecto al notebook:
- Sin matplotlib (separacion calculo / visualizacion).
- Persistencia del modelo con JoblibModelRegistry.
- Parametros configurables.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from adapters.ml_registry.joblib_registry import JoblibModelRegistry
from config.settings import settings
from core.logging import get_logger

log = get_logger("core.ml.regression")

REGRESSION_FEATURES = [
    "area_sembrada_ha",
    "rendimiento_lag1",
    "produccion_lag1",
    "target_enc_municipio",
    "target_enc_cultivo",
    "ano",
]
REGRESSION_TARGET = "log_produccion"
MODEL_NAME = "rf_regresion_v1"


def train_regression(
    df: pd.DataFrame,
    n_estimators: int = 200,
    max_depth: int = 10,
    test_size: float | None = None,
    persist_model: bool = True,
) -> dict[str, Any]:
    """
    Entrena un Random Forest Regressor sobre log(produccion).

    Args:
        df: DataFrame con features y target (post target-encoding).
        n_estimators: Numero de arboles (default 200).
        max_depth: Profundidad maxima de cada arbol (default 10).
        test_size: Proporcion de test. Si None, usa settings.ML_TEST_SIZE.
        persist_model: Si True, guarda el modelo con joblib.

    Returns:
        Diccionario con: modelo, metricas, importancia, df_residuos.
    """
    if test_size is None:
        test_size = settings.ML_TEST_SIZE

    available_features = [f for f in REGRESSION_FEATURES if f in df.columns]
    faltantes = [f for f in REGRESSION_FEATURES if f not in df.columns]
    if faltantes:
        log.warning("Features faltantes para regresion: %s", faltantes)

    X = df[available_features]
    y = df[REGRESSION_TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=settings.ML_RANDOM_STATE,
    )

    rf_reg = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=-1,
    )
    rf_reg.fit(X_train, y_train)

    # Predicciones y metricas
    y_pred_log = rf_reg.predict(X_test)
    rmse_log = float(np.sqrt(mean_squared_error(y_test, y_pred_log)))
    mae_log = float(mean_absolute_error(y_test, y_pred_log))
    r2 = float(r2_score(y_test, y_pred_log))

    # Metricas en escala real (toneladas)
    y_test_real = np.expm1(y_test)
    y_pred_real = np.expm1(y_pred_log)
    mae_toneladas = float(mean_absolute_error(y_test_real, y_pred_real))

    metricas = {
        "RMSE_Log": rmse_log,
        "MAE_Log": mae_log,
        "R2": r2,
        "MAE_Toneladas": mae_toneladas,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    # Importancia de variables
    importancia = pd.Series(
        rf_reg.feature_importances_, index=available_features
    ).sort_values(ascending=False)

    # DataFrame de residuos (para visualizacion posterior)
    df_residuos = pd.DataFrame({
        "Real_t": y_test_real,
        "Pred_t": y_pred_real,
        "Residuo_t": y_test_real - y_pred_real,
    })

    # Persistir modelo
    if persist_model:
        registry = JoblibModelRegistry()
        registry.save_model(rf_reg, MODEL_NAME)
        log.info("Modelo de regresion persistido como '%s'.", MODEL_NAME)

    log.info(
        "Regresion completada: R2=%.3f, MAE=%.0f t, Top feature=%s",
        r2, mae_toneladas, importancia.index[0],
    )

    return {
        "modelo": rf_reg,
        "metricas": metricas,
        "importancia": importancia,
        "df_residuos": df_residuos,
        "features_usadas": available_features,
    }
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: core/ml/classification.py
# ═══════════════════════════════════════════════════════════
CLASSIFICATION = '''"""
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
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: core/ml/forecasting.py
# ═══════════════════════════════════════════════════════════
FORECASTING = '''"""
Analisis 7.4: Proyeccion tendencial (Holt-Winters).
Suavizamiento exponencial de la produccion total semestral.

Mejoras respecto al notebook:
- Sin matplotlib (separacion calculo / visualizacion).
- Manejo robusto de series cortas.
"""
from __future__ import annotations

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from core.logging import get_logger

log = get_logger("core.ml.forecasting")

MIN_SERIE_LENGTH = 8
FORECAST_PERIODS = 2
FORECAST_LABELS = ["2025A", "2025B"]


def forecast_time_series(
    df: pd.DataFrame,
    forecast_periods: int = FORECAST_PERIODS,
) -> dict[str, pd.DataFrame | str]:
    """
    Proyeccion tendencial con Holt-Winters (sin estacionalidad).

    Args:
        df: DataFrame con columnas ano, periodo, produccion_t.
        forecast_periods: Numero de periodos a proyectar (default 2).

    Returns:
        Diccionario con: df_proyeccion (historico + pronostico),
        metodo ("holt_winters" o "insuficiente").
    """
    required_cols = ["ano", "periodo", "produccion_t"]
    faltantes = [c for c in required_cols if c not in df.columns]
    if faltantes:
        return {"error": f"Columnas faltantes: {faltantes}"}

    df_time = (
        df.groupby(["ano", "periodo"])["produccion_t"]
        .sum()
        .reset_index()
        .sort_values(["ano", "periodo"])
        .reset_index(drop=True)
    )

    serie = df_time["produccion_t"]
    if len(serie) < MIN_SERIE_LENGTH:
        log.warning(
            "Serie muy corta (%d < %d) para Holt-Winters. "
            "Retornando solo datos historicos.",
            len(serie), MIN_SERIE_LENGTH,
        )
        df_time["tipo"] = "Historico"
        return {"df_proyeccion": df_time, "metodo": "insuficiente"}

    try:
        modelo_hw = ExponentialSmoothing(
            serie,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        )
        fit_hw = modelo_hw.fit()
        pronostico = fit_hw.forecast(forecast_periods)

        df_forecast = pd.DataFrame({
            "periodo": FORECAST_LABELS[:forecast_periods],
            "produccion_predicha": pronostico,
            "tipo": "Pronostico",
        })

        df_hist = df_time.copy()
        df_hist["tipo"] = "Historico"
        df_hist = df_hist.rename(columns={"produccion_t": "produccion_predicha"})

        df_final = pd.concat([df_hist, df_forecast], ignore_index=True)

        log.info(
            "Holt-Winters completado: %d periodos historicos + %d pronosticados.",
            len(df_hist), forecast_periods,
        )
        return {"df_proyeccion": df_final, "metodo": "holt_winters"}

    except Exception as e:
        log.error("Error en Holt-Winters: %s", e)
        df_time["tipo"] = "Historico"
        return {"df_proyeccion": df_time, "metodo": f"error: {e}"}
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: core/ml/pipeline.py
# ═══════════════════════════════════════════════════════════
PIPELINE = '''"""
Orquestador del Paso 7: Analisis Predictivo.

Migrado del Notebook 7 (funcion ejecutar_paso7).
Mejoras:
- Sin prints (solo logging)
- Target encoding sin data leakage (fit solo con train)
- Persistencia de modelos con JoblibModelRegistry
- Configuracion desde config.settings
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from adapters.storage.csv_storage import CsvStorage
from config.settings import settings
from core.logging import get_logger, log_section
from core.ml.classification import train_classification
from core.ml.features import create_features_ml
from core.ml.forecasting import forecast_time_series
from core.ml.regression import train_regression
from core.ml.target_encoding import apply_target_encoding, fit_target_encoding

log = get_logger("core.ml.pipeline")

_csv_storage = CsvStorage()


def run_all_ml(
    input_path: Path | None = None,
    export_artifacts: bool = True,
    persist_models: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta el pipeline completo de analisis predictivo (Paso 7).

    Args:
        input_path: Ruta al CSV con modelo conceptual. Si es None, usa
            la ruta por defecto.
        export_artifacts: Si True, exporta los artefactos a CSV.
        persist_models: Si True, persiste los modelos con joblib.

    Returns:
        Diccionario con todos los artefactos generados.

    Raises:
        DatasetNotFoundError: Si el archivo de entrada no existe.
    """
    log_section("PASO 7 - ANALISIS PREDICTIVO (QUE PODRIA OCURRIR?)")

    if input_path is None:
        input_path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"

    # Cargar dataset
    df = _csv_storage.read_csv(input_path)
    log.info("Dataset cargado: %d registros", len(df))

    artefactos: dict[str, Any] = {}

    # 7.1 Feature Engineering (sin target encoding)
    log.info("Ejecutando 7.1 Feature Engineering...")
    df_ml = create_features_ml(df)
    if df_ml.empty:
        return {"error": "Feature engineering fallo. Verificar columnas de entrada."}
    log.info("Matriz de features lista: %d registros", len(df_ml))

    # Split ANTES del target encoding (evita data leakage)
    df_train, df_test = train_test_split(
        df_ml,
        test_size=settings.ML_TEST_SIZE,
        random_state=settings.ML_RANDOM_STATE,
    )
    log.info("Split completado: train=%d, test=%d", len(df_train), len(df_test))

    # Target encoding: fit con train, apply a ambos
    log.info("Ejecutando target encoding (fit solo con train)...")
    encoding_maps = fit_target_encoding(df_train)
    df_train_enc = apply_target_encoding(df_train, encoding_maps)
    df_test_enc = apply_target_encoding(df_test, encoding_maps)

    # Recombinar para pasar a los modelos (ya con encoding correcto)
    df_enc = pd.concat([df_train_enc, df_test_enc], ignore_index=True)

    # 7.2 Modelo de Regresion
    log.info("Ejecutando 7.2 Regresion (Random Forest)...")
    resultado_reg = train_regression(df_enc, persist_model=persist_models)
    artefactos["7_2_metricas_regresion"] = pd.DataFrame([resultado_reg["metricas"]])
    artefactos["7_2_importancia_variables"] = resultado_reg["importancia"].to_frame("importancia")
    artefactos["7_2_predicciones_regresion"] = resultado_reg["df_residuos"]

    # 7.3 Modelo de Clasificacion
    log.info("Ejecutando 7.3 Clasificacion (Random Forest)...")
    resultado_clf = train_classification(df_enc, persist_model=persist_models)
    if "error" not in resultado_clf.get("metricas", {}):
        clf_reporte_df = pd.DataFrame(resultado_clf["metricas"]).T
        artefactos["7_3_metricas_clasificacion"] = clf_reporte_df

    # 7.4 Proyeccion de Serie de Tiempo
    log.info("Ejecutando 7.4 Proyeccion (Holt-Winters)...")
    resultado_forecast = forecast_time_series(df)
    if "error" not in resultado_forecast:
        artefactos["7_4_proyeccion_macro"] = resultado_forecast["df_proyeccion"]

    # Exportar artefactos
    if export_artifacts:
        log.info("Exportando %d artefactos...", len(artefactos))
        for nombre, df_art in artefactos.items():
            if isinstance(df_art, pd.DataFrame) and not df_art.empty:
                ruta = settings.OUTPUTS_TABLES_PATH / f"{nombre}.csv"
                _csv_storage.write_csv(df_art, ruta)

    log.info("Paso 7 completado. %d artefactos generados.", len(artefactos))
    return artefactos
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: core/ml/__init__.py (FACHADA)
# ═══════════════════════════════════════════════════════════
ML_INIT = '''"""
Modulo de analisis predictivo del proyecto eva-valle-v3.0.

Fachada que orquesta los modelos del Paso 7.
Responde la pregunta: ¿Que podria ocurrir?

Uso:
    from core.ml import run_all_ml, create_features_ml, fit_target_encoding

    # Ejecutar el pipeline completo
    artefactos = run_all_ml()

    # O ejecutar componentes individuales
    df_features = create_features_ml(df)
    encoding_maps = fit_target_encoding(df_train)
"""
from core.ml.pipeline import run_all_ml
from core.ml.features import create_features_ml
from core.ml.target_encoding import fit_target_encoding, apply_target_encoding
from core.ml.regression import train_regression
from core.ml.classification import train_classification
from core.ml.forecasting import forecast_time_series

__all__ = [
    "run_all_ml",
    "create_features_ml",
    "fit_target_encoding",
    "apply_target_encoding",
    "train_regression",
    "train_classification",
    "forecast_time_series",
]
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "core/ml/features.py": FEATURES,
        "core/ml/target_encoding.py": TARGET_ENCODING,
        "core/ml/regression.py": REGRESSION,
        "core/ml/classification.py": CLASSIFICATION,
        "core/ml/forecasting.py": FORECASTING,
        "core/ml/pipeline.py": PIPELINE,
        "core/ml/__init__.py": ML_INIT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} archivos del modulo de ML creados.")
    print('Ejecuta: python -c "from core.ml import run_all_ml; print(\'OK\')"')