"""Reescribe ui/pages/15_Ejecutivo.py con analisis dual con/sin cana."""
from pathlib import Path

PAGE = '''"""Pagina 15: Resumen ejecutivo (estandar profesional) con analisis dual."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.executive import executive_summary
from core.analytics.pareto import (conc_metrics, pareto, quality,
                                   recomendaciones, territorial, tiering)
from core.reports.executive_report import build_executive_pdf
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Resumen | EVA Valle", page_icon="\\U0001F4CB", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(ttl=3600)
def get_summary(df: pd.DataFrame) -> dict:
    return executive_summary(df)


@st.cache_data(ttl=3600)
def get_pdf(df: pd.DataFrame) -> bytes:
    return build_executive_pdf(df)


def _pareto_fig(p: pd.DataFrame, titulo: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=p["cultivo"], y=p["share"], name="% individual",
                         marker_color="#2E8B57"))
    fig.add_trace(go.Scatter(x=p["cultivo"], y=p["cum"], name="% acumulado",
                             mode="lines+markers", yaxis="y2",
                             line=dict(color="#DD6B20", width=2)))
    fig.update_layout(
        template="plotly_white", title=titulo,
        yaxis=dict(title="% de la produccion"),
        yaxis2=dict(overlaying="y", side="right", range=[0, 100],
                    title="% acumulado"),
        xaxis=dict(tickangle=-40), height=420,
        legend=dict(orientation="h", y=1.15))
    return fig


def main() -> None:
    st.title("\\U0001F4CB Resumen Ejecutivo")
    st.caption("Vista de alto nivel - UPRA 2019-2024 - estandar profesional")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    s = get_summary(df)

    # 1. Panorama (KPIs con deltas)
    st.subheader("1. Panorama general")
    cols = st.columns(5)
    for col, k in zip(cols, s["kpis"]):
        col.metric(k["label"], k["value"], k["delta"])
    st.markdown("---")

    # 2. Concentracion productiva: CON cana vs SIN cana
    st.subheader("2. Concentracion productiva: con cana vs sin cana")
    cc, sc = conc_metrics(df, False), conc_metrics(df, True)
    comp = pd.DataFrame({
        "Indicador": ["HHI", "Gini", "Top 1 cultivo (%)", "Cultivos que explican 80%"],
        "Con cana": [f"{cc['hhi']:,.0f}", cc["gini"], f"{cc['top1_pct']:.1f} ({cc['top1']})", cc["n80"]],
        "Sin cana": [f"{sc['hhi']:,.0f}", sc["gini"], f"{sc['top1_pct']:.1f} ({sc['top1']})", sc["n80"]],
    })
    st.dataframe(comp, hide_index=True, use_container_width=True)
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(_pareto_fig(pareto(df, False), "Pareto CON cana"),
                        use_container_width=True)
    with g2:
        st.plotly_chart(_pareto_fig(pareto(df, True), "Pareto SIN cana"),
                        use_container_width=True)
    st.caption("\\U0001F4A1 Sin cana emerge la estructura real del resto del sector: "
               "frutas, platano y cultivos de exportacion ganan protagonismo.")
    st.markdown("---")

    # 3. Concentracion territorial + tipificacion
    st.subheader("3. Distribucion territorial")
    ter = territorial(df)
    st.caption(f"Gini territorial={ter['gini']:.2f} | HHI={ter['hhi']:,.0f} | "
               f"Lider: {ter['top']} ({ter['top_pct']:.1f}%)")
    t1, t2 = st.columns(2)
    with t1:
        st.dataframe(tiering(df), hide_index=True, use_container_width=True, height=300)
    with t2:
        fig = px.bar(s["top_municipios"], y="municipio", x="produccion_t", orientation="h",
                     color_discrete_sequence=["#3182CE"],
                     labels={"produccion_t": "Produccion (t)", "municipio": ""})
        fig.update_layout(template="plotly_white", title="Top municipios", height=300)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    # 4. Tendencias + dinamica
    st.subheader("4. Tendencias y dinamica")
    l, r = st.columns(2)
    with l:
        fig = px.line(s["tendencia"], x="ano", y="produccion", markers=True,
                      color_discrete_sequence=["#2E8B57"],
                      labels={"produccion": "Produccion (t)", "ano": "Ano"})
        fig.update_layout(template="plotly_white", title="Produccion por ano")
        st.plotly_chart(fig, use_container_width=True)
    with r:
        st.markdown("**Crecen (CAGR)**")
        st.dataframe(s["crecen"][["cultivo", "cagr"]], hide_index=True)
        st.markdown("**Declinan (CAGR)**")
        st.dataframe(s["declinan"][["cultivo", "cagr"]], hide_index=True)
    st.markdown("---")

    # 5. Calidad del dato
    st.subheader("5. Calidad y confiabilidad del dato")
    q = quality(df)
    st.caption(f"Fuente: {q['fuente']} | Cobertura: {q['cobertura']} | "
               f"{q['registros']:,} registros | Anomalias (cosechada>sembrada): "
               f"{q['pct_anomalia']}% | Vacios: {q['pct_nulos']}%")
    st.info("Las anomalias y vacios se declaran explicitamente; interpretar los "
            "promedios con esta salvedad.")
    st.markdown("---")

    # 6. Hallazgos / mensajes clave
    st.subheader("6. Hallazgos clave")
    for m in s["mensajes"]:
        st.markdown(f"- {m}")
    st.markdown("---")

    # 7. Recomendaciones
    st.subheader("7. Recomendaciones")
    for titulo, detalle in recomendaciones(df):
        st.markdown(f"**{titulo}.** {detalle}")

    st.markdown("---")
    st.download_button("\\U0001F4C4 Descargar Resumen Ejecutivo (PDF)",
                       data=get_pdf(df), file_name="resumen_ejecutivo.pdf",
                       mime="application/pdf", use_container_width=True)


main()
'''

Path("ui/pages/15_Ejecutivo.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/15_Ejecutivo.py (dual con/sin cana)")
print("\nEjecuta: streamlit run app.py")