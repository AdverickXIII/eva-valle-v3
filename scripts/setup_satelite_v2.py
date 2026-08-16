"""Reescribe la pagina de Validacion Satelital con mejoras visuales (v2)."""
from pathlib import Path

PAGE = '''"""Pagina 18: Validacion Satelital v2 (hero + dona + heatmap + imagen + metodologia)."""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Validacion Satelital | EVA Valle", page_icon="🛰️", layout="wide")

st.title("🛰️ Validacion Satelital: Sentinel-2 + Sentinel-1 vs UPRA")
st.caption("Cruce de datos oficiales (EVA 2019-2025) con imagenes opticas y radar de la Agencia Espacial Europea.")

csv_path = Path("outputs/validacion_optica_radar.csv")
if not csv_path.exists():
    st.error("No se encontro validacion_optica_radar.csv. Ejecuta primero el script de Earth Engine.")
    st.stop()

df = pd.read_csv(csv_path)

# ---------- 1. BANNER HEROE ----------
total = len(df)
coherentes = int(df["coherencia_final"].str.contains("Coherente", na=False).sum())
anomalias = int(df["coherencia_final"].str.contains("Anomal", na=False).sum())
cobertura = (df["fuente"] != "Ninguna").mean() * 100

c1, c2, c3 = st.columns(3)
c1.metric("Cobertura satelital", f"{cobertura:.0f}%")
c2.metric("Coherencia con UPRA", f"{coherentes/total*100:.1f}%")
c3.metric("Anomalias detectadas", str(anomalias))

if anomalias == 0:
    st.success("El satelite confirma la autodeclaracion municipal: **cero anomalias** "
               f"en {total} registros municipio-ano. La base EVA del Valle es confiable.")
st.markdown("---")

# ---------- 2. DONA + BARRA DE FUENTES ----------
def cat(x):
    x = str(x)
    if "Coherente" in x: return "Coherente"
    if "Anomal" in x: return "Anomalia"
    if "Indeterminado" in x: return "Indeterminado"
    return "Sin datos"

df["cat"] = df["coherencia_final"].map(cat)
vc = df["cat"].value_counts()
vf = df["fuente"].value_counts()

colA, colB = st.columns(2)
with colA:
    fig_donut = px.pie(names=vc.index, values=vc.values, hole=0.55,
                       color=vc.index,
                       color_discrete_map={"Coherente": "#2E8B57",
                                           "Indeterminado": "#FFA500",
                                           "Anomalia": "#DC143C",
                                           "Sin datos": "#999999"})
    fig_donut.update_layout(title="Estado de validacion", height=320,
                            showlegend=False,
                            margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig_donut, use_container_width=True)
with colB:
    fig_bar = px.bar(x=vf.index, y=vf.values, color=vf.index,
                     color_discrete_map={"Optico": "#2E8B57",
                                         "Radar": "#4682B4",
                                         "Ninguna": "#999999"})
    fig_bar.update_layout(title="Fuente de datos por registro", height=320,
                          showlegend=False,
                          margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig_bar, use_container_width=True)

# ---------- 3. HEATMAP NDVI (top 15 municipios) ----------
st.subheader("Estabilidad de la vegetacion: NDVI por municipio y ano (optico)")
df_opt = df.dropna(subset=["ndvi_mean"])
top_mun = (df_opt.groupby("municipio")["ndvi_mean"].mean()
           .sort_values(ascending=False).head(15).index)
piv = (df_opt[df_opt["municipio"].isin(top_mun)]
       .pivot_table(index="municipio", columns="ano", values="ndvi_mean"))
fig_heat = px.imshow(piv, color_continuous_scale="Greens", aspect="auto",
                     labels=dict(x="Ano", y="Municipio", color="NDVI"))
fig_heat.update_layout(height=520, margin=dict(t=20, b=10, l=10, r=10))
st.plotly_chart(fig_heat, use_container_width=True)
st.caption("Verde intenso = vegetacion densa y estable (tipico de cana y cafe). "
           "Los espacios vacios fueron cubiertos por radar (Sentinel-1).")

# ---------- 4. IMAGEN DE EXHIBICION ----------
img_path = Path("outputs/palmira_canaverales_sentinel2.png")
if img_path.exists():
    st.subheader("Asi ve el satelite al lider de la produccion")
    st.image(img_path, caption="Canaverales de Palmira - Sentinel-2 (10 m), ESA / Copernicus")

# ---------- 5. DETALLE TECNICO (expander) ----------
with st.expander("🔬 Detalle tecnico: dispersiones optico y radar"):
    df_o = df[df["fuente"] == "Optico"].dropna(subset=["ndvi_mean", "area_cosechada_eva"])
    if not df_o.empty:
        fig_o = px.scatter(df_o, x="area_cosechada_eva", y="ndvi_mean",
                           color="cat", hover_name="municipio", hover_data=["ano"],
                           title="Optico: NDVI vs area reportada",
                           color_discrete_map={"Coherente": "#2E8B57",
                                               "Indeterminado": "#FFA500",
                                               "Anomalia": "#DC143C"})
        fig_o.add_hline(y=0.4, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_o, use_container_width=True)
    df_r = df[df["fuente"] == "Radar"].dropna(subset=["vh_db", "area_cosechada_eva"])
    if not df_r.empty:
        fig_r = px.scatter(df_r, x="area_cosechada_eva", y="vh_db",
                           color="cat", hover_name="municipio", hover_data=["ano"],
                           title="Radar: VH (dB) vs area reportada",
                           color_discrete_map={"Coherente": "#4682B4",
                                               "Indeterminado": "#FFA500",
                                               "Anomalia": "#DC143C"})
        fig_r.add_hline(y=-18, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_r, use_container_width=True)

# ---------- 6. METODOLOGIA (expander) ----------
with st.expander("📚 Metodologia"):
    st.markdown("""
    - **NDVI (Sentinel-2, optico):** (infrarrojo - rojo) / (infrarrojo + rojo).
      Valores > 0.4 indican vegetacion activa; > 0.6 vegetacion densa (cana, cafe).
    - **VH (Sentinel-1, radar):** retrodispersion cruzada en dB; atraviesa nubes.
      Entre -22 y -12 dB indica vegetacion; < -24 dB superficie lisa (agua/suelo).
    - **Coherencia:** se compara la vegetacion observada por el satelite contra el
      area cosechada autodeclarada en EVA. Anomalia = contradiccion fuerte entre ambos.
    - **Limitacion conocida:** la nubosidad del Pacifico bloquea el optico;
      alli se usa radar. Fuentes: ESA Copernicus via Google Earth Engine.
    """)

# ---------- 7. TABLA + DESCARGA ----------
st.subheader("Detalle por municipio y ano")
df_tab = df[["municipio", "ano", "fuente", "ndvi_mean", "vh_db",
             "area_cosechada_eva", "coherencia_final"]].sort_values(["municipio", "ano"])
df_tab["ndvi_mean"] = df_tab["ndvi_mean"].round(3)
df_tab["vh_db"] = df_tab["vh_db"].round(1)
st.dataframe(df_tab.head(100), use_container_width=True, hide_index=True)

st.download_button("⬇️ Descargar datos de validacion (CSV)",
                   data=csv_path.read_bytes(),
                   file_name="validacion_optica_radar.csv",
                   mime="text/csv")

st.markdown("---")
st.caption("Fuentes: Sentinel-2 (optico) + Sentinel-1 (radar) via Google Earth Engine. "
           "Procesado por EVA Valle v3.0.")
'''

Path("ui/pages/18_Satelite.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/18_Satelite.py (v2 con mejoras visuales)")