"""Pagina 4: Predictivo v2 (forecast robusto + ML)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.forecast import elegir_mejor, proyectar_con_ic
from core.reports.predictivo_pdf import build_predictivo_pdf
from ui.components.loading_states import render_empty_state
from ui.services.error_handler import run_safe

st.set_page_config(page_title="Predictivo | EVA Valle", page_icon="\U0001F916", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def main() -> None:
    st.title("\U0001F916 Analisis Predictivo")
    st.caption("Proyeccion 2026-2028 con seleccion automatica de modelo y backtesting")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    # ---------- SELECTORES ----------
    c1, c2, c3 = st.columns(3)
    with c1:
        cultivos = (df.groupby("cultivo")["produccion_t"].sum()
                    .sort_values(ascending=False).index.tolist())
        cultivo = st.selectbox("Cultivo", cultivos)
    with c2:
        munis = ["Todo el departamento"] + sorted(df["municipio"].unique().tolist())
        muni = st.selectbox("Municipio", munis)
    with c3:
        horizonte = st.slider("Horizonte (anos)", 1, 5, 3)

    df_c = df[df["cultivo"] == cultivo].copy()
    if muni != "Todo el departamento":
        df_c = df_c[df_c["municipio"] == muni]
    if df_c.empty:
        st.warning("Sin datos para esa combinacion.")
        return

    # Serie anual
    serie = df_c.groupby("ano")["produccion_t"].sum().sort_index()
    if len(serie) < 4:
        st.error("Serie demasiado corta (se necesitan al menos 4 anos).")
        return

    # ---------- PROYECCION ----------
    res = proyectar_con_ic(serie, n_steps=horizonte)
    modelo = res["modelo"]
    if modelo is None:
        st.error("No se pudo ajustar ningun modelo.")
        return

    # KPIs
    ultimo = int(serie.index[-1])
    ultimo_v = float(serie.iloc[-1])
    proy_base = float(res["prediccion"][-1])
    var_pct = (proy_base / ultimo_v - 1) * 100
    mape = res["mape"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(f"Ultimo ano ({ultimo})", f"{ultimo_v:,.0f} t")
    k2.metric(f"Proyeccion {ultimo + horizonte}", f"{proy_base:,.0f} t",
              delta=f"{var_pct:+.1f}%")
    k3.metric("MAPE backtest", f"{mape:.1f}%",
              help="Error medio al predecir los ultimos 2 anos desde el resto")
    k4.metric("Modelo ganador", res["ganador"].replace("Suavizado exponencial ", ""))
    k5.metric("Conservador", f"{float(res['escenarios']['conservador'][-1]):,.0f} t")

    # ---------- GRAFICO ----------
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines+markers",
                             name="Historico", line=dict(color="#2E8B57", width=3)))
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    # IC
    fig.add_trace(go.Scatter(
        x=np.concatenate([anos_fut, anos_fut[::-1]]),
        y=np.concatenate([res["escenarios"]["ic_alto"],
                          res["escenarios"]["ic_bajo"][::-1]]),
        fill="toself", fillcolor="rgba(94,168,220,0.25)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 50%", showlegend=True))
    # Escenarios
    fig.add_trace(go.Scatter(x=anos_fut, y=res["escenarios"]["conservador"],
                             mode="lines", name="Conservador (P10)",
                             line=dict(color="#DD6B20", dash="dot", width=1.5)))
    fig.add_trace(go.Scatter(x=anos_fut, y=res["escenarios"]["tendencial"],
                             mode="lines+markers", name="Tendencial",
                             line=dict(color="#DD6B20", width=3)))
    fig.add_trace(go.Scatter(x=anos_fut, y=res["escenarios"]["optimista"],
                             mode="lines", name="Optimista (P90)",
                             line=dict(color="#2E8B57", dash="dot", width=1.5)))
    # Union historico-proyeccion
    fig.add_trace(go.Scatter(
        x=[ultimo, anos_fut[0]],
        y=[ultimo_v, res["escenarios"]["tendencial"][0]],
        mode="lines", line=dict(color="#DD6B20", width=3, dash="dash"),
        showlegend=False))
    fig.update_layout(template="plotly_white", height=480,
                      title=f"{cultivo} en {muni} - Proyeccion con IC",
                      yaxis_title="Produccion (t)")
    st.plotly_chart(fig, use_container_width=True)

    # ---------- TABLA DE ESCENARIOS ----------
    rows = []
    for i, an in enumerate(anos_fut):
        rows.append({
            "Ano": int(an),
            "Conservador (P10)": f"{res['escenarios']['conservador'][i]:,.0f}",
            "Tendencial": f"{res['escenarios']['tendencial'][i]:,.0f}",
            "Optimista (P90)": f"{res['escenarios']['optimista'][i]:,.0f}",
            "IC 50%": f"{res['escenarios']['ic_bajo'][i]:,.0f} - "
                      f"{res['escenarios']['ic_alto'][i]:,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Interpretacion automatica
    if mape < 10:
        nivel = "alta"
    elif mape < 20:
        nivel = "moderada"
    else:
        nivel = "baja"
    st.info(f"**Interpretacion:** El modelo **{res['ganador']}** fue seleccionado "
            f"automaticamente por tener el menor MAPE ({mape:.1f}%) al predecir "
            f"los ultimos 2 anos. Credibilidad del forecast: **{nivel}**. "
            f"Escenario tendencial: {proy_base:,.0f} t en {int(anos_fut[-1])} "
            f"({var_pct:+.1f}% vs {ultimo}).")

    # ---------- RANKING DE MODELOS (backtest) ----------
    with st.expander("🔬 Comparativa de modelos (backtest)"):
        st.caption("Se ocultan los ultimos 2 anos, se entrena cada modelo con "
                   "el resto y se mide el error al predecirlos. "
                   "El que menos se equivoca, gana.")
        filas = []
        for r in res["ranking"]:
            filas.append({
                "Modelo": r["modelo"]["nombre"],
                "MAPE (%)": f"{r['mape']:.1f}",
                "Ganador": "✅" if r is res["ranking"][0] else "",
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    # ---------- EXPORTACION ----------
    st.markdown("---")
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "⬇️ Descargar proyeccion (CSV)",
            data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
            file_name=f"proyeccion_{cultivo}_{muni}.csv".lower().replace(" ", "_"),
            mime="text/csv", use_container_width=True)
    with d2:
        st.download_button(
            "⬇️ Descargar proyeccion (PDF)",
            data=build_predictivo_pdf(cultivo, muni, serie, res, horizonte),
            file_name=f"proyeccion_{cultivo}_{muni}.pdf".lower().replace(" ", "_"),
            mime="application/pdf", use_container_width=True)


run_safe(main)
