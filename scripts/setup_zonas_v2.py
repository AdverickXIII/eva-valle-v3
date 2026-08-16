"""V2: Zonificacion Oficial del Valle del Cauca (Ordenanza 513 / Plan de Desarrollo 2024-2027)."""
from pathlib import Path

MOD = '''"""Zonificacion oficial del Valle del Cauca (POTD / Ordenanza 513 de 2019)."""
from __future__ import annotations
import pandas as pd

# Diccionario oficial con variaciones de nombres para cruzar con la base EVA
ZONAS = {
    "Norte": [
        "Alcalá", "Alcala", "Ansermanuevo", "Argelia", "Bolívar", "Bolivar",
        "Cartago", "El Águila", "El Aguila", "El Cairo", "El Dovio",
        "La Unión", "La Union", "La Victoria", "Obando", "Roldanillo",
        "Toro", "Ulloa", "Versalles", "Zarzal"
    ],
    "Centro": [
        "Andalucía", "Andalucia", "Guadalajara de Buga", "Buga", "Bugalagrande",
        "Calima", "Darien", "Ginebra", "Guacarí", "Guacari", "Restrepo",
        "Riofrío", "Riofrio", "San Pedro", "Trujillo", "Tuluá", "Tulua",
        "Yotoco", "Sevilla", "Caicedonia"
    ],
    "Sur": [
        "Cali", "Candelaria", "Dagua", "El Cerrito", "Florida",
        "Jamundí", "Jamundi", "La Cumbre", "Palmira", "Pradera",
        "Vijes", "Yumbo"
    ],
    "Pacífico": [
        "Buenaventura"
    ]
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

def indicadores_por_zona(df: pd.DataFrame) -> pd.DataFrame:
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

PAGE = '''"""Pagina 19: Analisis por Zonas Oficiales del Valle del Cauca."""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.zonas import asignar_zona, indicadores_por_zona

st.set_page_config(page_title="Zonas | EVA Valle", page_icon="🗺️", layout="wide")

@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False) if p.exists() else pd.DataFrame()

df = load_dataset()
if df.empty:
    st.error("Dataset no encontrado."); st.stop()

st.title("🗺️ Analisis por Subregiones Oficiales")
st.caption("Zonificacion segun POTD (Ordenanza 513 de 2019) y Plan de Desarrollo 2024-2027.")
st.info("📜 **Alineacion Institucional:** Esta pagina utiliza la division administrativa oficial del departamento (Norte, Centro, Sur, Pacifico), permitiendo que los hallazgos se integren directamente a los instrumentos de planeacion de la Gobernacion.")

anos = sorted(int(a) for a in df["ano"].dropna().unique())
sel = st.sidebar.multiselect("Anos", anos, default=[])
df_f = df.copy()
if sel: df_f = df_f[df_f["ano"].isin(sel)]

df_f["zona"] = df_f["municipio"].map(asignar_zona)
sin_zona = sorted(df_f[df_f["zona"] == "Sin zona"]["municipio"].unique())
if sin_zona:
    st.warning(f"Municipios en EVA sin mapeo oficial: {', '.join(sin_zona)}")

ind = indicadores_por_zona(df_f)

# ---------- 1. LIDERES POR METRICA ----------
st.subheader("Lideres por metrica")
tp = ind["produccion_t"].idxmax()
ts = ind["area_sembrada_ha"].idxmax()
tc = ind["area_cosechada_ha"].idxmax()
te = ind["rendimiento_t_ha"].idxmax()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Zona mas productiva", tp, f"{ind.loc[tp, 'produccion_t']:,.0f} t")
c2.metric("Mayor area sembrada", ts, f"{ind.loc[ts, 'area_sembrada_ha']:,.0f} ha")
c3.metric("Mayor area cosechada", tc, f"{ind.loc[tc, 'area_cosechada_ha']:,.0f} ha")
c4.metric("Mas eficiente (t/ha)", te, f"{ind.loc[te, 'rendimiento_t_ha']:.1f} t/ha")

# ---------- 2. PRODUCCION Y EFICIENCIA ----------
colA, colB = st.columns(2)
with colA:
    fig1 = px.bar(ind.reset_index(), x="zona", y="produccion_t", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacífico": "#F4A261"})
    fig1.update_layout(title="Produccion por zona (t)", showlegend=False,
                       yaxis_title="t", margin=dict(t=40, b=10))
    st.plotly_chart(fig1, use_container_width=True)
with colB:
    fig2 = px.bar(ind.reset_index(), x="zona", y="rendimiento_t_ha", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacífico": "#F4A261"})
    fig2.update_layout(title="Eficiencia por zona (t/ha cosechada)", showlegend=False,
                       yaxis_title="t/ha", margin=dict(t=40, b=10))
    st.plotly_chart(fig2, use_container_width=True)

# ---------- 3. GINI POR ZONA ----------
st.subheader("Concentracion interna por zona (Gini)")
colC, colD = st.columns(2)
with colC:
    fig3 = px.bar(ind.reset_index(), x="zona", y="gini_municipios", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacífico": "#F4A261"})
    fig3.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig3.update_layout(title="Gini territorial (municipios dentro de la zona)",
                       showlegend=False, yaxis_range=[0, 1], margin=dict(t=40, b=10))
    st.plotly_chart(fig3, use_container_width=True)
with colD:
    fig4 = px.bar(ind.reset_index(), x="zona", y="gini_cultivos", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacífico": "#F4A261"})
    fig4.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig4.update_layout(title="Gini de cultivos (diversificacion interna)",
                       showlegend=False, yaxis_range=[0, 1], margin=dict(t=40, b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.info("💡 **Lectura del Gini:** Un Gini territorial alto indica que la produccion de la zona depende de 1 o 2 municipios (riesgo). Un Gini de cultivos bajo indica que la zona esta diversificada (resiliencia).")

# ---------- 4. TABLA COMPLETA ----------
st.subheader("Indicadores por Subregion Oficial")
tabla = ind.copy()
tabla["produccion_t"] = tabla["produccion_t"].round(0)
tabla["area_sembrada_ha"] = tabla["area_sembrada_ha"].round(0)
tabla["area_cosechada_ha"] = tabla["area_cosechada_ha"].round(0)
tabla["rendimiento_t_ha"] = tabla["rendimiento_t_ha"].round(1)
tabla["aprovechamiento_pct"] = tabla["aprovechamiento_pct"].round(1)
tabla["share_dept_pct"] = tabla["share_dept_pct"].round(1)
tabla["gini_municipios"] = tabla["gini_municipios"].round(2)
tabla["gini_cultivos"] = tabla["gini_cultivos"].round(2)
st.dataframe(tabla, use_container_width=True)

st.markdown("---")
st.caption("Fuentes: UPRA - EVA 2019-2025. Zonificacion: POTD Valle del Cauca (Ordenanza 513 de 2019) y Plan de Desarrollo 2024-2027.")
'''

Path("core/analytics/zonas.py").write_text(MOD, encoding="utf-8")
Path("ui/pages/19_Zonas.py").write_text(PAGE, encoding="utf-8")
print("[OK] Zonificacion actualizada a la Oficial (Ordenanza 513 / Plan de Desarrollo)")
print("Reinicia Streamlit: Ctrl+C y luego streamlit run app.py")