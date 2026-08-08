"""Cards de metricas KPI estilizadas."""
from __future__ import annotations

import streamlit as st


def render_kpi_card(
    label: str,
    value: str,
    delta: str = "",
    delta_type: str = "neutral",
    icon: str = "",
) -> None:
    """
    Renderiza una card de metrica KPI.

    Args:
        label: Nombre de la metrica.
        value: Valor principal formateado.
        delta: Variacion porcentual o texto de cambio.
        delta_type: 'positive', 'negative' o 'neutral'.
        icon: Emoji o icono de la metrica.
    """
    delta_html = ""
    if delta:
        delta_html = f'<div class="metric-delta {delta_type}">{delta}</div>'

    icon_html = f'<div class="metric-icon">{icon}</div>' if icon else ""

    st.markdown(
        f'<div class="eva-metric-card">'
        f'{icon_html}'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_kpi_row(kpis: list[dict[str, str]], cols: int = 4) -> None:
    """
    Renderiza una fila de cards KPI.

    Args:
        kpis: Lista de dicts con keys: label, value, delta, delta_type, icon.
        cols: Numero de columnas (default 4).
    """
    columns = st.columns(cols)
    for i, kpi in enumerate(kpis):
        with columns[i % cols]:
            render_kpi_card(
                label=kpi.get("label", ""),
                value=kpi.get("value", ""),
                delta=kpi.get("delta", ""),
                delta_type=kpi.get("delta_type", "neutral"),
                icon=kpi.get("icon", ""),
            )
