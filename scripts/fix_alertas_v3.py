"""Alertas v3: regla cultivo-municipio, selector completo y radar legible."""
from pathlib import Path

# ---------- 1) Motor: ventaja competitiva cultivo-municipio ----------
pe = Path("core/analytics/alerts.py")
ce = pe.read_text(encoding="utf-8")

NUEVA_REGLA = '''    # 7) Ventaja competitiva cultivo-municipio (rendimiento vs promedio del cultivo)
    gmc = (df.groupby(["municipio", "cultivo"])
           .agg(p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum"))
           .reset_index())
    gmc["rend"] = gmc["p"] / gmc["c"].replace(0, 1)
    gc = (df.groupby("cultivo")
          .agg(p=("produccion_t", "sum"), c=("area_cosechada_ha", "sum"))
          .reset_index())
    gc["rend_d"] = gc["p"] / gc["c"].replace(0, 1)
    mg = gmc.merge(gc[["cultivo", "rend_d"]], on="cultivo")
    for _, r in mg.iterrows():
        if r["p"] >= 20000 and r["rend_d"] > 0 and r["rend"] >= 1.5 * r["rend_d"]:
            alerts.append(dict(severidad="DESTAQUE", tipo="Competitividad",
                               municipio=r["municipio"], cultivo=r["cultivo"],
                               titulo=f"{r['municipio']}: ventaja competitiva en {r['cultivo']}",
                               detalle=f"Rendimiento {r['rend']:.1f} t/ha vs "
                                       f"{r['rend_d']:.1f} t/ha del cultivo "
                                       f"({r['rend']/r['rend_d']:.1f}x)."))

'''

ancla_motor = '    orden = {"ALERTA": 0, "AVISO": 1, "DESTAQUE": 2}'
if "ventaja competitiva en" not in ce and ancla_motor in ce:
    ce = ce.replace(ancla_motor, NUEVA_REGLA + ancla_motor, 1)
    pe.write_text(ce, encoding="utf-8")
    print("[OK] Regla cultivo-municipio agregada (Sevilla/platanos entrara)")
else:
    print("[INFO] Motor ya tenia la regla")

# ---------- 2) Pagina: selector completo + mensaje sin alertas + radar legible ----------
pp = Path("ui/pages/12_Alertas.py")
cp = pp.read_text(encoding="utf-8")

old_sel = '        munis_con = sorted(set(df_a["municipio"]) - {"-"})'
new_sel = '        munis_con = sorted(df["municipio"].dropna().unique().tolist())'
if old_sel in cp:
    cp = cp.replace(old_sel, new_sel, 1)
    print("[OK] Selector con TODOS los municipios")

old_cap = '    st.caption(f"{len(df_f)} alertas tras filtros.")'
new_cap = old_cap + '''

    if mun_sel != "Todos":
        n_mun = len(df_f[df_f["municipio"] == mun_sel])
        if n_mun == 0:
            st.success(f"✅ **{mun_sel}** no tiene alertas activas con los filtros "
                       f"actuales: la ausencia de alertas tambien es una senal "
                       f"(municipio sin riesgos detectados).")'''
if old_cap in cp:
    cp = cp.replace(old_cap, new_cap, 1)
    print("[OK] Mensaje positivo para municipios sin alertas")

old_radar = '''    # ---------- RADAR municipio x tipo ----------
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
                "(las departamentales aparecen abajo).")'''

new_radar = '''    # ---------- RADAR: municipios con mas alertas (apilado por severidad) ----------
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

if old_radar in cp:
    cp = cp.replace(old_radar, new_radar, 1)
    pp.write_text(cp, encoding="utf-8")
    print("[OK] Radar reemplazado por barras apiladas por severidad")
else:
    pp.write_text(cp, encoding="utf-8")
    print("[AVISO] Bloque de radar distinto; revisa manualmente")

print("Reinicia Streamlit y prueba: selecciona Sevilla")