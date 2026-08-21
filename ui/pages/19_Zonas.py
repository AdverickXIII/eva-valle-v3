"""Pagina 19: Zonas oficiales con analisis dual CON/SIN cana."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import settings
from core.analytics.zonas import asignar_zona, indicadores_por_zona

st.set_page_config(page_title="Zonas | EVA Valle", page_icon="🗺️", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()


df = load_dataset()
if df.empty:
    st.error("Dataset no encontrado.")
    st.stop()

st.title("🗺️ Analisis por Subregiones Oficiales")
st.caption("Zonificacion segun POTD (Ordenanza 513 de 2019) y Plan de Desarrollo 2024-2027.")
st.info("📜 **Alineacion Institucional:** division administrativa oficial del departamento "
        "(Norte, Centro, Sur, Pacifico), alineada con los instrumentos de planeacion de la Gobernacion.")

# ---------- ESCENARIO DUAL ----------
escenario = st.radio("Escenario de analisis", ["Con caña", "Sin caña"],
                     horizontal=True,
                     help="La cana domina el tonelaje departamental; compara ambos escenarios.")

anos = sorted(int(a) for a in df["ano"].dropna().unique())
sel = st.sidebar.multiselect("Anos", anos, default=[])
df_f = df.copy()
if sel:
    df_f = df_f[df_f["ano"].isin(sel)]

df_f["zona"] = df_f["municipio"].map(asignar_zona)
sin_zona = sorted(df_f[df_f["zona"] == "Sin zona"]["municipio"].unique())
if sin_zona:
    st.warning(f"Municipios en EVA sin mapeo oficial: {', '.join(sin_zona)}")

ind = indicadores_por_zona(df_f, excluye_cana=(escenario == "Sin caña"))

# ---------- 1. LIDERES ----------
st.subheader(f"Lideres por metrica — escenario {escenario}")
tp = ind["produccion_t"].idxmax()
ts = ind["area_sembrada_ha"].idxmax()
tc = ind["area_cosechada_ha"].idxmax()
te = ind["rendimiento_t_ha"].idxmax()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Zona mas productiva", tp, f"{ind.loc[tp, 'produccion_t']:,.0f} t")
c2.metric("Mayor area sembrada", ts, f"{ind.loc[ts, 'area_sembrada_ha']:,.0f} ha")
c3.metric("Mayor area cosechada", tc, f"{ind.loc[tc, 'area_cosechada_ha']:,.0f} ha")
c4.metric("Mas eficiente (t/ha)", te, f"{ind.loc[te, 'rendimiento_t_ha']:.1f} t/ha")

COLORS = {"Norte": "#5FA8DC", "Centro": "#52B788", "Sur": "#2E8B57", "Pacífico": "#F4A261"}

# ---------- 2. PRODUCCION Y EFICIENCIA ----------
colA, colB = st.columns(2)
with colA:
    fig1 = px.bar(ind.reset_index(), x="zona", y="produccion_t", color="zona",
                  color_discrete_map=COLORS)
    fig1.update_layout(title=f"Produccion por zona ({escenario})", showlegend=False,
                       yaxis_title="t", margin=dict(t=40, b=10))
    st.plotly_chart(fig1, use_container_width=True)
with colB:
    fig2 = px.bar(ind.reset_index(), x="zona", y="rendimiento_t_ha", color="zona",
                  color_discrete_map=COLORS)
    fig2.update_layout(title=f"Eficiencia por zona ({escenario})", showlegend=False,
                       yaxis_title="t/ha", margin=dict(t=40, b=10))
    st.plotly_chart(fig2, use_container_width=True)

# ---------- 3. GINI ----------
st.subheader("Concentracion interna por zona (Gini)")
colC, colD = st.columns(2)
with colC:
    fig3 = px.bar(ind.reset_index(), x="zona", y="gini_municipios", color="zona",
                  color_discrete_map=COLORS)
    fig3.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig3.update_layout(title="Gini territorial (municipios dentro de la zona)",
                       showlegend=False, yaxis_range=[0, 1], margin=dict(t=40, b=10))
    st.plotly_chart(fig3, use_container_width=True)
with colD:
    fig4 = px.bar(ind.reset_index(), x="zona", y="gini_cultivos", color="zona",
                  color_discrete_map=COLORS)
    fig4.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig4.update_layout(title="Gini de cultivos (diversificacion interna)",
                       showlegend=False, yaxis_range=[0, 1], margin=dict(t=40, b=10))
    st.plotly_chart(fig4, use_container_width=True)

# ---------- 4. COMPARATIVA DUAL (siempre visible) ----------
st.caption("Nota: Pacifico = 1 municipio (Buenaventura) -> Gini territorial = 0 "
                   "por definicion (sin desigualdad interna posible).")
st.subheader("Comparativa dual: con cana vs sin cana")
ic = indicadores_por_zona(df_f, excluye_cana=False)
isn = indicadores_por_zona(df_f, excluye_cana=True)
comp = pd.DataFrame({
    "Prod. con cana (t)": ic["produccion_t"].map("{:,.0f}".format),
    "Prod. sin cana (t)": isn["produccion_t"].map("{:,.0f}".format),
    "Rend. con cana": ic["rendimiento_t_ha"].round(1),
    "Rend. sin cana": isn["rendimiento_t_ha"].round(1),
    "Gini cult. con": ic["gini_cultivos"].round(2),
    "Gini cult. sin": isn["gini_cultivos"].round(2),
})
st.dataframe(comp, use_container_width=True)

lider_con = ic["produccion_t"].idxmax()
lider_sin = isn["produccion_t"].idxmax()
if lider_con != lider_sin:
    st.success(f"💡 **El efecto cana:** con canña lidera **{lider_con}**; sin caña el "
               f"liderazgo productivo pasa a **{lider_sin}**.")
else:
    st.info(f"💡 **{lider_con}** lidera en ambos escenarios; sin caña su peso relativo cambia.")

# ---------- 5. TABLA COMPLETA ----------
st.subheader(f"Indicadores por zona — {escenario}")
tabla = ind.copy()
for col in ["produccion_t", "area_sembrada_ha", "area_cosechada_ha"]:
    tabla[col] = tabla[col].round(0)
for col in ["rendimiento_t_ha", "aprovechamiento_pct", "share_dept_pct"]:
    tabla[col] = tabla[col].round(1)
for col in ["gini_municipios", "gini_cultivos"]:
    tabla[col] = tabla[col].round(2)
st.dataframe(tabla, use_container_width=True)

st.markdown("---")
st.caption("Fuentes: UPRA - EVA 2019-2025. Zonificacion: POTD (Ordenanza 513 de 2019) "
           "y Plan de Desarrollo 2024-2027.")
