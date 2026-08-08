"""Pagina 11: Comparador de municipios."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Comparador | EVA Valle", page_icon="\u2696\uFE0F", layout="wide")

COL_A = "#2E8B57"
COL_B = "#DD6B20"


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _stats(df_m: pd.DataFrame, df_all: pd.DataFrame) -> dict:
    prod = df_m["produccion_t"].sum()
    cos = df_m["area_cosechada_ha"].sum()
    return {
        "Produccion total (t)": round(float(prod), 0),
        "Area sembrada (ha)": round(float(df_m["area_sembrada_ha"].sum()), 0),
        "Rendimiento (t/ha)": round(float(prod / cos), 1) if cos else 0,
        "Cultivos activos": int(df_m["cultivo"].nunique()),
        "% del departamento": round(float(prod / df_all["produccion_t"].sum() * 100), 2),
    }


def main() -> None:
    st.title("\u2696\uFE0F Comparador de Municipios")
    st.caption("Analiza dos municipios lado a lado")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    munis = sorted(df["municipio"].dropna().unique().tolist())
    c1, c2 = st.columns(2)
    with c1:
        a = st.selectbox("Municipio A", munis, index=0)
    with c2:
        b = st.selectbox("Municipio B", munis, index=1 if len(munis) > 1 else 0)

    if a == b:
        st.warning("Selecciona dos municipios distintos.")
        return

    df_ab = df[df["municipio"].isin([a, b])]

    # KPIs lado a lado
    sa, sb = _stats(df[df["municipio"] == a], df), _stats(df[df["municipio"] == b], df)
    st.markdown("---")
    ka, kb = st.columns(2)
    with ka:
        st.markdown(f"### \U0001F170\uFE0F {a}")
        for k, v in sa.items():
            st.markdown(f"- **{k}:** {v:,.0f}" if isinstance(v, float) else f"- **{k}:** {v}")
    with kb:
        st.markdown(f"### \U0001F171\uFE0F {b}")
        for k, v in sb.items():
            st.markdown(f"- **{k}:** {v:,.0f}" if isinstance(v, float) else f"- **{k}:** {v}")

    st.markdown("---")

    # Produccion por ano (barras agrupadas)
    anual = (df_ab.groupby(["ano", "municipio"])["produccion_t"].sum().reset_index())
    fig1 = px.bar(anual, x="ano", y="produccion_t", color="municipio",
                  barmode="group", color_discrete_sequence=[COL_A, COL_B],
                  labels={"produccion_t": "Produccion (t)", "ano": "Ano"})
    fig1.update_layout(template="plotly_white", title="Produccion por ano")
    st.plotly_chart(fig1, use_container_width=True)

    # Rendimiento por ano (lineas)
    rend = (df_ab.groupby(["ano", "municipio"])
            .agg(prod=("produccion_t", "sum"), cos=("area_cosechada_ha", "sum"))
            .reset_index())
    rend["rend"] = rend["prod"] / rend["cos"].replace(0, 1)
    fig2 = px.line(rend, x="ano", y="rend", color="municipio", markers=True,
                   color_discrete_sequence=[COL_A, COL_B],
                   labels={"rend": "Rendimiento (t/ha)", "ano": "Ano"})
    fig2.update_layout(template="plotly_white", title="Rendimiento por ano (t/ha)")
    st.plotly_chart(fig2, use_container_width=True)


main()
