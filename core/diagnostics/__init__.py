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
from core.diagnostics.comparison import compare_cycles
from core.diagnostics.correlation import (
    calculate_bivariate_stats,
    calculate_correlation_matrix,
)
from core.diagnostics.pipeline import run_all_diagnostics
from core.diagnostics.root_cause import find_root_causes
from core.diagnostics.segmentation import (
    find_optimal_clusters,
    segment_municipalities,
)
from core.diagnostics.shock import analyze_shock

__all__ = [
    "analyze_shock",
    "calculate_bivariate_stats",
    "calculate_correlation_matrix",
    "compare_cycles",
    "find_optimal_clusters",
    "find_root_causes",
    "run_all_diagnostics",
    "segment_municipalities",
]
