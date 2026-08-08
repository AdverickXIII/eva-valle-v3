"""Reemplaza 7_Cultivos.py con version que incluye historico por municipio."""
from pathlib import Path

PAGE_CULTIVOS = '''"""Pagina 7: Cultivos - Analisis individual por producto y municipio."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.metrics_cards import render_kpi_row
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.theme import apply_theme, PALETTE, COLOR_POSITIVO, COLOR_NEGATIVO

st.set_page_config(page_title="Cultivos | EVA Valle", page_icon="\\U0001F331", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def orden_periodo(p) -> float:
    """Convierte un periodo (2023A/2023B/2023) a clave numerica ordenable."""
    p = str(p)
    try:
        ano = int(p[:4])
    except (ValueError, TypeError):
        return 0.0
    if len(p) == 5 and p[4] in "Aa":
        return ano + 0.25
    if len(p) == 5 and p[4] in "Bb":
        return ano + 0.75
    return ano + 0.5


def main() -> None:
    st.title("\\U0001F331 Analisis por Cultivo")
    st.caption("Estadisticas individuales de cada producto, a nivel departamental y municipal")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    # ── Selector de cultivo ──────────────────────────────────
    prod_por_cultivo = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    cultivos = prod_por_cultivo.index.tolist()
    cultivo_sel = st.selectbox("Selecciona un cultivo", cultivos, index=0)

    df_c = df[df["cultivo"] == cultivo_sel].copy()

    st.markdown("---")

    # ── KPIs departamentales del cultivo ─────────────────────
    prod_total = df_c["produccion_t"].sum()
    area_total = df_c["area_sembrada_ha"].sum()
    rend_prom = df_c["produccion_t"].sum() / max(df_c["area_cosechada_ha"].sum(), 1)
    n_muni = df_c["municipio"].nunique()
    share = prod_total / df["produccion_t"].sum() * 100

    render_kpi_row([
        {"label": f"Produccion {cultivo_sel}", "value": f"{prod_total:,.0f} t", "icon": "\\U0001F33E"},
        {"label": "Area Sembrada", "value": f"{area_total:,.0f} ha", "icon": "\\U0001F4D0"},
        {"label": "Rendimiento Prom.", "value": f"{rend_prom:.1f} t/ha", "icon": "\\U0001F4C8"},
        {"label": "Municipios", "value": f"{n_muni}", "icon": "\\U0001F3D8\\uFE0F"},
        {"label": "% del Total Dptal.", "value": f"{share:.1f}%", "icon": "\\U0001F3AF"},
    ], cols=5)

    st.markdown("---")

    # ── Graficos departamentales ─────────────────────────────
    serie_ano = df_c.groupby("ano").agg(
        produccion=("produccion_t", "sum"),
        area=("area_sembrada_ha", "sum"),
        cosechada=("area_cosechada_ha", "sum"),
    ).reset_index()
    serie_ano["rendimiento"] = serie_ano["produccion"] / serie_ano["cosechada"].replace(0, 1)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("\\U0001F4C8 Produccion por Ano (Departamento)")
        fig_prod = go.Figure(go.Bar(
            x=serie_ano["ano"], y=serie_ano["produccion"],
            marker_color=PALETTE[0],
            text=[f"{v:,.0f}" for v in serie_ano["produccion"]],
            textposition="outside"))
        fig_prod.update_layout(template="plotly_dark", yaxis_title="Toneladas")
        st.plotly_chart(fig_prod, use_container_width=True)
    with col2:
        st.subheader("\\U0001F4CA Rendimiento por Ano (t/ha)")
        fig_rend = go.Figure(go.Scatter(
            x=serie_ano["ano"], y=serie_ano["rendimiento"],
            mode="lines+markers", line=dict(color=PALETTE[1], width=3),
            marker=dict(size=9)))
        fig_rend.update_layout(template="plotly_dark", yaxis_title="t/ha")
        st.plotly_chart(fig_rend, use_container_width=True)

    # ── Top municipios ───────────────────────────────────────
    muni_prod = (df_c.groupby("municipio")
        .agg(produccion=("produccion_t", "sum"))
        .sort_values("produccion", ascending=False).reset_index())
    top10 = muni_prod.head(10)

    st.subheader("\\U0001F3C6 Top 10 Municipios Productores")
    fig_muni = go.Figure(go.Bar(
        x=top10["produccion"], y=top10["municipio"], orientation="h",
        marker_color=PALETTE[2],
        text=[f"{v:,.0f} t" for v in top10["produccion"]],
        textposition="outside"))
    fig_muni.update_layout(template="plotly_dark", height=420,
        xaxis_title="Produccion (t)", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_muni, use_container_width=True)

    # ═══════════════════════════════════════════════════════
    # SECCION NUEVA: HISTORICO POR MUNICIPIO
    # ═══════════════════════════════════════════════════════
    st.markdown("---")
    st.header("\\U0001F4CD Historico por Municipio")
    st.caption("Selecciona un municipio para ver el historico completo "
               "(produccion, rendimiento, area) de este cultivo en ese municipio.")

    municipios = sorted(df_c["municipio"].dropna().unique().tolist())
    opcion_muni = ["Todo el departamento"] + municipios
    muni_sel = st.selectbox("Municipio", opcion_muni, index=0)

    if muni_sel == "Todo el departamento":
        st.info("Selecciona un municipio especifico para ver su historico detallado.")
    else:
        df_cm = df_c[df_c["municipio"] == muni_sel].copy()

        if df_cm.empty:
            st.warning(f"No hay registros de {cultivo_sel} en {muni_sel}.")
        else:
            # Ordenar cronologicamente por periodo
            df_cm["_orden"] = df_cm["periodo"].apply(orden_periodo)
            df_cm = df_cm.sort_values("_orden")

            # KPIs de la combinacion cultivo x municipio
            p_tot = df_cm["produccion_t"].sum()
            a_tot = df_cm["area_sembrada_ha"].sum()
            r_prom = df_cm["produccion_t"].sum() / max(df_cm["area_cosechada_ha"].sum(), 1)
            n_per = df_cm["periodo"].nunique()

            st.markdown(f"#### {cultivo_sel} en {muni_sel}")
            render_kpi_row([
                {"label": "Produccion", "value": f"{p_tot:,.0f} t", "icon": "\\U0001F33E"},
                {"label": "Area Sembrada", "value": f"{a_tot:,.0f} ha", "icon": "\\U0001F4D0"},
                {"label": "Rendimiento", "value": f"{r_prom:.1f} t/ha", "icon": "\\U0001F4C8"},
                {"label": "Periodos", "value": f"{n_per}", "icon": "\\U0001F4C5"},
            ], cols=4)

            # Graficos por periodo
            gc1, gc2 = st.columns(2)
            with gc1:
                st.subheader("\\U0001F4C8 Produccion por Periodo")
                fig_p = go.Figure(go.Bar(
                    x=df_cm["periodo"], y=df_cm["produccion_t"],
                    marker_color=PALETTE[0],
                    text=[f"{v:,.0f}" for v in df_cm["produccion_t"]],
                    textposition="outside"))
                fig_p.update_layout(template="plotly_dark", yaxis_title="Toneladas")
                st.plotly_chart(fig_p, use_container_width=True)
            with gc2:
                st.subheader("\\U0001F4C9 Rendimiento por Periodo (t/ha)")
                fig_r = go.Figure(go.Scatter(
                    x=df_cm["periodo"], y=df_cm["rendimiento_t_ha"],
                    mode="lines+markers", line=dict(color=PALETTE[1], width=3),
                    marker=dict(size=8)))
                fig_r.update_layout(template="plotly_dark", yaxis_title="t/ha")
                st.plotly_chart(fig_r, use_container_width=True)

            # Tabla detallada por periodo
            st.subheader("\\U0001F4CB Historico Detallado por Periodo")
            tabla = df_cm[["periodo", "ano", "area_sembrada_ha", "area_cosechada_ha",
                           "produccion_t", "rendimiento_t_ha"]].copy()
            tabla.columns = ["Periodo", "Anio", "Area Sembrada (ha)",
                             "Area Cosechada (ha)", "Produccion (t)", "Rendimiento (t/ha)"]
            st.dataframe(tabla, use_container_width=True, height=380)

            render_download_button(
                df_cm,
                f"{cultivo_sel}_{muni_sel}_historico.csv".lower().replace(" ", "_"),
                label="\\U0001F4E5 Descargar historico del cultivo en el municipio",
            )

    st.markdown("---")
    st.subheader("\\U0001F4CB Datos departamentales del cultivo")
    st.dataframe(df_c, use_container_width=True, height=300)
    render_download_button(df_c, f"{cultivo_sel}_departamento.csv".lower().replace(" ", "_"))

main()
'''

if __name__ == "__main__":
    path = Path("ui/pages/7_Cultivos.py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PAGE_CULTIVOS, encoding="utf-8")
    print(f"[OK] {path} actualizada con historico por municipio.")
    print("Ejecuta: streamlit run app.py")