"""Crea la pagina de Validacion Satelital en el Dashboard de Streamlit."""
from pathlib import Path

PAGE_CODE = '''"""Pagina 18: Validacion Satelital (Sentinel-2 vs UPRA)."""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Validacion Satelital | EVA Valle", page_icon="🛰️", layout="wide")

st.title("🛰️ Validacion Satelital: Sentinel-2 vs UPRA")
st.caption("Cruce de datos oficiales (EVA 2019-2025) con imagenes satelitales de la Agencia Espacial Europea.")

# Cargar datos
csv_path = Path("outputs/sentinel_ndvi_VALLE_COMPLETO.csv")
if not csv_path.exists():
    st.error("No se encontro el archivo de resultados. Ejecuta primero el script de Earth Engine.")
    st.stop()

df = pd.read_csv(csv_path)

# Filtros en barra lateral
st.sidebar.header("Filtros")
municipios = st.sidebar.multiselect("Municipios", df['municipio'].unique(), default=[])
anos = st.sidebar.multiselect("Anos", sorted(df['ano'].unique()), default=[])

df_f = df.copy()
if municipios:
    df_f = df_f[df_f['municipio'].isin(municipios)]
if anos:
    df_f = df_f[df_f['ano'].isin(anos)]

# Metricas principales
col1, col2, col3, col4 = st.columns(4)
total = len(df_f)
coherentes = len(df_f[df_f['coherencia'].str.contains('Coherente', na=False)])
nublados = len(df_f[df_f['coherencia'] == 'Sin datos satelitales'])
anomalias = len(df_f[df_f['coherencia'].str.contains('Anomalia', na=False)])

col1.metric("Registros Analizados", total)
col2.metric("✅ Coherentes", coherentes, f"{coherentes/total*100:.1f}%" if total>0 else "0%")
col3.metric("☁️ Sin datos (Nubes)", nublados, f"{nublados/total*100:.1f}%" if total>0 else "0%")
col4.metric("⚠️ Anomalias", anomalias)

st.markdown("---")

# Grafico de dispersion (Scatter Plot)
st.subheader("Area Cosechada Reportada (EVA) vs Vegetacion Observada (Satelite)")
st.info("Cada punto es un municipio en un ano especifico. El eje X es lo que dice el municipio (UPRA), el eje Y es lo que ve el satelite (NDVI).")

df_plot = df_f.dropna(subset=['ndvi_mean', 'area_cosechada_eva'])
if not df_plot.empty:
    fig = px.scatter(
        df_plot, 
        x="area_cosechada_eva", 
        y="ndvi_mean", 
        color="coherencia",
        hover_name="municipio",
        hover_data=["ano", "produccion_eva"],
        labels={
            "area_cosechada_eva": "Area Cosechada Reportada (ha)",
            "ndvi_mean": "NDVI Promedio (Satelite)",
            "coherencia": "Estado de Validacion",
            "ano": "Ano",
            "produccion_eva": "Produccion (t)"
        },
        color_discrete_map={
            "✅ Coherente (Alto NDVI / Alta Area)": "#2E8B57",
            "✅ Coherente": "#3CB371",
            "➖ Indeterminado": "#FFA500",
            "⚠️ Anomalía: NDVI bajo vs Area alta": "#DC143C",
            "⚠️ Anomalía: NDVI alto vs Area baja": "#DC143C"
        }
    )
    fig.update_layout(template="plotly_white", height=600)
    # Lineas de umbral
    fig.add_hline(y=0.4, line_dash="dash", line_color="gray", annotation_text="Umbral Vegetacion")
    fig.add_vline(x=1000, line_dash="dash", line_color="gray", annotation_text="Umbral Area")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay datos suficientes para graficar con los filtros seleccionados.")

# Tabla de detalles
st.subheader("Detalle por Municipio y Ano")
st.dataframe(
    df_f[['municipio', 'ano', 'ndvi_mean', 'area_cosechada_eva', 'produccion_eva', 'coherencia']]
    .sort_values(['municipio', 'ano']), 
    use_container_width=True
)

st.markdown("---")
st.caption("Fuente de datos satelitales: COPERNICUS/S2_SR_HARMONIZED (Sentinel-2) via Google Earth Engine. Procesado por EVA Valle v3.0.")
'''

out_path = Path("ui/pages/18_Satelite.py")
out_path.write_text(PAGE_CODE, encoding="utf-8")
print(f"[OK] Pagina creada: {out_path}")
print("Recarga el dashboard (Ctrl+R) y busca 'Validacion Satelital' en el menu lateral.")