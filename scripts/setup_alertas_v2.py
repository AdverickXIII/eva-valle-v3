"""Centro de Alertas v2: motor multi-indicador + filtros + radar + tabla + CSV."""
from pathlib import Path

ENGINE = '''"""Generacion de alertas inteligentes v2: motor multi-indicador."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _concentracion(df: pd.DataFrame):
    g = df.groupby("cultivo")["produccion_t"].sum().sort_values(ascending=True)
    shares = g / g.sum() * 100
    hhi = float((shares ** 2).sum())
    top1 = float(g.iloc[-1] / g.sum() * 100)
    return hhi, top1


def _cagr_por_cultivo(df: pd.DataFrame, min_prod: float = 1000.0) -> pd.DataFrame:
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) < 2:
        return pd.DataFrame()
    ini_y, fin_y = int(min(anos)), int(max(anos))
    n = fin_y - ini_y
    agg = df.groupby(["ano", "cultivo"]).agg(
        p=("produccion_t", "sum"), a=("area_sembrada_ha", "sum"),
        c=("area_cosechada_ha", "sum")).reset_index()
    ini = agg[agg["ano"] == ini_y].set_index("cultivo")
    fin = agg[agg["ano"] == fin_y].set_index("cultivo")
    d = pd.DataFrame({"ini": ini["p"], "fin": fin["p"],
                      "a_ini": ini["a"], "a_fin": fin["a"],
                      "c_ini": ini["c"], "c_fin": fin["c"]}).dropna()
    d = d[d["ini"] >= min_prod]
    if d.empty:
        return d.reset_index()
    d["cagr"] = ((d["fin"] / d["ini"]) ** (1 / n) - 1) * 100
    d["cagr_area"] = ((d["a_fin"] / d["a_ini"]) ** (1 / n) - 1) * 100
    rend_ini = d["ini"] / d["c_ini"].replace(0, np.nan)
    rend_fin = d["fin"] / d["c_fin"].replace(0, np.nan)
    d["cagr_rend"] = ((rend_fin / rend_ini) ** (1 / n) - 1) * 100
    return d.reset_index()


def _shannon_municipios(df: pd.DataFrame) -> pd.DataFrame:
    out = {}
    for m, sub in df.groupby("municipio"):
        g = sub.groupby("cultivo")["produccion_t"].sum()
        g = g[g > 0]
        if g.sum() <= 0:
            continue
        p = g / g.sum()
        out[m] = {"shannon": float(-(p * np.log(p)).sum()),
                  "top_share": float(g.max() / g.sum() * 100),
                  "top_cultivo": g.idxmax(),
                  "prod": float(g.sum())}
    return pd.DataFrame(out).T


def generate_alerts(df: pd.DataFrame) -> list:
    """Lista de alertas con severidad, tipo, municipio y cultivo."""
    alerts = []

    # 1) Concentracion departamental
    hhi, top1 = _concentracion(df)
    if hhi > 2500:
        alerts.append(dict(severidad="ALERTA", tipo="Concentracion",
                           municipio="-", cultivo="-",
                           titulo="Concentracion extrema de produccion",
                           detalle=f"HHI={hhi:,.0f} (>2,500). El cultivo lider aporta "
                                   f"{top1:.1f}% de la produccion departamental. "
                                   f"Riesgo por monocultivo."))

    # 2) CAGR por cultivo: colapso / declive / oportunidad / motor extensivo
    for _, r in _cagr_por_cultivo(df).iterrows():
        if r["cagr"] <= -5:
            alerts.append(dict(severidad="ALERTA", tipo="Crecimiento",
                               municipio="-", cultivo=r["cultivo"],
                               titulo=f"{r['cultivo']}: declive sostenido",
                               detalle=f"CAGR {r['cagr']:.1f}% en el periodo. "
                                       f"Revisar competitividad."))
        elif r["cagr"] < 0:
            alerts.append(dict(severidad="AVISO", tipo="Crecimiento",
                               municipio="-", cultivo=r["cultivo"],
                               titulo=f"{r['cultivo']}: tendencia a la baja",
                               detalle=f"CAGR {r['cagr']:.1f}%. Vigilar evolucion."))
        elif r["cagr"] >= 15:
            alerts.append(dict(severidad="DESTAQUE", tipo="Crecimiento",
                               municipio="-", cultivo=r["cultivo"],
                               titulo=f"{r['cultivo']}: oportunidad de crecimiento",
                               detalle=f"CAGR +{r['cagr']:.1f}%. Candidato a "
                                       f"incentivo/inversion."))
        if r["cagr"] > 5 and r.get("cagr_rend", 0) < -2:
            alerts.append(dict(severidad="AVISO", tipo="Motor",
                               municipio="-", cultivo=r["cultivo"],
                               titulo=f"{r['cultivo']}: expansion sin productividad",
                               detalle=f"Produccion +{r['cagr']:.1f}% pero rendimiento "
                                       f"{r['cagr_rend']:.1f}%. Crecimiento extensivo "
                                       f"vulnerable."))

    # 3) Caidas municipales entre los dos ultimos anos
    anos = sorted(df["ano"].dropna().unique())
    if len(anos) >= 2:
        a, b = int(anos[-2]), int(anos[-1])
        pa = df[df["ano"] == a].groupby("municipio")["produccion_t"].sum()
        pb = df[df["ano"] == b].groupby("municipio")["produccion_t"].sum()
        for m in pa.index:
            if m in pb.index and pa[m] > 0:
                var = (pb[m] / pa[m] - 1) * 100
                if var <= -20:
                    alerts.append(dict(severidad="AVISO", tipo="Caida anual",
                                       municipio=m, cultivo="-",
                                       titulo=f"{m}: caida de produccion",
                                       detalle=f"{var:.1f}% entre {a} y {b}."))

    # 4) Dependencia extrema y baja diversidad municipal
    sm = _shannon_municipios(df)
    for m, r in sm.iterrows():
        if r["prod"] >= 5000 and r["top_share"] >= 90:
            alerts.append(dict(severidad="AVISO", tipo="Dependencia",
                               municipio=m, cultivo=r["top_cultivo"],
                               titulo=f"{m}: dependencia extrema de {r['top_cultivo']}",
                               detalle=f"{r['top_share']:.1f}% de su produccion en un "
                                       f"solo cultivo."))
        if r["prod"] >= 5000 and r["shannon"] < 1.0:
            alerts.append(dict(severidad="AVISO", tipo="Diversidad",
                               municipio=m, cultivo="-",
                               titulo=f"{m}: baja diversidad productiva",
                               detalle=f"Shannon {r['shannon']:.2f} (<1.0). Canasta "
                                       f"concentrada."))

    # 5) Competitividad: rendimiento muy superior al departamento
    tot_p = df["produccion_t"].sum()
    tot_c = df["area_cosechada_ha"].sum()
    rend_dpto = tot_p / tot_c if tot_c else 0
    gm = (df.groupby("municipio")
          .agg(p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum"))
          .reset_index())
    gm["rend"] = gm["p"] / gm["c"].replace(0, 1)
    for _, r in gm.iterrows():
        if r["p"] >= 50000 and rend_dpto and r["rend"] >= 1.5 * rend_dpto:
            alerts.append(dict(severidad="DESTAQUE", tipo="Competitividad",
                               municipio=r["municipio"], cultivo="-",
                               titulo=f"{r['municipio']}: rendimiento superior",
                               detalle=f"{r['rend']:.1f} t/ha vs {rend_dpto:.1f} t/ha "
                                       f"del departamento ({r['rend']/rend_dpto:.1f}x). "
                                       f"Ventaja competitiva."))

    # 6) Calidad de datos: outliers
    try:
        from core.analytics.outliers import detect_multivariate_outliers
        df_out = detect_multivariate_outliers(df)
        if df_out is not None and len(df_out):
            alerts.append(dict(severidad="AVISO", tipo="Calidad de datos",
                               municipio="-", cultivo="-",
                               titulo="Registros atipicos detectados",
                               detalle=f"{len(df_out)} registros "
                                       f"({len(df_out)/len(df)*100:.1f}%) marcados por "
                                       f"Isolation Forest. Revisar antes de reportar."))
    except Exception:
        pass

    orden = {"ALERTA": 0, "AVISO": 1, "DESTAQUE": 2}
    alerts.sort(key=lambda x: orden[x["severidad"]])
    return alerts
'''

