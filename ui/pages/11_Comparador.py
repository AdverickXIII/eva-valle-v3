"""Pagina 11: Comparador de municipios (cara a cara profesional)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.loading_states import render_empty_state
from core.reports.comparador_pdf import build_comparador_pdf

st.set_page_config(page_title="Comparador | EVA Valle", page_icon="⚖️", layout="wide")

COL_A = "#2E8B57"
COL_B = "#DD6B20"


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _stats(df_m: pd.DataFrame, df_all: pd.DataFrame) -> dict:
    prod = float(df_m["produccion_t"].sum())
    sem = float(df_m["area_sembrada_ha"].sum())
    cos = float(df_m["area_cosechada_ha"].sum())
    g = df_m.groupby("cultivo")["produccion_t"].sum()
    g = g[g > 0]
    p = g / g.sum() if g.sum() else p
    shannon = float(-(p * np.log(p)).sum()) if len(p) else 0.0
    anual = df_m.groupby("ano")["produccion_t"].sum().sort_index()
    cagr = 0.0
    if len(anual) >= 2 and anual.iloc[0] > 0 and anual.iloc[-1] > 0:
        n = len(anual) - 1
        cagr = ((anual.iloc[-1] / anual.iloc[0]) ** (1 / n) - 1) * 100
    return {
        "Produccion total (t)": prod,
        "Area sembrada (ha)": sem,
        "Rendimiento (t/ha)": prod / cos if cos else 0.0,
        "Cultivos activos": int(df_m["cultivo"].nunique()),
        "% del departamento": prod / df_all["produccion_t"].sum() * 100
        if df_all["produccion_t"].sum() else 0.0,
        "Diversidad (Shannon)": shannon,
        "CAGR 2019-2025 (%)": cagr,
        "Top cultivo": g.idxmax() if len(g) else "-",
    }


def plot_mariposa(df_ab: pd.DataFrame, a: str, b: str):
    g = (df_ab.groupby(["grupo_cultivo", "municipio"])["produccion_t"]
         .sum().reset_index())
    piv = (g.pivot_table(index="grupo_cultivo", columns="municipio",
                         values="produccion_t", fill_value=0)
           .reindex(columns=[a, b], fill_value=0))
    piv["tot"] = piv[a] + piv[b]
    piv = piv.sort_values("tot", ascending=True).tail(8)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=piv.index, x=-piv[a].values, orientation="h", name=a,
                         marker_color=COL_A, customdata=piv[a].values,
                         hovertemplate="%{y}<br>" + a + ": %{customdata:,.0f} t<extra></extra>"))
    fig.add_trace(go.Bar(y=piv.index, x=piv[b].values, orientation="h", name=b,
                         marker_color=COL_B, customdata=piv[b].values,
                         hovertemplate="%{y}<br>" + b + ": %{customdata:,.0f} t<extra></extra>"))
    xmax = float(piv[[a, b]].max().max()) or 1
    ticks = [-xmax, -xmax / 2, 0, xmax / 2, xmax]
    fig.update_layout(barmode="group", height=440,
                      xaxis=dict(tickvals=ticks,
                                 ticktext=[f"{abs(t)/1000:,.0f}k" for t in ticks]),
                      margin=dict(t=50, b=10, l=10, r=10))
    fig.update_layout(title="Cara a cara por grupo de cultivo (toneladas)")
    return fig


def plot_radar(sa: dict, sb: dict, a: str, b: str):
    keys = ["Produccion total (t)", "Rendimiento (t/ha)", "Diversidad (Shannon)",
            "CAGR 2019-2025 (%)", "Area sembrada (ha)"]
    labels = ["Produccion", "Rendimiento", "Diversidad", "Crecimiento", "Area"]
    ra, rb = [], []
    for k in keys:
        va, vb = max(0.0, sa[k]), max(0.0, sb[k])
        mx = max(va, vb) or 1.0
        ra.append(va / mx * 100)
        rb.append(vb / mx * 100)
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=ra + [ra[0]], theta=labels + [labels[0]],
                                  name=a, line=dict(color=COL_A, width=3),
                                  fill="toself", opacity=0.7))
    fig.add_trace(go.Scatterpolar(r=rb + [rb[0]], theta=labels + [labels[0]],
                                  name=b, line=dict(color=COL_B, width=3),
                                  fill="toself", opacity=0.7))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                      height=460, margin=dict(t=50, b=10, l=40, r=40),
                      title="Perfil economico (100 = el mejor de los dos)")
    return fig


def main() -> None:
    st.title("⚖️ Comparador de Municipios")
    st.caption("Cara a cara profesional: KPIs con ganador, mariposa por grupo, radar y exportacion")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    munis = sorted(df["municipio"].dropna().unique().tolist())
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        a = st.selectbox("Municipio A", munis, index=0)
    with c2:
        b = st.selectbox("Municipio B", munis, index=1 if len(munis) > 1 else 0)
    with c3:
        sin_cana = st.checkbox("Comparar sin caña (economia real)", value=False,
                               help="Con caña, la comparativa queda dominada por el "
                                    "monocultivo; sin caña comparas la matriz agricola real.")

    if a == b:
        st.warning("Selecciona dos municipios distintos.")
        return

    df_work = df[df["cultivo"] != "Caña"] if sin_cana else df
    df_ab = df_work[df_work["municipio"].isin([a, b])]
    if df_ab.empty:
        st.warning("Sin datos para esa combinacion.")
        return

    sa = _stats(df_work[df_work["municipio"] == a], df_work)
    sb = _stats(df_work[df_work["municipio"] == b], df_work)

    # ---------- TABLA CON GANADOR ----------
    st.markdown("---")
    filas = []
    for k in ["Produccion total (t)", "Area sembrada (ha)", "Rendimiento (t/ha)",
              "Cultivos activos", "% del departamento", "Diversidad (Shannon)",
              "CAGR 2019-2025 (%)"]:
        va, vb = sa[k], sb[k]
        win = "🤝 Empate" if abs(va - vb) < 1e-9 else (f"🅰️ {a}" if va > vb else f"🅱️ {b}")
        filas.append({"Indicador": k, f"A · {a}": f"{va:,.1f}",
                      f"B · {b}": f"{vb:,.1f}", "Gana": win})
    filas.append({"Indicador": "Top cultivo", f"A · {a}": sa["Top cultivo"],
                  f"B · {b}": sb["Top cultivo"], "Gana": "—"})
    comp_df = pd.DataFrame(filas)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    gana_a = sum(1 for f in filas if f["Gana"].startswith("🅰️"))
    gana_b = sum(1 for f in filas if f["Gana"].startswith("🅱️"))
    st.info(f"**Marcador:** {a} gana {gana_a} indicadores · {b} gana {gana_b} "
            f"· {'sin caña' if sin_cana else 'con caña'}.")

    safe = lambda s: "".join(ch for ch in s if ch.isalnum() or ch in "_-").lower()
    d1, d2 = st.columns(2)
    with d1:
        st.download_button("⬇️ Descargar comparativa (CSV)",
                           data=comp_df.to_csv(index=False).encode("utf-8"),
                           file_name=f"comparativa_{safe(a)}_vs_{safe(b)}.csv",
                           mime="text/csv", use_container_width=True)
    with d2:
        st.download_button("⬇️ Descargar comparativa (PDF)",
                           data=build_comparador_pdf(a, b, sin_cana, comp_df, sa, sb, df_ab),
                           file_name=f"comparativa_{safe(a)}_vs_{safe(b)}.pdf",
                           mime="application/pdf", use_container_width=True)

    st.markdown("---")

    # ---------- GRAFICOS ----------
    st.plotly_chart(plot_mariposa(df_ab, a, b), use_container_width=True)

    r1, r2 = st.columns(2)
    with r1:
        st.plotly_chart(plot_radar(sa, sb, a, b), use_container_width=True)
    with r2:
        anual = (df_ab.groupby(["ano", "municipio"])["produccion_t"].sum()
                 .reset_index())
        fig1 = px.bar(anual, x="ano", y="produccion_t", color="municipio",
                      barmode="group", color_discrete_sequence=[COL_A, COL_B],
                      labels={"produccion_t": "Produccion (t)", "ano": "Ano"})
        fig1.update_layout(template="plotly_white", title="Produccion por ano")
        st.plotly_chart(fig1, use_container_width=True)

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
