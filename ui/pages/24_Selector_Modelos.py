"""Pagina 24: Selector de modelos por bandits (puente M3 a produccion)."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from core.analytics.model_selector import (recomendar, municipios, cultivos_de,
                                           ARMS, EPS, CRITICOS)

st.set_page_config(page_title="Selector de Modelos | EVA Valle", page_icon="\U0001F3B0",
                   layout="wide")
st.title("\U0001F3B0 Selector de modelos por bandits")
st.caption(f"Candidatos: {', '.join(ARMS)} | shrinkage empirico (N0=4) | IC 95%. "
           f"Exploracion etica: eps={EPS}, solo si IC se solapan y cultivo no critico "
           f"({', '.join(sorted(CRITICOS))}).")

mun = st.selectbox("Municipio", municipios())
cultivos = cultivos_de(mun)

rows, n_exp, n_pm3a = [], 0, 0
for cul in cultivos:
    r = recomendar(mun, cul)
    n_exp += r["explorar"]
    n_pm3a += r["modelo"] == "PM3A"
    rows.append({"cultivo": cul, "modelo": r["modelo"], "ape_est": r["ape_est"],
                 "ic95": f"[{r['ic'][0]}, {r['ic'][1]}]",
                 "explorar": "si" if r["explorar"] else "no",
                 "alternativa": r["alternativa"]})
R = pd.DataFrame(rows)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Campeon mas frecuente", R.modelo.mode().iloc[0])
k2.metric("Series donde PM3A sigue ganando", f"{n_pm3a}/{len(R)}")
k3.metric("Exploracion recomendada", f"{n_exp}/{len(R)}")
k4.metric("Regret vs status quo (torneo M3)", "-58%")

st.markdown("#### Recomendacion por cultivo (2026)")
c1, c2 = st.columns([3, 2])
with c1:
    st.table(R)
with c2:
    fig = go.Figure(go.Bar(x=R.modelo.value_counts().reindex(ARMS).fillna(0),
                           y=ARMS, orientation="h", marker_color="#5FA8DC"))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.info("**Etica de la exploracion:** solo se experimenta cuando hay duda real "
        "(IC solapados) y en cultivos que no comprometen seguridad alimentaria. "
        "En politica publica, explorar sin estas cotas seria irresponsable.")
