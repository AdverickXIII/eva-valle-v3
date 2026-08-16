"""V3: Zonas oficiales con analisis dual CON/SIN cana + fix Santiago de Cali."""
from pathlib import Path

MOD = '''"""Zonificacion oficial del Valle del Cauca (POTD / Ordenanza 513 de 2019)."""
from __future__ import annotations

import pandas as pd

ZONAS = {
    "Norte": [
        "Alcalá", "Alcala", "Ansermanuevo", "Argelia", "Bolívar", "Bolivar",
        "Cartago", "El Águila", "El Aguila", "El Cairo", "El Dovio",
        "La Unión", "La Union", "La Victoria", "Obando", "Roldanillo",
        "Toro", "Ulloa", "Versalles", "Zarzal"],
    "Centro": [
        "Andalucía", "Andalucia", "Guadalajara de Buga", "Buga", "Bugalagrande",
        "Calima", "Darien", "Ginebra", "Guacarí", "Guacari", "Restrepo",
        "Riofrío", "Riofrio", "San Pedro", "Trujillo", "Tuluá", "Tulua",
        "Yotoco", "Sevilla", "Caicedonia"],
    "Sur": [
        "Cali", "Santiago de Cali", "Candelaria", "Dagua", "El Cerrito",
        "Florida", "Jamundí", "Jamundi", "La Cumbre", "Palmira", "Pradera",
        "Vijes", "Yumbo"],
    "Pacífico": ["Buenaventura"],
}


def asignar_zona(municipio: str) -> str:
    m = str(municipio).strip()
    for zona, lista in ZONAS.items():
        if m in lista:
            return zona
    return "Sin zona"


def gini(values) -> float:
    v = sorted(float(x) for x in values if x > 0)
    n = len(v)
    if n == 0 or sum(v) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * sum(v)) - (n + 1) / n


def indicadores_por_zona(df: pd.DataFrame, excluye_cana: bool = False) -> pd.DataFrame:
    if excluye_cana:
        df = df[df["cultivo"] != "Caña"]
    filas = []
    total = df["produccion_t"].sum()
    for zona in ZONAS.keys():
        sub = df[df["zona"] == zona]
        if sub.empty:
            continue
        prod = sub["produccion_t"].sum()
        sem = sub["area_sembrada_ha"].sum()
        cos = sub["area_cosechada_ha"].sum()
        filas.append({
            "zona": zona,
            "municipios": sub["municipio"].nunique(),
            "produccion_t": prod,
            "area_sembrada_ha": sem,
            "area_cosechada_ha": cos,
            "rendimiento_t_ha": prod / cos if cos else 0,
            "aprovechamiento_pct": (cos / sem * 100) if sem else 0,
            "share_dept_pct": prod / total * 100 if total else 0,
            "gini_municipios": gini(sub.groupby("municipio")["produccion_t"].sum().values),
            "gini_cultivos": gini(sub.groupby("cultivo")["produccion_t"].sum().values),
        })
    return pd.DataFrame(filas).set_index("zona")
'''

PAGE = '''"""Pagina 19: Zonas oficiales con analisis dual CON/SIN cana."""
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
st.subheader("Comparativa dual: con cana vs sin cana")
ic = indicadores_por_zona(df_f, excluye_cana=False)
isn = indicadores_por_zona(df_f, excluye_cana=True)
comp = pd.DataFrame({
    "Prod. con cana (t)": ic["produccion_t"].round(0),
    "Prod. sin cana (t)": isn["produccion_t"].round(0),
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
'''

Path("core/analytics/zonas.py").write_text(MOD, encoding="utf-8")
Path("ui/pages/19_Zonas.py").write_text(PAGE, encoding="utf-8")
print("[OK] zonas.py v3: dual CON/SIN cana + 'Santiago de Cali' mapeado al Sur")
print("Reinicia Streamlit: Ctrl+C y streamlit run app.py")