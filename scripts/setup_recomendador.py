"""Recomendador prescriptivo IRS: dos caminos (municipio->cultivos, cultivo->municipios)."""
from pathlib import Path

Path("core/analytics").mkdir(parents=True, exist_ok=True)

IRS = '''"""IRS: Indice de Recomendacion de Siembra (capa prescriptiva)."""
from functools import lru_cache

import pandas as pd

try:
    from config import settings
except Exception:
    from config.settings import settings

PESOS = {"lq": 0.40, "cagr": 0.30, "eff": 0.20, "div": 0.10}


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    p = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    return pd.read_csv(p, low_memory=False)


def build_irs(df: pd.DataFrame) -> pd.DataFrame:
    yr = int(df["ano"].max())
    acc = df.groupby(["municipio", "cultivo"])["produccion_t"].sum().reset_index()
    ult = df[df["ano"] == yr].groupby(["municipio", "cultivo"]).agg(
        p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum")).reset_index()
    ult = ult[ult.p > 0]
    zona = df.drop_duplicates("municipio").set_index("municipio")["zona"]

    m_tot = acc.groupby("municipio")["produccion_t"].sum()
    c_tot = acc.groupby("cultivo")["produccion_t"].sum()
    d_tot = acc["produccion_t"].sum()

    m = acc.merge(ult, on=["municipio", "cultivo"])
    m = m[m.produccion_t >= 100]
    m["share_m"] = m.produccion_t / m.municipio.map(m_tot)
    m["LQ"] = m.share_m / (m.cultivo.map(c_tot) / d_tot)

    g = df.groupby(["municipio", "cultivo", "ano"])["produccion_t"].sum()
    cagrs = {}
    for (mu, cu), s in g.groupby(level=[0, 1]):
        s2 = s.droplevel([0, 1]).sort_index()
        s2 = s2[s2 > 0]
        if len(s2) >= 2:
            n = s2.index[-1] - s2.index[0]
            if n > 0:
                cagrs[(mu, cu)] = ((s2.iloc[-1] / s2.iloc[0]) ** (1 / n) - 1) * 100
    cs = pd.Series(cagrs, name="CAGR")
    m = m.merge(cs, left_on=["municipio", "cultivo"], right_index=True, how="left")
    m = m[m.CAGR.notna() & (m.CAGR >= -5)]

    tr = ult.assign(r=ult.p / ult.c.replace(0, float("nan")))
    tr = tr[tr.p >= 500].groupby("cultivo")["r"].max()
    m["eff"] = (m.p / m.c.replace(0, float("nan")) / m.cultivo.map(tr)).clip(0, 1)

    m["div"] = 1 - m.share_m
    m["IRS"] = (PESOS["lq"] * m.LQ.clip(0, 3) / 3
                + PESOS["cagr"] * (m.CAGR.clip(-5, 30) + 5) / 35
                + PESOS["eff"] * m.eff.fillna(0)
                + PESOS["div"] * m.div) * 100

    def etiqueta(r):
        if r.LQ >= 1 and r.CAGR >= 5:
            return "Expandir"
        if r.LQ >= 1:
            return "Proteger"
        if r.CAGR >= 15:
            return "Apostar"
        return "Diversificar"

    m["etiqueta"] = m.apply(etiqueta, axis=1)
    m["zona"] = m.municipio.map(zona)
    return m.sort_values("IRS", ascending=False).reset_index(drop=True)


def top_cultivos(irs, municipio, n=5):
    return irs[irs.municipio == municipio].head(n)


def top_municipios(irs, cultivo, n=5):
    return irs[irs.cultivo == cultivo].head(n)
'''
Path("core/analytics/irs.py").write_text(IRS, encoding="utf-8")
print("[OK] core/analytics/irs.py creado")

