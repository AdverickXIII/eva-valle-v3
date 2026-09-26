"""
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
from core.ml.classification import train_classification
from core.ml.features import create_features_ml
from core.ml.forecasting import forecast_time_series
from core.ml.pipeline import run_all_ml
from core.ml.regression import train_regression
from core.ml.target_encoding import apply_target_encoding, fit_target_encoding

__all__ = [
    "apply_target_encoding",
    "create_features_ml",
    "fit_target_encoding",
    "forecast_time_series",
    "run_all_ml",
    "train_classification",
    "train_regression",
]
