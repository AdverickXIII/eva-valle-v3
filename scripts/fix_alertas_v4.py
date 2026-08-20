"""Alertas v4: mensaje honesto por volumen, regla marginal y radar siempre visible."""
from pathlib import Path

# ---------- 1) Motor: agricultura marginal en declive ----------
pe = Path("core/analytics/alerts.py")
ce = pe.read_text(encoding="utf-8")

REGLA_MARGINAL = '''    # 8) Agricultura marginal en declive (municipios pequenos que caen)
    gm2 = df.groupby(["municipio", "ano"])["produccion_t"].sum().reset_index()
    for m, sub in gm2.groupby("municipio"):
        sub = sub.sort_values("ano")
        prod_tot = float(sub["produccion_t"].sum())
        if prod_tot >= 5000 or len(sub) < 2:
            continue
        ini = float(sub["produccion_t"].iloc[0])
        fin = float(sub["produccion_t"].iloc[-1])
        if ini > 0 and fin > 0:
            n = len(sub) - 1
            cagr_m = ((fin / ini) ** (1 / n) - 1) * 100
            if cagr_m <= -5:
                alerts.append(dict(severidad="AVISO", tipo="Marginal",
                                   municipio=m, cultivo="-",
                                   titulo=f"{m}: agricultura marginal en declive",
                                   detalle=f"{prod_tot:,.0f} t totales con CAGR "
                                           f"{cagr_m:.1f}%. Economia agricola minima "
                                           f"y en contraccion."))

'''

ancla = '    orden = {"ALERTA": 0, "AVISO": 1, "DESTAQUE": 2}'
if "agricultura marginal en declive" not in ce and ancla in ce:
    ce = ce.replace(ancla, REGLA_MARGINAL + ancla, 1)
    pe.write_text(ce, encoding="utf-8")
    print("[OK] Regla marginal agregada al motor")
else:
    print("[INFO] Motor ya tenia la regla marginal")

# ---------- 2) Pagina: mensaje por volumen + radar contextual ----------
pp = Path("ui/pages/12_Alertas.py")
cp = pp.read_text(encoding="utf-8")

old_msg = '''    if mun_sel != "Todos":
        n_mun = len(df_f[df_f["municipio"] == mun_sel])
        if n_mun == 0:
            st.success(f"✅ **{mun_sel}** no tiene alertas activas con los filtros "
                       f"actuales: la ausencia de alertas tambien es una senal "
                       f"(municipio sin riesgos detectados).")'''

new_msg = '''    if mun_sel != "Todos":
        n_mun = len(df_f[df_f["municipio"] == mun_sel])
        if n_mun == 0:
            prod_mun = float(df[df["municipio"] == mun_sel]["produccion_t"].sum())
            tot_dept = float(df["produccion_t"].sum()) or 1.0
            if prod_mun >= 5000:
                st.success(f"✅ **{mun_sel}** no tiene alertas activas con los filtros "
                           f"actuales: municipio con volumen significativo "
                           f"({prod_mun:,.0f} t) y sin riesgos detectados.")
            else:
                st.info(f"ℹ️ **{mun_sel}** registra {prod_mun:,.0f} t "
                        f"({prod_mun / tot_dept * 100:.2f}% del departamento), por "
                        f"debajo del umbral de analisis (5,000 t). La ausencia de "
                        f"alertas NO indica buen desempeno: refleja una economia "
                        f"agricola marginal.")'''

if old_msg in cp:
    cp = cp.replace(old_msg, new_msg, 1)
    print("[OK] Mensaje de tres estados (alertas / sano / marginal)")
else:
    print("[AVISO] Bloque de mensaje distinto; revisa manualmente")

old_radar = '''    # ---------- RADAR: municipios con mas alertas (apilado por severidad) ----------
    d_rad = df_f[df_f["municipio"] != "-"]
    if not d_rad.empty:
        counts = (d_rad.groupby(["municipio", "severidad"]).size()
                  .unstack(fill_value=0))
        counts["total"] = counts.sum(axis=1)
        counts = counts.sort_values("total").tail(12)
        fig = go.Figure()
        for sev, col in (("ALERTA", "#D62728"), ("AVISO", "#F4A261"),
                         ("DESTAQUE", "#2E8B57")):
            if sev in counts.columns:
                fig.add_trace(go.Bar(y=counts.index, x=counts[sev], name=sev,
                                     orientation="h", marker_color=col))
        fig.update_layout(barmode="stack", height=460,
                          xaxis_title="Numero de alertas",
                          legend=dict(orientation="h", y=-0.15),
                          margin=dict(t=50, b=10, l=10, r=10),
                          title="Radar territorial: municipios con mas alertas (por severidad)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Longitud de la barra = total de alertas del municipio; "
                   "colores = severidad (rojo alerta, amarillo aviso, verde destacado).")
    else:
        st.info("Sin alertas municipales con los filtros actuales "
                "(las departamentales aparecen abajo).")'''

new_radar = '''    # ---------- RADAR siempre visible (contexto severidad/tipo) ----------
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

if old_radar in cp:
    cp = cp.replace(old_radar, new_radar, 1)
    pp.write_text(cp, encoding="utf-8")
    print("[OK] Radar siempre visible con contexto departamental")
else:
    pp.write_text(cp, encoding="utf-8")
    print("[AVISO] Bloque de radar distinto; revisa manualmente")

print("Reinicia Streamlit y prueba Buenaventura y Sevilla")