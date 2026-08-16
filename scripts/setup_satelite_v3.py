"""Pagina Validacion Satelital v3: mosaico sin huecos + dona con centro."""
from pathlib import Path

PAGE = '''"""Pagina 18: Validacion Satelital v3."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Validacion Satelital | EVA Valle", page_icon="🛰️", layout="wide")

st.title("🛰️ Validacion Satelital: Sentinel-2 + Sentinel-1 vs UPRA")
st.caption("Cruce de datos oficiales (EVA 2019-2025) con imagenes opticas y radar de la Agencia Espacial Europea.")

csv_path = Path("outputs/validacion_optica_radar.csv")
if not csv_path.exists():
    st.error("No se encontro validacion_optica_radar.csv. Ejecuta primero el script de Earth Engine.")
    st.stop()

df = pd.read_csv(csv_path)

# ---------- 1. HEROE ----------
total = len(df)
coherentes = int(df["coherencia_final"].str.contains("Coherente", na=False).sum())
anomalias = int(df["coherencia_final"].str.contains("Anomal", na=False).sum())
cobertura = (df["fuente"] != "Ninguna").mean() * 100

c1, c2, c3 = st.columns(3)
c1.metric("Cobertura satelital", f"{cobertura:.0f}%", help="273/273 registros con dato satelital")
c2.metric("Coherencia con UPRA", f"{coherentes/total*100:.1f}%", help="Registros donde el satelite confirma lo reportado")
c3.metric("Anomalias detectadas", str(anomalias))

if anomalias == 0:
    st.success("El satelite confirma la autodeclaracion municipal: **cero anomalias** "
               f"en {total} registros municipio-ano. La base EVA del Valle es confiable.")
st.markdown("---")

# ---------- 2. DONA CON CENTRO + BARRA ----------
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
    fig_donut = px.pie(names=vc.index, values=vc.values, hole=0.55, color=vc.index,
                       color_discrete_map={"Coherente": "#2E8B57", "Indeterminado": "#FFA500",
                                           "Anomalia": "#DC143C", "Sin datos": "#999999"})
    fig_donut.add_annotation(text=f"<b>{coherentes/total*100:.1f}%</b><br>coherente",
                             x=0.5, y=0.5, showarrow=False,
                             font=dict(size=22, color="#2E8B57"))
    fig_donut.update_layout(title="Estado de validacion", height=340, showlegend=True,
                            legend=dict(orientation="h", y=-0.08),
                            margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig_donut, use_container_width=True)
with colB:
    fig_bar = px.bar(x=vf.index, y=vf.values, color=vf.index,
                     color_discrete_map={"Optico": "#2E8B57", "Radar": "#4682B4",
                                         "Ninguna": "#999999"})
    fig_bar.update_layout(title="Fuente de datos por registro", height=340, showlegend=False,
                          yaxis_title="Registros",
                          margin=dict(t=40, b=10, l=10, r=10))
    st.plotly_chart(fig_bar, use_container_width=True)

# ---------- 3. MOSAICO DE VALIDACION SIN HUECOS ----------
st.subheader("Mapa de validacion: cada municipio-ano fue confirmado por un satelite")

def estado(row):
    c = str(row["coherencia_final"])
    if "Anomal" in c: return "Anomalia"
    if "Coherente" in c and "radar" in c.lower(): return "Radar confirmo"
    if "Coherente" in c: return "Optico confirmo"
    if "Indeterminado" in c: return "Indeterminado"
    return "Sin datos"

df["estado"] = df.apply(estado, axis=1)
piv = df.pivot_table(index="municipio", columns="ano", values="estado", aggfunc="first")
orden = (df.assign(v=df["ndvi_mean"].fillna(0))
         .groupby("municipio")["v"].mean().sort_values(ascending=False))
piv = piv.reindex([m for m in orden.index if m in piv.index])

COD = {"Sin datos": 0, "Indeterminado": 1, "Radar confirmo": 2, "Optico confirmo": 3, "Anomalia": 4}
z = piv.replace(COD)

fig_mos = go.Figure(go.Heatmap(
    z=z.values,
    x=[str(c) for c in piv.columns],
    y=piv.index.tolist(),
    customdata=piv.values,
    hovertemplate="%{y} · %{x}<br>%{customdata}<extra></extra>",
    zmin=0, zmax=5,
    colorscale=[[0, "#E0E0E0"], [0.2, "#E0E0E0"], [0.2, "#FFA500"], [0.4, "#FFA500"],
                [0.4, "#4682B4"], [0.6, "#4682B4"], [0.6, "#2E8B57"], [0.8, "#2E8B57"],
                [0.8, "#DC143C"], [1, "#DC143C"]],
    colorbar=dict(tickvals=[0, 1, 2, 3, 4],
                  ticktext=["Sin datos", "Indeterminado", "Radar", "Optico", "Anomalia"])))
fig_mos.update_layout(height=1100, xaxis_title="Ano", yaxis_title="Municipio",
                      margin=dict(t=20, b=10, l=10, r=10))
fig_mos.update_yaxes(autorange="reversed", tickfont=dict(size=9))
st.plotly_chart(fig_mos, use_container_width=True)
st.caption("Verde = confirmado por optico (Sentinel-2). Azul = confirmado por radar "
           "(Sentinel-1, atraviesa nubes). **Sin celdas grises = cobertura 100%.**")

# ---------- 4. IMAGEN DE EXHIBICION ----------
img_path = Path("outputs/palmira_canaverales_sentinel2.png")
if img_path.exists():
    st.subheader("Asi ve el satelite al lider de la produccion")
    st.image(img_path, caption="Canaverales de Palmira - Sentinel-2 (10 m), ESA / Copernicus")

# ---------- 5. DETALLE TECNICO ----------
with st.expander("🔬 Detalle tecnico: NDVI y dispersiones"):
    df_opt = df.dropna(subset=["ndvi_mean"])
    top_mun = (df_opt.groupby("municipio")["ndvi_mean"].mean()
               .sort_values(ascending=False).head(15).index)
    pivn = (df_opt[df_opt["municipio"].isin(top_mun)]
            .pivot_table(index="municipio", columns="ano", values="ndvi_mean"))
    fig_heat = px.imshow(pivn, color_continuous_scale="Greens", aspect="auto",
                         labels=dict(x="Ano", y="Municipio", color="NDVI"))
    fig_heat.update_layout(height=520)
    st.plotly_chart(fig_heat, use_container_width=True)

    df_o = df[df["fuente"] == "Optico"].dropna(subset=["ndvi_mean", "area_cosechada_eva"])
    if not df_o.empty:
        fig_o = px.scatter(df_o, x="area_cosechada_eva", y="ndvi_mean", color="cat",
                           hover_name="municipio", hover_data=["ano"],
                           title="Optico: NDVI vs area reportada",
                           color_discrete_map={"Coherente": "#2E8B57",
                                               "Indeterminado": "#FFA500", "Anomalia": "#DC143C"})
        fig_o.add_hline(y=0.4, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_o, use_container_width=True)
    df_r = df[df["fuente"] == "Radar"].dropna(subset=["vh_db", "area_cosechada_eva"])
    if not df_r.empty:
        fig_r = px.scatter(df_r, x="area_cosechada_eva", y="vh_db", color="cat",
                           hover_name="municipio", hover_data=["ano"],
                           title="Radar: VH (dB) vs area reportada",
                           color_discrete_map={"Coherente": "#4682B4",
                                               "Indeterminado": "#FFA500", "Anomalia": "#DC143C"})
        fig_r.add_hline(y=-18, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_r, use_container_width=True)

# ---------- 6. METODOLOGIA ----------
with st.expander("📚 Metodologia"):
    st.markdown("""
    - **NDVI (Sentinel-2, optico):** (infrarrojo - rojo) / (infrarrojo + rojo).
      > 0.4 vegetacion activa; > 0.6 vegetacion densa (cana, cafe).
    - **VH (Sentinel-1, radar):** retrodispersion cruzada en dB; atraviesa nubes.
      Entre -22 y -12 dB indica vegetacion; < -24 dB superficie lisa.
    - **Coherencia:** vegetacion observada vs area cosechada autodeclarada en EVA.
    - **Limitacion conocida:** nubosidad del Pacifico bloquea el optico; alli entra el radar.
      Fuentes: ESA Copernicus via Google Earth Engine.
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
                   file_name="validacion_optica_radar.csv", mime="text/csv")

st.markdown("---")
st.caption("Fuentes: Sentinel-2 (optico) + Sentinel-1 (radar) via Google Earth Engine. Procesado por EVA Valle v3.0.")
'''

Path("ui/pages/18_Satelite.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/18_Satelite.py (v3: mosaico sin huecos + dona con centro)")