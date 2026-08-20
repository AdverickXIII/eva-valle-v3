"""Alertas v5: reemplaza el radar por Indice de Riesgo Territorial (0-100)."""
from pathlib import Path

# ---------- 1) Motor: indice de riesgo ----------
pe = Path("core/analytics/alerts.py")
ce = pe.read_text(encoding="utf-8")

INDICE = '''

def indice_riesgo_municipal(df: pd.DataFrame) -> pd.DataFrame:
    """Indice compuesto 0-100 de riesgo territorial por municipio."""
    def _cl(x: float) -> float:
        return max(0.0, min(100.0, x))

    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    filas = []
    for m, sub in df.groupby("municipio"):
        g = sub.groupby("cultivo")["produccion_t"].sum()
        g = g[g > 0]
        prod = float(g.sum())
        if prod <= 0:
            continue
        p = g / g.sum()
        shannon = float(-(p * np.log(p)).sum())
        top_share = float(g.max() / g.sum() * 100)
        an = sub.groupby("ano")["produccion_t"].sum().sort_index()
        cagr = 0.0
        if len(an) >= 2 and an.iloc[0] > 0 and an.iloc[-1] > 0:
            cagr = ((an.iloc[-1] / an.iloc[0]) ** (1 / (len(an) - 1)) - 1) * 100
        caida = 0.0
        if len(anos) >= 2:
            va = an.reindex([anos[-2], anos[-1]]).dropna()
            if len(va) == 2 and va.iloc[0] > 0:
                caida = (va.iloc[1] / va.iloc[0] - 1) * 100
        dep = _cl(top_share)
        div = _cl(100 - shannon * 40)
        dec = _cl(50 - cagr * 5)
        cai = _cl(50 - caida * 2.5)
        filas.append({"municipio": m,
                      "score": round((dep + div + dec + cai) / 4, 1),
                      "dependencia": round(dep, 1),
                      "baja_diversidad": round(div, 1),
                      "declive": round(dec, 1),
                      "caida": round(cai, 1),
                      "produccion_t": prod})
    return (pd.DataFrame(filas)
            .sort_values("score", ascending=False)
            .reset_index(drop=True))
'''

if "def indice_riesgo_municipal" not in ce:
    ce += INDICE
    pe.write_text(ce, encoding="utf-8")
    print("[OK] indice_riesgo_municipal agregado al motor")

# ---------- 2) Pagina: swap radar -> indice ----------
pp = Path("ui/pages/12_Alertas.py")
cp = pp.read_text(encoding="utf-8")

cp = cp.replace("from core.analytics.alerts import generate_alerts",
                "from core.analytics.alerts import (generate_alerts, indice_riesgo_municipal)")

old_radar = '''    # ---------- RADAR siempre visible (contexto severidad/tipo) ----------
    df_rad = df_a[df_a["severidad"].isin(sev_sel) & df_a["tipo"].isin(tip_sel)]
    d_rad = df_rad[df_rad["municipio"] != "-"]
    if not d_rad.empty:
        counts = (d_rad.groupby(["municipio", "severidad"]).size()
                  .unstack(fill_value=0))
        counts["total"] = counts.sum(axis=1)
        top = counts.sort_values("total").tail(12)
        if mun_sel != "Todos" and mun_sel in counts.index and mun_sel not in top.index:
            top = pd.concat([top, counts.loc[[mun_sel]]])
        fig = go.Figure()
        for sev, col in (("ALERTA", "#D62728"), ("AVISO", "#F4A261"),
                         ("DESTAQUE", "#2E8B57")):
            if sev in top.columns:
                fig.add_trace(go.Bar(y=top.index, x=top[sev], name=sev,
                                     orientation="h", marker_color=col))
        fig.update_layout(barmode="stack", height=480,
                          xaxis_title="Numero de alertas",
                          legend=dict(orientation="h", y=-0.15),
                          margin=dict(t=50, b=10, l=10, r=10),
                          title="Radar territorial: municipios con mas alertas (por severidad)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("El radar ignora el filtro de municipio para dar contexto "
                   "departamental; el municipio seleccionado se incluye si aparece.")
    else:
        st.info("Sin alertas municipales con los filtros de severidad/tipo.")'''

new_indice = '''    # ---------- INDICE DE RIESGO TERRITORIAL (estructural, sin filtros) ----------
    st.markdown("#### 🗺️ Indice de Riesgo Territorial (Top 15)")
    df_ir = indice_riesgo_municipal(df).head(15)
    fig = go.Figure(go.Bar(
        y=df_ir["municipio"], x=df_ir["score"], orientation="h",
        marker=dict(color=df_ir["score"], colorscale="RdYlGn_r",
                    colorbar=dict(title="Riesgo")),
        customdata=df_ir[["dependencia", "baja_diversidad", "declive", "caida"]].values,
        hovertemplate="%{y}: %{x:.0f}/100<br>Dependencia %{customdata[0]:.0f} · "
                      "Baja diversidad %{customdata[1]:.0f} · "
                      "Declive %{customdata[2]:.0f} · Caida %{customdata[3]:.0f}<extra></extra>"))
    fig.update_layout(height=520, xaxis=dict(range=[0, 100],
                      title="Riesgo (0-100)"), margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Indice compuesto = dependencia de un cultivo + baja diversidad + "
               "declive sostenido + caida reciente. Es contexto estructural: "
               "no cambia con los filtros de alertas.")'''

if old_radar in cp:
    cp = cp.replace(old_radar, new_indice, 1)
    pp.write_text(cp, encoding="utf-8")
    print("[OK] Radar reemplazado por Indice de Riesgo Territorial")
else:
    pp.write_text(cp, encoding="utf-8")
    print("[AVISO] Bloque de radar distinto; revisa manualmente")

print("Reinicia Streamlit y revisa Alertas")