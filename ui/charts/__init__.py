"""Modulo de visualizaciones interactivas con Plotly."""
from ui.charts.concentration import plot_ex_cana_donuts, plot_pareto_concentracion
from ui.charts.diagnostics import plot_correlation_heatmap, plot_scatter_bivariado
from ui.charts.distributions import plot_distribuciones_log
from ui.charts.growth import plot_cagr_divergente
from ui.charts.historical import plot_historico_cruces, plot_rendimiento_historico
from ui.charts.spatial import plot_lq_heatmap, plot_shannon_barras

__all__ = [
    "plot_cagr_divergente",
    "plot_correlation_heatmap",
    "plot_distribuciones_log",
    "plot_ex_cana_donuts",
    "plot_historico_cruces",
    "plot_lq_heatmap",
    "plot_pareto_concentracion",
    "plot_rendimiento_historico",
    "plot_scatter_bivariado",
    "plot_shannon_barras",
]
