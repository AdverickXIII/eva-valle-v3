"""
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
