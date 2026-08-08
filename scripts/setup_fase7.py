"""Fase 7: crea ui/services/performance.py con herramientas de optimizacion."""
from pathlib import Path

PERFORMANCE = '''"""Herramientas de optimizacion de performance para la UI."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.download_section import render_download_button


# ═══════════════════════════════════════════════════════════
# WRAPPERS CACHEADOS: calculan una sola vez por sesion
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def cached_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Isolation Forest cacheado (1 hora)."""
    from core.analytics.outliers import detect_multivariate_outliers
    return detect_multivariate_outliers(df)


@st.cache_data(ttl=3600)
def cached_time_series(df: pd.DataFrame) -> pd.DataFrame:
    """STL + Dickey-Fuller cacheado."""
    from core.analytics.time_series import analyze_time_series
    return analyze_time_series(df)


@st.cache_data(ttl=3600)
def cached_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Wilcoxon A vs B cacheado."""
    from core.analytics.seasonality import test_seasonality_ab
    return test_seasonality_ab(df)


@st.cache_data(ttl=3600)
def cached_segmentation(df: pd.DataFrame) -> dict:
    """K-Means + silueta cacheado."""
    from core.diagnostics.segmentation import segment_municipalities
    return segment_municipalities(df)


@st.cache_data(ttl=3600)
def cached_root_cause(df: pd.DataFrame) -> dict:
    """Arbol de decision cacheado."""
    from core.diagnostics.root_cause import find_root_causes
    return find_root_causes(df)


# ═══════════════════════════════════════════════════════════
# LAZY LOADING: calcula solo cuando el usuario lo pide
# ═══════════════════════════════════════════════════════════

def render_lazy(label: str, key: str):
    """
    Patron de carga bajo demanda.

    Uso:
        if render_lazy("Cargar analisis STL", "btn_stl"):
            resultado = cached_time_series(df)   # solo se ejecuta al hacer clic
            st.dataframe(resultado)

    Args:
        label: Texto del boton.
        key: Key unica del widget.

    Returns:
        True si el usuario hizo clic (ejecutar el calculo).
    """
    return st.button(f"\\u25B6\\uFE0F {label}", key=key)


# ═══════════════════════════════════════════════════════════
# TABLAS OPTIMIZADAS: muestra una muestra, descarga el completo
# ═══════════════════════════════════════════════════════════

def show_table(
    df: pd.DataFrame,
    n: int = 100,
    filename: str | None = None,
    height: int = 380,
) -> None:
    """
    Muestra las primeras n filas (virtualizacion) y ofrece descarga completa.

    Args:
        df: DataFrame completo.
        n: Numero de filas a mostrar (default 100).
        filename: Si se provee, anade boton de descarga del CSV completo.
        height: Altura de la tabla.
    """
    if len(df) > n:
        st.caption(f"Mostrando {n:,} de {len(df):,} filas.")
    st.dataframe(df.head(n), use_container_width=True, height=height)
    if filename is not None:
        render_download_button(df, filename)
'''

if __name__ == "__main__":
    path = Path("ui/services/performance.py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PERFORMANCE, encoding="utf-8")
    print(f"[OK] {path}")
    print("Ahora ejecuta: python scripts\\benchmark_analytics.py")