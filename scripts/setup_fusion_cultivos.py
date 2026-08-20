"""Fusiona 7_Cultivos + 20_Ficha en una sola pagina con 3 tabs profesionales."""
from pathlib import Path

NEW_PAGE = '''"""Pagina 7: Cultivos (fusion panoramica + analisis profundo + exportacion)."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ui.services.error_handler import run_safe

from config.settings import settings
from ui.components.metrics_cards import render_kpi_row
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.theme import PALETTE
from ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes
from ui.charts.growth import plot_cagr_divergente
from ui.charts.crop_card import (diagnostic_subset, plot_crop_motor,
                                 plot_crop_serie, plot_top_municipios)
from core.reports.ficha_pdf import build_ficha_pdf

st.set_page_config(page_title="Cultivos | EVA Valle", page_icon="🌱", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def orden_periodo(p) -> float:
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
    st.title("🌱 Analisis de Cultivos")
    st.caption("Panoramica departamental + ficha tecnica por cultivo y municipio + exportacion")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    # Filtro de anos compartido entre todos los tabs
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    anos_sel = st.sidebar.multiselect("Anos", anos, default=anos)
    df_f = df[df["ano"].isin(anos_sel)] if anos_sel else df

    tab1, tab2, tab3 = st.tabs([
        "📊 Panoramica Departamental",
        "🔬 Analisis Profundo (cultivo x municipio)",
        "⬇️ Exportar",
    ])

    # ================================================================
    # TAB 1: PANORAMICA DEPARTAMENTAL
    # ================================================================
    with tab1:
        st.subheader("Vista global de todos los cultivos")

        # KPIs departamentales
        render_kpi_row([
            {"label": "Cultivos", "value": f"{df_f['cultivo'].nunique()}", "icon": "🌾"},
            {"label": "Produccion total", "value": f"{df_f['produccion_t'].sum():,.0f} t", "icon": "📦"},
            {"label": "Area sembrada", "value": f"{df_f['area_sembrada_ha'].sum():,.0f} ha", "icon": "📐"},
            {"label": "Municipios", "value": f"{df_f['municipio'].nunique()}", "icon": "🏘️"},
            {"label": "Registros", "value": f"{len(df_f):,}", "icon": "📋"},
        ], cols=5)

        # Ranking Top 20 cultivos
        st.markdown("#### 🏆 Top 20 cultivos por produccion")
        top20 = (df_f.groupby("cultivo")["produccion_t"].sum()
                 .sort_values(ascending=False).head(20).reset_index())
        total_prod = df_f["produccion_t"].sum()
        top20["share_pct"] = (top20["produccion_t"] / total_prod * 100).round(2)
        top20["acumulado_pct"] = top20["share_pct"].cumsum().round(2)
        fig_rank = go.Figure(go.Bar(
            x=top20["cultivo"], y=top20["produccion_t"] / 1000,
            marker_color=PALETTE[0],
            text=top20["share_pct"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside"))
        fig_rank.update_layout(template="plotly_white",
                               title="Produccion Top 20 (miles de t)",
                               yaxis_title="Miles de t", height=420,
                               xaxis_tickangle=-45)
        st.plotly_chart(fig_rank, use_container_width=True)
        st.dataframe(top20.rename(columns={"cultivo": "Cultivo",
                                           "produccion_t": "Produccion (t)",
                                           "share_pct": "% del Dpto.",
                                           "acumulado_pct": "% Acumulado"}),
                     use_container_width=True, hide_index=True)

        # CAGR divergente
        st.markdown("#### 📈 Crecimiento 2019-2025 (CAGR por cultivo)")
        st.caption("Verde = expansion, rojo = colapso. Filtro: cultivos con volumen real.")
        st.plotly_chart(plot_cagr_divergente(df_f, min_prod=1000),
                        use_container_width=True)

        # Cuadrantes area vs rendimiento
        st.markdown("#### 🎯 Motor del crecimiento (area vs rendimiento)")
        df_dec = descomponer_crecimiento(df_f)
        st.plotly_chart(plot_cuadrantes(df_dec), use_container_width=True)
        st.caption("Tamano de burbuja = volumen total. Arriba-derecha = virtuoso; "
                   "abajo-izquierda = colapso.")

    # ================================================================
    # TAB 2: ANALISIS PROFUNDO (cultivo x municipio)
    # ================================================================
    with tab2:
        st.subheader("Ficha tecnica: selecciona cultivo y municipio")

        # Selectores
        c1, c2 = st.columns(2)
        with c1:
            cultivos = (df_f.groupby("cultivo")["produccion_t"].sum()
                        .sort_values(ascending=False).index.tolist())
            cultivo_sel = st.selectbox("Cultivo", cultivos, key="ficha_cultivo")
        with c2:
            muns = ["Todo el departamento"] + sorted(df_f["municipio"].unique().tolist())
            muni_sel = st.selectbox("Municipio", muns, key="ficha_muni")

        df_c = df_f[df_f["cultivo"] == cultivo_sel].copy()

        # KPIs departamentales del cultivo
        render_kpi_row([
            {"label": f"Produccion {cultivo_sel}",
             "value": f"{df_c['produccion_t'].sum():,.0f} t", "icon": "🌾"},
            {"label": "Area Sembrada",
             "value": f"{df_c['area_sembrada_ha'].sum():,.0f} ha", "icon": "📐"},
            {"label": "Rendimiento",
             "value": f"{df_c['produccion_t'].sum()/max(df_c['area_cosechada_ha'].sum(),1):.1f} t/ha",
             "icon": "📈"},
            {"label": "Municipios", "value": f"{df_c['municipio'].nunique()}", "icon": "🏘️"},
            {"label": "% del Dpto.",
             "value": f"{df_c['produccion_t'].sum()/df_f['produccion_t'].sum()*100:.1f}%",
             "icon": "🎯"},
        ], cols=5)

        st.markdown("---")

        # ========= FICHA TECNICA (CAGR + motor + elasticidad) =========
        st.markdown("#### 📊 Diagnostico causal del cultivo")
        total_ref = (df_f["produccion_t"].sum() if muni_sel == "Todo el departamento"
                     else df_c["produccion_t"].sum())
        sub_ficha = df_c if muni_sel == "Todo el departamento" else df_c[df_c["municipio"] == muni_sel]
        diag = diagnostic_subset(sub_ficha, total_ref)

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("Prod. acumulada", f"{diag['prod_total']:,.0f} t")
        k2.metric("CAGR produccion", f"{diag['cagr_prod']:+.1f}%")
        k3.metric("CAGR area", f"{diag['cagr_area']:+.1f}%")
        k4.metric("CAGR rendimiento", f"{diag['cagr_rend']:+.1f}%")
        k5.metric("Elasticidad",
                  f"{diag['elasticidad']:.2f}" if diag["elasticidad"] is not None else "n/d")
        k6.metric("Motor", diag["tipo"])

        st.info(f"**{cultivo_sel} — {muni_sel}:** {diag['narrativa']}")

        cA, cB = st.columns([3, 2])
        with cA:
            st.plotly_chart(
                plot_crop_serie(diag, f"Serie historica: {cultivo_sel} ({muni_sel})"),
                use_container_width=True)
        with cB:
            st.plotly_chart(plot_crop_motor(diag), use_container_width=True)

        if muni_sel == "Todo el departamento":
            st.plotly_chart(plot_top_municipios(df_c, cultivo_sel),
                            use_container_width=True)

        st.markdown("---")

        # ========= HISTORICO POR MUNICIPIO (Tablas A/B/C originales) =========
        if muni_sel == "Todo el departamento":
            st.info("👇 Selecciona un **municipio especifico** en el selector superior "
                    "para ver las 3 tablas detalladas (historico, comparativa, ranking).")
        else:
            df_cm = df_c[df_c["municipio"] == muni_sel].copy()
            if df_cm.empty:
                st.warning(f"No hay registros de {cultivo_sel} en {muni_sel}.")
            else:
                df_cm["_orden"] = df_cm["periodo"].apply(orden_periodo)
                df_cm = df_cm.sort_values("_orden")

                st.markdown(f"#### {cultivo_sel} en {muni_sel}")
                render_kpi_row([
                    {"label": "Produccion",
                     "value": f"{df_cm['produccion_t'].sum():,.0f} t", "icon": "🌾"},
                    {"label": "Area",
                     "value": f"{df_cm['area_sembrada_ha'].sum():,.0f} ha", "icon": "📐"},
                    {"label": "Rendimiento",
                     "value": f"{df_cm['produccion_t'].sum()/max(df_cm['area_cosechada_ha'].sum(),1):.1f} t/ha",
                     "icon": "📈"},
                    {"label": "Periodos", "value": f"{df_cm['periodo'].nunique()}", "icon": "📅"},
                ], cols=4)

                gc1, gc2 = st.columns(2)
                with gc1:
                    fig_p = go.Figure(go.Bar(x=df_cm["periodo"], y=df_cm["produccion_t"],
                        marker_color=PALETTE[0]))
                    fig_p.update_layout(template="plotly_white",
                                        title="Produccion por Periodo", yaxis_title="t")
                    st.plotly_chart(fig_p, use_container_width=True)
                with gc2:
                    fig_r = go.Figure(go.Scatter(x=df_cm["periodo"], y=df_cm["rendimiento_t_ha"],
                        mode="lines+markers", line=dict(color=PALETTE[1], width=3)))
                    fig_r.update_layout(template="plotly_white",
                                        title="Rendimiento por Periodo", yaxis_title="t/ha")
                    st.plotly_chart(fig_r, use_container_width=True)

                # TABLA A
                st.subheader("📋 Tabla A - Historico del Municipio por Periodo")
                tabla_a = df_cm[["periodo","ano","area_sembrada_ha","area_cosechada_ha",
                                 "produccion_t","rendimiento_t_ha"]].copy()
                tabla_a.columns = ["Periodo","Anio","Area Sembrada (ha)","Area Cosechada (ha)",
                                   "Produccion (t)","Rendimiento (t/ha)"]
                st.dataframe(tabla_a, use_container_width=True, height=320)
                st.download_button(
                    "⬇️ Historico (CSV)",
                    data=df_cm.to_csv(index=False).encode("utf-8"),
                    file_name=f"{cultivo_sel}_{muni_sel}_historico.csv".lower().replace(" ","_"),
                    mime="text/csv")

                # TABLA B
                st.subheader("🆚 Tabla B - Comparativa vs Departamento (por ano)")
                muni_ano = df_cm.groupby("ano").agg(
                    prod_muni=("produccion_t","sum"),
                    cosech_muni=("area_cosechada_ha","sum")).reset_index()
                dpto_ano = df_c.groupby("ano").agg(
                    prod_dpto=("produccion_t","sum"),
                    cosech_dpto=("area_cosechada_ha","sum")).reset_index()
                comp = muni_ano.merge(dpto_ano, on="ano")
                comp["rend_muni"] = comp["prod_muni"]/comp["cosech_muni"].replace(0,1)
                comp["rend_dpto"] = comp["prod_dpto"]/comp["cosech_dpto"].replace(0,1)
                comp["participacion_pct"] = comp["prod_muni"]/comp["prod_dpto"].replace(0,1)*100
                comp["dif_rend"] = comp["rend_muni"]-comp["rend_dpto"]
                tabla_b = comp[["ano","prod_muni","prod_dpto","participacion_pct",
                                "rend_muni","rend_dpto","dif_rend"]].copy()
                tabla_b.columns = ["Anio","Prod Municipio (t)","Prod Departamento (t)",
                                   "% Participacion","Rend Municipio (t/ha)",
                                   "Rend Departamento (t/ha)","Dif Rendimiento"]
                st.dataframe(tabla_b, use_container_width=True, height=300)
                st.download_button(
                    "⬇️ Comparativa (CSV)",
                    data=tabla_b.to_csv(index=False).encode("utf-8"),
                    file_name=f"{cultivo_sel}_{muni_sel}_comparativa.csv".lower().replace(" ","_"),
                    mime="text/csv")

        # TABLA C - Ranking (siempre visible)
        st.subheader("🏆 Tabla C - Ranking de Municipios (todo el departamento)")
        st.caption(f"Posicion de cada municipio en la produccion de {cultivo_sel}.")
        ranking = (df_c.groupby("municipio")
            .agg(produccion=("produccion_t","sum"), area=("area_sembrada_ha","sum"),
                 rendimiento=("rendimiento_t_ha","median"))
            .sort_values("produccion", ascending=False).reset_index())
        ranking["posicion"] = range(1, len(ranking)+1)
        ranking["share_pct"] = ranking["produccion"]/ranking["produccion"].sum()*100
        if muni_sel != "Todo el departamento":
            ranking["Seleccionado"] = ["✅" if m == muni_sel else "" for m in ranking["municipio"]]
            pos = ranking[ranking["municipio"] == muni_sel]
            if not pos.empty:
                p = pos.iloc[0]
                st.info(f"**{muni_sel}** ocupa la posicion **#{int(p['posicion'])} de {len(ranking)}** "
                        f"en produccion de {cultivo_sel}, con el {p['share_pct']:.1f}% del total.")
        st.dataframe(ranking, use_container_width=True, height=400)
        st.download_button(
            "⬇️ Ranking (CSV)",
            data=ranking.to_csv(index=False).encode("utf-8"),
            file_name=f"{cultivo_sel}_ranking_municipios.csv".lower().replace(" ","_"),
            mime="text/csv")

    # ================================================================
    # TAB 3: EXPORTAR
    # ================================================================
    with tab3:
        st.subheader("Centro de descargas")
        st.caption("Exporta los analisis del cultivo seleccionado en el Tab 2.")

        # PDF de ficha tecnica
        st.markdown("#### 📄 Ficha tecnica en PDF")
        ambito_pdf = muni_sel if muni_sel != "Todo el departamento" else "Todo el Valle"
        sub_pdf = df_c if muni_sel == "Todo el departamento" else df_c[df_c["municipio"] == muni_sel]
        if not sub_pdf.empty and diag["prod_total"] > 0:
            pdf = build_ficha_pdf(cultivo_sel, ambito_pdf, diag["agg"], diag)
            nombre_pdf = "".join(ch for ch in f"ficha_{cultivo_sel}_{ambito_pdf}"
                                 if ch.isalnum() or ch in "_-") + ".pdf"
            st.download_button("⬇️ Descargar ficha en PDF (con graficos)",
                               data=pdf, file_name=nombre_pdf, mime="application/pdf")
        else:
            st.warning("Selecciona un cultivo valido en el Tab 2 para generar el PDF.")

        st.markdown("---")

        # CSV completo del cultivo
        st.markdown("#### 📊 Dataset completo del cultivo")
        if not df_c.empty:
            st.download_button(
                "⬇️ Todos los registros del cultivo (CSV)",
                data=df_c.to_csv(index=False).encode("utf-8"),
                file_name=f"{cultivo_sel}_completo.csv".lower().replace(" ","_"),
                mime="text/csv")
            st.dataframe(df_c.head(20), use_container_width=True, hide_index=True)
            st.caption(f"Total: {len(df_c)} registros de {cultivo_sel} en los anos seleccionados.")

        st.markdown("---")
        st.caption("Fuente: UPRA - EVA 2019-2025.")


run_safe(main)
'''

Path("ui/pages/7_Cultivos.py").write_text(NEW_PAGE, encoding="utf-8")
print("[OK] 7_Cultivos.py reescrito con 3 tabs (panoramica + profundo + exportar)")

# --- Eliminar la entrada duplicada de Ficha Cultivo en app.py ---
app = Path("app.py")
c = app.read_text(encoding="utf-8")
if "20_Ficha.py" in c:
    lineas = c.splitlines(keepends=True)
    lineas = [l for l in lineas if "20_Ficha.py" not in l]
    app.write_text("".join(lineas), encoding="utf-8")
    print("[OK] Entrada de 20_Ficha.py eliminada del menu (fusionada en Cultivos)")
else:
    print("[INFO] 20_Ficha.py ya no estaba en el menu")

# --- Eliminar el archivo duplicado (opcional, mantener por si acaso) ---
ficha_vieja = Path("ui/pages/20_Ficha.py")
if ficha_vieja.exists():
    ficha_vieja.unlink()
    print("[OK] ui/pages/20_Ficha.py eliminado (contenido fusionado en 7_Cultivos)")

print("\nReinicia Streamlit y explora la nueva pagina 🌱 Cultivos con sus 3 tabs")