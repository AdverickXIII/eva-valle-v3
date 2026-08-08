"""Reemplaza 7_Cultivos.py con las 3 tablas: municipio, comparativa, ranking."""
from pathlib import Path

PAGE = '''"""Pagina 7: Cultivos - Analisis por producto y municipio (3 tablas)."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from ui.components.metrics_cards import render_kpi_row
from ui.components.loading_states import render_empty_state
from ui.components.download_section import render_download_button
from ui.charts.theme import PALETTE

st.set_page_config(page_title="Cultivos | EVA Valle", page_icon="\\U0001F331", layout="wide")

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
    st.title("\\U0001F331 Analisis por Cultivo")
    st.caption("Estadisticas por producto a nivel departamental y municipal")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    prod_cultivo = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    cultivo_sel = st.selectbox("Selecciona un cultivo", prod_cultivo.index.tolist(), index=0)
    df_c = df[df["cultivo"] == cultivo_sel].copy()

    st.markdown("---")

    # ── KPIs departamentales ─────────────────────────────────
    render_kpi_row([
        {"label": f"Produccion {cultivo_sel}", "value": f"{df_c['produccion_t'].sum():,.0f} t", "icon": "\\U0001F33E"},
        {"label": "Area Sembrada", "value": f"{df_c['area_sembrada_ha'].sum():,.0f} ha", "icon": "\\U0001F4D0"},
        {"label": "Rendimiento", "value": f"{df_c['produccion_t'].sum()/max(df_c['area_cosechada_ha'].sum(),1):.1f} t/ha", "icon": "\\U0001F4C8"},
        {"label": "Municipios", "value": f"{df_c['municipio'].nunique()}", "icon": "\\U0001F3D8\\uFE0F"},
        {"label": "% del Dpto.", "value": f"{df_c['produccion_t'].sum()/df['produccion_t'].sum()*100:.1f}%", "icon": "\\U0001F3AF"},
    ], cols=5)

    st.markdown("---")

    # ═══════════ HISTORICO POR MUNICIPIO ═══════════
    st.header("\\U0001F4CD Historico por Municipio")
    municipios = sorted(df_c["municipio"].dropna().unique().tolist())
    muni_sel = st.selectbox("Municipio", ["Todo el departamento"] + municipios, index=0)

    if muni_sel == "Todo el departamento":
        st.info("Selecciona un municipio especifico para ver sus 3 tablas.")
    else:
        df_cm = df_c[df_c["municipio"] == muni_sel].copy()
        if df_cm.empty:
            st.warning(f"No hay registros de {cultivo_sel} en {muni_sel}.")
        else:
            df_cm["_orden"] = df_cm["periodo"].apply(orden_periodo)
            df_cm = df_cm.sort_values("_orden")

            st.markdown(f"#### {cultivo_sel} en {muni_sel}")
            render_kpi_row([
                {"label": "Produccion", "value": f"{df_cm['produccion_t'].sum():,.0f} t", "icon": "\\U0001F33E"},
                {"label": "Area", "value": f"{df_cm['area_sembrada_ha'].sum():,.0f} ha", "icon": "\\U0001F4D0"},
                {"label": "Rendimiento", "value": f"{df_cm['produccion_t'].sum()/max(df_cm['area_cosechada_ha'].sum(),1):.1f} t/ha", "icon": "\\U0001F4C8"},
                {"label": "Periodos", "value": f"{df_cm['periodo'].nunique()}", "icon": "\\U0001F4C5"},
            ], cols=4)

            gc1, gc2 = st.columns(2)
            with gc1:
                fig_p = go.Figure(go.Bar(x=df_cm["periodo"], y=df_cm["produccion_t"],
                    marker_color=PALETTE[0]))
                fig_p.update_layout(template="plotly_dark", title="Produccion por Periodo", yaxis_title="t")
                st.plotly_chart(fig_p, use_container_width=True)
            with gc2:
                fig_r = go.Figure(go.Scatter(x=df_cm["periodo"], y=df_cm["rendimiento_t_ha"],
                    mode="lines+markers", line=dict(color=PALETTE[1], width=3)))
                fig_r.update_layout(template="plotly_dark", title="Rendimiento por Periodo", yaxis_title="t/ha")
                st.plotly_chart(fig_r, use_container_width=True)

            # ── TABLA A: Historico del municipio ─────────────
            st.subheader("\\U0001F4CB Tabla A - Historico del Municipio por Periodo")
            tabla_a = df_cm[["periodo","ano","area_sembrada_ha","area_cosechada_ha","produccion_t","rendimiento_t_ha"]].copy()
            tabla_a.columns = ["Periodo","Anio","Area Sembrada (ha)","Area Cosechada (ha)","Produccion (t)","Rendimiento (t/ha)"]
            st.dataframe(tabla_a, use_container_width=True, height=320)
            render_download_button(df_cm, f"{cultivo_sel}_{muni_sel}_historico.csv".lower().replace(" ","_"))

            # ── TABLA B: Comparativa municipio vs departamento ──
            st.subheader("\\U0001F19A Tabla B - Comparativa vs Departamento (por ano)")
            muni_ano = df_cm.groupby("ano").agg(
                prod_muni=("produccion_t","sum"), cosech_muni=("area_cosechada_ha","sum")).reset_index()
            dpto_ano = df_c.groupby("ano").agg(
                prod_dpto=("produccion_t","sum"), cosech_dpto=("area_cosechada_ha","sum")).reset_index()
            comp = muni_ano.merge(dpto_ano, on="ano")
            comp["rend_muni"] = comp["prod_muni"]/comp["cosech_muni"].replace(0,1)
            comp["rend_dpto"] = comp["prod_dpto"]/comp["cosech_dpto"].replace(0,1)
            comp["participacion_pct"] = comp["prod_muni"]/comp["prod_dpto"].replace(0,1)*100
            comp["dif_rend"] = comp["rend_muni"]-comp["rend_dpto"]
            tabla_b = comp[["ano","prod_muni","prod_dpto","participacion_pct","rend_muni","rend_dpto","dif_rend"]].copy()
            tabla_b.columns = ["Anio","Prod Municipio (t)","Prod Departamento (t)","% Participacion","Rend Municipio (t/ha)","Rend Departamento (t/ha)","Dif Rendimiento"]
            st.dataframe(tabla_b, use_container_width=True, height=300)
            render_download_button(tabla_b, f"{cultivo_sel}_{muni_sel}_comparativa.csv".lower().replace(" ","_"))

    st.markdown("---")

    # ── TABLA C: Ranking de municipios del cultivo ───────────
    st.subheader("\\U0001F3C6 Tabla C - Ranking de Municipios (todo el departamento)")
    st.caption(f"Posicion de cada municipio en la produccion de {cultivo_sel}.")
    ranking = (df_c.groupby("municipio")
        .agg(produccion=("produccion_t","sum"), area=("area_sembrada_ha","sum"),
             rendimiento=("rendimiento_t_ha","median"))
        .sort_values("produccion", ascending=False).reset_index())
    ranking["posicion"] = range(1, len(ranking)+1)
    ranking["share_pct"] = ranking["produccion"]/ranking["produccion"].sum()*100
    if muni_sel != "Todo el departamento":
        ranking["Seleccionado"] = ["\\u2705" if m == muni_sel else "" for m in ranking["municipio"]]
        pos = ranking[ranking["municipio"] == muni_sel]
        if not pos.empty:
            p = pos.iloc[0]
            st.info(f"**{muni_sel}** ocupa la posicion **#{int(p['posicion'])} de {len(ranking)}** "
                    f"en produccion de {cultivo_sel}, con el {p['share_pct']:.1f}% del total.")
    tabla_c = ranking.copy()
    st.dataframe(tabla_c, use_container_width=True, height=400)
    render_download_button(ranking, f"{cultivo_sel}_ranking_municipios.csv".lower().replace(" ","_"))

main()
'''

if __name__ == "__main__":
    path = Path("ui/pages/7_Cultivos.py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PAGE, encoding="utf-8")
    print(f"[OK] {path} actualizada con Tablas A, B y C.")
    print("Ejecuta: streamlit run app.py")