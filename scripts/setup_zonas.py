"""Crea modulo de zonas + pagina 19_Zonas + registro en app.py."""
from pathlib import Path

MOD = '''"""Zonificacion del Valle del Cauca y agregacion de indicadores por zona."""
from __future__ import annotations

import pandas as pd

ZONAS = {
    "Norte": ["Alcala", "Andalucia", "Ansermanuevo", "Argelia", "Bolivar",
              "Cartago", "Caicedonia", "El Aguila", "El Dovio", "La Union",
              "La Victoria", "Obando", "Roldanillo", "Riofrio", "Sevilla",
              "Toro", "Trujillo", "Ulloa", "Versalles", "Zarzal"],
    "Centro": ["Bugalagrande", "Guadalajara de Buga", "Buga", "El Cerrito",
               "Ginebra", "Guacari", "Restrepo", "San Pedro", "Tulua",
               "Vijes", "Yotoco"],
    "Sur": ["Cali", "Candelaria", "Florida", "Jamundi", "Palmira",
            "Pradera", "Yumbo"],
    "Pacifico / Occidente": ["Buenaventura", "Calima", "Dagua", "Darien",
                             "La Cumbre"],
}

# Alias por si el dataset usa tildes o nombres alternos
ALIAS = {"Alcalá": "Alcala", "Andalucía": "Andalucia", "Bolívar": "Bolivar",
         "El Águila": "El Aguila", "La Unión": "La Union", "Riofrío": "Riofria",
         "Tuluá": "Tulua", "Guacarí": "Guacari", "Jamundí": "Jamundi",
         "Roldanillo": "Roldanillo"}


def _norm(m: str) -> str:
    return ALIAS.get(m, m)


def asignar_zona(municipio: str) -> str:
    m = _norm(str(municipio))
    for zona, lista in ZONAS.items():
        if m in lista or str(municipio) in lista:
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
    for zona, lista in ZONAS.items():
        sub = df[df["municipio"].map(lambda m: _norm(m) in lista or m in lista)]
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

PAGE = '''"""Pagina 19: Analisis por Zonas del Valle del Cauca."""
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
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, low_memory=False)


df = load_dataset()
if df.empty:
    st.error("Dataset no encontrado.")
    st.stop()

st.title("🗺️ Analisis por Zonas del Valle del Cauca")
st.caption("Subregiones: Norte, Centro, Sur y Pacifico/Occidente.")

anos = sorted(int(a) for a in df["ano"].dropna().unique())
sel = st.sidebar.multiselect("Anos", anos, default=[])
df_f = df.copy()
if sel:
    df_f = df_f[df_f["ano"].isin(sel)]

df_f["zona"] = df_f["municipio"].map(asignar_zona)
sin_zona = sorted(df_f[df_f["zona"] == "Sin zona"]["municipio"].unique())
if sin_zona:
    st.warning(f"Municipios sin zona asignada (revisar diccionario): {', '.join(sin_zona)}")

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
                                      "Sur": "#2E8B57", "Pacifico / Occidente": "#F4A261"})
    fig1.update_layout(title="Produccion por zona (t)", showlegend=False,
                       yaxis_title="t", margin=dict(t=40, b=10))
    st.plotly_chart(fig1, use_container_width=True)
with colB:
    fig2 = px.bar(ind.reset_index(), x="zona", y="rendimiento_t_ha", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacifico / Occidente": "#F4A261"})
    fig2.update_layout(title="Eficiencia por zona (t/ha cosechada)", showlegend=False,
                       yaxis_title="t/ha", margin=dict(t=40, b=10))
    st.plotly_chart(fig2, use_container_width=True)

# ---------- 3. GINI POR ZONA ----------
st.subheader("Concentracion interna por zona (Gini)")
colC, colD = st.columns(2)
with colC:
    fig3 = px.bar(ind.reset_index(), x="zona", y="gini_municipios", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacifico / Occidente": "#F4A261"})
    fig3.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig3.update_layout(title="Gini territorial (municipios dentro de la zona)",
                       showlegend=False, yaxis_range=[0, 1], margin=dict(t=40, b=10))
    st.plotly_chart(fig3, use_container_width=True)
with colD:
    fig4 = px.bar(ind.reset_index(), x="zona", y="gini_cultivos", color="zona",
                  color_discrete_map={"Norte": "#5FA8DC", "Centro": "#52B788",
                                      "Sur": "#2E8B57", "Pacifico / Occidente": "#F4A261"})
    fig4.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig4.update_layout(title="Gini de cultivos (diversificacion interna)",
                       showlegend=False, yaxis_range=[0, 1], margin=dict(t=40, b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.info("Gini bajo = produccion repartida / zona diversificada (menos riesgo). "
        "Gini alto = dependencia de pocos municipios o de un solo cultivo.")

# ---------- 4. TABLA COMPLETA ----------
st.subheader("Indicadores por zona (2019-2025 o filtro)")
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
st.caption("Zonificacion editable en core/analytics/zonas.py. "
           "Fuente: UPRA - EVA 2019-2025.")
'''

Path("core/analytics/zonas.py").write_text(MOD, encoding="utf-8")
Path("ui/pages/19_Zonas.py").write_text(PAGE, encoding="utf-8")

# Registrar en app.py despues de la pagina satelite
app = Path("app.py")
lines = app.read_text(encoding="utf-8").splitlines(keepends=True)
if not any("19_Zonas.py" in l for l in lines):
    nueva = '    st.Page("ui/pages/19_Zonas.py", title="Zonas", icon="\\U0001F5FA️"),\n'
    for i, l in enumerate(lines):
        if "18_Satelite.py" in l:
            lines.insert(i + 1, nueva)
            break
    app.write_text("".join(lines), encoding="utf-8")
    print("[OK] Pagina Zonas registrada en app.py")
else:
    print("[INFO] Pagina Zonas ya estaba registrada")

print("[OK] core/analytics/zonas.py")
print("[OK] ui/pages/19_Zonas.py")
print("\nReinicia Streamlit (Ctrl+C y streamlit run app.py)")