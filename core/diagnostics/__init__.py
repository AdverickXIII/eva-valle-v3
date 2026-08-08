"""
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
