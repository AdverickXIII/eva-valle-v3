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
from core.analytics.forecast import (elegir_mejor, proyectar_con_ic,
                                      proyectar_estable_con_ic)
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


@st.cache_data(ttl=3600, show_spinner="Calculando proyeccion (estable + tendencial)...")
def _proyectar_cacheado(serie: pd.Series, horizonte: int) -> tuple:
    """AUD-UI-022: devuelve (oficial=estable, referencia=ensemble)."""
    return (
        proyectar_estable_con_ic(serie, n_steps=horizonte),
        proyectar_con_ic(serie, n_steps=horizonte),
    )


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

    # ---------- PROYECCION DUAL (AUD-UI-022) ----------
    res_estable, res_ensemble = _proyectar_cacheado(serie, horizonte)
    if res_estable["modelo"] is None or res_ensemble["modelo"] is None:
        st.error("No se pudo calcular la proyeccion.")
        return

    # KPIs - oficial = estable (naive), referencia = ensemble
    ultimo = int(serie.index[-1])
    ultimo_v = float(serie.iloc[-1])
    proy_oficial = float(res_estable["prediccion"][-1])
    proy_ref = float(res_ensemble["prediccion"][-1])
    var_pct_oficial = (proy_oficial / ultimo_v - 1) * 100
    var_pct_ref = (proy_ref / ultimo_v - 1) * 100
    mape_ensemble = res_ensemble["mape"]

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(f"Ultimo ano ({ultimo})", f"{ultimo_v:,.0f} t")
    k2.metric(f"Oficial {ultimo + horizonte}", f"{proy_oficial:,.0f} t",
              delta=f"{var_pct_oficial:+.1f}%",
              help="Escenario estable (naive) - proyeccion oficial")
    k3.metric("Referencia tendencial", f"{proy_ref:,.0f} t",
              delta=f"{var_pct_ref:+.1f}%",
              help="Ensemble local (Holt/lineal/PM/MLP) - referencia")
    k4.metric("MAPE ensemble", f"{mape_ensemble:.1f}%",
              help="Error del ensemble en backtest (ultimos 2 anos)")
    k5.metric("Modelo ensemble", res_ensemble["ganador"].replace("Suavizado exponencial ", ""))

    # ---------- GRAFICO DUAL (AUD-UI-022) ----------
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines+markers",
                             name="Historico", line=dict(color="#2E8B57", width=3)))
    anos_fut = np.arange(ultimo + 1, ultimo + 1 + horizonte)
    # IC del escenario oficial (estable/naive) - ensanchado con sqrt(t)
    fig.add_trace(go.Scatter(
        x=np.concatenate([anos_fut, anos_fut[::-1]]),
        y=np.concatenate([res_estable["escenarios"]["ic_alto"],
                          res_estable["escenarios"]["ic_bajo"][::-1]]),
        fill="toself", fillcolor="rgba(94,168,220,0.25)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 50% (oficial)", showlegend=True))
    # Escenario oficial: estable (naive) - linea solida
    fig.add_trace(go.Scatter(x=anos_fut, y=res_estable["escenarios"]["tendencial"],
                             mode="lines+markers", name="Oficial (estable)",
                             line=dict(color="#2E8B57", width=4)))
    # Escenario de referencia: ensemble - linea punteada
    fig.add_trace(go.Scatter(x=anos_fut, y=res_ensemble["escenarios"]["tendencial"],
                             mode="lines+markers", name="Referencia (tendencial)",
                             line=dict(color="#DD6B20", width=2.5, dash="dash")))
    # Union historico-proyeccion oficial
    fig.add_trace(go.Scatter(
        x=[ultimo, anos_fut[0]],
        y=[ultimo_v, res_estable["escenarios"]["tendencial"][0]],
        mode="lines", line=dict(color="#2E8B57", width=4, dash="dash"),
        showlegend=False))
    fig.update_layout(template="plotly_white", height=480,
                      title=f"{cultivo} en {muni} - Proyeccion oficial vs referencia",
                      yaxis_title="Produccion (t)")
    st.plotly_chart(fig, use_container_width=True)

    # ---------- TABLA DE ESCENARIOS DUAL (AUD-UI-022) ----------
    rows = []
    for i, an in enumerate(anos_fut):
        rows.append({
            "Ano": int(an),
            "Oficial (estable)": f"{res_estable['escenarios']['tendencial'][i]:,.0f}",
            "IC 50% (oficial)": f"{res_estable['escenarios']['ic_bajo'][i]:,.0f} - "
                                f"{res_estable['escenarios']['ic_alto'][i]:,.0f}",
            "Referencia (tendencial)": f"{res_ensemble['escenarios']['tendencial'][i]:,.0f}",
            "Diferencia": f"{res_ensemble['escenarios']['tendencial'][i] - res_estable['escenarios']['tendencial'][i]:+,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Interpretacion automatica (AUD-UI-022)
    st.info(
        f"**Proyeccion oficial:** escenario estable (naive) = {proy_oficial:,.0f} t "
        f"en {int(anos_fut[-1])} ({var_pct_oficial:+.1f}% vs {ultimo}). "
        f"El intervalo de confianza se ensancha con el tiempo (propiedad de random walks). "
        f"**Referencia tendencial:** ensemble ({res_ensemble['ganador']}) = {proy_ref:,.0f} t "
        f"({var_pct_ref:+.1f}% vs {ultimo}, MAPE backtest {mape_ensemble:.1f}%). "
        f"La proyeccion oficial usa el ultimo valor observado porque el ensemble "
        f"no supera al naive en el holdout 2024-2025 (Gate 3)."
    )
    st.caption(
        "TimesFM 2.5 (modelo fundacional, Google) fue evaluado en el mismo holdout "
        "y no supero al naive (WAPE mediano anual 17.3% vs 11.1%; semestral 39.5% "
        "vs 33.3%). Se documenta como resultado negativo en la auditoria."
    )

    # ---------- RANKING DE MODELOS (backtest del ensemble) ----------
    with st.expander("🔬 Comparativa de modelos (backtest del ensemble)"):
        st.caption("Ranking interno del ensemble (referencia tendencial). "
                   "Se ocultan los ultimos 2 anos, se entrena cada modelo con "
                   "el resto y se mide el error al predecirlos.")
        filas = []
        for r in res_ensemble["ranking"]:
            filas.append({
                "Modelo": r["modelo"]["nombre"],
                "MAPE (%)": f"{r['mape']:.1f}",
                "Ganador": "✅" if r is res_ensemble["ranking"][0] else "",
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
            data=build_predictivo_pdf(cultivo, muni, serie, res_ensemble, horizonte),
            file_name=f"proyeccion_{cultivo}_{muni}.pdf".lower().replace(" ", "_"),
            mime="application/pdf", use_container_width=True)


run_safe(main)
