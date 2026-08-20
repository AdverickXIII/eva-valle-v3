"""Descomposicion del crecimiento: CAGR produccion = CAGR area + CAGR rendimiento."""
import pandas as pd
import plotly.express as px

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
                     hover_data=["cagr_prod"], color_discrete_map=COLORES,
                     labels={"cagr_area": "CAGR area sembrada (%)",
                             "cagr_rend": "CAGR rendimiento (%)",
                             "tipo": "Tipo de crecimiento"})
    fig.add_hline(y=0, line_color="gray", line_dash="dash")
    fig.add_vline(x=0, line_color="gray", line_dash="dash")
    fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=560)
    return apply_theme(fig, "Motor del crecimiento: area vs rendimiento por cultivo")


def plot_motor_barras(df_dec, top_n: int = 12):
    """Barras agrupadas: CAGR produccion vs area vs rendimiento (Top por volumen)."""
    import plotly.graph_objects as go
    d = df_dec.sort_values("prod_total", ascending=False).head(top_n)
    d = d.sort_values("cagr_prod", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="CAGR produccion", x=d["cultivo"], y=d["cagr_prod"],
                         marker_color="#2E8B57"))
    fig.add_trace(go.Bar(name="CAGR area sembrada", x=d["cultivo"], y=d["cagr_area"],
                         marker_color="#F4A261"))
    fig.add_trace(go.Bar(name="CAGR rendimiento", x=d["cultivo"], y=d["cagr_rend"],
                         marker_color="#5FA8DC"))
    fig.update_layout(barmode="group", height=520, xaxis_tickangle=-45,
                      yaxis_title="CAGR (%)", legend=dict(orientation="h", y=-0.22),
                      margin=dict(t=40, b=10))
    return apply_theme(fig, "Motor del crecimiento: produccion vs area vs rendimiento")
