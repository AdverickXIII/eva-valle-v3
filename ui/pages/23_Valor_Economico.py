"""Pagina 23: Valor economico (PIB agro) con precios de referencia v0."""
import streamlit as st
import plotly.graph_objects as go

from core.analytics.economic import serie_pib, tabla_rank

st.set_page_config(page_title="Valor economico | EVA Valle", page_icon="\U0001F4B0",
                   layout="wide")

st.title("\U0001F4B0 Valor economico del agro vallecaucano")
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
