"""Manejo de errores global para paginas Streamlit."""
from __future__ import annotations

import functools

import streamlit as st

from core.logging import get_logger

log = get_logger("ui.errors")


def run_safe(main_func) -> None:
    """Ejecuta el main de una pagina con manejo de errores global."""
    try:
        main_func()
    except Exception as e:
        log.error("Error en pagina: %s", e)
        st.error(f"Ocurrio un error inesperado: {e}")
        st.info(
            "Intenta recargar la pagina, o verifica que el pipeline "
            "se haya ejecutado: python scripts/run_pipeline.py --skip-download"
        )


def safe_page(func):
    """Decorador que envuelve una pagina con manejo de errores."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error("Error en pagina: %s", e)
            st.error(f"Ocurrio un error inesperado: {e}")
    return wrapper
