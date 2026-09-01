"""Ficha tecnica oficial (estandar BID) + presentacion ejecutiva de EVA Valle."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from core.reports import meta
from core.reports.branding import LOGO, pagina_con_logo, build_con_logo

VERDE = colors.HexColor("#2E8B57")
VERDE_OSC = colors.HexColor("#1F5B41")
DORADO = colors.HexColor("#C98A2B")
GRIS = colors.HexColor("#4A5568")

REPO = "https://github.com/AdverickXIII/eva-valle-v3"
APP = "https://eva-valle-v3.streamlit.app"


def _logo(h=1.8):
    if not LOGO.exists():
        return None
    img = RLImage(str(LOGO))
    hh = h * cm
    w = img.drawWidth * hh / img.drawHeight
    img.drawHeight, img.drawWidth = hh, w
    return img


def _pie_portrait(canvas, doc):
    pagina_con_logo(canvas, doc)
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.2 * cm, meta.firma() + " | EVA Valle v3.0")
    canvas.drawRightString(19.6 * cm, 1.2 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


def _pie_landscape(canvas, doc):
    if LOGO.exists():
        canvas.saveState()
        canvas.drawImage(str(LOGO), 25.4 * cm, 18.4 * cm, width=1.7 * cm, height=1.7 * cm,
                         preserveAspectRatio=True, mask="auto")
        canvas.restoreState()
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(1.5 * cm, 0.8 * cm,
                      "EVA Valle v3.0 | Inteligencia territorial del agro vallecaucano")
    canvas.drawRightString(26.4 * cm, 0.8 * cm, f"{doc.page}")
    canvas.restoreState()


def _styles():
    st_ = getSampleStyleSheet()
    st_.add(ParagraphStyle("slide_title", parent=st_["Title"], textColor=VERDE_OSC,
                           fontSize=24, spaceAfter=6))
    st_.add(ParagraphStyle("slide_body", parent=st_["Normal"], fontSize=13, leading=18))
    st_.add(ParagraphStyle("small_d", parent=st_["Normal"], fontSize=9, textColor=DORADO))
    st_.add(ParagraphStyle("cover_t", parent=st_["Title"], textColor=VERDE_OSC, fontSize=30))
    st_.add(ParagraphStyle("sec_h", parent=st_["Heading2"], textColor=VERDE_OSC, fontSize=13))
    return st_


# ================= FICHA TECNICA (formato BID) =================
def build_ficha_tecnica_pdf() -> bytes:
    buf = __import__("io").BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Ficha Tecnica EVA Valle",
                            onPage=_pie_portrait)
    st_ = _styles()
    story = []

    cab = [[_logo(2.2) or "", Paragraph(
        "<b>EVA Valle v3.0</b><br/>Inteligencia territorial del agro vallecaucano",
        st_["Title"])]]
    t = Table(cab, colWidths=[3.5 * cm, 13 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story += [t, Spacer(1, 0.6 * cm)]

    cards = Table(
        [["Idioma", "Tipo de herramienta", "Licencia", "Version"],
         ["Python - Streamlit - Plotly", "Plataforma analitica / dashboard",
          "MIT (propuesta)", "v3.0"]],
        colWidths=[4.2 * cm, 5.6 * cm, 3.4 * cm, 3.3 * cm])
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EAF4EE")),
        ("FONTSIZE", (0, 1), (-1, 1), 8), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [cards, Spacer(1, 0.7 * cm)]

    acerca = [
        ("Responsable", f"{meta.firma()}. Fuente de datos: UPRA - Encuestas de Valuacion "
                        "Agropecuaria (EVA) 2019-2025."),
        ("Que es", "Plataforma analitica de codigo abierto que convierte el dato agricola "
                   "oficial del Valle del Cauca en inteligencia para la decision: 4 niveles "
                   "analiticos (descriptivo, diagnostico, predictivo, prescriptivo) mas "
                   "gobernanza del dato (auditoria y validacion satelital)."),
        ("Que problema resuelve", "El dato agricola oficial es publico pero no interpretado: "
                                  "los tomadores de decisiones carecen de diagnostico causal, "
                                  "proyecciones y prescripciones territoriales; la matriz "
                                  "productiva real queda oculta por el peso de la cana."),
        ("Como funciona", "Pipeline reproducible: descarga y auditoria del dato UPRA, modelo "
                          "conceptual, 18 modulos analiticos, validacion satelital Sentinel-1/2 "
                          "y entregables PDF/Excel firmados. Interfaz Streamlit con 3 roles y "
                          "despliegue en la nube."),
        ("Estandares abiertos", "Datos de fuente oficial (UPRA); codigo abierto con licencia MIT "
                                "(propuesta); metodologia documentada; alineado con principios de "
                                "Digital Public Goods (DPG)."),
        ("Como acceder", f"App en produccion: {APP}  |  Codigo fuente: {REPO}"),
    ]
    story.append(Paragraph("<b>Acerca de la herramienta</b>", st_["sec_h"]))
    for tit, txt in acerca:
        story += [Spacer(1, 0.25 * cm), Paragraph(f"<b>{tit}</b>", st_["Normal"]),
                  Paragraph(txt, st_["Normal"])]
    story += [Spacer(1, 0.6 * cm), Paragraph("<b>Etiquetas</b>", st_["sec_h"])]
    tags = Table(
        [["Sector", "Agricultura y desarrollo rural"],
         ["Caracteristicas", "IA predictiva - Geoespacial satelital - Apoyo a la decision - Datos abiertos"],
         ["ODS", "ODS 2 Hambre cero - ODS 9 Innovacion - ODS 16 Instituciones solidas"],
         ["Kits", "Agro - Municipios - Inteligencia territorial"]],
        colWidths=[4 * cm, 12.5 * cm])
    tags.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE_OSC),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [tags, Spacer(1, 0.6 * cm), Paragraph("<b>Evidencia</b>", st_["sec_h"])]
    ev = Table(
        [["42", "municipios cubiertos"], ["78", "cultivos analizados"],
         ["7", "anos (2019-2025)"], ["4+1", "niveles analiticos + gobernanza"],
         ["11", "generadores de PDF firmados"], ["0", "anomalias en validacion satelital"]],
        colWidths=[2.5 * cm, 14 * cm])
    ev.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (0, -1), 14),
        ("TEXTCOLOR", (0, 0), (0, -1), DORADO), ("FONTSIZE", (1, 0), (1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story.append(ev)
    build_con_logo(doc, story)
    return buf.getvalue()


# ================= PRESENTACION EJECUTIVA (10 laminas) =================
def build_presentacion_pdf() -> bytes:
    buf = __import__("io").BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter),
                            title="Presentacion Ejecutiva EVA Valle",
                            onPage=_pie_landscape,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=1.5 * cm)
    st_ = _styles()
    S = []

    # Lamina 1: portada
    lg = _logo(4.5)
    if lg:
        S += [Spacer(1, 1.5 * cm), lg, Spacer(1, 0.8 * cm)]
    S += [Paragraph("EVA Valle v3.0", st_["cover_t"]),
          Paragraph("Inteligencia territorial del agro vallecaucano", st_["slide_body"]),
          Spacer(1, 0.6 * cm),
          Paragraph("Datos oficiales UPRA - EVA 2019-2025", st_["small_d"]),
          Paragraph(meta.firma() + " - Data Analyst", st_["small_d"])]
    slides = [S]

    def lamina(num, titulo, bullets):
        s = [Paragraph(f"<font color='#C98A2B'>{num} / 10</font>", st_["small_d"]),
             Paragraph(titulo, st_["slide_title"]), Spacer(1, 0.4 * cm)]
        for b in bullets:
            s += [Paragraph(f"&bull;&nbsp;&nbsp;{b}", st_["slide_body"]), Spacer(1, 0.22 * cm)]
        slides.append(s)

    lamina(2, "El problema", [
        "El dato agricola oficial existe y es publico: UPRA lo levanta, AGRONET lo publica.",
        "Pero nadie lo interpreta para el Valle: sin diagnostico, sin pronostico, sin prescripcion.",
        "Decision publica sin evidencia territorial = inversion a ciegas."])
    lamina(3, "La solucion: inteligencia en 4 niveles", [
        "Descriptivo - que paso: 12 analisis, concentracion con/sin cana, LQ, Shannon.",
        "Diagnostico - por que paso: causa raiz, clusters, shock 2020.",
        "Predictivo - que pasara: backtesting (MAPE), escenarios P10/P50/P90.",
        "Prescriptivo - que hacer: zonas Ord. 513, matriz LQ x Shannon, alertas.",
        "Gobernanza: auditoria de datos + validacion satelital Sentinel-1/2."])
    lamina(4, "Rigor metodologico", [
        "Fuente unica oficial: UPRA - EVA 2019-2025 (42 municipios, 78 cultivos).",
        "Auditoria de calidad declarada; 0 anomalias en validacion satelital.",
        "Modelos con seleccion automatica por backtesting; credibilidad declarada.",
        "Codigo abierto (MIT propuesta): el gobierno, dueno de su herramienta."])
    lamina(5, "Hallazgo 1 - La matriz oculta (con/sin cana)", [
        "Con cana: 95.3% del tonelaje departamental; el mapa parece monocultivo.",
        "Sin cana: Centro lidera (41.7%) y Sur es el mas eficiente (14 t/ha).",
        "La lectura dual cambia las prioridades de inversion publica."])
    lamina(6, "Hallazgo 2 - Motores de crecimiento", [
        "Platano Sevilla: +12.2% anual por intensificacion (rendimiento +10.3%).",
        "Alcala: maracuya +45.5% y papaya +37.3% (apuestas emergentes).",
        "Cada ficha descompone crecimiento en area vs rendimiento."])
    lamina(7, "Hallazgo 3 - Prediccion con credibilidad", [
        "Proyeccion 2026-2028 por cultivo y municipio con 3 escenarios.",
        "Credibilidad declarada segun MAPE de backtesting (ej. 4.2% = alta).",
        "Alertas tempranas: dependencia, declive sostenido, caida reciente."])
    lamina(8, "Prescripcion territorial", [
        "Zonas oficiales POTD (Ordenanza 513): Norte, Centro, Sur, Pacifico.",
        "Pacifico: 1% del dpto y aprovechamiento 73.2% -> prioridad de inversion.",
        "Matriz LQ x Shannon: proteger, diversificar, apostar, priorizar."])
    lamina(9, "Entregables", [
        "11 generadores de PDF firmados: fichas, reportes, ejecutivo, zonas, satelital.",
        "Excel y CSV por municipio y cultivo; ranking y comparativas.",
        "Dashboard en la nube con 3 roles: usuario, analista, admin."])
    lamina(10, "Hoja de ruta", [
        "Modelo economico: precios, segmentacion, proyeccion a 36 meses.",
        "Asistente conversacional determinista: el dato responde, sin alucinacion.",
        "Publicacion como Digital Public Good / catalogo BID (code@iadb.org).",
        f"Contacto: {meta.firma()} - Data Analyst."])

    story = []
    for i, s in enumerate(slides):
        story += s
        if i < len(slides) - 1:
            story.append(PageBreak())
    build_con_logo(doc, story)
    return buf.getvalue()
