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
