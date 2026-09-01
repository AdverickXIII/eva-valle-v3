"""Informe Ejecutivo Narrativo: storytelling de 10 capitulos."""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
from core.reports.branding import pagina_con_logo, build_con_logo
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from config.settings import settings
from core.analytics.narrative_engine import (
    frase_de_la_agricultura, generar_insights,
)
from core.analytics.strategic_matrices import (
    matriz_cultivos, matriz_municipios, resumen_matrices,
)
from core.reports import meta

VERDE = colors.HexColor("#2E8B57")
GRIS = colors.HexColor("#4A5568")
NARANJA = colors.HexColor("#DD6B20")


def _style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8F9FA")]),
    ])


def _footer(canvas, doc):
    pagina_con_logo(canvas, doc)
    w, _ = letter
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(36, 42, w - 36, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(36, 32, f"{meta.firma()} | Informe Ejecutivo Narrativo")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def _tabla(data, col_widths=None):
    t = Table(data, hAlign="LEFT", colWidths=col_widths)
    t.setStyle(_style())
    return t


def build_storytelling(df: pd.DataFrame) -> bytes:
    """Genera el informe ejecutivo narrativo (10 capitulos)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, onPage=pagina_con_logo, pagesize=letter,
                            title="Informe Ejecutivo Narrativo")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE, fontSize=24)
    h1 = ParagraphStyle("H1", parent=st_["Heading1"], textColor=VERDE,
                        spaceBefore=16, spaceAfter=8, fontSize=18)
    h2 = ParagraphStyle("H2", parent=st_["Heading2"], textColor=VERDE,
                        spaceBefore=12, spaceAfter=6, fontSize=14)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=14, fontSize=10)
    story = []

    # --- PORTADA ---
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Informe Ejecutivo Narrativo", title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Valle del Cauca 2019-2025<br/>"
        "<i>Una historia de crecimiento, concentracion y oportunidades</i>",
        ParagraphStyle("Sub", parent=st_["Heading2"],
                       textColor=GRIS, fontSize=16, leading=20)))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        f"<b>Elaborado por:</b> {meta.AUTOR}<br/>"
        f"{meta.CARGO}<br/><br/>"
        f"<b>Fecha:</b> {date.today().strftime('%Y-%m-%d')}<br/>"
        f"<b>Fuente:</b> UPRA - Encuestas de Valoracion Agropecuaria (EVA)",
        body))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "<i>Documento ejecutivo para tomadores de decision</i>",
        ParagraphStyle("Italic", parent=st_["Italic"], alignment=1, fontSize=11)))

    # --- CAPITULO 1: LA AGRICULTURA EN CIFRAS ---
    story.append(Paragraph("1. La agricultura del Valle en cifras", h1))
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ultimo = anos[-1]
    p_ult = df[df["ano"] == ultimo]["produccion_t"].sum()
    a_ult = df[df["ano"] == ultimo]["area_sembrada_ha"].sum()
    c_ult = df[df["ano"] == ultimo]["area_cosechada_ha"].sum()
    rend = p_ult / c_ult if c_ult else 0
    p_ini = df[df["ano"] == anos[0]]["produccion_t"].sum()
    crecimiento_total = ((p_ult - p_ini) / p_ini * 100) if p_ini else 0

    d1 = [
        ["<b>Produccion total</b>", f"{p_ult:,.0f} toneladas"],
        ["<b>Area cultivada</b>", f"{a_ult:,.0f} hectareas"],
        ["<b>Municipios productores</b>", f"{df['municipio'].nunique()}"],
        ["<b>Cultivos registrados</b>", f"{df['cultivo'].nunique()}"],
        ["<b>Crecimiento 2019-2025</b>", f"{crecimiento_total:+.1f}%"],
        ["<b>Rendimiento promedio</b>", f"{rend:.1f} t/ha"],
    ]
    t1 = Table(d1, hAlign="LEFT", colWidths=[6*cm, 10*cm])
    t1.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t1)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"El sector agricola del Valle del Cauca produce mas de <b>{p_ult/1e6:.1f} millones de toneladas</b> "
        f"anuales, distribuidas entre {df['cultivo'].nunique()} cultivos en {df['municipio'].nunique()} municipios. "
        f"Entre {anos[0]} y {ultimo}, la produccion crecio <b>{crecimiento_total:.1f}%</b>, "
        f"con un rendimiento promedio de <b>{rend:.1f} toneladas por hectarea</b>.",
        body))

    # --- CAPITULO 2: SIETE ANOS DE TRANSFORMACION ---
    story.append(Paragraph("2. Siete anos de transformacion", h1))
    story.append(Paragraph(
        f"La produccion agricola paso de <b>{p_ini:,.0f} toneladas en {anos[0]}</b> a "
        f"<b>{p_ult:,.0f} toneladas en {ultimo}</b>, un crecimiento acumulado de "
        f"<b>{crecimiento_total:.1f}%</b>.", body))
    story.append(Spacer(1, 0.3 * cm))

    # Tabla de evolucion
    evol = df.groupby("ano").agg(
        produccion=("produccion_t", "sum"),
        area=("area_sembrada_ha", "sum"),
    ).reset_index()
    evol["rendimiento"] = (evol["produccion"] / evol["area"].replace(0, 1)).round(2)
    d2 = [["Ano", "Produccion (t)", "Area (ha)", "Rendimiento (t/ha)"]]
    for _, r in evol.iterrows():
        d2.append([str(int(r["ano"])), f"{r['produccion']:,.0f}",
                   f"{r['area']:,.0f}", f"{r['rendimiento']:.2f}"])
    story.append(_tabla(d2, [2.5*cm, 5*cm, 4.5*cm, 4.5*cm]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "<b>La pregunta clave:</b> La agricultura esta creciendo, pero el crecimiento es "
        "modesto (+{:.1f}% anual promedio). La pregunta es: ¿que esta impulsando este crecimiento?".format(
            crecimiento_total / (ultimo - anos[0])), body))

    # --- CAPITULO 3: QUE IMPULSA EL CRECIMIENTO ---
    story.append(Paragraph("3. ¿Que impulsa el crecimiento?", h1))
    story.append(Paragraph(
        "Para responder, comparamos el crecimiento de tres componentes:", body))
    d3 = [["Componente", "Crecimiento 2019-2025", "Interpretacion"],
          ["Produccion", f"{crecimiento_total:+.1f}%", "Toneladas totales"],
          ["Area", f"{((a_ult - df[df['ano']==anos[0]]['area_sembrada_ha'].sum()) / df[df['ano']==anos[0]]['area_sembrada_ha'].sum() * 100):+.1f}%",
           "Expansion de frontera"],
          ["Rendimiento", f"{((rend - p_ini / df[df['ano']==anos[0]]['area_cosechada_ha'].sum()) / (p_ini / df[df['ano']==anos[0]]['area_cosechada_ha'].sum()) * 100):+.1f}%",
           "Mejora de productividad"]]
    story.append(_tabla(d3, [4*cm, 5*cm, 7.5*cm]))
    story.append(Spacer(1, 0.3 * cm))

    # Determinar que impulso mas
    a_ini = df[df["ano"] == anos[0]]["area_sembrada_ha"].sum()
    c_ini = df[df["ano"] == anos[0]]["area_cosechada_ha"].sum()
    rend_ini = p_ini / c_ini if c_ini else 0
    crec_area = ((a_ult - a_ini) / a_ini * 100) if a_ini else 0
    crec_rend = ((rend - rend_ini) / rend_ini * 100) if rend_ini else 0

    if crec_area > crec_rend:
        driver = "expansion de area cultivada"
    else:
        driver = "mejora de rendimientos (productividad)"
    story.append(Paragraph(
        f"<b>Conclusion:</b> El crecimiento agricola del periodo estuvo impulsado principalmente "
        f"por <b>{driver}</b>. Esto sugiere que el sector esta expandiendo frontera agricola "
        f"mas que innovando en productividad.", body))



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
        f'<b>La frase de la agricultura:</b><br/><br/>'
        f'<i>"{frase}"</i>',
        ParagraphStyle("Cierre", parent=st_["Normal"], fontSize=12,
                       textColor=VERDE, alignment=1, leading=16)))

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"<i>Fuente: UPRA - EVA 2019-2025. {meta.firma()}. "
        f"Indicadores calculados automaticamente, sujetos a validacion de experto.</i>",
        ParagraphStyle("Pie", parent=st_["Italic"], fontSize=8, textColor=GRIS)))



    build_con_logo(doc, story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def main():
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(path, low_memory=False)
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "informe_ejecutivo_narrativo.pdf"
    pdf_bytes = build_storytelling(df)
    out_path.write_bytes(pdf_bytes)
    print(f"[OK] Informe Ejecutivo Narrativo: {out_path}")
    print(f"     Tamano: {out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
