"""Crea la pagina 7_Cultivos.py y la registra en la navegacion."""
from pathlib import Path

PAGE_CULTIVOS = '''"""Pagina 7: Cultivos - Analisis individual por producto."""
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

def main() -> None:
    st.title("\\U0001F331 Analisis por Cultivo")
    st.caption("Estadisticas individuales de cada producto (platano, cafe, pina, etc.)")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    # Lista de cultivos ordenada por produccion total
    prod_por_cultivo = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=False)
    cultivos = prod_por_cultivo.index.tolist()

    # Selector de cultivo
    cultivo_sel = st.selectbox(
        "Selecciona un cultivo",
        cultivos,
        index=0,
        help="Los cultivos estan ordenados por produccion total descendente.",
    )

    # Filtrar dataset por cultivo
    df_c = df[df["cultivo"] == cultivo_sel].copy()

    st.markdown("---")

    # ── KPIs del cultivo ─────────────────────────────────────
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

    # ── Serie de tiempo y rendimiento por ano ────────────────
    col1, col2 = st.columns(2)

    serie_ano = df_c.groupby("ano").agg(
        produccion=("produccion_t", "sum"),
        area=("area_sembrada_ha", "sum"),
        cosechada=("area_cosechada_ha", "sum"),
    ).reset_index()
    serie_ano["rendimiento"] = serie_ano["produccion"] / serie_ano["cosechada"].replace(0, 1)

    with col1:
        st.subheader("\\U0001F4C8 Produccion por Ano")
        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(
            x=serie_ano["ano"], y=serie_ano["produccion"],
            marker_color=PALETTE[0], name="Produccion (t)",
            text=[f"{v:,.0f}" for v in serie_ano["produccion"]],
            textposition="outside",
        ))
        fig_prod.update_layout(template="plotly_dark", yaxis_title="Toneladas")
        st.plotly_chart(fig_prod, use_container_width=True)

    with col2:
        st.subheader("\\U0001F4CA Rendimiento por Ano (t/ha)")
        fig_rend = go.Figure()
        fig_rend.add_trace(go.Scatter(
            x=serie_ano["ano"], y=serie_ano["rendimiento"],
            mode="lines+markers",
            line=dict(color=PALETTE[1], width=3),
            marker=dict(size=9),
        ))
        fig_rend.update_layout(template="plotly_dark", yaxis_title="t/ha")
        st.plotly_chart(fig_rend, use_container_width=True)

    st.markdown("---")

    # ── Top municipios ───────────────────────────────────────
    st.subheader("\\U0001F3C6 Top 10 Municipios Productores")

    muni_prod = (df_c.groupby("municipio")
        .agg(produccion=("produccion_t", "sum"),
             area=("area_sembrada_ha", "sum"),
             rendimiento=("rendimiento_t_ha", "median"))
        .sort_values("produccion", ascending=False)
        .reset_index())

    top10 = muni_prod.head(10)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig_muni = go.Figure()
        fig_muni.add_trace(go.Bar(
            x=top10["produccion"], y=top10["municipio"],
            orientation="h", marker_color=PALETTE[2],
            text=[f"{v:,.0f} t" for v in top10["produccion"]],
            textposition="outside",
        ))
        fig_muni.update_layout(template="plotly_dark", height=450,
            xaxis_title="Produccion (t)", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_muni, use_container_width=True)

    with col2:
        st.subheader("\\U0001F4CA Concentracion")
        top3_share = top10.head(3)["produccion"].sum() / max(muni_prod["produccion"].sum(), 1) * 100
        st.metric("Top 3 municipios", f"{top3_share:.1f}%",
            help="Porcentaje de la produccion del cultivo concentrada en los 3 principales municipios.")
        st.info(f"**{top10.iloc[0]['municipio']}** es el principal productor con "
                f"{top10.iloc[0]['produccion']:,.0f} t.")

    st.markdown("---")

    # ── Tabla resumen por ano ────────────────────────────────
    st.subheader("\\U0001F4CB Resumen Anual Detallado")
    st.dataframe(serie_ano, use_container_width=True)
    render_download_button(
        df_c, f"{cultivo_sel.lower().replace(' ', '_')}_detalle.csv",
        label="\\U0001F4E5 Descargar datos del cultivo",
    )

main()
'''

# ═══════════════════════════════════════════════════════════
# ACTUALIZAR app.py para registrar la nueva pagina
# ═══════════════════════════════════════════════════════════
def actualizar_navegacion() -> bool:
    app_path = Path("app.py")
    if not app_path.exists():
        print("[ERROR] app.py no encontrado.")
        return False

    content = app_path.read_text(encoding="utf-8")

    if "7_Cultivos.py" in content:
        print("[INFO] La pagina Cultivos ya esta registrada en app.py.")
        return True

    # Insertar la nueva pagina antes del cierre de st.navigation
    anchor = 'st.Page("ui/pages/6_Configuracion.py"'
    if anchor in content:
        nueva_linea = '    st.Page("ui/pages/7_Cultivos.py", title="Cultivos", icon="\\U0001F331"),\n'
        # Encontrar la linea de Configuracion y agregar despues
        idx = content.find(anchor)
        fin_linea = content.find("\n", idx)
        content = content[:fin_linea + 1] + nueva_linea + content[fin_linea + 1:]
        app_path.write_text(content, encoding="utf-8")
        print("[OK] Pagina Cultivos registrada en app.py")
        return True
    else:
        print("[WARN] No se encontro el anchor de navegacion. Registra manualmente.")
        return False


if __name__ == "__main__":
    # Crear la pagina
    path = Path("ui/pages/7_Cultivos.py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PAGE_CULTIVOS, encoding="utf-8")
    print(f"[OK] {path}")

    # Registrar en navegacion
    actualizar_navegacion()

    print("\nPagina Cultivos creada. Ejecuta: streamlit run app.py")