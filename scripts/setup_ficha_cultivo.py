"""Agrega 4.15: ficha tecnica interactiva por cultivo (CAGR + series + elasticidad)."""
from pathlib import Path

MOD = '''"""Diagnostico interactivo por cultivo: serie, motor CAGR, elasticidad y narrativa."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ui.charts.theme import apply_theme


def crop_diagnostic(df: pd.DataFrame, cultivo: str) -> dict:
    sub = df[df["cultivo"] == cultivo]
    agg = (sub.groupby("ano")
           .agg(p=("produccion_t", "sum"), a=("area_sembrada_ha", "sum"),
                c=("area_cosechada_ha", "sum"))
           .sort_index())
    agg = agg[(agg.p > 0) & (agg.c > 0)]
    f, l = agg.iloc[0], agg.iloc[-1]
    n = max(len(agg) - 1, 1)
    cagr_p = ((l.p / f.p) ** (1 / n) - 1) * 100
    cagr_a = ((l.a / f.a) ** (1 / n) - 1) * 100 if (l.a > 0 and f.a > 0) else 0.0
    cagr_r = (((l.p / l.c) / (f.p / f.c)) ** (1 / n) - 1) * 100

    elast = None
    if len(agg) >= 4 and agg.a.nunique() > 1 and (agg.a > 0).all():
        elast = float(np.polyfit(np.log(agg.a.values), np.log(agg.p.values), 1)[0])

    total_dept = df["produccion_t"].sum()
    prod_total = sub["produccion_t"].sum()

    if cagr_p <= -5:
        tipo = "Colapso"
    elif cagr_a > 2 and cagr_r > 2:
        tipo = "Expansion con tecnologia"
    elif cagr_a > 2:
        tipo = "Expansion extensiva"
    elif cagr_r > 2:
        tipo = "Intensificacion"
    else:
        tipo = "Estable"

    top_mun = (sub.groupby("municipio")["produccion_t"].sum()
               .sort_values(ascending=False).head(5))
    top_df = pd.DataFrame({"municipio": top_mun.index, "produccion_t": top_mun.values})
    top_df["share_pct"] = (top_df["produccion_t"] / prod_total * 100).round(1)

    narrativa = (
        f"**{cultivo}**: {prod_total:,.0f} t acumuladas "
        f"({prod_total / total_dept * 100:.1f}% del Valle). "
        f"CAGR {cagr_p:+.1f}% anual 2019-2025. "
        f"Motor: **{tipo.lower()}** (area {cagr_a:+.1f}% / rendimiento {cagr_r:+.1f}%). "
    )
    if elast is not None:
        narrativa += (f"Elasticidad area-produccion ≈ {elast:.2f}: "
                      + ("crecimiento sensible al area (extensivo)."
                         if elast > 0.8
                         else "crecimiento poco dependiente del area (intensivo)."))
    else:
        narrativa += "Elasticidad no estimable con pocos anos."

    return {"prod_total": prod_total, "cagr_prod": cagr_p, "cagr_area": cagr_a,
            "cagr_rend": cagr_r, "tipo": tipo, "elasticidad": elast,
            "top_mun": top_df, "narrativa": narrativa, "agg": agg}


def plot_crop_serie(diag: dict, cultivo: str):
    agg = diag["agg"]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Produccion (t)", "Rendimiento (t/ha)"],
                        vertical_spacing=0.12)
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p, mode="lines+markers",
                             line=dict(color="#2E8B57", width=3), name="Produccion"), 1, 1)
    fig.add_trace(go.Scatter(x=agg.index, y=agg.p / agg.c, mode="lines+markers",
                             line=dict(color="#5FA8DC", width=2), name="Rendimiento"), 2, 1)
    fig.update_layout(height=480, margin=dict(t=40, b=10), showlegend=False,
                      xaxis_title="Ano")
    return apply_theme(fig, f"Serie historica: {cultivo}")


def plot_crop_motor(diag: dict):
    vals = [diag["cagr_prod"], diag["cagr_area"], diag["cagr_rend"]]
    labs = ["CAGR produccion", "CAGR area", "CAGR rendimiento"]
    cols = ["#2E8B57" if v >= 0 else "#D62728" for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=labs, orientation="h", marker_color=cols,
                           text=[f"{v:+.1f}%" for v in vals], textposition="outside"))
    fig.add_vline(x=0, line_color="gray")
    fig.update_layout(margin=dict(t=40, b=10, l=10), height=300,
                      xaxis_title="CAGR 2019-2025 (%)")
    return apply_theme(fig, "Motor del crecimiento")
'''

Path("ui/charts/crop_card.py").write_text(MOD, encoding="utf-8")

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

if "crop_card" not in c:
    imp = "from ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes"
    c = c.replace(imp, imp + "\nfrom ui.charts.crop_card import crop_diagnostic, plot_crop_serie, plot_crop_motor")

marcador = 'tamano de burbuja = volumen total.")'
if marcador not in c:
    print("[ERROR] No encontre el caption de 4.14")
    raise SystemExit(1)

NEW = marcador + '''
        st.subheader("4.15 Diagnostico interactivo por cultivo")
        cultivos_ord = (df_f.groupby("cultivo")["produccion_t"].sum()
                        .sort_values(ascending=False))
        opcion = st.selectbox("Selecciona un cultivo", cultivos_ord.index.tolist(),
                              help="Elige cualquier cultivo para ver su diagnostico completo.")
        diag = crop_diagnostic(df_f, opcion)
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Produccion acumulada", f"{diag['prod_total']:,.0f} t")
        k2.metric("CAGR produccion", f"{diag['cagr_prod']:+.1f}%")
        k3.metric("CAGR area", f"{diag['cagr_area']:+.1f}%")
        k4.metric("CAGR rendimiento", f"{diag['cagr_rend']:+.1f}%")
        k5.metric("Elasticidad",
                  f"{diag['elasticidad']:.2f}" if diag['elasticidad'] is not None else "n/d")
        st.info(diag["narrativa"])
        cA, cB = st.columns([3, 2])
        with cA:
            st.plotly_chart(plot_crop_serie(diag, opcion), use_container_width=True)
        with cB:
            st.plotly_chart(plot_crop_motor(diag), use_container_width=True)
            st.markdown("**Top 5 municipios productores**")
            st.dataframe(diag["top_mun"], use_container_width=True, hide_index=True)
'''

c = c.replace(marcador, NEW, 1)
p.write_text(c, encoding="utf-8")
print("[OK] ui/charts/crop_card.py creado")
print("[OK] 4.15 ficha interactiva por cultivo agregada")
print("Reinicia Streamlit y revisa Descriptivo -> Crecimiento -> 4.15")