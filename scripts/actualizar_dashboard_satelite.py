"""Actualiza la pagina de Validacion Satelital con datos optico + radar."""
from pathlib import Path

PAGE_CODE = '''"""Pagina 18: Validacion Satelital Optico + Radar (Sentinel-2 + Sentinel-1)."""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Validacion Satelital | EVA Valle", page_icon="🛰️", layout="wide")

st.title("🛰️ Validacion Satelital: Sentinel-2 + Sentinel-1 vs UPRA")
st.caption("Cruce de datos oficiales (EVA 2019-2025) con imagenes opticas (Sentinel-2) y radar (Sentinel-1) de la Agencia Espacial Europea.")

# Cargar datos combinados
csv_path = Path("outputs/validacion_optica_radar.csv")
if not csv_path.exists():
    st.error("No se encontro validacion_optica_radar.csv. Ejecuta primero el script de Earth Engine.")
    st.stop()

df = pd.read_csv(csv_path)

# Filtros
st.sidebar.header("Filtros")
municipios = st.sidebar.multiselect("Municipios", df['municipio'].unique(), default=[])
anos = st.sidebar.multiselect("Anos", sorted(df['ano'].unique()), default=[])
fuente = st.sidebar.multiselect("Fuente", df['fuente'].unique(), default=[])

df_f = df.copy()
if municipios:
    df_f = df_f[df_f['municipio'].isin(municipios)]
if anos:
    df_f = df_f[df_f['ano'].isin(anos)]
if fuente:
    df_f = df_f[df_f['fuente'].isin(fuente)]

# Metricas
col1, col2, col3, col4 = st.columns(4)
total = len(df_f)
coherentes = len(df_f[df_f['coherencia_final'].str.contains('Coherente', na=False)])
optico = len(df_f[df_f['fuente'] == 'Optico'])
radar = len(df_f[df_f['fuente'] == 'Radar'])

col1.metric("Registros Analizados", total)
col2.metric("✅ Coherentes", coherentes, f"{coherentes/total*100:.1f}%" if total>0 else "0%")
col3.metric("🌤️ Optico (Sentinel-2)", optico, f"{optico/total*100:.1f}%" if total>0 else "0%")
col4.metric("📡 Radar (Sentinel-1)", radar, f"{radar/total*100:.1f}%" if total>0 else "0%")

st.markdown("---")

# Grafico de dispersion
st.subheader("Area Cosechada Reportada (EVA) vs Vegetacion Observada (Satelite)")

df_opt = df_f[df_f['fuente'] == 'Optico'].dropna(subset=['ndvi_mean', 'area_cosechada_eva'])
df_rad = df_f[df_f['fuente'] == 'Radar'].dropna(subset=['vh_db', 'area_cosechada_eva'])

if not df_opt.empty:
    fig_opt = px.scatter(
        df_opt,
        x="area_cosechada_eva",
        y="ndvi_mean",
        color="coherencia_final",
        hover_name="municipio",
        hover_data=["ano", "produccion_eva"],
        title="Validacion Optica (Sentinel-2 NDVI)",
        labels={
            "area_cosechada_eva": "Area Cosechada Reportada (ha)",
            "ndvi_mean": "NDVI Promedio (Optico)",
            "coherencia_final": "Estado",
        },
        color_discrete_map={
            "✅ Coherente (Alto NDVI / Alta Area)": "#2E8B57",
            "✅ Coherente": "#3CB371",
            "➖ Indeterminado": "#FFA500",
        }
    )
    fig_opt.add_hline(y=0.4, line_dash="dash", line_color="gray")
    fig_opt.add_vline(x=1000, line_dash="dash", line_color="gray")
    fig_opt.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig_opt, use_container_width=True)

if not df_rad.empty:
    fig_rad = px.scatter(
        df_rad,
        x="area_cosechada_eva",
        y="vh_db",
        color="coherencia_final",
        hover_name="municipio",
        hover_data=["ano", "produccion_eva"],
        title="Validacion Radar (Sentinel-1 VH dB)",
        labels={
            "area_cosechada_eva": "Area Cosechada Reportada (ha)",
            "vh_db": "VH Promedio (dB, Radar)",
            "coherencia_final": "Estado",
        },
        color_discrete_map={
            "✅ Coherente (radar)": "#4682B4",
            "⚠️ Anomalía radar": "#DC143C",
            "➖ Indeterminado (radar)": "#FFA500",
        }
    )
    fig_rad.add_hline(y=-18, line_dash="dash", line_color="gray", annotation_text="Umbral vegetacion (-18 dB)")
    fig_rad.add_vline(x=1000, line_dash="dash", line_color="gray")
    fig_rad.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig_rad, use_container_width=True)

# Tabla
st.subheader("Detalle por Municipio y Ano")
st.dataframe(
    df_f[['municipio', 'ano', 'fuente', 'ndvi_mean', 'vh_db', 'area_cosechada_eva', 'coherencia_final']]
    .sort_values(['municipio', 'ano']),
    use_container_width=True
)

st.markdown("---")
st.caption("Fuentes: Sentinel-2 (optico) + Sentinel-1 (radar) via Google Earth Engine. Procesado por EVA Valle v3.0.")
'''

out_path = Path("ui/pages/18_Satelite.py")
out_path.write_text(PAGE_CODE, encoding="utf-8")
print(f"[OK] Pagina actualizada: {out_path}")
print("Recarga Streamlit (Ctrl+R) para ver los 2 graficos (optico + radar).")