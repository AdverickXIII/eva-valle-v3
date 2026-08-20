"""Pagina 20: Ficha interactiva cultivo x municipio (layout apilado + PDF con graficos)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from config.settings import settings
from ui.charts.crop_card import (diagnostic_subset, plot_crop_motor,
                                 plot_crop_serie, plot_top_municipios)
from core.reports.ficha_pdf import build_ficha_pdf

st.set_page_config(page_title="Ficha Cultivo | EVA Valle", page_icon="🌱", layout="wide")


@st.cache_data(ttl=3600)
def load():
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()


df = load()
if df.empty:
    st.error("Dataset no encontrado.")
    st.stop()

st.title("🌱 Ficha Tecnica Interactiva: cultivo x municipio")
st.caption("Selecciona cultivo y ambito; consulta CAGR, serie, elasticidad y descarga el PDF con graficos.")

c1, c2 = st.columns(2)
with c1:
    cultivos = (df.groupby("cultivo")["produccion_t"].sum()
                .sort_values(ascending=False).index.tolist())
    cultivo = st.selectbox("Cultivo (todos disponibles)", cultivos)
with c2:
    muns = ["Todo el Valle"] + sorted(df["municipio"].unique().tolist())
    ambito = st.selectbox("Municipio", muns)

sub = df[df["cultivo"] == cultivo]
if ambito != "Todo el Valle":
    sub = sub[sub["municipio"] == ambito]

if sub.empty or sub["produccion_t"].sum() <= 0:
    st.warning("Sin datos para esa combinacion cultivo-municipio.")
    st.stop()

total_ref = (df["produccion_t"].sum() if ambito == "Todo el Valle"
             else df[df["cultivo"] == cultivo]["produccion_t"].sum())
diag = diagnostic_subset(sub, total_ref)

# KPIs en dos filas de tres (mas aire)
r1a, r1b, r1c = st.columns(3)
r1a.metric("Produccion acumulada", f"{diag['prod_total']:,.0f} t")
r1b.metric("CAGR produccion", f"{diag['cagr_prod']:+.1f}%")
r1c.metric("CAGR area", f"{diag['cagr_area']:+.1f}%")
r2a, r2b, r2c = st.columns(3)
r2a.metric("CAGR rendimiento", f"{diag['cagr_rend']:+.1f}%")
r2b.metric("Elasticidad",
           f"{diag['elasticidad']:.2f}" if diag["elasticidad"] is not None else "n/d")
r2c.metric("Motor", diag["tipo"])

st.info(f"**{cultivo} — {ambito}:** {diag['narrativa']}")

# Graficos APILADOS a ancho completo, con espacio entre ellos
fig_serie = plot_crop_serie(diag, f"Serie historica: {cultivo} ({ambito})")
st.plotly_chart(fig_serie, use_container_width=True)

fig_motor = plot_crop_motor(diag)
st.plotly_chart(fig_motor, use_container_width=True)

figs_pdf = [("Serie historica", fig_serie), ("Motor del crecimiento", fig_motor)]

if ambito == "Todo el Valle":
    fig_top = plot_top_municipios(sub, cultivo)
    st.plotly_chart(fig_top, use_container_width=True)
    figs_pdf.append(("Top 10 municipios", fig_top))
else:
    st.subheader("Top 5 municipios del cultivo (referencia departamental)")
    st.dataframe(diag["top_mun"], use_container_width=True, hide_index=True)

st.markdown("---")
pdf = build_ficha_pdf(cultivo, ambito, diag["agg"], diag)
nombre = "".join(ch for ch in f"ficha_{cultivo}_{ambito}" if ch.isalnum() or ch in "_-") + ".pdf"
st.download_button("⬇️ Descargar ficha en PDF (con graficos)", data=pdf,
                   file_name=nombre, mime="application/pdf")

st.caption("Fuente: UPRA - EVA 2019-2025.")
