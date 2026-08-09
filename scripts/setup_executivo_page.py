"""Crea ui/pages/15_Ejecutivo.py y la registra."""
from pathlib import Path

PAGE = '''"""Pagina 15: Resumen ejecutivo (vista unica para gerencia)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.alerts import generate_alerts
from core.reports.crop_data import _gini, interpretar_gini
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
def get_pdf(df: pd.DataFrame) -> bytes:
    return build_executive_pdf(df)


def main() -> None:
    st.title("\\U0001F4CB Resumen Ejecutivo")
    st.caption("Vista unica para toma de decisiones - UPRA 2019-2024")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    prod = float(df["produccion_t"].sum())
    cos = float(df["area_cosechada_ha"].sum())
    g = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=True)
    hhi = float(((g / g.sum() * 100) ** 2).sum())
    gini = _gini(g.values)

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Produccion", f"{prod:,.0f} t")
    c2.metric("Area", f"{df['area_sembrada_ha'].sum():,.0f} ha")
    c3.metric("Rendimiento", f"{prod / cos:.1f} t/ha" if cos else "-")
    c4.metric("Municipios", df["municipio"].nunique())
    c5.metric("Gini", f"{gini:.2f}")
    st.caption(f"Concentracion: HHI={hhi:,.0f} | **{interpretar_gini(gini)}**")
    st.markdown("---")

    # Graficos
    l, r = st.columns(2)
    with l:
        y = df.groupby("ano")["produccion_t"].sum().reset_index()
        fig1 = px.line(y, x="ano", y="produccion_t", markers=True,
                       color_discrete_sequence=["#2E8B57"],
                       labels={"produccion_t": "Produccion (t)", "ano": "Ano"})
        fig1.update_layout(template="plotly_white", title="Produccion por ano")
        st.plotly_chart(fig1, use_container_width=True)
    with r:
        tc = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False) \
               .head(6).reset_index()
        fig2 = px.bar(tc, y="cultivo", x="produccion_t", orientation="h",
                      color_discrete_sequence=["#3182CE"],
                      labels={"produccion_t": "Produccion (t)", "cultivo": ""})
        fig2.update_layout(template="plotly_white", title="Top cultivos")
        st.plotly_chart(fig2, use_container_width=True)

    # Alertas + top municipios
    l2, r2 = st.columns(2)
    with l2:
        st.subheader("\\U0001F3C6 Top municipios")
        tm = df.groupby("municipio")["produccion_t"].sum() \
               .sort_values(ascending=False).head(6).reset_index()
        st.dataframe(tm, hide_index=True, use_container_width=True)
    with r2:
        st.subheader("\\U0001F6A8 Alertas principales")
        for a in generate_alerts(df)[:5]:
            msg = f"**{a['titulo']}**"
            if a["severidad"] == "ALERTA":
                st.error(msg)
            elif a["severidad"] == "AVISO":
                st.warning(msg)
            else:
                st.success(msg)

    st.markdown("---")
    st.download_button("\\U0001F4C4 Descargar Resumen Ejecutivo (PDF)",
                       data=get_pdf(df), file_name="resumen_ejecutivo.pdf",
                       mime="application/pdf", use_container_width=True)


main()
'''

if __name__ == "__main__":
    Path("ui/pages/15_Ejecutivo.py").write_text(PAGE, encoding="utf-8")
    print("[OK] ui/pages/15_Ejecutivo.py")

    app = Path("app.py")
    c = app.read_text(encoding="utf-8")
    anchor = 'st.Page("ui/pages/14_Ficha.py"'
    nueva = '    st.Page("ui/pages/15_Ejecutivo.py", title="Resumen Ejecutivo", icon="\\U0001F4CB"),\n'
    if anchor in c and "15_Ejecutivo.py" not in c:
        i = c.find(anchor)
        fin = c.find("\n", i)
        c = c[: fin + 1] + nueva + c[fin + 1 :]
        app.write_text(c, encoding="utf-8")
        print("[OK] app.py (pagina Resumen Ejecutivo)")
    print("\nEjecuta: streamlit run app.py")