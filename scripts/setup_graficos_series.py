"""Agrega graficos a la pestana Series de Tiempo (4.7 y 4.8)."""
from pathlib import Path

MOD = '''"""Graficos de series de tiempo: serie+tendencia, shocks y estacionalidad A/B."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ui.charts.theme import apply_theme


def _serie_anual(df: pd.DataFrame):
    s = df.groupby("ano")["produccion_t"].sum().sort_index()
    x = s.index.astype(int).values
    xc = x - x.min()
    y = s.values.astype(float)
    coef = np.polyfit(xc, y, 1)
    trend = np.polyval(coef, xc)
    return x, y, trend


def plot_serie_produccion(df: pd.DataFrame) -> go.Figure:
    x, y, trend = _serie_anual(df)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers",
                             name="Produccion observada",
                             line=dict(color="#2E8B57", width=3),
                             marker=dict(size=9)))
    fig.add_trace(go.Scatter(x=x, y=trend, mode="lines",
                             name="Tendencia lineal",
                             line=dict(color="#94A3B8", dash="dash", width=2)))
    fig.update_layout(yaxis_title="Produccion (t)", xaxis_title="Ano",
                      yaxis_tickformat="~s", hovermode="x unified",
                      margin=dict(t=40, b=10))
    return apply_theme(fig, "Serie anual de produccion y su tendencia")


def plot_shocks(df: pd.DataFrame) -> go.Figure:
    x, y, trend = _serie_anual(df)
    resid = (y - trend) / trend * 100
    colors = ["#D62728" if abs(r) > 2 else "#52B788" for r in resid]
    fig = go.Figure(go.Bar(x=x, y=resid, marker_color=colors,
                           hovertemplate="Ano %{x}<br>Desviacion: %{y:.2f}%<extra></extra>"))
    fig.add_hline(y=0, line_color="gray")
    fig.update_layout(yaxis_title="Desviacion vs tendencia (%)",
                      showlegend=False, margin=dict(t=40, b=10))
    return apply_theme(fig, "Shocks: anos que se salieron de la tendencia")


def plot_estacionalidad_ab(df_est: pd.DataFrame) -> go.Figure:
    d = df_est.sort_values("dif_porcent", key=abs, ascending=False).head(12)
    d = d.sort_values("dif_porcent")
    colors = ["#2E8B57" if s else "#ADB5BD" for s in d["diferencia_significativa"]]
    fig = go.Figure(go.Bar(y=d["cultivo"], x=d["dif_porcent"], orientation="h",
                           marker_color=colors,
                           hovertemplate="%{y}<br>B vs A: %{x:.1f}%<extra></extra>"))
    fig.add_vline(x=0, line_color="gray")
    fig.update_layout(xaxis_title="Diferencia semestre B vs A (%)",
                      yaxis=dict(autorange="reversed"), showlegend=False,
                      margin=dict(t=40, b=10, l=10))
    return apply_theme(fig, "Estacionalidad: cultivos con diferencia significativa A vs B")
'''

Path("ui/charts/ts_charts.py").write_text(MOD, encoding="utf-8")

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

# 1) Import
imp = "from ui.charts.growth import plot_cagr_divergente"
if "ts_charts" not in c:
    c = c.replace(imp, imp + "\nfrom ui.charts.ts_charts import (plot_serie_produccion, plot_shocks, plot_estacionalidad_ab)")

# 2) Reemplazar bloque tab4
i4 = c.find("    with tab4:")
i5 = c.find("    with tab5:")
if i4 == -1 or i5 == -1:
    print("[ERROR] No encontre tab4/tab5")
    raise SystemExit(1)

NEW_TAB4 = '''    with tab4:
        st.subheader("4.7 Series de Tiempo (STL)")
        with st.spinner("Ejecutando STL..."):
            df_stl = cached_time_series(df_f)
        if not df_stl.empty:
            st.dataframe(df_stl, use_container_width=True)
            st.caption("Dickey-Fuller con p > 0.05 = serie **no estacionaria**: tiene "
                       "tendencia propia (crecimiento estructural), por eso se modela aparte.")
        colA, colB = st.columns(2)
        with colA:
            st.plotly_chart(plot_serie_produccion(df_f), use_container_width=True)
        with colB:
            st.plotly_chart(plot_shocks(df_f), use_container_width=True)
        st.caption("Rojo = ano que se desvio >2% de la tendencia (candidato a shock: "
                   "clima, paro, plaga). Verde = comportamiento normal.")

        st.subheader("4.8 Estacionalidad A vs B")
        with st.spinner("Ejecutando Wilcoxon..."):
            df_est = cached_seasonality(df_f)
        if not df_est.empty:
            st.plotly_chart(plot_estacionalidad_ab(df_est), use_container_width=True)
            st.caption("Verde = diferencia significativa entre semestres (p < 0.05): "
                       "cultivo con estacionalidad marcada. Gris = no significativa.")
            st.dataframe(df_est.head(15), use_container_width=True)
            render_download_button(df_est, "estacionalidad_ab.csv")

'''

c = c[:i4] + NEW_TAB4 + c[i5:]
p.write_text(c, encoding="utf-8")
print("[OK] ui/charts/ts_charts.py creado")
print("[OK] tab4 con 3 graficos nuevos")
print("Reinicia Streamlit y revisa Descriptivo -> Series de Tiempo")