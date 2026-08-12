"""PARTE 2: Agrega capitulos 4-7 al storytelling."""
from pathlib import Path

CAPS_4_7 = '''

    # --- CAPITULO 4: QUE PRODUCE EL VALLE ---
    story.append(Paragraph("4. ¿Que produce el Valle?", h1))
    story.append(Paragraph(
        "El Valle produce {n} cultivos diferentes, pero la produccion esta fuertemente "
        "concentrada. Clasificamos los cultivos en <b>4 cuadrantes estrategicos</b> segun "
        "su participacion y crecimiento:".format(n=df['cultivo'].nunique()), body))
    story.append(Spacer(1, 0.3 * cm))

    mc = matriz_cultivos(df)
    rm = resumen_matrices(df)

    # Tabla de cuadrantes
    d4 = [["Cuadrante", "Numero", "Ejemplos", "Significado"],
          ["🚀 Motores", str(rm['cultivos']['n_motores']),
           rm['cultivos']['motores'], "Alta participacion + alto crecimiento"],
          ["🏛️ Consolidados", str(rm['cultivos']['n_consolidados']),
           rm['cultivos']['consolidados'], "Alta participacion + bajo crecimiento"],
          ["🌱 Emergentes", str(rm['cultivos']['n_emergentes']),
           rm['cultivos']['emergentes'], "Baja participacion + alto crecimiento"],
          ["⚠️ Rezagados", str(rm['cultivos']['n_rezagados']),
           rm['cultivos']['rezagados'], "Baja participacion + bajo crecimiento"]]
    story.append(_tabla(d4, [3.5*cm, 2*cm, 6*cm, 5*cm]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        f"<b>Los motores del crecimiento</b> son {rm['cultivos']['motores']}: cultivos con alta "
        f"participacion y crecimiento positivo. Los <b>emergentes</b> ({rm['cultivos']['emergentes']}) "
        f"representan oportunidades de inversion para escalar produccion.", body))

    # --- CAPITULO 5: DONDE SE PRODUCE ---
    story.append(Paragraph("5. ¿Donde se produce?", h1))
    story.append(Paragraph(
        "La produccion se distribuye entre {n} municipios, pero con alta concentracion "
        "territorial. Clasificamos los municipios en <b>4 cuadrantes</b> segun produccion "
        "y productividad:".format(n=df['municipio'].nunique()), body))
    story.append(Spacer(1, 0.3 * cm))

    mm = matriz_municipios(df)

    # Tabla de cuadrantes municipales
    d5 = [["Cuadrante", "Numero", "Ejemplos", "Significado"],
          ["🟢 Motores", str(rm['municipios']['n_motores']),
           rm['municipios']['motores'], "Alta produccion + alta productividad"],
          ["🟡 Mejora", str(rm['municipios']['n_mejora']),
           rm['municipios']['mejora'], "Alta produccion + baja productividad"],
          ["🔵 Potenciales", str(rm['municipios']['n_potenciales']),
           rm['municipios']['potenciales'], "Baja produccion + alta productividad"],
          ["🔴 Rezagados", str(rm['municipios']['n_rezagados']),
           rm['municipios']['rezagados'], "Baja produccion + baja productividad"]]
    story.append(_tabla(d5, [3.5*cm, 2*cm, 6*cm, 5*cm]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        f"<b>Los municipios motores</b> ({rm['municipios']['motores']}) son los pilares de la "
        f"produccion. Los <b>de mejora</b> ({rm['municipios']['mejora']}) requieren asistencia "
        f"tecnica para mejorar rendimientos.", body))

    # --- CAPITULO 6: UN TERRITORIO CON DIFERENTES AGRICULTURAS ---
    story.append(Paragraph("6. Un territorio con diferentes agriculturas", h1))
    story.append(Paragraph(
        "No todos los municipios son iguales. La clasificacion por desempeno revela "
        "tres categorias:", body))
    story.append(Spacer(1, 0.3 * cm))

    from core.analytics.informe_indicators import idam
    idam_df = idam(df)
    lideres = idam_df[idam_df["clasificacion"] == "Lider"].head(5)
    rezagados = idam_df[idam_df["clasificacion"] == "Rezagado"].tail(5)

    d6 = [["Categoria", "Municipios", "Caracteristicas"],
          ["🟢 Lideres", ", ".join(lideres["municipio"].tolist()),
           "Alto IDAM (produccion + productividad + crecimiento)"],
          ["🟡 Intermedios", f"{len(idam_df[idam_df['clasificacion']=='Intermedio'])} municipios",
           "Desempeno moderado"],
          ["🔴 Rezagados", ", ".join(rezagados["municipio"].tolist()),
           "Bajo IDAM; requieren intervencion"]]
    story.append(_tabla(d6, [3*cm, 6*cm, 7.5*cm]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Cada municipio tiene una <b>ficha tecnica</b> con sus indicadores clave: produccion, "
        "rendimiento, CAGR, cultivo dominante, especializacion y diversificacion.", body))

    # --- CAPITULO 7: QUE TAN CONCENTRADA ESTA LA AGRICULTURA ---
    story.append(Paragraph("7. ¿Que tan concentrada esta la agricultura?", h1))
    from core.analytics.pareto import conc_metrics, territorial
    cc = conc_metrics(df, False)
    ter = territorial(df)

    story.append(Paragraph(
        f"La produccion agricola presenta <b>alta concentracion</b> tanto productiva como "
        f"territorial:", body))
    story.append(Spacer(1, 0.3 * cm))

    d7 = [["Indicador", "Valor", "Interpretacion"],
          ["Gini productivo", f"{cc['gini']:.2f}", "Concentracion extrema por cultivo"],
          ["HHI productivo", f"{cc['hhi']:,.0f}", "Monocultivo (cana)"],
          ["Gini territorial", f"{ter['gini']:.2f}", "Alta concentracion espacial"],
          ["Municipio lider", f"{ter['top']} ({ter['top_pct']:.1f}%)", "Domina la produccion"]]
    story.append(_tabla(d7, [4*cm, 3.5*cm, 9*cm]))
    story.append(Spacer(1, 0.3 * cm))

    from core.analytics.informe_indicators import brechas
    bg = brechas(df)
    story.append(Paragraph(
        f"<b>La brecha territorial es significativa:</b> el municipio en el percentil 90 "
        f"produce <b>{bg['ratio_p90_p10']:.1f} veces mas</b> que el del percentil 10. "
        f"Esto indica alta desigualdad espacial en la produccion.", body))

    # CAPITULOS_8_10_PLACEHOLDER
'''

p = Path("core/reports/storytelling_report.py")
c = p.read_text(encoding="utf-8")
c = c.replace("    # CAPITULOS_4_7_PLACEHOLDER", CAPS_4_7)
p.write_text(c, encoding="utf-8")
print("[OK] Parte 2 agregada (capitulos 4-7)")
print("Sigue: python scripts\\setup_storytelling_parte3.py")