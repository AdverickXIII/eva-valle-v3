"""Pagina 12: Centro de Alertas (filtros, radar, tabla y exportacion)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.alerts import (generate_alerts, indice_riesgo_municipal)
from core.reports.riesgo_report import build_riesgo_pdf
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Alertas | EVA Valle", page_icon="🚨", layout="wide")


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
    st.title("🚨 Centro de Alertas")
    st.caption("Monitoreo automatico: riesgos, dependencias y oportunidades del agro vallecaucano")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    alerts = get_alerts(df)
    df_a = pd.DataFrame(alerts)

    n_a = sum(1 for x in alerts if x["severidad"] == "ALERTA")
    n_v = sum(1 for x in alerts if x["severidad"] == "AVISO")
    n_d = sum(1 for x in alerts if x["severidad"] == "DESTAQUE")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚨 Total", len(alerts))
    k2.metric("🔴 Alertas", n_a)
    k3.metric("🟡 Avisos", n_v)
    k4.metric("🟢 Destacados", n_d)
    st.markdown("---")

    # ---------- FILTROS ----------
    f1, f2, f3 = st.columns(3)
    with f1:
        sev_sel = st.multiselect("Severidad",
                                 ["ALERTA", "AVISO", "DESTAQUE"],
                                 default=["ALERTA", "AVISO", "DESTAQUE"])
    with f2:
        tip_sel = st.multiselect("Tipo de alerta",
                                 sorted(df_a["tipo"].unique().tolist()),
                                 default=sorted(df_a["tipo"].unique().tolist()))
    with f3:
        munis_con = sorted(df["municipio"].dropna().unique().tolist())
        mun_sel = st.selectbox("Municipio", ["Todos"] + munis_con)

    df_f = df_a[df_a["severidad"].isin(sev_sel) & df_a["tipo"].isin(tip_sel)]
    if mun_sel != "Todos":
        df_f = df_f[(df_f["municipio"] == mun_sel) | (df_f["municipio"] == "-")]

    st.caption(f"{len(df_f)} alertas tras filtros.")

    if mun_sel != "Todos":
        n_mun = len(df_f[df_f["municipio"] == mun_sel])
        if n_mun == 0:
            prod_mun = float(df[df["municipio"] == mun_sel]["produccion_t"].sum())
            tot_dept = float(df["produccion_t"].sum()) or 1.0
            if prod_mun >= 5000:
                st.success(f"✅ **{mun_sel}** no tiene alertas activas con los filtros "
                           f"actuales: municipio con volumen significativo "
                           f"({prod_mun:,.0f} t) y sin riesgos detectados.")
            else:
                st.info(f"ℹ️ **{mun_sel}** registra {prod_mun:,.0f} t "
                        f"({prod_mun / tot_dept * 100:.2f}% del departamento), por "
                        f"debajo del umbral de analisis (5,000 t). La ausencia de "
                        f"alertas NO indica buen desempeno: refleja una economia "
                        f"agricola marginal.")

    # ---------- INDICE DE RIESGO TERRITORIAL (42 municipios, sin filtros) ----------
    st.markdown("#### 🗺️ Indice de Riesgo Territorial (42 municipios)")
    df_ir = indice_riesgo_municipal(df)
    fig = go.Figure(go.Bar(
        y=df_ir["municipio"], x=df_ir["score"], orientation="h",
        marker=dict(color=df_ir["score"], colorscale="RdYlGn_r",
                    colorbar=dict(title="Riesgo")),
        customdata=df_ir[["dependencia", "baja_diversidad", "declive", "caida"]].values,
        hovertemplate="%{y}: %{x:.0f}/100<br>Dependencia %{customdata[0]:.0f} · "
                      "Baja diversidad %{customdata[1]:.0f} · "
                      "Declive %{customdata[2]:.0f} · Caida %{customdata[3]:.0f}<extra></extra>"))
    fig.update_layout(height=1250, xaxis=dict(range=[0, 100],
                      title="Riesgo (0-100)"), margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Indice compuesto = dependencia de un cultivo + baja diversidad + "
               "declive sostenido + caida reciente. Es contexto estructural: "
               "no cambia con los filtros de alertas.")

    st.download_button("⬇️ Descargar Indice de Riesgo (PDF)",
                       data=build_riesgo_pdf(df_ir),
                       file_name="indice_riesgo_territorial_valle.pdf",
                       mime="application/pdf")

    # ---------- TABLA + CSV ----------
    st.subheader("📋 Detalle de alertas")
    show = df_f[["severidad", "tipo", "municipio", "cultivo", "titulo", "detalle"]]
    st.dataframe(show, use_container_width=True, height=380, hide_index=True)
    st.download_button("⬇️ Descargar alertas (CSV)",
                       data=show.to_csv(index=False).encode("utf-8"),
                       file_name="alertas_eva_valle.csv", mime="text/csv")

    st.markdown("---")

    # ---------- TARJETAS ----------
    st.subheader("🔔 Narrativa de alertas")
    for _, x in df_f.iterrows():
        msg = f"**{x['titulo']}**\n\n{x['detalle']}"
        if x["severidad"] == "ALERTA":
            st.error(msg)
        elif x["severidad"] == "AVISO":
            st.warning(msg)
        else:
            st.success(msg)


main()
