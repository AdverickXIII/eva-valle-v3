"""PARTE 3: Agrega secciones 9-12 (correlaciones, brechas, hallazgos, recomendaciones)."""
from pathlib import Path

SECCIONES_9_12 = '''

    # --- 9. RELACIONES ESTADISTICAS ---
    story.append(Paragraph("9. Relaciones estadisticas", h1))
    story.append(Paragraph(
        "Se calcularon correlaciones Pearson (lineal) y Spearman (monotona) entre "
        "las principales variables productivas, con correccion por valores cero:", body))
    corr = correlaciones(df)
    if not corr.empty:
        d9 = [["Relacion", "n", "Pearson r", "p-value", "Spearman r", "Interpretacion"]]
        for _, r in corr.iterrows():
            d9.append([r["relacion"], str(int(r["n"])),
                       f"{r['pearson_r']:.2f}", f"{r['pearson_p']:.3f}",
                       f"{r['spearman_r']:.2f}", r["interpretacion"]])
        story.append(_tabla(d9, [4*cm, 1.5*cm, 2*cm, 2*cm, 2*cm, 5*cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "La correlacion area-produccion suele ser fuerte (relacion escala-dependiente), "
        "mientras que area-rendimiento es debil o negativa (rendimientos decrecientes en "
        "fronteras agricolas expandidas).", body))

    # --- 10. BRECHAS, RIESGOS Y OPORTUNIDADES ---
    story.append(Paragraph("10. Brechas, riesgos y oportunidades", h1))
    bg = brechas(df)
    if bg:
        d10 = [["Indicador", "Valor", "Significado"],
               ["Ratio maximo / minimo", f"{bg['ratio_max_min']:.1f}x",
                "Brecha extrema entre municipios"],
               ["Ratio P90 / P10", f"{bg['ratio_p90_p10']:.1f}x",
                "Desigualdad entre cuantiles"],
               ["Ratio promedio / mediana", f"{bg['ratio_promedio_mediana']:.2f}x",
                "Asimetria positiva"],
               ["Mediana produccion municipal", f"{bg['mediana']:,.0f} t",
                "Municipio tipico"],
               ["Promedio produccion municipal", f"{bg['promedio']:,.0f} t",
                "Promedio aritmetico"]]
        story.append(_tabla(d10, [5*cm, 3.5*cm, 8*cm]))

    story.append(Paragraph("<b>10.1 Riesgos identificados</b>", h2))
    for r in [
        "Dependencia extrema de la cana (95% del tonelaje, HHI > 2,500).",
        "Concentracion territorial (Gini 0.64): 1 municipio lidera 17.8% del dpto.",
        "Cultivos en declive sostenido (malanga, coco, borojo).",
        "Anomalias de reporte persistentes (~4% cosechada > sembrada).",
    ]:
        story.append(Paragraph(f"&bull; {r}", body))

    story.append(Paragraph("<b>10.2 Oportunidades</b>", h2))
    for o in [
        "Sin cana, HHI cae a ~1,045: base diversificada real.",
        "Cultivos en alto crecimiento: cebolla de rama, aji, tomate (CAGR > 18%).",
        "Municipios intermedios con alto potencial productivo.",
        "Especializaciones territoriales claras para cadenas de valor.",
    ]:
        story.append(Paragraph(f"&bull; {o}", body))

    # --- 11. CLASIFICACION MUNICIPAL (IDAM) ---
    story.append(Paragraph("11. Clasificacion municipal por desempeno (IDAM)", h1))
    story.append(Paragraph(
        "El Indice de Desempeno Agricola Municipal (IDAM) combina 5 componentes "
        "ponderados: produccion (25%), rendimiento (20%), diversificacion (20%), "
        "crecimiento (20%) y estabilidad (15%). Escala 0-100.", body))
    idam_df = idam(df)
    story.append(Paragraph("<b>Top 10 municipios lideres</b>", h2))
    d11 = [["Municipio", "IDAM", "Produccion", "Shannon", "CAGR %", "Clasificacion"]]
    for _, r in idam_df.head(10).iterrows():
        d11.append([r["municipio"], f"{r['idam']:.1f}",
                    f"{r['produccion']:,.0f}", f"{r['shannon']:.2f}",
                    f"{r['crecimiento_pct']:+.1f}%", r["clasificacion"]])
    story.append(_tabla(d11, [3.5*cm, 2*cm, 3*cm, 2*cm, 2.5*cm, 3.5*cm]))

    story.append(Paragraph("<b>Municipios rezagados (bottom 5)</b>", h2))
    d11b = [["Municipio", "IDAM", "Produccion", "Shannon", "CAGR %", "Clasificacion"]]
    for _, r in idam_df.tail(5).iterrows():
        d11b.append([r["municipio"], f"{r['idam']:.1f}",
                     f"{r['produccion']:,.0f}", f"{r['shannon']:.2f}",
                     f"{r['crecimiento_pct']:+.1f}%", r["clasificacion"]])
    story.append(_tabla(d11b, [3.5*cm, 2*cm, 3*cm, 2*cm, 2.5*cm, 3.5*cm]))

    # --- 12. CONCLUSIONES Y RECOMENDACIONES ---
    story.append(Paragraph("12. Conclusiones y recomendaciones", h1))
    story.append(Paragraph("<b>12.1 Conclusiones principales</b>", h2))
    for c in [
        "El sector agricola del Valle esta dominado por la cana, pero la economia "
        "no-canera es diversificada y dinamica.",
        "Existe alta concentracion territorial: pocos municipios concentran la mayoria "
        "de la produccion, generando vulnerabilidad espacial.",
        "El rendimiento promedio se ha mantenido estable (+0.4% interanual), "
        "sugiriendo expansion de frontera mas que innovacion tecnologica.",
        "La especializacion territorial es clara: municipios con vocacion especifica "
        "(LQ > 1.5) en cultivos puntuales.",
        "Los municipios con menor IDAM no son necesariamente los mas pobres; "
        "muchos tienen alto potencial sin explotar.",
    ]:
        story.append(Paragraph(f"&bull; {c}", body))

    story.append(Paragraph("<b>12.2 Recomendaciones de politica</b>", h2))
    recs = [
        ("Diversificacion productiva",
         "Fomentar cadenas no-caneras de alto valor (platano, citricos, tomate) "
         "en municipios con LQ > 1.5 para esos cultivos."),
        ("Priorizacion territorial",
         "Focalizar asistencia tecnica en municipios rezagados del IDAM pero con "
         "alta diversificacion (Shannon alto) y crecimiento positivo."),
        ("Alertas tempranas",
         "Monitorear cultivos en declive (malanga, coco, borojo) para identificar "
         "causas (climaticas, de mercado, fitosanitarias)."),
        ("Mejora de calidad del dato",
         "Implementar validacion cruzada con teledeteccion para reducir anomalias "
         "de reporte municipal."),
        ("Observatorio permanente",
         "Institucionalizar un tablero de indicadores departamental con actualizacion "
         "anual automatica."),
    ]
    for titulo, det in recs:
        story.append(Paragraph(f"<b>{titulo}.</b> {det}", body))

    # --- PIE FINAL ---
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"<i>Fuente: UPRA - EVA 2019-2025. {meta.firma()}. "
        f"Indicadores calculados con metodologia reproducible. "
        f"Sujeto a validacion de experto.</i>",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8, textColor=GRIS)))
'''

p = Path("core/reports/informe_tecnico.py")
c = p.read_text(encoding="utf-8")
c = c.replace("    # SECCION_9_12_PLACEHOLDER", SECCIONES_9_12)
p.write_text(c, encoding="utf-8")
print("[OK] Parte 3 agregada (secciones 9-12)")
print("Sigue: python scripts\\generar_informe_tecnico_final.py")