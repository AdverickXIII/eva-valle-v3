"""Reporte municipal: proyeccion con seleccion automatica de modelo (motor v2)."""
from pathlib import Path

p = Path("core/reports/pdf_report.py")
c = p.read_text(encoding="utf-8")

# 1) Import del motor v2
old_imp = "from core.reports import meta"
new_imp = "from core.analytics.forecast import proyectar_con_ic\nfrom core.reports import meta"
if "proyectar_con_ic" not in c:
    c = c.replace(old_imp, new_imp, 1)
    print("[OK] Import del motor v2 agregado")

# 2) Seccion 4: proyeccion con backtesting + escenarios
old_sec = '''    # 4. Proyeccion grafica
    f = forecast_municipality(df_m)
    if f:
        fy = f["forecast_years"][0]
        fv = f["forecast_values"][0]
        last_v = f["values"][-1]
        var = (fv / last_v - 1) * 100 if last_v else 0.0
        story.append(Paragraph(f"4. Proyeccion de produccion {fy}",
                               st_["Heading2"]))
        story.append(_production_chart(f))
        story.append(Paragraph(
            "<font color='#2E8B57'>Verde</font> = historico | "
            "<font color='#DD6B20'>Naranja</font> = proyeccion tendencial",
            st_["Italic"]))
        story.append(Spacer(1, 0.2 * cm))
        signo = "+" if var >= 0 else ""
        story.append(Paragraph(
            f"Produccion proyectada {fy}: <b>{fv:,.0f} t</b> "
            f"({signo}{var:.1f}% vs {f['years'][-1]}).", st_["Normal"]))
        story.append(Spacer(1, 0.4 * cm))'''

new_sec = '''    # 4. Proyeccion con seleccion automatica de modelo (motor v2)
    nota_proy = "Proyeccion basada en tendencia lineal historica."
    serie = pd.Series({int(r["ano"]): float(r["produccion"])
                       for _, r in yearly(df_m).iterrows()}).sort_index()
    res_fc = proyectar_con_ic(serie, n_steps=3) if len(serie) >= 4 else {}
    if res_fc.get("modelo") is not None:
        ultimo = int(serie.index[-1])
        ultimo_v = float(serie.iloc[-1])
        anos_fut = list(range(ultimo + 1, ultimo + 4))
        f = {"years": [int(y) for y in serie.index],
             "values": [float(v) for v in serie.values],
             "forecast_years": anos_fut,
             "forecast_values": [float(v)
                                 for v in res_fc["escenarios"]["tendencial"]]}
        fy = anos_fut[0]
        fv = float(res_fc["escenarios"]["tendencial"][0])
        var = (fv / ultimo_v - 1) * 100 if ultimo_v else 0.0
        mape = float(res_fc["mape"])
        nivel = "alta" if mape < 10 else ("moderada" if mape < 20 else "baja")
        nota_proy = ("Proyeccion con seleccion automatica de modelo por "
                     "backtesting (MAPE).")
        story.append(Paragraph(f"4. Proyeccion de produccion {fy}-{anos_fut[-1]}",
                               st_["Heading2"]))
        story.append(_production_chart(f))
        story.append(Paragraph(
            "<font color='#2E8B57'>Verde</font> = historico | "
            "<font color='#DD6B20'>Naranja</font> = proyeccion (modelo ganador)",
            st_["Italic"]))
        story.append(Spacer(1, 0.2 * cm))
        signo = "+" if var >= 0 else ""
        story.append(Paragraph(
            f"Produccion proyectada {fy}: <b>{fv:,.0f} t</b> "
            f"({signo}{var:.1f}% vs {ultimo}). Modelo: <b>{res_fc['ganador']}</b> | "
            f"MAPE backtest: <b>{mape:.1f}%</b> | Credibilidad: <b>{nivel}</b>.",
            st_["Normal"]))
        rows = [["Ano", "Conservador (P10)", "Tendencial", "Optimista (P90)"]]
        for i, an in enumerate(anos_fut):
            rows.append([str(an),
                         f"{float(res_fc['escenarios']['conservador'][i]):,.0f}",
                         f"{float(res_fc['escenarios']['tendencial'][i]):,.0f}",
                         f"{float(res_fc['escenarios']['optimista'][i]):,.0f}"])
        t4 = Table(rows, hAlign="LEFT")
        t4.setStyle(_style())
        story += [Spacer(1, 0.2 * cm), t4, Spacer(1, 0.4 * cm)]
    else:
        f = forecast_municipality(df_m)
        if f:
            fy = f["forecast_years"][0]
            fv = f["forecast_values"][0]
            last_v = f["values"][-1]
            var = (fv / last_v - 1) * 100 if last_v else 0.0
            story.append(Paragraph(f"4. Proyeccion de produccion {fy}",
                                   st_["Heading2"]))
            story.append(_production_chart(f))
            story.append(Paragraph(
                "<font color='#2E8B57'>Verde</font> = historico | "
                "<font color='#DD6B20'>Naranja</font> = proyeccion tendencial",
                st_["Italic"]))
            story.append(Spacer(1, 0.2 * cm))
            signo = "+" if var >= 0 else ""
            story.append(Paragraph(
                f"Produccion proyectada {fy}: <b>{fv:,.0f} t</b> "
                f"({signo}{var:.1f}% vs {f['years'][-1]}).", st_["Normal"]))
            story.append(Spacer(1, 0.4 * cm))'''

if old_sec in c:
    c = c.replace(old_sec, new_sec, 1)
    print("[OK] Seccion 4 con modelo ganador + MAPE + escenarios")
else:
    print("[AVISO] Seccion 4 distinta; revisa manualmente")

# 3) Pie de pagina dinamico
old_pie = '''    story.append(Paragraph(
        f"Fuente: {meta.FUENTE}. Proyeccion basada en tendencia lineal historica. "
        f"{meta.firma()}.", st_["Italic"]))'''
new_pie = '''    story.append(Paragraph(
        f"Fuente: {meta.FUENTE}. {nota_proy} {meta.firma()}.", st_["Italic"]))'''
if old_pie in c:
    c = c.replace(old_pie, new_pie, 1)
    p.write_text(c, encoding="utf-8")
    print("[OK] Pie de pagina dinamico (metodologia real)")
else:
    p.write_text(c, encoding="utf-8")
    print("[AVISO] Pie distinto; revisa manualmente")

print("Reinicia Streamlit y descarga de nuevo el reporte de Andalucia")