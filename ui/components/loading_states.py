"""Estados de carga y mensajes vacios."""
from __future__ import annotations

import streamlit as st


def render_loading(message: str = "Cargando datos...") -> None:
    """Renderiza un spinner de carga."""
    with st.spinner(message):
        pass


def render_empty_state(
    message: str = "No hay datos disponibles",
    icon: str = "\U0001F4ED",
    hint: str = "",
) -> None:
    """
    Renderiza un estado vacio cuando no hay datos.

    Args:
        message: Mensaje principal.
        icon: Emoji de estado vacio.
        hint: Pista de como resolver (ej: 'Ejecuta el pipeline primero').
    """
    st.markdown(
        f'<div style="text-align:center; padding:3rem; color:var(--eva-text-muted);">'
        f'<div style="font-size:3rem;">{icon}</div>'
        f'<h3 style="color:var(--eva-text);">{message}</h3>'
        + (f'<p>{hint}</p>' if hint else "")
        + "</div>",
        unsafe_allow_html=True,
    )
