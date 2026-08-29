"""Pagina 22: Recomendador prescriptivo en dos direcciones (IRS)."""
import streamlit as st
import plotly.graph_objects as go

from core.analytics.irs import build_irs, load_df

st.set_page_config(page_title="Recomendador | EVA Valle", page_icon="\U0001F3AF", layout="wide")

st.title("\U0001F3AF Recomendador Prescriptivo (IRS)")
st.caption("IRS = 40% especializacion (LQ) + 30% momentum (CAGR) + 20% eficiencia + "
           "10% diversificacion. Filtros: volumen acumulado >= 100 t, CAGR >= -5%, "
           "activo en el ultimo ano.")


@st.cache_data(show_spinner=False, ttl=3600)
def get_irs():
    return build_irs(load_df())


irs = get_irs()
COLOR = {"Expandir": "#2E8B57", "Proteger": "#2B6CB0",
         "Apostar": "#C98A2B", "Diversificar": "#DD6B20"}

modo = st.radio("Modo de recomendacion",
                ["\U0001F331 Recomendar siembra (elige municipio)",
                 "\U0001F4CD Recomendar municipio (elige cultivo)"],
                horizontal=True)
es_cultivo = modo.startswith("\U0001F331")
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
               f"\u2192 estrategia **{r0['etiqueta']}**.")
