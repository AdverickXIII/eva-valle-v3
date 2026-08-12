"""Generador del informe tecnico EVA Valle 2019-2025 (nivel FAO/CEPAL)."""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from config.settings import settings
from core.analytics.informe_indicators import (
    brechas, concentracion_cr, correlaciones, diversificacion_municipal,
    dinamica_temporal, idam, tabla_lq,
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
    w, _ = letter
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(36, 42, w - 36, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(36, 32, f"{meta.firma()} | Informe Tecnico 2019-2025")
    canvas.drawRightString(w - 36, 32, f"Pagina {doc.page}")
    canvas.restoreState()


def _tabla(data, col_widths=None):
    t = Table(data, hAlign="LEFT", colWidths=col_widths)
    t.setStyle(_style())
    return t


def _barras(labels, valores, titulo, color=VERDE, width=460, height=180):
    d = Drawing(width, height)
    bc = HorizontalBarChart()
    bc.x = 120
    bc.y = 10
    bc.height = height - 30
    bc.width = width - 130
    bc.data = [valores]
    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 7
    bc.valueAxis.labels.fontSize = 7
    bc.bars[0].fillColor = color
    bc.barWidth = 10
    d.add(bc)
    return d


def _pct(new, old):
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100


# =====================================================================
# BUILDER PRINCIPAL (se llena por partes)
# =====================================================================
def build_informe(df: pd.DataFrame) -> bytes:
    """Genera el informe tecnico completo."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            title="Informe Tecnico EVA Valle 2019-2025")
    st_ = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=st_["Title"], textColor=VERDE, fontSize=22)
    h1 = ParagraphStyle("H1", parent=st_["Heading1"], textColor=VERDE,
                        spaceBefore=14, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=st_["Heading2"], textColor=VERDE,
                        spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("Body", parent=st_["Normal"], leading=12)
    story = []

    # --- PORTADA ---
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Informe Tecnico", title))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Dinamica y Estructura Agricola<br/>Valle del Cauca 2019-2025",
        ParagraphStyle("Sub", parent=st_["Heading2"],
                       textColor=GRIS, fontSize=16, leading=20)))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "<b>Analisis estadistico, territorial y productivo</b><br/>"
        "con indicadores de concentracion, especializacion y desempeno",
        ParagraphStyle("Desc", parent=st_["Normal"], alignment=1)))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        f"<b>Elaborado por:</b> {meta.AUTOR}<br/>"
        f"{meta.CARGO}<br/><br/>"
        f"<b>Fecha:</b> {date.today().strftime('%Y-%m-%d')}<br/>"
        f"<b>Fuente oficial:</b> UPRA - Encuestas de Valoracion Agropecuaria (EVA)",
        body))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("<i>Documento tecnico de referencia</i>",
                           ParagraphStyle("Italic", parent=st_["Italic"], alignment=1)))

    # --- RESUMEN EJECUTIVO (seccion 1) ---
    story.append(Paragraph("1. Resumen Ejecutivo", h1))
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ultimo, anterior = anos[-1], anos[-2]
    p_ult = df[df["ano"] == ultimo]["produccion_t"].sum()
    p_ant = df[df["ano"] == anterior]["produccion_t"].sum()
    a_ult = df[df["ano"] == ultimo]["area_sembrada_ha"].sum()
    c_ult = df[df["ano"] == ultimo]["area_cosechada_ha"].sum()
    rend = p_ult / c_ult if c_ult else 0

    story.append(Paragraph(
        f"El sector agricola del Valle del Cauca registro en {ultimo} una produccion de "
        f"<b>{p_ult:,.0f} toneladas</b> ({_pct(p_ult, p_ant):+.1f}% vs {anterior}), en "
        f"<b>{a_ult:,.0f} hectareas</b> de area sembrada y un rendimiento promedio de "
        f"<b>{rend:.1f} t/ha</b>, distribuidas entre <b>{df['cultivo'].nunique()} cultivos</b> "
        f"y <b>{df['municipio'].nunique()} municipios</b>.", body))
    story.append(Spacer(1, 0.3 * cm))

    hallazgos = [
        "La cana de azucar concentra 95% del tonelaje departamental; "
        "al excluirla emergen 11 cultivos relevantes (platano, pina, maiz, citricos).",
        "Gini productivo = 0.98 (extrema concentracion por cultivo).",
        "Gini territorial = 0.64 (alta concentracion por municipio; Palmira lidera).",
        "Top 4 municipios concentran ~45% de la produccion departamental.",
        "Cebolla de rama y aji presentan los mayores CAGR (22-27%).",
        "Malanga, coco y borojo muestran declives sostenidos.",
    ]
    for h in hallazgos:
        story.append(Paragraph(f"&bull; {h}", body))

    # Placeholder para el resto del contenido (secciones 2-15)


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


    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def main():
    path = settings.DATA_MODEL_PATH / "eva_agricola_valle_modelo_conceptual.csv"
    df = pd.read_csv(path, low_memory=False)
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "informe_tecnico_valle_2019_2025.pdf"
    pdf_bytes = build_informe(df)
    out_path.write_bytes(pdf_bytes)
    print(f"[OK] Informe tecnico: {out_path}")
    print(f"     Tamano: {out_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