PAGE = '''"""Pagina 22: Recomendador prescriptivo en dos direcciones (IRS)."""
import streamlit as st
import plotly.graph_objects as go

from core.analytics.irs import build_irs, load_df

st.set_page_config(page_title="Recomendador | EVA Valle", page_icon="\\U0001F3AF", layout="wide")

st.title("\\U0001F3AF Recomendador Prescriptivo (IRS)")
st.caption("IRS = 40% especializacion (LQ) + 30% momentum (CAGR) + 20% eficiencia + "
           "10% diversificacion. Filtros: volumen acumulado >= 100 t, CAGR >= -5%, "
           "activo en el ultimo ano.")


@st.cache_data(show_spinner=False)
def get_irs():
    return build_irs(load_df())


irs = get_irs()
COLOR = {"Expandir": "#2E8B57", "Proteger": "#2B6CB0",
         "Apostar": "#C98A2B", "Diversificar": "#DD6B20"}

modo = st.radio("Modo de recomendacion",
                ["\\U0001F331 Recomendar siembra (elige municipio)",
                 "\\U0001F4CD Recomendar municipio (elige cultivo)"],
                horizontal=True)
es_cultivo = modo.startswith("\\U0001F331")
nombre = "cultivo" if es_cultivo else "municipio"

if es_cultivo:
    sel = st.selectbox("Municipio", sorted(irs["municipio"].unique()))
    top = irs[irs["municipio"] == sel].head(5)
    st.markdown(f"#### Top 5 de siembras recomendadas para **{sel}**")
else:
    sel = st.selectbox("Cultivo", sorted(irs["cultivo"].unique()))
    top = irs[irs["cultivo"] == sel].head(5)
    st.markdown(f"#### Top 5 de municipios recomendados para **{sel}**")

if top.empty:
    st.warning("Sin candidatos que pasen los filtros para esa seleccion.")
else:
    c1, c2 = st.columns([3, 2])
    with c1:
        tbl = top[[nombre, "IRS", "LQ", "CAGR", "etiqueta", "zona"]].copy()
        tbl["IRS"] = tbl["IRS"].round(1)
        tbl["LQ"] = tbl["LQ"].round(2)
        tbl["CAGR"] = tbl["CAGR"].round(1).astype(str) + "%"
        tbl.columns = [nombre.capitalize(), "IRS (0-100)", "LQ", "CAGR", "Estrategia", "Zona"]
        st.table(tbl)
    with c2:
        fig = go.Figure(go.Bar(x=top["IRS"], y=top[nombre], orientation="h",
                               marker_color=[COLOR.get(e, "#4A5568") for e in top["etiqueta"]]))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)
    r0 = top.iloc[0]
    st.success(f"**Lectura:** para {sel}, la mejor opcion es **{r0[nombre]}** "
               f"(IRS {r0['IRS']:.0f}/100, LQ {r0['LQ']:.2f}, CAGR {r0['CAGR']:+.1f}%) "
               f"\\u2192 estrategia **{r0['etiqueta']}**.")
'''
Path("ui/pages/22_Recomendador.py").write_text(PAGE, encoding="utf-8")
print("[OK] ui/pages/22_Recomendador.py creada")

app = Path("app.py")
c = app.read_text(encoding="utf-8")
if "22_Recomendador" not in c:
    i = c.find("19_Zonas.py")
    if i != -1:
        eol = c.find("\n", i) + 1
        nueva = ('        ("\\U0001F3AF 4 \\u00b7 Prescriptivo \\u2014 \\u00bfque hacer?", 1, '
                 'st.Page("ui/pages/22_Recomendador.py", title="Recomendador", icon="\\U0001F3AF")),\\n')
        c = c[:eol] + nueva + c[eol:]
        app.write_text(c, encoding="utf-8")
        print("[OK] Recomendador registrado en 4 · Prescriptivo (rol analista+)")
    else:
        print("[AVISO] No encontre la linea de Zonas en app.py")
else:
    print("[INFO] El Recomendador ya estaba registrado")

print("\\nReinicia Streamlit y entra a 🎯 Recomendador")