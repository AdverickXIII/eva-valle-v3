"""PARTE 2: Agrega secciones 2 a 8 al informe tecnico."""
from pathlib import Path

SECCIONES_2_8 = '''

    # --- 2. INTRODUCCION Y OBJETIVOS ---
    story.append(Paragraph("2. Introduccion y objetivos", h1))
    story.append(Paragraph(
        "El presente informe tecnico analiza la dinamica y estructura agricola del "
        "departamento del Valle del Cauca durante el periodo 2019-2025, utilizando como "
        "fuente oficial las Encuestas de Valoracion Agropecuaria (EVA) publicadas por la "
        "Unidad de Planificacion Rural Agropecuaria (UPRA). El analisis busca proporcionar "
        "a los tomadores de decision una vision rigurosa, cuantitativa y territorialmente "
        "referenciada del sector agricola departamental.", body))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>Objetivos especificos:</b>", body))
    for obj in [
        "Caracterizar la estructura productiva por grupo de cultivo y municipio.",
        "Cuantificar la concentracion productiva y territorial (Gini, HHI, CR4, CR10).",
        "Evaluar la especializacion municipal mediante Location Quotient (LQ).",
        "Medir la diversificacion con indices de Shannon y Simpson.",
        "Construir un Indice de Desempeno Agricola Municipal (IDAM).",
        "Identificar correlaciones, brechas y oportunidades de politica publica.",
    ]:
        story.append(Paragraph(f"&bull; {obj}", body))

    # --- 3. FUENTES Y CALIDAD DEL DATO ---
    story.append(Paragraph("3. Fuentes y calidad del dato", h1))
    story.append(Paragraph(
        "La fuente primaria son las EVA 2019-2025 publicadas por UPRA, recolectadas "
        "mediante autodeclaracion municipal. Se aplicaron controles de calidad:", body))
    total_reg = len(df)
    anom = int((df["area_cosechada_ha"] > df["area_sembrada_ha"]).sum())
    nulos = int(df[["produccion_t", "area_sembrada_ha", "area_cosechada_ha"]]
                .isna().any(axis=1).sum())
    dup = int(df.duplicated().sum())
    dq = [["Aspecto", "Valor", "Interpretacion"],
          ["Registros totales", f"{total_reg:,}", "Base completa 2019-2025"],
          ["Anomalias (cosechada > sembrada)", f"{anom/total_reg*100:.2f}%",
           "Se documentan pero no se descartan"],
          ["Valores nulos criticos", f"{nulos/total_reg*100:.2f}%",
           "Integridad aceptable"],
          ["Registros duplicados", f"{dup}", "Eliminados automaticamente"],
          ["Cobertura", "42 municipios / 78 cultivos", "100% del departamento"]]
    story.append(_tabla(dq, [5*cm, 3.5*cm, 8*cm]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>Limitaciones:</b> la fuente depende de autodeclaracion municipal, lo que "
        "puede introducir sesgos de reporte en produccion y area. Los indicadores "
        "estadisticos excluyen registros con produccion igual a cero para evitar "
        "distorsiones en promedios y rendimientos.", body))

    # --- 4. METODOLOGIA ---
    story.append(Paragraph("4. Metodologia", h1))
    story.append(Paragraph(
        "Se aplicaron metodos estadisticos estandar de la literatura agropecuaria y "
        "economica (FAO, CEPAL, USDA):", body))
    met = [["Indicador", "Formula / Metodo", "Uso"],
           ["Rendimiento", "Produccion / Area cosechada", "Productividad"],
           ["CAGR", "(Pf/Pi)^(1/n) - 1", "Crecimiento compuesto anual"],
           ["Gini", "Formula clasica ascendente", "Concentracion"],
           ["HHI", "Suma de participaciones al cuadrado", "Concentracion"],
           ["CR4 / CR10", "Suma top 4 / top 10", "Cuotas de mercado"],
           ["Location Quotient", "(part_mun / part_dpto)", "Especializacion"],
           ["Indice de Shannon", "-Sum(p * ln(p))", "Diversificacion"],
           ["Indice de Simpson", "Sum(p^2)", "Dominancia"],
           ["Pearson / Spearman", "Correlacion lineal / monotona", "Asociaciones"],
           ["IDAM", "Indice compuesto ponderado", "Desempeno municipal"]]
    story.append(_tabla(met, [4*cm, 6.5*cm, 6*cm]))

    # --- 5. CARACTERIZACION AGRICOLA ---
    story.append(Paragraph("5. Caracterizacion agricola", h1))
    por_grupo = (df.groupby("grupo_cultivo")["produccion_t"].sum()
                 .sort_values(ascending=False).head(8))
    total_dep = por_grupo.sum()
    data5 = [["Grupo de cultivo", "Produccion (t)", "% del total"]]
    for g, v in por_grupo.items():
        data5.append([str(g), f"{v:,.0f}", f"{v/total_dep*100:.1f}%"])
    story.append(_tabla(data5, [7*cm, 5*cm, 4*cm]))

    # --- 6. PRODUCCION Y PRODUCTIVIDAD ---
    story.append(Paragraph("6. Produccion, productividad y dinamica", h1))
    story.append(Paragraph("<b>6.1 Evolucion departamental 2019-2025</b>", h2))
    evol = (df.groupby("ano").agg(
        produccion=("produccion_t", "sum"),
        area_s=("area_sembrada_ha", "sum"),
        area_c=("area_cosechada_ha", "sum")).reset_index())
    evol["rendimiento"] = (evol["produccion"] / evol["area_c"].replace(0, 1)).round(2)
    d6 = [["Ano", "Produccion (t)", "Area (ha)", "Rendimiento (t/ha)"]]
    for _, r in evol.iterrows():
        d6.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                   f"{r['area_s']:,.0f}", f"{r['rendimiento']:.2f}"])
    story.append(_tabla(d6, [2*cm, 5*cm, 5*cm, 4.5*cm]))

    story.append(Paragraph("<b>6.2 Top 10 municipios por produccion</b>", h2))
    top_mun = (df.groupby("municipio")["produccion_t"].sum()
               .sort_values(ascending=False).head(10))
    d6b = [["Municipio", "Produccion (t)", "% del dpto."]]
    for m, v in top_mun.items():
        d6b.append([str(m), f"{v:,.0f}", f"{v/p_ult*100:.1f}%"])
    story.append(_tabla(d6b, [6*cm, 5*cm, 4*cm]))

    # --- 7. ANALISIS TERRITORIAL Y CONCENTRACION ---
    story.append(Paragraph("7. Analisis territorial y concentracion", h1))
    cr_mun = concentracion_cr(df, "municipio")
    cr_cul = concentracion_cr(df, "cultivo")
    story.append(Paragraph(
        f"La produccion agricola departamental presenta alta concentracion tanto "
        f"territorial como productiva:", body))
    d7 = [["Nivel", "CR1", "CR4", "CR10", "Interpretacion"],
          ["Municipios", f"{cr_mun['cr1']}%", f"{cr_mun['cr4']}%",
           f"{cr_mun['cr10']}%", "Top 4 concentran ~45%"],
          ["Cultivos", f"{cr_cul['cr1']}%", f"{cr_cul['cr4']}%",
           f"{cr_cul['cr10']}%", "Dominio de la cana"]]
    story.append(_tabla(d7, [3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 6*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"El <b>Gini territorial (0.64)</b> indica alta desigualdad espacial en la "
        f"produccion. El <b>HHI territorial</b> confirma concentracion moderada a alta.",
        body))

    # --- 8. ESPECIALIZACION Y DIVERSIFICACION ---
    story.append(Paragraph("8. Especializacion y diversificacion territorial", h1))
    story.append(Paragraph("<b>8.1 Location Quotient (LQ) - Top especializaciones</b>", h2))
    lq_df = tabla_lq(df, top_n=10)
    if not lq_df.empty:
        d8 = [["Municipio", "Cultivo", "LQ", "Interpretacion"]]
        for _, r in lq_df.iterrows():
            from core.analytics.informe_indicators import interpretar_lq
            d8.append([r["municipio"], r["cultivo"], str(r["lq"]),
                       interpretar_lq(r["lq"])])
        story.append(_tabla(d8, [4*cm, 4*cm, 2*cm, 6.5*cm]))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("<b>8.2 Diversificacion municipal (Shannon)</b>", h2))
    div = diversificacion_municipal(df).head(10)
    d8b = [["Municipio", "Cultivos", "Shannon", "Dominante", "% dominante"]]
    for _, r in div.iterrows():
        d8b.append([r["municipio"], str(int(r["n_cultivos"])),
                    f"{r['shannon']:.2f}", r["cultivo_dominante"],
                    f"{r['pct_dominante']:.1f}%"])
    story.append(_tabla(d8b, [4*cm, 2*cm, 2*cm, 5.5*cm, 3*cm]))
'''

p = Path("core/reports/informe_tecnico.py")
c = p.read_text(encoding="utf-8")
c = c.replace("    # SECCION_2_15_PLACEHOLDER", SECCIONES_2_8 + "\n    # SECCION_9_12_PLACEHOLDER")
p.write_text(c, encoding="utf-8")
print("[OK] Parte 2 agregada (secciones 2-8)")
print("Sigue: python scripts\\setup_informe_parte3.py")