"""Agrega 4.14: descomposicion del crecimiento (area vs rendimiento) con scatter de cuadrantes."""
from pathlib import Path

MOD = '''"""Descomposicion del crecimiento: CAGR produccion = CAGR area + CAGR rendimiento."""
import plotly.express as px
import pandas as pd

from ui.charts.theme import apply_theme

COLORES = {"Expansion con tecnologia": "#2E8B57",
           "Intensificacion": "#52B788",
           "Expansion extensiva": "#F4A261",
           "Estable": "#ADB5BD",
           "Colapso": "#D62728"}


def descomponer_crecimiento(df: pd.DataFrame, min_prod_total: float = 10000) -> pd.DataFrame:
    filas = []
    for cultivo, sub in df.groupby("cultivo"):
        agg = (sub.groupby("ano")
               .agg(p=("produccion_t", "sum"), a=("area_sembrada_ha", "sum"),
                    c=("area_cosechada_ha", "sum"))
               .sort_index())
        agg = agg[(agg.p > 0) & (agg.a > 0) & (agg.c > 0)]
        if len(agg) < 2 or agg.p.sum() < min_prod_total:
            continue
        f, l = agg.iloc[0], agg.iloc[-1]
        n = len(agg) - 1
        cagr_p = ((l.p / f.p) ** (1 / n) - 1) * 100
        cagr_a = ((l.a / f.a) ** (1 / n) - 1) * 100
        cagr_r = (((l.p / l.c) / (f.p / f.c)) ** (1 / n) - 1) * 100
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
        filas.append({"cultivo": cultivo, "cagr_prod": round(cagr_p, 1),
                      "cagr_area": round(cagr_a, 1), "cagr_rend": round(cagr_r, 1),
                      "tipo": tipo, "prod_total": round(agg.p.sum())})
    return pd.DataFrame(filas)


def plot_cuadrantes(df_dec: pd.DataFrame):
    fig = px.scatter(df_dec, x="cagr_area", y="cagr_rend", color="tipo",
                     size="prod_total", size_max=28, hover_name="cultivo",
                     hover_data=["cagr_prod"],
                     color_discrete_map=COLORES,
                     labels={"cagr_area": "CAGR area sembrada (%)",
                             "cagr_rend": "CAGR rendimiento (%)",
                             "tipo": "Tipo de crecimiento"})
    fig.add_hline(y=0, line_color="gray", line_dash="dash")
    fig.add_vline(x=0, line_color="gray", line_dash="dash")
    fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=560)
    return apply_theme(fig, "Motor del crecimiento: area vs rendimiento por cultivo")
'''

Path("ui/charts/growth_decomp.py").write_text(MOD, encoding="utf-8")

p = Path("ui/pages/2_Descriptivo.py")
c = p.read_text(encoding="utf-8")

if "growth_decomp" not in c:
    imp = "from ui.charts.growth import plot_cagr_divergente"
    c = c.replace(imp, imp + "\nfrom ui.charts.growth_decomp import descomponer_crecimiento, plot_cuadrantes")

old = '            st.info(f"Un 1% de aumento en area genera ~{elast[\'elasticidad\']:.2f}% en produccion.")'
new = old + '''
        st.subheader("4.14 Descomposicion del crecimiento: area vs rendimiento")
        df_dec = descomponer_crecimiento(df_f)
        st.plotly_chart(plot_cuadrantes(df_dec), use_container_width=True)
        st.dataframe(df_dec.sort_values("cagr_prod", ascending=False).head(25),
                     use_container_width=True, hide_index=True)
        st.caption("Cuadrante superior-derecho = expansion con tecnologia (virtuoso). "
                   "Derecha-abajo = extensivo puro. Arriba-izquierda = intensificacion sin "
                   "expandir area. Abajo-izquierda = colapso. Tamano de burbuja = volumen total.")
'''
if old in c:
    c = c.replace(old, new, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] 4.14 agregada: scatter de cuadrantes + tabla de descomposicion")
else:
    print("[AVISO] No encontre el bloque de elasticidad; revisa manualmente")

print("Reinicia Streamlit y revisa Descriptivo -> Crecimiento")