"""Pagina 12: Alertas inteligentes."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.alerts import generate_alerts
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Alertas | EVA Valle", page_icon="\U0001F6A8", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(ttl=3600)
def get_alerts(df: pd.DataFrame) -> list:
    return generate_alerts(df)


def main() -> None:
    st.title("\U0001F6A8 Alertas Inteligentes")
    st.caption("El sistema detecta automaticamente riesgos y oportunidades")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    alerts = get_alerts(df)

    n_a = sum(1 for x in alerts if x["severidad"] == "ALERTA")
    n_v = sum(1 for x in alerts if x["severidad"] == "AVISO")
    n_d = sum(1 for x in alerts if x["severidad"] == "DESTAQUE")

    c1, c2, c3 = st.columns(3)
    c1.metric("\U0001F534 Alertas", n_a)
    c2.metric("\U0001F7E1 Avisos", n_v)
    c3.metric("\U0001F7E2 Destacados", n_d)
    st.markdown("---")

    for x in alerts:
        msg = f"**{x['titulo']}**\n\n{x['detalle']}"
        if x["severidad"] == "ALERTA":
            st.error(msg)
        elif x["severidad"] == "AVISO":
            st.warning(msg)
        else:
            st.success(msg)


main()