PAGE = '''"""Pagina 12: Centro de Alertas (filtros, radar, tabla y exportacion)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings
from core.analytics.alerts import generate_alerts
from ui.components.loading_states import render_empty_state

st.set_page_config(page_title="Alertas | EVA Valle", page_icon="🚨", layout="wide")


@st.cache_data(ttl=3600)
def load_dataset() -> pd.DataFrame:
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@st.cache_data(ttl=3600)
def get_alerts(df: pd.DataFrame) -> list:
    return generate_alerts(df)


def main() -> None:
    st.title("🚨 Centro de Alertas")
    st.caption("Monitoreo automatico: riesgos, dependencias y oportunidades del agro vallecaucano")

    df = load_dataset()
    if df.empty:
        render_empty_state("Dataset no encontrado",
            hint="Ejecuta: python scripts/run_pipeline.py --skip-download")
        return

    alerts = get_alerts(df)
    df_a = pd.DataFrame(alerts)

    n_a = sum(1 for x in alerts if x["severidad"] == "ALERTA")
    n_v = sum(1 for x in alerts if x["severidad"] == "AVISO")
    n_d = sum(1 for x in alerts if x["severidad"] == "DESTAQUE")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚨 Total", len(alerts))
    k2.metric("🔴 Alertas", n_a)
    k3.metric("🟡 Avisos", n_v)
    k4.metric("🟢 Destacados", n_d)
    st.markdown("---")

    # ---------- FILTROS ----------
    f1, f2, f3 = st.columns(3)
    with f1:
        sev_sel = st.multiselect("Severidad",
                                 ["ALERTA", "AVISO", "DESTAQUE"],
                                 default=["ALERTA", "AVISO", "DESTAQUE"])
    with f2:
        tip_sel = st.multiselect("Tipo de alerta",
                                 sorted(df_a["tipo"].unique().tolist()),
                                 default=sorted(df_a["tipo"].unique().tolist()))
    with f3:
        munis_con = sorted(set(df_a["municipio"]) - {"-"})
        mun_sel = st.selectbox("Municipio", ["Todos"] + munis_con)

    df_f = df_a[df_a["severidad"].isin(sev_sel) & df_a["tipo"].isin(tip_sel)]
    if mun_sel != "Todos":
        df_f = df_f[(df_f["municipio"] == mun_sel) | (df_f["municipio"] == "-")]

    st.caption(f"{len(df_f)} alertas tras filtros.")

    # ---------- RADAR municipio x tipo ----------
    d_rad = df_f[df_f["municipio"] != "-"]
    if not d_rad.empty:
        piv = (d_rad.pivot_table(index="municipio", columns="tipo",
                                 values="titulo", aggfunc="size", fill_value=0))
        fig = go.Figure(go.Heatmap(
            z=piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
            colorscale="YlOrRd", xgap=2, ygap=2,
            hovertemplate="%{y} · %{x}: %{z} alerta(s)<extra></extra>",
            colorbar=dict(title="Alertas")))
        fig.update_layout(height=420, margin=dict(t=40, b=10, l=10, r=10),
                          title="Radar territorial: donde se acumulan las alertas")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin alertas municipales con los filtros actuales "
                "(las departamentales aparecen abajo).")

    # ---------- TABLA + CSV ----------
    st.subheader("📋 Detalle de alertas")
    show = df_f[["severidad", "tipo", "municipio", "cultivo", "titulo", "detalle"]]
    st.dataframe(show, use_container_width=True, height=380, hide_index=True)
    st.download_button("⬇️ Descargar alertas (CSV)",
                       data=show.to_csv(index=False).encode("utf-8"),
                       file_name="alertas_eva_valle.csv", mime="text/csv")

    st.markdown("---")

    # ---------- TARJETAS ----------
    st.subheader("🔔 Narrativa de alertas")
    for _, x in df_f.iterrows():
        msg = f"**{x['titulo']}**\\n\\n{x['detalle']}"
        if x["severidad"] == "ALERTA":
            st.error(msg)
        elif x["severidad"] == "AVISO":
            st.warning(msg)
        else:
            st.success(msg)


main()
'''

Path("core/analytics/alerts.py").write_text(ENGINE, encoding="utf-8")
Path("ui/pages/12_Alertas.py").write_text(PAGE, encoding="utf-8")
print("[OK] core/analytics/alerts.py v2 (7 familias de reglas)")
print("[OK] ui/pages/12_Alertas.py v2 (filtros + radar + tabla + CSV)")
print("Reinicia Streamlit y abre Alertas")