"""Pagina Valor Economico: PIB agro municipal con precios v0 y doble ranking."""
from pathlib import Path

ECON = '''"""Modelo economico v0: valorizacion con precios de referencia (supuesto declarado)."""
from functools import lru_cache
import unicodedata

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

PRECIOS_REF = {  # COP/t, v0 (validar con Primer Mercado UPRA)
    "Caña": 160000, "Caña de azúcar": 160000,
    "Plátano": 1200000, "Banano": 1200000,
    "Naranja": 700000, "Mandarina": 900000, "Tomate": 1500000,
    "Piña": 900000, "Maracuyá": 3500000, "Papaya": 1000000,
    "Café": 2800000, "Aguacate": 2500000, "Yuca": 900000,
    "Maíz": 1100000, "Cacao": 12000000, "Guanábana": 2000000,
    "Guayaba": 800000,
}


def _norm(s) -> str:
    s = str(s)
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def _es_cana(nombre) -> bool:
    return "cana" in _norm(nombre)


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    return pd.read_csv(settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv",
                       low_memory=False)


def valorizar(df=None):
    df = df if df is not None else load_df()
    d = df.copy()
    d["precio_t"] = d.cultivo.map(PRECIOS_REF)
    d["valor"] = d.produccion_t * d.precio_t
    return d


def tabla_rank(anio=2025, excluye_cana=False):
    d = valorizar()
    d = d[d.ano == anio]
    if excluye_cana:
        d = d[~d.cultivo.map(_es_cana)]
    g = d.groupby("municipio").agg(valor=("valor", "sum"), ton=("produccion_t", "sum"))
    g = g[g.valor > 0]
    g["rank_pesos"] = g.valor.rank(ascending=False).astype(int)
    g["rank_ton"] = g.ton.rank(ascending=False).astype(int)
    g["salto"] = g.rank_ton - g.rank_pesos
    return g.sort_values("valor", ascending=False)


def serie_pib(excluye_cana=False):
    d = valorizar()
    d = d[d.valor > 0]
    if excluye_cana:
        d = d[~d.cultivo.map(_es_cana)]
    return d.groupby("ano")["valor"].sum()
'''
Path("core/analytics/economic.py").write_text(ECON, encoding="utf-8")
print("[OK] core/analytics/economic.py v2")

PAGE = '''"""Pagina 23: Valor economico (PIB agro) con precios de referencia v0."""
import streamlit as st
import plotly.graph_objects as go

from core.analytics.economic import serie_pib, tabla_rank

st.set_page_config(page_title="Valor economico | EVA Valle", page_icon="\\U0001F4B0",
                   layout="wide")

st.title("\\U0001F4B0 Valor economico del agro vallecaucano")
st.caption("PIB agro = produccion x precio de referencia v0. Supuesto metodologico "
           "declarado, pendiente de validacion con Precios de Primer Mercado (UPRA).")

c1, _ = st.columns([1, 3])
with c1:
    anio = st.selectbox("Ano", list(range(2019, 2026)), index=6)
    sin_cana = st.checkbox("Excluir cana de azucar")

tab = tabla_rank(anio, sin_cana)
serie = serie_pib(sin_cana)
n = serie.index[-1] - serie.index[0]
cagr = ((serie.iloc[-1] / serie.iloc[0]) ** (1 / n) - 1) * 100
salto = tab["salto"].idxmax()
s = tab.loc[salto]

k1, k2, k3, k4 = st.columns(4)
k1.metric("PIB agro dpto (billones COP)", f"{serie.loc[anio] / 1e12:,.2f}")
k2.metric("CAGR en pesos 19-25", f"{cagr:+.1f}%")
k3.metric(f"Top en pesos {anio}", tab.index[0])
k4.metric("Mayor salto de ranking", salto, f"+{int(s['salto'])} puestos")

st.markdown("#### Top 10 en pesos vs toneladas")
ca, cb = st.columns([3, 2])
t = tab.head(10).copy()
with ca:
    tv = t.copy()
    tv["M_COP"] = (tv.valor / 1e6).round(0)
    tv["ton"] = tv.ton.round(0)
    st.table(tv[["M_COP", "ton", "rank_pesos", "rank_ton", "salto"]])
with cb:
    fig = go.Figure(go.Bar(x=(t.valor / 1e6).round(0), y=t.index, orientation="h",
                           marker_color="#2E8B57"))
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("#### PIB agro departamental anual (miles de M COP)")
fig2 = go.Figure(go.Scatter(x=serie.index, y=(serie / 1e9).round(1),
                            mode="lines+markers", line=dict(color="#C98A2B")))
fig2.update_layout(height=320, margin=dict(l=20, r=20, t=10, b=10))
st.plotly_chart(fig2, use_container_width=True)

st.info(f"**Lectura:** el ranking en pesos no es el de toneladas. En {anio}, "
        f"**{salto}** salta {int(s['salto'])} puestos (#{int(s['rank_ton'])} en toneladas "
        f"-> #{int(s['rank_pesos'])} en pesos): su tonelada vale mas.")
'''
Path("ui/pages/23_Valor_Economico.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/23_Valor_Economico.py creada")

app = Path("app.py")
c = app.read_text(encoding="utf-8")
if "23_Valor_Economico" not in c:
    i = c.find("22_Recomendador.py")
    if i != -1:
        eol = c.find("\n", i) + 1
        nueva = ('        ("💰 5 · Económico — ¿cuánto vale?", 1, '
                 'st.Page("ui/pages/23_Valor_Economico.py", title="Valor Economico", '
                 'icon="💰")),\n')
        c = c[:eol] + nueva + c[eol:]
        app.write_text(c, encoding="utf-8")
        print("[OK] Valor Economico registrado (seccion 5, rol analista+)")
    else:
        print("[AVISO] no encontre la linea del Recomendador en app.py")
else:
    print("[INFO] ya estaba registrada")

print("\nReinicia Streamlit y entra a 💰 Valor Economico")