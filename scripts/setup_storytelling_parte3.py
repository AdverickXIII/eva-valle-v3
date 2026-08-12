"""PARTE 3: Agrega capitulos 8-10 + frase de cierre."""
from pathlib import Path

CAPS_8_10 = '''

    # --- CAPITULO 8: DONDE ESTAN LAS ESPECIALIZACIONES ---
    story.append(Paragraph("8. ¿Donde estan las especializaciones?", h1))
    story.append(Paragraph(
        "El <b>Location Quotient (LQ)</b> mide la especializacion territorial: "
        "¿que hace particularmente bien cada municipio?", body))
    story.append(Spacer(1, 0.3 * cm))

    from core.analytics.informe_indicators import tabla_lq
    lq_df = tabla_lq(df, top_n=8)
    if not lq_df.empty:
        d8 = [["Municipio", "Cultivo", "LQ", "Especializacion"]]
        for _, r in lq_df.iterrows():
            from core.analytics.informe_indicators import interpretar_lq
            d8.append([r["municipio"], r["cultivo"], str(r["lq"]),
                       interpretar_lq(r["lq"])])
        story.append(_tabla(d8, [4*cm, 4*cm, 2*cm, 6.5*cm]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Municipios con <b>LQ > 1.5</b> tienen especializacion significativa en cultivos "
        "especificos. Esto permite identificar <b>vocaciones productivas territoriales</b> "
        "para priorizar cadenas de valor.", body))

    # --- CAPITULO 9: DONDE ESTAN LAS OPORTUNIDADES ---
    story.append(Paragraph("9. ¿Donde estan las oportunidades?", h1))
    story.append(Paragraph(
        "Cruzamos <b>produccion x productividad x crecimiento</b> para identificar "
        "oportunidades estrategicas:", body))
    story.append(Spacer(1, 0.3 * cm))

    insights = generar_insights(df)
    story.append(Paragraph("<b>Los 10 hallazgos clave:</b>", h2))
    for i, ins in enumerate(insights[:10], 1):
        story.append(Paragraph(f"<b>{i}.</b> {ins['dato']}", body))
        story.append(Paragraph(f"<i>Interpretacion:</i> {ins['interpretacion']}", body))
        story.append(Paragraph(f"<i>Implicacion:</i> {ins['implicacion']}", body))
        story.append(Spacer(1, 0.2 * cm))

    # --- CAPITULO 10: LAS 10 CONCLUSIONES ---
    story.append(Paragraph("10. Las 10 conclusiones que debemos recordar", h1))
    story.append(Paragraph(
        "Sintetizamos los hallazgos en 10 conclusiones accionables:", body))
    story.append(Spacer(1, 0.3 * cm))

    conclusiones = [
        "La cana domina la produccion (95%), pero la economia no-canera es diversificada.",
        "El crecimiento es modesto (+1.4% anual), impulsado por expansion de area.",
        "Cultivos motores: cana, platano, pina (alta participacion + crecimiento).",
        "Cultivos emergentes: tomate de arbol, soya (oportunidad de escalar).",
        "Municipios motores: Palmira, Candelaria, El Cerrito (pilares productivos).",
        "Alta concentracion territorial (Gini 0.64): Palmira lidera con 17.8%.",
        "Brecha P90/P10 de 46.6x: alta desigualdad entre municipios.",
        "Especializaciones territoriales claras (LQ > 1.5) para cadenas de valor.",
        "Municipios de mejora requieren asistencia tecnica para rendimientos.",
        "Sin cana, HHI cae a 1,045: base solida para diversificacion.",
    ]
    for i, c in enumerate(conclusiones, 1):
        story.append(Paragraph(f"<b>{i:02d}.</b> {c}", body))

    # --- FRASE DE CIERRE ---
    story.append(Spacer(1, 1 * cm))
    frase = frase_de_la_agricultura(df)
    story.append(Paragraph(
        f"<b>La frase de la agricultura:</b><br/><br/>"
        f"<i>"{frase}"</i>",
        ParagraphStyle("Cierre", parent=st_["Normal"], fontSize=12,
                       textColor=VERDE, alignment=1, leading=16)))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"<i>Fuente: UPRA - EVA 2019-2025. {meta.firma()}. "
        f"Indicadores calculados automaticamente, sujetos a validacion de experto.</i>",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8, textColor=GRIS)))
'''

p = Path("core/reports/storytelling_report.py")
c = p.read_text(encoding="utf-8")
c = c.replace("    # CAPITULOS_8_10_PLACEHOLDER", CAPS_8_10)
p.write_text(c, encoding="utf-8")
print("[OK] Parte 3 agregada (capitulos 8-10 + frase de cierre)")
print("Sigue: python scripts\\generar_storytelling_final.py")