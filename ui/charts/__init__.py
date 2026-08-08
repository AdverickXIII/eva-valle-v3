"""Modulo de visualizaciones interactivas con Plotly."""
from ui.charts.historical import plot_historico_cruces, plot_rendimiento_historico
from ui.charts.distributions import plot_distribuciones_log
from ui.charts.concentration import plot_pareto_concentracion, plot_ex_cana_donuts
from ui.charts.growth import plot_cagr_divergente
from ui.charts.spatial import plot_lq_heatmap, plot_shannon_barras
from ui.charts.diagnostics import plot_correlation_heatmap, plot_scatter_bivariado

__all__ = [
    "plot_historico_cruces","plot_rendimiento_historico","plot_distribuciones_log",
    "plot_pareto_concentracion","plot_ex_cana_donuts","plot_cagr_divergente",
    "plot_lq_heatmap","plot_shannon_barras","plot_correlation_heatmap",
    "plot_scatter_bivariado",
]
