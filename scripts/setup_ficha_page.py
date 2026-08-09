"""Crea ui/pages/14_Ficha.py y la registra."""
from pathlib import Path

PAGE = '''"""Pagina 14: Ficha tecnica por cultivo."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.reports.crop_data import (crop_concentration, crop_kpis,
                                    crop_top_municipios, crop_yearly,
                                    filter_cultivo, interpretar_gini)
from core.reports.crop_report import build_crop_excel, build_crop_pdf
from ui.charts.spatial_map import plot_choropleth_municipios
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Ficha | EVA Valle", page_icon="\\U0001F4C7", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(ttl=3600)
def get_pdf(df: pd.DataFrame, cultivo: str) -> bytes:
    return build_crop_pdf(df, cultivo)


@st.cache_data(ttl=3600)
def get_excel(df: pd.DataFrame, cultivo: str) -> bytes:
    return build_crop_excel(df, cultivo)


def main() -> None:
    st.title("\\U0001F4C7 Ficha Tecnica por Cultivo")
    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    cultivos = sorted(df["cultivo"].dropna().unique().tolist())
    cultivo = st.selectbox("Selecciona un cultivo", cultivos)
    df_c = filter_cultivo(df, cultivo)

    k = crop_kpis(df_c, df)
    conc = crop_concentration(df_c)

    # Carne
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Produccion", f"{k['Produccion total (t)']:,.0f} t")
    c2.metric("Area", f"{k['Area sembrada (ha)']:,.0f} ha")
    c3.metric("Rendimiento", f"{k['Rendimiento (t/ha)']:.1f} t/ha")
    c4.metric("% del dpto.", f"{k['% del departamento']:.1f}%")
    c5.metric("Gini municipal", f"{conc['gini']:.2f}")
    st.caption(f"Concentracion territorial: **{interpretar_gini(conc['gini'])}** "
               f"(HHI={conc['hhi']:,.0f}; lider={conc['top1_pct']:.1f}%).")
    st.markdown("---")

    # Graficos
    left, right = st.columns(2)
    with left:
        y = crop_yearly(df_c)
        fig1 = px.bar(y, x="ano", y="produccion", color_discrete_sequence=["#2E8B57"],
                      labels={"produccion": "Produccion (t)", "ano": "Ano"})
        fig1.update_layout(template="plotly_white", title="Produccion por ano")
        st.plotly_chart(fig1, use_container_width=True)
    with right:
        top = crop_top_municipios(df_c, 8)
        fig2 = px.bar(top, y="municipio", x="produccion_t", orientation="h",
                      color_discrete_sequence=["#3182CE"],
                      labels={"produccion_t": "Produccion (t)", "municipio": ""})
        fig2.update_layout(template="plotly_white", title="Top municipios")
        st.plotly_chart(fig2, use_container_width=True)

    # Mini-mapa del cultivo
    st.subheader("\\U0001F5FA\\uFE0F Donde se produce")
    fig = plot_choropleth_municipios(df_c, "produccion_t", f"{cultivo} por municipio")
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # Export firmado
    st.markdown("---")
    safe = cultivo.replace(" ", "_").lower()
    e1, e2 = st.columns(2)
    with e1:
        st.download_button("\\U0001F4C4 Descargar PDF", data=get_pdf(df, cultivo),
                           file_name=f"ficha_{safe}.pdf", mime="application/pdf",
                           use_container_width=True)
    with e2:
        st.download_button("\\U0001F4CA Descargar Excel", data=get_excel(df, cultivo),
                           file_name=f"ficha_{safe}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)


main()
'''

if __name__ == "__main__":
    Path("ui/pages/14_Ficha.py").write_text(PAGE, encoding="utf-8")
    print("[OK] ui/pages/14_Ficha.py")

    app = Path("app.py")
    c = app.read_text(encoding="utf-8")
    anchor = 'st.Page("ui/pages/13_Treemap.py"'
    nueva = '    st.Page("ui/pages/14_Ficha.py", title="Ficha Tecnica", icon="\\U0001F4C7"),\n'
    if anchor in c and "14_Ficha.py" not in c:
        i = c.find(anchor)
        fin = c.find("\n", i)
        c = c[: fin + 1] + nueva + c[fin + 1 :]
        app.write_text(c, encoding="utf-8")
        print("[OK] app.py (pagina Ficha Tecnica)")
    print("\nEjecuta: streamlit run app.py")